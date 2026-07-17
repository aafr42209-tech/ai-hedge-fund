from __future__ import annotations

import json

import pytest

from .artifacts import ArtifactExistsError
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_d3_preflight import (
    R02D3PersistedPreflight,
    build_zero_call_preflight,
    persist_zero_call_preflight,
)
from .r02_d3_replay import R02D3ReplayError, replay_zero_call_preflight
from .test_r02_d3_preflight import (
    ROOT,
    FakeZeroCallRunner,
    _authorization_sha256,
    _preregistration,
    _transport_snapshot,
)


def _persist(tmp_path):
    preregistration = _preregistration()
    transport = _transport_snapshot()
    preflight = build_zero_call_preflight(ROOT, preregistration, transport)
    store = R02AppendOnlyArtifactStore(tmp_path / ".research_artifacts" / "r02-d3-test")
    persisted = persist_zero_call_preflight(
        store,
        preflight.preflight_id,
        preregistration,
        transport,
        preflight,
    )
    return preregistration, transport, preflight, store, persisted


def test_preflight_persistence_and_recapture_replay_are_byte_exact(tmp_path) -> None:
    preregistration, _transport, preflight, store, persisted = _persist(tmp_path)
    verification = replay_zero_call_preflight(
        store,
        persisted,
        ROOT,
        authorization_sha256=_authorization_sha256(),
        expected_preflight_sha256=persisted.preflight.sha256,
        expected_audit_graph_sha256=persisted.audit_graph.sha256,
        runner=FakeZeroCallRunner(preregistration),
    )
    assert verification.preflight_id == preflight.preflight_id
    assert verification.verified_artifacts == 6
    assert verification.transport_recaptured is True
    assert verification.provider_calls == 0
    assert verification.live_execution is False


def test_preflight_persistence_is_append_only(tmp_path) -> None:
    preregistration, transport, preflight, store, _persisted = _persist(tmp_path)
    with pytest.raises(ArtifactExistsError):
        persist_zero_call_preflight(
            store,
            preflight.preflight_id,
            preregistration,
            transport,
            preflight,
        )


def test_preflight_replay_rejects_anchor_mismatch(tmp_path) -> None:
    preregistration, _transport, _preflight, store, persisted = _persist(tmp_path)
    with pytest.raises(R02D3ReplayError, match="preflight anchor mismatch"):
        replay_zero_call_preflight(
            store,
            persisted,
            ROOT,
            authorization_sha256=_authorization_sha256(),
            expected_preflight_sha256="0" * 64,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            runner=FakeZeroCallRunner(preregistration),
        )


def test_preflight_replay_rejects_node_byte_tamper(tmp_path) -> None:
    preregistration, _transport, _preflight, store, persisted = _persist(tmp_path)
    graph = json.loads(store.read_bytes(persisted.audit_graph))
    transport_reference = graph["nodes"][2]
    (store.root / transport_reference["relative_path"]).write_bytes(b"{}")
    with pytest.raises(R02D3ReplayError, match="node integrity failed"):
        replay_zero_call_preflight(
            store,
            persisted,
            ROOT,
            authorization_sha256=_authorization_sha256(),
            expected_preflight_sha256=persisted.preflight.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            runner=FakeZeroCallRunner(preregistration),
        )


def test_preflight_replay_rejects_persisted_reference_drift(tmp_path) -> None:
    preregistration, _transport, _preflight, store, persisted = _persist(tmp_path)
    raw = json.loads(persisted.model_dump_json())
    raw["preflight"]["sha256"] = "f" * 64
    drifted = R02D3PersistedPreflight.model_validate(raw)
    with pytest.raises(R02D3ReplayError, match="preflight anchor mismatch"):
        replay_zero_call_preflight(
            store,
            drifted,
            ROOT,
            authorization_sha256=_authorization_sha256(),
            expected_preflight_sha256=persisted.preflight.sha256,
            expected_audit_graph_sha256=persisted.audit_graph.sha256,
            runner=FakeZeroCallRunner(preregistration),
        )
