"""Read-only verifier for the provider-free R02 D4-S1 commitment stage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import GeneratorConfig
from v2.research.overlay.r02_d4_s1_seed import (
    R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
    R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_PATH,
    R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
    R02_D4_S1_GENERATOR_CONFIG_SHA256,
    R02_D4_S1_SEED_CONTRACT_PATH,
    R02_D4_S1_SEED_CONTRACT_SHA256,
    pinned_preimage_fields,
    validate_coordinator_commitment_record,
)


class R02D4S1VerificationError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S1VerificationError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S1VerificationError(code)


def verify_s1(repo_root: Path) -> dict[str, Any]:
    design_path = repo_root / R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_PATH
    contract_path = repo_root / R02_D4_S1_SEED_CONTRACT_PATH
    intent_path = repo_root / "docs" / "r02-d4-s1-seed-intent.json"
    commitment_path = repo_root / "docs" / "r02-d4-s1-coordinator-commitment.json"
    _require_equal(
        _sha256_file(design_path),
        R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
        "ACCEPTED_DESIGN_MANIFEST_SHA256_MISMATCH",
    )
    _require_equal(
        _sha256_file(contract_path),
        R02_D4_S1_SEED_CONTRACT_SHA256,
        "SEED_CONTRACT_SHA256_MISMATCH",
    )
    contract = _read_json(contract_path)
    expected_template = {
        **pinned_preimage_fields(),
        "accepted_design_commit": None,
        "accepted_design_manifest_sha256": None,
        "generator_config_sha256": None,
        "coordinator_nonce_commitment_sha256": None,
        "coordinator_nonce_reveal_hex": None,
        "reviewer_nonce_commitment_sha256": None,
        "reviewer_nonce_reveal_hex": None,
    }
    _require_equal(
        contract.get("preimage_template"),
        expected_template,
        "SEED_CONTRACT_PREIMAGE_TEMPLATE_MISMATCH",
    )
    intent = _read_json(intent_path)
    commitment = _read_json(commitment_path)
    validate_coordinator_commitment_record(commitment)
    _require_equal(
        intent.get("accepted_design_commit"),
        R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
        "INTENT_ACCEPTED_DESIGN_COMMIT_MISMATCH",
    )
    _require_equal(
        intent.get("accepted_design_manifest", {}).get("sha256"),
        R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
        "INTENT_ACCEPTED_DESIGN_MANIFEST_MISMATCH",
    )
    _require_equal(
        intent.get("generator_config", {}).get("sha256"),
        R02_D4_S1_GENERATOR_CONFIG_SHA256,
        "INTENT_GENERATOR_CONFIG_MISMATCH",
    )
    _require_equal(
        canonical_sha256(GeneratorConfig()),
        R02_D4_S1_GENERATOR_CONFIG_SHA256,
        "CURRENT_GENERATOR_CONFIG_SHA256_MISMATCH",
    )
    _require_equal(
        commitment.get("intent_sha256"),
        _sha256_file(intent_path),
        "COORDINATOR_COMMITMENT_INTENT_SHA256_MISMATCH",
    )
    _require_equal(
        commitment.get("accepted_design_commit"),
        R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
        "COORDINATOR_COMMITMENT_DESIGN_COMMIT_MISMATCH",
    )
    _require_equal(
        commitment.get("accepted_design_manifest_sha256"),
        R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
        "COORDINATOR_COMMITMENT_DESIGN_MANIFEST_MISMATCH",
    )
    _require_equal(
        commitment.get("generator_config_sha256"),
        R02_D4_S1_GENERATOR_CONFIG_SHA256,
        "COORDINATOR_COMMITMENT_GENERATOR_CONFIG_MISMATCH",
    )
    return {
        "schema_version": "r02-d4-s1-seed-verification-v1",
        "status": "PASS_COORDINATOR_COMMITMENT_SEALED",
        "accepted_design_commit": R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
        "accepted_design_manifest_sha256": (
            R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256
        ),
        "generator_config_sha256": R02_D4_S1_GENERATOR_CONFIG_SHA256,
        "coordinator_nonce_commitment_sha256": commitment[
            "coordinator_nonce_commitment_sha256"
        ],
        "reviewer_nonce_commitment_sha256": None,
        "coordinator_nonce_reveal_hex": None,
        "reviewer_nonce_reveal_hex": None,
        "resolved_frame_seed_sha256": None,
        "provider_calls": 0,
        "frame_generation": False,
        "frame_scan": False,
        "live_execution": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = verify_s1(args.repo_root.resolve())
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
