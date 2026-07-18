"""Typed contracts for the R02 D3 production runner readiness successor."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import ArtifactReference, StrictModel


R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256 = (
    "b650b8379d36292eaafd1d2df29f0f400df486da94d8c8e74f22348db2cd7b07"
)
R02_D3_ACCEPTED_PREFLIGHT_SHA256 = (
    "b1ec1eba58bedb959279af60067ff2d51610a9faa4c81ed9efb1146fcb73b529"
)
R02_D3_ACCEPTED_PREREGISTRATION_SHA256 = (
    "5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4"
)
R02_D3_EXPECTED_EXECUTABLE_SHA256 = (
    "cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4"
)
R02_D3_ATTEMPT_RESERVE = 32_000
R02_D3_MICRO_ATTEMPTS = 6
R02_D3_FULL_ATTEMPTS = 55
R02_D3_MICRO_TOKEN_CAP = 192_000
R02_D3_FULL_TOKEN_CAP = 1_760_000
R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT = (1 << 63) - 1
R02_D3_MAX_REPORTED_TOKENS_PER_RUN = (
    R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT * R02_D3_FULL_ATTEMPTS
)
R02_D3_MICRO_FALLBACK_CAP = 1
R02_D3_FULL_FAIL_CLOSED_CAP = 5


class R02D3RunnerSourcePin(StrictModel):
    role: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class R02D3LiveAuthorizationArtifact(StrictModel):
    """Canonical external approval artifact for one indivisible LIVE run."""

    schema_version: Literal["r02-d3-live-authorization-artifact-v1"] = (
        "r02-d3-live-authorization-artifact-v1"
    )
    authorization_id: str = Field(pattern=r"^r02-d3-live-auth-[a-z0-9-]{4,80}$")
    run_id: str = Field(pattern=r"^r02-d3-[a-z0-9-]{4,80}$")
    approved_scope: Literal["INDIVISIBLE_6_PLUS_49_LIVE"] = (
        "INDIVISIBLE_6_PLUS_49_LIVE"
    )
    accepted_live_gate_freeze_sha256: Literal[
        R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256
    ] = R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256
    runner_readiness_freeze_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_executable_sha256: Literal[R02_D3_EXPECTED_EXECUTABLE_SHA256] = (
        R02_D3_EXPECTED_EXECUTABLE_SHA256
    )
    indivisible_6_plus_49_approved: Literal[True] = True
    provider_calls_authorized: Literal[True] = True
    utility_outcomes_available_to_continuation_gate: Literal[False] = False


class R02D3RunAuthorization(StrictModel):
    """Run-local scope bound to external LIVE approval when applicable."""

    schema_version: Literal["r02-d3-run-authorization-v2"] = (
        "r02-d3-run-authorization-v2"
    )
    run_id: str = Field(pattern=r"^r02-d3-[a-z0-9-]{4,80}$")
    mode: Literal["OFFLINE_FAKE", "LIVE"]
    authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_live_gate_freeze_sha256: Literal[
        R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256
    ] = R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256
    runner_readiness_freeze_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    indivisible_6_plus_49_approved: bool
    provider_calls_authorized: bool
    utility_outcomes_available_to_continuation_gate: Literal[False] = False
    live_authorization_artifact: R02D3LiveAuthorizationArtifact | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "R02D3RunAuthorization":
        live_flags = (
            self.indivisible_6_plus_49_approved,
            self.provider_calls_authorized,
        )
        if self.mode == "LIVE":
            artifact = self.live_authorization_artifact
            if artifact is None:
                raise ValueError("live mode requires an external authorization artifact")
            if live_flags != (True, True):
                raise ValueError("live mode requires explicit indivisible 6+49 authorization")
            if (
                artifact.run_id != self.run_id
                or artifact.accepted_live_gate_freeze_sha256
                != self.accepted_live_gate_freeze_sha256
                or artifact.runner_readiness_freeze_sha256
                != self.runner_readiness_freeze_sha256
            ):
                raise ValueError("live authorization artifact identity mismatch")
        elif live_flags != (False, False):
            raise ValueError("offline fake mode cannot authorize provider calls")
        elif self.live_authorization_artifact is not None:
            raise ValueError("offline fake mode cannot carry a live authorization artifact")
        return self


class R02D3PlannedEpisode(StrictModel):
    run_ordinal: int = Field(ge=0, lt=R02_D3_FULL_ATTEMPTS)
    frame_ordinal: int = Field(ge=0, lt=160)
    fixture_id: str = Field(pattern=r"^development-[0-9]{4}$")
    stratum: Literal["REPRESENTATIVE", "CHALLENGE_HEADROOM"]
    candidate_count: Literal[2, 3, 4]
    micro_pilot: bool


class R02D3RunPlan(StrictModel):
    schema_version: Literal["r02-d3-run-plan-v1"] = "r02-d3-run-plan-v1"
    run_id: str
    episodes: tuple[R02D3PlannedEpisode, ...] = Field(
        min_length=R02_D3_FULL_ATTEMPTS,
        max_length=R02_D3_FULL_ATTEMPTS,
    )
    retry_attempt_cap: Literal[0] = 0
    replacement_cases_allowed: Literal[False] = False
    case_deletion_allowed: Literal[False] = False
    no_stop_action: Literal["CONTINUE_REMAINING_49_WITHOUT_SECOND_APPROVAL"] = (
        "CONTINUE_REMAINING_49_WITHOUT_SECOND_APPROVAL"
    )

    @model_validator(mode="after")
    def validate_plan(self) -> "R02D3RunPlan":
        if tuple(item.run_ordinal for item in self.episodes) != tuple(
            range(R02_D3_FULL_ATTEMPTS)
        ):
            raise ValueError("run ordinals must be contiguous")
        if len({item.fixture_id for item in self.episodes}) != R02_D3_FULL_ATTEMPTS:
            raise ValueError("planned fixtures must be unique")
        if tuple(item.micro_pilot for item in self.episodes[:6]) != (True,) * 6:
            raise ValueError("first six episodes must be the frozen micro-pilot")
        if any(item.micro_pilot for item in self.episodes[6:]):
            raise ValueError("only the first six episodes may be micro-pilot cases")
        remaining = tuple(item.frame_ordinal for item in self.episodes[6:])
        if remaining != tuple(sorted(remaining)):
            raise ValueError("remaining 49 episodes must follow frame order")
        return self


class R02D3PromptIdentity(StrictModel):
    schema_version: Literal["r02-d3-prompt-identity-v1"] = (
        "r02-d3-prompt-identity-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    selector_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    system_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    user_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdin_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    live_argv_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    requested_model_id: str


class R02D3TokenReservation(StrictModel):
    schema_version: Literal["r02-d3-token-reservation-v1"] = (
        "r02-d3-token-reservation-v1"
    )
    run_id: str
    fixture_id: str
    run_ordinal: int = Field(ge=0, lt=R02_D3_FULL_ATTEMPTS)
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_attempt_ordinal: int = Field(ge=1, le=R02_D3_FULL_ATTEMPTS)
    reserve_tokens: Literal[R02_D3_ATTEMPT_RESERVE] = R02_D3_ATTEMPT_RESERVE
    reserved_attempts_before: int = Field(ge=0, lt=R02_D3_FULL_ATTEMPTS)
    reserved_tokens_before: int = Field(ge=0, le=R02_D3_FULL_TOKEN_CAP)
    reserved_tokens_after: int = Field(ge=0, le=R02_D3_FULL_TOKEN_CAP)

    @model_validator(mode="after")
    def validate_reservation(self) -> "R02D3TokenReservation":
        if self.provider_attempt_ordinal != self.reserved_attempts_before + 1:
            raise ValueError("attempt reservation ordinal mismatch")
        if self.reserved_tokens_after != self.reserved_tokens_before + self.reserve_tokens:
            raise ValueError("token reservation arithmetic mismatch")
        return self


class R02D3AttemptStarted(StrictModel):
    schema_version: Literal["r02-d3-attempt-started-v1"] = (
        "r02-d3-attempt-started-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_attempt_ordinal: int = Field(ge=1, le=R02_D3_FULL_ATTEMPTS)
    reservation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    launch_may_have_occurred: Literal[True] = True


class R02D3PrelaunchFailure(StrictModel):
    schema_version: Literal["r02-d3-prelaunch-failure-v1"] = (
        "r02-d3-prelaunch-failure-v1"
    )
    run_id: str = Field(pattern=r"^r02-d3-[a-z0-9-]{4,80}$")
    fixture_id: str = Field(pattern=r"^development-[0-9]{4}$")
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    code: str = Field(min_length=1)
    launch_error: str | None = None


class R02D3LiveTokenLedger(StrictModel):
    schema_version: Literal["r02-d3-live-token-ledger-v1"] = (
        "r02-d3-live-token-ledger-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_attempt_ordinal: int = Field(ge=1, le=R02_D3_FULL_ATTEMPTS)
    input_tokens: int = Field(ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT)
    cached_input_tokens: int = Field(ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT)
    output_tokens: int = Field(ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT)
    reasoning_output_tokens: int = Field(ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT)
    accounting_total_tokens: int = Field(
        ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT
    )
    external_provider_calls: Literal[0, 1]

    @model_validator(mode="after")
    def validate_usage(self) -> "R02D3LiveTokenLedger":
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("cached input tokens exceed input tokens")
        if self.reasoning_output_tokens > self.output_tokens:
            raise ValueError("reasoning output tokens exceed output tokens")
        if self.accounting_total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("token accounting must be input plus output exactly once")
        return self


class R02D3LiveTransportRecord(StrictModel):
    schema_version: Literal["r02-d3-live-transport-v1"] = (
        "r02-d3-live-transport-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    selector_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_identity_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdout_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stderr_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stdout_base64: str
    stderr_base64: str
    exit_code: int | None
    timed_out: bool
    launch_error: str | None = None
    duration_ms: int = Field(ge=0)
    parsed_provider_response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    external_provider_calls: Literal[0, 1]


class R02D3TokenSettlement(StrictModel):
    schema_version: Literal["r02-d3-token-settlement-v1"] = (
        "r02-d3-token-settlement-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    reservation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    settled: bool
    debit_tokens: int = Field(ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT)
    observed_total_tokens: int | None = Field(
        default=None, ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_ATTEMPT
    )
    failure_code: str | None = None
    invalid_run_budget_breach: bool = False

    @model_validator(mode="after")
    def validate_settlement(self) -> "R02D3TokenSettlement":
        if self.settled:
            if self.observed_total_tokens is None or self.failure_code is not None:
                raise ValueError("settled usage requires observed tokens and no failure")
            if self.debit_tokens != self.observed_total_tokens:
                raise ValueError("settled debit must equal observed token total")
            if self.invalid_run_budget_breach != (
                self.observed_total_tokens > R02_D3_ATTEMPT_RESERVE
            ):
                raise ValueError("budget-breach label must match the observed usage")
        else:
            if self.debit_tokens != R02_D3_ATTEMPT_RESERVE or not self.failure_code:
                raise ValueError("unsettled attempt must debit the full reserve")
        return self


class R02D3SelectorOutcome(StrictModel):
    schema_version: Literal["r02-d3-selector-outcome-v1"] = (
        "r02-d3-selector-outcome-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_presented_id: str | None = None
    selected_canonical_id: str | None = None
    baseline_canonical_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    executed_canonical_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_fallback: bool
    error_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_outcome(self) -> "R02D3SelectorOutcome":
        if self.baseline_fallback:
            if self.executed_canonical_id != self.baseline_canonical_id:
                raise ValueError("fallback must execute the baseline")
            if not self.error_codes:
                raise ValueError("fallback requires typed error codes")
        elif self.executed_canonical_id != self.selected_canonical_id:
            raise ValueError("accepted selection identity mismatch")
        return self


class R02D3CandidateExecution(StrictModel):
    schema_version: Literal["r02-d3-candidate-execution-v1"] = (
        "r02-d3-candidate-execution-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    executed_canonical_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_fallback: bool


class R02D3PairedResult(StrictModel):
    schema_version: Literal["r02-d3-paired-result-v1"] = (
        "r02-d3-paired-result-v1"
    )
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_utility_e12: int
    executed_utility_e12: int
    paired_utility_delta_e12: int
    baseline_fallback: bool

    @model_validator(mode="after")
    def validate_delta(self) -> "R02D3PairedResult":
        if self.paired_utility_delta_e12 != (
            self.executed_utility_e12 - self.baseline_utility_e12
        ):
            raise ValueError("paired utility delta arithmetic mismatch")
        if self.baseline_fallback and self.paired_utility_delta_e12 != 0:
            raise ValueError("baseline fallback delta must be zero")
        return self


class R02D3ContinuationDecision(StrictModel):
    schema_version: Literal["r02-d3-continuation-decision-v1"] = (
        "r02-d3-continuation-decision-v1"
    )
    run_id: str
    after_attempts: int = Field(ge=1, le=R02_D3_FULL_ATTEMPTS)
    action: Literal["CONTINUE", "COMPLETE", "HARD_STOP"]
    hard_stop_code: str | None = None
    fallback_count: int = Field(ge=0)
    unsettled_attempt_count: int = Field(ge=0)
    utility_outcomes_consulted: Literal[False] = False
    second_authorization_requested: Literal[False] = False

    @model_validator(mode="after")
    def validate_decision(self) -> "R02D3ContinuationDecision":
        if (self.action == "HARD_STOP") != (self.hard_stop_code is not None):
            raise ValueError("hard-stop action and code must be paired")
        if self.action == "COMPLETE" and self.after_attempts != R02_D3_FULL_ATTEMPTS:
            raise ValueError("completion requires all 55 ITT attempts")
        return self


class R02D3RunLedger(StrictModel):
    schema_version: Literal["r02-d3-run-ledger-v1"] = "r02-d3-run-ledger-v1"
    run_id: str
    planned_episode_count: Literal[R02_D3_FULL_ATTEMPTS] = R02_D3_FULL_ATTEMPTS
    reserved_attempt_count: int = Field(ge=0, le=R02_D3_FULL_ATTEMPTS)
    launched_attempt_count: int = Field(ge=0, le=R02_D3_FULL_ATTEMPTS)
    settled_attempt_count: int = Field(ge=0, le=R02_D3_FULL_ATTEMPTS)
    unsettled_attempt_count: int = Field(ge=0, le=R02_D3_FULL_ATTEMPTS)
    fallback_count: int = Field(ge=0, le=R02_D3_FULL_ATTEMPTS)
    debited_tokens: int = Field(ge=0, le=R02_D3_MAX_REPORTED_TOKENS_PER_RUN)
    attempted_fixture_ids: tuple[str, ...]
    status: Literal["RUNNING", "COMPLETE", "HARD_STOP", "INVALID_RUN"]
    terminal_code: str | None = None
    external_provider_calls: int = Field(ge=0, le=R02_D3_FULL_ATTEMPTS)

    @model_validator(mode="after")
    def validate_ledger(self) -> "R02D3RunLedger":
        if self.launched_attempt_count != len(self.attempted_fixture_ids):
            raise ValueError("ITT attempted fixture ledger mismatch")
        if len(set(self.attempted_fixture_ids)) != len(self.attempted_fixture_ids):
            raise ValueError("duplicate attempted fixture identity")
        if self.settled_attempt_count + self.unsettled_attempt_count != self.launched_attempt_count:
            raise ValueError("attempt settlement counts do not reconcile")
        if self.status in ("HARD_STOP", "INVALID_RUN") and not self.terminal_code:
            raise ValueError("terminal failure requires a code")
        if self.status in ("RUNNING", "COMPLETE") and self.terminal_code is not None:
            raise ValueError("non-failure status cannot carry a terminal code")
        return self


class R02D3AuditNode(StrictModel):
    schema_version: Literal["r02-d3-audit-node-v1"] = "r02-d3-audit-node-v1"
    run_id: str
    sequence: int = Field(ge=1)
    node_type: str = Field(pattern=r"^[a-z][a-z0-9_]{2,80}$")
    previous_node_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    payload: ArtifactReference


class R02D3AuditAnchor(StrictModel):
    schema_version: Literal["r02-d3-audit-anchor-v1"] = "r02-d3-audit-anchor-v1"
    run_id: str
    sequence: int = Field(ge=1)
    node_types: tuple[str, ...]
    nodes: tuple[ArtifactReference, ...]
    head_node_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_anchor(self) -> "R02D3AuditAnchor":
        if self.sequence != len(self.nodes) or len(self.node_types) != len(self.nodes):
            raise ValueError("audit anchor sequence mismatch")
        if self.nodes[-1].sha256 != self.head_node_sha256:
            raise ValueError("audit anchor head mismatch")
        return self


class R02D3RunnerReadinessFreeze(StrictModel):
    schema_version: Literal["r02-d3-runner-readiness-freeze-v1"] = (
        "r02-d3-runner-readiness-freeze-v1"
    )
    authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_live_gate_freeze_sha256: Literal[
        R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256
    ] = R02_D3_ACCEPTED_LIVE_GATE_FREEZE_SHA256
    accepted_preflight_sha256: Literal[R02_D3_ACCEPTED_PREFLIGHT_SHA256] = (
        R02_D3_ACCEPTED_PREFLIGHT_SHA256
    )
    expected_executable_sha256: Literal[R02_D3_EXPECTED_EXECUTABLE_SHA256] = (
        R02_D3_EXPECTED_EXECUTABLE_SHA256
    )
    output_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_contract_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_identity_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_pins: tuple[R02D3RunnerSourcePin, ...] = Field(min_length=6)
    zero_call_allowed_command_labels: tuple[str, ...]
    live_argv_allowed_by_zero_call: Literal[False] = False
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    micro_pilot_executed: Literal[False] = False
    full_6_plus_49_executed: Literal[False] = False
    status: Literal["READY_FOR_INDEPENDENT_REVIEW_NOT_LIVE_AUTHORIZED"] = (
        "READY_FOR_INDEPENDENT_REVIEW_NOT_LIVE_AUTHORIZED"
    )


class R02D3ReadinessReplayVerification(StrictModel):
    schema_version: Literal["r02-d3-readiness-replay-v1"] = (
        "r02-d3-readiness-replay-v1"
    )
    freeze_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verified_source_pins: int = Field(ge=6)
    output_schema_matches: Literal[True] = True
    accepted_live_gate_matches: Literal[True] = True
    executable_pin_matches: Literal[True] = True
    zero_call_allowlist_excludes_live_argv: Literal[True] = True
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
