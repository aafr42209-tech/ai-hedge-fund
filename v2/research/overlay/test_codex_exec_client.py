from __future__ import annotations

import json

import pytest

from .canonical import canonical_sha256, sha256_hex
from .codex_exec_client import (
    POLICY_FIXTURE_DELIMITER,
    CodexExecClient,
    CodexExecError,
    CodexProcessCapture,
    build_codex_command_spec,
    codex_jsonl_schema_sha256,
    compose_stdin_bytes,
    parse_codex_jsonl,
)
from .contracts import AcquisitionIdentity, CodexCommandSpec


def _jsonl(events: list[dict[str, object]]) -> bytes:
    return ("\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n").encode()


def _events(
    raw_text: str = '{"decisions":{}}',
    *,
    usage: dict[str, int] | None = None,
    extra: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    terminal_usage = usage or {
        "input_tokens": 100,
        "cached_input_tokens": 40,
        "output_tokens": 20,
        "reasoning_output_tokens": 5,
    }
    return [
        {"type": "thread.started", "thread_id": "thread-b1"},
        {"type": "turn.started"},
        *(extra or []),
        {
            "type": "item.completed",
            "item": {"id": "message-1", "type": "agent_message", "text": raw_text},
        },
        {"type": "turn.completed", "usage": terminal_usage},
    ]


def _capture(
    events: list[dict[str, object]] | None = None,
    *,
    stdout: bytes | None = None,
    stderr: bytes = b"",
    exit_code: int | None = 0,
    timed_out: bool = False,
    launch_error: str | None = None,
) -> CodexProcessCapture:
    return CodexProcessCapture(
        stdout=_jsonl(events or _events()) if stdout is None else stdout,
        stderr=stderr,
        exit_code=exit_code,
        duration_ms=17,
        timed_out=timed_out,
        launch_error=launch_error,
    )


def _identity(channel: str = "development") -> AcquisitionIdentity:
    return AcquisitionIdentity(
        experiment_id="b1-test",
        case_id="development-0000",
        channel=channel,
        replicate_id=0,
        attempt=1,
    )


class FakeRunner:
    def __init__(self, capture: CodexProcessCapture) -> None:
        self.capture = capture
        self.calls: list[dict[str, object]] = []

    def run(self, **kwargs) -> CodexProcessCapture:
        self.calls.append(kwargs)
        return self.capture


def _client(tmp_path, capture: CodexProcessCapture, sink_calls: list[object]):
    runner = FakeRunner(capture)
    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        disabled_features=("web_search", "shell_tool"),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false",),
        working_directory=str(tmp_path),
        timeout_ms=30_000,
        process_runner=runner,
        capture_sink=lambda spec, raw: sink_calls.append((spec, raw)),
    )
    return client, runner


def test_command_spec_is_shell_free_deterministic_and_hashes_exact_stdin(tmp_path) -> None:
    first, stdin_bytes = build_codex_command_spec(
        executable="codex",
        model_id="mock-model-id",
        disabled_features=("web_search", "shell_tool"),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false", "zeta=false"),
        working_directory=str(tmp_path),
        timeout_ms=30_000,
        policy_instruction="policy",
        fixture_prompt="fixture",
    )
    second, second_stdin = build_codex_command_spec(
        executable="codex",
        model_id="mock-model-id",
        disabled_features=("shell_tool", "web_search"),
        active_feature_allowlist=(),
        config_overrides=("zeta=false", "tools.web_search=false"),
        working_directory=str(tmp_path),
        timeout_ms=30_000,
        policy_instruction="policy",
        fixture_prompt="fixture",
    )

    assert first == second
    assert stdin_bytes == second_stdin == f"policy{POLICY_FIXTURE_DELIMITER}fixture".encode()
    assert first.stdin_sha256 == sha256_hex(stdin_bytes)
    assert first.jsonl_schema_sha256 == codex_jsonl_schema_sha256()
    assert first.argv == (
        "codex",
        "--disable",
        "shell_tool",
        "--disable",
        "web_search",
        "exec",
        "--model",
        "mock-model-id",
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--strict-config",
        "--config",
        "tools.web_search=false",
        "--config",
        "zeta=false",
        "--json",
        "-",
    )
    assert "--output-schema" not in first.argv
    assert "--output-last-message" not in first.argv
    assert canonical_sha256(first) == canonical_sha256(second)
    stable_payload = first.model_dump(mode="python")
    stable_payload["working_directory"] = "C:/r01-pilot-sandbox"
    stable_spec = CodexCommandSpec.model_validate(stable_payload)
    assert codex_jsonl_schema_sha256() == "cf7ed097a3a8734485f7d229c57eb95a3fe594f5dcc5795b3793fb17332d1da4"
    assert canonical_sha256(stable_spec) == "b13eda86e49ed60a6a80b149db2eaed4f418541a9d68ce9b5ef66890f73faf2e"


