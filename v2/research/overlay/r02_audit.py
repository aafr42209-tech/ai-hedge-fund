"""Append-only persistence for the provider-free R02 D2a audit graph."""

from __future__ import annotations

from pathlib import Path

from .artifacts import AppendOnlyArtifactStore, ArtifactError
from .contracts import SyntheticEpisode, normalize_artifact_relative_path
from .r02_contracts import (
    R02AuditGraph,
    R02PersistedPreparation,
    R02PersistedSelectionRun,
    R02PreparationState,
    R02ProviderFreePreparation,
    R02SelectionAuditGraph,
    R02SelectionRun,
)

DEFAULT_R02_ARTIFACT_ROOT = Path(".research_artifacts/r02")


class R02ArtifactRootError(ArtifactError):
    pass


def _targets_r01_artifact_tree(root: str | Path) -> bool:
    resolved = Path(root).resolve()
    for candidate in (resolved, *resolved.parents):
        name = candidate.name.lower()
        if candidate.parent.name.lower() == ".research_artifacts" and (
            name == "r01" or name.startswith("r01-")
        ):
            return True
    return False


class R02AppendOnlyArtifactStore(AppendOnlyArtifactStore):
    """R02 store that rejects every sealed R01 artifact root and descendant."""

    def __init__(self, root: str | Path = DEFAULT_R02_ARTIFACT_ROOT) -> None:
        if _targets_r01_artifact_tree(root):
            raise R02ArtifactRootError("R02 store cannot target an R01 artifact tree")
        super().__init__(root)


def _ensure_r02_artifact_root(store: AppendOnlyArtifactStore) -> None:
    if _targets_r01_artifact_tree(store.root):
        raise R02ArtifactRootError("R02 persistence cannot target an R01 artifact tree")


def persist_provider_free_preparation(
    store: AppendOnlyArtifactStore,
    prefix: str,
    episode: SyntheticEpisode,
    preparation: R02ProviderFreePreparation,
) -> R02PersistedPreparation:
    """Persist one immutable R02 preparation graph and return its two anchors."""

    _ensure_r02_artifact_root(store)
    normalized_prefix = normalize_artifact_relative_path(prefix).rstrip("/")
    if episode.public.case_id != preparation.identity.fixture_id:
        raise ValueError("fixture ID does not match preparation identity")
    if episode.content_sha256 != preparation.identity.fixture_content_sha256:
        raise ValueError("fixture content hash does not match preparation identity")

    node_types: list[str] = []
    nodes = []

    def write(node_type: str, filename: str, value: object) -> None:
        node_types.append(node_type)
        nodes.append(store.write_json(f"{normalized_prefix}/{filename}", value))

    write("public_fixture", "public_fixture.json", episode.public)
    write("eligibility_decision", "eligibility_decision.json", preparation.eligibility)
    if preparation.candidate_set is not None:
        write("candidate_set", "candidate_set.json", preparation.candidate_set)
    if preparation.permutation is not None:
        write("candidate_permutation", "candidate_permutation.json", preparation.permutation)
    if preparation.no_call is not None:
        write("no_call_record", "no_call_record.json", preparation.no_call)
    if preparation.execution_decision is not None:
        write("execution_decision", "execution_decision.json", preparation.execution_decision)
    if preparation.episode_result is not None:
        write("episode_result", "episode_result.json", preparation.episode_result)
    preparation_ref = store.write_json(
        f"{normalized_prefix}/preparation.json",
        preparation,
    )
    node_types.append("preparation")
    nodes.append(preparation_ref)
    graph = R02AuditGraph(
        identity=preparation.identity,
        preparation_state=preparation.state,
        node_types=tuple(node_types),
        nodes=tuple(nodes),
        terminal=preparation.state is R02PreparationState.NO_CALL_TERMINAL,
    )
    graph_ref = store.write_json(f"{normalized_prefix}/audit_graph.json", graph)
    return R02PersistedPreparation(
        preparation=preparation_ref,
        audit_graph=graph_ref,
    )


def persist_scripted_selection_run(
    store: AppendOnlyArtifactStore,
    prefix: str,
    episode: SyntheticEpisode,
    run: R02SelectionRun,
) -> R02PersistedSelectionRun:
    """Persist one terminal D2b scripted selection graph without provider access."""

    _ensure_r02_artifact_root(store)
    normalized_prefix = normalize_artifact_relative_path(prefix).rstrip("/")
    if episode.public.case_id != run.identity.fixture_id:
        raise ValueError("fixture ID does not match selection-run identity")
    if episode.content_sha256 != run.identity.fixture_content_sha256:
        raise ValueError("fixture content hash does not match selection-run identity")

    node_types: list[str] = []
    nodes = []

    def write_json(node_type: str, filename: str, value: object) -> None:
        node_types.append(node_type)
        nodes.append(store.write_json(f"{normalized_prefix}/{filename}", value))

    write_json("public_fixture", "public_fixture.json", episode.public)
    write_json("eligibility_decision", "eligibility_decision.json", run.preparation.eligibility)
    write_json("candidate_set", "candidate_set.json", run.preparation.candidate_set)
    write_json(
        "candidate_permutation",
        "candidate_permutation.json",
        run.preparation.permutation,
    )
    write_json("preparation", "preparation.json", run.preparation)
    write_json("selector_request", "selector_request.json", run.selector_request)
    write_json("selector_token_ledger", "selector_token_ledger.json", run.token_ledger)
    write_json("selector_transport", "selector_transport.json", run.scripted_transport)
    node_types.append("selector_raw_response")
    nodes.append(
        store.write_text(
            f"{normalized_prefix}/selector_raw_response.txt",
            run.raw_response,
        )
    )
    write_json("selector_response", "selector_response.json", run.selector_response)
    write_json("acceptance_gate", "acceptance_gate.json", run.acceptance_gate)
    if run.baseline_fallback is not None:
        write_json(
            "baseline_fallback",
            "baseline_fallback.json",
            run.baseline_fallback,
        )
    write_json("execution_decision", "execution_decision.json", run.execution_decision)
    write_json("episode_result", "episode_result.json", run.episode_result)
    selection_run_ref = store.write_json(
        f"{normalized_prefix}/selection_run.json",
        run,
    )
    node_types.append("selection_run")
    nodes.append(selection_run_ref)
    graph = R02SelectionAuditGraph(
        identity=run.identity,
        node_types=tuple(node_types),
        nodes=tuple(nodes),
    )
    graph_ref = store.write_json(f"{normalized_prefix}/audit_graph.json", graph)
    return R02PersistedSelectionRun(
        selection_run=selection_run_ref,
        audit_graph=graph_ref,
    )
