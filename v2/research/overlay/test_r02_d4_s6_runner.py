from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from .artifacts import ArtifactIntegrityError
from .canonical import canonical_sha256
from .r02_d4_s6_audit import R02D4S6AuditError
from .r02_d4_s6_contracts import (
    offline_fake_authorization,
    R02_D4_S6_ATTEMPT_CAP,
    R02_D4_S6_FAIL_CLOSED_CAP,
    R02_D4_S6_HARD_STOP_CONDITIONS,
    R02_D4_S6_TIMEOUT_MS,
    R02_D4_S6_TOKEN_CAP,
    R02_D4_S6_TOKEN_RESERVE,
    R02D4S6ContractBinding,
    R02D4S6LiveAuthorizationArtifact,
    R02D4S6RunAuthorization,
    R02D4S6TransportResult,
)
from .r02_d4_s6_replay import R02D4S6ReplayError, replay_s6_audit_root
from .r02_d4_s6_runner import (
    build_provider_free_run_plan,
    R02D4S6Runner,
    R02D4S6RunnerError,
)

ROOT = Path(__file__).resolve().parents[3]
_PREPARED_RUN = None


def _prepared_run():
    global _PREPARED_RUN
    if _PREPARED_RUN is None:
        _PREPARED_RUN = build_provider_free_run_plan(ROOT)
    return _PREPARED_RUN


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


class FakeTransport:
    r02_d4_s6_execution_capability = "OFFLINE_FAKE"

    def __init__(self, modes: list[str] | None = None) -> None:
        self.modes = modes or []
        self.calls: list[dict[str, object]] = []

    def execute(
        self,
        *,
        run_id: str,
        attempt_id: str,
        attempt,
        selector_request,
        timeout_ms: int,
    ) -> R02D4S6TransportResult:
        self.calls.append(
            {
                "run_id": run_id,
                "attempt_id": attempt_id,
                "fixture_id": attempt.fixture_id,
                "request_sha256": canonical_sha256(selector_request),
                "timeout_ms": timeout_ms,
            }
        )
        mode = self.modes[len(self.calls) - 1] if len(self.calls) <= len(self.modes) else "OK"
        raw = "{}" if mode == "FALLBACK" else _response()
        common = {
            "run_id": run_id,
            "fixture_id": attempt.fixture_id,
            "attempt_id": attempt_id,
            "duration_ms": 17,
            "external_provider_calls": 0,
        }
        if mode == "TIMEOUT":
            return R02D4S6TransportResult(
                **common,
                raw_response=None,
                raw_response_sha256=canonical_sha256({"raw_response": None}),
                terminal_usage_event_count=0,
                exit_code=None,
                timed_out=True,
            )
        if mode == "MISSING_USAGE":
            return R02D4S6TransportResult(
                **common,
                raw_response=raw,
                raw_response_sha256=canonical_sha256({"raw_response": raw}),
                terminal_usage_event_count=0,
                exit_code=0,
                timed_out=False,
            )
        input_tokens = 32_001 if mode == "OVER_RESERVE" else 100
        cached_input_tokens = 101 if mode == "BAD_CACHED_SUBSET" else 40
        output_tokens = 20
        reasoning_output_tokens = 21 if mode == "BAD_REASONING_SUBSET" else 5
        return R02D4S6TransportResult(
            **common,
            raw_response=raw,
            raw_response_sha256=canonical_sha256({"raw_response": raw}),
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            reasoning_output_tokens=reasoning_output_tokens,
            terminal_usage_event_count=2 if mode == "DUPLICATE_USAGE" else 1,
            exit_code=7 if mode == "NONZERO_EXIT" else 0,
            timed_out=False,
            launch_error="fake launch error" if mode == "LAUNCH_ERROR" else None,
        )


class WrongCapabilityTransport(FakeTransport):
    r02_d4_s6_execution_capability = "LIVE_PROVIDER_PROCESS"


def _runner(tmp_path: Path, modes: list[str] | None = None, *, root_name: str = "audit"):
    transport = FakeTransport(modes)
    runner = R02D4S6Runner(
        repository_root=ROOT,
        audit_root=tmp_path / root_name,
        authorization=offline_fake_authorization("r02-d4-s6-offline-test"),
        transport=transport,
        prepared_run=_prepared_run(),
    )
    return runner, transport


