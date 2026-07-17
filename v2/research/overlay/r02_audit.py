"""Append-only persistence for the provider-free R02 D2a audit graph."""

from __future__ import annotations

from pathlib import Path

from .artifacts import AppendOnlyArtifactStore, ArtifactError
from .contracts import SyntheticEpisode, normalize_artifact_relative_path
from .r02_contracts import (
    R02AuditGraph,
    R02PersistedPreparation,
    R02PreparationState,
    R02ProviderFreePreparation,
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


def persist_provider_free_preparation(
    store: AppendOnlyArtifactStore,
    prefix: str,
    episode: SyntheticEpisode,
    preparation: R02ProviderFreePreparation,
) -> R02PersistedPreparation:
    """Persist one immutable R02 preparation graph and return its two anchors."""

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
