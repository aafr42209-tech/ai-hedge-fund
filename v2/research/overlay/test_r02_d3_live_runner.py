from __future__ import annotations

import json
import ast
from pathlib import Path

import pytest

from .canonical import canonical_json_bytes, canonical_sha256
from .codex_exec_client import CodexProcessCapture
from .r02_candidates import prepare_provider_free_episode
from .r02_d3_contracts import selector_output_schema
from .r02_d3_live_audit import R02D3AuditWriter
from .r02_d3_live_orchestrator import (
    R02D3LiveOrchestrator,
    _attempt_id,
    build_run_plan,
    load_accepted_preregistration,
)
from .r02_d3_live_runner_replay import (
    R02D3ReplayError,
    replay_audit_root,
    verify_readiness_artifacts,
)
from .r02_d3_live_selector_adapter import (
    R02D3BoundAttempt,
    R02D3CodexSelectorAdapter,
)
from .r02_d3_preflight import load_frame_episode
from .r02_d3_runner_contracts import (
    R02_D3_ATTEMPT_RESERVE,
    R02D3AttemptStarted,
    R02D3RunAuthorization,
    R02D3TokenReservation,
)
from .r02_selector import build_selector_request


ROOT = Path(__file__).resolve().parents[3]


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
    raw_response: str,
    *,
    usage: object = None,
    duplicate_terminal: bool = False,
    model: str | None = None,
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
    thread = {"type": "thread.started", "thread_id": "thread-r02-d3"}
    if model is not None:
        thread["model"] = model
    events = [
        thread,
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "message-1", "type": "agent_message", "text": raw_response},
        },
        {"type": "turn.completed", "usage": terminal_usage},
    ]
    if duplicate_terminal:
        events.append({"type": "turn.completed", "usage": terminal_usage})
    return ("\n".join(json.dumps(value, separators=(",", ":")) for value in events) + "\n").encode()


class FakeProcessRunner:
    def __init__(
        self,
        responses: list[str] | None = None,
        captures: list[CodexProcessCapture] | None = None,
    ) -> None:
        self.responses = responses or []
        self.captures = captures or []
        self.calls: list[dict[str, object]] = []

    def run(self, **kwargs) -> CodexProcessCapture:
        self.calls.append(kwargs)
        index = len(self.calls) - 1
        if index < len(self.captures):
            return self.captures[index]
        raw = self.responses[index] if index < len(self.responses) else _response()
        return CodexProcessCapture(
            stdout=_jsonl(raw),
            stderr=b"",
            exit_code=0,
            duration_ms=17,
        )


def _authorization(run_id: str) -> R02D3RunAuthorization:
    return R02D3RunAuthorization(
        run_id=run_id,
        mode="OFFLINE_FAKE",
        authorization_sha256="a" * 64,
        runner_readiness_freeze_sha256="b" * 64,
        indivisible_6_plus_49_approved=False,
        provider_calls_authorized=False,
    )


def _schema(tmp_path: Path) -> Path:
    path = (tmp_path / "r02-selector-output-schema.json").resolve()
    path.write_bytes(canonical_json_bytes(selector_output_schema()))
    return path


def _harness(
    tmp_path: Path,
    *,
    run_id: str,
    responses: list[str] | None = None,
    captures: list[CodexProcessCapture] | None = None,
):
    preregistration = load_accepted_preregistration(ROOT)
    runner = FakeProcessRunner(responses, captures)
    adapter = R02D3CodexSelectorAdapter(
        preregistration=preregistration,
        output_schema_path=_schema(tmp_path),
        working_directory=ROOT,
        process_runner=runner,
    )
    authorization = _authorization(run_id)
    audit_root = tmp_path / "audit"
    orchestrator = R02D3LiveOrchestrator(
        repository_root=ROOT,
        audit_root=audit_root,
        authorization=authorization,
        adapter=adapter,
        preregistration=preregistration,
    )
    return orchestrator, runner, audit_root


