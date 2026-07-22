"""Strict R03 contracts and numeric identity rules.

The models deliberately reuse R02's frozen ``StrictModel`` and canonical JSON
helpers.  Economic values cross contract boundaries as e12 integers.  Model
internals may use finite binary64 values whose normative identity is their
normalized IEEE-754 bit pattern.
"""

from __future__ import annotations

import math
import struct
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from v2.research.overlay.canonical import canonical_json_bytes, canonical_sha256
from v2.research.overlay.contracts import StrictModel

PLAN_COMMIT = "6da16688b3da581d1a919d7c75e285827ed10e85"
R03_IMPLEMENTATION_STATUS = "CODE_ONLY_AUTHORIZED_DATA_AND_INFERENCE_NO_GO"
UTILITY_SCALE = 10**12
ARTICLE_BYTE_CAP = 32_768
TICKER_SESSION_BYTE_CAP = 131_072
DELTA_STAR_E12 = 500_000_000
SHA256_PATTERN = r"^[0-9a-f]{64}$"

# Normative additive amendment:
# docs/r03-news-reasoning-g2-gate-interpretation-amendment.md
# sha256: 5a2cdae55cf83da37fda6fe64ba9067a0e8cce354a29ff834ff9e3450421fbbe
R03_G2_INCREMENTAL_PRIMARY_GATE_RULE = "SEALED_UPPER_95_BOUND_OF_U_T2_MINUS_U_T0_VERSUS_DELTA_STAR_IS_SOLE_GATE_" "PASS_IS_NON_PAUSE_FAIL_IS_SEALED_PAUSE_NOT_EFFICACY_V1"
R03_G2_ABSOLUTE_PROFITABILITY_FLAG_RULE = "SECONDARY_RECORDED_SIGN_OF_U_T2_POINT_ESTIMATE_WITH_ONE_SIDED_BOUND_VERSUS_" "ZERO_PER_REGISTERED_COST_CELL_REPORT_ONLY_NEVER_GATE_BEARING_V1"
R03_G2_LOSES_LESS_INTERPRETATION_RULE = "INCREMENTAL_PASS_WITH_T2_ABSOLUTE_PROFITABILITY_NEGATIVE_MEANS_LOSES_LESS_" "OVER_LOSING_BASELINE_NOT_PROFITABILITY_AND_MUST_NOT_BE_CITED_AS_MAKING_MONEY_V1"


class R03ContractError(ValueError):
    """Raised when a sealed R03 contract cannot be constructed or replayed."""


class R03PinKind(StrEnum):
    GIT_BLOB_SHA256 = "git_blob_sha256"
    NORMALIZED_LF_SHA256 = "normalized_lf_sha256"
    CANONICAL_JSON_SHA256 = "canonical_json_sha256"
    FILESYSTEM_SHA256 = "filesystem_sha256"
    AGGREGATE_INVENTORY_SHA256 = "aggregate_inventory_sha256"


class R03GateLabel(StrEnum):
    G1_CONTINUE = "G1_CONTINUE_NO_FUTILITY_PROOF"
    G1_STOP = "STOP_NO_ECONOMIC_HEADROOM"
    G1_INVALID = "G1_INVALID_NO_DECISION"
    G2_CONTINUE = "G2_CONTINUE_CHEAP_TEXT_SUPPORT"
    G2_PAUSE = "PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION"
    G2_USER_STOP = "STOP_BUDGET_FUTILITY_USER_RATIFIED"
    G2_USER_CONTINUE = "CONTINUE_AFTER_G2_PAUSE_USER_RATIFIED"
    G3_CONTINUE = "G3_CONTINUE_POWER_ADEQUATE"
    G3_STOP = "STOP_UNDERPOWERED"
    G3_INVALID = "G3_INVALID_NO_DECISION"


class R03G2IncrementalAxis(StrEnum):
    """Sealed-label projection; PASS is a non-pause, not efficacy evidence."""

    G2_INCREMENTAL_PASS = "G2_INCREMENTAL_PASS"
    G2_INCREMENTAL_FAIL = "G2_INCREMENTAL_FAIL"


