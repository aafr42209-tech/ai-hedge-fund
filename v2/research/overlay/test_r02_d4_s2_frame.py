from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

from . import r02_d4_s2_frame
from .contracts import GeneratorConfig
from .fixtures import generate_episode
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


def test_s2_constants_pin_one_150_50_frame() -> None:
    assert r02_d4_s2_frame.R02_D4_S2_FRAME_ID == "r02-d4-frame-0716a1b9c13a"
    assert r02_d4_s2_frame.R02_D4_S2_REPRESENTATIVE_COUNT == 150
    assert r02_d4_s2_frame.R02_D4_S2_CHALLENGE_COUNT == 50
    assert r02_d4_s2_frame.R02_D4_S2_TOTAL_COUNT == 200
    assert r02_d4_s2_frame.R02_D4_S2_CHALLENGE_SCAN_LIMIT == 4_096


def test_generator_source_and_config_pins_match() -> None:
    assert r02_d4_s2_frame.candidate_generator_source_sha256() == (
        r02_d4_s2_frame.R02_D4_S2_CANDIDATE_GENERATOR_SOURCE_SHA256
    )
    assert r02_d4_s2_frame.fixture_generator_source_sha256() == (
        r02_d4_s2_frame.R02_D4_S2_FIXTURE_GENERATOR_SOURCE_SHA256
    )
    assert r02_d4_s2_frame.canonical_sha256(GeneratorConfig()) == (
        r02_d4_s2_frame.R02_D4_S2_GENERATOR_CONFIG_SHA256
    )


def test_classification_is_deterministic_and_provider_free() -> None:
    episode = generate_episode(GeneratorConfig(), "0" * 64, 0)
    first = r02_d4_s2_frame.classify_episode(episode, source_index=0)
    second = r02_d4_s2_frame.classify_episode(episode, source_index=0)
    assert first == second


def test_challenge_scan_accepts_exact_contiguous_fifty() -> None:
    records = tuple(_admitted_record(150 + index) for index in range(50))
    scan = r02_d4_s2_frame.R02D4S2ChallengeScan(
        records=records,
        admitted_source_indexes=tuple(record.source_index for record in records),
    )
    assert len(scan.admitted_source_indexes) == 50


def test_challenge_scan_rejects_gap_or_short_admission() -> None:
    records = tuple(_admitted_record(150 + index) for index in range(49))
    with pytest.raises(ValidationError):
        r02_d4_s2_frame.R02D4S2ChallengeScan(
            records=records,
            admitted_source_indexes=tuple(record.source_index for record in records),
        )


def test_builder_has_no_count_seed_or_retry_parameters() -> None:
    assert tuple(inspect.signature(r02_d4_s2_frame.build_provider_free_frame).parameters) == ()


def test_s2_source_has_no_provider_network_process_or_live_imports() -> None:
    tree = ast.parse(Path(r02_d4_s2_frame.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(r02_d4_s2_frame.forbidden_capability_names())


def test_sealed_d2c_builder_source_remains_unchanged() -> None:
    root = Path(__file__).resolve().parents[3]
    source = root / "v2" / "research" / "overlay" / "r02_frame.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == (
        "bc2d3c64d04b4b47d8a4bee81da24bd02c411cb299f09fa15747a7871a7a8f40"
    )
