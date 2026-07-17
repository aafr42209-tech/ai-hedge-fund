"""Fail-closed replay of provider-free R02 D2a audit graphs."""

from __future__ import annotations

from pathlib import Path

from .artifacts import AppendOnlyArtifactStore, ArtifactIntegrityError
from .canonical import canonical_json_bytes
from .contracts import PublicEpisode, SyntheticEpisode
from .r02_candidates import DEFAULT_R02_FREEZE_PATH, prepare_provider_free_episode
from .r02_contracts import (
    R02AuditGraph,
    R02CandidatePermutation,
    R02CandidateSet,
    R02EligibilityDecision,
    R02EpisodeResult,
    R02ExecutionDecision,
    R02NoCallRecord,
    R02PersistedPreparation,
    R02ProviderFreePreparation,
    R02ReplayVerification,
    R02_FREEZE_SHA256,
)


class R02ReplayError(RuntimeError):
    pass


_NODE_MODELS = {
    "public_fixture": PublicEpisode,
    "eligibility_decision": R02EligibilityDecision,
    "candidate_set": R02CandidateSet,
    "candidate_permutation": R02CandidatePermutation,
    "no_call_record": R02NoCallRecord,
    "execution_decision": R02ExecutionDecision,
    "episode_result": R02EpisodeResult,
    "preparation": R02ProviderFreePreparation,
}


def _expected_node(preparation: R02ProviderFreePreparation, node_type: str, episode: SyntheticEpisode) -> object:
    mapping = {
        "public_fixture": episode.public,
        "eligibility_decision": preparation.eligibility,
        "candidate_set": preparation.candidate_set,
        "candidate_permutation": preparation.permutation,
        "no_call_record": preparation.no_call,
        "execution_decision": preparation.execution_decision,
        "episode_result": preparation.episode_result,
        "preparation": preparation,
    }
    return mapping[node_type]


def replay_provider_free_preparation(
    store: AppendOnlyArtifactStore,
    persisted: R02PersistedPreparation,
    episode: SyntheticEpisode,
    *,
    expected_preparation_sha256: str,
    expected_audit_graph_sha256: str,
    expected_freeze_sha256: str,
    freeze_path: str | Path = DEFAULT_R02_FREEZE_PATH,
) -> R02ReplayVerification:
    """Verify hashes, graph topology, contracts, and deterministic reproduction."""

    if expected_freeze_sha256 != R02_FREEZE_SHA256:
        raise R02ReplayError("unexpected R02 freeze identity")
    if persisted.preparation.sha256 != expected_preparation_sha256:
        raise R02ReplayError("preparation anchor mismatch")
    if persisted.audit_graph.sha256 != expected_audit_graph_sha256:
        raise R02ReplayError("audit graph anchor mismatch")
    try:
        preparation = R02ProviderFreePreparation.model_validate_json(
            store.read_bytes(persisted.preparation)
        )
        graph = R02AuditGraph.model_validate_json(store.read_bytes(persisted.audit_graph))
    except Exception as exc:
        if isinstance(exc, R02ReplayError):
            raise
        raise R02ReplayError(f"anchor validation failed: {exc}") from exc
    if graph.identity != preparation.identity:
        raise R02ReplayError("graph identity mismatch")
    if graph.nodes[-1] != persisted.preparation:
        raise R02ReplayError("graph does not terminate at the preparation anchor")
    if episode.public.case_id != preparation.identity.fixture_id:
        raise R02ReplayError("replay fixture ID mismatch")
    if episode.content_sha256 != preparation.identity.fixture_content_sha256:
        raise R02ReplayError("replay fixture content hash mismatch")

    for node_type, reference in zip(graph.node_types, graph.nodes, strict=True):
        model = _NODE_MODELS.get(node_type)
        if model is None:
            raise R02ReplayError(f"unknown audit node type: {node_type}")
        try:
            actual = model.model_validate_json(store.read_bytes(reference))
        except (ArtifactIntegrityError, ValueError, TypeError) as exc:
            raise R02ReplayError(f"invalid {node_type} artifact: {exc}") from exc
        expected = _expected_node(preparation, node_type, episode)
        if expected is None or canonical_json_bytes(actual) != canonical_json_bytes(expected):
            raise R02ReplayError(f"{node_type} artifact does not match preparation")

    reproduced = prepare_provider_free_episode(
        episode,
        experiment_id=preparation.identity.experiment_id,
        replicate_id=preparation.identity.replicate_id,
        provider_attempt_count=preparation.provider_attempt_count,
        freeze_path=freeze_path,
    )
    if canonical_json_bytes(reproduced) != canonical_json_bytes(preparation):
        raise R02ReplayError("deterministic preparation replay mismatch")
    return R02ReplayVerification(
        identity=preparation.identity,
        verified_artifacts=len(graph.nodes) + 1,
    )
