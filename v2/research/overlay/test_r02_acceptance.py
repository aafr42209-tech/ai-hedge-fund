from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .r02_contracts import (
    R02_ACCEPTED_COMMIT,
    R02_FREEZE_SHA256,
    R02_MANIFEST_SHA256,
)

ROOT = Path(__file__).resolve().parents[3]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_d1_acceptance_pins_immutable_freeze_and_manifest() -> None:
    record = json.loads(
        (ROOT / "docs" / "r02-d1-final-acceptance.json").read_text(encoding="utf-8")
    )
    assert record["status"] == "R2_D1_FINAL_ACCEPTED"
    assert record["accepted_commit"] == R02_ACCEPTED_COMMIT
    assert record["freeze_spec_sha256"] == R02_FREEZE_SHA256
    assert record["freeze_manifest_sha256"] == R02_MANIFEST_SHA256
    assert _sha256(ROOT / "docs" / "r02-d1-candidate-trigger-freeze.json") == R02_FREEZE_SHA256
    assert _sha256(ROOT / "docs" / "r02-d1-freeze-manifest.json") == R02_MANIFEST_SHA256


def test_d2a_authorization_remains_provider_free_and_non_live() -> None:
    record = json.loads(
        (ROOT / "docs" / "r02-d1-final-acceptance.json").read_text(encoding="utf-8")
    )
    authorization = record["authorization"]
    assert authorization["r2_d2a_provider_free_production_implementation"] is True
    assert authorization["offline_tests"] is True
    for forbidden in (
        "provider_calls",
        "live_execution",
        "zero_call_preflight_finalization",
        "statistical_freeze",
        "provider_budget_freeze",
    ):
        assert authorization[forbidden] is False


def test_frozen_r01_source_identities_are_unchanged() -> None:
    freeze = json.loads(
        (ROOT / "docs" / "r02-d1-candidate-trigger-freeze.json").read_text(encoding="utf-8")
    )
    identity = freeze["source_identity"]
    paths = {
        "primary_baseline_source_sha256": "v2/research/overlay/baselines.py",
        "validator_source_sha256": "v2/research/overlay/validator.py",
        "contracts_source_sha256": "v2/research/overlay/contracts.py",
        "scoring_source_sha256": "v2/research/overlay/scoring.py",
        "lattice_source_sha256": "v2/research/overlay/lattice.py",
    }
    for field, relative_path in paths.items():
        assert _sha256(ROOT / relative_path) == identity[field]


def test_d2a_modules_have_no_provider_or_live_client_imports() -> None:
    for filename in (
        "r02_contracts.py",
        "r02_candidates.py",
        "r02_audit.py",
        "r02_replay.py",
    ):
        source = (ROOT / "v2" / "research" / "overlay" / filename).read_text(
            encoding="utf-8"
        )
        assert "codex_exec_client" not in source
        assert "llm_policy" not in source
        assert "from openai" not in source
