from __future__ import annotations

import json

import pytest

from . import runner
from .artifacts import (
    AppendOnlyArtifactStore,
    ArtifactExistsError,
    ArtifactIntegrityError,
)
from .contracts import ASSET_IDS, AcquisitionIdentity
from .llm_policy import ScriptedAcquisitionClient, acquisition_key
from .runner import (
    generate_development_manifest,
    main,
    replay,
    run_scripted_acquisition,
    scripted_response_template,
)


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


def _anchored_replay(store, result_ref, manifest_ref, *, persist=False):
    return replay(
        store,
        result_reference=result_ref,
        expected_manifest_sha256=manifest_ref.sha256,
        expected_result_sha256=result_ref.sha256,
        persist_verification=persist,
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
    for unsafe in ("../outside.txt", ".", "C:\\outside.txt", "a//b.txt"):
        with pytest.raises(ValueError, match="safe relative path"):
            store.write_text(unsafe, "forbidden")


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
    verification = _anchored_replay(store, result_ref, manifest_ref)
    assert verification.provider_calls == 0
    assert verification.verified_acquisitions == 1
    anchored = _anchored_replay(store, result_ref, manifest_ref)
    assert anchored.all_hashes_match
    with pytest.raises(RuntimeError, match="run-result hash"):
        replay(
            store,
            result_reference=result_ref,
            persist_verification=False,
            expected_manifest_sha256=manifest_ref.sha256,
            expected_result_sha256="0" * 64,
        )
    with pytest.raises(RuntimeError, match="manifest hash"):
        replay(
            store,
            result_reference=result_ref,
            persist_verification=False,
            expected_manifest_sha256="0" * 64,
            expected_result_sha256=result_ref.sha256,
        )
    with pytest.raises(SystemExit):
        main(
            [
                "--artifact-root",
                str(tmp_path),
                "verify",
                "--result",
                result_ref.relative_path,
            ]
        )


def test_scripted_template_cli_emits_production_acquisition_keys(tmp_path, capsys) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    manifest_ref, manifest = generate_development_manifest(
        store,
        experiment_id="template-test",
        root_seed="template-seed",
        contract_bytes=b"draft-contract",
        count=1,
    )
    output = tmp_path / "scripted-responses.json"
    assert (
        main(
            [
                "--artifact-root",
                str(tmp_path),
                "scripted-template",
                "--manifest",
                manifest_ref.relative_path,
                "--replicates",
                "2",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    capsys.readouterr()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == scripted_response_template(manifest, 2)
    assert len(payload) == 2


def test_oracle_is_cached_once_per_fixture_in_acquisition_and_replay(tmp_path, monkeypatch) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    manifest_ref, manifest = generate_development_manifest(
        store,
        experiment_id="oracle-cache-test",
        root_seed="oracle-cache-seed",
        contract_bytes=b"draft-contract",
        count=1,
    )
    identities = [
        AcquisitionIdentity(
            experiment_id="oracle-cache-test",
            case_id=manifest.fixtures[0].case_id,
            channel="development",
            replicate_id=replicate,
            attempt=1,
        )
        for replicate in range(2)
    ]
    client = ScriptedAcquisitionClient({acquisition_key(identity): _hold_raw() for identity in identities})
    real_solve_oracle = runner.solve_oracle
    calls = 0

    def counted_solve_oracle(episode):
        nonlocal calls
        calls += 1
        return real_solve_oracle(episode)

    monkeypatch.setattr(runner, "solve_oracle", counted_solve_oracle)
    result_ref, _result = run_scripted_acquisition(
        store,
        manifest_reference=manifest_ref,
        client=client,
        replicates=2,
    )
    assert calls == 1
    calls = 0
    _anchored_replay(store, result_ref, manifest_ref)
    assert calls == 1


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
        _anchored_replay(store, result_ref, manifest_ref)


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
        _anchored_replay(store, result_ref, manifest_ref)
