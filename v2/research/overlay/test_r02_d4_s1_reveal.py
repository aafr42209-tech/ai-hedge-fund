from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from . import r02_d4_s1_reveal
from .r02_d4_s1_reveal import (
    R02D4S1RevealError,
    validate_coordinator_reveal_record,
    validate_reveal_matches_commitment,
    validate_reviewer_commitment_record,
)
from .r02_d4_s1_seed import nonce_commitment_sha256

ROOT = Path(__file__).resolve().parents[3]


def _sha256_file(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def _coordinator_reveal_record(reveal_hex: str) -> dict[str, object]:
    return {
        "schema_version": "r02-d4-s1-coordinator-reveal-v1",
        "status": "COORDINATOR_REVEAL_SEALED_REVIEWER_REVEAL_PENDING",
        "reviewer_commitment_artifact_path": (
            r02_d4_s1_reveal.R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH
        ),
        "reviewer_commitment_artifact_sha256": (
            r02_d4_s1_reveal.R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256
        ),
        "accepted_design_commit": "d9f984866c8775153d9c1ac1aea9b49fc9647635",
        "accepted_design_manifest_sha256": (
            "784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900"
        ),
        "generator_config_sha256": (
            "e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf"
        ),
        "seed_slot": 0,
        "coordinator": "CODEX",
        "reviewer": "CLAUDE",
        "sequence_ordinal": 3,
        "commitment_algorithm": "SHA256_RAW_32_BYTE_NONCE",
        "nonce_byte_length": 32,
        "coordinator_nonce_commitment_sha256": (
            r02_d4_s1_reveal.R02_D4_S1_COORDINATOR_COMMITMENT_SHA256
        ),
        "reviewer_nonce_commitment_sha256": (
            r02_d4_s1_reveal.R02_D4_S1_REVIEWER_COMMITMENT_SHA256
        ),
        "coordinator_nonce_reveal_hex": reveal_hex,
        "reviewer_nonce_reveal_hex": None,
        "resolved_frame_seed_sha256": None,
        "resolved_frame_id": None,
        "frame_seed_created": False,
        "retry_cap": 0,
        "replacement_cap": 0,
        "provider_calls": 0,
        "frame_generation": False,
        "frame_scan": False,
        "live_execution": False,
    }


def test_prior_commitment_stage_artifacts_remain_byte_identical() -> None:
    expected = {
        "docs/r02-d4-s1-seed-intent.json": (
            "638a8a0a5de3718576fee7446e064282fa871f18b335364c0294ec831cdd016e"
        ),
        "docs/r02-d4-s1-coordinator-commitment.json": (
            "7ea3288a36424f939d295ec2e96751b33908a82dba78818cfdd16adbdd0687fe"
        ),
        "docs/r02-d4-s1-zero-call-manifest.json": (
            "79c8fa298d3268ef2f0abb15408f285f79b83f8914bae4032572f03579639c9b"
        ),
    }
    assert {path: _sha256_file(path) for path in expected} == expected


def test_reviewer_commitment_artifact_is_exact_and_pre_reveal() -> None:
    path = ROOT / r02_d4_s1_reveal.R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        r02_d4_s1_reveal.R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_SHA256
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    validate_reviewer_commitment_record(record)


def test_reviewer_record_rejects_premature_reveal() -> None:
    path = ROOT / r02_d4_s1_reveal.R02_D4_S1_REVIEWER_COMMITMENT_ARTIFACT_PATH
    record = json.loads(path.read_text(encoding="utf-8"))
    record["reviewer_nonce_reveal_hex"] = "a" * 64
    with pytest.raises(R02D4S1RevealError, match="PREMATURE_REVIEWER_REVEAL"):
        validate_reviewer_commitment_record(record)


def test_generic_reveal_validation_hashes_raw_bytes() -> None:
    nonce = bytes(range(32))
    validate_reveal_matches_commitment(
        nonce.hex(), nonce_commitment_sha256(nonce), "TEST"
    )
    with pytest.raises(R02D4S1RevealError, match="TEST_REVEAL_COMMITMENT_MISMATCH"):
        validate_reveal_matches_commitment((b"z" * 32).hex(), nonce_commitment_sha256(nonce), "TEST")


def test_coordinator_record_rejects_wrong_actual_reveal() -> None:
    record = _coordinator_reveal_record(bytes(32).hex())
    with pytest.raises(R02D4S1RevealError, match="COORDINATOR_REVEAL_COMMITMENT_MISMATCH"):
        validate_coordinator_reveal_record(record)


def test_coordinator_record_rejects_premature_reviewer_reveal() -> None:
    record = _coordinator_reveal_record(bytes(32).hex())
    record["reviewer_nonce_reveal_hex"] = "b" * 64
    with pytest.raises(R02D4S1RevealError, match="PREMATURE_REVIEWER_REVEAL"):
        validate_coordinator_reveal_record(record)


def test_reveal_source_has_no_nonce_generator_provider_process_or_frame_imports() -> None:
    tree = ast.parse(Path(r02_d4_s1_reveal.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    relative_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
            if node.level:
                relative_modules.add(node.module)
    assert imported.isdisjoint(r02_d4_s1_reveal.forbidden_capability_names())
    assert relative_modules == {"r02_d4_s1_seed"}


def test_no_seed_or_frame_resolution_surface_before_both_reveals() -> None:
    source = Path(r02_d4_s1_reveal.__file__).read_text(encoding="utf-8")
    imported = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "secrets" not in imported
    assert "resolve_frame_seed_sha256(" not in source
    assert "frame_generation(" not in source
