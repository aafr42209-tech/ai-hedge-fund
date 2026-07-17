from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from .artifacts import ArtifactExistsError
from .contracts import ArtifactReference, SyntheticEpisode
from .r02_audit import (
    R02AppendOnlyArtifactStore,
    R02ArtifactRootError,
    persist_provider_free_preparation,
)
from .r02_candidates import prepare_provider_free_episode
from .r02_contracts import (
    R02AuditGraph,
    R02PersistedPreparation,
    R02PreparationState,
    R02_FREEZE_SHA256,
)
from .r02_replay import R02ReplayError, replay_provider_free_preparation

ROOT = Path(__file__).resolve().parents[3]


def _episode(*, triggered: bool) -> SyntheticEpisode:
    vectors = json.loads((ROOT / "docs" / "r02-d1-test-vectors.json").read_text())
    vector = next(value for value in vectors["vectors"] if value["trigger"]["triggered"] is triggered)
    path = ROOT / vectors["source_store_root"] / vector["fixture"]["relative_path"]
    return SyntheticEpisode.model_validate_json(path.read_text(encoding="utf-8"))


def _persist(tmp_path: Path, *, triggered: bool):
    episode = _episode(triggered=triggered)
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id=f"r02-d2a-replay-{triggered}",
    )
    store = R02AppendOnlyArtifactStore(tmp_path)
    persisted = persist_provider_free_preparation(
        store,
        f"episode-{triggered}",
        episode,
        preparation,
    )
    return episode, preparation, store, persisted


@pytest.mark.parametrize(
    "relative_root",
    (
        ".research_artifacts/r01",
        ".research_artifacts/r01-b3-deadbeef",
        ".research_artifacts/r01-b3-deadbeef/nested/r02",
        ".research_artifacts/R01-B3-DEADBEEF/nested",
    ),
)
def test_r02_store_rejects_r01_artifact_roots_and_descendants(
    tmp_path, relative_root
) -> None:
    with pytest.raises(R02ArtifactRootError, match="cannot target an R01 artifact tree"):
        R02AppendOnlyArtifactStore(tmp_path / relative_root)


@pytest.mark.parametrize(
    "relative_root",
    (
        ".research_artifacts/r02",
        ".research_artifacts/r010",
        "custom/r01-b3-test",
    ),
)
def test_r02_store_allows_non_r01_artifact_roots(tmp_path, relative_root) -> None:
    store = R02AppendOnlyArtifactStore(tmp_path / relative_root)
    assert store.root == (tmp_path / relative_root).resolve()


def test_r02_store_rejects_existing_sealed_r01_root() -> None:
    sealed_roots = sorted((ROOT / ".research_artifacts").glob("r01-*"))
    assert sealed_roots
    with pytest.raises(R02ArtifactRootError):
        R02AppendOnlyArtifactStore(sealed_roots[0])


@pytest.mark.parametrize("triggered", [False, True])
def test_persisted_provider_free_graph_replays_exactly(tmp_path, triggered) -> None:
    episode, preparation, store, persisted = _persist(tmp_path, triggered=triggered)
    verification = replay_provider_free_preparation(
        store,
        persisted,
        episode,
        expected_preparation_sha256=persisted.preparation.sha256,
        expected_audit_graph_sha256=persisted.audit_graph.sha256,
        expected_freeze_sha256=R02_FREEZE_SHA256,
    )
    graph = R02AuditGraph.model_validate_json(store.read_bytes(persisted.audit_graph))
    assert verification.provider_calls == 0
    assert verification.all_hashes_match is True
    assert graph.provider_calls == 0
    assert graph.terminal is (not triggered)
    assert graph.node_types[-1] == "preparation"
    if triggered:
        assert preparation.state is R02PreparationState.SELECTOR_ELIGIBLE_NOT_CALLED
        assert graph.node_types == (
            "public_fixture",
            "eligibility_decision",
            "candidate_set",
            "candidate_permutation",
            "preparation",
        )
    else:
        assert preparation.state is R02PreparationState.NO_CALL_TERMINAL
        assert graph.node_types == (
            "public_fixture",
            "eligibility_decision",
            "no_call_record",
            "execution_decision",
            "episode_result",
            "preparation",
        )


def test_audit_persistence_is_append_only(tmp_path) -> None:
    episode, preparation, store, _persisted = _persist(tmp_path, triggered=False)
    with pytest.raises(ArtifactExistsError):
        persist_provider_free_preparation(
            store,
            "episode-False",
            episode,
            preparation,
        )


def test_replay_rejects_preparation_anchor_mismatch(tmp_path) -> None:
    episode, _preparation, store, persisted = _persist(tmp_path, triggered=False)
    with pytest.raises(R02ReplayError, match="preparation anchor mismatch"):
        replay_provider_free_preparation(
            store,
            persisted,
            episode,
            expected_preparation_sha256="0" * 64,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            expected_freeze_sha256=R02_FREEZE_SHA256,
        )


def test_replay_rejects_wrong_freeze_identity(tmp_path) -> None:
    episode, _preparation, store, persisted = _persist(tmp_path, triggered=True)
    with pytest.raises(R02ReplayError, match="freeze identity"):
        replay_provider_free_preparation(
            store,
            persisted,
            episode,
            expected_preparation_sha256=persisted.preparation.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            expected_freeze_sha256="0" * 64,
        )


def test_replay_rejects_tampered_node_bytes(tmp_path) -> None:
    episode, _preparation, store, persisted = _persist(tmp_path, triggered=False)
    graph = R02AuditGraph.model_validate_json(store.read_bytes(persisted.audit_graph))
    node = graph.nodes[1]
    (tmp_path / node.relative_path).write_bytes(b"{}")
    with pytest.raises(R02ReplayError, match="invalid eligibility_decision artifact"):
        replay_provider_free_preparation(
            store,
            persisted,
            episode,
            expected_preparation_sha256=persisted.preparation.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            expected_freeze_sha256=R02_FREEZE_SHA256,
        )


def test_replay_rejects_fixture_identity_mismatch(tmp_path) -> None:
    _episode_false, _preparation, store, persisted = _persist(tmp_path, triggered=False)
    with pytest.raises(R02ReplayError, match="fixture ID mismatch"):
        replay_provider_free_preparation(
            store,
            persisted,
            _episode(triggered=True),
            expected_preparation_sha256=persisted.preparation.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            expected_freeze_sha256=R02_FREEZE_SHA256,
        )


def test_persisted_contract_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        R02PersistedPreparation.model_validate(
            {
                "preparation": ArtifactReference(
                    relative_path="a.json", sha256="0" * 64, size_bytes=0
                ),
                "audit_graph": ArtifactReference(
                    relative_path="b.json", sha256="0" * 64, size_bytes=0
                ),
                "selector_request": {},
            }
        )
