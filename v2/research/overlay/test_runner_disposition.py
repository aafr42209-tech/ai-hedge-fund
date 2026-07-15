from __future__ import annotations

import json

import pytest

from . import runner
from ._test_helpers import episode, hold_batch
from .artifacts import AppendOnlyArtifactStore
from .canonical import canonical_sha256, sha256_hex
from .codex_exec_client import CodexExecError
from .contracts import (
    AcquisitionDisposition,
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
