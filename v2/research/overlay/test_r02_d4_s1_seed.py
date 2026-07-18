from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from . import r02_d4_s1_seed
from .canonical import canonical_sha256
from .contracts import GeneratorConfig
from .r02_d4_s1_seed import (
    R02D4S1SeedError,
    build_resolved_preimage,
    nonce_commitment_sha256,
    pinned_preimage_fields,
    resolve_frame_seed_sha256,
    validate_coordinator_commitment_record,
)

ROOT = Path(__file__).resolve().parents[3]


def test_static_pins_match_accepted_commit_design_and_generator() -> None:
    pins = pinned_preimage_fields()
    design_path = ROOT / r02_d4_s1_seed.R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_PATH
    contract_path = ROOT / r02_d4_s1_seed.R02_D4_S1_SEED_CONTRACT_PATH
    d2c = json.loads(
        (ROOT / "docs" / "r02-d2c-frame-manifest.json").read_text(encoding="utf-8")
    )
    assert hashlib.sha256(design_path.read_bytes()).hexdigest() == (
        r02_d4_s1_seed.R02_D4_S1_ACCEPTED_DESIGN_MANIFEST_SHA256
    )
    assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == (
        r02_d4_s1_seed.R02_D4_S1_SEED_CONTRACT_SHA256
    )
    assert pins["accepted_design_commit"] == (
        "d9f984866c8775153d9c1ac1aea9b49fc9647635"
    )
    assert d2c["generator_config_sha256"] == pins["generator_config_sha256"]
    assert canonical_sha256(GeneratorConfig()) == pins["generator_config_sha256"]


def test_nonce_commitment_uses_raw_32_bytes() -> None:
    nonce = bytes(range(32))
    assert nonce_commitment_sha256(nonce) == hashlib.sha256(nonce).hexdigest()
    with pytest.raises(R02D4S1SeedError, match="NONCE_MUST_BE_EXACTLY_32_RAW_BYTES"):
        nonce_commitment_sha256(nonce.hex().encode("ascii"))


def test_resolved_preimage_matches_frozen_contract_shape() -> None:
    coordinator = bytes(range(32))
    reviewer = bytes(reversed(range(32)))
    preimage = build_resolved_preimage(
        coordinator_nonce_commitment_sha256=nonce_commitment_sha256(coordinator),
        reviewer_nonce_commitment_sha256=nonce_commitment_sha256(reviewer),
        coordinator_nonce_reveal_hex=coordinator.hex(),
        reviewer_nonce_reveal_hex=reviewer.hex(),
    )
    contract = json.loads(
        (ROOT / "docs" / "r02-d4-seed-contract.json").read_text(encoding="utf-8")
    )
    assert set(preimage) == set(contract["preimage_template"])
    for key, value in contract["preimage_template"].items():
        if value is not None:
            assert preimage[key] == value
    assert resolve_frame_seed_sha256(
        coordinator_nonce_commitment_sha256=nonce_commitment_sha256(coordinator),
        reviewer_nonce_commitment_sha256=nonce_commitment_sha256(reviewer),
        coordinator_nonce_reveal_hex=coordinator.hex(),
        reviewer_nonce_reveal_hex=reviewer.hex(),
    ) == canonical_sha256(preimage)


@pytest.mark.parametrize("role", ["coordinator", "reviewer"])
def test_reveal_mismatch_aborts_without_seed(role: str) -> None:
    coordinator = bytes(range(32))
    reviewer = bytes(reversed(range(32)))
    values = {
        "coordinator_nonce_commitment_sha256": nonce_commitment_sha256(coordinator),
        "reviewer_nonce_commitment_sha256": nonce_commitment_sha256(reviewer),
        "coordinator_nonce_reveal_hex": coordinator.hex(),
        "reviewer_nonce_reveal_hex": reviewer.hex(),
    }
    values[f"{role}_nonce_reveal_hex"] = (b"x" * 32).hex()
    with pytest.raises(R02D4S1SeedError, match=f"{role.upper()}_REVEAL_COMMITMENT_MISMATCH"):
        resolve_frame_seed_sha256(**values)


def test_coordinator_record_rejects_premature_reviewer_or_reveal_data() -> None:
    record = {
        "schema_version": r02_d4_s1_seed.R02_D4_S1_SCHEMA_VERSION,
        "status": "COORDINATOR_COMMITMENT_SEALED_REVIEWER_COMMITMENT_PENDING",
        "seed_slot": 0,
        "coordinator": "CODEX",
        "reviewer": "CLAUDE",
        "coordinator_nonce_commitment_sha256": "a" * 64,
        "reviewer_nonce_commitment_sha256": None,
        "coordinator_nonce_reveal_hex": None,
        "reviewer_nonce_reveal_hex": None,
        "resolved_frame_seed_sha256": None,
        "resolved_frame_id": None,
        "provider_calls": 0,
        "frame_generation": False,
        "frame_scan": False,
        "live_execution": False,
    }
    validate_coordinator_commitment_record(record)
    record["reviewer_nonce_commitment_sha256"] = "b" * 64
    with pytest.raises(R02D4S1SeedError, match="PREMATURE_REVIEWER_OR_REVEAL_DATA"):
        validate_coordinator_commitment_record(record)


def test_s1_source_has_no_provider_network_process_or_frame_imports() -> None:
    tree = ast.parse(Path(r02_d4_s1_seed.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    relative_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
            if node.level:
                relative_modules.add(node.module)
    assert imported.isdisjoint(r02_d4_s1_seed.forbidden_capability_names())
    assert relative_modules == {"canonical"}


def test_single_slot_and_no_retry_or_replacement_surface() -> None:
    source = Path(r02_d4_s1_seed.__file__).read_text(encoding="utf-8")
    assert r02_d4_s1_seed.R02_D4_S1_SEED_SLOT == 0
    assert "random" not in source
    assert "retry" not in source.lower()
    assert "replacement" not in source.lower()
