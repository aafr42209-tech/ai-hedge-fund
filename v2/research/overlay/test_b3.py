from __future__ import annotations

import json

import pytest

from . import b3, runner
from .artifacts import AppendOnlyArtifactStore
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .codex_exec_client import (
    codex_transport_shape_spec_sha256,
    CodexExecClient,
    CodexExecError,
    CodexProcessCapture,
    SubprocessCodexProcessRunner,
)
from .codex_preflight import pilot_sandbox_identity_sha256
from .contracts import (
    AcquisitionDisposition,
    AcquisitionFailureRecord,
    AcquisitionIdentity,
    CodexAttemptTransportArtifacts,
    CodexFeatureCatalogEntry,
    CodexFeatureGate,
    DevelopmentBudgetCarryForward,
    DevelopmentManifest,
    DevelopmentTokenBudgetSummary,
    REGIMES,
    RunPlanEntry,
    TokenBudgetReservation,
)
from .freeze import generate_provider_free_freeze
from .lattice import hold_batch
from .llm_policy import ScriptedAcquisitionClient
from .oracle import solve_oracle


def _carry_forward() -> DevelopmentBudgetCarryForward:
    return DevelopmentBudgetCarryForward(
        source_kind="STOP_RECORD",
        source_experiment_id="stopped-b3-test",
        source_preflight_sha256="a" * 64,
        source_failure_sha256="b" * 64,
        source_stop_report_sha256="c" * 64,
        provider_attempts=1,
        successful_responses=0,
        failed_or_unsettled_attempts=1,
        actual_total_tokens=0,
        observed_unsettled_actual_tokens=13_651,
        conservatively_charged_total_tokens=32_000,
    )


def _development_manifest(store, *, experiment_id: str, root_seed: str):
    freeze_sha256 = canonical_sha256(generate_provider_free_freeze(root_seed_label=root_seed, count=40))
    reference, manifest = runner.generate_development_manifest(
        store,
        experiment_id=experiment_id,
        root_seed=root_seed,
        contract_bytes=b"b3-test-contract",
        expected_freeze_sha256=freeze_sha256,
        count=40,
    )
    return reference, manifest


def _minimal_feature_gate() -> CodexFeatureGate:
    catalog = tuple(CodexFeatureCatalogEntry(name=name, stage="removed", enabled=True) for name in b3.ACTIVE_FEATURE_ALLOWLIST)
    return CodexFeatureGate(
        feature_catalog=catalog,
        feature_catalog_sha256=canonical_sha256(catalog),
        feature_catalog_definition_sha256=canonical_sha256(tuple({"name": entry.name, "stage": entry.stage} for entry in catalog)),
        baseline_effective_true_features=b3.ACTIVE_FEATURE_ALLOWLIST,
        active_feature_allowlist=b3.ACTIVE_FEATURE_ALLOWLIST,
        disabled_features=(),
        post_disable_effective_true_features=b3.ACTIVE_FEATURE_ALLOWLIST,
    )


def _jsonl_capture(*, include_message: bool) -> CodexProcessCapture:
    events: list[dict[str, object]] = [
        {"type": "thread.started", "thread_id": "b3-thread"},
        {"type": "turn.started"},
    ]
    if include_message:
        events.append(
            {
                "type": "item.completed",
                "item": {
                    "id": "message-1",
                    "type": "agent_message",
                    "text": canonical_json_bytes(hold_batch()).decode("utf-8"),
                },
            }
        )
    events.append(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "output_tokens": 20,
                "reasoning_output_tokens": 5,
            },
        }
    )
    stdout = ("\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n").encode()
    return CodexProcessCapture(
        stdout=stdout,
        stderr=b"",
        exit_code=0,
        duration_ms=1,
    )


class _SequenceRunner:
    def __init__(self, captures, *, drift_directory=None) -> None:
        self.captures = list(captures)
        self.calls = 0
        self.drift_directory = drift_directory

    def run(self, **kwargs):
        del kwargs
        capture = self.captures[self.calls]
        self.calls += 1
        if self.drift_directory is not None and self.calls == 1:
            (self.drift_directory / "unexpected-file").write_text("drift", encoding="utf-8")
        return capture