def _seed_reservation_before_launch(
    orchestrator: R02D3LiveOrchestrator,
    audit_root: Path,
) -> tuple[R02D3AuditWriter, R02D3TokenReservation, str]:
    writer = R02D3AuditWriter(audit_root, orchestrator.authorization.run_id)
    writer.append_json("run_authorization", orchestrator.authorization)
    writer.append_json(
        "freeze_identity",
        {
            "accepted_live_gate_freeze_sha256": (
                orchestrator.authorization.accepted_live_gate_freeze_sha256
            ),
            "runner_readiness_freeze_sha256": (
                orchestrator.authorization.runner_readiness_freeze_sha256
            ),
        },
    )
    writer.append_json("run_plan", orchestrator.plan)
    planned = orchestrator.plan.episodes[0]
    episode = load_frame_episode(ROOT, planned.fixture_id)
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id=orchestrator.authorization.run_id,
        replicate_id=0,
        provider_attempt_count=0,
    )
    request = build_selector_request(preparation)
    attempt_id = _attempt_id(orchestrator.authorization.run_id, planned)
    orchestrator.adapter.bind_attempt(
        R02D3BoundAttempt(orchestrator.authorization, preparation, attempt_id, 1)
    )
    prompt_identity, _, _ = orchestrator.adapter.describe(request)
    writer.append_json("episode_preparation", preparation)
    writer.append_json("prompt_identity", prompt_identity)
    reservation = R02D3TokenReservation(
        run_id=orchestrator.authorization.run_id,
        fixture_id=planned.fixture_id,
        run_ordinal=0,
        attempt_id=attempt_id,
        provider_attempt_ordinal=1,
        reserved_attempts_before=0,
        reserved_tokens_before=0,
        reserved_tokens_after=R02_D3_ATTEMPT_RESERVE,
    )
    writer.append_json("token_reservation", reservation)
    return writer, reservation, attempt_id


def test_plan_is_frozen_micro_six_then_remaining_49_in_frame_order() -> None:
    preregistration = load_accepted_preregistration(ROOT)
    plan = build_run_plan(ROOT, preregistration, "r02-d3-plan-test")
    assert len(plan.episodes) == 55
    assert all(value.micro_pilot for value in plan.episodes[:6])
    assert not any(value.micro_pilot for value in plan.episodes[6:])
    remaining = tuple(value.frame_ordinal for value in plan.episodes[6:])
    assert remaining == tuple(sorted(remaining))


def test_adapter_uses_only_frozen_stdin_live_argv_and_injected_runner(tmp_path: Path) -> None:
    orchestrator, runner, audit_root = _harness(
        tmp_path,
        run_id="r02-d3-adapter-test",
        responses=[_response()],
    )
    preregistration = orchestrator.preregistration
    planned = orchestrator.plan.episodes[0]
    episode = load_frame_episode(ROOT, planned.fixture_id)
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id=orchestrator.authorization.run_id,
        replicate_id=0,
        provider_attempt_count=0,
    )
    request = build_selector_request(preparation)
    attempt_id = _attempt_id(orchestrator.authorization.run_id, planned)
    orchestrator.adapter.bind_attempt(
        R02D3BoundAttempt(orchestrator.authorization, preparation, attempt_id, 1)
    )
    identity, expected_stdin, expected_argv = orchestrator.adapter.describe(request)
    raw, ledger, _ = orchestrator.adapter.select(request)
    assert raw == _response()
    assert runner.calls[0]["stdin_bytes"] == expected_stdin
    assert runner.calls[0]["argv"] == expected_argv
    assert expected_argv[-1] == "-"
    assert ledger.external_provider_calls == 0
    assert identity.requested_model_id == preregistration.model_identity.requested_model_id
    assert not audit_root.exists()


