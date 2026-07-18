"""Fail-closed 6+49 R02 D3 production runner orchestration."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from pydantic import ValidationError

from .baselines import primary_deterministic
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import ASSET_IDS, Decision, DecisionBatch, SyntheticEpisode
from .r02_candidates import canonical_candidate_id, prepare_provider_free_episode
from .r02_contracts import R02CandidateBatch, R02ProviderFreePreparation
from .r02_d3_live_audit import R02D3AuditWriter, audit_root_has_files
from .r02_d3_live_runner_replay import (
    R02D3ReplayError,
    replay_audit_root,
    verify_readiness_artifacts,
)
from .r02_d3_live_selector_adapter import (
    R02D3BoundAttempt,
    R02D3CodexSelectorAdapter,
    R02D3SelectorTransportError,
)
from .r02_d3_preflight import R02D3Preregistration, load_frame_episode
from .r02_d3_runner_contracts import (
    R02_D3_ATTEMPT_RESERVE,
    R02_D3_ACCEPTED_PREREGISTRATION_SHA256,
    R02_D3_FULL_ATTEMPTS,
    R02_D3_FULL_FAIL_CLOSED_CAP,
    R02_D3_FULL_TOKEN_CAP,
    R02_D3_MICRO_ATTEMPTS,
    R02_D3_MICRO_FALLBACK_CAP,
    R02_D3_MICRO_TOKEN_CAP,
    R02D3AttemptStarted,
    R02D3CandidateExecution,
    R02D3ContinuationDecision,
    R02D3LiveAuthorizationArtifact,
    R02D3PairedResult,
    R02D3PlannedEpisode,
    R02D3PrelaunchFailure,
    R02D3RunAuthorization,
    R02D3RunLedger,
    R02D3RunPlan,
    R02D3SelectorOutcome,
    R02D3TokenReservation,
    R02D3TokenSettlement,
)
from .r02_selector import R02SelectorParseError, build_selector_request, parse_selector_response
from .scoring import score_episode
from .validator import validate_batch


class R02D3OrchestratorError(RuntimeError):
    pass


def verify_external_live_authorization_artifact(
    repository_root: str | Path,
    audit_root: str | Path,
    authorization: R02D3RunAuthorization,
    artifact_path: str | Path | None,
) -> Path | None:
    """Bind LIVE scope to exact external canonical bytes; offline rejects the path."""

    if authorization.mode == "OFFLINE_FAKE":
        if artifact_path is not None:
            raise R02D3OrchestratorError(
                "offline mode cannot receive a live authorization artifact path"
            )
        return None
    if artifact_path is None:
        raise R02D3OrchestratorError("live mode requires an external authorization artifact")
    root = Path(repository_root).resolve()
    audit = Path(audit_root).resolve()
    path = Path(artifact_path).resolve()
    if not path.is_file():
        raise R02D3OrchestratorError("external live authorization artifact is missing")
    if path == root or root in path.parents or path == audit or audit in path.parents:
        raise R02D3OrchestratorError(
            "live authorization artifact must remain outside repository and audit roots"
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise R02D3OrchestratorError(
            "external live authorization artifact could not be read"
        ) from exc
    if sha256_hex(raw) != authorization.authorization_sha256:
        raise R02D3OrchestratorError("external live authorization artifact hash mismatch")
    try:
        artifact = R02D3LiveAuthorizationArtifact.model_validate_json(raw)
    except ValidationError as exc:
        raise R02D3OrchestratorError(
            "external live authorization artifact validation failed"
        ) from exc
    if raw != canonical_json_bytes(artifact):
        raise R02D3OrchestratorError(
            "external live authorization artifact is not canonical JSON"
        )
    if artifact != authorization.live_authorization_artifact:
        raise R02D3OrchestratorError("external live authorization artifact identity mismatch")
    return path


def load_accepted_preregistration(repository_root: str | Path) -> R02D3Preregistration:
    path = Path(repository_root).resolve() / "docs/r02-d3-preregistration.json"
    if sha256_hex(path.read_bytes()) != R02_D3_ACCEPTED_PREREGISTRATION_SHA256:
        raise R02D3OrchestratorError("accepted D3 preregistration artifact drift")
    return R02D3Preregistration.model_validate_json(path.read_bytes())


def build_run_plan(
    repository_root: str | Path,
    preregistration: R02D3Preregistration,
    run_id: str,
) -> R02D3RunPlan:
    root = Path(repository_root).resolve()
    frame = json.loads((root / "docs/r02-d2c-frame-manifest.json").read_text(encoding="utf-8"))
    raw_cases = frame.get("cases")
    if not isinstance(raw_cases, list):
        raise R02D3OrchestratorError("frozen frame cases are missing")
    eligible = {
        str(value["fixture_id"]): value
        for value in raw_cases
        if isinstance(value, dict)
        and value.get("eligible_opportunity") is True
        and value.get("triggered") is True
        and value.get("candidate_count") in (2, 3, 4)
    }
    if len(eligible) != R02_D3_FULL_ATTEMPTS:
        raise R02D3OrchestratorError("frozen eligible frame must contain exactly 55 cases")
    micro_ids = tuple(case.fixture_id for case in preregistration.execution.cases)
    if len(micro_ids) != R02_D3_MICRO_ATTEMPTS or not set(micro_ids).issubset(eligible):
        raise R02D3OrchestratorError("frozen micro-pilot is not a subset of the eligible frame")
    ordered = tuple(eligible[fixture_id] for fixture_id in micro_ids) + tuple(
        sorted(
            (value for fixture_id, value in eligible.items() if fixture_id not in micro_ids),
            key=lambda value: int(value["frame_ordinal"]),
        )
    )
    return R02D3RunPlan(
        run_id=run_id,
        episodes=tuple(
            R02D3PlannedEpisode(
                run_ordinal=index,
                frame_ordinal=int(value["frame_ordinal"]),
                fixture_id=str(value["fixture_id"]),
                stratum=str(value["stratum"]),
                candidate_count=int(value["candidate_count"]),
                micro_pilot=index < R02_D3_MICRO_ATTEMPTS,
            )
            for index, value in enumerate(ordered)
        ),
    )


def _validation_batch(candidate: R02CandidateBatch) -> DecisionBatch:
    return DecisionBatch(
        decisions={
            asset_id: Decision(
                action=candidate.decisions[asset_id].action,
                quantity=candidate.decisions[asset_id].quantity,
                confidence=100,
                reasoning="r02:d3-live-acceptance-gate",
            )
            for asset_id in ASSET_IDS
        }
    )


def _semantic_match(candidate: R02CandidateBatch, validation) -> bool:
    return all(
        candidate.decisions[asset_id].action
        == validation.executable.decisions[asset_id].action
        and candidate.decisions[asset_id].quantity
        == validation.executable.decisions[asset_id].quantity
        for asset_id in ASSET_IDS
    )


def _evaluate_selection(
    authorization: R02D3RunAuthorization,
    episode: SyntheticEpisode,
    preparation: R02ProviderFreePreparation,
    attempt_id: str,
    raw_response: str,
) -> tuple[R02D3SelectorOutcome, R02D3CandidateExecution, R02D3PairedResult]:
    if preparation.candidate_set is None or preparation.permutation is None:
        raise R02D3OrchestratorError("eligible preparation lacks candidates or permutation")
    baseline = primary_deterministic(episode)
    if not baseline.validation.raw_valid or baseline.validation.fell_back:
        raise R02D3OrchestratorError("primary baseline is not executable")
    baseline_batch = R02CandidateBatch(
        decisions={
            asset_id: {
                "action": baseline.validation.executable.decisions[asset_id].action,
                "quantity": baseline.validation.executable.decisions[asset_id].quantity,
            }
            for asset_id in ASSET_IDS
        }
    )
    baseline_id = canonical_candidate_id(baseline_batch)
    if baseline_id != preparation.candidate_set.baseline_canonical_candidate_id:
        raise R02D3OrchestratorError("primary baseline identity drift")

    selected_presented_id: str | None = None
    selected_canonical_id: str | None = None
    selected_candidate = None
    selected_validation = None
    error_codes: tuple[str, ...] = ()
    try:
        parsed = parse_selector_response(raw_response)
        selected_presented_id = parsed.selected_candidate_id
        selected_canonical_id = preparation.permutation.presented_to_canonical_map.get(
            selected_presented_id
        )
        selected_candidate = next(
            (
                candidate
                for candidate in preparation.candidate_set.candidates
                if candidate.canonical_candidate_id == selected_canonical_id
            ),
            None,
        )
        if selected_candidate is None:
            error_codes = ("UNKNOWN_PRESENTED_ID",)
        else:
            selected_validation = validate_batch(
                episode.public,
                _validation_batch(selected_candidate.candidate),
            )
            if (
                not selected_validation.raw_valid
                or selected_validation.fell_back
                or not _semantic_match(selected_candidate.candidate, selected_validation)
            ):
                error_codes = ("ACCEPTANCE_VALIDATION_FAILED",)
    except R02SelectorParseError as exc:
        error_codes = exc.codes

    fallback = bool(error_codes)
    if fallback:
        executed_id = baseline_id
        executed_validation = baseline.validation
    else:
        if selected_candidate is None or selected_validation is None:
            raise R02D3OrchestratorError(
                "accepted selector outcome is missing candidate validation"
            )
        executed_id = selected_candidate.canonical_candidate_id
        executed_validation = selected_validation
    outcome = R02D3SelectorOutcome(
        run_id=authorization.run_id,
        fixture_id=preparation.identity.fixture_id,
        attempt_id=attempt_id,
        selected_presented_id=selected_presented_id,
        selected_canonical_id=selected_canonical_id,
        baseline_canonical_id=baseline_id,
        executed_canonical_id=executed_id,
        baseline_fallback=fallback,
        error_codes=error_codes,
    )
    execution = R02D3CandidateExecution(
        run_id=authorization.run_id,
        fixture_id=preparation.identity.fixture_id,
        attempt_id=attempt_id,
        executed_canonical_id=executed_id,
        validation_report_sha256=canonical_sha256(executed_validation),
        baseline_fallback=fallback,
    )
    executed_score = score_episode(episode, executed_validation)
    paired = R02D3PairedResult(
        run_id=authorization.run_id,
        fixture_id=preparation.identity.fixture_id,
        attempt_id=attempt_id,
        baseline_utility_e12=baseline.score.utility_e12,
        executed_utility_e12=executed_score.utility_e12,
        paired_utility_delta_e12=executed_score.utility_e12 - baseline.score.utility_e12,
        baseline_fallback=fallback,
    )
    return outcome, execution, paired


def _attempt_id(run_id: str, planned: R02D3PlannedEpisode) -> str:
    return canonical_sha256(
        {
            "domain": "r02-d3-provider-attempt-v1",
            "run_id": run_id,
            "run_ordinal": planned.run_ordinal,
            "fixture_id": planned.fixture_id,
        }
    )


class R02D3LiveOrchestrator:
    def __init__(
        self,
        *,
        repository_root: str | Path,
        audit_root: str | Path,
        authorization: R02D3RunAuthorization,
        adapter: R02D3CodexSelectorAdapter,
        preregistration: R02D3Preregistration,
        live_authorization_artifact_path: str | Path | None = None,
    ) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.audit_root = Path(audit_root).resolve()
        self.authorization = authorization
        self.adapter = adapter
        self.preregistration = preregistration
        self.live_authorization_artifact_path = verify_external_live_authorization_artifact(
            self.repository_root,
            self.audit_root,
            authorization,
            live_authorization_artifact_path,
        )
        self.plan = build_run_plan(self.repository_root, preregistration, authorization.run_id)
        if authorization.mode == "LIVE":
            verification = verify_readiness_artifacts(self.repository_root)
            if verification.freeze_sha256 != authorization.runner_readiness_freeze_sha256:
                raise R02D3OrchestratorError("live authorization readiness freeze mismatch")

    def run(self) -> R02D3RunLedger:
        verify_external_live_authorization_artifact(
            self.repository_root,
            self.audit_root,
            self.authorization,
            self.live_authorization_artifact_path,
        )
        if audit_root_has_files(self.audit_root):
            state = replay_audit_root(self.audit_root)
            if state.authorization != self.authorization or state.plan != self.plan:
                raise R02D3OrchestratorError("resume authorization or plan identity mismatch")
            if state.ledgers and state.ledgers[-1].status != "RUNNING":
                return state.ledgers[-1]
            writer = R02D3AuditWriter(
                self.audit_root,
                self.authorization.run_id,
                existing_anchor=state.anchor,
            )
            launched_ids = {value.attempt_id for value in state.attempts_started}
            settled_ids = {value.attempt_id for value in state.settlements}
            unsettled = launched_ids - settled_ids
            if unsettled:
                return self._seal_crash_after_launch(writer, state, next(iter(unsettled)))
            latest = state.ledgers[-1] if state.ledgers else None
            reserved_count = (
                latest.reserved_attempt_count if latest else len(state.reservations)
            )
            launched_count = (
                latest.launched_attempt_count if latest else len(state.attempts_started)
            )
            settled_count = (
                latest.settled_attempt_count if latest else len(state.settlements)
            )
            fallback_count = latest.fallback_count if latest else len(
                [value for value in state.outcomes if value.baseline_fallback]
            )
            debited_tokens = latest.debited_tokens if latest else sum(
                value.debit_tokens for value in state.settlements
            )
            attempted = list(
                latest.attempted_fixture_ids
                if latest
                else tuple(value.fixture_id for value in state.attempts_started)
            )
            external_calls = latest.external_provider_calls if latest else 0
            pending_reservation = (
                state.reservations[-1]
                if len(state.reservations) == launched_count + 1
                else None
            )
        else:
            writer = R02D3AuditWriter(self.audit_root, self.authorization.run_id)
            writer.append_json("run_authorization", self.authorization)
            writer.append_json(
                "freeze_identity",
                {
                    "accepted_live_gate_freeze_sha256": (
                        self.authorization.accepted_live_gate_freeze_sha256
                    ),
                    "runner_readiness_freeze_sha256": (
                        self.authorization.runner_readiness_freeze_sha256
                    ),
                },
            )
            writer.append_json("run_plan", self.plan)
            reserved_count = launched_count = settled_count = fallback_count = 0
            debited_tokens = external_calls = 0
            attempted: list[str] = []
            pending_reservation = None

        for planned in self.plan.episodes[launched_count:]:
            episode = load_frame_episode(self.repository_root, planned.fixture_id)
            attempt_id = _attempt_id(self.authorization.run_id, planned)
            if attempt_id in {
                _attempt_id(self.authorization.run_id, value)
                for value in self.plan.episodes[:launched_count]
            }:
                raise R02D3OrchestratorError("duplicate provider call structurally blocked")
            preparation = prepare_provider_free_episode(
                episode,
                experiment_id=self.authorization.run_id,
                replicate_id=0,
                provider_attempt_count=launched_count,
            )
            request = build_selector_request(preparation)
            bound = R02D3BoundAttempt(
                authorization=self.authorization,
                preparation=preparation,
                attempt_id=attempt_id,
                provider_attempt_ordinal=launched_count + 1,
            )
            try:
                self.adapter.bind_attempt(bound)
                prompt_identity, _, _ = self.adapter.describe(request)
            except R02D3SelectorTransportError as exc:
                return self._terminalize_prelaunch_failure(
                    writer=writer,
                    planned=planned,
                    attempt_id=attempt_id,
                    failure=exc,
                    reserved_count=reserved_count,
                    launched_count=launched_count,
                    settled_count=settled_count,
                    fallback_count=fallback_count,
                    debited_tokens=debited_tokens,
                    attempted=tuple(attempted),
                    external_calls=external_calls,
                )

            if pending_reservation is None:
                if (reserved_count + 1) * R02_D3_ATTEMPT_RESERVE > R02_D3_FULL_TOKEN_CAP:
                    raise R02D3OrchestratorError("full token reservation cap exceeded")
                if planned.micro_pilot and (
                    (reserved_count + 1) * R02_D3_ATTEMPT_RESERVE > R02_D3_MICRO_TOKEN_CAP
                ):
                    raise R02D3OrchestratorError("micro token reservation cap exceeded")
                writer.append_json("episode_preparation", preparation)
                writer.append_json("prompt_identity", prompt_identity)
                reservation = R02D3TokenReservation(
                    run_id=self.authorization.run_id,
                    fixture_id=planned.fixture_id,
                    run_ordinal=planned.run_ordinal,
                    attempt_id=attempt_id,
                    provider_attempt_ordinal=launched_count + 1,
                    reserved_attempts_before=reserved_count,
                    reserved_tokens_before=reserved_count * R02_D3_ATTEMPT_RESERVE,
                    reserved_tokens_after=(reserved_count + 1) * R02_D3_ATTEMPT_RESERVE,
                )
                writer.append_json("token_reservation", reservation)
                reserved_count += 1
            else:
                reservation = pending_reservation
                pending_reservation = None
                if reservation.attempt_id != attempt_id:
                    raise R02D3OrchestratorError("unlaunched reservation is not the next episode")

            started = R02D3AttemptStarted(
                run_id=self.authorization.run_id,
                fixture_id=planned.fixture_id,
                attempt_id=attempt_id,
                provider_attempt_ordinal=launched_count + 1,
                reservation_sha256=canonical_sha256(reservation),
            )
            writer.append_json("attempt_started", started)
            launched_count += 1
            attempted.append(planned.fixture_id)
            try:
                raw_response, token_ledger, transport = self.adapter.select(request)
            except R02D3SelectorTransportError as exc:
                writer.append_bytes("raw_jsonl_transport", exc.capture.stdout, suffix="jsonl")
                writer.append_bytes("raw_stderr", exc.capture.stderr, suffix="bin")
                writer.append_json(
                    "transport_failure",
                    {
                        "attempt_id": attempt_id,
                        "code": exc.code,
                        "exit_code": exc.capture.exit_code,
                        "timed_out": exc.capture.timed_out,
                        "launch_error": exc.capture.launch_error,
                    },
                )
                settlement = R02D3TokenSettlement(
                    run_id=self.authorization.run_id,
                    fixture_id=planned.fixture_id,
                    attempt_id=attempt_id,
                    reservation_sha256=canonical_sha256(reservation),
                    settled=False,
                    debit_tokens=R02_D3_ATTEMPT_RESERVE,
                    failure_code=exc.code,
                )
                writer.append_json("token_settlement", settlement)
                debited_tokens += R02_D3_ATTEMPT_RESERVE
                decision = R02D3ContinuationDecision(
                    run_id=self.authorization.run_id,
                    after_attempts=launched_count,
                    action="HARD_STOP",
                    hard_stop_code=exc.code,
                    fallback_count=fallback_count,
                    unsettled_attempt_count=1,
                )
                writer.append_json("continuation_decision", decision)
                ledger = R02D3RunLedger(
                    run_id=self.authorization.run_id,
                    reserved_attempt_count=reserved_count,
                    launched_attempt_count=launched_count,
                    settled_attempt_count=settled_count,
                    unsettled_attempt_count=1,
                    fallback_count=fallback_count,
                    debited_tokens=debited_tokens,
                    attempted_fixture_ids=tuple(attempted),
                    status="HARD_STOP",
                    terminal_code=exc.code,
                    external_provider_calls=external_calls,
                )
                writer.append_json("run_ledger", ledger)
                writer.append_json("run_terminal", ledger)
                return ledger

            stdout = base64.b64decode(transport.stdout_base64)
            stderr = base64.b64decode(transport.stderr_base64)
            writer.append_bytes("raw_jsonl_transport", stdout, suffix="jsonl")
            writer.append_bytes("raw_stderr", stderr, suffix="bin")
            writer.append_json("transport_capture", transport)
            writer.append_json(
                "parsed_response",
                {
                    "attempt_id": attempt_id,
                    "raw_response": raw_response,
                    "raw_response_sha256": sha256_hex(raw_response.encode("utf-8")),
                    "token_ledger": token_ledger.model_dump(mode="json"),
                },
            )
            observed = token_ledger.accounting_total_tokens
            settlement = R02D3TokenSettlement(
                run_id=self.authorization.run_id,
                fixture_id=planned.fixture_id,
                attempt_id=attempt_id,
                reservation_sha256=canonical_sha256(reservation),
                settled=True,
                debit_tokens=observed,
                observed_total_tokens=observed,
                invalid_run_budget_breach=observed > R02_D3_ATTEMPT_RESERVE,
            )
            writer.append_json("token_settlement", settlement)
            settled_count += 1
            debited_tokens += observed
            external_calls += token_ledger.external_provider_calls
            if settlement.invalid_run_budget_breach or debited_tokens > R02_D3_FULL_TOKEN_CAP:
                decision = R02D3ContinuationDecision(
                    run_id=self.authorization.run_id,
                    after_attempts=launched_count,
                    action="HARD_STOP",
                    hard_stop_code="INVALID_RUN_BUDGET_BREACH",
                    fallback_count=fallback_count,
                    unsettled_attempt_count=0,
                )
                writer.append_json("continuation_decision", decision)
                ledger = R02D3RunLedger(
                    run_id=self.authorization.run_id,
                    reserved_attempt_count=reserved_count,
                    launched_attempt_count=launched_count,
                    settled_attempt_count=settled_count,
                    unsettled_attempt_count=0,
                    fallback_count=fallback_count,
                    debited_tokens=debited_tokens,
                    attempted_fixture_ids=tuple(attempted),
                    status="INVALID_RUN",
                    terminal_code="INVALID_RUN_BUDGET_BREACH",
                    external_provider_calls=external_calls,
                )
                writer.append_json("run_ledger", ledger)
                writer.append_json("run_terminal", ledger)
                return ledger

            outcome, execution, paired = _evaluate_selection(
                self.authorization,
                episode,
                preparation,
                attempt_id,
                raw_response,
            )
            writer.append_json("selector_outcome", outcome)
            writer.append_json("candidate_execution", execution)
            writer.append_json("paired_result", paired)
            if outcome.baseline_fallback:
                fallback_count += 1
            hard_stop_code = None
            if planned.micro_pilot and fallback_count > R02_D3_MICRO_FALLBACK_CAP:
                hard_stop_code = "MICRO_SELECTOR_FALLBACK_CAP_EXCEEDED"
            elif fallback_count > R02_D3_FULL_FAIL_CLOSED_CAP:
                hard_stop_code = "FULL_FAIL_CLOSED_ATTEMPT_CAP_EXCEEDED"
            action = (
                "HARD_STOP"
                if hard_stop_code
                else ("COMPLETE" if launched_count == R02_D3_FULL_ATTEMPTS else "CONTINUE")
            )
            decision = R02D3ContinuationDecision(
                run_id=self.authorization.run_id,
                after_attempts=launched_count,
                action=action,
                hard_stop_code=hard_stop_code,
                fallback_count=fallback_count,
                unsettled_attempt_count=0,
            )
            writer.append_json("continuation_decision", decision)
            status = "HARD_STOP" if hard_stop_code else (
                "COMPLETE" if launched_count == R02_D3_FULL_ATTEMPTS else "RUNNING"
            )
            ledger = R02D3RunLedger(
                run_id=self.authorization.run_id,
                reserved_attempt_count=reserved_count,
                launched_attempt_count=launched_count,
                settled_attempt_count=settled_count,
                unsettled_attempt_count=0,
                fallback_count=fallback_count,
                debited_tokens=debited_tokens,
                attempted_fixture_ids=tuple(attempted),
                status=status,
                terminal_code=hard_stop_code,
                external_provider_calls=external_calls,
            )
            writer.append_json("run_ledger", ledger)
            if status != "RUNNING":
                writer.append_json("run_terminal", ledger)
                return ledger
        raise R02D3OrchestratorError("orchestrator exhausted plan without terminal ledger")

    def _terminalize_prelaunch_failure(
        self,
        *,
        writer: R02D3AuditWriter,
        planned: R02D3PlannedEpisode,
        attempt_id: str,
        failure: R02D3SelectorTransportError,
        reserved_count: int,
        launched_count: int,
        settled_count: int,
        fallback_count: int,
        debited_tokens: int,
        attempted: tuple[str, ...],
        external_calls: int,
    ) -> R02D3RunLedger:
        writer.append_json(
            "prelaunch_failure",
            R02D3PrelaunchFailure(
                run_id=self.authorization.run_id,
                fixture_id=planned.fixture_id,
                attempt_id=attempt_id,
                code=failure.code,
                launch_error=failure.capture.launch_error,
            ),
        )
        ledger = R02D3RunLedger(
            run_id=self.authorization.run_id,
            reserved_attempt_count=reserved_count,
            launched_attempt_count=launched_count,
            settled_attempt_count=settled_count,
            unsettled_attempt_count=0,
            fallback_count=fallback_count,
            debited_tokens=debited_tokens,
            attempted_fixture_ids=attempted,
            status="HARD_STOP",
            terminal_code=failure.code,
            external_provider_calls=external_calls,
        )
        writer.append_json("run_ledger", ledger)
        writer.append_json("run_terminal", ledger)
        return ledger

    def _seal_crash_after_launch(self, writer, state, attempt_id: str) -> R02D3RunLedger:
        reservation = next(
            (value for value in state.reservations if value.attempt_id == attempt_id),
            None,
        )
        if reservation is None:
            raise R02D3OrchestratorError("unsettled launch has no reservation")
        latest = state.ledgers[-1] if state.ledgers else None
        launched = len(state.attempts_started)
        settled = len(state.settlements)
        attempted = tuple(value.fixture_id for value in state.attempts_started)
        fallback_count = latest.fallback_count if latest else len(state.outcomes)
        debit_before = latest.debited_tokens if latest else sum(
            value.debit_tokens for value in state.settlements
        )
        settlement = R02D3TokenSettlement(
            run_id=self.authorization.run_id,
            fixture_id=reservation.fixture_id,
            attempt_id=attempt_id,
            reservation_sha256=canonical_sha256(reservation),
            settled=False,
            debit_tokens=R02_D3_ATTEMPT_RESERVE,
            failure_code="CRASH_AFTER_LAUNCH_UNSETTLED",
        )
        writer.append_json("token_settlement", settlement)
        decision = R02D3ContinuationDecision(
            run_id=self.authorization.run_id,
            after_attempts=launched,
            action="HARD_STOP",
            hard_stop_code="CRASH_AFTER_LAUNCH_UNSETTLED",
            fallback_count=fallback_count,
            unsettled_attempt_count=1,
        )
        writer.append_json("continuation_decision", decision)
        ledger = R02D3RunLedger(
            run_id=self.authorization.run_id,
            reserved_attempt_count=len(state.reservations),
            launched_attempt_count=launched,
            settled_attempt_count=settled,
            unsettled_attempt_count=1,
            fallback_count=fallback_count,
            debited_tokens=debit_before + R02_D3_ATTEMPT_RESERVE,
            attempted_fixture_ids=attempted,
            status="HARD_STOP",
            terminal_code="CRASH_AFTER_LAUNCH_UNSETTLED",
            external_provider_calls=(
                (latest.external_provider_calls if latest else 0)
                + (1 if self.authorization.mode == "LIVE" else 0)
            ),
        )
        writer.append_json("run_ledger", ledger)
        writer.append_json("run_terminal", ledger)
        return ledger
