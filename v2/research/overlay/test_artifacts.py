from __future__ import annotations

import json

import pytest

from .artifacts import (
    AppendOnlyArtifactStore,
    ArtifactExistsError,
    ArtifactIntegrityError,
)
from .contracts import ASSET_IDS, AcquisitionIdentity
from .llm_policy import ScriptedAcquisitionClient, acquisition_key
from .runner import generate_development_manifest, replay, run_scripted_acquisition


def _hold_raw() -> str:
    return json.dumps(
        {
            "decisions": {
                asset_id: {
                    "action": "hold",
                    "quantity": 0,
                    "confidence": 50,
                    "reasoning": "scripted",
                }
                for asset_id in ASSET_IDS
            }
        },
        separators=(",", ":"),
    )


def test_artifact_store_is_append_only_and_hash_verified(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    reference = store.write_text("x/value.txt", "first")
    with pytest.raises(ArtifactExistsError):
        store.write_text("x/value.txt", "second")
    assert store.read_bytes(reference) == b"first"
    (tmp_path / "x" / "value.txt").write_text("tampered")
    with pytest.raises(ArtifactIntegrityError):
        store.read_bytes(reference)


def test_artifact_store_rejects_path_escape(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    with pytest.raises(ValueError, match="safe relative path"):
        store.write_text("../outside.txt", "forbidden")


def test_scripted_run_and_zero_call_replay_are_byte_identical(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    manifest_ref, manifest = generate_development_manifest(
        store,
        experiment_id="artifact-test",
        root_seed="artifact-seed",
        contract_bytes=b"draft-contract",
        count=1,
    )
    assert manifest.scoring_spec.sha256 == manifest.scoring_spec_sha256
    assert manifest.analysis_spec.sha256 == manifest.analysis_spec_sha256
    store.verify(manifest.scoring_spec)
    store.verify(manifest.analysis_spec)
    identity = AcquisitionIdentity(
        experiment_id="artifact-test",
        case_id=manifest.fixtures[0].case_id,
        channel="development",
        replicate_id=0,
        attempt=1,
    )
    client = ScriptedAcquisitionClient({acquisition_key(identity): _hold_raw()})
    result_ref, result = run_scripted_acquisition(
        store,
        manifest_reference=manifest_ref,
        client=client,
    )
    assert client.provider_calls == 1
    acquisition = result.acquisitions[0]
    assert store.read_bytes(acquisition.raw_response) == _hold_raw().encode()
    verification = replay(store, result_reference=result_ref, persist_verification=False)
    assert verification.provider_calls == 0
    assert verification.verified_acquisitions == 1


def test_replay_fails_on_tampered_derived_artifact(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    manifest_ref, manifest = generate_development_manifest(
        store,
        experiment_id="tamper-test",
        root_seed="tamper-seed",
        contract_bytes=b"draft-contract",
        count=1,
    )
    identity = AcquisitionIdentity(
        experiment_id="tamper-test",
        case_id=manifest.fixtures[0].case_id,
        channel="development",
        replicate_id=0,
        attempt=1,
    )
    result_ref, result = run_scripted_acquisition(
        store,
        manifest_reference=manifest_ref,
        client=ScriptedAcquisitionClient({acquisition_key(identity): _hold_raw()}),
    )
    score_path = tmp_path / result.acquisitions[0].episode_score.relative_path
    score_path.write_bytes(b"{}")
    with pytest.raises(ArtifactIntegrityError):
        replay(store, result_reference=result_ref, persist_verification=False)


def test_replay_fails_on_tampered_machine_spec(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    manifest_ref, manifest = generate_development_manifest(
        store,
        experiment_id="spec-tamper-test",
        root_seed="spec-tamper-seed",
        contract_bytes=b"draft-contract",
        count=1,
    )
    identity = AcquisitionIdentity(
        experiment_id="spec-tamper-test",
        case_id=manifest.fixtures[0].case_id,
        channel="development",
        replicate_id=0,
        attempt=1,
    )
    result_ref, _result = run_scripted_acquisition(
        store,
        manifest_reference=manifest_ref,
        client=ScriptedAcquisitionClient({acquisition_key(identity): _hold_raw()}),
    )
    (tmp_path / manifest.scoring_spec.relative_path).write_bytes(b"{}")
    with pytest.raises(ArtifactIntegrityError):
        replay(store, result_reference=result_ref, persist_verification=False)