def test_offline_normal_flow_runs_indivisible_6_plus_49_without_provider_calls(tmp_path: Path) -> None:
    orchestrator, runner, audit_root = _harness(
        tmp_path,
        run_id="r02-d3-normal-offline",
    )
    ledger = orchestrator.run()
    assert ledger.status == "COMPLETE"
    assert ledger.launched_attempt_count == 55
    assert ledger.settled_attempt_count == 55
    assert ledger.external_provider_calls == 0
    assert len(runner.calls) == 55
    replay = replay_audit_root(audit_root)
    assert len(replay.attempts_started) == 55
    assert replay.decisions[5].action == "CONTINUE"
    assert not replay.decisions[5].second_authorization_requested
    assert not replay.decisions[5].utility_outcomes_consulted
    calls_before = len(runner.calls)
    assert orchestrator.run().status == "COMPLETE"
    assert len(runner.calls) == calls_before


def test_second_micro_fallback_is_a_hard_stop_and_both_attempts_remain_itt(tmp_path: Path) -> None:
    orchestrator, runner, audit_root = _harness(
        tmp_path,
        run_id="r02-d3-micro-fallback",
        responses=["{}", "{}"],
    )
    ledger = orchestrator.run()
    assert ledger.status == "HARD_STOP"
    assert ledger.terminal_code == "MICRO_SELECTOR_FALLBACK_CAP_EXCEEDED"
    assert ledger.launched_attempt_count == 2
    assert ledger.fallback_count == 2
    assert len(ledger.attempted_fixture_ids) == 2
    assert len(runner.calls) == 2
    replay = replay_audit_root(audit_root)
    paired = tuple(json.loads(raw) for raw in replay.payloads_by_type["paired_result"])
    assert all(value["paired_utility_delta_e12"] == 0 for value in paired)


def test_sixth_full_fail_closed_attempt_stops_without_retry_or_replacement(tmp_path: Path) -> None:
    responses = [_response() for _ in range(11)]
    for index in (0, 6, 7, 8, 9, 10):
        responses[index] = "{}"
    orchestrator, runner, _ = _harness(
        tmp_path,
        run_id="r02-d3-full-fallback",
        responses=responses,
    )
    ledger = orchestrator.run()
    assert ledger.terminal_code == "FULL_FAIL_CLOSED_ATTEMPT_CAP_EXCEEDED"
    assert ledger.launched_attempt_count == 11
    assert ledger.fallback_count == 6
    assert len(runner.calls) == 11


@pytest.mark.parametrize(
    ("stdout", "expected_code"),
    (
        (_jsonl(_response(), usage={}), "missing_usage"),
        (_jsonl(_response(), duplicate_terminal=True), "duplicate_terminal_event"),
        (
            _jsonl(
                _response(),
                usage={
                    "input_tokens": -1,
                    "cached_input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_output_tokens": 0,
                },
            ),
            "invalid_usage",
        ),
    ),
)
def test_missing_duplicate_or_invalid_usage_debits_reserve_and_stops_unsettled(
    tmp_path: Path,
    stdout: bytes,
    expected_code: str,
) -> None:
    capture = CodexProcessCapture(stdout=stdout, stderr=b"", exit_code=0, duration_ms=1)
    orchestrator, _, audit_root = _harness(
        tmp_path,
        run_id=f"r02-d3-usage-{expected_code.replace('_', '-')}",
        captures=[capture],
    )
    ledger = orchestrator.run()
    assert ledger.status == "HARD_STOP"
    assert ledger.terminal_code == expected_code
    assert ledger.unsettled_attempt_count == 1
    assert ledger.debited_tokens == R02_D3_ATTEMPT_RESERVE
    replay = replay_audit_root(audit_root)
    assert not replay.settlements[-1].settled
    assert replay.settlements[-1].debit_tokens == R02_D3_ATTEMPT_RESERVE


