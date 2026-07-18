from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from . import r02_d4_s1_resolve
from .r02_d4_s1_resolve import (
    R02D4S1ResolveError,
    build_verified_preimage,
    validate_reviewer_reveal_record,
)

ROOT = Path(__file__).resolve().parents[3]


def _sha256_file(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def _reviewer_reveal() -> dict[str, object]:
    return json.loads(
        (ROOT / r02_d4_s1_resolve.R02_D4_S1_REVIEWER_REVEAL_ARTIFACT_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_reviewer_reveal_artifact_hash_and_record_are_exact() -> None:
    assert _sha256_file(r02_d4_s1_resolve.R02_D4_S1_REVIEWER_REVEAL_ARTIFACT_PATH) == (
        r02_d4_s1_resolve.R02_D4_S1_REVIEWER_REVEAL_ARTIFACT_SHA256
    )
    validate_reviewer_reveal_record(_reviewer_reveal())


def test_prior_reveal_lineage_remains_byte_identical() -> None:
    expected = {
        "docs/r02-d4-s1-coordinator-reveal.json": (
            "a674c1ae1852b51650b680916ce6c5dbdb8d652384bae1a6209c970558e0c8a5"
        ),
        "docs/r02-d4-s1-coordinator-reveal-zero-call-manifest.json": (
            "9775488293d9a590e754e5e5d6a7d53c3e881e35c735e12370eb4add65b16d7a"
        ),
        "docs/r02-d4-s1-reviewer-commitment.json": (
            "2c93c329e30693ea3de99f9114f1f16af9282acfaff6b2b49e2e555438092215"
        ),
    }
    assert {path: _sha256_file(path) for path in expected} == expected


def test_reviewer_reveal_matches_coordinator_sealed_value() -> None:
    reviewer = _reviewer_reveal()
    coordinator = json.loads(
        (ROOT / "docs" / "r02-d4-s1-coordinator-reveal.json").read_text(
            encoding="utf-8"
        )
    )
    assert reviewer["coordinator_nonce_reveal_hex"] == coordinator[
        "coordinator_nonce_reveal_hex"
    ]


def test_verified_preimage_has_exact_frozen_contract_shape() -> None:
    preimage = build_verified_preimage(_reviewer_reveal())
    contract = json.loads(
        (ROOT / "docs" / "r02-d4-seed-contract.json").read_text(encoding="utf-8")
    )
    assert set(preimage) == set(contract["preimage_template"])
    assert preimage["seed_slot"] == 0
    assert preimage["total_n"] == 200


def test_reviewer_reveal_rejects_premature_seed() -> None:
    record = _reviewer_reveal()
    record["resolved_frame_seed_sha256"] = "a" * 64
    with pytest.raises(R02D4S1ResolveError, match="resolved_frame_seed_sha256"):
        validate_reviewer_reveal_record(record)


def test_reviewer_reveal_rejects_missing_reveal_without_replacement_path() -> None:
    record = _reviewer_reveal()
    record["reviewer_nonce_reveal_hex"] = None
    with pytest.raises(Exception, match="REVIEWER_REVEAL_HEX_INVALID"):
        validate_reviewer_reveal_record(record)


def test_resolve_source_has_no_nonce_generator_provider_process_or_frame_imports() -> None:
    tree = ast.parse(Path(r02_d4_s1_resolve.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(r02_d4_s1_resolve.forbidden_capability_names())


def test_resolve_source_has_no_frame_creation_or_alternate_seed_surface() -> None:
    source = Path(r02_d4_s1_resolve.__file__).read_text(encoding="utf-8")
    assert r02_d4_s1_resolve.R02_D4_S1_SEED_SLOT == 0
    assert "frame_generation(" not in source
    assert "retry(" not in source
    assert "replacement(" not in source