def test_sealed_plan_binds_exact_s5_order_and_request_identities() -> None:
    prepared = _prepared_run()
    assert len(prepared.attempts) == R02_D4_S6_ATTEMPT_CAP == 69
    assert prepared.plan.micro_pilot_decision == "NO_MICRO_PILOT"
    assert prepared.plan.retry_cap == prepared.plan.replacement_cap == prepared.plan.resume_cap == 0
    assert prepared.plan.attempts[0].fixture_id == "development-0002"
    assert prepared.plan.attempts[-1].fixture_id == "development-0560"
    assert tuple(item.planned for item in prepared.attempts) == prepared.plan.attempts
    assert all(item.planned.selector_request_sha256 == canonical_sha256(item.selector_request) for item in prepared.attempts)


def test_all_69_fake_attempts_complete_and_replay_byte_exact(tmp_path: Path) -> None:
    runner, transport = _runner(tmp_path)
    result = runner.run()
    assert result.terminal.terminal_status == "COMPLETE"
    ledger = result.terminal.final_ledger
    assert ledger.reserved_attempt_count == ledger.launched_attempt_count == 69
    assert ledger.reserved_tokens == R02_D4_S6_TOKEN_CAP == 2_208_000
    assert ledger.settled_attempt_count == 69
    assert ledger.unsettled_attempt_count == 0
    assert ledger.micro_pilot_attempts == 0
    assert ledger.retry_count == ledger.replacement_count == ledger.resume_count == 0
    assert ledger.external_provider_calls == 0
    assert len(transport.calls) == 69
    assert all(call["timeout_ms"] == R02_D4_S6_TIMEOUT_MS for call in transport.calls)
    replay = replay_s6_audit_root(
        result.audit_root,
        repository_root=ROOT,
        expected_authorization=runner.authorization,
        expected_plan=runner.prepared_run.plan,
        expected_prepared_run=runner.prepared_run,
    )
    assert canonical_sha256(replay.terminal) == canonical_sha256(result.terminal)
    assert replay.node_count == 3 + (69 * 6) + 1

    orphan = result.audit_root / "payloads/orphan.json"
    orphan.write_text("{}", encoding="utf-8")
    with pytest.raises(R02D4S6ReplayError, match="orphan"):
        replay_s6_audit_root(result.audit_root, repository_root=ROOT)


def test_seventh_settled_fallback_is_invalid_hard_stop(tmp_path: Path) -> None:
    runner, transport = _runner(tmp_path, ["FALLBACK"] * 7)
    result = runner.run()
    ledger = result.terminal.final_ledger
    assert len(transport.calls) == 7
    assert ledger.status == "INVALID_RUN"
    assert ledger.settled_fail_closed_count == R02_D4_S6_FAIL_CLOSED_CAP + 1 == 7
    assert ledger.terminal_code == "SETTLED_FAIL_CLOSED_COUNT_WOULD_EXCEED_6"
    assert ledger.unsettled_attempt_count == 0


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        (
            "TIMEOUT",
            "TRANSPORT_TIMEOUT_NONZERO_EXIT_MISSING_USAGE_OR_UNSETTLED_ATTEMPT",
        ),
        (
            "MISSING_USAGE",
            "TRANSPORT_TIMEOUT_NONZERO_EXIT_MISSING_USAGE_OR_UNSETTLED_ATTEMPT",
        ),
        ("OVER_RESERVE", "REPORTED_USAGE_OVER_32000_TOKEN_RESERVE"),
    ],
)
def test_unsettled_or_over_reserve_debits_full_reserve_then_stops(tmp_path: Path, mode: str, code: str) -> None:
    runner, transport = _runner(tmp_path, [mode])
    result = runner.run()
    ledger = result.terminal.final_ledger
    assert len(transport.calls) == 1
    assert ledger.status == "INVALID_RUN"
    assert ledger.terminal_code == code
    assert ledger.debited_tokens == R02_D4_S6_TOKEN_RESERVE
    assert ledger.unsettled_attempt_count == 1
    assert ledger.reserved_attempt_count == 1
    if mode == "TIMEOUT":
        for extra in (
            "NONZERO_EXIT",
            "LAUNCH_ERROR",
            "DUPLICATE_USAGE",
            "BAD_CACHED_SUBSET",
            "BAD_REASONING_SUBSET",
        ):
            extra_runner, extra_transport = _runner(
                tmp_path,
                [extra],
                root_name=f"audit-{extra.lower().replace('_', '-')}",
            )
            extra_result = extra_runner.run()
            extra_ledger = extra_result.terminal.final_ledger
            assert len(extra_transport.calls) == 1
            assert extra_ledger.terminal_code == ("TRANSPORT_TIMEOUT_NONZERO_EXIT_MISSING_USAGE_OR_UNSETTLED_ATTEMPT")
            assert extra_ledger.debited_tokens == R02_D4_S6_TOKEN_RESERVE
            assert extra_ledger.unsettled_attempt_count == 1


