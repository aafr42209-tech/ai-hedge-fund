"""Hash-anchored replay for the provider-free R02 D3 zero-call preflight."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .artifacts import ArtifactError
from .canonical import canonical_json_bytes, canonical_sha256
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d3_contracts import (
    R02_D3_NODE_TYPES,
    R02D3PersistedPreflight,
    R02D3PreflightAuditGraph,
    R02D3ReplayVerification,
    R02D3TransportSnapshot,
    R02D3ZeroCallAssertions,
    R02D3ZeroCallPreflight,
    selector_output_schema,
)
from .r02_d3_preflight import (
    LocalCommandRunner,
    R02D3Preregistration,
    build_preregistration,
    build_zero_call_preflight,
    capture_transport_snapshot,
)


class R02D3ReplayError(RuntimeError):
    pass


def _load_json_object(raw: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise R02D3ReplayError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise R02D3ReplayError(f"{label} is not a JSON object")
    return value


def replay_zero_call_preflight(
    store: R02AppendOnlyArtifactStore,
    persisted: R02D3PersistedPreflight,
    repository_root: str | Path,
    *,
    authorization_sha256: str,
    expected_preflight_sha256: str,
    expected_audit_graph_sha256: str,
    runner: LocalCommandRunner,
) -> R02D3ReplayVerification:
    if persisted.preflight.sha256 != expected_preflight_sha256:
        raise R02D3ReplayError("preflight anchor mismatch")
    if persisted.audit_graph.sha256 != expected_audit_graph_sha256:
        raise R02D3ReplayError("preflight audit-graph anchor mismatch")
    try:
        graph = R02D3PreflightAuditGraph.model_validate_json(
            store.read_bytes(persisted.audit_graph)
        )
    except (ArtifactError, ValidationError, ValueError) as exc:
        raise R02D3ReplayError(f"preflight graph validation failed: {exc}") from exc
    if graph.node_types != R02_D3_NODE_TYPES:
        raise R02D3ReplayError("preflight graph node order mismatch")
    if graph.nodes[-1] != persisted.preflight:
        raise R02D3ReplayError("preflight graph does not terminate at the preflight anchor")

    raw_nodes: list[bytes] = []
    try:
        for reference in graph.nodes:
            raw_nodes.append(store.read_bytes(reference))
    except ArtifactError as exc:
        raise R02D3ReplayError(f"preflight node integrity failed: {exc}") from exc

    try:
        preregistration = R02D3Preregistration.model_validate_json(raw_nodes[0])
        output_schema = _load_json_object(raw_nodes[1], "selector output schema")
        transport = R02D3TransportSnapshot.model_validate_json(raw_nodes[2])
        assertions = R02D3ZeroCallAssertions.model_validate_json(raw_nodes[3])
        preflight = R02D3ZeroCallPreflight.model_validate_json(raw_nodes[4])
    except (ValidationError, ValueError) as exc:
        raise R02D3ReplayError(f"preflight node validation failed: {exc}") from exc

    expected_node_bytes = (
        canonical_json_bytes(preregistration),
        canonical_json_bytes(output_schema),
        canonical_json_bytes(transport),
        canonical_json_bytes(assertions),
        canonical_json_bytes(preflight),
    )
    if tuple(raw_nodes) != expected_node_bytes:
        raise R02D3ReplayError("preflight node bytes are not canonical")
    if output_schema != selector_output_schema():
        raise R02D3ReplayError("selector output schema did not reproduce")
    if preflight.assertions != assertions:
        raise R02D3ReplayError("preflight assertion node mismatch")
    if preflight.preregistration_sha256 != canonical_sha256(preregistration):
        raise R02D3ReplayError("preflight preregistration hash mismatch")
    if preflight.transport_snapshot_sha256 != canonical_sha256(transport):
        raise R02D3ReplayError("preflight transport hash mismatch")

    rebuilt_preregistration = build_preregistration(
        repository_root,
        authorization_sha256=authorization_sha256,
        executable_path=preregistration.model_identity.executable_path,
    )
    if canonical_json_bytes(rebuilt_preregistration) != raw_nodes[0]:
        raise R02D3ReplayError("preregistration did not reproduce byte-for-byte")
    recaptured_transport = capture_transport_snapshot(rebuilt_preregistration, runner)
    if canonical_json_bytes(recaptured_transport) != raw_nodes[2]:
        raise R02D3ReplayError("zero-call transport did not recapture byte-for-byte")
    rebuilt_preflight = build_zero_call_preflight(
        repository_root,
        rebuilt_preregistration,
        recaptured_transport,
    )
    if canonical_json_bytes(rebuilt_preflight) != raw_nodes[4]:
        raise R02D3ReplayError("zero-call preflight did not reproduce byte-for-byte")

    return R02D3ReplayVerification(
        preflight_id=preflight.preflight_id,
    )