@pytest.mark.parametrize(
    ("capture", "expected_code"),
    (
        (
            CodexProcessCapture(
                stdout=b"", stderr=b"", exit_code=None, duration_ms=1, timed_out=True
            ),
            "TIMEOUT",
        ),
        (
            CodexProcessCapture(
                stdout=_jsonl(_response()), stderr=b"boom", exit_code=2, duration_ms=1
            ),
            "PROCESS_STATUS_VIOLATION",
        ),
        (
            CodexProcessCapture(
                stdout=_jsonl(_response(), model="wrong-model"),
                stderr=b"",
                exit_code=0,
                duration_ms=1,
            ),
            "model_identity_mismatch",
        ),
    ),
)
def test_timeout_nonzero_and_model_echo_mismatch_fail_closed(
    tmp_path: Path,
    capture: CodexProcessCapture,
    expected_code: str,
) -> None:
    orchestrator, runner, _ = _harness(
        tmp_path,
        run_id=f"r02-d3-transport-{expected_code.lower().replace('_', '-')}",
        captures=[capture],
    )
    ledger = orchestrator.run()
    assert ledger.terminal_code == expected_code
    assert len(runner.calls) == 1


def test_actual_usage_above_reserve_marks_invalid_run_budget_breach(tmp_path: Path) -> None:
    capture = CodexProcessCapture(
        stdout=_jsonl(
            _response(),
            usage={
                "input_tokens": 32_001,
                "cached_input_tokens": 0,
                "output_tokens": 0,
                "reasoning_output_tokens": 0,
            },
        ),
        stderr=b"",
        exit_code=0,
        duration_ms=1,
    )
    orchestrator, _, audit_root = _harness(
        tmp_path,
        run_id="r02-d3-budget-breach",
        captures=[capture],
    )
    ledger = orchestrator.run()
    assert ledger.status == "INVALID_RUN"
    assert ledger.terminal_code == "INVALID_RUN_BUDGET_BREACH"
    assert replay_audit_root(audit_root).settlements[-1].invalid_run_budget_breach


def test_resume_after_launch_never_retries_same_episode(tmp_path: Path) -> None:
    orchestrator, runner, audit_root = _harness(
        tmp_path,
        run_id="r02-d3-crash-after-launch",
    )
    writer, reservation, attempt_id = _seed_reservation_before_launch(
        orchestrator, audit_root
    )
    writer.append_json(
        "attempt_started",
        R02D3AttemptStarted(
            run_id=orchestrator.authorization.run_id,
            fixture_id=reservation.fixture_id,
            attempt_id=attempt_id,
            provider_attempt_ordinal=1,
            reservation_sha256=canonical_sha256(reservation),
        ),
    )
    ledger = orchestrator.run()
    assert ledger.terminal_code == "CRASH_AFTER_LAUNCH_UNSETTLED"
    assert len(runner.calls) == 0


def test_resume_after_crash_before_launch_uses_existing_reservation_once(
    tmp_path: Path,
) -> None:
    orchestrator, runner, audit_root = _harness(
        tmp_path,
        run_id="r02-d3-crash-before-launch",
        responses=["{}", "{}"],
    )
    _seed_reservation_before_launch(orchestrator, audit_root)
    ledger = orchestrator.run()
    assert ledger.terminal_code == "MICRO_SELECTOR_FALLBACK_CAP_EXCEEDED"
    assert len(runner.calls) == 2
    replay = replay_audit_root(audit_root)
    assert len(replay.reservations) == 2
    assert len(replay.attempts_started) == 2
    assert len({value.attempt_id for value in replay.attempts_started}) == 2


def test_append_only_tamper_or_orphan_fails_replay(tmp_path: Path) -> None:
    orchestrator, _, audit_root = _harness(
        tmp_path,
        run_id="r02-d3-tamper-test",
        responses=["{}", "{}"],
    )
    orchestrator.run()
    (audit_root / "orphan.bin").write_bytes(b"orphan")
    with pytest.raises(R02D3ReplayError, match="orphan"):
        replay_audit_root(audit_root)


