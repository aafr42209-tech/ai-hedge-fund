from __future__ import annotations

import json
from pathlib import Path

import pytest

from .artifacts import AppendOnlyArtifactStore, ArtifactExistsError
from .contracts import SyntheticEpisode
from .r02_audit import (
    R02AppendOnlyArtifactStore,
    R02ArtifactRootError,
    persist_provider_free_preparation,
    persist_scripted_selection_run,
)
from .r02_candidates import prepare_provider_free_episode
from .r02_contracts import (
    R02ScriptedExchange,
    R02SelectionAuditGraph,
    R02_FREEZE_SHA256,
)
from .r02_replay import R02ReplayError, replay_scripted_selection_run
from .r02_selector import ScriptedR02SelectorClient, run_scripted_selector_episode


ROOT = Path(__file__).resolve().parents[3]


def _triggered_episode(index: int = 0) -> SyntheticEpisode:
    vectors = json.loads(
        (ROOT / "docs" / "r02-d1-test-vectors.json").read_text(encoding="utf-8")
    )
    triggered = [value for value in vectors["vectors"] if value["trigger"]["triggered"]]
    vector = triggered[index]
    path = ROOT / vectors["source_store_root"] / vector["fixture"]["relative_path"]
    return SyntheticEpisode.model_validate_json(path.read_text(encoding="utf-8"))


def _response(candidate_id: str) -> str:
    return json.dumps(
        {
            "schema_version": "r02-selector-response-v1",
            "selected_candidate_id": candidate_id,
            "confidence": 64,
            "reason_codes": ["TIE_BREAK_PREFERENCE"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _selection_run(*, fallback: bool):
    episode = _triggered_episode()
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id=f"r02-d2b-audit-{fallback}",
        provider_attempt_count=6,
    )
    assert preparation.candidate_set is not None
    assert preparation.permutation is not None
    if fallback:
        presented_id = "P99"
    else:
        baseline_id = preparation.candidate_set.baseline_canonical_candidate_id
        presented_id = next(
            key
            for key, value in preparation.permutation.presented_to_canonical_map.items()
            if value != baseline_id
        )
    exchange = R02ScriptedExchange(
        raw_response=_response(presented_id),
        input_tokens=31,
        cached_input_tokens=3,
        output_tokens=13,
        reasoning_output_tokens=5,
    )
    client = ScriptedR02SelectorClient((exchange,), initial_attempt_count=6)
    return episode, run_scripted_selector_episode(episode, preparation, client)


def _persist(tmp_path: Path, *, fallback: bool):
    episode, run = _selection_run(fallback=fallback)
    store = R02AppendOnlyArtifactStore(tmp_path)
    persisted = persist_scripted_selection_run(
        store,
        f"selection-{fallback}",
        episode,
        run,
    )
    return episode, run, store, persisted


@pytest.mark.parametrize("fallback", [False, True])
def test_persisted_scripted_selection_graph_replays_exactly(tmp_path, fallback) -> None:
    episode, run, store, persisted = _persist(tmp_path, fallback=fallback)
    verification = replay_scripted_selection_run(
        store,
        persisted,
        episode,
        expected_selection_run_sha256=persisted.selection_run.sha256,
        expected_audit_graph_sha256=persisted.audit_graph.sha256,
        expected_freeze_sha256=R02_FREEZE_SHA256,
    )
    graph = R02SelectionAuditGraph.model_validate_json(store.read_bytes(persisted.audit_graph))

    expected = [
        "public_fixture",
        "eligibility_decision",
        "candidate_set",
        "candidate_permutation",
        "preparation",
        "selector_request",
        "selector_token_ledger",
        "selector_transport",
        "selector_raw_response",
        "selector_response",
        "acceptance_gate",
    ]
    if fallback:
        expected.append("baseline_fallback")
    expected.extend(("execution_decision", "episode_result", "selection_run"))
    assert list(graph.node_types) == expected
    assert verification.verified_artifacts == len(graph.nodes) + 1
    assert verification.external_provider_calls == 0
    assert verification.live_execution is False
    assert graph.external_provider_calls == 0
    assert graph.live_execution is False
    assert run.episode_result.paired_utility_delta_e12 == (
        0
        if fallback
        else run.episode_result.executed_score.utility_e12
        - run.episode_result.baseline_score.utility_e12
    )


def test_selection_audit_persistence_is_append_only(tmp_path) -> None:
    episode, run, store, _persisted = _persist(tmp_path, fallback=False)
    with pytest.raises(ArtifactExistsError):
        persist_scripted_selection_run(store, "selection-False", episode, run)


def test_selection_replay_rejects_anchor_mismatch(tmp_path) -> None:
    episode, _run, store, persisted = _persist(tmp_path, fallback=False)
    with pytest.raises(R02ReplayError, match="selection-run anchor mismatch"):
        replay_scripted_selection_run(
            store,
            persisted,
            episode,
            expected_selection_run_sha256="0" * 64,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            expected_freeze_sha256=R02_FREEZE_SHA256,
        )


def test_selection_replay_rejects_tampered_raw_response_bytes(tmp_path) -> None:
    episode, _run, store, persisted = _persist(tmp_path, fallback=False)
    graph = R02SelectionAuditGraph.model_validate_json(store.read_bytes(persisted.audit_graph))
    index = graph.node_types.index("selector_raw_response")
    raw_reference = graph.nodes[index]
    (tmp_path / raw_reference.relative_path).write_text("{}", encoding="utf-8")
    with pytest.raises(R02ReplayError, match="invalid selector raw response"):
        replay_scripted_selection_run(
            store,
            persisted,
            episode,
            expected_selection_run_sha256=persisted.selection_run.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            expected_freeze_sha256=R02_FREEZE_SHA256,
        )


def test_selection_replay_rejects_fixture_identity_mismatch(tmp_path) -> None:
    _episode, _run, store, persisted = _persist(tmp_path, fallback=True)
    with pytest.raises(R02ReplayError, match="fixture ID mismatch"):
        replay_scripted_selection_run(
            store,
            persisted,
            _triggered_episode(index=1),
            expected_selection_run_sha256=persisted.selection_run.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            expected_freeze_sha256=R02_FREEZE_SHA256,
        )


def test_generic_store_cannot_persist_d2a_graph_into_r01_root(tmp_path) -> None:
    episode = _triggered_episode()
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id="r02-d2b-generic-store-guard",
    )
    store = AppendOnlyArtifactStore(tmp_path / ".research_artifacts" / "r01-b3-test")
    with pytest.raises(R02ArtifactRootError, match="cannot target an R01 artifact tree"):
        persist_provider_free_preparation(
            store,
            "must-not-write",
            episode,
            preparation,
        )
    assert not store.root.exists()
