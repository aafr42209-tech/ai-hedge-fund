"""Strict provider-free production contracts for the R02 candidate selector.

These models cover only D2a: deterministic trigger/candidate preparation,
first-class no-call outcomes, append-only audit persistence, and replay.  They
contain no provider client and cannot authorize an R02 live run.
"""

from __future__ import annotations

from enum import StrEnum
import hashlib
import hmac
import json
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .canonical import canonical_json_bytes, canonical_sha256
from .contracts import (
    ASSET_IDS,
    ArtifactReference,
    EpisodeScore,
    StrictModel,
    ValidationReport,
)

R02_CONTRACT_ID = "R02-baseline-anchored-candidate-selection-v0-draft"
R02_FREEZE_SHA256 = "2d5961806b5051ff56c874b8b05933df014136bacb98717c4846f2b48f645778"
R02_MANIFEST_SHA256 = "81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf"
R02_ACCEPTED_COMMIT = "2a532c74176f8df93923775482846d3b3448c83e"
R02_TRIGGER_THRESHOLD_BPS = 50
R02_ROOT_SEED = b"r02-candidate-order-root-v1-20260717"
R02_SEED_LABEL = b"r02-candidate-order-v1"


def _candidate_id(batch: "R02CandidateBatch") -> str:
    payload = {
        "schema_version": batch.schema_version,
        "decisions": {
            asset_id: {
                "action": batch.decisions[asset_id].action,
                "quantity": batch.decisions[asset_id].quantity,
            }
            for asset_id in ASSET_IDS
        },
    }
    content = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class R02CandidateRole(StrEnum):
    BASELINE = "BASELINE"
    NO_CHANGE = "NO_CHANGE"
    HALF_BASELINE_DELTA = "HALF_BASELINE_DELTA"
    DROP_MAX_COST_TRADE = "DROP_MAX_COST_TRADE"


R02_ROLE_ORDER = tuple(R02CandidateRole)


class R02NoCallReason(StrEnum):
    TRIGGER_FALSE = "TRIGGER_FALSE"
    CANDIDATE_COLLAPSE = "CANDIDATE_COLLAPSE"
    PRE_PROVIDER_BUDGET_STOP = "PRE_PROVIDER_BUDGET_STOP"
    PRE_PROVIDER_INTEGRITY_STOP = "PRE_PROVIDER_INTEGRITY_STOP"


class R02PreparationState(StrEnum):
    NO_CALL_TERMINAL = "NO_CALL_TERMINAL"
    SELECTOR_ELIGIBLE_NOT_CALLED = "SELECTOR_ELIGIBLE_NOT_CALLED"


class R02Identity(StrictModel):
    schema_version: Literal["r02-identity-v1"] = "r02-identity-v1"
    contract_id: Literal[R02_CONTRACT_ID] = R02_CONTRACT_ID
    experiment_id: str = Field(min_length=1)
    fixture_id: str = Field(min_length=1)
    fixture_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    channel: Literal["candidate_selection"] = "candidate_selection"
    replicate_id: int = Field(default=0, ge=0)


class R02CandidateDecision(StrictModel):
    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_action_quantity(self) -> "R02CandidateDecision":
        if self.action == "hold" and self.quantity != 0:
            raise ValueError("hold requires quantity 0")
        if self.action != "hold" and self.quantity <= 0:
            raise ValueError("buy and sell require positive quantity")
        return self


class R02CandidateBatch(StrictModel):
    schema_version: Literal["r02-candidate-decision-v1"] = "r02-candidate-decision-v1"
    decisions: dict[str, R02CandidateDecision]

    @field_validator("decisions")
    @classmethod
    def validate_decision_keys(
        cls, value: dict[str, R02CandidateDecision]
    ) -> dict[str, R02CandidateDecision]:
        if set(value) != set(ASSET_IDS):
            raise ValueError("candidate decisions must contain exactly A0 through A5")
        return value


class R02TriggerCostLine(StrictModel):
    asset_id: str
    notional_cents: int = Field(gt=0)
    total_cost_cents: int = Field(ge=0)
    effective_cost_bps: int = Field(ge=0)

    @field_validator("asset_id")
    @classmethod
    def validate_asset_id(cls, value: str) -> str:
        if value not in ASSET_IDS:
            raise ValueError("unknown anonymous asset ID")
        return value

    @model_validator(mode="after")
    def validate_effective_cost(self) -> "R02TriggerCostLine":
        expected = (self.total_cost_cents * 10_000 + self.notional_cents - 1) // self.notional_cents
        if self.effective_cost_bps != expected:
            raise ValueError("effective cost bps arithmetic mismatch")
        return self


class R02TriggerInput(StrictModel):
    schema_version: Literal["r02-trigger-input-v1"] = "r02-trigger-input-v1"
    baseline_canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    cost_lines: tuple[R02TriggerCostLine, ...] = ()

    @model_validator(mode="after")
    def validate_cost_line_order(self) -> "R02TriggerInput":
        asset_ids = tuple(line.asset_id for line in self.cost_lines)
        if asset_ids != tuple(sorted(asset_ids)) or len(asset_ids) != len(set(asset_ids)):
            raise ValueError("trigger cost lines must be unique and sorted by asset_id")
        return self


