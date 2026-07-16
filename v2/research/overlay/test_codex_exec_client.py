from __future__ import annotations

import json

import pytest

from .artifacts import AppendOnlyArtifactStore
from .canonical import canonical_sha256, sha256_hex
from .codex_exec_client import (
    build_codex_command_spec,
    codex_jsonl_schema_sha256,
    codex_transport_shape_spec_sha256,
    CodexExecClient,
    CodexExecError,
    CodexProcessCapture,
    complete_response_disposition,
    compose_stdin_bytes,
    parse_codex_jsonl,
    POLICY_FIXTURE_DELIMITER,
)
from .codex_preflight import pilot_sandbox_identity_sha256
from .contracts import (
    AcquisitionDisposition,
    AcquisitionIdentity,
    codex_feature_catalog_snapshot_sha256,
    codex_pilot_sandbox_identity_sha256,
    CodexCommandSpec,
    CodexFeatureCatalogEntry,
)


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


def _identity(channel: str = "development", *, attempt: int = 1) -> AcquisitionIdentity:
    return AcquisitionIdentity(
        experiment_id="b1-test",
        case_id="development-0000",
        channel=channel,
        replicate_id=0,
        attempt=attempt,
    )


class FakeRunner:
    def __init__(self, capture: CodexProcessCapture) -> None:
        self.capture = capture
        self.calls: list[dict[str, object]] = []

    def run(self, **kwargs) -> CodexProcessCapture:
        self.calls.append(kwargs)
        return self.capture


def _feature_catalog() -> tuple[CodexFeatureCatalogEntry, ...]:
    return (
        CodexFeatureCatalogEntry(
            name="shell_tool",
            stage="stable",
            enabled=True,
        ),
        CodexFeatureCatalogEntry(
            name="web_search",
            stage="stable",
            enabled=True,
        ),
    )


def _command_gate_kwargs(tmp_path) -> dict[str, object]:
    catalog = _feature_catalog()
    return {
        "feature_catalog": catalog,
        "expected_feature_catalog_sha256": (codex_feature_catalog_snapshot_sha256(catalog)),
        "post_disable_effective_true_features": (),
        "expected_pilot_sandbox_sha256": pilot_sandbox_identity_sha256(str(tmp_path)),
        "expected_transport_shape_spec_sha256": (codex_transport_shape_spec_sha256()),
    }


def _client(tmp_path, capture: CodexProcessCapture, sink_calls: list[object], process_runner=None):
    runner = process_runner or FakeRunner(capture)
    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        **_command_gate_kwargs(tmp_path),
        disabled_features=("web_search", "shell_tool"),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false",),
        working_directory=str(tmp_path),
        timeout_ms=30_000,
        process_runner=runner,
        capture_sink=lambda spec, raw: sink_calls.append((spec, raw)),
    )
    return client, runner


def test_live_transport_artifacts_are_bound_to_the_exact_attempt(tmp_path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    store = AppendOnlyArtifactStore(tmp_path / "artifacts")
    capture = _capture()
    process_runner = FakeRunner(capture)
    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        **_command_gate_kwargs(sandbox),
        disabled_features=("web_search", "shell_tool"),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false",),
        working_directory=str(sandbox),
        timeout_ms=30_000,
        process_runner=process_runner,
        transport_store=store,
    )
    identity = _identity()

    response = client.complete(system="system", user="fixture", identity=identity)
    transport = client.transport_artifacts_for(identity)

    assert response.request_id == "thread-b1"
    assert transport is not None
    for reference in (
        transport.command_spec,
        transport.stdout_jsonl,
        transport.stderr,
        transport.process_status,
        transport.provider_response,
    ):
        store.verify(reference)
    assert store.read_bytes(transport.stdout_jsonl) == capture.stdout