def test_command_spec_rejects_contradictory_config_keys(tmp_path) -> None:
    with pytest.raises(ValueError, match="keys must be unique"):
        build_codex_command_spec(
            executable="codex",
            model_id="mock-model-id",
            disabled_features=(),
            active_feature_allowlist=(),
            config_overrides=("tools.web_search=false", "tools.web_search=true"),
            working_directory=str(tmp_path),
            timeout_ms=30_000,
            policy_instruction="policy",
            fixture_prompt="fixture",
        )


def test_client_success_uses_injected_runner_and_sinks_raw_before_return(tmp_path) -> None:
    sink_calls: list[object] = []
    capture = _capture()
    client, runner = _client(tmp_path, capture, sink_calls)

    response = client.complete(system="policy", user="fixture", identity=_identity())

    assert client.provider_calls == 1
    assert len(runner.calls) == len(sink_calls) == 1
    assert sink_calls[0][1] is capture
    assert runner.calls[0]["argv"] == sink_calls[0][0].argv
    assert runner.calls[0]["stdin_bytes"] == compose_stdin_bytes("policy", "fixture")
    assert response.raw_text == '{"decisions":{}}'
    assert response.input_tokens == 100
    assert response.cached_input_tokens == 40
    assert response.output_tokens == 20
    assert response.reasoning_output_tokens == 5
    assert response.request_id == "thread-b1"
    assert not response.tool_use_violation
    assert not response.process_status_violation
    assert not response.model_identity_verified_by_transport
    assert canonical_sha256(response.process_status) == "df1989e4c60454a542b4806b6fd718ee54144f771b74a12a095aa269ea60cb10"
    assert canonical_sha256(response) == "98f00424dcaae95aa452949cba7260e9988d442dd5274a90377d44528a190f57"


@pytest.mark.parametrize(
    ("capture", "expected_code"),
    (
        (_capture(stdout=b"", exit_code=None, timed_out=True), "timeout_without_complete_response"),
        (_capture(stdout=b"", exit_code=7, stderr=b"failure"), "nonzero_exit_without_complete_response"),
        (_capture(stdout=b"not-json"), "malformed_jsonl"),
        (
            _capture(_events(usage={"input_tokens": 1, "output_tokens": 2})),
            "missing_usage",
        ),
        (
            _capture(
                _events()
                + [
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 1,
                            "cached_input_tokens": 0,
                            "output_tokens": 1,
                            "reasoning_output_tokens": 0,
                        },
                    }
                ]
            ),
            "duplicate_terminal_event",
        ),
        (_capture(_events(raw_text="")), "empty_response"),
    ),
)
def test_transport_failures_are_retry_eligible(tmp_path, capture, expected_code) -> None:
    sink_calls: list[object] = []
    client, _runner = _client(tmp_path, capture, sink_calls)
    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())
    assert raised.value.code == expected_code
    assert raised.value.retry_eligible
    assert len(sink_calls) == 1


def test_missing_final_message_is_retry_eligible() -> None:
    events = [event for event in _events() if event["type"] != "item.completed"]
    with pytest.raises(CodexExecError) as raised:
        parse_codex_jsonl(_capture(events), requested_model_id="mock-model-id")
    assert raised.value.code == "missing_final_message"
    assert raised.value.retry_eligible