class R02TriggerDecision(StrictModel):
    schema_version: Literal["r02-trigger-decision-v1"] = "r02-trigger-decision-v1"
    trigger_id: Literal["R02-TRIGGER-EFFECTIVE-COST-50BPS-v1"] = (
        "R02-TRIGGER-EFFECTIVE-COST-50BPS-v1"
    )
    trade_count: int = Field(ge=0)
    max_traded_effective_cost_bps: int = Field(ge=0)
    triggered: bool
    reason_codes: tuple[
        Literal[
            "MAX_TRADED_EFFECTIVE_COST_BPS_GE_50",
            "MAX_TRADED_EFFECTIVE_COST_BPS_LT_50_OR_NO_TRADE",
        ],
        ...,
    ]

    @model_validator(mode="after")
    def validate_trigger(self) -> "R02TriggerDecision":
        expected = self.trade_count > 0 and self.max_traded_effective_cost_bps >= R02_TRIGGER_THRESHOLD_BPS
        if self.triggered != expected:
            raise ValueError("trigger decision does not match the frozen predicate")
        reason = (
            "MAX_TRADED_EFFECTIVE_COST_BPS_GE_50"
            if expected
            else "MAX_TRADED_EFFECTIVE_COST_BPS_LT_50_OR_NO_TRADE"
        )
        if self.reason_codes != (reason,):
            raise ValueError("trigger reason code mismatch")
        if self.trade_count == 0 and self.max_traded_effective_cost_bps != 0:
            raise ValueError("empty cost ledger must have maximum 0")
        return self


class R02EligibilityDecision(StrictModel):
    schema_version: Literal["r02-eligibility-decision-v1"] = "r02-eligibility-decision-v1"
    identity: R02Identity
    overlay_spec_sha256: Literal[R02_FREEZE_SHA256] = R02_FREEZE_SHA256
    public_fixture_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trigger_rule_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trigger_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trigger_input: R02TriggerInput
    trigger: R02TriggerDecision

    @model_validator(mode="after")
    def validate_eligibility_hashes(self) -> "R02EligibilityDecision":
        if self.trigger_input_sha256 != canonical_sha256(self.trigger_input):
            raise ValueError("trigger input hash mismatch")
        maximum = max(
            (line.effective_cost_bps for line in self.trigger_input.cost_lines),
            default=0,
        )
        if self.trigger.trade_count != len(self.trigger_input.cost_lines):
            raise ValueError("trigger trade count mismatch")
        if self.trigger.max_traded_effective_cost_bps != maximum:
            raise ValueError("trigger maximum cost mismatch")
        return self


class R02RawCandidateAudit(StrictModel):
    role: R02CandidateRole
    candidate: R02CandidateBatch
    canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_report: ValidationReport
    validation_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_valid: Literal[True] = True
    fell_back: Literal[False] = False
    executable_matches: Literal[True] = True

    @model_validator(mode="after")
    def validate_raw_candidate(self) -> "R02RawCandidateAudit":
        if self.canonical_candidate_id != _candidate_id(self.candidate):
            raise ValueError("raw candidate identity mismatch")
        if self.validation_report_sha256 != canonical_sha256(self.validation_report):
            raise ValueError("validation report hash mismatch")
        if not self.validation_report.raw_valid or self.validation_report.fell_back:
            raise ValueError("raw candidate audit must contain a valid non-fallback report")
        return self


class R02CanonicalCandidate(StrictModel):
    primary_role: R02CandidateRole
    aliases: tuple[R02CandidateRole, ...] = ()
    canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate: R02CandidateBatch

    @model_validator(mode="after")
    def validate_roles(self) -> "R02CanonicalCandidate":
        if self.primary_role in self.aliases or len(self.aliases) != len(set(self.aliases)):
            raise ValueError("candidate aliases must be unique and exclude the primary role")
        if self.canonical_candidate_id != _candidate_id(self.candidate):
            raise ValueError("canonical candidate identity mismatch")
        return self


class R02CandidateSet(StrictModel):
    schema_version: Literal["r02-candidate-set-v1"] = "r02-candidate-set-v1"
    identity: R02Identity
    eligibility_decision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    generator_id: Literal["R02-CANDIDATE-GENERATOR-A-COST-v1"] = (
        "R02-CANDIDATE-GENERATOR-A-COST-v1"
    )
    generator_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    generator_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_candidates: tuple[R02RawCandidateAudit, ...]
    candidates: tuple[R02CanonicalCandidate, ...] = Field(min_length=1, max_length=4)
    canonical_candidate_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_candidate_set(self) -> "R02CandidateSet":
        raw_roles = tuple(item.role for item in self.raw_candidates)
        if raw_roles != R02_ROLE_ORDER:
            raise ValueError("all four raw roles must be validated in frozen order")
        ids = tuple(item.canonical_candidate_id for item in self.candidates)
        if len(ids) != len(set(ids)):
            raise ValueError("canonical candidates must be unique")
        if self.candidates[0].primary_role is not R02CandidateRole.BASELINE:
            raise ValueError("BASELINE must be the first canonical candidate")
        if self.candidates[0].canonical_candidate_id != self.baseline_canonical_candidate_id:
            raise ValueError("baseline candidate identity mismatch")
        flattened_roles = tuple(
            role for candidate in self.candidates for role in (candidate.primary_role, *candidate.aliases)
        )
        if sorted(flattened_roles, key=R02_ROLE_ORDER.index) != list(R02_ROLE_ORDER):
            raise ValueError("deduplication must preserve every raw role exactly once")
        raw_by_role = {item.role: item for item in self.raw_candidates}
        for candidate in self.candidates:
            for role in (candidate.primary_role, *candidate.aliases):
                raw = raw_by_role[role]
                if raw.canonical_candidate_id != candidate.canonical_candidate_id:
                    raise ValueError("deduplicated role points to the wrong candidate")
        expected_set_sha256 = canonical_sha256(
            tuple(candidate.model_dump(mode="python") for candidate in self.candidates)
        )
        if self.canonical_candidate_set_sha256 != expected_set_sha256:
            raise ValueError("canonical candidate-set hash mismatch")
        return self