def test_reviewed_command_spec_mismatch_stops_before_provider_call(tmp_path) -> None:
    process_runner = FakeRunner(_capture())
    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        **_command_gate_kwargs(tmp_path),
        disabled_features=("web_search", "shell_tool"),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false",),
        working_directory=str(tmp_path),
        timeout_ms=30_000,
        process_runner=process_runner,
        expected_command_spec_sha256_by_prompt={"unreviewed": "0" * 64},
    )

    with pytest.raises(CodexExecError) as raised:
        client.complete(system="system", user="fixture", identity=_identity())

    assert raised.value.code == "command_spec_preflight_mismatch"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert client.provider_calls == 0
    assert process_runner.calls == []


def test_command_spec_build_failure_is_classified_before_provider_call(tmp_path) -> None:
    gate_kwargs = _command_gate_kwargs(tmp_path)
    (tmp_path / "unexpected-file").write_text("sandbox drift", encoding="utf-8")
    process_runner = FakeRunner(_capture())
    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        **gate_kwargs,
        disabled_features=("web_search", "shell_tool"),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false",),
        working_directory=str(tmp_path),
        timeout_ms=30_000,
        process_runner=process_runner,
    )

    with pytest.raises(CodexExecError) as raised:
        client.complete(system="system", user="fixture", identity=_identity())

    assert raised.value.code == "command_spec_build_failure"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert client.provider_calls == 0
    assert process_runner.calls == []


@pytest.mark.parametrize(
    ("collision_name", "expected_code"),
    (
        ("command_spec.json", "transport_artifact_persistence_failure"),
        ("provider_response.json", "provider_response_artifact_persistence_failure"),
    ),
)
def test_transport_artifact_collisions_are_classified_stop(
    tmp_path,
    collision_name,
    expected_code,
) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    store = AppendOnlyArtifactStore(tmp_path / "artifacts")
    prefix = "b1-test/acquisitions/development-0000/development/replicate-000/attempt-1/transport"
    store.write_json(f"{prefix}/{collision_name}", {})
    process_runner = FakeRunner(_capture())
    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        **_command_gate_kwargs(sandbox),
        disabled_features=("web_search", "shell_tool"),
        active_feature_allowlist=(),
        config_overrides=("tools.web_search=false",),
        working_directory=str(sandbox),
        timeout_ms=30_000,
        process_runner=process_runner,
        transport_store=store,
    )

    with pytest.raises(CodexExecError) as raised:
        client.complete(system="system", user="fixture", identity=_identity())

    assert raised.value.code == expected_code
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert client.provider_calls == 1


