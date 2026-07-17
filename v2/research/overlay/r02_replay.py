"""Fail-closed replay of provider-free R02 D2a audit graphs."""

from __future__ import annotations

from pathlib import Path

from .artifacts import AppendOnlyArtifactStore, ArtifactIntegrityError
from .canonical import canonical_json_bytes
from .contracts import PublicEpisode, SyntheticEpisode
from .r02_candidates import DEFAULT_R02_FREEZE_PATH, prepare_provider_free_episode
from .r02_contracts import (
    R02AuditGraph,
    R02AcceptanceGate,
    R02BaselineFallbackRecord,
    R02CandidatePermutation,
    R02CandidateSet,
    R02EligibilityDecision,
    R02EpisodeResult,
    R02ExecutionDecision,
    R02NoCallRecord,
    R02PersistedPreparation,
    R02PersistedSelectionRun,
    R02ProviderFreePreparation,
    R02ReplayVerification,
    R02ScriptedExchange,
    R02ScriptedTransportRecord,
    R02SelectionAuditGraph,
    R02SelectionReplayVerification,
    R02SelectionRun,
    R02SelectorRequest,
    R02SelectorResponseRecord,
    R02SelectorTokenLedger,
    R02TriggeredEpisodeResult,
    R02TriggeredExecutionDecision,
    R02_FREEZE_SHA256,
)
from .r02_selector import ScriptedR02SelectorClient, run_scripted_selector_episode


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


_SELECTION_NODE_MODELS = {
    "public_fixture": PublicEpisode,
    "eligibility_decision": R02EligibilityDecision,
    "candidate_set": R02CandidateSet,
    "candidate_permutation": R02CandidatePermutation,
    "preparation": R02ProviderFreePreparation,
    "selector_request": R02SelectorRequest,
    "selector_token_ledger": R02SelectorTokenLedger,
    "selector_transport": R02ScriptedTransportRecord,
    "selector_response": R02SelectorResponseRecord,
    "acceptance_gate": R02AcceptanceGate,
    "baseline_fallback": R02BaselineFallbackRecord,
    "execution_decision": R02TriggeredExecutionDecision,
    "episode_result": R02TriggeredEpisodeResult,
    "selection_run": R02SelectionRun,
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


def _expected_selection_node(
    run: R02SelectionRun,
    node_type: str,
    episode: SyntheticEpisode,
) -> object:
    mapping = {
        "public_fixture": episode.public,
        "eligibility_decision": run.preparation.eligibility,
        "candidate_set": run.preparation.candidate_set,
        "candidate_permutation": run.preparation.permutation,
        "preparation": run.preparation,
        "selector_request": run.selector_request,
        "selector_token_ledger": run.token_ledger,
        "selector_transport": run.scripted_transport,
        "selector_response": run.selector_response,
        "acceptance_gate": run.acceptance_gate,
        "baseline_fallback": run.baseline_fallback,
        "execution_decision": run.execution_decision,
        "episode_result": run.episode_result,
        "selection_run": run,
    }
    return mapping[node_type]


def replay_scripted_selection_run(
    store: AppendOnlyArtifactStore,
    persisted: R02PersistedSelectionRun,
    episode: SyntheticEpisode,
    *,
    expected_selection_run_sha256: str,
    expected_audit_graph_sha256: str,
    expected_freeze_sha256: str,
    freeze_path: str | Path = DEFAULT_R02_FREEZE_PATH,
) -> R02SelectionReplayVerification:
    """Replay a terminal scripted D2b graph without provider or live access."""

    if expected_freeze_sha256 != R02_FREEZE_SHA256:
        raise R02ReplayError("unexpected R02 freeze identity")
    if persisted.selection_run.sha256 != expected_selection_run_sha256:
        raise R02ReplayError("selection-run anchor mismatch")
    if persisted.audit_graph.sha256 != expected_audit_graph_sha256:
        raise R02ReplayError("selection audit-graph anchor mismatch")
    try:
        run = R02SelectionRun.model_validate_json(
            store.read_bytes(persisted.selection_run)
        )
        graph = R02SelectionAuditGraph.model_validate_json(
            store.read_bytes(persisted.audit_graph)
        )
    except Exception as exc:
        raise R02ReplayError(f"selection anchor validation failed: {exc}") from exc
    if graph.identity != run.identity:
        raise R02ReplayError("selection graph identity mismatch")
    if graph.nodes[-1] != persisted.selection_run:
        raise R02ReplayError("selection graph does not terminate at the run anchor")
    if episode.public.case_id != run.identity.fixture_id:
        raise R02ReplayError("selection replay fixture ID mismatch")
    if episode.content_sha256 != run.identity.fixture_content_sha256:
        raise R02ReplayError("selection replay fixture content hash mismatch")

    for node_type, reference in zip(graph.node_types, graph.nodes, strict=True):
        if node_type == "selector_raw_response":
            try:
                actual_raw = store.read_bytes(reference).decode("utf-8")
            except (ArtifactIntegrityError, UnicodeDecodeError) as exc:
                raise R02ReplayError(f"invalid selector raw response: {exc}") from exc
            if actual_raw != run.raw_response:
                raise R02ReplayError("selector raw response does not match run")
            continue
        model = _SELECTION_NODE_MODELS.get(node_type)
        if model is None:
            raise R02ReplayError(f"unknown selection node type: {node_type}")
        try:
            actual = model.model_validate_json(store.read_bytes(reference))
        except (ArtifactIntegrityError, ValueError, TypeError) as exc:
            raise R02ReplayError(f"invalid {node_type} artifact: {exc}") from exc
        expected = _expected_selection_node(run, node_type, episode)
        if expected is None or canonical_json_bytes(actual) != canonical_json_bytes(expected):
            raise R02ReplayError(f"{node_type} artifact does not match selection run")

    reproduced_preparation = prepare_provider_free_episode(
        episode,
        experiment_id=run.identity.experiment_id,
        replicate_id=run.identity.replicate_id,
        provider_attempt_count=run.preparation.provider_attempt_count,
        freeze_path=freeze_path,
    )
    if canonical_json_bytes(reproduced_preparation) != canonical_json_bytes(run.preparation):
        raise R02ReplayError("D2a preparation mismatch during selection replay")
    exchange = R02ScriptedExchange(
        raw_response=run.raw_response,
        input_tokens=run.token_ledger.input_tokens,
        cached_input_tokens=run.token_ledger.cached_input_tokens,
        output_tokens=run.token_ledger.output_tokens,
        reasoning_output_tokens=run.token_ledger.reasoning_output_tokens,
    )
    client = ScriptedR02SelectorClient(
        (exchange,),
        initial_attempt_count=run.token_ledger.scripted_attempts_before,
    )
    reproduced_run = run_scripted_selector_episode(
        episode,
        reproduced_preparation,
        client,
    )
    if canonical_json_bytes(reproduced_run) != canonical_json_bytes(run):
        raise R02ReplayError("scripted selection replay mismatch")
    return R02SelectionReplayVerification(
        identity=run.identity,
        verified_artifacts=len(graph.nodes) + 1,
    )
