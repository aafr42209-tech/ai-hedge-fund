"""Strict provider-free contracts for the R02 D4-S6 runner and audit chain."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .canonical import canonical_sha256
from .contracts import ArtifactReference, StrictModel
from .r02_d4_s5_live_gate import (
    R02_D4_S5_AGGREGATE_TOKEN_CAP,
    R02_D4_S5_ELIGIBLE_COUNT,
    R02_D4_S5_ELIGIBLE_FRAME_ORDINALS,
    R02_D4_S5_EXECUTION_PLAN_SHA256,
    R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP,
    R02_D4_S5_FRAME_ID,
    R02_D4_S5_LIVE_TIMEOUT_MS,
    R02_D4_S5_PER_ATTEMPT_TOKEN_RESERVE,
)

R02_D4_S6_BASE_COMMIT = "bf8c293ab656be915b34c392133d77f3b8e748b2"
R02_D4_S6_S5_FREEZE_SHA256 = "d931edfaa347165975a0edcff1a256f81cd7d56fc7268d7a2a19bf97379f50ab"
R02_D4_S6_S5_IDENTITY_SNAPSHOT_SHA256 = "248f3683db276d45f275b5a2c236bc02909f6b7bf1be4ff56f6886573b2df5dc"
R02_D4_S6_S4_BUDGET_SHA256 = "722eb1aee9e115c76990387f7baf8a19dbfd66226ebaae4060acf29f1bf74e70"
R02_D4_S6_FRAME_MANIFEST_SHA256 = "368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1"
R02_D4_S6_FRAME_SEAL_SHA256 = "40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838"
R02_D4_S6_S3_FREEZE_SHA256 = "3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449"
R02_D4_S6_FRAME_TREE_SHA256 = "65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29"
R02_D4_S6_FRAME_TREE_FILE_COUNT = 202
R02_D4_S6_RUN_PLAN_SHA256 = "188c971db338d5456c72a1e6e71801119dd8f992dd90fd86c3952f09121cffc9"
R02_D4_S6_ATTEMPT_CAP = R02_D4_S5_ELIGIBLE_COUNT
R02_D4_S6_TOKEN_RESERVE = R02_D4_S5_PER_ATTEMPT_TOKEN_RESERVE
R02_D4_S6_TOKEN_CAP = R02_D4_S5_AGGREGATE_TOKEN_CAP
R02_D4_S6_TIMEOUT_MS = R02_D4_S5_LIVE_TIMEOUT_MS
R02_D4_S6_FAIL_CLOSED_CAP = R02_D4_S5_FAIL_CLOSED_ATTEMPT_CAP
R02_D4_S6_RETRY_CAP = 0
R02_D4_S6_REPLACEMENT_CAP = 0
R02_D4_S6_RESUME_CAP = 0
R02_D4_S6_MICRO_PILOT_CAP = 0
R02_D4_S6_MAX_REPORTED_TOKENS = (1 << 63) - 1

R02_D4_S6_HARD_STOP_CONDITIONS = (
    "MISSING_SEPARATE_LIVE_AUTHORIZATION",
    "TRUST_ANCHOR_PROTECTED_TREE_OR_SOURCE_PIN_DRIFT",
    "FRAME_ID_MANIFEST_SEAL_TREE_OR_EXECUTION_ORDER_DRIFT",
    "PROMPT_OUTPUT_SCHEMA_MODEL_PROVIDER_EXECUTABLE_FEATURE_OR_COMMAND_DRIFT",
    "ATTEMPT_OR_TOKEN_BUDGET_WOULD_BE_EXCEEDED",
    "TRANSPORT_TIMEOUT_NONZERO_EXIT_MISSING_USAGE_OR_UNSETTLED_ATTEMPT",
    "REPORTED_USAGE_OVER_32000_TOKEN_RESERVE",
    "SETTLED_FAIL_CLOSED_COUNT_WOULD_EXCEED_6",
    "AUDIT_PERSISTENCE_HASH_OR_REPLAY_FAILURE",
    "RETRY_REPLACEMENT_OR_RESUME_REQUESTED",
)


class R02D4S6LiveAuthorizationArtifact(StrictModel):
    """Schema only. S6 does not create an instance of this future artifact."""

    schema_version: Literal["r02-d4-s6-live-authorization-artifact-v1"] = "r02-d4-s6-live-authorization-artifact-v1"
    authorization_id: str = Field(pattern=r"^r02-d4-live-auth-[a-z0-9-]{4,80}$")
    run_id: str = Field(pattern=r"^r02-d4-[a-z0-9-]{4,80}$")
    approved_scope: Literal["INDIVISIBLE_ALL_69_LIVE"] = "INDIVISIBLE_ALL_69_LIVE"
    accepted_s5_freeze_sha256: Literal[R02_D4_S6_S5_FREEZE_SHA256] = R02_D4_S6_S5_FREEZE_SHA256
    accepted_s6_review_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_calls_authorized: Literal[True] = True
    production_artifact_root_authorized: Literal[True] = True
    all_69_one_shot_authorized: Literal[True] = True
    micro_pilot_authorized: Literal[False] = False
    retry_or_replacement_authorized: Literal[False] = False
    resume_authorized: Literal[False] = False


class R02D4S6RunAuthorization(StrictModel):
    schema_version: Literal["r02-d4-s6-run-authorization-v1"] = "r02-d4-s6-run-authorization-v1"
    run_id: str = Field(pattern=r"^r02-d4-[a-z0-9-]{4,80}$")
    mode: Literal["OFFLINE_FAKE", "LIVE"]
    authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_s5_freeze_sha256: Literal[R02_D4_S6_S5_FREEZE_SHA256] = R02_D4_S6_S5_FREEZE_SHA256
    artifact_root_kind: Literal["TEMP_TEST_ONLY", "PRODUCTION"]
    provider_calls_authorized: bool
    production_artifact_root_authorized: bool
    all_69_one_shot_authorized: bool
    micro_pilot_attempts: Literal[0] = 0
    retry_cap: Literal[0] = 0
    replacement_cap: Literal[0] = 0
    resume_cap: Literal[0] = 0
    live_authorization_artifact: R02D4S6LiveAuthorizationArtifact | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "R02D4S6RunAuthorization":
        if self.mode == "OFFLINE_FAKE":
            expected = canonical_sha256(
                {
                    "domain": "r02-d4-s6-offline-fake-authorization-v1",
                    "run_id": self.run_id,
                    "accepted_s5_freeze_sha256": self.accepted_s5_freeze_sha256,
                }
            )
            if self.authorization_sha256 != expected:
                raise ValueError("offline fake authorization digest mismatch")
            if self.artifact_root_kind != "TEMP_TEST_ONLY":
                raise ValueError("offline fake mode requires a temporary artifact root")
            if any(
                (
                    self.provider_calls_authorized,
                    self.production_artifact_root_authorized,
                    self.all_69_one_shot_authorized,
                )
            ):
                raise ValueError("offline fake mode cannot self-authorize LIVE capabilities")
            if self.live_authorization_artifact is not None:
                raise ValueError("offline fake mode cannot carry a LIVE authorization artifact")
            return self

        artifact = self.live_authorization_artifact
        if artifact is None:
            raise ValueError("LIVE mode requires a separate external authorization artifact")
        if self.artifact_root_kind != "PRODUCTION":
            raise ValueError("LIVE mode requires the production artifact-root kind")
        if not all(
            (
                self.provider_calls_authorized,
                self.production_artifact_root_authorized,
                self.all_69_one_shot_authorized,
            )
        ):
            raise ValueError("LIVE mode requires the indivisible all-69 capability set")
        if artifact.run_id != self.run_id:
            raise ValueError("LIVE authorization run identity mismatch")
        if self.authorization_sha256 != canonical_sha256(artifact):
            raise ValueError("LIVE authorization digest mismatch")
        return self


def offline_fake_authorization(run_id: str) -> R02D4S6RunAuthorization:
    digest = canonical_sha256(
        {
            "domain": "r02-d4-s6-offline-fake-authorization-v1",
            "run_id": run_id,
            "accepted_s5_freeze_sha256": R02_D4_S6_S5_FREEZE_SHA256,
        }
    )
    return R02D4S6RunAuthorization(
        run_id=run_id,
        mode="OFFLINE_FAKE",
        authorization_sha256=digest,
        artifact_root_kind="TEMP_TEST_ONLY",
        provider_calls_authorized=False,
        production_artifact_root_authorized=False,
        all_69_one_shot_authorized=False,
    )


class R02D4S6PlannedAttempt(StrictModel):
    execution_ordinal: int = Field(ge=0, lt=R02_D4_S6_ATTEMPT_CAP)
    frame_ordinal: int = Field(ge=0, lt=200)
    fixture_id: str = Field(pattern=r"^development-[0-9]{4}$")
    stratum: Literal["REPRESENTATIVE", "CHALLENGE_HEADROOM"]
    candidate_count: Literal[2, 3, 4]
    fixture_artifact: ArtifactReference
    fixture_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preparation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selector_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class R02D4S6RunPlan(StrictModel):
    schema_version: Literal["r02-d4-s6-run-plan-v1"] = "r02-d4-s6-run-plan-v1"
    frame_id: Literal[R02_D4_S5_FRAME_ID] = R02_D4_S5_FRAME_ID
    s5_execution_plan_sha256: Literal[R02_D4_S5_EXECUTION_PLAN_SHA256] = R02_D4_S5_EXECUTION_PLAN_SHA256
    attempts: tuple[R02D4S6PlannedAttempt, ...] = Field(
        min_length=R02_D4_S6_ATTEMPT_CAP,
        max_length=R02_D4_S6_ATTEMPT_CAP,
    )
    ordering: Literal["ELIGIBLE_CASES_BY_FRAME_ORDINAL_ASCENDING"] = "ELIGIBLE_CASES_BY_FRAME_ORDINAL_ASCENDING"
    micro_pilot_decision: Literal["NO_MICRO_PILOT"] = "NO_MICRO_PILOT"
    retry_cap: Literal[0] = 0
    replacement_cap: Literal[0] = 0
    resume_cap: Literal[0] = 0

    @model_validator(mode="after")
    def validate_plan(self) -> "R02D4S6RunPlan":
        if tuple(item.execution_ordinal for item in self.attempts) != tuple(range(R02_D4_S6_ATTEMPT_CAP)):
            raise ValueError("execution ordinals must be contiguous")
        if tuple(item.frame_ordinal for item in self.attempts) != tuple(R02_D4_S5_ELIGIBLE_FRAME_ORDINALS):
            raise ValueError("eligible frame execution order drift")
        if len({item.fixture_id for item in self.attempts}) != R02_D4_S6_ATTEMPT_CAP:
            raise ValueError("planned fixture identities must be unique")
        if canonical_sha256(self) != R02_D4_S6_RUN_PLAN_SHA256:
            raise ValueError("complete prepared run-plan digest drift")
        return self


class R02D4S6ContractBinding(StrictModel):
    schema_version: Literal["r02-d4-s6-contract-binding-v1"] = "r02-d4-s6-contract-binding-v1"
    base_commit: Literal[R02_D4_S6_BASE_COMMIT] = R02_D4_S6_BASE_COMMIT
    s5_freeze_sha256: Literal[R02_D4_S6_S5_FREEZE_SHA256] = R02_D4_S6_S5_FREEZE_SHA256
    identity_snapshot_sha256: Literal[R02_D4_S6_S5_IDENTITY_SNAPSHOT_SHA256] = R02_D4_S6_S5_IDENTITY_SNAPSHOT_SHA256
    frame_manifest_sha256: Literal[R02_D4_S6_FRAME_MANIFEST_SHA256] = R02_D4_S6_FRAME_MANIFEST_SHA256
    frame_seal_sha256: Literal[R02_D4_S6_FRAME_SEAL_SHA256] = R02_D4_S6_FRAME_SEAL_SHA256
    frame_tree_sha256: Literal[R02_D4_S6_FRAME_TREE_SHA256] = R02_D4_S6_FRAME_TREE_SHA256
    frame_tree_file_count: Literal[R02_D4_S6_FRAME_TREE_FILE_COUNT] = R02_D4_S6_FRAME_TREE_FILE_COUNT
    run_plan_sha256: Literal[R02_D4_S6_RUN_PLAN_SHA256] = R02_D4_S6_RUN_PLAN_SHA256
    attempt_cap: Literal[R02_D4_S6_ATTEMPT_CAP] = R02_D4_S6_ATTEMPT_CAP
    token_reserve: Literal[R02_D4_S6_TOKEN_RESERVE] = R02_D4_S6_TOKEN_RESERVE
    aggregate_token_cap: Literal[R02_D4_S6_TOKEN_CAP] = R02_D4_S6_TOKEN_CAP
    timeout_ms: Literal[R02_D4_S6_TIMEOUT_MS] = R02_D4_S6_TIMEOUT_MS
    fail_closed_cap: Literal[R02_D4_S6_FAIL_CLOSED_CAP] = R02_D4_S6_FAIL_CLOSED_CAP
    micro_pilot_attempts: Literal[0] = 0
    retry_cap: Literal[0] = 0
    replacement_cap: Literal[0] = 0
    resume_cap: Literal[0] = 0
    hard_stop_conditions: tuple[Literal[*R02_D4_S6_HARD_STOP_CONDITIONS], ...] = R02_D4_S6_HARD_STOP_CONDITIONS

    @model_validator(mode="after")
    def validate_binding(self) -> "R02D4S6ContractBinding":
        if self.hard_stop_conditions != R02_D4_S6_HARD_STOP_CONDITIONS:
            raise ValueError("S5 hard-stop ordering or membership drift")
        return self


class R02D4S6TokenReservation(StrictModel):
    schema_version: Literal["r02-d4-s6-token-reservation-v1"] = "r02-d4-s6-token-reservation-v1"
    run_id: str
    fixture_id: str
    execution_ordinal: int = Field(ge=0, lt=R02_D4_S6_ATTEMPT_CAP)
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_attempt_ordinal: int = Field(ge=1, le=R02_D4_S6_ATTEMPT_CAP)
    reserve_tokens: Literal[R02_D4_S6_TOKEN_RESERVE] = R02_D4_S6_TOKEN_RESERVE
    reserved_attempts_before: int = Field(ge=0, lt=R02_D4_S6_ATTEMPT_CAP)
    reserved_tokens_before: int = Field(ge=0, le=R02_D4_S6_TOKEN_CAP)
    reserved_tokens_after: int = Field(ge=0, le=R02_D4_S6_TOKEN_CAP)

    @model_validator(mode="after")
    def validate_reservation(self) -> "R02D4S6TokenReservation":
        if self.provider_attempt_ordinal != self.reserved_attempts_before + 1:
            raise ValueError("attempt reservation ordinal mismatch")
        if self.reserved_tokens_after != self.reserved_tokens_before + self.reserve_tokens:
            raise ValueError("token reservation arithmetic mismatch")
        return self


class R02D4S6AttemptStarted(StrictModel):
    schema_version: Literal["r02-d4-s6-attempt-started-v1"] = "r02-d4-s6-attempt-started-v1"
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_attempt_ordinal: int = Field(ge=1, le=R02_D4_S6_ATTEMPT_CAP)
    reservation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    launch_may_have_occurred: Literal[True] = True
    timeout_ms: Literal[R02_D4_S6_TIMEOUT_MS] = R02_D4_S6_TIMEOUT_MS


class R02D4S6TransportResult(StrictModel):
    schema_version: Literal["r02-d4-s6-transport-result-v1"] = "r02-d4-s6-transport-result-v1"
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_response: str | None = None
    raw_response_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    input_tokens: int | None = Field(default=None, ge=0, le=R02_D4_S6_MAX_REPORTED_TOKENS)
    cached_input_tokens: int | None = Field(default=None, ge=0, le=R02_D4_S6_MAX_REPORTED_TOKENS)
    output_tokens: int | None = Field(default=None, ge=0, le=R02_D4_S6_MAX_REPORTED_TOKENS)
    reasoning_output_tokens: int | None = Field(default=None, ge=0, le=R02_D4_S6_MAX_REPORTED_TOKENS)
    terminal_usage_event_count: int = Field(ge=0)
    exit_code: int | None
    timed_out: bool
    launch_error: str | None = None
    duration_ms: int = Field(ge=0)
    external_provider_calls: Literal[0, 1]

    @model_validator(mode="after")
    def validate_raw_hash(self) -> "R02D4S6TransportResult":
        expected = canonical_sha256({"raw_response": self.raw_response})
        if self.raw_response_sha256 != expected:
            raise ValueError("raw response digest mismatch")
        return self


class R02D4S6AttemptOutcome(StrictModel):
    schema_version: Literal["r02-d4-s6-attempt-outcome-v1"] = "r02-d4-s6-attempt-outcome-v1"
    run_id: str
    fixture_id: str
    attempt_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal[
        "SETTLED_ACCEPTED",
        "SETTLED_FAIL_CLOSED",
        "UNSETTLED_HARD_STOP",
        "INVALID_BUDGET_HARD_STOP",
    ]
    settled: bool
    debit_tokens: int = Field(ge=0, le=R02_D4_S6_TOKEN_RESERVE)
    observed_total_tokens: int | None = Field(default=None, ge=0, le=R02_D4_S6_MAX_REPORTED_TOKENS)
    selected_presented_id: str | None = None
    selected_canonical_id: str | None = None
    baseline_canonical_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    executed_canonical_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    baseline_fallback: bool
    error_codes: tuple[str, ...] = ()
    baseline_utility_e12: int | None = None
    executed_utility_e12: int | None = None
    paired_utility_delta_e12: int | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> "R02D4S6AttemptOutcome":
        if self.settled != self.status.startswith("SETTLED_"):
            raise ValueError("attempt settlement status mismatch")
        if self.settled:
            if self.observed_total_tokens is None or self.debit_tokens != self.observed_total_tokens:
                raise ValueError("settled debit must equal observed usage")
            if any(
                value is None
                for value in (
                    self.baseline_canonical_id,
                    self.executed_canonical_id,
                    self.baseline_utility_e12,
                    self.executed_utility_e12,
                    self.paired_utility_delta_e12,
                )
            ):
                raise ValueError("settled result requires complete paired outcome fields")
            assert self.paired_utility_delta_e12 is not None
            assert self.baseline_utility_e12 is not None
            assert self.executed_utility_e12 is not None
            if self.paired_utility_delta_e12 != (self.executed_utility_e12 - self.baseline_utility_e12):
                raise ValueError("paired utility delta arithmetic mismatch")
            if self.baseline_fallback and self.paired_utility_delta_e12 != 0:
                raise ValueError("fail-closed fallback delta must be zero")
        elif self.debit_tokens != R02_D4_S6_TOKEN_RESERVE:
            raise ValueError("unsettled or invalid usage must debit the full reserve")
        return self


class R02D4S6ContinuationDecision(StrictModel):
    schema_version: Literal["r02-d4-s6-continuation-decision-v1"] = "r02-d4-s6-continuation-decision-v1"
    run_id: str
    after_attempts: int = Field(ge=1, le=R02_D4_S6_ATTEMPT_CAP)
    action: Literal["CONTINUE", "COMPLETE", "HARD_STOP"]
    hard_stop_code: str | None = None
    settled_fail_closed_count: int = Field(ge=0)
    unsettled_attempt_count: int = Field(ge=0)
    utility_outcomes_consulted: Literal[False] = False
    interim_outcomes_disclosed: Literal[False] = False
    second_authorization_requested: Literal[False] = False
    micro_pilot_used: Literal[False] = False

    @model_validator(mode="after")
    def validate_decision(self) -> "R02D4S6ContinuationDecision":
        if (self.action == "HARD_STOP") != (self.hard_stop_code is not None):
            raise ValueError("hard-stop action and code must be paired")
        if self.action == "COMPLETE" and self.after_attempts != R02_D4_S6_ATTEMPT_CAP:
            raise ValueError("completion requires all 69 ITT attempts")
        if self.hard_stop_code is not None and self.hard_stop_code not in R02_D4_S6_HARD_STOP_CONDITIONS:
            raise ValueError("unknown hard-stop code")
        return self


class R02D4S6RunLedger(StrictModel):
    schema_version: Literal["r02-d4-s6-run-ledger-v1"] = "r02-d4-s6-run-ledger-v1"
    run_id: str
    planned_attempt_count: Literal[R02_D4_S6_ATTEMPT_CAP] = R02_D4_S6_ATTEMPT_CAP
    reserved_attempt_count: int = Field(ge=0, le=R02_D4_S6_ATTEMPT_CAP)
    reserved_tokens: int = Field(ge=0, le=R02_D4_S6_TOKEN_CAP)
    launched_attempt_count: int = Field(ge=0, le=R02_D4_S6_ATTEMPT_CAP)
    settled_attempt_count: int = Field(ge=0, le=R02_D4_S6_ATTEMPT_CAP)
    unsettled_attempt_count: int = Field(ge=0, le=1)
    settled_fail_closed_count: int = Field(ge=0, le=R02_D4_S6_FAIL_CLOSED_CAP + 1)
    debited_tokens: int = Field(ge=0, le=R02_D4_S6_TOKEN_CAP)
    attempted_fixture_ids: tuple[str, ...]
    status: Literal["RUNNING", "COMPLETE", "INVALID_RUN"]
    terminal_code: str | None = None
    transport_invocations: int = Field(ge=0, le=R02_D4_S6_ATTEMPT_CAP)
    external_provider_calls: int = Field(ge=0, le=R02_D4_S6_ATTEMPT_CAP)
    micro_pilot_attempts: Literal[0] = 0
    retry_count: Literal[0] = 0
    replacement_count: Literal[0] = 0
    resume_count: Literal[0] = 0

    @model_validator(mode="after")
    def validate_ledger(self) -> "R02D4S6RunLedger":
        if self.reserved_tokens != self.reserved_attempt_count * R02_D4_S6_TOKEN_RESERVE:
            raise ValueError("reserved token arithmetic mismatch")
        if self.launched_attempt_count != len(self.attempted_fixture_ids):
            raise ValueError("ITT attempted fixture ledger mismatch")
        if len(set(self.attempted_fixture_ids)) != len(self.attempted_fixture_ids):
            raise ValueError("duplicate attempted fixture identity")
        if self.settled_attempt_count + self.unsettled_attempt_count != self.launched_attempt_count:
            raise ValueError("attempt settlement counts do not reconcile")
        if self.transport_invocations != self.launched_attempt_count:
            raise ValueError("transport invocation count mismatch")
        if self.status == "INVALID_RUN" and self.terminal_code is None:
            raise ValueError("invalid run requires a terminal code")
        if self.status != "INVALID_RUN" and self.terminal_code is not None:
            raise ValueError("non-invalid ledger cannot carry a terminal code")
        if self.status == "COMPLETE" and self.launched_attempt_count != R02_D4_S6_ATTEMPT_CAP:
            raise ValueError("complete ledger requires all 69 attempts")
        return self


class R02D4S6AuditNode(StrictModel):
    schema_version: Literal["r02-d4-s6-audit-node-v1"] = "r02-d4-s6-audit-node-v1"
    run_id: str
    sequence: int = Field(ge=1)
    node_type: str = Field(pattern=r"^[a-z][a-z0-9_]{2,80}$")
    previous_node_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    payload: ArtifactReference


class R02D4S6AuditAnchor(StrictModel):
    schema_version: Literal["r02-d4-s6-audit-anchor-v1"] = "r02-d4-s6-audit-anchor-v1"
    run_id: str
    sequence: int = Field(ge=1)
    node_types: tuple[str, ...]
    nodes: tuple[ArtifactReference, ...]
    head_node_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_anchor(self) -> "R02D4S6AuditAnchor":
        if self.sequence != len(self.nodes) or len(self.node_types) != len(self.nodes):
            raise ValueError("audit anchor sequence mismatch")
        if self.nodes[-1].sha256 != self.head_node_sha256:
            raise ValueError("audit anchor head mismatch")
        return self


class R02D4S6RunTerminal(StrictModel):
    schema_version: Literal["r02-d4-s6-run-terminal-v1"] = "r02-d4-s6-run-terminal-v1"
    run_id: str
    authorization_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    contract_binding_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    run_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    final_ledger: R02D4S6RunLedger
    terminal_status: Literal["COMPLETE", "INVALID_RUN"]
    replay_required: Literal[True] = True

    @model_validator(mode="after")
    def validate_terminal(self) -> "R02D4S6RunTerminal":
        if self.final_ledger.status != self.terminal_status:
            raise ValueError("terminal status and final ledger mismatch")
        return self
