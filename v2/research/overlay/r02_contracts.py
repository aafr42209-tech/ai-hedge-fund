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

from .canonical import canonical_sha256
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