class R02PresentedCandidate(StrictModel):
    presented_id: str = Field(pattern=r"^P[0-9]{2}$")
    candidate: R02CandidateBatch


class R02CandidatePermutation(StrictModel):
    schema_version: Literal["r02-candidate-permutation-v1"] = "r02-candidate-permutation-v1"
    identity: R02Identity
    candidate_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed_label: Literal["r02-candidate-order-v1"] = "r02-candidate-order-v1"
    seed_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    derived_seed_hex: str = Field(pattern=r"^[0-9a-f]{64}$")
    original_canonical_order: tuple[str, ...]
    presented_order: tuple[str, ...]
    presented_to_canonical_map: dict[str, str]
    presented_candidates: tuple[R02PresentedCandidate, ...]
    permutation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_permutation(self) -> "R02CandidatePermutation":
        expected_presented = tuple(f"P{index:02d}" for index in range(len(self.presented_order)))
        if tuple(self.presented_to_canonical_map) != expected_presented:
            raise ValueError("presented IDs must be contiguous and ordered")
        if tuple(item.presented_id for item in self.presented_candidates) != expected_presented:
            raise ValueError("presented candidate order mismatch")
        if tuple(self.presented_to_canonical_map.values()) != self.presented_order:
            raise ValueError("presented map and order mismatch")
        if set(self.original_canonical_order) != set(self.presented_order):
            raise ValueError("permutation must contain every candidate exactly once")
        if len(self.original_canonical_order) != len(set(self.original_canonical_order)):
            raise ValueError("original candidate order must be unique")
        for presented in self.presented_candidates:
            if _candidate_id(presented.candidate) != self.presented_to_canonical_map[presented.presented_id]:
                raise ValueError("presented candidate content identity mismatch")
        seed_message = (
            R02_SEED_LABEL
            + b"\x00"
            + self.identity.fixture_content_sha256.encode("ascii")
            + b"\x00"
            + R02_FREEZE_SHA256.encode("ascii")
        )
        if self.seed_input_sha256 != hashlib.sha256(seed_message).hexdigest():
            raise ValueError("permutation seed-input hash mismatch")
        derived_seed = hmac.new(R02_ROOT_SEED, seed_message, hashlib.sha256).digest()
        if self.derived_seed_hex != derived_seed.hex():
            raise ValueError("permutation seed mismatch")
        expected_order = tuple(
            candidate_id
            for _key, candidate_id in sorted(
                (
                    hmac.new(derived_seed, candidate_id.encode("ascii"), hashlib.sha256).hexdigest(),
                    candidate_id,
                )
                for candidate_id in self.original_canonical_order
            )
        )
        if self.presented_order != expected_order:
            raise ValueError("HMAC candidate order mismatch")
        expected_permutation_sha256 = canonical_sha256(
            {
                "seed_label": self.seed_label,
                "seed_input_sha256": self.seed_input_sha256,
                "derived_seed_hex": self.derived_seed_hex,
                "original_canonical_order": self.original_canonical_order,
                "presented_order": self.presented_order,
                "presented_to_canonical_map": self.presented_to_canonical_map,
            }
        )
        if self.permutation_sha256 != expected_permutation_sha256:
            raise ValueError("permutation identity mismatch")
        return self


class R02NoCallAbsenceAssertions(StrictModel):
    selector_request_absent: Literal[True] = True
    selector_response_absent: Literal[True] = True
    transport_artifacts_absent: Literal[True] = True


class R02NoCallRecord(StrictModel):
    schema_version: Literal["r02-no-call-record-v1"] = "r02-no-call-record-v1"
    identity: R02Identity
    eligibility_decision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_set_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    reason_code: R02NoCallReason
    provider_attempts_before: int = Field(ge=0)
    provider_attempts_after: int = Field(ge=0)
    baseline_canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    executed_canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_batch: R02CandidateBatch
    executed_batch: R02CandidateBatch
    integrity_error_codes: tuple[str, ...] = ()
    absence_assertions: R02NoCallAbsenceAssertions = R02NoCallAbsenceAssertions()

    @model_validator(mode="after")
    def validate_no_call(self) -> "R02NoCallRecord":
        if self.provider_attempts_before != self.provider_attempts_after:
            raise ValueError("no-call record must leave provider attempts unchanged")
        if self.executed_canonical_candidate_id != self.baseline_canonical_candidate_id:
            raise ValueError("no-call execution must be BASELINE")
        if self.baseline_batch != self.executed_batch:
            raise ValueError("no-call batch must equal BASELINE byte-for-byte")
        if _candidate_id(self.baseline_batch) != self.baseline_canonical_candidate_id:
            raise ValueError("no-call baseline batch identity mismatch")
        if self.reason_code is R02NoCallReason.PRE_PROVIDER_INTEGRITY_STOP:
            if not self.integrity_error_codes:
                raise ValueError("integrity stop requires typed error codes")
        elif self.integrity_error_codes:
            raise ValueError("integrity error codes are reserved for integrity stops")
        if self.reason_code is R02NoCallReason.CANDIDATE_COLLAPSE:
            if self.candidate_set_sha256 is None:
                raise ValueError("candidate collapse requires a candidate-set identity")
        elif self.candidate_set_sha256 is not None:
            raise ValueError("only candidate collapse may attach a no-call candidate set")
        return self


