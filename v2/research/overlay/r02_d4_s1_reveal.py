"""Provider-free state validation for R02 D4-S1 reveal stages.

The accepted coordinator and reviewer commitment artifacts are immutable inputs
to this module.  It validates ordering and commitment equality only.  It does
not generate nonces, resolve a seed before both reveals, build or scan frames,
call providers, launch processes, or authorize LIVE execution.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from .r02_d4_s1_seed import (
    R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
    R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
    R02_D4_S1_GENERATOR_CONFIG_SHA256,
    R02_D4_S1_SEED_SLOT,
    R02D4S1SeedError,
    nonce_commitment_sha256,
)

R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_PATH = (
    "docs/r02-d4-s1-coordinator-commitment.json"
)
R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_SHA256 = (
    "7ea3288a36424f939d295ec2e96751b33908a82dba78818cfdd16adbdd0687fe"
)
R02_D4_S1_COORDINATOR_COMMITMENT_SHA256 = (
    "7d2f9653b12d3b3ad6746ea067829b1b5222564821ace311f1f7fb98550fb5d3"
)
R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH = (
    "docs/r02-d4-s1-reviewer-commitment.json"
)
R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256 = (
    "2c93c329e30693ea3de99f9114f1f16af9282acfaff6b2b49e2e555438092215"
)
R02_D4_S1_REVIEWER_COMMITMENT_SHA256 = (
    "4943ea6a6f990fe88d400d6d3afe880c2634c65a4a842c9d2966d662ee52b144"
)
R02_D4_S1_PRIOR_ZERO_CALL_MANIFEST_SHA256 = (
    "79c8fa298d3268ef2f0abb15408f285f79b83f8914bae4032572f03579639c9b"
)

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class R02D4S1RevealError(RuntimeError):
    """Raised when the one-shot reveal sequence cannot safely continue."""


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S1RevealError(code)


def _require_hex64(value: object, code: str) -> str:
    if not isinstance(value, str) or _HEX_64.fullmatch(value) is None:
        raise R02D4S1RevealError(code)
    return value


def validate_reveal_matches_commitment(
    reveal_hex: object, commitment_sha256: object, role: str
) -> None:
    """Validate a lowercase 32-byte reveal against a raw-byte commitment."""

    reveal = _require_hex64(reveal_hex, f"{role}_REVEAL_HEX_INVALID")
    commitment = _require_hex64(
        commitment_sha256, f"{role}_COMMITMENT_SHA256_INVALID"
    )
    try:
        actual = nonce_commitment_sha256(bytes.fromhex(reveal))
    except R02D4S1SeedError as exc:
        raise R02D4S1RevealError(f"{role}_REVEAL_LENGTH_INVALID") from exc
    if actual != commitment:
        raise R02D4S1RevealError(f"{role}_REVEAL_COMMITMENT_MISMATCH")


def _validate_common_pins(record: Mapping[str, Any], prefix: str) -> None:
    _require_equal(
        record.get("accepted_design_commit"),
        R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
        f"{prefix}_ACCEPTED_DESIGN_COMMIT_MISMATCH",
    )
    _require_equal(
        record.get("accepted_design_manifest_sha256"),
        R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256,
        f"{prefix}_ACCEPTED_DESIGN_MANIFEST_MISMATCH",
    )
    _require_equal(
        record.get("generator_config_sha256"),
        R02_D4_S1_GENERATOR_CONFIG_SHA256,
        f"{prefix}_GENERATOR_CONFIG_MISMATCH",
    )
    _require_equal(
        record.get("seed_slot"),
        R02_D4_S1_SEED_SLOT,
        f"{prefix}_SEED_SLOT_MISMATCH",
    )
    _require_equal(record.get("coordinator"), "CODEX", f"{prefix}_COORDINATOR_MISMATCH")
    _require_equal(record.get("reviewer"), "CLAUDE", f"{prefix}_REVIEWER_MISMATCH")
    _require_equal(
        record.get("commitment_algorithm"),
        "SHA256_RAW_32_BYTE_NONCE",
        f"{prefix}_COMMITMENT_ALGORITHM_MISMATCH",
    )
    _require_equal(record.get("nonce_byte_length"), 32, f"{prefix}_NONCE_LENGTH_MISMATCH")
    _require_equal(
        record.get("coordinator_nonce_commitment_sha256"),
        R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
        f"{prefix}_COORDINATOR_COMMITMENT_MISMATCH",
    )
    _require_equal(
        record.get("reviewer_nonce_commitment_sha256"),
        R02_D4_S1_REVIEWER_COMMITMENT_SHA256,
        f"{prefix}_REVIEWER_COMMITMENT_MISMATCH",
    )


def _validate_zero_boundaries(record: Mapping[str, Any], prefix: str) -> None:
    _require_equal(record.get("provider_calls"), 0, f"{prefix}_PROVIDER_BOUNDARY_MISMATCH")
    for field in ("frame_generation", "frame_scan", "live_execution"):
        _require_equal(record.get(field), False, f"{prefix}_{field.upper()}_BOUNDARY_MISMATCH")
    _require_equal(record.get("frame_seed_created"), False, f"{prefix}_FRAME_SEED_STATE_MISMATCH")
    _require_equal(record.get("resolved_frame_seed_sha256"), None, f"{prefix}_PREMATURE_SEED")
    _require_equal(record.get("resolved_frame_id"), None, f"{prefix}_PREMATURE_FRAME_ID")
    _require_equal(record.get("retry_cap"), 0, f"{prefix}_RETRY_CAP_MISMATCH")
    _require_equal(record.get("replacement_cap"), 0, f"{prefix}_REPLACEMENT_CAP_MISMATCH")


def validate_reviewer_commitment_record(record: Mapping[str, Any]) -> None:
    """Validate sequence ordinal two before coordinator disclosure."""

    _require_equal(
        record.get("schema_version"),
        "r02-d4-s1-reviewer-commitment-v1",
        "REVIEWER_RECORD_SCHEMA_MISMATCH",
    )
    _require_equal(
        record.get("status"),
        "REVIEWER_COMMITMENT_SEALED_COORDINATOR_REVEAL_PENDING",
        "REVIEWER_RECORD_STATUS_MISMATCH",
    )
    _require_equal(record.get("sequence_ordinal"), 2, "REVIEWER_RECORD_SEQUENCE_MISMATCH")
    _require_equal(
        record.get("coordinator_commitment_artifact_path"),
        R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_PATH,
        "REVIEWER_RECORD_COORDINATOR_ARTIFACT_PATH_MISMATCH",
    )
    _require_equal(
        record.get("coordinator_commitment_artifact_sha256"),
        R02_D4_S1_COORDINATOR_COMMITMENT_ARTIFACT_SHA256,
        "REVIEWER_RECORD_COORDINATOR_ARTIFACT_SHA256_MISMATCH",
    )
    _validate_common_pins(record, "REVIEWER_RECORD")
    _validate_zero_boundaries(record, "REVIEWER_RECORD")
    _require_equal(
        record.get("coordinator_nonce_reveal_hex"),
        None,
        "REVIEWER_RECORD_PREMATURE_COORDINATOR_REVEAL",
    )
    _require_equal(
        record.get("reviewer_nonce_reveal_hex"),
        None,
        "REVIEWER_RECORD_PREMATURE_REVIEWER_REVEAL",
    )
    custody = record.get("reviewer_nonce_custody")
    if not isinstance(custody, Mapping):
        raise R02D4S1RevealError("REVIEWER_RECORD_CUSTODY_MISSING")
    _require_equal(
        custody.get("storage"),
        "WINDOWS_DPAPI_CURRENT_USER_OUTSIDE_REPOSITORY",
        "REVIEWER_RECORD_CUSTODY_STORAGE_MISMATCH",
    )
    _require_equal(
        custody.get("dpapi_roundtrip_commitment_match"),
        True,
        "REVIEWER_RECORD_CUSTODY_ROUNDTRIP_MISMATCH",
    )
    _require_equal(
        custody.get("plaintext_nonce_persisted"),
        False,
        "REVIEWER_RECORD_PLAINTEXT_PERSISTED",
    )
    _require_equal(
        custody.get("plaintext_nonce_emitted"),
        False,
        "REVIEWER_RECORD_PLAINTEXT_EMITTED",
    )
    _require_hex64(
        custody.get("protected_blob_sha256"),
        "REVIEWER_RECORD_CUSTODY_BLOB_SHA256_INVALID",
    )
    blob_bytes = custody.get("protected_blob_bytes")
    if not isinstance(blob_bytes, int) or isinstance(blob_bytes, bool) or blob_bytes <= 32:
        raise R02D4S1RevealError("REVIEWER_RECORD_CUSTODY_BLOB_SIZE_INVALID")


def validate_coordinator_reveal_record(record: Mapping[str, Any]) -> None:
    """Validate sequence ordinal three while reviewer reveal stays absent."""

    _require_equal(
        record.get("schema_version"),
        "r02-d4-s1-coordinator-reveal-v1",
        "COORDINATOR_REVEAL_RECORD_SCHEMA_MISMATCH",
    )
    _require_equal(
        record.get("status"),
        "COORDINATOR_REVEAL_SEALED_REVIEWER_REVEAL_PENDING",
        "COORDINATOR_REVEAL_RECORD_STATUS_MISMATCH",
    )
    _require_equal(
        record.get("sequence_ordinal"), 3, "COORDINATOR_REVEAL_RECORD_SEQUENCE_MISMATCH"
    )
    _require_equal(
        record.get("reviewer_commitment_artifact_path"),
        R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH,
        "COORDINATOR_REVEAL_REVIEWER_ARTIFACT_PATH_MISMATCH",
    )
    _require_equal(
        record.get("reviewer_commitment_artifact_sha256"),
        R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256,
        "COORDINATOR_REVEAL_REVIEWER_ARTIFACT_SHA256_MISMATCH",
    )
    _validate_common_pins(record, "COORDINATOR_REVEAL_RECORD")
    _validate_zero_boundaries(record, "COORDINATOR_REVEAL_RECORD")
    _require_equal(
        record.get("reviewer_nonce_reveal_hex"),
        None,
        "COORDINATOR_REVEAL_RECORD_PREMATURE_REVIEWER_REVEAL",
    )
    validate_reveal_matches_commitment(
        record.get("coordinator_nonce_reveal_hex"),
        R02_D4_S1_COORDINATOR_COMMITMENT_SHA256,
        "COORDINATOR",
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
