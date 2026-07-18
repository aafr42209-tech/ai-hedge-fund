from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

from . import r02_d4_s2_frame, r02_d4_s2a_frame
from .r02_frame import R02ChallengeDisposition, R02ChallengeScanRecord


def _admitted_record(index: int) -> R02ChallengeScanRecord:
    return R02ChallengeScanRecord(
        source_index=index,
        fixture_id=f"fixture-{index}",
        fixture_content_sha256=f"{index:064x}",
        public_state_fingerprint_sha256=f"{index + 1:064x}",
        regime="test",
        triggered=True,
        candidate_count=2,
        eligible_opportunity=True,
        baseline_utility_e12=0,
        best_candidate_utility_e12=1,
        candidate_headroom_e12=1,
        best_candidate_canonical_id=f"{index + 2:064x}",
        disposition=R02ChallengeDisposition.ADMITTED,
        admitted=True,
    )


def test_s2a_uses_new_identity_root_and_same_seed() -> None:
    assert r02_d4_s2a_frame.R02_D4_S2A_ATTEMPT_NAME == "R02_D4_S2A"
    assert r02_d4_s2a_frame.R02_D4_S2A_FRAME_ID == "r02-d4-s2a-frame-0716a1b9c13a"
    assert r02_d4_s2a_frame.R02_D4_S2A_ARTIFACT_ROOT_RELATIVE == (
        ".research_artifacts/r02-d4-s2a-frame-0716a1b9c13a"
    )
    assert r02_d4_s2_frame.R02_D4_S2_ROOT_SEED_HEX == (
        "0716a1b9c13aec596b29776f48b3d8d1fc0a9afacc1c5010bd2cf2a9629d0621"
    )


def test_s2a_pins_900_seconds_and_no_in_process_full_replay() -> None:
    assert r02_d4_s2a_frame.R02_D4_S2A_EXECUTION_TIMEOUT_SECONDS == 900
    assert r02_d4_s2a_frame.R02D4S2AFrameManifest.model_fields[
        "in_generation_process_full_replay"
    ].default is False


def test_s2a_base_builder_and_generators_remain_pinned() -> None:
    assert r02_d4_s2a_frame.base_builder_source_sha256() == (
        r02_d4_s2a_frame.R02_D4_S2A_BASE_BUILDER_SOURCE_SHA256
    )
    assert r02_d4_s2a_frame.candidate_generator_source_sha256() == (
        r02_d4_s2_frame.R02_D4_S2_CANDIDATE_GENERATOR_SOURCE_SHA256
    )
    assert r02_d4_s2a_frame.fixture_generator_source_sha256() == (
        r02_d4_s2_frame.R02_D4_S2_FIXTURE_GENERATOR_SOURCE_SHA256
    )


def test_s2a_scan_accepts_exact_contiguous_fifty_under_new_identity() -> None:
    records = tuple(_admitted_record(150 + index) for index in range(50))
    scan = r02_d4_s2a_frame.R02D4S2AChallengeScan(
        records=records,
        admitted_source_indexes=tuple(record.source_index for record in records),
    )
    assert scan.frame_id == r02_d4_s2a_frame.R02_D4_S2A_FRAME_ID
    assert scan.predecessor_partial_root_reused is False


def test_s2a_scan_rejects_short_admission() -> None:
    records = tuple(_admitted_record(150 + index) for index in range(49))
    with pytest.raises(ValidationError):
        r02_d4_s2a_frame.R02D4S2AChallengeScan(
            records=records,
            admitted_source_indexes=tuple(record.source_index for record in records),
        )


def test_s2a_builder_has_no_seed_count_root_or_retry_parameters() -> None:
    assert tuple(inspect.signature(r02_d4_s2a_frame.build_provider_free_frame).parameters) == ()


def test_s2a_source_has_no_provider_network_process_or_live_imports() -> None:
    tree = ast.parse(Path(r02_d4_s2a_frame.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(r02_d4_s2a_frame.forbidden_capability_names())


def test_s2_abort_sources_and_evidence_remain_byte_identical() -> None:
    root = Path(__file__).resolve().parents[3]
    expected = {
        "v2/research/overlay/r02_d4_s2_frame.py": (
            "178e9b5d943d2062517dfd5be746968e135b4a4bc1248092f17960b00e9786c3"
        ),
        "docs/r02-d4-s2-abort-diagnostic.json": (
            "6f404821a35096eafc1cba060d52faa9d3bf0652ddb49580e98d07bbfa455e35"
        ),
        "docs/r02-d4-s2-zero-call-manifest.json": (
            "d665fd6972c39197a62b2f94d7e160b11ceb26bc9c79daa1c528619edc4ea20e"
        ),
    }
    for relative_path, expected_sha256 in expected.items():
        assert hashlib.sha256((root / relative_path).read_bytes()).hexdigest() == expected_sha256