def _live_test_client(store, sandbox, process_runner) -> CodexExecClient:
    gate = _minimal_feature_gate()
    return CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        feature_catalog=gate.feature_catalog,
        expected_feature_catalog_sha256=gate.feature_catalog_sha256,
        disabled_features=gate.disabled_features,
        active_feature_allowlist=gate.active_feature_allowlist,
        post_disable_effective_true_features=gate.post_disable_effective_true_features,
        config_overrides=("tools.web_search=false",),
        working_directory=str(sandbox),
        expected_pilot_sandbox_sha256=pilot_sandbox_identity_sha256(str(sandbox)),
        expected_transport_shape_spec_sha256=codex_transport_shape_spec_sha256(),
        timeout_ms=30_000,
        process_runner=process_runner,
        transport_store=store,
    )


def test_b3_anchor_manifest_selects_one_frozen_case_per_regime(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    manifest_reference, manifest = _development_manifest(
        store,
        experiment_id="b3-anchor-test",
        root_seed="b3-anchor-seed",
    )

    anchor_reference, anchors = runner.build_b3_anchor_manifest(
        store,
        manifest_reference=manifest_reference,
        manifest=manifest,
    )

    assert anchor_reference.sha256 == canonical_sha256(anchors)
    assert tuple(anchor.regime for anchor in anchors.anchors) == REGIMES
    assert tuple(anchor.case_id for anchor in anchors.anchors) == tuple(min(fixture.case_id for fixture in manifest.fixtures if fixture.regime == regime) for regime in REGIMES)
    assert len(runner.b3_acquisition_identities(anchors)) == 12


def test_b3_scripted_micro_pilot_binds_token_budget_and_replays(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    manifest_reference, manifest = _development_manifest(
        store,
        experiment_id="b3-scripted-test",
        root_seed="b3-scripted-seed",
    )
    anchor_reference, _anchors = runner.build_b3_anchor_manifest(
        store,
        manifest_reference=manifest_reference,
        manifest=manifest,
    )
    client = ScriptedAcquisitionClient(runner.scripted_response_template(manifest, 2))

    result_reference, result = runner.run_b3_micro_pilot(
        store,
        manifest_reference=manifest_reference,
        anchor_manifest_reference=anchor_reference,
        client=client,
        expected_freeze_sha256=manifest.provider_free_freeze_sha256,
        expected_anchor_manifest_sha256=anchor_reference.sha256,
        budget_carry_forward=_carry_forward(),
    )

    assert client.provider_calls == 12
    assert len(result.acquisitions) == 12
    assert result.schema_version == "r01-development-run-result-v4"
    summary = DevelopmentTokenBudgetSummary.model_validate_json(store.read_bytes(result.token_budget_summary))
    assert summary.provider_attempts == 13
    assert summary.successful_responses == 12
    assert summary.failed_or_unsettled_attempts == 1
    assert summary.actual_total_tokens == 0
    assert summary.conservatively_charged_total_tokens == 32_000
    assert summary.carry_forward == _carry_forward()
    first_reservation = TokenBudgetReservation.model_validate_json(store.read_bytes(result.acquisitions[0].token_reservation))
    assert first_reservation.provider_attempt_ordinal == 2
    assert first_reservation.charged_total_tokens_before == 32_000
    verification = runner.replay(
        store,
        result_reference=result_reference,
        expected_freeze_sha256=manifest.provider_free_freeze_sha256,
        expected_manifest_sha256=manifest_reference.sha256,
        expected_result_sha256=result_reference.sha256,
        persist_verification=False,
    )
    assert verification.verified_acquisitions == 12


def test_b3_preflight_is_provider_free_and_binds_reviewed_command_specs(
    tmp_path,
    monkeypatch,
) -> None:
    artifact_root = tmp_path / "artifacts"
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    store = AppendOnlyArtifactStore(artifact_root)
    manifest_reference, manifest = _development_manifest(
        store,
        experiment_id="b3-preflight-test",
        root_seed="b3-preflight-seed",
    )
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"pinned-test-executable")
    attestation = tmp_path / "attestation.md"
    attestation.write_text("zero cost attested", encoding="utf-8")
    carry_forward = tmp_path / "budget-carry-forward.json"
    carry_forward.write_bytes(canonical_json_bytes(_carry_forward()))
    gate = _minimal_feature_gate()
    monkeypatch.setattr(
        b3,
        "_current_feature_gate",
        lambda *args, **kwargs: ({"codex_cli_version": b3.EXPECTED_CLI_VERSION}, gate),
    )

    preflight_reference, preflight = b3.prepare_b3_preflight(
        store,
        manifest_reference=manifest_reference,
        expected_freeze_sha256=manifest.provider_free_freeze_sha256,
        executable=str(executable),
        expected_executable_sha256=sha256_hex(executable.read_bytes()),
        sandbox_directory=str(sandbox),
        account_attestation_path=attestation,
        expected_account_attestation_sha256=sha256_hex(attestation.read_bytes()),
        budget_carry_forward_path=carry_forward,
        expected_budget_carry_forward_sha256=sha256_hex(carry_forward.read_bytes()),
        committed_capture_path=tmp_path / "unused.json",
    )

    assert preflight.provider_calls == 0
    assert preflight.schema_version == "r01-b3-preflight-v2"
    assert preflight.budget_carry_forward == _carry_forward()
    assert len(preflight.command_specs) == 6
    assert len(list(sandbox.iterdir())) == 0
    client, rebuilt = b3.build_live_b3_client(
        store,
        preflight_reference=preflight_reference,
        expected_preflight_sha256=preflight_reference.sha256,
        sandbox_directory=str(sandbox),
        account_attestation_path=attestation,
        budget_carry_forward_path=carry_forward,
        committed_capture_path=tmp_path / "unused.json",
    )
    assert client.provider_calls == 0
    assert rebuilt == preflight


def test_retry_failure_transport_is_bound_and_replayed(tmp_path) -> None:
    artifact_root = tmp_path / "artifacts"
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    store = AppendOnlyArtifactStore(artifact_root)
    freeze_sha256 = canonical_sha256(generate_provider_free_freeze(root_seed_label="retry-transport-seed", count=1))
    manifest_reference, manifest = runner.generate_development_manifest(
        store,
        experiment_id="retry-transport-test",
        root_seed="retry-transport-seed",
        contract_bytes=b"retry-transport-contract",
        expected_freeze_sha256=freeze_sha256,
        count=1,
    )
    process_runner = _SequenceRunner((_jsonl_capture(include_message=False), _jsonl_capture(include_message=True)))
    client = _live_test_client(store, sandbox, process_runner)

    result_reference, result = runner.run_scripted_acquisition(
        store,
        manifest_reference=manifest_reference,
        client=client,
        expected_freeze_sha256=manifest.provider_free_freeze_sha256,
    )

    failure = AcquisitionFailureRecord.model_validate_json(store.read_bytes(result.acquisitions[0].prior_attempt_failures[0]))
    assert failure.transport_artifacts is not None
    for reference in (
        failure.transport_artifacts.command_spec,
        failure.transport_artifacts.stdout_jsonl,
        failure.transport_artifacts.stderr,
        failure.transport_artifacts.process_status,
    ):
        store.verify(reference)
    verification = runner.replay(
        store,
        result_reference=result_reference,
        expected_freeze_sha256=manifest.provider_free_freeze_sha256,
        expected_manifest_sha256=manifest_reference.sha256,
        expected_result_sha256=result_reference.sha256,
        persist_verification=False,
    )
    assert verification.verified_acquisitions == 1


def test_retry_sandbox_drift_writes_classified_second_failure(tmp_path) -> None:
    artifact_root = tmp_path / "artifacts"
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    store = AppendOnlyArtifactStore(artifact_root)
    freeze_sha256 = canonical_sha256(generate_provider_free_freeze(root_seed_label="sandbox-drift-seed", count=1))
    manifest_reference, manifest = runner.generate_development_manifest(
        store,
        experiment_id="sandbox-drift-test",
        root_seed="sandbox-drift-seed",
        contract_bytes=b"sandbox-drift-contract",
        expected_freeze_sha256=freeze_sha256,
        count=1,
    )
    process_runner = _SequenceRunner(
        (_jsonl_capture(include_message=False),),
        drift_directory=sandbox,
    )
    client = _live_test_client(store, sandbox, process_runner)

    with pytest.raises(CodexExecError) as raised:
        runner.run_scripted_acquisition(
            store,
            manifest_reference=manifest_reference,
            client=client,
            expected_freeze_sha256=manifest.provider_free_freeze_sha256,
        )

    assert raised.value.code == "command_spec_build_failure"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    case_id = manifest.fixtures[0].case_id
    first = AcquisitionFailureRecord.model_validate_json(store.read_bytes(store.reference_for_existing(f"sandbox-drift-test/acquisitions/{case_id}/development/replicate-000/attempt-1/acquisition_failure.json")))
    second = AcquisitionFailureRecord.model_validate_json(store.read_bytes(store.reference_for_existing(f"sandbox-drift-test/acquisitions/{case_id}/development/replicate-000/attempt-2/acquisition_failure.json")))
    assert first.transport_artifacts is not None
    assert second.code == "command_spec_build_failure"
    assert second.transport_artifacts is None
    assert process_runner.calls == 1


def test_per_attempt_token_reserve_excess_stops_after_one_response(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    fixture = runner.generate_development_episodes(  # type: ignore[attr-defined]
        runner.GeneratorConfig(),
        "token-reserve-test",
        1,
    )[0]
    fixture_reference = store.write_json("fixtures/token-reserve.json", fixture)
    identity = AcquisitionIdentity(
        experiment_id="token-reserve-test",
        case_id=fixture.public.case_id,
        channel="development",
        replicate_id=0,
        attempt=1,
    )
    raw = json.dumps(hold_batch().model_dump(mode="json"))
    transport_artifacts = CodexAttemptTransportArtifacts(
        command_spec=store.write_text("transport/command_spec.json", "{}"),
        stdout_jsonl=store.write_text("transport/stdout.jsonl", "{}\n"),
        stderr=store.write_bytes("transport/stderr.bin", b""),
        process_status=store.write_text("transport/process_status.json", "{}"),
        provider_response=store.write_text("transport/provider_response.json", "{}"),
    )

    class HighUsageClient:
        provider_calls = 0

        def complete(self, *, system, user, identity):
            self.provider_calls += 1
            response = ScriptedAcquisitionClient({runner.acquisition_key(identity): raw}).complete(system=system, user=user, identity=identity)
            return response.model_copy(
                update={
                    "input_tokens": 32_000,
                    "output_tokens": 1,
                    "reasoning_output_tokens": 0,
                }
            )

        def transport_artifacts_for(self, identity):
            return transport_artifacts

    client = HighUsageClient()
    with pytest.raises(CodexExecError) as raised:
        runner._complete_acquisition(
            store,
            entry=RunPlanEntry(identity=identity, fixture=fixture_reference),
            episode=fixture,
            client=client,
            oracle=solve_oracle(fixture),
        )
    assert raised.value.code == "per_attempt_token_reserve_exceeded"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert client.provider_calls == 1
    prefix = f"token-reserve-test/acquisitions/{fixture.public.case_id}/development/replicate-000/attempt-1"
    failure = AcquisitionFailureRecord.model_validate_json(store.read_bytes(store.reference_for_existing(f"{prefix}/acquisition_failure.json")))
    assert failure.schema_version == "r01-acquisition-failure-v3"
    assert failure.token_reservation is not None
    assert failure.post_response_artifacts is not None
    assert failure.post_response_artifacts.transport_artifacts == transport_artifacts
    for reference in (
        failure.token_reservation,
        failure.post_response_artifacts.policy_input,
        failure.post_response_artifacts.system_prompt,
        failure.post_response_artifacts.user_prompt,
        failure.post_response_artifacts.provider_request,
        failure.post_response_artifacts.raw_response,
        failure.post_response_artifacts.provider_response_metadata,
        failure.post_response_artifacts.token_usage,
        transport_artifacts.command_spec,
        transport_artifacts.stdout_jsonl,
        transport_artifacts.stderr,
        transport_artifacts.process_status,
        transport_artifacts.provider_response,
    ):
        store.verify(reference)


def test_subprocess_runner_removes_secret_bearing_environment_names() -> None:
    process_runner = SubprocessCodexProcessRunner(
        {
            "PATH": "safe",
            "HOME": "safe",
            "OPENAI_API_KEY": "forbidden",
            "SESSION_TOKEN": "forbidden",
        }
    )
    assert process_runner.environment == {"PATH": "safe", "HOME": "safe"}
    assert process_runner.removed_environment_keys == ("OPENAI_API_KEY", "SESSION_TOKEN")