class R02ExecutionDecision(StrictModel):
    schema_version: Literal["r02-execution-decision-v1"] = "r02-execution-decision-v1"
    identity: R02Identity
    eligibility_decision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_set_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    selected_presented_id: None = None
    selected_canonical_id: None = None
    executed_canonical_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    acceptance_disposition: Literal["BASELINE_NO_CALL"] = "BASELINE_NO_CALL"
    baseline_fallback: Literal[True] = True
    executable_batch: R02CandidateBatch

    @model_validator(mode="after")
    def validate_executable_identity(self) -> "R02ExecutionDecision":
        if _candidate_id(self.executable_batch) != self.executed_canonical_id:
            raise ValueError("execution candidate identity mismatch")
        return self


class R02EpisodeResult(StrictModel):
    schema_version: Literal["r02-episode-result-v1"] = "r02-episode-result-v1"
    identity: R02Identity
    execution_decision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_score: EpisodeScore
    executed_score: EpisodeScore
    paired_utility_delta_e12: Literal[0] = 0
    provider_attempt_count: int = Field(ge=0)
    audit_disposition: Literal["NO_CALL_BASELINE_DELTA_ZERO"] = "NO_CALL_BASELINE_DELTA_ZERO"

    @model_validator(mode="after")
    def validate_zero_delta(self) -> "R02EpisodeResult":
        if self.baseline_score != self.executed_score:
            raise ValueError("no-call result must execute the baseline score exactly")
        return self


class R02ProviderFreePreparation(StrictModel):
    schema_version: Literal["r02-provider-free-preparation-v1"] = (
        "r02-provider-free-preparation-v1"
    )
    identity: R02Identity
    accepted_commit: Literal[R02_ACCEPTED_COMMIT] = R02_ACCEPTED_COMMIT
    freeze_spec_sha256: Literal[R02_FREEZE_SHA256] = R02_FREEZE_SHA256
    freeze_manifest_sha256: Literal[R02_MANIFEST_SHA256] = R02_MANIFEST_SHA256
    provider_calls: Literal[0] = 0
    provider_attempt_count: int = Field(ge=0)
    state: R02PreparationState
    eligibility: R02EligibilityDecision
    candidate_set: R02CandidateSet | None = None
    permutation: R02CandidatePermutation | None = None
    no_call: R02NoCallRecord | None = None
    execution_decision: R02ExecutionDecision | None = None
    episode_result: R02EpisodeResult | None = None

    @model_validator(mode="after")
    def validate_state_graph(self) -> "R02ProviderFreePreparation":
        if self.eligibility.identity != self.identity:
            raise ValueError("eligibility identity mismatch")
        if self.state is R02PreparationState.SELECTOR_ELIGIBLE_NOT_CALLED:
            if not self.eligibility.trigger.triggered:
                raise ValueError("selector eligibility requires a true trigger")
            if self.candidate_set is None or len(self.candidate_set.candidates) < 2:
                raise ValueError("selector eligibility requires at least two candidates")
            if self.permutation is None:
                raise ValueError("selector eligibility requires a frozen permutation")
            if any(value is not None for value in (self.no_call, self.execution_decision, self.episode_result)):
                raise ValueError("D2a selector-eligible preparation is non-terminal and provider-free")
        else:
            if self.permutation is not None:
                raise ValueError("no-call path must not create a selector permutation")
            if any(value is None for value in (self.no_call, self.execution_decision, self.episode_result)):
                raise ValueError("terminal no-call path requires record, execution, and result")
            assert self.no_call is not None
            if self.no_call.reason_code is R02NoCallReason.TRIGGER_FALSE:
                if self.eligibility.trigger.triggered or self.candidate_set is not None:
                    raise ValueError("TRIGGER_FALSE graph must stop before candidate generation")
            elif self.no_call.reason_code is R02NoCallReason.CANDIDATE_COLLAPSE:
                if not self.eligibility.trigger.triggered or self.candidate_set is None:
                    raise ValueError("candidate collapse requires a triggered candidate set")
                if len(self.candidate_set.candidates) != 1:
                    raise ValueError("candidate collapse requires K=1")
            elif self.no_call.reason_code is R02NoCallReason.PRE_PROVIDER_INTEGRITY_STOP:
                if not self.eligibility.trigger.triggered or self.candidate_set is not None:
                    raise ValueError("integrity stop must occur during triggered candidate generation")
        eligibility_sha256 = canonical_sha256(self.eligibility)
        if self.candidate_set is not None:
            if self.candidate_set.identity != self.identity:
                raise ValueError("candidate-set identity mismatch")
            if self.candidate_set.eligibility_decision_sha256 != eligibility_sha256:
                raise ValueError("candidate-set eligibility reference mismatch")
        candidate_set_sha256 = canonical_sha256(self.candidate_set) if self.candidate_set is not None else None
        if self.permutation is not None:
            if self.permutation.identity != self.identity:
                raise ValueError("permutation identity mismatch")
            if self.permutation.candidate_set_sha256 != candidate_set_sha256:
                raise ValueError("permutation candidate-set reference mismatch")
        if self.no_call is not None:
            if self.no_call.identity != self.identity:
                raise ValueError("no-call identity mismatch")
            if self.no_call.eligibility_decision_sha256 != eligibility_sha256:
                raise ValueError("no-call eligibility reference mismatch")
            if self.no_call.candidate_set_sha256 != candidate_set_sha256:
                raise ValueError("no-call candidate-set reference mismatch")
        if self.execution_decision is not None:
            if self.execution_decision.identity != self.identity:
                raise ValueError("execution identity mismatch")
            if self.execution_decision.eligibility_decision_sha256 != eligibility_sha256:
                raise ValueError("execution eligibility reference mismatch")
            if self.execution_decision.candidate_set_sha256 != candidate_set_sha256:
                raise ValueError("execution candidate-set reference mismatch")
        if self.episode_result is not None:
            assert self.execution_decision is not None
            if self.episode_result.identity != self.identity:
                raise ValueError("episode-result identity mismatch")
            if self.episode_result.execution_decision_sha256 != canonical_sha256(self.execution_decision):
                raise ValueError("episode-result execution reference mismatch")
        return self


