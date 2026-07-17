from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path

import pytest

from .artifacts import ArtifactExistsError, ArtifactIntegrityError
from .canonical import canonical_json_bytes, sha256_hex
from .contracts import GeneratorConfig
from .fixtures import generate_episode
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_frame import (
    R02ChallengeDisposition,
    R02FrameManifest,
    R02FrameSeal,
    R02FrameError,
    R02FrameStratum,
    R02_FRAME_CHALLENGE_COUNT,
    R02_FRAME_CHALLENGE_SCAN_START,
    R02_FRAME_ID,
    R02_FRAME_REPRESENTATIVE_COUNT,
    R02_FRAME_ROOT_SEED_HEX,
    build_provider_free_frame,
    persist_provider_free_frame,
    verify_persisted_frame,
)
from . import r02_frame


@lru_cache(maxsize=1)
def _mini_build():
    return build_provider_free_frame(
        representative_count=6,
        challenge_count=2,
        challenge_scan_limit=200,
    )


def test_frame_root_seed_is_identity_derived_and_counts_are_fixed() -> None:
    assert R02_FRAME_ROOT_SEED_HEX == (
        "53be0c4bb060051e16c13f913f93afcbd97aa2106b90c29d77a4fd6ebd78a93d"
    )
    assert R02_FRAME_ID == "r02-d2c-frame-53be0c4bb060"
    assert R02_FRAME_REPRESENTATIVE_COUNT == 120
    assert R02_FRAME_CHALLENGE_COUNT == 40
    assert R02_FRAME_CHALLENGE_SCAN_START == 120


def test_provider_free_frame_is_deterministic_and_challenge_admission_is_exact() -> None:
    first = _mini_build()
    second = build_provider_free_frame(
        representative_count=6,
        challenge_count=2,
        challenge_scan_limit=200,
    )
    assert first == second
    assert tuple(
        record.source_index for record in first.representative_classifications
    ) == tuple(range(6))
    assert first.challenge_scan.scan_start_index == 120
    assert len(first.challenge_episodes) == 2
    admitted = tuple(record for record in first.challenge_scan.records if record.admitted)
    assert len(admitted) == 2
    assert all(record.triggered for record in admitted)
    assert all(record.candidate_count >= 2 for record in admitted)
    assert all(record.candidate_headroom_e12 > 0 for record in admitted)
    assert all(
        record.disposition is R02ChallengeDisposition.ADMITTED for record in admitted
    )


def test_frozen_full_frame_seal_and_source_identities_verify() -> None:
    manifest = R02FrameManifest.model_validate_json(
        (Path(__file__).resolve().parents[3] / "docs" / "r02-d2c-frame-manifest.json").read_bytes()
    )
    seal = R02FrameSeal.model_validate_json(
        (Path(__file__).resolve().parents[3] / "docs" / "r02-d2c-frame-seal.json").read_bytes()
    )
    store = R02AppendOnlyArtifactStore(
        Path(__file__).resolve().parents[3] / seal.artifact_root_relative_path
    )
    verified = verify_persisted_frame(store, seal)

    assert verified == manifest
    assert manifest.representative_count == 120
    assert manifest.challenge_count == 40
    assert manifest.representative_trigger_count == 15
    assert manifest.representative_eligible_count == 15
    assert manifest.challenge_scanned_count == 394
    assert manifest.challenge_eligible_count == 40
    assert manifest.total_eligible_count == 55
    assert manifest.trigger_threshold_bps == 50
    assert manifest.trigger_recalibrated_after_frame is False
    assert seal.full_tree_file_count == 162
    assert seal.full_tree_sha256 == (
        "316eb5757b2eda3a04ec16f19a225df7a6e44fdf7f506482aa947b9cf77fb494"
    )
    assert manifest.frame_builder_source_sha256 == sha256_hex(
        Path(r02_frame.__file__).read_bytes()
    )


def test_persisted_frame_is_append_only_and_tamper_evident(tmp_path) -> None:
    build = _mini_build()
    root = tmp_path / "r02-d2c-mini"
    manifest, seal = persist_provider_free_frame(build, artifact_root=root)
    store = R02AppendOnlyArtifactStore(root)
    verified = verify_persisted_frame(store, seal)

    assert verified == manifest
    assert manifest.provider_calls == 0
    assert manifest.live_execution is False
    assert manifest.trigger_threshold_bps == 50
    assert manifest.trigger_recalibrated_after_frame is False
    assert manifest.payload_file_count == 9
    assert seal.full_tree_file_count == 10
    assert tuple(case.stratum for case in manifest.cases[:6]) == (
        R02FrameStratum.REPRESENTATIVE,
    ) * 6
    assert tuple(case.stratum for case in manifest.cases[6:]) == (
        R02FrameStratum.CHALLENGE_HEADROOM,
    ) * 2

    with pytest.raises(ArtifactExistsError):
        persist_provider_free_frame(build, artifact_root=root)

    fixture = manifest.cases[0].fixture_artifact
    (root / fixture.relative_path).write_bytes(b"{}")
    with pytest.raises(ArtifactIntegrityError, match="artifact hash mismatch"):
        verify_persisted_frame(store, seal)


def test_duplicate_or_near_duplicate_invalidates_frame_without_skip(monkeypatch) -> None:
    episode = generate_episode(GeneratorConfig(), R02_FRAME_ROOT_SEED_HEX, 0)

    def duplicate_episode(_config, _seed, _index):
        return episode

    monkeypatch.setattr(r02_frame, "generate_episode", duplicate_episode)
    with pytest.raises(R02FrameError, match="duplicate or near-duplicate"):
        build_provider_free_frame(
            representative_count=2,
            challenge_count=1,
            challenge_scan_limit=1,
        )


def test_frame_builder_source_has_no_selector_provider_network_or_process_boundary() -> None:
    source_path = Path(r02_frame.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(
        {
            "anthropic",
            "httpx",
            "openai",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
    )
    assert "r02_selector" not in source
    assert sha256_hex(source_path.read_bytes()) == r02_frame._frame_builder_source_sha256()
    assert canonical_json_bytes(_mini_build().challenge_scan)