def test_fake_mode_rejects_production_root_before_transport(tmp_path: Path) -> None:
    transport = FakeTransport()
    with pytest.raises(R02D4S6AuditError, match="outside the repository"):
        R02D4S6Runner(
            repository_root=ROOT,
            audit_root=ROOT / ".research_artifacts/r02-d4-s6-forbidden-test",
            authorization=offline_fake_authorization("r02-d4-s6-root-test"),
            transport=transport,
            prepared_run=_prepared_run(),
        )
    assert transport.calls == []


def test_missing_live_authorization_and_capability_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="separate external authorization"):
        R02D4S6RunAuthorization(
            run_id="r02-d4-s6-live-test",
            mode="LIVE",
            authorization_sha256="0" * 64,
            artifact_root_kind="PRODUCTION",
            provider_calls_authorized=True,
            production_artifact_root_authorized=True,
            all_69_one_shot_authorized=True,
        )
    with pytest.raises(R02D4S6RunnerError, match="transport capability"):
        R02D4S6Runner(
            repository_root=ROOT,
            audit_root=tmp_path / "audit",
            authorization=offline_fake_authorization("r02-d4-s6-capability-test"),
            transport=WrongCapabilityTransport(),
            prepared_run=_prepared_run(),
        )

    artifact = R02D4S6LiveAuthorizationArtifact(
        authorization_id="r02-d4-live-auth-test-one",
        run_id="r02-d4-s6-live-test",
        accepted_s6_review_sha256="1" * 64,
    )
    bound_live = R02D4S6RunAuthorization(
        run_id=artifact.run_id,
        mode="LIVE",
        authorization_sha256=canonical_sha256(artifact),
        artifact_root_kind="PRODUCTION",
        provider_calls_authorized=True,
        production_artifact_root_authorized=True,
        all_69_one_shot_authorized=True,
        live_authorization_artifact=artifact,
    )
    live_transport = WrongCapabilityTransport()
    with pytest.raises(R02D4S6RunnerError, match="separate external authorization file"):
        R02D4S6Runner(
            repository_root=ROOT,
            audit_root=tmp_path / "unused-live-root",
            authorization=bound_live,
            transport=live_transport,
            prepared_run=_prepared_run(),
        )
    assert live_transport.calls == []


def test_contract_tamper_cannot_loosen_hard_stops_or_zero_caps() -> None:
    with pytest.raises(ValidationError):
        R02D4S6ContractBinding(hard_stop_conditions=tuple(reversed(R02_D4_S6_HARD_STOP_CONDITIONS)))
    clean = offline_fake_authorization("r02-d4-s6-contract-test")
    payload = clean.model_dump(mode="python")
    payload["retry_cap"] = 1
    with pytest.raises(ValidationError):
        R02D4S6RunAuthorization.model_validate(payload)


def test_audit_root_is_append_only_and_cannot_be_resumed(tmp_path: Path) -> None:
    root = tmp_path / "audit"
    runner, _ = _runner(tmp_path, ["TIMEOUT"])
    runner.run()
    with pytest.raises(R02D4S6AuditError, match="retry and resume"):
        R02D4S6Runner(
            repository_root=ROOT,
            audit_root=root,
            authorization=offline_fake_authorization("r02-d4-s6-offline-test"),
            transport=FakeTransport(),
            prepared_run=_prepared_run(),
        )


def test_replay_rejects_payload_byte_tamper(tmp_path: Path) -> None:
    runner, _ = _runner(tmp_path, ["TIMEOUT"])
    result = runner.run()
    payload = result.audit_root / "payloads/00001-run_authorization.json"
    payload.write_bytes(payload.read_bytes() + b" ")
    with pytest.raises((R02D4S6ReplayError, ArtifactIntegrityError)):
        replay_s6_audit_root(result.audit_root, repository_root=ROOT)


def test_s6_sources_have_no_provider_process_or_network_boundary() -> None:
    forbidden_imports = {
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "codex_exec_client",
    }
    for name in (
        "r02_d4_s6_contracts.py",
        "r02_d4_s6_audit.py",
        "r02_d4_s6_runner.py",
        "r02_d4_s6_replay.py",
    ):
        path = ROOT / "v2/research/overlay" / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[-1])
        assert imported.isdisjoint(forbidden_imports)
