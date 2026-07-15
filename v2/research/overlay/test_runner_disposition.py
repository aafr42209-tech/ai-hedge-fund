from __future__ import annotations

import json

import pytest

from . import runner
from ._test_helpers import episode, hold_batch
from .artifacts import AppendOnlyArtifactStore
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .codex_exec_client import CodexExecError
from .contracts import (
    AcquisitionDisposition,
    AcquisitionFailureRecord,
    AcquisitionIdentity,
    CodexProcessStatus,
    CompleteResponseDispositionRecord,
    ProviderResponse,
    RunPlanEntry,
)
from .llm_policy import acquisition_key, ScriptedAcquisitionClient
from .oracle import solve_oracle


def _response(
    raw_text: str,
    *,
    tool_event_types: tuple[str, ...] = (),
    exit_code: int = 0,
) -> ProviderResponse:
    stdout = raw_text.encode("utf-8")
    process_status = CodexProcessStatus(
        exit_code=exit_code,
        timed_out=False,
        duration_ms=1,
        stdout_sha256=sha256_hex(stdout),
        stdout_size_bytes=len(stdout),
        stderr_sha256=sha256_hex(b""),
        stderr_size_bytes=0,
    )
    return ProviderResponse(
        raw_text=raw_text,
        provider="scripted",
        model_id="scripted-v1",
        request_id="request-1",
        input_tokens=1,
        cached_input_tokens=0,
        output_tokens=1,
        reasoning_output_tokens=0,
        model_identity_verified_by_transport=True,
        model_identity_evidence="matching_transport_echo",
        transport_model_echoes=("scripted-v1",),
        tool_use_violation=bool(tool_event_types),
        tool_event_types=tool_event_types,
        process_status_violation=exit_code != 0,
        event_types=("thread.started", "turn.started", "turn.completed"),
        agent_message_count=1,
        transport_sha256=sha256_hex(stdout),
        observed_transport_shape_sha256=canonical_sha256(
            {
                "schema_version": "test-transport-shape-v1",
                "tool_event_types": tool_event_types,
            }
        ),
        process_status=process_status,
    )


class _RetryingClient:
    def __init__(self, *, succeed_on_attempt: int | None) -> None:
        self.provider_calls = 0
        self.attempts: list[int] = []
        self._succeed_on_attempt = succeed_on_attempt

    def complete(self, *, system, user, identity):
        del system, user
        self.provider_calls += 1
        self.attempts.append(identity.attempt)
        if identity.attempt == self._succeed_on_attempt:
            return _response(json.dumps(hold_batch().model_dump(mode="json")))
        raise CodexExecError(
            "timeout_without_complete_response",
            "scripted timeout",
            disposition=AcquisitionDisposition.RETRY_TRANSPORT,
        )


def test_complete_tool_response_is_consumed_as_one_hold_outcome() -> None:
    outcome, record = runner._consume_complete_response(
        episode(),
        _response("valid text is intentionally not parsed", tool_event_types=("command_execution",)),
    )

    assert record.disposition is AcquisitionDisposition.FAIL_CLOSED_SCORE
    assert record.reason_codes == ("tool_use_violation",)
    assert record.scored_as_hold
    assert outcome.parsed_batch is None
    assert outcome.parsed_artifact["fail_closed_error"]["code"] == "tool_use_violation"
    assert outcome.validation.fell_back
    assert all(decision.action == "hold" for decision in outcome.validation.executable.decisions.values())


def test_complete_parse_failure_gets_explicit_fail_closed_disposition() -> None:
    outcome, record = runner._consume_complete_response(episode(), _response("not json"))

    assert record.disposition is AcquisitionDisposition.FAIL_CLOSED_SCORE
    assert record.reason_codes == ("schema_invalid",)
    assert record.scored_as_hold
    assert "parse_error" in outcome.parsed_artifact
    assert outcome.validation.fell_back


def test_fail_closed_response_without_reason_stops_as_harness_error(monkeypatch) -> None:
    valid = runner.parse_and_validate(
        episode().public,
        json.dumps(hold_batch().model_dump(mode="json")),
    )
    invalid = valid.validation.model_copy(
        update={"fell_back": True, "violations": ()},
    )
    monkeypatch.setattr(
        runner,
        "parse_and_validate",
        lambda public, raw_text: runner.ParsedPolicyOutcome(
            parsed_batch=valid.parsed_batch,
            parsed_artifact=valid.parsed_artifact,
            validation=invalid,
        ),
    )

    with pytest.raises(CodexExecError) as raised:
        runner._consume_complete_response(episode(), _response("ignored"))

    assert raised.value.code == "fail_closed_without_reason"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE


def test_complete_acquisition_scores_fail_closed_hold_exactly_once(tmp_path, monkeypatch) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    fixture = episode()
    fixture_ref = store.write_json("fixtures/case.json", fixture)
    identity = AcquisitionIdentity(
        experiment_id="b3-disposition-test",
        case_id=fixture.public.case_id,
        channel="development",
        replicate_id=0,
        attempt=1,
    )
    entry = RunPlanEntry(identity=identity, fixture=fixture_ref)
    client = ScriptedAcquisitionClient(
        {
            acquisition_key(identity): _response(
                "tool response",
                tool_event_types=("command_execution",),
            )
        }
    )
    score_calls = []
    real_score_episode = runner.score_episode

    def counting_score_episode(scored_episode, validation):
        score_calls.append(validation)
        return real_score_episode(scored_episode, validation)

    monkeypatch.setattr(runner, "score_episode", counting_score_episode)
    acquisition = runner._complete_acquisition(
        store,
        entry=entry,
        episode=fixture,
        client=client,
        oracle=solve_oracle(fixture),
    )

    assert len(score_calls) == 1
    assert score_calls[0].fell_back
    assert acquisition.disposition.disposition is AcquisitionDisposition.FAIL_CLOSED_SCORE
    persisted = CompleteResponseDispositionRecord.model_validate_json(store.read_bytes(acquisition.artifacts.response_disposition))
    assert persisted == acquisition.disposition


def test_complete_acquisition_binds_one_retry_before_success(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    fixture = episode()
    fixture_ref = store.write_json("fixtures/retry-case.json", fixture)
    identity = AcquisitionIdentity(
        experiment_id="b3-retry-success",
        case_id=fixture.public.case_id,
        channel="development",
        replicate_id=0,
        attempt=1,
    )
    client = _RetryingClient(succeed_on_attempt=2)

    acquisition = runner._complete_acquisition(
        store,
        entry=RunPlanEntry(identity=identity, fixture=fixture_ref),
        episode=fixture,
        client=client,
        oracle=solve_oracle(fixture),
    )

    assert client.attempts == [1, 2]
    assert acquisition.artifacts.identity.attempt == 2
    assert len(acquisition.artifacts.prior_attempt_failures) == 1
    failure = AcquisitionFailureRecord.model_validate_json(store.read_bytes(acquisition.artifacts.prior_attempt_failures[0]))
    assert failure.identity == identity
    assert failure.code == "timeout_without_complete_response"
    assert failure.disposition is AcquisitionDisposition.RETRY_TRANSPORT


def test_second_consecutive_transport_failure_stops_before_third_call(tmp_path) -> None:
    store = AppendOnlyArtifactStore(tmp_path)
    fixture = episode()
    fixture_ref = store.write_json("fixtures/retry-limit-case.json", fixture)
    identity = AcquisitionIdentity(
        experiment_id="b3-retry-limit",
        case_id=fixture.public.case_id,
        channel="development",
        replicate_id=0,
        attempt=1,
    )
    client = _RetryingClient(succeed_on_attempt=None)

    with pytest.raises(CodexExecError) as raised:
        runner._complete_acquisition(
            store,
            entry=RunPlanEntry(identity=identity, fixture=fixture_ref),
            episode=fixture,
            client=client,
            oracle=solve_oracle(fixture),
        )

    assert client.attempts == [1, 2]
    assert raised.value.code == "retry_transport_limit_reached"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    final_failure_ref = store.reference_for_existing(runner._acquisition_prefix(identity.model_copy(update={"attempt": 2})) + "/acquisition_failure.json")
    final_failure = AcquisitionFailureRecord.model_validate_json(store.read_bytes(final_failure_ref))
    assert final_failure.disposition is AcquisitionDisposition.STOP_PHASE
    assert final_failure.origin_code == "timeout_without_complete_response"
    assert final_failure.origin_disposition is AcquisitionDisposition.RETRY_TRANSPORT


def test_replay_raw_text_hash_is_bound_separately_from_transport_hash() -> None:
    response = _response("final agent text")
    metadata = response.model_dump(mode="python", exclude={"raw_text"})
    metadata["raw_text_sha256"] = "0" * 64

    with pytest.raises(RuntimeError, match="raw response hash"):
        runner._reconstruct_provider_response(
            response.raw_text.encode("utf-8"),
            canonical_json_bytes(metadata),
        )


def test_valid_complete_response_has_no_failure_disposition() -> None:
    raw_text = json.dumps(hold_batch().model_dump(mode="json"))
    outcome, record = runner._consume_complete_response(episode(), _response(raw_text))

    assert record.disposition is None
    assert record.reason_codes == ()
    assert not record.scored_as_hold
    assert outcome.validation.raw_valid
    assert not outcome.validation.fell_back


def test_complete_stop_phase_response_never_enters_scoring() -> None:
    with pytest.raises(CodexExecError) as raised:
        runner._consume_complete_response(episode(), _response("complete", exit_code=7))

    assert raised.value.code == "complete_response_stop_phase"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE


def test_unconsumed_complete_retry_disposition_stops_phase(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "complete_response_disposition",
        lambda response: AcquisitionDisposition.RETRY_TRANSPORT,
    )

    with pytest.raises(CodexExecError) as raised:
        runner._consume_complete_response(episode(), _response("complete"))

    assert raised.value.code == "missing_complete_response_disposition_consumer"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
