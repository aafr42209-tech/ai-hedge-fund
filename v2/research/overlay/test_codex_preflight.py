from __future__ import annotations

import pytest

from .codex_preflight import (
    build_codex_feature_gate,
    parse_codex_feature_catalog,
    pilot_sandbox_identity_sha256,
)
from .contracts import codex_feature_catalog_snapshot_sha256


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
