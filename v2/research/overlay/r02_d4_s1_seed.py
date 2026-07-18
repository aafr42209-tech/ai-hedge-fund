"""Provider-free commit/reveal primitives for R02 D4-S1.

This module validates the single seed slot fixed by the accepted D4 design.  It
does not generate frames, scan seeds, call providers, launch processes, or
authorize LIVE execution.  Nonce generation and custody stay outside this
module so the coordinator and reviewer remain independent parties.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from .canonical import canonical_sha256

R02_D4_S1_SCHEMA_VERSION = "r02-d4-s1-seed-resolution-v1"
R02_D4_S1_DOMAIN = "R02-D4-EXACT-REPLICATION-FRAME-SEED-V1"
R02_D4_S1_SEED_SLOT = 0
R02_D4_S1_ACCEPTED_DESIGN_COMMIT = (
    "d9f984866c8775153d9c1ac1aea9b49fc9647635"
)
R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_PATH = (
    "docs/r02-d4-replication-design.json"
)
R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256 = (
    "784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900"
)
R02_D4_S1_SEED_CONTRACT_PATH = "docs/r02-d4-seed-contract.json"
R02_D4_S1_SEED_CONTRACT_SHA256 = (
    "7b670cc9613a16e6f170b613a3b05a24529699c379bad14cad911736e34792fa"
)
R02_D4_S1_GENERATOR_CONFIG_SHA256 = (
    "e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf"
)
R02_D4_S1_CANDIDATE_GENERATOR_SOURCE_SHA256 = (
    "29c13547230d1729d8b9cec637ccb13335fbcae52c1360e63718359d993a320e"
)
R02_D4_S1_FIXTURE_GENERATOR_SOURCE_SHA256 = (
    "732ca6ff358590edd856ba68bcb6cefb612246da9d81b97aa08d12db786eabfe"
)
R02_D4_S1_R02_D1_FREEZE_SHA256 = (
    "2d5961806b5051ff56c874b8b05933df014136bacb98717c4846f2b48f645778"
)
R02_D4_S1_R02_D1_MANIFEST_SHA256 = (
    "81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf"
)

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class R02D4S1SeedError(RuntimeError):
    """Raised when S1 cannot continue without violating the frozen contract."""


def _require_hex64(value: object, code: str) -> str:
    if not isinstance(value, str) or _HEX_64.fullmatch(value) is None:
        raise R02D4S1SeedError(code)
    return value


def nonce_commitment_sha256(nonce: bytes) -> str:
    """Commit to exactly one raw 32-byte nonce."""

    if type(nonce) is not bytes or len(nonce) != 32:
        raise R02D4S1SeedError("NONCE_MUST_BE_EXACTLY_32_RAW_BYTES")
    return hashlib.sha256(nonce).hexdigest()


def _nonce_from_reveal(reveal_hex: object, role: str) -> bytes:
    value = _require_hex64(reveal_hex, f"{role}_REVEAL_HEX_INVALID")
    nonce = bytes.fromhex(value)
    if len(nonce) != 32:
        raise R02D4S1SeedError(f"{role}_REVEAL_LENGTH_INVALID")
    return nonce


def pinned_preimage_fields() -> dict[str, str | int]:
    """Return every non-interactive field frozen before either nonce exists."""

    return {
        "accepted_design_commit": R02_D4_S1_ACCEPTED_DESIGN_COMMIT,
        "accepted_design_manifest_sha256": (
            R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256
        ),
        "candidate_generator_source_sha256": (
            R02_D4_S1_CANDIDATE_GENERATOR_SOURCE_SHA256
        ),
        "challenge_n": 50,
        "domain": R02_D4_S1_DOMAIN,
        "fixture_generator_source_sha256": (
            R02_D4_S1_FIXTURE_GENERATOR_SOURCE_SHA256
        ),
        "generator_config_sha256": R02_D4_S1_GENERATOR_CONFIG_SHA256,
        "r02_d1_freeze_sha256": R02_D4_S1_R02_D1_FREEZE_SHA256,
        "r02_d1_manifest_sha256": R02_D4_S1_R02_D1_MANIFEST_SHA256,
        "representative_n": 150,
        "seed_slot": R02_D4_S1_SEED_SLOT,
        "total_n": 200,
    }


def build_resolved_preimage(
    *,
    coordinator_nonce_commitment_sha256: str,
    reviewer_nonce_commitment_sha256: str,
    coordinator_nonce_reveal_hex: str,
    reviewer_nonce_reveal_hex: str,
) -> dict[str, str | int]:
    """Verify both commitments and construct the one allowed seed preimage."""

    coordinator_commitment = _require_hex64(
        coordinator_nonce_commitment_sha256,
        "COORDINATOR_COMMITMENT_SHA256_INVALID",
    )
    reviewer_commitment = _require_hex64(
        reviewer_nonce_commitment_sha256,
        "REVIEWER_COMMITMENT_SHA256_INVALID",
    )
    coordinator_nonce = _nonce_from_reveal(
        coordinator_nonce_reveal_hex, "COORDINATOR"
    )
    reviewer_nonce = _nonce_from_reveal(reviewer_nonce_reveal_hex, "REVIEWER")
    if nonce_commitment_sha256(coordinator_nonce) != coordinator_commitment:
        raise R02D4S1SeedError("COORDINATOR_REVEAL_COMMITMENT_MISMATCH")
    if nonce_commitment_sha256(reviewer_nonce) != reviewer_commitment:
        raise R02D4S1SeedError("REVIEWER_REVEAL_COMMITMENT_MISMATCH")
    return {
        **pinned_preimage_fields(),
        "coordinator_nonce_commitment_sha256": coordinator_commitment,
        "coordinator_nonce_reveal_hex": coordinator_nonce_reveal_hex,
        "reviewer_nonce_commitment_sha256": reviewer_commitment,
        "reviewer_nonce_reveal_hex": reviewer_nonce_reveal_hex,
    }


def resolve_frame_seed_sha256(
    *,
    coordinator_nonce_commitment_sha256: str,
    reviewer_nonce_commitment_sha256: str,
    coordinator_nonce_reveal_hex: str,
    reviewer_nonce_reveal_hex: str,
) -> str:
    """Hash the verified canonical preimage once for frozen seed slot zero."""

    preimage = build_resolved_preimage(
        coordinator_nonce_commitment_sha256=coordinator_nonce_commitment_sha256,
        reviewer_nonce_commitment_sha256=reviewer_nonce_commitment_sha256,
        coordinator_nonce_reveal_hex=coordinator_nonce_reveal_hex,
        reviewer_nonce_reveal_hex=reviewer_nonce_reveal_hex,
    )
    return canonical_sha256(preimage)


def validate_coordinator_commitment_record(record: Mapping[str, Any]) -> None:
    """Fail closed unless a record is exactly the pre-reviewer S1 state."""

    if record.get("schema_version") != R02_D4_S1_SCHEMA_VERSION:
        raise R02D4S1SeedError("COORDINATOR_RECORD_SCHEMA_MISMATCH")
    if record.get("status") != (
        "COORDINATOR_COMMITMENT_SEALED_REVIEWER_COMMITMENT_PENDING"
    ):
        raise R02D4S1SeedError("COORDINATOR_RECORD_STATUS_MISMATCH")
    if record.get("seed_slot") != R02_D4_S1_SEED_SLOT:
        raise R02D4S1SeedError("COORDINATOR_RECORD_SEED_SLOT_MISMATCH")
    if record.get("coordinator") != "CODEX" or record.get("reviewer") != "CLAUDE":
        raise R02D4S1SeedError("COORDINATOR_RECORD_ROLE_MISMATCH")
    _require_hex64(
        record.get("coordinator_nonce_commitment_sha256"),
        "COORDINATOR_COMMITMENT_SHA256_INVALID",
    )
    forbidden_non_null = (
        "reviewer_nonce_commitment_sha256",
        "coordinator_nonce_reveal_hex",
        "reviewer_nonce_reveal_hex",
        "resolved_frame_seed_sha256",
        "resolved_frame_id",
    )
    if any(record.get(field) is not None for field in forbidden_non_null):
        raise R02D4S1SeedError("COORDINATOR_RECORD_PREMATURE_REVIEWER_OR_REVEAL_DATA")
    if record.get("provider_calls") != 0:
        raise R02D4S1SeedError("COORDINATOR_RECORD_PROVIDER_BOUNDARY_MISMATCH")
    for field in ("frame_generation", "frame_scan", "live_execution"):
        if record.get(field) is not False:
            raise R02D4S1SeedError(
                f"COORDINATOR_RECORD_BOUNDARY_MISMATCH:{field}"
            )


def forbidden_capability_names() -> set[str]:
    """Names used by the source-level zero-call audit."""

    return {
        "asyncio",
        "http",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "codex_exec_client",
        "r02_frame",
        "r02_d3_live_orchestrator",
        "r02_d3_live_selector_adapter",
    }
