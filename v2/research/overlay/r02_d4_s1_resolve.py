"""Provider-free validation and sealing rules for R02 D4-S1 slot-zero seed.

This module accepts only the already committed and revealed nonce pair.  It
contains no nonce generator, alternate slot, frame builder, frame scanner,
provider, network, subprocess, or LIVE capability.
"""

from __future__ import annotations

from typing import Any, Mapping

from .canonical import canonical_sha256
from .r02_d4_s1_reveal import (
    R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
    R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH,
    R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256,
    R02_D4_S1_REVIEWER_COMMITMENT_SHA256,
    validate_reveal_matches_commitment,
)
from .r02_d4_s1_seed import (
    R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
    R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
    R02_D4_S1_GENERATOR_CONFIG_SHA256,
    R02_D4_S1_SEED_SLOT,
    build_resolved_preimage,
)

R02_D4_S1_COORDINATOR_REVEAL_ARTIFACT_PATH = (
    "docs/r02-d4-s1-coordinator-reveal.json"
)
R02_D4_S1_COORDINATOR_REVEAL_ARTIFACT_SHA256 = (
    "a674c1ae1852b51650b680916ce6c5dbdb8d652384bae1a6209c970558e0c8a5"
)
R02_D4_S1_REVIEWER_REVEAL_ARTIFACT_PATH = (
    "docs/r02-d4-s1-reviewer-reveal.json"
)
R02_D4_S1_REVIEWER_REVEAL_ARTIFACT_SHA256 = (
    "52227dcbcc3c8754a95a425172fc9f31479f62b5b4155ae5c1ed15995c198ec0"
)
R02_D4_S1_COORDINATOR_REVEAL_ZERO_CALL_MANIFEST_SHA256 = (
    "9775488293d9a590e754e5e5d6a7d53c3e881e35c735e12370eb4add65b16d7a"
)


class R02D4S1ResolveError(RuntimeError):
    """Raised when the accepted seed preimage or closeout record drifts."""


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S1ResolveError(code)


def _validate_zero_boundaries(record: Mapping[str, Any], prefix: str) -> None:
    _require_equal(record.get("provider_calls"), 0, f"{prefix}_PROVIDER_BOUNDARY_MISMATCH")
    for field in ("frame_generation", "frame_scan", "live_execution"):
        _require_equal(record.get(field), False, f"{prefix}_{field.upper()}_BOUNDARY_MISMATCH")
    _require_equal(record.get("resolved_frame_id"), None, f"{prefix}_PREMATURE_FRAME_ID")
    _require_equal(record.get("retry_cap"), 0, f"{prefix}_RETRY_CAP_MISMATCH")
    _require_equal(record.get("replacement_cap"), 0, f"{prefix}_REPLACEMENT_CAP_MISMATCH")
    _require_equal(record.get("alternate_seed_slots"), 0, f"{prefix}_ALTERNATE_SLOT_MISMATCH")