def test_live_authorization_cannot_be_inferred_from_offline_approval() -> None:
    with pytest.raises(ValueError, match="live mode requires"):
        R02D3RunAuthorization(
            run_id="r02-d3-live-not-approved",
            mode="LIVE",
            authorization_sha256="a" * 64,
            runner_readiness_freeze_sha256="b" * 64,
            indivisible_6_plus_49_approved=False,
            provider_calls_authorized=False,
        )


def test_adapter_rejects_prompt_executable_and_schema_drift(tmp_path: Path) -> None:
    preregistration = load_accepted_preregistration(ROOT)
    schema_path = _schema(tmp_path)
    schema_path.write_bytes(b"{}")
    with pytest.raises(ValueError, match="schema"):
        R02D3CodexSelectorAdapter(
            preregistration=preregistration,
            output_schema_path=schema_path,
            working_directory=ROOT,
            process_runner=FakeProcessRunner(),
        )
    schema_path.write_bytes(canonical_json_bytes(selector_output_schema()))
    drifted_prompt = preregistration.prompt.model_copy(
        update={"system_prompt": preregistration.prompt.system_prompt + " drift"}
    )
    with pytest.raises(ValueError, match="preregistration identity drift"):
        R02D3CodexSelectorAdapter(
            preregistration=preregistration.model_copy(update={"prompt": drifted_prompt}),
            output_schema_path=schema_path,
            working_directory=ROOT,
            process_runner=FakeProcessRunner(),
        )
    drifted_model = preregistration.model_identity.model_copy(
        update={"executable_sha256": "0" * 64}
    )
    with pytest.raises(ValueError, match="preregistration identity drift"):
        R02D3CodexSelectorAdapter(
            preregistration=preregistration.model_copy(
                update={"model_identity": drifted_model}
            ),
            output_schema_path=schema_path,
            working_directory=ROOT,
            process_runner=FakeProcessRunner(),
        )


def test_new_runner_sources_have_no_direct_provider_or_network_boundary() -> None:
    relative_paths = (
        "v2/research/overlay/r02_d3_runner_contracts.py",
        "v2/research/overlay/r02_d3_live_selector_adapter.py",
        "v2/research/overlay/r02_d3_live_orchestrator.py",
        "v2/research/overlay/r02_d3_live_audit.py",
        "v2/research/overlay/r02_d3_live_runner_replay.py",
        "scripts/r02_d3_live_runner_readiness.py",
    )
    banned_modules = {"socket", "requests", "httpx", "urllib", "subprocess"}
    for relative_path in relative_paths:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        assert not (imports & banned_modules), relative_path
        assert "SubprocessCodexProcessRunner" not in source
        if relative_path.endswith("r02_d3_live_orchestrator.py"):
            assert not any(isinstance(node, ast.Assert) for node in ast.walk(tree))


def test_invalid_utf8_readiness_manifest_is_typed_replay_error(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "r02-d3-runner-readiness-freeze.json").write_bytes(
        (ROOT / "docs/r02-d3-runner-readiness-freeze.json").read_bytes()
    )
    (docs / "r02-d3-runner-readiness-manifest.json").write_bytes(b"\xff")
    with pytest.raises(R02D3ReplayError, match="readiness artifact load failed"):
        verify_readiness_artifacts(tmp_path)


def test_readiness_manifest_replays_and_excludes_provider_argv() -> None:
    verification = verify_readiness_artifacts(ROOT)
    assert verification.verified_source_pins == 6
    assert verification.zero_call_allowlist_excludes_live_argv
    manifest = json.loads(
        (ROOT / "docs/r02-d3-runner-readiness-manifest.json").read_text(encoding="utf-8")
    )
    flattened = [
        token for argv in manifest["zero_call_commands"].values() for token in argv
    ]
    assert "exec" not in flattened
    assert "--output-schema" not in flattened
    assert manifest["provider_calls"] == 0
    assert not manifest["live_execution"]