class R02AuditGraph(StrictModel):
    schema_version: Literal["r02-audit-graph-v1"] = "r02-audit-graph-v1"
    identity: R02Identity
    preparation_state: R02PreparationState
    node_types: tuple[str, ...]
    nodes: tuple[ArtifactReference, ...]
    provider_calls: Literal[0] = 0
    terminal: bool

    @model_validator(mode="after")
    def validate_graph_shape(self) -> "R02AuditGraph":
        if len(self.node_types) != len(self.nodes):
            raise ValueError("audit graph node types and references must align")
        if len(set(self.node_types)) != len(self.node_types):
            raise ValueError("audit graph node types must be unique")
        if len({node.relative_path for node in self.nodes}) != len(self.nodes):
            raise ValueError("audit graph paths must be unique")
        expected = (
            (
                "public_fixture",
                "eligibility_decision",
                "candidate_set",
                "candidate_permutation",
                "preparation",
            )
            if self.preparation_state is R02PreparationState.SELECTOR_ELIGIBLE_NOT_CALLED
            else (
                "public_fixture",
                "eligibility_decision",
                *(('candidate_set',) if "candidate_set" in self.node_types else ()),
                "no_call_record",
                "execution_decision",
                "episode_result",
                "preparation",
            )
        )
        if self.node_types != expected:
            raise ValueError("audit graph node order mismatch")
        if self.terminal != (self.preparation_state is R02PreparationState.NO_CALL_TERMINAL):
            raise ValueError("audit graph terminal flag mismatch")
        return self


class R02PersistedPreparation(StrictModel):
    schema_version: Literal["r02-persisted-preparation-v1"] = "r02-persisted-preparation-v1"
    preparation: ArtifactReference
    audit_graph: ArtifactReference


class R02ReplayVerification(StrictModel):
    schema_version: Literal["r02-replay-verification-v1"] = "r02-replay-verification-v1"
    identity: R02Identity
    verified_artifacts: int = Field(ge=1)
    provider_calls: Literal[0] = 0
    all_hashes_match: Literal[True] = True
    trigger_reproduced: Literal[True] = True
    candidates_reproduced: Literal[True] = True
    permutation_reproduced: Literal[True] = True
    no_call_reconciled: Literal[True] = True


class R02SelectorReasonCode(StrEnum):
    FEWER_NON_HOLD_ACTIONS = "FEWER_NON_HOLD_ACTIONS"
    LOWER_TOTAL_QUANTITY = "LOWER_TOTAL_QUANTITY"
    ZERO_ACTIVITY_PREFERENCE = "ZERO_ACTIVITY_PREFERENCE"
    ACTION_DIRECTION_PREFERENCE = "ACTION_DIRECTION_PREFERENCE"
    TIE_BREAK_PREFERENCE = "TIE_BREAK_PREFERENCE"


class R02SelectorResponseStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"


class R02AcceptanceStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class R02FallbackReason(StrEnum):
    SELECTOR_SCHEMA_INVALID = "SELECTOR_SCHEMA_INVALID"
    UNKNOWN_PRESENTED_ID = "UNKNOWN_PRESENTED_ID"
    ACCEPTANCE_VALIDATION_FAILED = "ACCEPTANCE_VALIDATION_FAILED"


class R02SelectorSafePayload(StrictModel):
    schema_version: Literal["r02-selector-input-v1"] = "r02-selector-input-v1"
    candidates: tuple[R02PresentedCandidate, ...] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def validate_presented_ids(self) -> "R02SelectorSafePayload":
        expected = tuple(f"P{index:02d}" for index in range(len(self.candidates)))
        if tuple(candidate.presented_id for candidate in self.candidates) != expected:
            raise ValueError("selector-safe candidates must use contiguous presented IDs")
        return self


class R02SelectorPromptDraft(StrictModel):
    schema_version: Literal["r02-selector-prompt-draft-v1"] = (
        "r02-selector-prompt-draft-v1"
    )
    status: Literal["DRAFT_NOT_FROZEN"] = "DRAFT_NOT_FROZEN"
    input_contract: Literal["SELECTOR_SAFE_PAYLOAD_ONLY"] = (
        "SELECTOR_SAFE_PAYLOAD_ONLY"
    )
    selector_payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    system_prompt: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)


class R02ScriptedCommandSpec(StrictModel):
    schema_version: Literal["r02-scripted-command-spec-v1"] = (
        "r02-scripted-command-spec-v1"
    )
    transport_kind: Literal["SCRIPTED_ONLY"] = "SCRIPTED_ONLY"
    requested_model: Literal["scripted-r02-selector-v1"] = (
        "scripted-r02-selector-v1"
    )
    selector_runtime_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_status: Literal["DRAFT_NOT_FROZEN"] = "DRAFT_NOT_FROZEN"
    external_provider_enabled: Literal[False] = False