class R03T2AbsoluteProfitabilityFlag(StrEnum):
    T2_ABSOLUTE_PROFITABILITY_POSITIVE = "T2_ABSOLUTE_PROFITABILITY_POSITIVE"
    T2_ABSOLUTE_PROFITABILITY_NEGATIVE = "T2_ABSOLUTE_PROFITABILITY_NEGATIVE"


class R03AuthorityState(StrEnum):
    PLAN_REVIEWED = "PLAN_REVIEWED"
    CODE_ONLY_AUTHORIZED = "CODE_ONLY_AUTHORIZED"
    CODE_ONLY_ACCEPTED = "CODE_ONLY_ACCEPTED"
    READ_ONLY_DATA_CHECK_AUTHORIZED = "READ_ONLY_DATA_CHECK_AUTHORIZED"
    FRAME_MATERIALIZATION_AUTHORIZED = "FRAME_MATERIALIZATION_AUTHORIZED"
    G1_G2_G3_EXECUTION_AUTHORIZED = "G1_G2_G3_EXECUTION_AUTHORIZED"
    PROSPECTIVE_D_DESIGN_AUTHORIZED = "PROSPECTIVE_D_DESIGN_AUTHORIZED"
    LOCAL_T3_INFERENCE_AUTHORIZED = "LOCAL_T3_INFERENCE_AUTHORIZED"
    EXTERNAL_PROVIDER_AUTHORIZED = "EXTERNAL_PROVIDER_AUTHORIZED"


def require_aware(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise R03ContractError(f"{field} must be timezone-aware")
    return value


def float64_hex(value: float) -> str:
    """Return normative normalized binary64 identity."""

    value = float(value)
    if not math.isfinite(value):
        raise R03ContractError("binary64 value must be finite")
    if value == 0.0:
        value = 0.0
    return struct.pack(">d", value).hex()


def float64_from_hex(value: str) -> float:
    if len(value) != 16 or any(ch not in "0123456789abcdef" for ch in value):
        raise R03ContractError("binary64 identity must be 16 lowercase hex digits")
    result = struct.unpack(">d", bytes.fromhex(value))[0]
    if not math.isfinite(result):
        raise R03ContractError("binary64 identity decodes to a non-finite value")
    return 0.0 if result == 0.0 else result


def e12_from_float(value: float) -> int:
    """Convert one finite binary64 value to e12 with decimal half-even rounding."""

    value = float(value)
    if not math.isfinite(value):
        raise R03ContractError("e12 conversion requires a finite value")
    quantized = Decimal.from_float(value).quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN)
    return int(quantized * UTILITY_SCALE)