def test_command_spec_is_shell_free_deterministic_and_hashes_exact_stdin(tmp_path) -> None:
    first, stdin_bytes = build_codex_command_spec(
        executable="codex",
        model_id="mock-model-id",
        **_command_gate_kwargs(tmp_path),
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
        **_command_gate_kwargs(tmp_path),
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
    stable_payload["pilot_sandbox_sha256"] = codex_pilot_sandbox_identity_sha256("C:/r01-pilot-sandbox")
    stable_spec = CodexCommandSpec.model_validate(stable_payload)
    assert codex_jsonl_schema_sha256() == "ba8751646f3f01a0806f23fe967cf8d5d4d2370fa89682c8a34d77efc0a698ff"
    assert canonical_sha256(stable_spec) == "497739b89a388dec7df584fcc3f3ec26cec4d43c57ff29f69c7ee2ab8d1e2f4c"


def test_command_spec_rejects_contradictory_config_keys(tmp_path) -> None:
    with pytest.raises(ValueError, match="keys must be unique"):
        build_codex_command_spec(
            executable="codex",
            model_id="mock-model-id",
            **_command_gate_kwargs(tmp_path),
            disabled_features=("shell_tool", "web_search"),
            active_feature_allowlist=(),
            config_overrides=("tools.web_search=false", "tools.web_search=true"),
            working_directory=str(tmp_path),
            timeout_ms=30_000,
            policy_instruction="policy",
            fixture_prompt="fixture",
        )


def test_command_spec_rejects_incomplete_catalog_and_secret_config(tmp_path) -> None:
    common = {
        "executable": "codex",
        "model_id": "mock-model-id",
        **_command_gate_kwargs(tmp_path),
        "active_feature_allowlist": (),
        "working_directory": str(tmp_path),
        "timeout_ms": 30_000,
        "policy_instruction": "policy",
        "fixture_prompt": "fixture",
    }
    with pytest.raises(ValueError, match="must cover the catalog"):
        build_codex_command_spec(
            **common,
            disabled_features=("web_search",),
            config_overrides=("tools.web_search=false",),
        )
    with pytest.raises(ValueError, match="secret-bearing config"):
        build_codex_command_spec(
            **common,
            disabled_features=("shell_tool", "web_search"),
            config_overrides=(
                "api_key=must-not-enter-artifact",
                "tools.web_search=false",
            ),
        )

    for sensitive_config in (
        "provider.foo_key=hidden",
        "provider.private_value=hidden",
        "provider.session_id=hidden",
    ):
        with pytest.raises(ValueError, match="secret-bearing config"):
            build_codex_command_spec(
                **common,
                disabled_features=("shell_tool", "web_search"),
                config_overrides=(sensitive_config, "tools.web_search=false"),
            )

    for secret_value in (
        "tools.foo=sk-live-abc123",
        "tools.foo=Bearer abc123",
        "tools.foo=api_key=abc123",
    ):
        with pytest.raises(ValueError, match="secret-bearing config values"):
            build_codex_command_spec(
                **common,
                disabled_features=("shell_tool", "web_search"),
                config_overrides=(secret_value, "tools.web_search=false"),
            )


@pytest.mark.parametrize(
    ("override", "executable"),
    (
        ("tools.web_search=false\0hidden", "codex"),
        ("tools.web_search=false", "codex\0hidden"),
    ),
)
def test_command_spec_rejects_null_bytes(tmp_path, override, executable) -> None:
    with pytest.raises(ValueError):
        build_codex_command_spec(
            executable=executable,
            model_id="mock-model-id",
            **_command_gate_kwargs(tmp_path),
            disabled_features=("shell_tool", "web_search"),
            active_feature_allowlist=(),
            config_overrides=(override,),
            working_directory=str(tmp_path),
            timeout_ms=30_000,
            policy_instruction="policy",
            fixture_prompt="fixture",
        )


def test_command_spec_rejects_wrong_sandbox_and_transport_shape_anchors(
    tmp_path,
) -> None:
    common = {
        "executable": "codex",
        "model_id": "mock-model-id",
        **_command_gate_kwargs(tmp_path),
        "disabled_features": ("shell_tool", "web_search"),
        "active_feature_allowlist": (),
        "config_overrides": ("tools.web_search=false",),
        "working_directory": str(tmp_path),
        "timeout_ms": 30_000,
        "policy_instruction": "policy",
        "fixture_prompt": "fixture",
    }
    wrong_sandbox = {**common, "expected_pilot_sandbox_sha256": "0" * 64}
    with pytest.raises(RuntimeError, match="sandbox differs"):
        build_codex_command_spec(**wrong_sandbox)
    wrong_shape = {
        **common,
        "expected_transport_shape_spec_sha256": "0" * 64,
    }
    with pytest.raises(RuntimeError, match="transport shape spec differs"):
        build_codex_command_spec(**wrong_shape)


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
    assert response.model_identity_evidence == "transport_echo_absent"
    assert response.transport_model_echoes == ()
    assert canonical_sha256(response.process_status) == "df1989e4c60454a542b4806b6fd718ee54144f771b74a12a095aa269ea60cb10"
    assert canonical_sha256(response) == "75f2157756cd3f6e7807ab00942c7f4be1c541ca31a313b797368c9221676963"


@pytest.mark.parametrize(
    ("capture", "expected_code"),
    (
        (_capture(stdout=b"", exit_code=None, timed_out=True), "timeout_without_complete_response"),
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
    assert raised.value.disposition is AcquisitionDisposition.RETRY_TRANSPORT
    if expected_code == "timeout_without_complete_response":
        assert raised.value.origin_code is not None
        assert raised.value.origin_disposition is AcquisitionDisposition.RETRY_TRANSPORT
    else:
        assert raised.value.origin_code is None
        assert raised.value.origin_disposition is None
    assert len(sink_calls) == 1


def test_initial_nonzero_without_complete_response_stops_before_retry(tmp_path) -> None:
    sink_calls: list[object] = []
    client, _runner = _client(
        tmp_path,
        _capture(stdout=b"", exit_code=7, stderr=b"failure"),
        sink_calls,
    )

    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())

    assert raised.value.code == "nonzero_exit_without_complete_response"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert raised.value.origin_disposition is AcquisitionDisposition.RETRY_TRANSPORT
    assert len(sink_calls) == 1


def test_retry_nonzero_without_complete_response_remains_transport_failure(tmp_path) -> None:
    sink_calls: list[object] = []
    client, _runner = _client(
        tmp_path,
        _capture(stdout=b"", exit_code=7, stderr=b"failure"),
        sink_calls,
    )

    with pytest.raises(CodexExecError) as raised:
        client.complete(
            system="policy",
            user="fixture",
            identity=_identity(attempt=2),
        )

    assert raised.value.code == "nonzero_exit_without_complete_response"
    assert raised.value.disposition is AcquisitionDisposition.RETRY_TRANSPORT
    assert raised.value.origin_disposition is AcquisitionDisposition.RETRY_TRANSPORT
    assert len(sink_calls) == 1


def test_missing_final_message_is_retry_eligible() -> None:
    events = [event for event in _events() if event["type"] != "item.completed"]
    with pytest.raises(CodexExecError) as raised:
        parse_codex_jsonl(_capture(events), requested_model_id="mock-model-id")
    assert raised.value.code == "missing_final_message"
    assert raised.value.disposition is AcquisitionDisposition.RETRY_TRANSPORT


@pytest.mark.parametrize(
    ("capture", "expected_code", "expected_disposition"),
    (
        (
            _capture(_events(extra=[{"type": "turn.failed", "error": "failed"}])),
            "contradictory_terminal_status",
            AcquisitionDisposition.RETRY_TRANSPORT,
        ),
        (
            _capture(_events(extra=[{"type": "new.event"}])),
            "jsonl_schema_drift",
            AcquisitionDisposition.STOP_PHASE,
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
            "jsonl_schema_drift",
            AcquisitionDisposition.STOP_PHASE,
        ),
        (
            _capture(_events(extra=[{"type": "thread.started", "thread_id": "duplicate"}])),
            "thread_identity_violation",
            AcquisitionDisposition.RETRY_TRANSPORT,
        ),
    ),
)
def test_strict_jsonl_schema_drift_fails_closed(
    capture,
    expected_code,
    expected_disposition,
) -> None:
    with pytest.raises(CodexExecError) as raised:
        parse_codex_jsonl(capture, requested_model_id="mock-model-id")
    assert raised.value.code == expected_code
    assert raised.value.disposition is expected_disposition


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
    assert complete_response_disposition(response) is AcquisitionDisposition.FAIL_CLOSED_SCORE


def test_matching_model_echo_is_verified_and_mismatch_stops_phase() -> None:
    matching = _events()
    matching[0]["model"] = "mock-model-id"
    response = parse_codex_jsonl(
        _capture(matching),
        requested_model_id="mock-model-id",
    )
    assert response.model_identity_verified_by_transport
    assert response.model_identity_evidence == "matching_transport_echo"
    assert response.transport_model_echoes == ("mock-model-id",)

    mismatched = _events()
    mismatched[0]["model"] = "different-model"
    with pytest.raises(CodexExecError) as raised:
        parse_codex_jsonl(
            _capture(mismatched),
            requested_model_id="mock-model-id",
        )
    assert raised.value.code == "model_identity_mismatch"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE


@pytest.mark.parametrize(
    "capture_kwargs",
    (
        {"exit_code": 9, "stderr": b"model selection failed"},
        {"exit_code": None, "timed_out": True},
    ),
)
def test_stop_phase_parse_errors_are_never_downgraded(tmp_path, capture_kwargs) -> None:
    mismatched = _events()
    mismatched[0]["model"] = "different-model"
    sink_calls: list[object] = []
    client, _runner = _client(tmp_path, _capture(mismatched, **capture_kwargs), sink_calls)

    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())

    assert raised.value.code == "model_identity_mismatch"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert raised.value.origin_code is None
    assert len(sink_calls) == 1


def test_unknown_item_and_known_event_field_are_schema_drift_stop() -> None:
    unknown_item = {
        "type": "item.completed",
        "item": {"id": "future-1", "type": "future_item"},
    }
    with pytest.raises(CodexExecError) as item_error:
        parse_codex_jsonl(
            _capture(_events(extra=[unknown_item])),
            requested_model_id="mock-model-id",
        )
    assert item_error.value.code == "jsonl_schema_drift"
    assert item_error.value.disposition is AcquisitionDisposition.STOP_PHASE

    unknown_field_events = _events()
    unknown_field_events[1]["future_field"] = True
    with pytest.raises(CodexExecError) as field_error:
        parse_codex_jsonl(
            _capture(unknown_field_events),
            requested_model_id="mock-model-id",
        )
    assert field_error.value.code == "jsonl_schema_drift"
    assert field_error.value.disposition is AcquisitionDisposition.STOP_PHASE


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
    parsed = parse_codex_jsonl(capture, requested_model_id="mock-model-id")
    assert parsed.process_status_violation
    assert complete_response_disposition(parsed) is AcquisitionDisposition.STOP_PHASE

    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())
    assert raised.value.code == "process_status_violation"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert len(sink_calls) == 1