class R02SelectorRequest(StrictModel):
    schema_version: Literal["r02-selector-request-v1"] = "r02-selector-request-v1"
    identity: R02Identity
    candidate_permutation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selector_payload: R02SelectorSafePayload
    prompt: R02SelectorPromptDraft
    command_spec: R02ScriptedCommandSpec

    @model_validator(mode="after")
    def validate_request_barrier(self) -> "R02SelectorRequest":
        payload_sha256 = canonical_sha256(self.selector_payload)
        if self.prompt.selector_payload_sha256 != payload_sha256:
            raise ValueError("selector prompt payload hash mismatch")
        rendered_payload = canonical_json_bytes(self.selector_payload).decode("utf-8")
        if self.prompt.user_prompt.count(rendered_payload) != 1:
            raise ValueError("selector prompt must contain the safe payload exactly once")
        rendered_prompt = f"{self.prompt.system_prompt}\n{self.prompt.user_prompt}".lower()
        forbidden = (
            "baseline",
            "no_change",
            "half_baseline_delta",
            "drop_max_cost_trade",
            "canonical_candidate_id",
            "presented_to_canonical_map",
            "derived_seed",
            "oracle",
            "headroom",
            "future_returns",
        )
        if any(token in rendered_prompt for token in forbidden):
            raise ValueError("selector prompt crosses the frozen information barrier")
        return self


class R02SelectorResponsePayload(StrictModel):
    schema_version: Literal["r02-selector-response-v1"] = (
        "r02-selector-response-v1"
    )
    selected_candidate_id: str = Field(pattern=r"^P[0-9]{2}$")
    confidence: int = Field(ge=0, le=100)
    reason_codes: tuple[R02SelectorReasonCode, ...] = Field(
        min_length=1,
        max_length=3,
    )

    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes(
        cls, value: tuple[R02SelectorReasonCode, ...]
    ) -> tuple[R02SelectorReasonCode, ...]:
        if len(value) != len(set(value)):
            raise ValueError("selector reason codes must be unique")
        return value


class R02SelectorTokenLedger(StrictModel):
    schema_version: Literal["r02-selector-token-ledger-v1"] = (
        "r02-selector-token-ledger-v1"
    )
    identity: R02Identity
    scripted_attempt_ordinal: int = Field(ge=1)
    scripted_attempts_before: int = Field(ge=0)
    scripted_attempts_after: int = Field(ge=1)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_output_tokens: int = Field(ge=0)
    accounting_total_tokens: int = Field(ge=0)
    external_provider_calls: Literal[0] = 0

    @model_validator(mode="after")
    def validate_ledger(self) -> "R02SelectorTokenLedger":
        if self.scripted_attempts_after != self.scripted_attempts_before + 1:
            raise ValueError("scripted selector attempt counter must increment exactly once")
        if self.scripted_attempt_ordinal != self.scripted_attempts_after:
            raise ValueError("scripted attempt ordinal mismatch")
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("cached input tokens cannot exceed input tokens")
        if self.reasoning_output_tokens > self.output_tokens:
            raise ValueError("reasoning output tokens cannot exceed output tokens")
        if self.accounting_total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("accounting total must count input plus output exactly once")
        return self


class R02ScriptedExchange(StrictModel):
    schema_version: Literal["r02-scripted-exchange-v1"] = (
        "r02-scripted-exchange-v1"
    )
    raw_response: str
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_output_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_exchange_usage(self) -> "R02ScriptedExchange":
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("cached input tokens cannot exceed input tokens")
        if self.reasoning_output_tokens > self.output_tokens:
            raise ValueError("reasoning output tokens cannot exceed output tokens")
        return self


class R02ScriptedTransportRecord(StrictModel):
    schema_version: Literal["r02-scripted-transport-v1"] = (
        "r02-scripted-transport-v1"
    )
    identity: R02Identity
    selector_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    command_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    token_ledger_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    transport_kind: Literal["SCRIPTED_ONLY"] = "SCRIPTED_ONLY"
    transport_status: Literal["SCRIPTED_RESPONSE"] = "SCRIPTED_RESPONSE"
    external_provider_calls: Literal[0] = 0


class R02ModelIdentityEvidence(StrictModel):
    schema_version: Literal["r02-model-identity-evidence-v1"] = (
        "r02-model-identity-evidence-v1"
    )
    requested_model: Literal["scripted-r02-selector-v1"] = (
        "scripted-r02-selector-v1"
    )
    command_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selector_runtime_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_model_echo: None = None
    external_provider_calls: Literal[0] = 0


class R02SelectorResponseRecord(StrictModel):
    schema_version: Literal["r02-selector-response-record-v1"] = (
        "r02-selector-response-record-v1"
    )
    identity: R02Identity
    selector_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scripted_transport_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: R02SelectorResponseStatus
    parsed_response: R02SelectorResponsePayload | None = None
    validation_error_codes: tuple[str, ...] = ()
    model_identity_evidence: R02ModelIdentityEvidence

    @model_validator(mode="after")
    def validate_response_status(self) -> "R02SelectorResponseRecord":
        if self.status is R02SelectorResponseStatus.VALID:
            if self.parsed_response is None or self.validation_error_codes:
                raise ValueError("valid selector response requires one parsed payload")
        elif self.parsed_response is not None or not self.validation_error_codes:
            raise ValueError("invalid selector response requires typed errors and no payload")
        if len(self.validation_error_codes) != len(set(self.validation_error_codes)):
            raise ValueError("selector response error codes must be unique")
        return self