def validate_reviewer_reveal_record(record: Mapping[str, Any]) -> None:
    """Validate sequence ordinal four without calculating the final seed."""

    _require_equal(
        record.get("schema_version"),
        "r02-d4-s1-reviewer-reveal-v1",
        "REVIEWER_REVEAL_SCHEMA_MISMATCH",
    )
    _require_equal(
        record.get("status"),
        "REVIEWER_REVEAL_SEALED_SEED_DERIVATION_PENDING",
        "REVIEWER_REVEAL_STATUS_MISMATCH",
    )
    _require_equal(record.get("sequence_ordinal"), 4, "REVIEWER_REVEAL_SEQUENCE_MISMATCH")
    _require_equal(
        record.get("coordinator_reveal_artifact_path"),
        R02_D4_S1_COORDINATOR_REVEAL_ARTIFACT_PATH,
        "REVIEWER_REVEAL_COORDINATOR_ARTIFACT_PATH_MISMATCH",
    )
    _require_equal(
        record.get("coordinator_reveal_artifact_sha256"),
        R02_D4_S1_COORDINATOR_REVEAL_ARTIFACT_SHA256,
        "REVIEWER_REVEAL_COORDINATOR_ARTIFACT_SHA256_MISMATCH",
    )
    _require_equal(
        record.get("reviewer_commitment_artifact_path"),
        R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH,
        "REVIEWER_REVEAL_COMMITMENT_ARTIFACT_PATH_MISMATCH",
    )
    _require_equal(
        record.get("reviewer_commitment_artifact_sha256"),
        R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256,
        "REVIEWER_REVEAL_COMMITMENT_ARTIFACT_SHA256_MISMATCH",
    )
    expected = {
        "accepted_design_commit": R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
        "accepted_design_manifest_sha256": R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
        "generator_config_sha256": R02_D4_S1_GENERATOR_CONFIG_SHA256,
        "seed_slot": R02_D4_S1_SEED_SLOT,
        "coordinator": "CODEX",
        "reviewer": "CLAUDE",
        "commitment_algorithm": "SHA256_RAW_32_BYTE_NONCE",
        "nonce_byte_length": 32,
        "coordinator_nonce_commitment_sha256": R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
        "reviewer_nonce_commitment_sha256": R02_D4_S1_REVIEWER_COMMITMENT_SHA256,
        "reviewer_reveal_commitment_match": True,
        "reviewer_reveal_count": 1,
        "reviewer_escrow_blob_sha256": (
            "04b9b87c83845b5719118bc8efe4549d276609ef492378ef47e464f606faeccd"
        ),
        "frame_seed_created": False,
        "resolved_frame_seed_sha256": None,
    }
    for field, value in expected.items():
        _require_equal(record.get(field), value, f"REVIEWER_REVEAL_FIELD_MISMATCH:{field}")
    _validate_zero_boundaries(record, "REVIEWER_REVEAL")
    validate_reveal_matches_commitment(
        record.get("coordinator_nonce_reveal_hex"),
        R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
        "COORDINATOR",
    )
    validate_reveal_matches_commitment(
        record.get("reviewer_nonce_reveal_hex"),
        R02_D4_S1_REVIEWER_COMMITMENT_SHA256,
        "REVIEWER",
    )


def build_verified_preimage(record: Mapping[str, Any]) -> dict[str, str | int]:
    """Construct the frozen preimage after validating both one-shot reveals."""

    validate_reviewer_reveal_record(record)
    return build_resolved_preimage(
        coordinator_nonce_commitment_sha256=R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
        reviewer_nonce_commitment_sha256=R02_D4_S1_REVIEWER_COMMITMENT_SHA256,
        coordinator_nonce_reveal_hex=str(record["coordinator_nonce_reveal_hex"]),
        reviewer_nonce_reveal_hex=str(record["reviewer_nonce_reveal_hex"]),
    )


def validate_resolved_seed_record(
    record: Mapping[str, Any], reviewer_reveal: Mapping[str, Any]
) -> None:
    """Reproduce a sealed seed identity without enabling downstream frame work."""

    _require_equal(
        record.get("schema_version"),
        "r02-d4-s1-resolved-seed-v1",
        "RESOLVED_SEED_SCHEMA_MISMATCH",
    )
    _require_equal(
        record.get("status"),
        "SEED_SLOT_ZERO_RESOLVED_AND_SEALED_FRAME_NOT_AUTHORIZED",
        "RESOLVED_SEED_STATUS_MISMATCH",
    )
    _require_equal(record.get("seed_slot"), 0, "RESOLVED_SEED_SLOT_MISMATCH")
    _require_equal(record.get("seed_derivation_count"), 1, "RESOLVED_SEED_COUNT_MISMATCH")
    _require_equal(record.get("frame_seed_created"), True, "RESOLVED_SEED_CREATED_FLAG_MISMATCH")
    _validate_zero_boundaries(record, "RESOLVED_SEED")
    expected_preimage = build_verified_preimage(reviewer_reveal)
    _require_equal(record.get("preimage"), expected_preimage, "RESOLVED_SEED_PREIMAGE_MISMATCH")
    expected_digest = canonical_sha256(expected_preimage)
    _require_equal(
        record.get("resolved_frame_seed_sha256"),
        expected_digest,
        "RESOLVED_SEED_DIGEST_MISMATCH",
    )
    _require_equal(
        record.get("reviewer_reveal_artifact_sha256"),
        R02_D4_S1_REVIEWER_REVEAL_ARTIFACT_SHA256,
        "RESOLVED_SEED_REVIEWER_REVEAL_ARTIFACT_MISMATCH",
    )


def forbidden_capability_names() -> set[str]:
    return {
        "asyncio",
        "http",
        "requests",
        "secrets",
        "socket",
        "subprocess",
        "urllib",
        "codex_exec_client",
        "r02_frame",
        "r02_d3_live_orchestrator",
        "r02_d3_live_selector_adapter",
    }
