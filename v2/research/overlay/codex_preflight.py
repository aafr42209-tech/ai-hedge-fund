"""Provider-free Codex feature and isolation gates for R01 Phase B2."""

from __future__ import annotations

import base64
import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .canonical import canonical_json_bytes
from .contracts import (
    CodexFeatureCatalogEntry,
    CodexFeatureGate,
    codex_feature_catalog_definition_sha256,
    codex_feature_catalog_snapshot_sha256,
    codex_pilot_sandbox_identity_sha256,
)

PINNED_CODEX_FEATURE_CATALOG_COUNT = 92
FEATURE_NAME = re.compile(r"^[a-z0-9_]+$")
ZERO_CALL_CAPTURE_FILENAMES = {
    "baseline_features": "r01-b2-codex-features-baseline.raw.b64",
    "post_disable_features": "r01-b2-codex-features-post-disable.raw.b64",
    "global_disable_help": "r01-b2-codex-global-disable-help.raw.b64",
    "summary": "r01-b2-zero-call-capture.json",
}


@dataclass(frozen=True)
class LocalCommandCapture:
    argv: tuple[str, ...]
    stdout: bytes
    stderr: bytes
    exit_code: int


class LocalCommandRunner(Protocol):
    def run(self, argv: tuple[str, ...]) -> LocalCommandCapture:
        ...


class SubprocessLocalCommandRunner:
    """Run only the explicit provider-free commands assembled below."""

    def run(self, argv: tuple[str, ...]) -> LocalCommandCapture:
        if not _is_provider_free_command(argv):
            raise ValueError("command is outside the B2 provider-free allowlist")
        completed = subprocess.run(argv, capture_output=True, check=False)
        return LocalCommandCapture(
            argv=argv,
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
        )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_provider_free_command(argv: tuple[str, ...]) -> bool:
    if len(argv) < 2 or not argv[0]:
        return False
    arguments = argv[1:]
    if arguments in {
        ("--version",),
        ("login", "status"),
        ("features", "list"),
        ("--disable", "shell_tool", "exec", "--help"),
    }:
        return True
    if len(arguments) < 4 or arguments[-2:] != ("features", "list"):
        return False
    disable_arguments = arguments[:-2]
    if len(disable_arguments) % 2:
        return False
    names: list[str] = []
    for index in range(0, len(disable_arguments), 2):
        flag, name = disable_arguments[index : index + 2]
        if flag != "--disable" or FEATURE_NAME.fullmatch(name) is None:
            return False
        names.append(name)
    return len(names) == len(set(names))


def _require_success(capture: LocalCommandCapture, label: str) -> None:
    if capture.exit_code != 0:
        raise RuntimeError(f"provider-free {label} command failed")


def capture_zero_call_preflight(
    executable: str,
    *,
    expected_catalog_sha256: str,
    expected_definition_sha256: str,
    runner: LocalCommandRunner,
) -> tuple[dict[str, object], dict[str, bytes]]:
    """Capture the pinned B2 local facts without issuing a model request."""

    baseline = runner.run((executable, "features", "list"))
    _require_success(baseline, "baseline feature catalog")
    baseline_catalog = parse_codex_feature_catalog(baseline.stdout)
    actual_catalog_sha256 = codex_feature_catalog_snapshot_sha256(baseline_catalog)
    actual_definition_sha256 = codex_feature_catalog_definition_sha256(baseline_catalog)
    if actual_catalog_sha256 != expected_catalog_sha256:
        raise RuntimeError("feature catalog differs from the B2 snapshot anchor")
    if actual_definition_sha256 != expected_definition_sha256:
        raise RuntimeError("feature catalog definition differs from the B2 anchor")

    disable_argv = [executable]
    for entry in baseline_catalog:
        disable_argv.extend(("--disable", entry.name))
    disable_argv.extend(("features", "list"))
    post_disable = runner.run(tuple(disable_argv))
    _require_success(post_disable, "post-disable feature catalog")
    post_disable_catalog = parse_codex_feature_catalog(post_disable.stdout)
    if codex_feature_catalog_definition_sha256(post_disable_catalog) != actual_definition_sha256:
        raise RuntimeError("post-disable feature catalog definition drifted")

    global_disable_help = runner.run((executable, "--disable", "shell_tool", "exec", "--help"))
    _require_success(global_disable_help, "global disable help")
    if b"Usage: codex exec" not in global_disable_help.stdout:
        raise RuntimeError("global --disable placement was not accepted by the pinned CLI")

    version = runner.run((executable, "--version"))
    _require_success(version, "version")
    login = runner.run((executable, "login", "status"))
    _require_success(login, "login status")
    login_text = (login.stdout + b"\n" + login.stderr).decode("utf-8", errors="strict").strip()
    if login_text != "Logged in using ChatGPT":
        raise RuntimeError("authentication mode is not the pinned ChatGPT mode")

    raw_artifacts = {
        "baseline_features": baseline.stdout,
        "post_disable_features": post_disable.stdout,
        "global_disable_help": global_disable_help.stdout,
    }
    summary: dict[str, object] = {
        "schema_version": "r01-b2-zero-call-capture-v1",
        "provider_calls": 0,
        "evaluation_fixtures_generated": 0,
        "codex_cli_version": version.stdout.decode("utf-8", errors="strict").strip(),
        "authentication_mode": "ChatGPT",
        "feature_catalog_count": len(baseline_catalog),
        "feature_catalog_sha256": actual_catalog_sha256,
        "feature_catalog_definition_sha256": actual_definition_sha256,
        "baseline_effective_true_features": [entry.name for entry in baseline_catalog if entry.enabled],
        "disabled_features": [entry.name for entry in baseline_catalog],
        "post_disable_effective_true_features": [entry.name for entry in post_disable_catalog if entry.enabled],
        "global_disable_before_exec_help_verified": True,
        "raw_sha256": {key: _sha256(value) for key, value in sorted(raw_artifacts.items())},
        "raw_encoding": "base64 of exact captured bytes; artifact files have no trailing newline",
    }
    return summary, raw_artifacts