def mean_e12(values: tuple[int, ...] | list[int]) -> int:
    if not values:
        raise R03ContractError("mean_e12 requires at least one value")
    numerator = Decimal(sum(values))
    return int((numerator / Decimal(len(values))).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


class R03HashPin(StrictModel):
    sha256: str = Field(pattern=SHA256_PATTERN)
    pin_kind: R03PinKind


class R03SourceDescriptor(StrictModel):
    schema_version: Literal["r03-source-descriptor-v1"] = "r03-source-descriptor-v1"
    root_identity: R03HashPin
    all_json_sha256: str = Field(pattern=SHA256_PATTERN)
    page_sha256: str = Field(pattern=SHA256_PATTERN)
    manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    json_file_count: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    page_count: int = Field(ge=0)
    manifest_count: int = Field(ge=0)


class R03ArticleRecord(StrictModel):
    article_id: str = Field(min_length=1, max_length=256)
    created_at: datetime
    updated_at: datetime
    symbols: tuple[str, ...] = Field(min_length=1)
    source: str | None = Field(default=None, max_length=512)
    headline: str | None = None
    summary: str | None = None
    content: str | None = None
    input_text_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_record(self) -> "R03ArticleRecord":
        require_aware(self.created_at, "created_at")
        require_aware(self.updated_at, "updated_at")
        if len(set(self.symbols)) != len(self.symbols):
            raise R03ContractError("symbols must be distinct")
        if tuple(sorted(self.symbols)) != self.symbols:
            raise R03ContractError("symbols must be sorted")
        return self

    @property
    def available_at(self) -> datetime:
        return max(self.created_at, self.updated_at)


class R03CanonicalArticle(StrictModel):
    article_id: str
    available_at: datetime
    symbols: tuple[str, ...]
    source: str | None
    headline: str
    summary: str | None
    content: str | None
    summary_present: bool
    content_present: bool
    content_truncated: bool

    @model_validator(mode="after")
    def validate_article(self) -> "R03CanonicalArticle":
        require_aware(self.available_at, "available_at")
        if not self.headline:
            raise R03ContractError("canonical article requires a headline")
        if self.summary_present != (self.summary is not None):
            raise R03ContractError("summary_present mismatch")
        if self.content_present != (self.content is not None):
            raise R03ContractError("content_present mismatch")
        return self


class R03CanonicalBundle(StrictModel):
    schema_version: Literal["r03-canonical-news-bundle-v1"] = "r03-canonical-news-bundle-v1"
    ticker: str = Field(min_length=1, max_length=32)
    decision_at: datetime
    article_byte_cap: Literal[ARTICLE_BYTE_CAP] = ARTICLE_BYTE_CAP
    ticker_session_byte_cap: Literal[TICKER_SESSION_BYTE_CAP] = TICKER_SESSION_BYTE_CAP
    articles: tuple[R03CanonicalArticle, ...]
    text_bytes: int = Field(ge=0, le=TICKER_SESSION_BYTE_CAP)
    payload_bytes: int = Field(ge=0)
    payload_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_bundle(self) -> "R03CanonicalBundle":
        require_aware(self.decision_at, "decision_at")
        keys = [(a.available_at, a.article_id) for a in self.articles]
        expected = sorted(keys, key=lambda item: (-item[0].timestamp(), item[1]))
        if keys != expected:
            raise R03ContractError("articles are not in canonical order")
        return self


class R03SplitRecord(StrictModel):
    name: Literal["DEVELOPMENT", "PURGE_1", "CALIBRATION", "PURGE_2", "PROCEDURAL_OOS", "LABEL_ONLY"]
    start: date
    end: date
    session_count: int = Field(gt=0)
    permitted_use: Literal["FIT_SELECT", "PURGE", "CALIBRATION_GATE", "SEALED_OOS", "LABEL_ONLY"]

    @model_validator(mode="after")
    def validate_dates(self) -> "R03SplitRecord":
        if self.end < self.start:
            raise R03ContractError("split end precedes start")
        return self


class R03FrameRow(StrictModel):
    decision_id: str
    ticker: str
    sector: str
    decision_at: datetime
    feature_cutoff_at: datetime
    label_maturity_at: datetime
    phase_book: int = Field(ge=0, le=4)
    payload_sha256: str = Field(pattern=SHA256_PATTERN)
    outcome_e12: int | None = None

    @model_validator(mode="after")
    def validate_temporal_order(self) -> "R03FrameRow":
        require_aware(self.decision_at, "decision_at")
        require_aware(self.feature_cutoff_at, "feature_cutoff_at")
        require_aware(self.label_maturity_at, "label_maturity_at")
        if self.feature_cutoff_at >= self.decision_at:
            raise R03ContractError("feature cutoff must precede decision")
        if self.label_maturity_at <= self.decision_at:
            raise R03ContractError("label maturity must follow decision")
        return self


class R03TierConfig(StrictModel):
    tier: Literal["T0", "T1", "T2", "T3_CONTRACT_ONLY"]
    config_sha256: str = Field(pattern=SHA256_PATTERN)
    canonical_schema_sha256: str = Field(pattern=SHA256_PATTERN)
    payload_sha256: str = Field(pattern=SHA256_PATTERN)


class R03TrainingFrameIdentity(StrictModel):
    split_sha256: str = Field(pattern=SHA256_PATTERN)
    training_frame_sha256: str = Field(pattern=SHA256_PATTERN)
    feature_frame_sha256: str = Field(pattern=SHA256_PATTERN)
    label_frame_sha256: str = Field(pattern=SHA256_PATTERN)
    maximum_source_at: datetime
    maximum_label_maturity_at: datetime
    fit_cutoff_at: datetime

    @model_validator(mode="after")
    def validate_cutoffs(self) -> "R03TrainingFrameIdentity":
        for field in ("maximum_source_at", "maximum_label_maturity_at", "fit_cutoff_at"):
            require_aware(getattr(self, field), field)
        if self.maximum_source_at > self.fit_cutoff_at:
            raise R03ContractError("source timestamp exceeds fit cutoff")
        if self.maximum_label_maturity_at > self.fit_cutoff_at:
            raise R03ContractError("unmatured label included in training frame")
        return self


class R03T2ModelIdentity(StrictModel):
    schema_version: Literal["r03-t2-model-identity-v1"] = "r03-t2-model-identity-v1"
    python_version: str
    numpy_version: str
    scipy_version: str
    scikit_learn_version: str
    hashing_vectorizer_id: str
    tfidf_transformer_id: str
    ridge_implementation_id: str
    solver: Literal["lsqr"] = "lsqr"
    solver_tolerance_hex: str = Field(pattern=r"^[0-9a-f]{16}$")
    solver_max_iterations: Literal[10000] = 10000
    blas_lapack_identity: str
    canonical_schema_sha256: str = Field(pattern=SHA256_PATTERN)
    payload_sha256: str = Field(pattern=SHA256_PATTERN)
    training_frame_sha256: str = Field(pattern=SHA256_PATTERN)
    split_sha256: str = Field(pattern=SHA256_PATTERN)
    feature_config_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_alpha: Literal[1, 10, 100, 1000]
    prediction_clip_low_hex: str = Field(pattern=r"^[0-9a-f]{16}$")
    prediction_clip_high_hex: str = Field(pattern=r"^[0-9a-f]{16}$")
    fitted_parameter_sha256: str = Field(pattern=SHA256_PATTERN)
    model_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_model_hash(self) -> "R03T2ModelIdentity":
        unsigned = self.model_dump(mode="json", exclude={"model_sha256"})
        if canonical_sha256(unsigned) != self.model_sha256:
            raise R03ContractError("T2 model identity hash mismatch")
        low = float64_from_hex(self.prediction_clip_low_hex)
        high = float64_from_hex(self.prediction_clip_high_hex)
        if low > high:
            raise R03ContractError("prediction clip bounds reversed")
        return self


class R03BoundCertificate(StrictModel):
    schema_version: Literal["r03-g1-bound-certificate-v1"] = "r03-g1-bound-certificate-v1"
    contract_name: Literal["G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1"] = "G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1"
    decision_id: str
    valid_name_set_sha256: str = Field(pattern=SHA256_PATTERN)
    sorted_return_order_sha256: str = Field(pattern=SHA256_PATTERN)
    long_tickers: tuple[str, ...]
    short_tickers: tuple[str, ...]
    bound_e12: int
    certificate_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_certificate_shape_and_hash(self) -> "R03BoundCertificate":
        if len(self.long_tickers) not in (0, 10) or len(self.short_tickers) not in (0, 10):
            raise R03ContractError("G1 legs must both be empty or both contain ten names")
        if set(self.long_tickers) & set(self.short_tickers):
            raise R03ContractError("G1 legs overlap")
        if bool(self.long_tickers) != bool(self.short_tickers):
            raise R03ContractError("G1 legs must share no-trade state")
        unsigned = self.model_dump(mode="json", exclude={"certificate_sha256"})
        if canonical_sha256(unsigned) != self.certificate_sha256:
            raise R03ContractError("G1 certificate hash mismatch")
        return self


class R03GateResult(StrictModel):
    gate: Literal["G1", "G2", "G3"]
    label: R03GateLabel
    point_estimate_e12: int | None
    upper_95_e12: int | None
    lower_95_e12: int | None
    seed_sha256: str = Field(pattern=SHA256_PATTERN)
    input_sha256: str = Field(pattern=SHA256_PATTERN)
    result_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_result_hash(self) -> "R03GateResult":
        unsigned = self.model_dump(mode="json", exclude={"result_sha256"})
        if canonical_sha256(unsigned) != self.result_sha256:
            raise R03ContractError("gate result hash mismatch")
        return self


class R03G2GateResult(StrictModel):
    """Two-axis G2 record under the pinned additive amendment.

    ``G2_INCREMENTAL_PASS`` is only a futility/budget-governance non-pause. It is
    not evidence that news, text, or LLM reasoning is effective or profitable.
    The absolute-profitability flag is report-only and never gate-bearing.
    """

    gate: Literal["G2"] = "G2"
    label: R03GateLabel
    incremental_axis: R03G2IncrementalAxis
    absolute_profitability_flag: R03T2AbsoluteProfitabilityFlag
    point_estimate_e12: int
    upper_95_e12: int
    lower_95_e12: int
    t2_absolute_point_estimate_e12: int
    t2_absolute_lower_95_e12: int
    seed_sha256: str = Field(pattern=SHA256_PATTERN)
    input_sha256: str = Field(pattern=SHA256_PATTERN)
    incremental_primary_gate_rule: str = R03_G2_INCREMENTAL_PRIMARY_GATE_RULE
    absolute_profitability_flag_rule: str = R03_G2_ABSOLUTE_PROFITABILITY_FLAG_RULE
    loses_less_interpretation_rule: str = R03_G2_LOSES_LESS_INTERPRETATION_RULE
    result_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_two_axis_result_and_hash(self) -> "R03G2GateResult":
        expected_incremental = {
            R03GateLabel.G2_CONTINUE: R03G2IncrementalAxis.G2_INCREMENTAL_PASS,
            R03GateLabel.G2_PAUSE: R03G2IncrementalAxis.G2_INCREMENTAL_FAIL,
        }.get(self.label)
        if expected_incremental is None or self.incremental_axis != expected_incremental:
            raise R03ContractError("G2 incremental axis must map from the sealed label")
        expected_absolute = R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_POSITIVE if self.t2_absolute_point_estimate_e12 > 0 else R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_NEGATIVE
        if self.absolute_profitability_flag != expected_absolute:
            raise R03ContractError("G2 absolute-profitability flag must map from the T2 point estimate")
        expected_rules = (
            R03_G2_INCREMENTAL_PRIMARY_GATE_RULE,
            R03_G2_ABSOLUTE_PROFITABILITY_FLAG_RULE,
            R03_G2_LOSES_LESS_INTERPRETATION_RULE,
        )
        actual_rules = (
            self.incremental_primary_gate_rule,
            self.absolute_profitability_flag_rule,
            self.loses_less_interpretation_rule,
        )
        if actual_rules != expected_rules:
            raise R03ContractError("G2 amendment rule binding mismatch")
        unsigned = self.model_dump(mode="json", exclude={"result_sha256"})
        if canonical_sha256(unsigned) != self.result_sha256:
            raise R03ContractError("G2 gate result hash mismatch")
        return self


class R03T3Reason(StrictModel):
    code: str = Field(min_length=1, max_length=64)
    field_refs: tuple[str, ...] = Field(min_length=1, max_length=8)


class R03T3Response(StrictModel):
    schema_version: Literal["r03-t3-response-contract-v1"] = "r03-t3-response-contract-v1"
    ticker: str
    score_hex: str = Field(pattern=r"^[0-9a-f]{16}$")
    confidence: int = Field(ge=0, le=100)
    reasons: tuple[R03T3Reason, ...] = Field(min_length=1, max_length=4)


class R03ZeroCounters(StrictModel):
    provider_calls: Literal[0] = 0
    local_inference_calls: Literal[0] = 0
    network_attempts: Literal[0] = 0
    model_downloads: Literal[0] = 0
    raw_source_opens: Literal[0] = 0
    fixture_materializations: Literal[0] = 0
    frame_materializations: Literal[0] = 0
    research_gate_executions: Literal[0] = 0
    oos_accesses: Literal[0] = 0


def contract_schema_bundle() -> dict[str, Any]:
    models = (
        R03SourceDescriptor,
        R03ArticleRecord,
        R03CanonicalBundle,
        R03SplitRecord,
        R03FrameRow,
        R03TierConfig,
        R03TrainingFrameIdentity,
        R03T2ModelIdentity,
        R03BoundCertificate,
        R03GateResult,
        R03G2GateResult,
        R03T3Response,
        R03ZeroCounters,
    )
    return {model.__name__: model.model_json_schema() for model in models}


def contract_schema_sha256() -> str:
    return canonical_sha256(contract_schema_bundle())


def canonical_model_bytes(value: StrictModel) -> bytes:
    return canonical_json_bytes(value.model_dump(mode="json"))