class R02AcceptanceGate(StrictModel):
    schema_version: Literal["r02-acceptance-gate-v1"] = "r02-acceptance-gate-v1"
    identity: R02Identity
    selector_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selector_response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: R02AcceptanceStatus
    selected_presented_id: str | None = Field(default=None, pattern=r"^P[0-9]{2}$")
    selected_canonical_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    validation_report: ValidationReport | None = None
    validation_report_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    error_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_gate(self) -> "R02AcceptanceGate":
        if self.status is R02AcceptanceStatus.ACCEPTED:
            if self.selected_presented_id is None or self.selected_canonical_id is None:
                raise ValueError("accepted selection requires both candidate identities")
            if self.validation_report is None or self.validation_report_sha256 is None:
                raise ValueError("accepted selection requires deterministic validation")
            if self.error_codes:
                raise ValueError("accepted selection cannot retain error codes")
            if not self.validation_report.raw_valid or self.validation_report.fell_back:
                raise ValueError("accepted selection must be raw-valid without fallback")
            if self.validation_report_sha256 != canonical_sha256(self.validation_report):
                raise ValueError("acceptance validation-report hash mismatch")
        else:
            if not self.error_codes:
                raise ValueError("rejected selection requires typed error codes")
            if (self.validation_report is None) != (self.validation_report_sha256 is None):
                raise ValueError("rejected validation report and hash must be paired")
            if (
                self.validation_report is not None
                and self.validation_report_sha256
                != canonical_sha256(self.validation_report)
            ):
                raise ValueError("rejected validation-report hash mismatch")
        return self


class R02BaselineFallbackRecord(StrictModel):
    schema_version: Literal["r02-baseline-fallback-v1"] = (
        "r02-baseline-fallback-v1"
    )
    identity: R02Identity
    acceptance_gate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason_code: R02FallbackReason
    selected_presented_id: str | None = Field(default=None, pattern=r"^P[0-9]{2}$")
    selected_canonical_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    baseline_canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_batch: R02CandidateBatch

    @model_validator(mode="after")
    def validate_baseline_identity(self) -> "R02BaselineFallbackRecord":
        if self.baseline_canonical_candidate_id != _candidate_id(self.baseline_batch):
            raise ValueError("fallback baseline candidate identity mismatch")
        return self


class R02TriggeredExecutionDecision(StrictModel):
    schema_version: Literal["r02-triggered-execution-decision-v1"] = (
        "r02-triggered-execution-decision-v1"
    )
    identity: R02Identity
    acceptance_gate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_presented_id: str | None = Field(default=None, pattern=r"^P[0-9]{2}$")
    selected_canonical_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    executed_canonical_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    acceptance_disposition: Literal[
        "SELECTED_CANDIDATE_ACCEPTED",
        "BASELINE_FALLBACK",
    ]
    baseline_fallback: bool
    executable_batch: R02CandidateBatch
    validation_report: ValidationReport

    @model_validator(mode="after")
    def validate_execution(self) -> "R02TriggeredExecutionDecision":
        if self.executed_canonical_id != _candidate_id(self.executable_batch):
            raise ValueError("triggered execution candidate identity mismatch")
        if not self.validation_report.raw_valid or self.validation_report.fell_back:
            raise ValueError("triggered execution must use a raw-valid non-fallback batch")
        if self.baseline_fallback != (
            self.acceptance_disposition == "BASELINE_FALLBACK"
        ):
            raise ValueError("triggered execution fallback disposition mismatch")
        if not self.baseline_fallback and (
            self.selected_presented_id is None
            or self.selected_canonical_id != self.executed_canonical_id
        ):
            raise ValueError("accepted execution must preserve selected candidate identity")
        return self


class R02TriggeredEpisodeResult(StrictModel):
    schema_version: Literal["r02-triggered-episode-result-v1"] = (
        "r02-triggered-episode-result-v1"
    )
    identity: R02Identity
    execution_decision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_score: EpisodeScore
    executed_score: EpisodeScore
    paired_utility_delta_e12: int
    scripted_attempt_count: int = Field(ge=1)
    external_provider_calls: Literal[0] = 0
    audit_disposition: Literal["SCRIPTED_SELECTOR_OFFLINE"] = (
        "SCRIPTED_SELECTOR_OFFLINE"
    )

    @model_validator(mode="after")
    def validate_delta(self) -> "R02TriggeredEpisodeResult":
        expected = self.executed_score.utility_e12 - self.baseline_score.utility_e12
        if self.paired_utility_delta_e12 != expected:
            raise ValueError("paired utility delta arithmetic mismatch")
        return self