def write_zero_call_preflight(
    output_directory: str,
    summary: dict[str, object],
    raw_artifacts: dict[str, bytes],
) -> tuple[Path, ...]:
    """Write exact reversible captures and the canonical summary exclusively."""

    output = Path(output_directory)
    if not output.is_absolute() or not output.is_dir():
        raise ValueError("output directory must be an existing absolute directory")
    if set(raw_artifacts) != {
        "baseline_features",
        "post_disable_features",
        "global_disable_help",
    }:
        raise ValueError("raw artifact set differs from the B2 capture contract")
    payloads = {ZERO_CALL_CAPTURE_FILENAMES[key]: base64.b64encode(value) for key, value in raw_artifacts.items()}
    payloads[ZERO_CALL_CAPTURE_FILENAMES["summary"]] = canonical_json_bytes(summary)
    written: list[Path] = []
    for name, payload in sorted(payloads.items()):
        destination = output / name
        with destination.open("xb") as handle:
            handle.write(payload)
        written.append(destination)
    return tuple(written)


def parse_codex_feature_catalog(
    raw: bytes,
    *,
    expected_count: int = PINNED_CODEX_FEATURE_CATALOG_COUNT,
) -> tuple[CodexFeatureCatalogEntry, ...]:
    """Parse every `codex features list` row without fixed-width assumptions."""

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("feature catalog is not valid UTF-8") from exc
    lines = text.rstrip("\r\n").splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise ValueError("feature catalog contains no rows or an empty row")
    entries: list[CodexFeatureCatalogEntry] = []
    for line_number, line in enumerate(lines, start=1):
        tokens = line.split()
        if len(tokens) < 3 or tokens[-1] not in {"true", "false"}:
            raise ValueError(f"unparsed feature catalog row {line_number}")
        if FEATURE_NAME.fullmatch(tokens[0]) is None:
            raise ValueError(f"invalid feature name on catalog row {line_number}")
        entries.append(
            CodexFeatureCatalogEntry(
                name=tokens[0],
                stage=" ".join(tokens[1:-1]),
                enabled=tokens[-1] == "true",
            )
        )
    if len(entries) != expected_count:
        raise ValueError(f"feature catalog row count {len(entries)} != pinned {expected_count}")
    ordered = tuple(sorted(entries, key=lambda entry: entry.name))
    if len({entry.name for entry in ordered}) != len(ordered):
        raise ValueError("feature catalog contains duplicate names")
    return ordered


def build_codex_feature_gate(
    baseline_catalog: tuple[CodexFeatureCatalogEntry, ...],
    post_disable_catalog: tuple[CodexFeatureCatalogEntry, ...],
    *,
    active_feature_allowlist: tuple[str, ...],
    expected_feature_catalog_sha256: str,
) -> CodexFeatureGate:
    """Bind one complete catalog and reject any post-disable feature escape."""

    baseline = tuple(sorted(baseline_catalog, key=lambda entry: entry.name))
    post_disable = tuple(sorted(post_disable_catalog, key=lambda entry: entry.name))
    actual_catalog_sha256 = codex_feature_catalog_snapshot_sha256(baseline)
    if actual_catalog_sha256 != expected_feature_catalog_sha256:
        raise RuntimeError("feature catalog differs from the external trust anchor")
    catalog_definition_sha256 = codex_feature_catalog_definition_sha256(baseline)
    if catalog_definition_sha256 != codex_feature_catalog_definition_sha256(post_disable):
        raise RuntimeError("post-disable feature catalog definition drifted")
    allowlist = tuple(sorted(set(active_feature_allowlist)))
    if len(allowlist) != len(active_feature_allowlist):
        raise ValueError("active feature allowlist contains duplicates")
    catalog_names = tuple(entry.name for entry in baseline)
    if not set(allowlist).issubset(catalog_names):
        raise ValueError("active feature allowlist contains an unknown feature")
    disabled = tuple(sorted(set(catalog_names) - set(allowlist)))
    post_true = tuple(entry.name for entry in post_disable if entry.enabled)
    return CodexFeatureGate(
        feature_catalog=baseline,
        feature_catalog_sha256=actual_catalog_sha256,
        feature_catalog_definition_sha256=catalog_definition_sha256,
        baseline_effective_true_features=tuple(entry.name for entry in baseline if entry.enabled),
        active_feature_allowlist=allowlist,
        disabled_features=disabled,
        post_disable_effective_true_features=post_true,
    )


def pilot_sandbox_identity_sha256(working_directory: str) -> str:
    """Validate one empty out-of-repository sandbox and return its identity."""

    directory = Path(working_directory)
    if not directory.is_absolute() or not directory.is_dir():
        raise ValueError("pilot sandbox must be an existing absolute directory")
    if directory.is_symlink():
        raise ValueError("pilot sandbox cannot be a symbolic link")
    resolved = directory.resolve()
    repository_root = Path(__file__).resolve().parents[3]
    if resolved == repository_root or repository_root in resolved.parents:
        raise ValueError("pilot sandbox must be outside the repository tree")
    entries = tuple(sorted(path.name for path in resolved.iterdir()))
    if entries:
        raise ValueError("pilot sandbox must be empty before every launch")
    return codex_pilot_sandbox_identity_sha256(str(resolved))