@pytest.mark.parametrize(
    ("capture", "expected_code"),
    (
        (
            _capture(_events(extra=[{"type": "turn.failed", "error": "failed"}])),
            "contradictory_terminal_status",
        ),
        (
            _capture(_events(extra=[{"type": "new.event"}])),
            "jsonl_schema_drift",
        ),
        (
            _capture(
                _events(
                    usage={
                        "input_tokens": 1,
                        "cached_input_tokens": 0,
                        "output_tokens": 1,
                        "reasoning_output_tokens": 0,
                        "new_usage_field": 1,
                    }
                )
            ),
            "missing_usage",
        ),
        (
            _capture(_events(extra=[{"type": "thread.started", "thread_id": "duplicate"}])),
            "thread_identity_violation",
        ),
    ),
)
def test_strict_jsonl_schema_drift_fails_closed(capture, expected_code) -> None:
    with pytest.raises(CodexExecError) as raised:
        parse_codex_jsonl(capture, requested_model_id="mock-model-id")
    assert raised.value.code == expected_code
    assert raised.value.retry_eligible


def test_duplicate_json_key_fails_closed() -> None:
    raw = b'{"type":"thread.started","thread_id":"one","thread_id":"two"}\n' + _jsonl(_events()[1:])
    with pytest.raises(CodexExecError) as raised:
        parse_codex_jsonl(_capture(stdout=raw), requested_model_id="mock-model-id")
    assert raised.value.code == "malformed_jsonl"


def test_nonfinite_json_number_fails_closed() -> None:
    raw = b'{"type":"thread.started","thread_id":"one","value":NaN}\n' + _jsonl(_events()[1:])
    with pytest.raises(CodexExecError) as raised:
        parse_codex_jsonl(_capture(stdout=raw), requested_model_id="mock-model-id")
    assert raised.value.code == "malformed_jsonl"


def test_complete_tool_use_response_is_observed_not_retried(tmp_path) -> None:
    tool_event = {
        "type": "item.completed",
        "item": {"id": "tool-1", "type": "command_execution", "command": "pwd"},
    }
    sink_calls: list[object] = []
    client, _runner = _client(tmp_path, _capture(_events(extra=[tool_event])), sink_calls)

    response = client.complete(system="policy", user="fixture", identity=_identity())

    assert response.tool_use_violation
    assert response.tool_event_types == ("command_execution",)
    assert not response.process_status_violation


def test_complete_invalid_decision_text_is_not_transport_retry(tmp_path) -> None:
    sink_calls: list[object] = []
    client, _runner = _client(tmp_path, _capture(_events(raw_text="not decision JSON")), sink_calls)
    response = client.complete(system="policy", user="fixture", identity=_identity())
    assert response.raw_text == "not decision JSON"
    assert not response.tool_use_violation


@pytest.mark.parametrize(
    "capture",
    (
        _capture(_events(), exit_code=9, stderr=b"late failure"),
        _capture(_events(), exit_code=None, timed_out=True),
    ),
)
def test_complete_response_with_process_violation_is_not_retried(tmp_path, capture) -> None:
    sink_calls: list[object] = []
    client, _runner = _client(tmp_path, capture, sink_calls)
    response = client.complete(system="policy", user="fixture", identity=_identity())
    assert response.process_status_violation


def test_forbidden_channel_is_nonretryable_and_never_invokes_runner(tmp_path) -> None:
    sink_calls: list[object] = []
    client, runner = _client(tmp_path, _capture(), sink_calls)
    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity("primary"))
    assert raised.value.code == "forbidden_channel"
    assert not raised.value.retry_eligible
    assert client.provider_calls == 0
    assert not runner.calls
    assert not sink_calls


def test_launch_failure_is_retryable_after_capture_is_sunk(tmp_path) -> None:
    sink_calls: list[object] = []
    capture = _capture(stdout=b"", exit_code=None, launch_error="binary missing")
    client, _runner = _client(tmp_path, capture, sink_calls)
    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())
    assert raised.value.code == "process_launch_failure"
    assert raised.value.retry_eligible
    assert len(sink_calls) == 1


def test_artifact_sink_failure_is_nonretryable(tmp_path) -> None:
    runner = FakeRunner(_capture())

    def broken_sink(_spec, _capture) -> None:
        raise OSError("disk full")

    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        disabled_features=("web_search",),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false",),
        working_directory=str(tmp_path),
        timeout_ms=30_000,
        process_runner=runner,
        capture_sink=broken_sink,
    )
    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())
    assert raised.value.code == "artifact_sink_failure"
    assert not raised.value.retry_eligible
