"""Read-only verifier for R02 D4-S1 reviewer commitment and reveal stages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import GeneratorConfig
from v2.research.overlay.r02_d4_s1_reveal import (
    R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_PATH,
    R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_SHA256,
    R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
    R02_D4_S1_PRIOR_ZERO_CALL_MANIFEST_SHA256,
    R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH,
    R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256,
    R02_D4_S1_REVIEWER_COMMITMENT_SHA256,
    validate_coordinator_reveal_record,
    validate_reviewer_commitment_record,
)
from v2.research.overlay.r02_d4_s1_seed import (
    R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
    R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_PATH,
    R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
    R02_D4_S1_GENERATOR_CONFIG_SHA256,
    R02_D4_S1_SEED_CONTRACT_PATH,
    R02_D4_S1_SEED_CONTRACT_SHA256,
)


class R02D4S1RevealVerificationError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S1RevealVerificationError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_hash(repo_root: Path, relative_path: str, expected: str) -> None:
    if _sha256_file(repo_root / relative_path) != expected:
        raise R02D4S1RevealVerificationError(f"ARTIFACT_SHA256_MISMATCH:{relative_path}")


def _verify_static_lineage(repo_root: Path) -> dict[str, Any]:
    expected = {
        R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_PATH: (
            R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256
        ),
        R02_D4_S1_SEED_CONTRACT_PATH: R02_D4_S1_SEED_CONTRACT_SHA256,
        "docs/r02-d4-s1-seed-intent.json": (
            "638a8a0a5de3718576fee7446e064282fa871f18b335364c0294ec831cdd016e"
        ),
        R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_PATH: (
            R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_SHA256
        ),
        "docs/r02-d4-s1-zero-call-manifest.json": (
            R02_D4_S1_PRIOR_ZERO_CALL_MANIFEST_SHA256
        ),
        R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH: (
            R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256
        ),
        "docs/r02-d3-successor-provider-free-posthoc.json": (
            "1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73"
        ),
    }
    for relative_path, digest in expected.items():
        _require_hash(repo_root, relative_path, digest)
    if canonical_sha256(GeneratorConfig()) != R02_D4_S1_GENERATOR_CONFIG_SHA256:
        raise R02D4S1RevealVerificationError("CURRENT_GENERATOR_CONFIG_SHA256_MISMATCH")
    reviewer = _read_json(repo_root / R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH)
    validate_reviewer_commitment_record(reviewer)
    return reviewer


def verify_reveal_stage(repo_root: Path, stage: str) -> dict[str, Any]:
    _verify_static_lineage(repo_root)
    result: dict[str, Any] = {
        "schema_version": "r02-d4-s1-reveal-verification-v1",
        "accepted_design_commit": R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
        "accepted_design_manifest_sha256": R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
        "generator_config_sha256": R02_D4_S1_GENERATOR_CONFIG_SHA256,
        "coordinator_nonce_commitment_sha256": R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
        "reviewer_nonce_commitment_sha256": R02_D4_S1_REVIEWER_COMMITMENT_SHA256,
        "reviewer_nonce_reveal_hex": None,
        "resolved_frame_seed_sha256": None,
        "provider_calls": 0,
        "frame_generation": False,
        "frame_scan": False,
        "live_execution": False,
    }
    if stage == "reviewer-commitment":
        result.update(
            status="PASS_REVIEWER_COMMITMENT_SEALED",
            coordinator_nonce_reveal_hex=None,
            coordinator_reveal_commitment_match=None,
        )
        return result
    coordinator_path = repo_root / "docs" / "r02-d4-s1-coordinator-reveal.json"
    coordinator = _read_json(coordinator_path)
    validate_coordinator_reveal_record(coordinator)
    result.update(
        status="PASS_COORDINATOR_REVEAL_SEALED",
        coordinator_nonce_reveal_hex="PRESENT_REDACTED_FROM_VERIFIER_OUTPUT",
        coordinator_reveal_commitment_match=True,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("reviewer-commitment", "coordinator-reveal"),
        required=True,
    )
    args = parser.parse_args(argv)
    result = verify_reveal_stage(args.repo_root.resolve(), args.stage)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
