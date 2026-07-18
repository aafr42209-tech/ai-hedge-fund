"""Provider-free R02 D4-S6 state machine with an injected transport boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from .baselines import primary_deterministic
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import ASSET_IDS, Decision, DecisionBatch, SyntheticEpisode
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_candidates import canonical_candidate_id, prepare_provider_free_episode
from .r02_contracts import (
    R02CandidateBatch,
    R02ProviderFreePreparation,
    R02SelectorRequest,
)
from .r02_d4_s2a_frame import DEFAULT_R02_D4_S2A_ARTIFACT_ROOT, R02D4S2AFrameManifest
from .r02_d4_s5_live_gate import (
    build_execution_plan,
    R02_D4_S5_EXECUTION_PLAN_SHA256,
    verify_live_gate_freeze,
)
from .r02_d4_s6_audit import R02D4S6AuditError, R02D4S6AuditWriter
from .r02_d4_s6_contracts import (
    R02_D4_S6_ATTEMPT_CAP,
    R02_D4_S6_FAIL_CLOSED_CAP,
    R02_D4_S6_FRAME_MANIFEST_SHA256,
    R02_D4_S6_HARD_STOP_CONDITIONS,
    R02_D4_S6_S5_FREEZE_SHA256,
    R02_D4_S6_TIMEOUT_MS,
    R02_D4_S6_TOKEN_CAP,
    R02_D4_S6_TOKEN_RESERVE,
    R02D4S6AttemptOutcome,
    R02D4S6AttemptStarted,
    R02D4S6AuditAnchor,
    R02D4S6ContinuationDecision,
    R02D4S6ContractBinding,
    R02D4S6LiveAuthorizationArtifact,
    R02D4S6PlannedAttempt,
    R02D4S6RunAuthorization,
    R02D4S6RunLedger,
    R02D4S6RunPlan,
    R02D4S6RunTerminal,
    R02D4S6TokenReservation,
    R02D4S6TransportResult,
)
from .r02_selector import (
    build_selector_request,
    parse_selector_response,
    R02SelectorParseError,
)
from .scoring import score_episode
from .validator import validate_batch


class R02D4S6RunnerError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class R02D4S6Transport(Protocol):
    r02_d4_s6_execution_capability: Literal["OFFLINE_FAKE", "LIVE_PROVIDER_PROCESS"]

    def execute(
        self,
        *,
        run_id: str,
        attempt_id: str,
        attempt: R02D4S6PlannedAttempt,
        selector_request: R02SelectorRequest,
        timeout_ms: int,
    ) -> R02D4S6TransportResult:
        ...


@dataclass(frozen=True)
class R02D4S6PreparedAttempt:
    planned: R02D4S6PlannedAttempt
    episode: SyntheticEpisode
    preparation: R02ProviderFreePreparation
    selector_request: R02SelectorRequest


@dataclass(frozen=True)
class R02D4S6PreparedRun:
    plan: R02D4S6RunPlan
    attempts: tuple[R02D4S6PreparedAttempt, ...]


@dataclass(frozen=True)
class R02D4S6RunResult:
    terminal: R02D4S6RunTerminal
    terminal_anchor: R02D4S6AuditAnchor
    audit_root: Path


def _read_json_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R02D4S6RunnerError(
            "TRUST_ANCHOR_PROTECTED_TREE_OR_SOURCE_PIN_DRIFT",
            f"expected JSON object: {path}",
        )
    return value


def verify_s5_contract(repository_root: str | Path) -> dict[str, object]:
    repo = Path(repository_root).resolve()
    freeze_path = repo / "docs/r02-d4-s5-live-gate-freeze.json"
    if sha256_hex(freeze_path.read_bytes()) != R02_D4_S6_S5_FREEZE_SHA256:
        raise R02D4S6RunnerError("TRUST_ANCHOR_PROTECTED_TREE_OR_SOURCE_PIN_DRIFT", "S5 freeze byte drift")
    freeze = _read_json_object(freeze_path)
    try:
        verify_live_gate_freeze(repo, freeze)
    except Exception as exc:
        raise R02D4S6RunnerError(
            "TRUST_ANCHOR_PROTECTED_TREE_OR_SOURCE_PIN_DRIFT",
            f"S5 contract verification failed: {exc}",
        ) from exc
    return freeze


def verify_external_live_authorization(
    authorization: R02D4S6RunAuthorization,
    artifact_path: str | Path | None,
) -> None:
    if authorization.mode == "OFFLINE_FAKE":
        if artifact_path is not None:
            raise R02D4S6RunnerError(
                "MISSING_SEPARATE_LIVE_AUTHORIZATION",
                "offline fake mode cannot accept a LIVE authorization path",
            )
        return
    if artifact_path is None:
        raise R02D4S6RunnerError(
            "MISSING_SEPARATE_LIVE_AUTHORIZATION",
            "LIVE mode requires a separate external authorization file",
        )
    path = Path(artifact_path).resolve()
    try:
        raw = path.read_bytes()
        artifact = R02D4S6LiveAuthorizationArtifact.model_validate_json(raw)
    except Exception as exc:
        raise R02D4S6RunnerError(
            "MISSING_SEPARATE_LIVE_AUTHORIZATION",
            f"LIVE authorization file is missing or invalid: {exc}",
        ) from exc
    if raw != canonical_json_bytes(artifact):
        raise R02D4S6RunnerError(
            "MISSING_SEPARATE_LIVE_AUTHORIZATION",
            "LIVE authorization file is not canonical JSON",
        )
    if authorization.live_authorization_artifact is None or canonical_sha256(artifact) != canonical_sha256(authorization.live_authorization_artifact):
        raise R02D4S6RunnerError(
            "MISSING_SEPARATE_LIVE_AUTHORIZATION",
            "LIVE authorization file differs from the bound run authorization",
        )


def verify_prepared_run(prepared_run: R02D4S6PreparedRun) -> None:
    if len(prepared_run.attempts) != R02_D4_S6_ATTEMPT_CAP:
        raise R02D4S6RunnerError(
            "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
            "prepared attempt count drift",
        )
    if tuple(item.planned for item in prepared_run.attempts) != prepared_run.plan.attempts:
        raise R02D4S6RunnerError(
            "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
            "prepared attempt order differs from the frozen plan",
        )
    for item in prepared_run.attempts:
        if canonical_sha256(item.episode) != item.planned.fixture_sha256 or canonical_sha256(item.preparation) != item.planned.preparation_sha256 or canonical_sha256(item.selector_request) != item.planned.selector_request_sha256:
            raise R02D4S6RunnerError(
                "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
                f"prepared attempt digest drift: {item.planned.fixture_id}",
            )


def build_provider_free_run_plan(repository_root: str | Path) -> R02D4S6PreparedRun:
    """Read the sealed S2A input; never writes the production artifact tree."""

    repo = Path(repository_root).resolve()
    verify_s5_contract(repo)
    manifest_path = repo / "docs/r02-d4-s2a-frame-manifest.json"
    if sha256_hex(manifest_path.read_bytes()) != R02_D4_S6_FRAME_MANIFEST_SHA256:
        raise R02D4S6RunnerError(
            "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
            "S2A frame manifest byte drift",
        )
    manifest = R02D4S2AFrameManifest.model_validate_json(manifest_path.read_bytes())
    raw_manifest = _read_json_object(manifest_path)
    frozen_rows = build_execution_plan(raw_manifest)
    if canonical_sha256(frozen_rows) != R02_D4_S5_EXECUTION_PLAN_SHA256:
        raise R02D4S6RunnerError(
            "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
            "S5 execution plan digest drift",
        )
    input_root = (repo / ".research_artifacts/r02-d4-s2a-frame-0716a1b9c13a").resolve()
    if input_root != DEFAULT_R02_D4_S2A_ARTIFACT_ROOT.resolve():
        raise R02D4S6RunnerError(
            "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
            "sealed frame input root drift",
        )
    store = R02AppendOnlyArtifactStore(input_root)
    cases = {case.frame_ordinal: case for case in manifest.cases}
    prepared: list[R02D4S6PreparedAttempt] = []
    planned: list[R02D4S6PlannedAttempt] = []
    for row in frozen_rows:
        frame_ordinal = int(row["frame_ordinal"])
        case = cases[frame_ordinal]
        episode_bytes = store.read_bytes(case.fixture_artifact)
        episode = SyntheticEpisode.model_validate_json(episode_bytes)
        preparation = prepare_provider_free_episode(
            episode,
            experiment_id=manifest.frame_id,
            provider_attempt_count=0,
        )
        if preparation.candidate_set is None or preparation.permutation is None:
            raise R02D4S6RunnerError(
                "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
                f"eligible fixture is not selector-ready: {case.fixture_id}",
            )
        request = build_selector_request(preparation)
        item = R02D4S6PlannedAttempt(
            execution_ordinal=int(row["execution_ordinal"]),
            frame_ordinal=frame_ordinal,
            fixture_id=str(row["fixture_id"]),
            stratum=str(row["stratum"]),
            candidate_count=int(row["candidate_count"]),
            fixture_artifact=case.fixture_artifact,
            fixture_sha256=sha256_hex(episode_bytes),
            preparation_sha256=canonical_sha256(preparation),
            selector_request_sha256=canonical_sha256(request),
        )
        if item.fixture_sha256 != str(row["fixture_sha256"]):
            raise R02D4S6RunnerError(
                "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
                f"fixture digest drift: {item.fixture_id}",
            )
        planned.append(item)
        prepared.append(
            R02D4S6PreparedAttempt(
                planned=item,
                episode=episode,
                preparation=preparation,
                selector_request=request,
            )
        )
    plan = R02D4S6RunPlan(attempts=tuple(planned))
    return R02D4S6PreparedRun(plan=plan, attempts=tuple(prepared))


def _validation_batch(candidate: R02CandidateBatch) -> DecisionBatch:
    return DecisionBatch(
        decisions={
            asset_id: Decision(
                action=candidate.decisions[asset_id].action,
                quantity=candidate.decisions[asset_id].quantity,
                confidence=100,
                reasoning="r02:d4-s6-acceptance-gate",
            )
            for asset_id in ASSET_IDS
        }
    )


def _semantic_match(candidate: R02CandidateBatch, validation) -> bool:
    return all(candidate.decisions[asset_id].action == validation.executable.decisions[asset_id].action and candidate.decisions[asset_id].quantity == validation.executable.decisions[asset_id].quantity for asset_id in ASSET_IDS)


def _evaluate_settled_response(
    *,
    run_id: str,
    attempt_id: str,
    prepared: R02D4S6PreparedAttempt,
    raw_response: str,
    observed_total_tokens: int,
) -> R02D4S6AttemptOutcome:
    preparation = prepared.preparation
    episode = prepared.episode
    if preparation.candidate_set is None or preparation.permutation is None:
        raise R02D4S6RunnerError(
            "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
            "eligible preparation lacks candidates or permutation",
        )
    baseline = primary_deterministic(episode)
    if not baseline.validation.raw_valid or baseline.validation.fell_back:
        raise R02D4S6RunnerError(
            "TRUST_ANCHOR_PROTECTED_TREE_OR_SOURCE_PIN_DRIFT",
            "deterministic baseline is not executable",
        )
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
        raise R02D4S6RunnerError(
            "TRUST_ANCHOR_PROTECTED_TREE_OR_SOURCE_PIN_DRIFT",
            "primary baseline identity drift",
        )

    selected_presented_id: str | None = None
    selected_canonical_id: str | None = None
    selected_candidate = None
    selected_validation = None
    error_codes: tuple[str, ...] = ()
    try:
        parsed = parse_selector_response(raw_response)
        decoded = json.loads(raw_response)
        if "schema_version" not in decoded:
            raise R02SelectorParseError("SCHEMA:schema_version:missing")
        selected_presented_id = parsed.selected_candidate_id
        selected_canonical_id = preparation.permutation.presented_to_canonical_map.get(selected_presented_id)
        selected_candidate = next(
            (candidate for candidate in preparation.candidate_set.candidates if candidate.canonical_candidate_id == selected_canonical_id),
            None,
        )
        if selected_candidate is None:
            error_codes = ("UNKNOWN_PRESENTED_ID",)
        else:
            selected_validation = validate_batch(
                episode.public,
                _validation_batch(selected_candidate.candidate),
            )
            if not selected_validation.raw_valid or selected_validation.fell_back or not _semantic_match(selected_candidate.candidate, selected_validation):
                error_codes = ("ACCEPTANCE_VALIDATION_FAILED",)
    except (R02SelectorParseError, json.JSONDecodeError, TypeError) as exc:
        error_codes = tuple(exc.codes) if isinstance(exc, R02SelectorParseError) else ("SCHEMA:raw_response:invalid",)

    fallback = bool(error_codes)
    if fallback:
        executed_id = baseline_id
        executed_validation = baseline.validation
    else:
        if selected_candidate is None or selected_validation is None:
            raise R02D4S6RunnerError(
                "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
                "accepted selector outcome lacks executable validation",
            )
        executed_id = selected_candidate.canonical_candidate_id
        executed_validation = selected_validation
    executed_score = score_episode(episode, executed_validation)
    return R02D4S6AttemptOutcome(
        run_id=run_id,
        fixture_id=prepared.planned.fixture_id,
        attempt_id=attempt_id,
        status="SETTLED_FAIL_CLOSED" if fallback else "SETTLED_ACCEPTED",
        settled=True,
        debit_tokens=observed_total_tokens,
        observed_total_tokens=observed_total_tokens,
        selected_presented_id=selected_presented_id,
        selected_canonical_id=selected_canonical_id,
        baseline_canonical_id=baseline_id,
        executed_canonical_id=executed_id,
        baseline_fallback=fallback,
        error_codes=error_codes,
        baseline_utility_e12=baseline.score.utility_e12,
        executed_utility_e12=executed_score.utility_e12,
        paired_utility_delta_e12=(executed_score.utility_e12 - baseline.score.utility_e12),
    )


def _attempt_id(run_id: str, planned: R02D4S6PlannedAttempt) -> str:
    return canonical_sha256(
        {
            "domain": "r02-d4-s6-provider-attempt-v1",
            "run_id": run_id,
            "execution_ordinal": planned.execution_ordinal,
            "frame_ordinal": planned.frame_ordinal,
            "fixture_id": planned.fixture_id,
        }
    )


def _transport_failure_result(
    *,
    run_id: str,
    fixture_id: str,
    attempt_id: str,
    external_provider_calls: int,
    error: Exception,
) -> R02D4S6TransportResult:
    return R02D4S6TransportResult(
        run_id=run_id,
        fixture_id=fixture_id,
        attempt_id=attempt_id,
        raw_response=None,
        raw_response_sha256=canonical_sha256({"raw_response": None}),
        terminal_usage_event_count=0,
        exit_code=None,
        timed_out=False,
        launch_error=f"{type(error).__name__}:{error}",
        duration_ms=0,
        external_provider_calls=external_provider_calls,
    )


def _usage_status(result: R02D4S6TransportResult) -> tuple[str | None, int | None]:
    values = (
        result.input_tokens,
        result.cached_input_tokens,
        result.output_tokens,
        result.reasoning_output_tokens,
    )
    if result.timed_out or result.exit_code != 0 or result.launch_error is not None or result.terminal_usage_event_count != 1 or any(value is None for value in values) or result.raw_response is None:
        return (
            "TRANSPORT_TIMEOUT_NONZERO_EXIT_MISSING_USAGE_OR_UNSETTLED_ATTEMPT",
            None,
        )
    input_tokens, cached_tokens, output_tokens, reasoning_tokens = values
    assert input_tokens is not None
    assert cached_tokens is not None
    assert output_tokens is not None
    assert reasoning_tokens is not None
    if cached_tokens > input_tokens or reasoning_tokens > output_tokens:
        return (
            "TRANSPORT_TIMEOUT_NONZERO_EXIT_MISSING_USAGE_OR_UNSETTLED_ATTEMPT",
            None,
        )
    total = input_tokens + output_tokens
    if total > R02_D4_S6_TOKEN_RESERVE:
        return "REPORTED_USAGE_OVER_32000_TOKEN_RESERVE", total
    return None, total


class R02D4S6Runner:
    def __init__(
        self,
        *,
        repository_root: str | Path,
        audit_root: str | Path,
        authorization: R02D4S6RunAuthorization,
        transport: R02D4S6Transport,
        prepared_run: R02D4S6PreparedRun | None = None,
        external_live_authorization_path: str | Path | None = None,
    ) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.authorization = authorization
        self.transport = transport
        verify_external_live_authorization(authorization, external_live_authorization_path)
        if prepared_run is None:
            self.prepared_run = build_provider_free_run_plan(self.repository_root)
        else:
            verify_s5_contract(self.repository_root)
            self.prepared_run = prepared_run
        verify_prepared_run(self.prepared_run)
        expected_capability = "LIVE_PROVIDER_PROCESS" if authorization.mode == "LIVE" else "OFFLINE_FAKE"
        if getattr(transport, "r02_d4_s6_execution_capability", None) != expected_capability:
            raise R02D4S6RunnerError(
                "PROMPT_OUTPUT_SCHEMA_MODEL_PROVIDER_EXECUTABLE_FEATURE_OR_COMMAND_DRIFT",
                "transport capability does not match the run authorization",
            )
        self.audit = R02D4S6AuditWriter(
            audit_root,
            run_id=authorization.run_id,
            repository_root=self.repository_root,
            authorization=authorization,
        )

    def _append(self, node_type: str, value: object) -> None:
        try:
            self.audit.append_json(node_type, value)
        except Exception as exc:
            raise R02D4S6RunnerError(
                "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
                f"audit append failed at {node_type}: {exc}",
            ) from exc

    def run(self) -> R02D4S6RunResult:
        authorization = self.authorization
        plan = self.prepared_run.plan
        if len(self.prepared_run.attempts) != R02_D4_S6_ATTEMPT_CAP:
            raise R02D4S6RunnerError(
                "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
                "prepared attempt count drift",
            )
        binding = R02D4S6ContractBinding()
        self._append("run_authorization", authorization)
        self._append("contract_binding", binding)
        self._append("run_plan", plan)

        reserved_attempts = 0
        reserved_tokens = 0
        launched_attempts = 0
        settled_attempts = 0
        unsettled_attempts = 0
        settled_fail_closed = 0
        debited_tokens = 0
        attempted_fixture_ids: list[str] = []
        external_provider_calls = 0
        final_ledger: R02D4S6RunLedger | None = None

        for prepared in self.prepared_run.attempts:
            planned = prepared.planned
            if reserved_attempts + 1 > R02_D4_S6_ATTEMPT_CAP or reserved_tokens + R02_D4_S6_TOKEN_RESERVE > R02_D4_S6_TOKEN_CAP:
                raise R02D4S6RunnerError(
                    "ATTEMPT_OR_TOKEN_BUDGET_WOULD_BE_EXCEEDED",
                    "full attempt reservation does not fit before launch",
                )
            attempt_id = _attempt_id(authorization.run_id, planned)
            reservation = R02D4S6TokenReservation(
                run_id=authorization.run_id,
                fixture_id=planned.fixture_id,
                execution_ordinal=planned.execution_ordinal,
                attempt_id=attempt_id,
                provider_attempt_ordinal=reserved_attempts + 1,
                reserved_attempts_before=reserved_attempts,
                reserved_tokens_before=reserved_tokens,
                reserved_tokens_after=reserved_tokens + R02_D4_S6_TOKEN_RESERVE,
            )
            self._append("token_reservation", reservation)
            reserved_attempts += 1
            reserved_tokens += R02_D4_S6_TOKEN_RESERVE
            started = R02D4S6AttemptStarted(
                run_id=authorization.run_id,
                fixture_id=planned.fixture_id,
                attempt_id=attempt_id,
                provider_attempt_ordinal=reserved_attempts,
                reservation_sha256=canonical_sha256(reservation),
            )
            self._append("attempt_started", started)
            launched_attempts += 1
            attempted_fixture_ids.append(planned.fixture_id)
            expected_external_calls = 1 if authorization.mode == "LIVE" else 0
            try:
                transport_result = self.transport.execute(
                    run_id=authorization.run_id,
                    attempt_id=attempt_id,
                    attempt=planned,
                    selector_request=prepared.selector_request,
                    timeout_ms=R02_D4_S6_TIMEOUT_MS,
                )
            except Exception as exc:
                transport_result = _transport_failure_result(
                    run_id=authorization.run_id,
                    fixture_id=planned.fixture_id,
                    attempt_id=attempt_id,
                    external_provider_calls=expected_external_calls,
                    error=exc,
                )
            if transport_result.run_id != authorization.run_id or transport_result.fixture_id != planned.fixture_id or transport_result.attempt_id != attempt_id or transport_result.external_provider_calls != expected_external_calls:
                transport_result = _transport_failure_result(
                    run_id=authorization.run_id,
                    fixture_id=planned.fixture_id,
                    attempt_id=attempt_id,
                    external_provider_calls=expected_external_calls,
                    error=R02D4S6RunnerError(
                        "PROMPT_OUTPUT_SCHEMA_MODEL_PROVIDER_EXECUTABLE_FEATURE_OR_COMMAND_DRIFT",
                        "transport result identity or call accounting drift",
                    ),
                )
            external_provider_calls += transport_result.external_provider_calls
            self._append("transport_result", transport_result)

            hard_stop_code, observed_total = _usage_status(transport_result)
            if hard_stop_code is not None:
                outcome = R02D4S6AttemptOutcome(
                    run_id=authorization.run_id,
                    fixture_id=planned.fixture_id,
                    attempt_id=attempt_id,
                    status=("INVALID_BUDGET_HARD_STOP" if hard_stop_code == "REPORTED_USAGE_OVER_32000_TOKEN_RESERVE" else "UNSETTLED_HARD_STOP"),
                    settled=False,
                    debit_tokens=R02_D4_S6_TOKEN_RESERVE,
                    observed_total_tokens=observed_total,
                    baseline_fallback=False,
                    error_codes=(hard_stop_code,),
                )
                unsettled_attempts += 1
                debited_tokens += R02_D4_S6_TOKEN_RESERVE
            else:
                assert observed_total is not None
                assert transport_result.raw_response is not None
                outcome = _evaluate_settled_response(
                    run_id=authorization.run_id,
                    attempt_id=attempt_id,
                    prepared=prepared,
                    raw_response=transport_result.raw_response,
                    observed_total_tokens=observed_total,
                )
                settled_attempts += 1
                debited_tokens += observed_total
                if outcome.baseline_fallback:
                    settled_fail_closed += 1
                    if settled_fail_closed > R02_D4_S6_FAIL_CLOSED_CAP:
                        hard_stop_code = "SETTLED_FAIL_CLOSED_COUNT_WOULD_EXCEED_6"
            self._append("attempt_outcome", outcome)

            if debited_tokens > R02_D4_S6_TOKEN_CAP:
                hard_stop_code = "ATTEMPT_OR_TOKEN_BUDGET_WOULD_BE_EXCEEDED"
            if hard_stop_code is not None:
                action = "HARD_STOP"
                status = "INVALID_RUN"
            elif launched_attempts == R02_D4_S6_ATTEMPT_CAP:
                action = "COMPLETE"
                status = "COMPLETE"
            else:
                action = "CONTINUE"
                status = "RUNNING"
            decision = R02D4S6ContinuationDecision(
                run_id=authorization.run_id,
                after_attempts=launched_attempts,
                action=action,
                hard_stop_code=hard_stop_code,
                settled_fail_closed_count=settled_fail_closed,
                unsettled_attempt_count=unsettled_attempts,
            )
            self._append("continuation_decision", decision)
            ledger = R02D4S6RunLedger(
                run_id=authorization.run_id,
                reserved_attempt_count=reserved_attempts,
                reserved_tokens=reserved_tokens,
                launched_attempt_count=launched_attempts,
                settled_attempt_count=settled_attempts,
                unsettled_attempt_count=unsettled_attempts,
                settled_fail_closed_count=settled_fail_closed,
                debited_tokens=debited_tokens,
                attempted_fixture_ids=tuple(attempted_fixture_ids),
                status=status,
                terminal_code=hard_stop_code,
                transport_invocations=launched_attempts,
                external_provider_calls=external_provider_calls,
            )
            self._append("run_ledger", ledger)
            final_ledger = ledger
            if action != "CONTINUE":
                break

        if final_ledger is None or final_ledger.status == "RUNNING":
            raise R02D4S6RunnerError(
                "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
                "runner exited without a terminal ledger",
            )
        terminal = R02D4S6RunTerminal(
            run_id=authorization.run_id,
            authorization_sha256=canonical_sha256(authorization),
            contract_binding_sha256=canonical_sha256(binding),
            run_plan_sha256=canonical_sha256(plan),
            final_ledger=final_ledger,
            terminal_status=final_ledger.status,
        )
        self._append("run_terminal", terminal)
        if self.audit.latest_anchor is None:
            raise R02D4S6RunnerError("AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE", "terminal anchor is missing")

        from .r02_d4_s6_replay import replay_s6_audit_root

        try:
            replay = replay_s6_audit_root(
                self.audit.root,
                repository_root=self.repository_root,
                expected_authorization=authorization,
                expected_plan=plan,
                expected_prepared_run=self.prepared_run,
            )
        except Exception as exc:
            raise R02D4S6RunnerError(
                "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
                f"terminal replay failed: {exc}",
            ) from exc
        if canonical_sha256(replay.terminal) != canonical_sha256(terminal):
            raise R02D4S6RunnerError(
                "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
                "terminal replay is not byte-exact",
            )
        return R02D4S6RunResult(
            terminal=terminal,
            terminal_anchor=self.audit.latest_anchor,
            audit_root=self.audit.root,
        )
