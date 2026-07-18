from __future__ import annotations

import json
from pathlib import Path

import pytest

from .canonical import canonical_json_bytes
from .codex_exec_client import CodexProcessCapture
from .r02_d4_s6_contracts import offline_fake_authorization, R02_D4_S6_TIMEOUT_MS
from .r02_d4_s6_runner import build_provider_free_run_plan, R02D4S6Runner
from .r02_d4_s7_transport import (
    R02D4S7CodexTransport,
    R02D4S7TransportError,
    R02D4S7TransportEvidenceStore,
)

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "docs/r02-d4-s7-selector-output-schema.json"


def _response(candidate_id: str = "P00") -> str:
    return json.dumps(
        {
            "schema_version": "r02-selector-response-v1",
            "selected_candidate_id": candidate_id,
            "confidence": 64,
            "reason_codes": ["TIE_BREAK_PREFERENCE"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _jsonl(
    raw_response: str | None = None,
    *,
    usage: object = None,
    duplicate_terminal: bool = False,
) -> bytes:
    terminal_usage = (
        {
            "input_tokens": 100,
            "cached_input_tokens": 40,
            "output_tokens": 20,
            "reasoning_output_tokens": 5,
        }
        if usage is None
        else usage
    )
    events = [
        {"type": "thread.started", "thread_id": "thread-r02-d4-s7"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "message-1",
                "type": "agent_message",
                "text": raw_response or _response(),
            },
        },
        {"type": "turn.completed", "usage": terminal_usage},
    ]
    if duplicate_terminal:
        events.append({"type": "turn.completed", "usage": terminal_usage})
    return ("\n".join(json.dumps(value, separators=(",", ":")) for value in events) + "\n").encode()


class FakeProcessRunner:
    r02_d3_execution_capability = "OFFLINE_FAKE"

    def __init__(self, captures: list[CodexProcessCapture] | None = None) -> None:
        self.captures = captures or []
        self.calls: list[dict[str, object]] = []

    def run(
        self,
        *,
        argv: tuple[str, ...],
        stdin_bytes: bytes,
        working_directory: str,
        timeout_ms: int,
    ) -> CodexProcessCapture:
        self.calls.append(
            {
                "argv": argv,
                "stdin_bytes": stdin_bytes,
                "working_directory": working_directory,
                "timeout_ms": timeout_ms,
            }
        )
        index = len(self.calls) - 1
        if index < len(self.captures):
            return self.captures[index]
        return CodexProcessCapture(
            stdout=_jsonl(),
            stderr=b"",
            exit_code=0,
            duration_ms=17,
        )


class LiveCapableFakeProcessRunner(FakeProcessRunner):
    r02_d3_execution_capability = "LIVE_PROVIDER_PROCESS"


def _transport(tmp_path: Path, runner: FakeProcessRunner) -> R02D4S7CodexTransport:
    return R02D4S7CodexTransport(
        repository_root=ROOT,
        output_schema_path=SCHEMA,
        process_runner=runner,
        evidence_store=R02D4S7TransportEvidenceStore(tmp_path / "evidence"),
        live_authorized=False,
    )


def test_transport_binds_exact_prompt_command_timeout_and_full_capture(
    tmp_path: Path,
) -> None:
    prepared = build_provider_free_run_plan(ROOT).attempts[0]
    runner = FakeProcessRunner()
    transport = _transport(tmp_path, runner)
    result = transport.execute(
        run_id="r02-d4-s7-offline-transport",
        attempt_id="a" * 64,
        attempt=prepared.planned,
        selector_request=prepared.selector_request,
        timeout_ms=R02_D4_S6_TIMEOUT_MS,
    )
    assert result.raw_response == _response()
    assert result.input_tokens == 100
    assert result.output_tokens == 20
    assert result.external_provider_calls == 0
    assert len(runner.calls) == 1
    assert runner.calls[0]["timeout_ms"] == 900_000
    argv = runner.calls[0]["argv"]
    assert isinstance(argv, tuple)
    assert "exec" in argv
    assert "--ephemeral" in argv
    assert "--output-schema" in argv
    evidence_files = list((tmp_path / "evidence/attempts").glob("*.json"))
    assert len(evidence_files) == 1
    evidence = json.loads(evidence_files[0].read_text(encoding="utf-8"))
    assert evidence["timeout_ms"] == 900_000
    assert evidence["terminal_usage_event_count"] == 1
    assert evidence["external_provider_calls"] == 0


def test_duplicate_attempt_is_blocked_before_second_process_call(tmp_path: Path) -> None:
    prepared = build_provider_free_run_plan(ROOT).attempts[0]
    runner = FakeProcessRunner()
    transport = _transport(tmp_path, runner)
    kwargs = {
        "run_id": "r02-d4-s7-offline-duplicate",
        "attempt_id": "b" * 64,
        "attempt": prepared.planned,
        "selector_request": prepared.selector_request,
        "timeout_ms": R02_D4_S6_TIMEOUT_MS,
    }
    transport.execute(**kwargs)
    with pytest.raises(R02D4S7TransportError, match="duplicate"):
        transport.execute(**kwargs)
    assert len(runner.calls) == 1


@pytest.mark.parametrize(
    ("capture", "expected_error"),
    [
        (
            CodexProcessCapture(
                stdout=b"",
                stderr=b"",
                exit_code=None,
                duration_ms=900_000,
                timed_out=True,
            ),
            "TIMEOUT",
        ),
        (
            CodexProcessCapture(
                stdout=b"",
                stderr=b"boom",
                exit_code=2,
                duration_ms=19,
            ),
            "NONZERO_EXIT",
        ),
        (
            CodexProcessCapture(
                stdout=_jsonl(duplicate_terminal=True),
                stderr=b"",
                exit_code=0,
                duration_ms=19,
            ),
            "duplicate_terminal_event",
        ),
    ],
)
def test_unsettled_transport_is_persisted_and_returned_fail_closed(
    tmp_path: Path,
    capture: CodexProcessCapture,
    expected_error: str,
) -> None:
    prepared = build_provider_free_run_plan(ROOT).attempts[0]
    transport = _transport(tmp_path, FakeProcessRunner([capture]))
    result = transport.execute(
        run_id="r02-d4-s7-offline-unsettled",
        attempt_id="c" * 64,
        attempt=prepared.planned,
        selector_request=prepared.selector_request,
        timeout_ms=R02_D4_S6_TIMEOUT_MS,
    )
    assert result.raw_response is None
    assert result.input_tokens is None
    assert result.launch_error is not None or result.timed_out
    evidence_file = next((tmp_path / "evidence/attempts").glob("*.json"))
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert evidence["parse_error_code"] == expected_error


def test_live_capability_cannot_be_injected_without_live_authorization(
    tmp_path: Path,
) -> None:
    with pytest.raises(R02D4S7TransportError, match="LIVE authorization"):
        R02D4S7CodexTransport(
            repository_root=ROOT,
            output_schema_path=SCHEMA,
            process_runner=LiveCapableFakeProcessRunner(),
            evidence_store=R02D4S7TransportEvidenceStore(tmp_path / "evidence"),
            live_authorized=False,
        )


def test_schema_byte_drift_is_rejected_before_process_call(tmp_path: Path) -> None:
    schema = tmp_path / "schema.json"
    schema.write_bytes(SCHEMA.read_bytes() + b"\n")
    runner = FakeProcessRunner()
    with pytest.raises(R02D4S7TransportError, match="schema"):
        R02D4S7CodexTransport(
            repository_root=ROOT,
            output_schema_path=schema,
            process_runner=runner,
            evidence_store=R02D4S7TransportEvidenceStore(tmp_path / "evidence"),
            live_authorized=False,
        )
    assert runner.calls == []


def test_complete_69_case_fake_run_uses_temp_root_and_replays(tmp_path: Path) -> None:
    run_id = "r02-d4-s7-offline-full"
    runner = FakeProcessRunner()
    audit_root = tmp_path / "s7-audit"
    evidence_root = tmp_path / "s7-evidence"
    transport = R02D4S7CodexTransport(
        repository_root=ROOT,
        output_schema_path=SCHEMA,
        process_runner=runner,
        evidence_store=R02D4S7TransportEvidenceStore(evidence_root),
        live_authorized=False,
    )
    orchestrator = R02D4S6Runner(
        repository_root=ROOT,
        audit_root=audit_root,
        authorization=offline_fake_authorization(run_id),
        transport=transport,
    )
    result = orchestrator.run()
    assert result.terminal.terminal_status == "COMPLETE"
    assert result.terminal.final_ledger.launched_attempt_count == 69
    assert result.terminal.final_ledger.reserved_tokens == 2_208_000
    assert result.terminal.final_ledger.external_provider_calls == 0
    assert len(runner.calls) == 69
    assert len(list((evidence_root / "attempts").glob("*.json"))) == 69


def test_schema_file_is_exact_successor_export() -> None:
    from .r02_d3_successor_contracts import selector_output_schema

    assert SCHEMA.read_bytes() == canonical_json_bytes(selector_output_schema())
