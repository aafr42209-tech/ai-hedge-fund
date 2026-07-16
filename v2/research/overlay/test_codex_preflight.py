from __future__ import annotations

import base64
import subprocess

import pytest

from . import codex_preflight
from .codex_preflight import (
    build_codex_feature_gate,
    capture_zero_call_preflight,
    LOCAL_COMMAND_TIMEOUT_SECONDS,
    LocalCommandCapture,
    parse_codex_feature_catalog,
    pilot_sandbox_identity_sha256,
    SubprocessLocalCommandRunner,
    write_zero_call_preflight,
)
from .contracts import (
    codex_feature_catalog_definition_sha256,
    codex_feature_catalog_snapshot_sha256,
)


def _catalog_bytes(*, shell_enabled: bool, web_enabled: bool) -> bytes:
    return ("shell_tool under development " + str(shell_enabled).lower() + "\nweb_search stable " + str(web_enabled).lower() + "\n").encode()


def test_feature_catalog_parser_handles_multiword_stage_and_exact_count() -> None:
    catalog = parse_codex_feature_catalog(
        _catalog_bytes(shell_enabled=True, web_enabled=False),
        expected_count=2,
    )

    assert tuple(entry.name for entry in catalog) == ("shell_tool", "web_search")
    assert catalog[0].stage == "under development"
    with pytest.raises(ValueError, match="row count"):
        parse_codex_feature_catalog(
            _catalog_bytes(shell_enabled=True, web_enabled=False),
            expected_count=3,
        )
    with pytest.raises(ValueError, match="invalid feature name"):
        parse_codex_feature_catalog(
            b"shell-tool stable false\n",
            expected_count=1,
        )


def test_feature_gate_requires_complete_disable_coverage() -> None:
    baseline = parse_codex_feature_catalog(
        _catalog_bytes(shell_enabled=True, web_enabled=True),
        expected_count=2,
    )
    post_disable = parse_codex_feature_catalog(
        _catalog_bytes(shell_enabled=False, web_enabled=False),
        expected_count=2,
    )
    catalog_sha256 = codex_feature_catalog_snapshot_sha256(baseline)
    gate = build_codex_feature_gate(
        baseline,
        post_disable,
        active_feature_allowlist=(),
        expected_feature_catalog_sha256=catalog_sha256,
    )

    assert gate.disabled_features == ("shell_tool", "web_search")
    assert gate.post_disable_effective_true_features == ()
    with pytest.raises(ValueError, match="exceeds the allowlist"):
        build_codex_feature_gate(
            baseline,
            baseline,
            active_feature_allowlist=(),
            expected_feature_catalog_sha256=catalog_sha256,
        )


def test_feature_gate_rejects_missing_row_and_catalog_anchor_drift() -> None:
    baseline = parse_codex_feature_catalog(
        _catalog_bytes(shell_enabled=True, web_enabled=True),
        expected_count=2,
    )
    missing = parse_codex_feature_catalog(
        b"shell_tool under development false\n",
        expected_count=1,
    )
    with pytest.raises(RuntimeError, match="definition drifted"):
        build_codex_feature_gate(
            baseline,
            missing,
            active_feature_allowlist=(),
            expected_feature_catalog_sha256=(codex_feature_catalog_snapshot_sha256(baseline)),
        )
    with pytest.raises(RuntimeError, match="external trust anchor"):
        build_codex_feature_gate(
            baseline,
            baseline,
            active_feature_allowlist=("shell_tool", "web_search"),
            expected_feature_catalog_sha256="0" * 64,
        )


def test_pilot_sandbox_must_be_empty_and_outside_repository(tmp_path) -> None:
    identity = pilot_sandbox_identity_sha256(str(tmp_path))
    assert len(identity) == 64

    (tmp_path / "AGENTS.md").write_text("must not be visible", encoding="utf-8")
    with pytest.raises(ValueError, match="must be empty"):
        pilot_sandbox_identity_sha256(str(tmp_path))

    repository_root = __file__.replace("\\", "/").rsplit("/v2/", 1)[0]
    with pytest.raises(ValueError, match="outside the repository"):
        pilot_sandbox_identity_sha256(repository_root)


class _FakeLocalRunner:
    def __init__(self, baseline: bytes, post_disable: bytes) -> None:
        self.baseline = baseline
        self.post_disable = post_disable
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: tuple[str, ...]) -> LocalCommandCapture:
        self.calls.append(argv)
        if argv[-2:] == ("features", "list"):
            stdout = self.post_disable if "--disable" in argv else self.baseline
            return LocalCommandCapture(argv, stdout, b"", 0)
        if argv[-2:] == ("exec", "--help"):
            return LocalCommandCapture(argv, b"Usage: codex exec [OPTIONS]\n", b"", 0)
        if argv[-1:] == ("--version",):
            return LocalCommandCapture(argv, b"codex-cli 0.144.1\n", b"", 0)
        if argv[-2:] == ("login", "status"):
            return LocalCommandCapture(argv, b"", b"Logged in using ChatGPT\n", 0)
        raise AssertionError(f"unexpected provider-free command: {argv}")


def test_zero_call_capture_is_reversible_and_global_flags_precede_exec(tmp_path) -> None:
    baseline = "".join(f"feature_{index:02d} stable {'true' if index < 2 else 'false'}\n" for index in range(92)).encode()
    post_disable = "".join(f"feature_{index:02d} stable false\n" for index in range(92)).encode()
    baseline_catalog = parse_codex_feature_catalog(baseline)
    runner = _FakeLocalRunner(baseline, post_disable)

    summary, raw_artifacts = capture_zero_call_preflight(
        "codex.exe",
        expected_catalog_sha256=codex_feature_catalog_snapshot_sha256(baseline_catalog),
        expected_definition_sha256=codex_feature_catalog_definition_sha256(baseline_catalog),
        runner=runner,
    )

    assert summary["provider_calls"] == 0
    assert summary["post_disable_effective_true_features"] == []
    help_argv = next(argv for argv in runner.calls if "exec" in argv)
    assert help_argv == ("codex.exe", "--disable", "shell_tool", "exec", "--help")
    assert all("exec" not in argv or argv[-1] == "--help" for argv in runner.calls)

    written = write_zero_call_preflight(str(tmp_path), summary, raw_artifacts)
    assert len(written) == 4
    baseline_artifact = tmp_path / "r01-b2-codex-features-baseline.raw.b64"
    assert base64.b64decode(baseline_artifact.read_bytes(), validate=True) == baseline
    with pytest.raises(FileExistsError):
        write_zero_call_preflight(str(tmp_path), summary, raw_artifacts)


def test_subprocess_preflight_runner_rejects_provider_acquisition() -> None:
    with pytest.raises(ValueError, match="provider-free allowlist"):
        SubprocessLocalCommandRunner().run(("codex.exe", "exec", "-"))


def test_subprocess_preflight_runner_has_bounded_timeout(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run(argv, *, capture_output, check, timeout):
        observed.update(
            capture_output=capture_output,
            check=check,
            timeout=timeout,
        )
        raise subprocess.TimeoutExpired(argv, timeout)

    monkeypatch.setattr(codex_preflight.subprocess, "run", fake_run)
    with pytest.raises(TimeoutError, match="timed out"):
        SubprocessLocalCommandRunner().run(("codex.exe", "--version"))
    assert observed == {
        "capture_output": True,
        "check": False,
        "timeout": LOCAL_COMMAND_TIMEOUT_SECONDS,
    }