def test_forbidden_channel_is_nonretryable_and_never_invokes_runner(tmp_path) -> None:
    sink_calls: list[object] = []
    client, runner = _client(tmp_path, _capture(), sink_calls)
    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity("primary"))
    assert raised.value.code == "forbidden_channel"
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert client.provider_calls == 0
    assert not runner.calls
    assert not sink_calls


class _RaisingRunner:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def run(self, **kwargs):
        raise self.error


@pytest.mark.parametrize(
    ("error", "expected_type"),
    (
        (
            CodexExecError(
                "runner_schema_failure",
                "runner reported a phase stop",
                disposition=AcquisitionDisposition.STOP_PHASE,
            ),
            CodexExecError,
        ),
        (TypeError("runner programming error"), TypeError),
    ),
)
def test_runner_errors_are_not_reclassified_as_transport_retry(tmp_path, error, expected_type) -> None:
    sink_calls: list[object] = []
    client, _runner = _client(
        tmp_path,
        _capture(),
        sink_calls,
        process_runner=_RaisingRunner(error),
    )

    with pytest.raises(expected_type) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())

    if isinstance(error, CodexExecError):
        assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
    assert not sink_calls


def test_oserror_runner_failure_remains_retryable(tmp_path) -> None:
    sink_calls: list[object] = []
    client, _runner = _client(
        tmp_path,
        _capture(),
        sink_calls,
        process_runner=_RaisingRunner(OSError("binary missing")),
    )

    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())

    assert raised.value.code == "process_launch_failure"
    assert raised.value.disposition is AcquisitionDisposition.RETRY_TRANSPORT
    assert not sink_calls


def test_launch_failure_is_retryable_after_capture_is_sunk(tmp_path) -> None:
    sink_calls: list[object] = []
    capture = _capture(stdout=b"", exit_code=None, launch_error="binary missing")
    client, _runner = _client(tmp_path, capture, sink_calls)
    with pytest.raises(CodexExecError) as raised:
        client.complete(system="policy", user="fixture", identity=_identity())
    assert raised.value.code == "process_launch_failure"
    assert raised.value.disposition is AcquisitionDisposition.RETRY_TRANSPORT
    assert len(sink_calls) == 1


def test_artifact_sink_failure_is_nonretryable(tmp_path) -> None:
    runner = FakeRunner(_capture())

    def broken_sink(_spec, _capture) -> None:
        raise OSError("disk full")

    client = CodexExecClient(
        executable="codex",
        model_id="mock-model-id",
        **_command_gate_kwargs(tmp_path),
        disabled_features=("shell_tool", "web_search"),
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
    assert raised.value.disposition is AcquisitionDisposition.STOP_PHASE