class R02SelectionRun(StrictModel):
    schema_version: Literal["r02-scripted-selection-run-v1"] = (
        "r02-scripted-selection-run-v1"
    )
    identity: R02Identity
    preparation: R02ProviderFreePreparation
    selector_request: R02SelectorRequest
    raw_response: str
    token_ledger: R02SelectorTokenLedger
    scripted_transport: R02ScriptedTransportRecord
    selector_response: R02SelectorResponseRecord
    acceptance_gate: R02AcceptanceGate
    baseline_fallback: R02BaselineFallbackRecord | None = None
    execution_decision: R02TriggeredExecutionDecision
    episode_result: R02TriggeredEpisodeResult
    external_provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False

    @model_validator(mode="after")
    def validate_run_graph(self) -> "R02SelectionRun":
        if self.preparation.state is not R02PreparationState.SELECTOR_ELIGIBLE_NOT_CALLED:
            raise ValueError("scripted selection requires an eligible D2a preparation")
        components = (
            self.preparation.identity,
            self.selector_request.identity,
            self.token_ledger.identity,
            self.scripted_transport.identity,
            self.selector_response.identity,
            self.acceptance_gate.identity,
            self.execution_decision.identity,
            self.episode_result.identity,
        )
        if any(identity != self.identity for identity in components):
            raise ValueError("scripted selection component identity mismatch")
        request_sha256 = canonical_sha256(self.selector_request)
        ledger_sha256 = canonical_sha256(self.token_ledger)
        transport_sha256 = canonical_sha256(self.scripted_transport)
        response_sha256 = canonical_sha256(self.selector_response)
        acceptance_sha256 = canonical_sha256(self.acceptance_gate)
        execution_sha256 = canonical_sha256(self.execution_decision)
        candidate_set_sha256 = canonical_sha256(self.preparation.candidate_set)
        permutation_sha256 = canonical_sha256(self.preparation.permutation)
        raw_sha256 = hashlib.sha256(self.raw_response.encode("utf-8")).hexdigest()
        if self.selector_request.candidate_permutation_sha256 != permutation_sha256:
            raise ValueError("selector request permutation reference mismatch")
        if self.scripted_transport.selector_request_sha256 != request_sha256:
            raise ValueError("transport request reference mismatch")
        if self.scripted_transport.command_spec_sha256 != canonical_sha256(
            self.selector_request.command_spec
        ):
            raise ValueError("transport command-spec reference mismatch")
        if self.scripted_transport.token_ledger_sha256 != ledger_sha256:
            raise ValueError("transport token-ledger reference mismatch")
        if self.scripted_transport.raw_response_sha256 != raw_sha256:
            raise ValueError("transport raw-response reference mismatch")
        if self.selector_response.selector_request_sha256 != request_sha256:
            raise ValueError("selector response request reference mismatch")
        if self.selector_response.scripted_transport_sha256 != transport_sha256:
            raise ValueError("selector response transport reference mismatch")
        if self.selector_response.raw_response_sha256 != raw_sha256:
            raise ValueError("selector response raw bytes mismatch")
        if self.acceptance_gate.selector_request_sha256 != request_sha256:
            raise ValueError("acceptance request reference mismatch")
        if self.acceptance_gate.selector_response_sha256 != response_sha256:
            raise ValueError("acceptance response reference mismatch")
        if self.acceptance_gate.candidate_set_sha256 != candidate_set_sha256:
            raise ValueError("acceptance candidate-set reference mismatch")
        if self.execution_decision.acceptance_gate_sha256 != acceptance_sha256:
            raise ValueError("execution acceptance reference mismatch")
        if self.episode_result.execution_decision_sha256 != execution_sha256:
            raise ValueError("episode result execution reference mismatch")
        if self.episode_result.scripted_attempt_count != self.token_ledger.scripted_attempts_after:
            raise ValueError("episode result attempt counter mismatch")
        fallback_expected = self.acceptance_gate.status is R02AcceptanceStatus.REJECTED
        if (self.baseline_fallback is not None) != fallback_expected:
            raise ValueError("fallback node presence mismatch")
        if self.execution_decision.baseline_fallback != fallback_expected:
            raise ValueError("execution fallback state mismatch")
        if self.baseline_fallback is not None:
            if self.baseline_fallback.identity != self.identity:
                raise ValueError("fallback identity mismatch")
            if self.baseline_fallback.acceptance_gate_sha256 != acceptance_sha256:
                raise ValueError("fallback acceptance reference mismatch")
            baseline = self.preparation.candidate_set.candidates[0]
            if (
                self.baseline_fallback.baseline_canonical_candidate_id
                != baseline.canonical_candidate_id
            ):
                raise ValueError("fallback does not execute frozen BASELINE")
        return self


class R02SelectionAuditGraph(StrictModel):
    schema_version: Literal["r02-selection-audit-graph-v1"] = (
        "r02-selection-audit-graph-v1"
    )
    identity: R02Identity
    node_types: tuple[str, ...]
    nodes: tuple[ArtifactReference, ...]
    external_provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    terminal: Literal[True] = True

    @model_validator(mode="after")
    def validate_selection_graph(self) -> "R02SelectionAuditGraph":
        if len(self.node_types) != len(self.nodes):
            raise ValueError("selection graph node types and references must align")
        if len(set(self.node_types)) != len(self.node_types):
            raise ValueError("selection graph node types must be unique")
        base = (
            "public_fixture",
            "eligibility_decision",
            "candidate_set",
            "candidate_permutation",
            "preparation",
            "selector_request",
            "selector_token_ledger",
            "selector_transport",
            "selector_raw_response",
            "selector_response",
            "acceptance_gate",
        )
        suffix = (
            "baseline_fallback",
            "execution_decision",
            "episode_result",
            "selection_run",
        ) if "baseline_fallback" in self.node_types else (
            "execution_decision",
            "episode_result",
            "selection_run",
        )
        if self.node_types != (*base, *suffix):
            raise ValueError("selection graph node order mismatch")
        if len({node.relative_path for node in self.nodes}) != len(self.nodes):
            raise ValueError("selection graph paths must be unique")
        return self


class R02PersistedSelectionRun(StrictModel):
    schema_version: Literal["r02-persisted-selection-run-v1"] = (
        "r02-persisted-selection-run-v1"
    )
    selection_run: ArtifactReference
    audit_graph: ArtifactReference


class R02SelectionReplayVerification(StrictModel):
    schema_version: Literal["r02-selection-replay-verification-v1"] = (
        "r02-selection-replay-verification-v1"
    )
    identity: R02Identity
    verified_artifacts: int = Field(ge=1)
    external_provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    all_hashes_match: Literal[True] = True
    selector_request_reproduced: Literal[True] = True
    selector_response_reproduced: Literal[True] = True
    acceptance_reproduced: Literal[True] = True
    execution_reproduced: Literal[True] = True
    paired_delta_reproduced: Literal[True] = True
