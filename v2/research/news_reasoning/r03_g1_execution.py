"""Synthetic-safe preparation contracts for the R03 G1 calibration gate.

This module deliberately has no file, raw-news, provider, network, subprocess,
or OOS capability.  It freezes the T0 numerical/refit protocol and produces
only in-memory identities or aggregate G1 results.  Historical materialization,
development fitting, and calibration execution require separate authority.
"""

from __future__ import annotations

import hashlib
import math
import platform
import struct
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from os import environ
from typing import Literal

from pydantic import Field, model_validator

from v2.research.overlay.canonical import canonical_sha256, sha256_hex
from v2.research.overlay.contracts import StrictModel

T0_BASE_FEATURES = (
    "sector_relative_log_return_5",
    "sector_relative_log_return_20",
    "sector_relative_log_return_60",
    "volatility_20",
    "volatility_60",
    "downside_semideviation_20",
    "sector_beta_60",
    "mean_log_dollar_volume_20",
    "volume_shock_5_vs_20",
)
T0_DESIGN_COLUMNS = tuple(column for feature in T0_BASE_FEATURES for column in (feature, f"{feature}_missing"))
T0_ALPHA_E1_GRID = (1, 10, 100, 1000)
T0_FOLD_END_YEARS = (2017, 2018, 2019, 2020)
T0_COST_CELLS_BPS = (5, 10, 15)
T0_SELECTION_CELLS = tuple(f"fold_end={fold}|cost_bps={cost}" for fold in T0_FOLD_END_YEARS for cost in T0_COST_CELLS_BPS)
T0_CANDIDATE_RUN_ORDER = tuple(f"alpha_e1={alpha}|fold_end={fold}" for alpha in T0_ALPHA_E1_GRID for fold in T0_FOLD_END_YEARS)
T0_REFIT_PROTOCOL = "MONTHLY_EXPANDING_FIXED_ALPHA_MATURED_LABELS_ONLY_V1"
T0_SOLVER_CONTRACT = "SCIPY_CHOLESKY_NORMAL_EQUATION_FLOAT64_V1:" "SUM_SQUARED_ERROR_PLUS_ALPHA_L2:NO_SAMPLE_NORMALIZATION:" "UNPENALIZED_INTERCEPT:TRAIN_ROWS_CENTER_ONLY:ASSUME_A_POS:NO_FALLBACK"
T0_ALPHA_SELECTION_RULE = "MAXIMIZE_MIN_OVER_FOLD_X_COST_THEN_LARGER_T0_ALPHA_E1"
T0_EXECUTION_STATUS = "BLOCKED_PENDING_SEPARATE_EXECUTION_AUTHORITY"
G1_SEED_DOMAIN = "R03_G1_STATIONARY_BOOTSTRAP_V1"
G1_BOOTSTRAP_PRIMITIVE = "R03_HEADROOM_STATIONARY_BOOTSTRAP_MEANS_E12_V1"
G1_BOOTSTRAP_DOMAIN_SEED_RULE = "SHA256_SEED_BYTES_CONCAT_LABEL_UTF8_NO_SEPARATOR_FIRST_16_BYTES_BIG_ENDIAN"
G1_GOVERNING_COST_CELL_RULE = "MAX_UPPER_95_THEN_LARGER_COST_BPS"
G1_GATE_RECONCILIATION_RULE = "ZERO_COST_TIME_DECOUPLED_SORTING_RELAXATION_MINUS_IDENTICAL_B0_T0_GOVERNS_STOP_GREEDY_COST_BEARING_FEASIBLE_BRACKET_DIAGNOSTIC_ONLY_V1"
G1_PRE_EXECUTION_POWER_PREDICTION_RULE = "CONFIGURED_G1_EXPECTED_TO_RETURN_CONTINUE_WITH_NEAR_CERTAINTY_INSTRUMENT_PROPERTY_NOT_FINDING_V1"
G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE = "G1_CONTINUE_NOT_SUPPORT_FOR_NEWS_TEXT_OR_LLM_CONTRIBUTION_AND_MUST_NOT_BE_CITED_AS_SUCH_V1"
G1_SANDWICH_REPORTING_RULE = "REPORT_GREEDY_COST_BEARING_LOWER_AND_ZERO_COST_TIME_DECOUPLED_POINT_AND_UPPER_95_WITH_DECISION_BAND_WIDTH_AND_BAND_UNDETERMINED_BY_COST_CELL_V1"
G1_BOUND_CERTIFICATE_DECISION_ID_RULE = "CALIBRATION_PIPE_DECISION_ORDINAL_06D_PIPE_DECISION_DATE_YYYY_MM_DD_V1"
G1_BOUND_CERTIFICATE_ROOT_RULE = "CANONICAL_SHA256_ORDERED_TUPLE_OF_PER_DECISION_CERTIFICATE_SHA256_IN_DECISION_ORDER_V1"
G1_STAGE2_ASSET_ACCESS_RULE = "EXECUTION_PATH_EXACT_RESOLVED_ABSOLUTE_PATH_MATCH_ONLY_NO_PREFIX_NO_RECURSION_TEST_DOUBLES_AND_INTEGRITY_HASH_INVENTORIES_OUT_OF_SCOPE_V2"
G1_SESSION_ORDINAL_RULE = "PINNED_MARKET_BAR_SESSION_ORDINALS_NOMINAL_1530_ET_EARLY_CLOSE_DEFERRED_TO_T2_T3"
G1_MARKET_UNIVERSE_TICKER_RULE = "EXACT_TICKER_SET_EQUALITY_MARKET_BARS_TO_PINNED_UNIVERSE_SNAPSHOT"
G1_GATE_RECONCILIATION_AMENDMENT_PATH = "docs/r03-news-reasoning-g1-gate-definition-reconciliation-amendment.md"
G1_GATE_RECONCILIATION_AMENDMENT_SHA256 = "47e42e2920fae2da6ef4c6383216e361dfcc524b4d8e519c2c40d4828d3fbdfe"
T0_FOLD_VALIDATION_WINDOW_RULE = "DEVELOPMENT_DECISION_SESSIONS_WITH_CALENDAR_YEAR_EQUAL_FOLD_END_YEAR_EXPANDING_STRICTLY_EARLIER_MATURED_HISTORY_BEFORE_EACH_MONTHLY_REFIT_V1"
T0_TIMESTAMP_RULE = "UTC_SESSION_DATE_NOMINAL_1530_AMERICA_NEW_YORK_DECISION_T_FEATURE_T_MINUS_1_LABEL_T_PLUS_5_V1"
T0_ROW_ID_RULE = "SPLIT_PIPE_DECISION_ORDINAL_06D_PIPE_DECISION_DATE_YYYY_MM_DD_PIPE_TICKER_V1"
T0_UNIVERSE_SOURCE_PATH = "C:/Users/User/Desktop/FinGPT/configs/universe.json"
T0_UNIVERSE_SOURCE_SHA256 = "3017ce3138887867ae238ece81dc7fa6db6c646014554cc07408abbd64b356fe"
T0_UNIVERSE_SNAPSHOT_PATH = ".research_artifacts/r03-news-reasoning/universe-snapshot-v1.json"
T0_UNIVERSE_SNAPSHOT_SHA256 = "66271aabbb787b2e8710dfeec2fa714ef9f1f757deaecf65c594f1b092b70201"
T0_UNIVERSE_SNAPSHOT_FILE_SHA256 = "c8a0793f5c37adf19f4a7d17f541bb10c50e6b598dc1d71027b24fda076bc818"
T0_FEATURE_FORMULA_CONTRACT = "R03_T0_FEATURE_FORMULA_AMENDMENT_V1"
T0_FEATURE_FORMULA_AMENDMENT_PATH = "docs/r03-news-reasoning-t0-feature-formula-amendment.md"
T0_FEATURE_FORMULA_AMENDMENT_SHA256 = "60fa138f6dc9670421428a30e331867cded809aae8a87eea10b9e7892022485c"
T0_RAW_FEATURE_FORMULA_RULE = "FLOAT64_LOG_RETURN_WINDOWS_SR_SUM_VOL_DDOF0_DOWNSIDE_ZERO_SEALED_SECTOR_BETA_EXPLICIT_DEPARTURE_TO_UNIVERSE_BETA_VALID_NAMES_MIN1_SPLIT_ADJUSTED_CLOSE_ASSUMED_UNCERTIFIED_LOG_DOLLAR_VOLUME_LOG_MEAN_VOLUME_RATIO_V2"
T0_LABEL_FORMULA_RULE = "H5_SIMPLE_RETURN_MINUS_SAME_SESSION_EQUAL_WEIGHT_SECTOR_MEAN_V1"
T0_RAW_MISSING_RULE = "COMPLETE_WINDOW_REQUIRED_INVALID_NONFINITE_OR_NONPOSITIVE_INPUT_AND_ZERO_BETA_DENOMINATOR_ARE_MISSING_V1"
G1_BLOCK_LENGTH = 10
G1_RESAMPLES = 10_000
DELTA_STAR_E12 = 500_000_000
UTILITY_SCALE = 10**12
SHA256_PATTERN = r"^[0-9a-f]{64}$"
COMMIT_SHA_PATTERN = r"^[0-9a-f]{40}$"
FLOAT64_HEX_PATTERN = r"^[0-9a-f]{16}$"
COEFFICIENT_HEX_PATTERN = rf"^[0-9a-f]{{{len(T0_DESIGN_COLUMNS) * 16}}}$"
THREAD_ENV_KEYS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
)
T0_THREAD_ENVIRONMENT_CONTRACT = "PRECONFIGURED_BEFORE_PROCESS_START"
PURGE_SPLITS = frozenset({"PURGE_1", "PURGE_2"})
R03_FLAKE8_EXTEND_IGNORE = ("E203",)
_T0_RUNTIME_CACHE = None


class R03G1PreparationError(ValueError):
    pass


def _require_aware(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise R03G1PreparationError(f"{field} must be timezone-aware")
    return value


def _utc_iso(value: datetime) -> str:
    _require_aware(value, "datetime")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _float64_hex(value: float) -> str:
    if not math.isfinite(value):
        raise R03G1PreparationError("non-finite float64 diagnostic")
    return struct.pack(">d", value).hex()


def _little_endian_float64_hex(value: float) -> str:
    if not math.isfinite(value):
        raise R03G1PreparationError("non-finite fitted parameter")
    return struct.pack("<d", value).hex()


def _little_endian_float64_from_hex(value: str) -> float:
    try:
        decoded = struct.unpack("<d", bytes.fromhex(value))[0]
    except (ValueError, struct.error) as exc:
        raise R03G1PreparationError("invalid little-endian float64 hex") from exc
    if not math.isfinite(decoded):
        raise R03G1PreparationError("non-finite fitted parameter")
    return decoded


def _float64_from_hex(value: str) -> float:
    try:
        decoded = struct.unpack(">d", bytes.fromhex(value))[0]
    except (ValueError, struct.error) as exc:
        raise R03G1PreparationError("invalid float64 diagnostic hex") from exc
    if not math.isfinite(decoded):
        raise R03G1PreparationError("non-finite float64 diagnostic")
    return decoded


def _mean_e12(values: Sequence[int]) -> int:
    if not values:
        raise R03G1PreparationError("mean requires a nonempty sequence")
    return int((Decimal(sum(values)) / Decimal(len(values))).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def t0_alpha_from_e1(t0_alpha_e1: int) -> float:
    if t0_alpha_e1 not in T0_ALPHA_E1_GRID:
        raise R03G1PreparationError("T0 alpha_e1 is outside the frozen grid")
    alpha = t0_alpha_e1 / 10.0
    if round(alpha * 10) != t0_alpha_e1:
        raise R03G1PreparationError("T0 alpha_e1 conversion mismatch")
    return alpha


class T0ProtocolIdentity(StrictModel):
    schema_version: Literal["r03-t0-protocol-identity-v2"] = "r03-t0-protocol-identity-v2"
    execution_status: Literal["BLOCKED_PENDING_SEPARATE_EXECUTION_AUTHORITY"] = T0_EXECUTION_STATUS
    base_features: tuple[str, ...]
    design_columns: tuple[str, ...]
    imputation: Literal["same_date_sector_then_universe_median"]
    clipping: Literal["same_date_cross_section_percentile_1_99_linear"]
    sector_demean: Literal[True] = True
    zscore_ddof: Literal[0] = 0
    zero_dispersion_value_e12: Literal[0] = 0
    missing_flags_unscaled: Literal[True] = True
    additional_scaling: Literal["NONE"] = "NONE"
    objective: Literal["SUM_SQUARED_ERROR_PLUS_ALPHA_L2_NO_SAMPLE_NORMALIZATION"] = "SUM_SQUARED_ERROR_PLUS_ALPHA_L2_NO_SAMPLE_NORMALIZATION"
    intercept: Literal["UNPENALIZED_TRAIN_ROWS_CENTER_ONLY"]
    solver_contract: Literal["SCIPY_CHOLESKY_NORMAL_EQUATION_FLOAT64_V1:SUM_SQUARED_ERROR_PLUS_ALPHA_L2:NO_SAMPLE_NORMALIZATION:UNPENALIZED_INTERCEPT:TRAIN_ROWS_CENTER_ONLY:ASSUME_A_POS:NO_FALLBACK"]
    t0_alpha_e1_grid: tuple[int, ...]
    fold_end_years: tuple[int, ...]
    cost_cells_bps: tuple[int, ...]
    selection_cells: tuple[str, ...]
    candidate_run_order: tuple[str, ...]
    alpha_selection_rule: Literal["MAXIMIZE_MIN_OVER_FOLD_X_COST_THEN_LARGER_T0_ALPHA_E1"]
    fold_validation_window_rule: Literal["DEVELOPMENT_DECISION_SESSIONS_WITH_CALENDAR_YEAR_EQUAL_FOLD_END_YEAR_EXPANDING_STRICTLY_EARLIER_MATURED_HISTORY_BEFORE_EACH_MONTHLY_REFIT_V1"]
    refit_protocol: Literal["MONTHLY_EXPANDING_FIXED_ALPHA_MATURED_LABELS_ONLY_V1"]
    timestamp_rule: Literal["UTC_SESSION_DATE_NOMINAL_1530_AMERICA_NEW_YORK_DECISION_T_FEATURE_T_MINUS_1_LABEL_T_PLUS_5_V1"]
    row_id_rule: Literal["SPLIT_PIPE_DECISION_ORDINAL_06D_PIPE_DECISION_DATE_YYYY_MM_DD_PIPE_TICKER_V1"]
    effective_interval: Literal["LEFT_CLOSED_RIGHT_OPEN"]
    label_rule: Literal["H5_MATURED_AT_OR_BEFORE_REFIT"]
    purge_decision_rows: Literal["ALWAYS_EXCLUDED"]
    calibration_alpha_reselection: Literal["FORBIDDEN"]
    arbitrary_refit: Literal["FORBIDDEN"]
    g2_t0_reuse: Literal["REQUIRE_IDENTICAL_T0_MODEL_SERIES_ID"]
    g1_bootstrap_primitive: Literal["R03_HEADROOM_STATIONARY_BOOTSTRAP_MEANS_E12_V1"]
    g1_bootstrap_domain_seed_rule: Literal["SHA256_SEED_BYTES_CONCAT_LABEL_UTF8_NO_SEPARATOR_FIRST_16_BYTES_BIG_ENDIAN"]
    governing_cost_cell_rule: Literal["MAX_UPPER_95_THEN_LARGER_COST_BPS"]
    gate_reconciliation_rule: Literal["ZERO_COST_TIME_DECOUPLED_SORTING_RELAXATION_MINUS_IDENTICAL_B0_T0_GOVERNS_STOP_GREEDY_COST_BEARING_FEASIBLE_BRACKET_DIAGNOSTIC_ONLY_V1"]
    pre_execution_power_prediction_rule: Literal["CONFIGURED_G1_EXPECTED_TO_RETURN_CONTINUE_WITH_NEAR_CERTAINTY_INSTRUMENT_PROPERTY_NOT_FINDING_V1"]
    continue_evidential_weight_rule: Literal["G1_CONTINUE_NOT_SUPPORT_FOR_NEWS_TEXT_OR_LLM_CONTRIBUTION_AND_MUST_NOT_BE_CITED_AS_SUCH_V1"]
    sandwich_reporting_rule: Literal["REPORT_GREEDY_COST_BEARING_LOWER_AND_ZERO_COST_TIME_DECOUPLED_POINT_AND_UPPER_95_WITH_DECISION_BAND_WIDTH_AND_BAND_UNDETERMINED_BY_COST_CELL_V1"]
    bound_certificate_decision_id_rule: Literal["CALIBRATION_PIPE_DECISION_ORDINAL_06D_PIPE_DECISION_DATE_YYYY_MM_DD_V1"]
    bound_certificate_root_rule: Literal["CANONICAL_SHA256_ORDERED_TUPLE_OF_PER_DECISION_CERTIFICATE_SHA256_IN_DECISION_ORDER_V1"]
    gate_reconciliation_amendment_path: Literal["docs/r03-news-reasoning-g1-gate-definition-reconciliation-amendment.md"]
    gate_reconciliation_amendment_sha256: str = Field(pattern=SHA256_PATTERN)
    stage2_asset_access_rule: Literal["EXECUTION_PATH_EXACT_RESOLVED_ABSOLUTE_PATH_MATCH_ONLY_NO_PREFIX_NO_RECURSION_TEST_DOUBLES_AND_INTEGRITY_HASH_INVENTORIES_OUT_OF_SCOPE_V2"]
    g1_session_ordinal_rule: Literal["PINNED_MARKET_BAR_SESSION_ORDINALS_NOMINAL_1530_ET_EARLY_CLOSE_DEFERRED_TO_T2_T3"]
    market_universe_ticker_rule: Literal["EXACT_TICKER_SET_EQUALITY_MARKET_BARS_TO_PINNED_UNIVERSE_SNAPSHOT"]
    universe_source_path: Literal["C:/Users/User/Desktop/FinGPT/configs/universe.json"]
    universe_source_sha256: str = Field(pattern=SHA256_PATTERN)
    universe_snapshot_path: Literal[".research_artifacts/r03-news-reasoning/universe-snapshot-v1.json"]
    universe_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    universe_snapshot_file_sha256: str = Field(pattern=SHA256_PATTERN)
    feature_formula_contract: Literal["R03_T0_FEATURE_FORMULA_AMENDMENT_V1"]
    feature_formula_amendment_path: Literal["docs/r03-news-reasoning-t0-feature-formula-amendment.md"]
    feature_formula_amendment_sha256: str = Field(pattern=SHA256_PATTERN)
    raw_feature_formula_rule: Literal["FLOAT64_LOG_RETURN_WINDOWS_SR_SUM_VOL_DDOF0_DOWNSIDE_ZERO_SEALED_SECTOR_BETA_EXPLICIT_DEPARTURE_TO_UNIVERSE_BETA_VALID_NAMES_MIN1_SPLIT_ADJUSTED_CLOSE_ASSUMED_UNCERTIFIED_LOG_DOLLAR_VOLUME_LOG_MEAN_VOLUME_RATIO_V2"]
    label_formula_rule: Literal["H5_SIMPLE_RETURN_MINUS_SAME_SESSION_EQUAL_WEIGHT_SECTOR_MEAN_V1"]
    raw_missing_rule: Literal["COMPLETE_WINDOW_REQUIRED_INVALID_NONFINITE_OR_NONPOSITIVE_INPUT_AND_ZERO_BETA_DENOMINATOR_ARE_MISSING_V1"]
    protocol_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_protocol(self) -> "T0ProtocolIdentity":
        if self.base_features != T0_BASE_FEATURES:
            raise R03G1PreparationError("T0 base-feature order mismatch")
        if self.design_columns != T0_DESIGN_COLUMNS:
            raise R03G1PreparationError("T0 design-column order mismatch")
        if self.t0_alpha_e1_grid != T0_ALPHA_E1_GRID:
            raise R03G1PreparationError("T0 alpha grid mismatch")
        if self.fold_end_years != T0_FOLD_END_YEARS:
            raise R03G1PreparationError("T0 fold topology mismatch")
        if self.cost_cells_bps != T0_COST_CELLS_BPS:
            raise R03G1PreparationError("T0 cost-cell topology mismatch")
        if self.selection_cells != T0_SELECTION_CELLS:
            raise R03G1PreparationError("T0 selection-cell topology mismatch")
        if self.candidate_run_order != T0_CANDIDATE_RUN_ORDER:
            raise R03G1PreparationError("T0 candidate-run topology mismatch")
        unsigned = self.model_dump(mode="json", exclude={"protocol_sha256"})
        if canonical_sha256(unsigned) != self.protocol_sha256:
            raise R03G1PreparationError("T0 protocol hash mismatch")
        return self


def t0_protocol_identity() -> T0ProtocolIdentity:
    unsigned = {
        "schema_version": "r03-t0-protocol-identity-v2",
        "execution_status": T0_EXECUTION_STATUS,
        "base_features": T0_BASE_FEATURES,
        "design_columns": T0_DESIGN_COLUMNS,
        "imputation": "same_date_sector_then_universe_median",
        "clipping": "same_date_cross_section_percentile_1_99_linear",
        "sector_demean": True,
        "zscore_ddof": 0,
        "zero_dispersion_value_e12": 0,
        "missing_flags_unscaled": True,
        "additional_scaling": "NONE",
        "objective": "SUM_SQUARED_ERROR_PLUS_ALPHA_L2_NO_SAMPLE_NORMALIZATION",
        "intercept": "UNPENALIZED_TRAIN_ROWS_CENTER_ONLY",
        "solver_contract": T0_SOLVER_CONTRACT,
        "t0_alpha_e1_grid": T0_ALPHA_E1_GRID,
        "fold_end_years": T0_FOLD_END_YEARS,
        "cost_cells_bps": T0_COST_CELLS_BPS,
        "selection_cells": T0_SELECTION_CELLS,
        "candidate_run_order": T0_CANDIDATE_RUN_ORDER,
        "alpha_selection_rule": T0_ALPHA_SELECTION_RULE,
        "fold_validation_window_rule": T0_FOLD_VALIDATION_WINDOW_RULE,
        "refit_protocol": T0_REFIT_PROTOCOL,
        "timestamp_rule": T0_TIMESTAMP_RULE,
        "row_id_rule": T0_ROW_ID_RULE,
        "effective_interval": "LEFT_CLOSED_RIGHT_OPEN",
        "label_rule": "H5_MATURED_AT_OR_BEFORE_REFIT",
        "purge_decision_rows": "ALWAYS_EXCLUDED",
        "calibration_alpha_reselection": "FORBIDDEN",
        "arbitrary_refit": "FORBIDDEN",
        "g2_t0_reuse": "REQUIRE_IDENTICAL_T0_MODEL_SERIES_ID",
        "g1_bootstrap_primitive": G1_BOOTSTRAP_PRIMITIVE,
        "g1_bootstrap_domain_seed_rule": G1_BOOTSTRAP_DOMAIN_SEED_RULE,
        "governing_cost_cell_rule": G1_GOVERNING_COST_CELL_RULE,
        "gate_reconciliation_rule": G1_GATE_RECONCILIATION_RULE,
        "pre_execution_power_prediction_rule": G1_PRE_EXECUTION_POWER_PREDICTION_RULE,
        "continue_evidential_weight_rule": G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE,
        "sandwich_reporting_rule": G1_SANDWICH_REPORTING_RULE,
        "bound_certificate_decision_id_rule": G1_BOUND_CERTIFICATE_DECISION_ID_RULE,
        "bound_certificate_root_rule": G1_BOUND_CERTIFICATE_ROOT_RULE,
        "gate_reconciliation_amendment_path": G1_GATE_RECONCILIATION_AMENDMENT_PATH,
        "gate_reconciliation_amendment_sha256": G1_GATE_RECONCILIATION_AMENDMENT_SHA256,
        "stage2_asset_access_rule": G1_STAGE2_ASSET_ACCESS_RULE,
        "g1_session_ordinal_rule": G1_SESSION_ORDINAL_RULE,
        "market_universe_ticker_rule": G1_MARKET_UNIVERSE_TICKER_RULE,
        "universe_source_path": T0_UNIVERSE_SOURCE_PATH,
        "universe_source_sha256": T0_UNIVERSE_SOURCE_SHA256,
        "universe_snapshot_path": T0_UNIVERSE_SNAPSHOT_PATH,
        "universe_snapshot_sha256": T0_UNIVERSE_SNAPSHOT_SHA256,
        "universe_snapshot_file_sha256": T0_UNIVERSE_SNAPSHOT_FILE_SHA256,
        "feature_formula_contract": T0_FEATURE_FORMULA_CONTRACT,
        "feature_formula_amendment_path": T0_FEATURE_FORMULA_AMENDMENT_PATH,
        "feature_formula_amendment_sha256": T0_FEATURE_FORMULA_AMENDMENT_SHA256,
        "raw_feature_formula_rule": T0_RAW_FEATURE_FORMULA_RULE,
        "label_formula_rule": T0_LABEL_FORMULA_RULE,
        "raw_missing_rule": T0_RAW_MISSING_RULE,
    }
    return T0ProtocolIdentity(**unsigned, protocol_sha256=canonical_sha256(unsigned))


def preprocess_t0_cross_section(
    rows: Mapping[str, Mapping[str, float | None]],
    sectors: Mapping[str, str],
) -> dict[str, tuple[float, ...]]:
    """Apply the frozen same-date T0 preprocessing without extra scaling."""

    # NumPy is imported lazily so Stage 2 can validate thread settings first.
    initialize_t0_numeric_runtime()
    import numpy as np

    tickers = sorted(rows)
    if not tickers or set(tickers) != set(sectors):
        raise R03G1PreparationError("T0 rows and sector map must contain identical tickers")
    values_by_ticker: dict[str, list[float]] = {ticker: [] for ticker in tickers}
    for feature in T0_BASE_FEATURES:
        finite = {ticker: float(value) for ticker in tickers if (value := rows[ticker].get(feature)) is not None and math.isfinite(float(value))}
        universe_values = sorted(finite.values())
        universe_median = float(np.median(universe_values)) if universe_values else 0.0
        sector_values: dict[str, list[float]] = {}
        for ticker, value in finite.items():
            sector_values.setdefault(sectors[ticker], []).append(value)
        imputed = {
            ticker: finite.get(
                ticker,
                float(np.median(sector_values[sectors[ticker]])) if sectors[ticker] in sector_values else universe_median,
            )
            for ticker in tickers
        }
        cross_section = np.asarray([imputed[ticker] for ticker in tickers], dtype=np.float64)
        low, high = np.percentile(cross_section, [1, 99], method="linear")
        clipped = {ticker: float(np.clip(imputed[ticker], low, high)) for ticker in tickers}
        sector_mean = {sector: float(np.mean([clipped[ticker] for ticker in tickers if sectors[ticker] == sector])) for sector in sorted(set(sectors.values()))}
        demeaned = np.asarray(
            [clipped[ticker] - sector_mean[sectors[ticker]] for ticker in tickers],
            dtype=np.float64,
        )
        scale = float(demeaned.std(ddof=0))
        for index, ticker in enumerate(tickers):
            standardized = 0.0 if scale == 0.0 else float(demeaned[index] / scale)
            values_by_ticker[ticker].extend((standardized, 0.0 if ticker in finite else 1.0))
    return {ticker: tuple(values) for ticker, values in values_by_ticker.items()}


class T0FitRowMetadata(StrictModel):
    row_id: str = Field(min_length=1)
    decision_at: datetime
    feature_cutoff_at: datetime
    label_maturity_at: datetime
    decision_session_ordinal: int = Field(ge=1)
    feature_session_ordinal: int = Field(ge=0)
    label_session_ordinal: int = Field(ge=1)
    split_name: Literal[
        "DEVELOPMENT",
        "PURGE_1",
        "CALIBRATION",
        "PURGE_2",
        "PROCEDURAL_OOS",
        "LABEL_ONLY",
    ]
    phase_book: int = Field(ge=0, le=4)

    @model_validator(mode="after")
    def validate_temporal_contract(self) -> "T0FitRowMetadata":
        _require_aware(self.decision_at, "decision_at")
        _require_aware(self.feature_cutoff_at, "feature_cutoff_at")
        _require_aware(self.label_maturity_at, "label_maturity_at")
        if self.feature_cutoff_at >= self.decision_at:
            raise R03G1PreparationError("T0 feature cutoff must precede decision")
        if self.feature_session_ordinal != self.decision_session_ordinal - 1:
            raise R03G1PreparationError("T0 features must stop at the t-1 session")
        if self.label_maturity_at <= self.decision_at:
            raise R03G1PreparationError("T0 label maturity must follow decision")
        if self.label_session_ordinal != self.decision_session_ordinal + 5:
            raise R03G1PreparationError("T0 label must be the exact matured h=5 label")
        return self


def eligible_fit_indices(
    rows: Sequence[T0FitRowMetadata],
    *,
    refit_at: datetime,
    stage: Literal["DEVELOPMENT", "CALIBRATION"],
) -> tuple[int, ...]:
    """Select train rows; maturity and explicit purge exclusion both govern."""

    _require_aware(refit_at, "refit_at")
    order = tuple((row.decision_at, row.row_id) for row in rows)
    if order != tuple(sorted(order)):
        raise R03G1PreparationError("T0 fit rows must be in canonical time/id order")
    allowed = {"DEVELOPMENT"} if stage == "DEVELOPMENT" else {"DEVELOPMENT", "CALIBRATION"}
    selected = []
    for index, row in enumerate(rows):
        if row.split_name in PURGE_SPLITS:
            continue
        if row.split_name not in allowed:
            continue
        if row.decision_at >= refit_at:
            continue
        if row.label_maturity_at <= refit_at:
            selected.append(index)
    return tuple(selected)


def monthly_refit_cutoffs(decision_times: Sequence[datetime]) -> tuple[datetime, ...]:
    if not decision_times:
        raise R03G1PreparationError("monthly refit schedule requires decisions")
    for value in decision_times:
        _require_aware(value, "decision_at")
    ordered = tuple(decision_times)
    if ordered != tuple(sorted(ordered)) or len(set(ordered)) != len(ordered):
        raise R03G1PreparationError("decision times must be strictly increasing")
    cutoffs = []
    previous_month = None
    for value in ordered:
        local_month = (value.year, value.month)
        if local_month != previous_month:
            cutoffs.append(value)
            previous_month = local_month
    return tuple(cutoffs)


class T0TrainingFrameIdentity(StrictModel):
    schema_version: Literal["r03-t0-training-frame-identity-v1"] = "r03-t0-training-frame-identity-v1"
    execution_status: Literal["BLOCKED_PENDING_SEPARATE_EXECUTION_AUTHORITY"] = T0_EXECUTION_STATUS
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    row_count: int = Field(gt=0)
    feature_count: Literal[18] = len(T0_DESIGN_COLUMNS)
    design_columns: tuple[str, ...]
    row_metadata_sha256: str = Field(pattern=SHA256_PATTERN)
    feature_matrix_float64_le_sha256: str = Field(pattern=SHA256_PATTERN)
    target_e12_int64_le_sha256: str = Field(pattern=SHA256_PATTERN)
    training_frame_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_identity(self) -> "T0TrainingFrameIdentity":
        if self.design_columns != T0_DESIGN_COLUMNS:
            raise R03G1PreparationError("training-frame design order mismatch")
        unsigned = self.model_dump(mode="json", exclude={"training_frame_sha256"})
        if canonical_sha256(unsigned) != self.training_frame_sha256:
            raise R03G1PreparationError("training-frame hash mismatch")
        return self


def build_training_frame_identity(
    rows: Sequence[T0FitRowMetadata],
    feature_matrix: Sequence[Sequence[float]],
    target_e12: Sequence[int],
    *,
    protocol: T0ProtocolIdentity | None = None,
) -> T0TrainingFrameIdentity:
    initialize_t0_numeric_runtime()
    import numpy as np

    protocol = protocol or t0_protocol_identity()
    if not rows or len(rows) != len(feature_matrix) or len(rows) != len(target_e12):
        raise R03G1PreparationError("training-frame row counts are inconsistent")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in target_e12):
        raise R03G1PreparationError("T0 targets must be e12 integers")
    matrix = np.asarray(feature_matrix, dtype="<f8", order="C")
    if matrix.shape != (len(rows), len(T0_DESIGN_COLUMNS)):
        raise R03G1PreparationError("T0 training matrix must have exactly 18 columns")
    if not np.isfinite(matrix).all():
        raise R03G1PreparationError("T0 training matrix contains non-finite values")
    try:
        targets = np.asarray(target_e12, dtype="<i8", order="C")
    except OverflowError as exc:
        raise R03G1PreparationError("T0 target exceeds signed int64") from exc
    metadata = [row.model_dump(mode="json") for row in rows]
    unsigned = {
        "schema_version": "r03-t0-training-frame-identity-v1",
        "execution_status": T0_EXECUTION_STATUS,
        "t0_protocol_id": protocol.protocol_sha256,
        "row_count": len(rows),
        "feature_count": len(T0_DESIGN_COLUMNS),
        "design_columns": T0_DESIGN_COLUMNS,
        "row_metadata_sha256": canonical_sha256(metadata),
        "feature_matrix_float64_le_sha256": sha256_hex(matrix.tobytes(order="C")),
        "target_e12_int64_le_sha256": sha256_hex(targets.tobytes(order="C")),
    }
    return T0TrainingFrameIdentity(**unsigned, training_frame_sha256=canonical_sha256(unsigned))


class T0AlphaCandidate(StrictModel):
    t0_alpha_e1: int
    cell_order: tuple[str, ...]
    cell_utility_e12: tuple[int, ...]
    worst_cell_utility_e12: int
    candidate_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_candidate(self) -> "T0AlphaCandidate":
        t0_alpha_from_e1(self.t0_alpha_e1)
        if self.cell_order != T0_SELECTION_CELLS:
            raise R03G1PreparationError("T0 alpha candidate cell order mismatch")
        if len(self.cell_utility_e12) != len(T0_SELECTION_CELLS):
            raise R03G1PreparationError("T0 alpha candidate requires 12 cells")
        if self.worst_cell_utility_e12 != min(self.cell_utility_e12):
            raise R03G1PreparationError("T0 alpha candidate worst-cell mismatch")
        unsigned = self.model_dump(mode="json", exclude={"candidate_sha256"})
        if canonical_sha256(unsigned) != self.candidate_sha256:
            raise R03G1PreparationError("T0 alpha candidate hash mismatch")
        return self


class T0AlphaSelection(StrictModel):
    schema_version: Literal["r03-t0-alpha-selection-v1"] = "r03-t0-alpha-selection-v1"
    execution_status: Literal["BLOCKED_PENDING_SEPARATE_EXECUTION_AUTHORITY"] = T0_EXECUTION_STATUS
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    fold_evaluation_refit_protocol: Literal["MONTHLY_EXPANDING_FIXED_ALPHA_MATURED_LABELS_ONLY_V1"] = T0_REFIT_PROTOCOL
    candidate_run_order: tuple[str, ...]
    candidate_run_sha256: tuple[str, ...]
    candidates: tuple[T0AlphaCandidate, ...]
    selected_t0_alpha_e1: int
    selection_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_selection(self) -> "T0AlphaSelection":
        if self.t0_protocol_id != t0_protocol_identity().protocol_sha256:
            raise R03G1PreparationError("T0 alpha selection protocol mismatch")
        if self.candidate_run_order != T0_CANDIDATE_RUN_ORDER:
            raise R03G1PreparationError("T0 alpha selection run order mismatch")
        if len(self.candidate_run_sha256) != len(T0_CANDIDATE_RUN_ORDER) or any(len(value) != 64 or any(character not in "0123456789abcdef" for character in value) for value in self.candidate_run_sha256):
            raise R03G1PreparationError("T0 alpha selection run identity coverage mismatch")
        if tuple(candidate.t0_alpha_e1 for candidate in self.candidates) != T0_ALPHA_E1_GRID:
            raise R03G1PreparationError("T0 alpha candidates must cover the frozen grid")
        selected = max(
            self.candidates,
            key=lambda candidate: (
                candidate.worst_cell_utility_e12,
                candidate.t0_alpha_e1,
            ),
        )
        if self.selected_t0_alpha_e1 != selected.t0_alpha_e1:
            raise R03G1PreparationError("T0 alpha selection mismatch")
        unsigned = self.model_dump(mode="json", exclude={"selection_sha256"})
        if canonical_sha256(unsigned) != self.selection_sha256:
            raise R03G1PreparationError("T0 alpha selection hash mismatch")
        return self


def select_t0_alpha(
    utilities_e12: Mapping[int, Mapping[tuple[int, int], int]],
    candidate_run_sha256: Mapping[int, Mapping[int, str]],
) -> T0AlphaSelection:
    if set(utilities_e12) != set(T0_ALPHA_E1_GRID):
        raise R03G1PreparationError("T0 alpha selection requires the exact frozen grid")
    if set(candidate_run_sha256) != set(T0_ALPHA_E1_GRID) or any(set(candidate_run_sha256[alpha]) != set(T0_FOLD_END_YEARS) for alpha in T0_ALPHA_E1_GRID):
        raise R03G1PreparationError("T0 alpha selection requires all candidate runs")
    expected_cells = {(fold, cost) for fold in T0_FOLD_END_YEARS for cost in T0_COST_CELLS_BPS}
    candidates = []
    for t0_alpha_e1 in T0_ALPHA_E1_GRID:
        cells = utilities_e12[t0_alpha_e1]
        if set(cells) != expected_cells:
            raise R03G1PreparationError("T0 alpha selection requires all fold x cost cells")
        values = tuple(cells[(fold, cost)] for fold in T0_FOLD_END_YEARS for cost in T0_COST_CELLS_BPS)
        unsigned = {
            "t0_alpha_e1": t0_alpha_e1,
            "cell_order": T0_SELECTION_CELLS,
            "cell_utility_e12": values,
            "worst_cell_utility_e12": min(values),
        }
        candidates.append(T0AlphaCandidate(**unsigned, candidate_sha256=canonical_sha256(unsigned)))
    selected = max(
        candidates,
        key=lambda candidate: (
            candidate.worst_cell_utility_e12,
            candidate.t0_alpha_e1,
        ),
    )
    unsigned_selection = {
        "schema_version": "r03-t0-alpha-selection-v1",
        "execution_status": T0_EXECUTION_STATUS,
        "t0_protocol_id": t0_protocol_identity().protocol_sha256,
        "fold_evaluation_refit_protocol": T0_REFIT_PROTOCOL,
        "candidate_run_order": T0_CANDIDATE_RUN_ORDER,
        "candidate_run_sha256": tuple(candidate_run_sha256[alpha][fold] for alpha in T0_ALPHA_E1_GRID for fold in T0_FOLD_END_YEARS),
        "candidates": tuple(candidates),
        "selected_t0_alpha_e1": selected.t0_alpha_e1,
    }
    return T0AlphaSelection(
        **unsigned_selection,
        selection_sha256=canonical_sha256(unsigned_selection),
    )


def assert_single_thread_environment() -> tuple[str, ...]:
    values = tuple(f"{key}={environ.get(key, '')}" for key in THREAD_ENV_KEYS)
    if any(value != f"{key}=1" for key, value in zip(THREAD_ENV_KEYS, values)):
        raise R03G1PreparationError("all BLAS/runtime thread controls must equal 1")
    return values


class T0RuntimeIdentity(StrictModel):
    schema_version: Literal["r03-t0-runtime-identity-v1"] = "r03-t0-runtime-identity-v1"
    python_version: str
    numpy_version: str
    scipy_version: str
    blas_lapack_sha256: str = Field(pattern=SHA256_PATTERN)
    byteorder: Literal["little", "big"]
    thread_environment: tuple[str, ...]
    thread_environment_contract: Literal["PRECONFIGURED_BEFORE_PROCESS_START"] = T0_THREAD_ENVIRONMENT_CONTRACT
    runtime_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_runtime(self) -> "T0RuntimeIdentity":
        if self.thread_environment != tuple(f"{key}=1" for key in THREAD_ENV_KEYS):
            raise R03G1PreparationError("T0 runtime is not single-thread pinned")
        unsigned = self.model_dump(mode="json", exclude={"runtime_sha256"})
        if canonical_sha256(unsigned) != self.runtime_sha256:
            raise R03G1PreparationError("T0 runtime hash mismatch")
        return self


def installed_t0_runtime_identity() -> T0RuntimeIdentity:
    """Identify the runtime under the required process-launch environment."""

    thread_environment = assert_single_thread_environment()
    import numpy as np
    import scipy

    numpy_version = np.__version__
    scipy_version = scipy.__version__
    numpy_config = getattr(np.__config__, "CONFIG", None)
    scipy_config = getattr(getattr(scipy, "__config__", None), "CONFIG", None)
    blas_lapack_sha256 = canonical_sha256(
        {
            "numpy_config": numpy_config if numpy_config is not None else "unavailable",
            "scipy_config": scipy_config if scipy_config is not None else "unavailable",
            "byteorder": sys.byteorder,
        }
    )
    unsigned = {
        "schema_version": "r03-t0-runtime-identity-v1",
        "python_version": platform.python_version(),
        "numpy_version": numpy_version,
        "scipy_version": scipy_version,
        "blas_lapack_sha256": blas_lapack_sha256,
        "byteorder": sys.byteorder,
        "thread_environment": thread_environment,
        "thread_environment_contract": T0_THREAD_ENVIRONMENT_CONTRACT,
    }
    return T0RuntimeIdentity(**unsigned, runtime_sha256=canonical_sha256(unsigned))


def initialize_t0_numeric_runtime() -> T0RuntimeIdentity:
    """Validate the process-launch thread contract and cache runtime identity."""

    global _T0_RUNTIME_CACHE
    thread_environment = assert_single_thread_environment()
    if _T0_RUNTIME_CACHE is None:
        _T0_RUNTIME_CACHE = installed_t0_runtime_identity()
    elif _T0_RUNTIME_CACHE.thread_environment != thread_environment:
        raise R03G1PreparationError("T0 runtime thread environment changed after initialization")
    return _T0_RUNTIME_CACHE


def _resolve_t0_runtime(runtime: T0RuntimeIdentity | None) -> T0RuntimeIdentity:
    active = initialize_t0_numeric_runtime()
    if runtime is not None and runtime.runtime_sha256 != active.runtime_sha256:
        raise R03G1PreparationError("supplied T0 runtime differs from initialized runtime")
    return active


class T0SnapshotIdentity(StrictModel):
    schema_version: Literal["r03-t0-snapshot-identity-v1"] = "r03-t0-snapshot-identity-v1"
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    alpha_selection_sha256: str = Field(pattern=SHA256_PATTERN)
    t0_alpha_e1: int
    refit_at: datetime
    training_frame_sha256: str = Field(pattern=SHA256_PATTERN)
    runtime: T0RuntimeIdentity
    coefficient_float64_le_hex: str = Field(pattern=COEFFICIENT_HEX_PATTERN)
    t0_coefficient_sha256: str = Field(pattern=SHA256_PATTERN)
    intercept_float64_le_hex: str = Field(pattern=FLOAT64_HEX_PATTERN)
    normal_equation_condition_float64_hex: str = Field(pattern=FLOAT64_HEX_PATTERN)
    normal_equation_residual_norm_float64_hex: str = Field(pattern=FLOAT64_HEX_PATTERN)
    t0_snapshot_id: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_snapshot(self) -> "T0SnapshotIdentity":
        _require_aware(self.refit_at, "refit_at")
        t0_alpha_from_e1(self.t0_alpha_e1)
        coefficient_bytes = bytes.fromhex(self.coefficient_float64_le_hex)
        if sha256_hex(coefficient_bytes) != self.t0_coefficient_sha256:
            raise R03G1PreparationError("T0 coefficient hash mismatch")
        coefficients = tuple(struct.unpack("<d", coefficient_bytes[index : index + 8])[0] for index in range(0, len(coefficient_bytes), 8))
        if len(coefficients) != len(T0_DESIGN_COLUMNS) or not all(math.isfinite(value) for value in coefficients):
            raise R03G1PreparationError("T0 coefficient block is invalid")
        _little_endian_float64_from_hex(self.intercept_float64_le_hex)
        _float64_from_hex(self.normal_equation_condition_float64_hex)
        _float64_from_hex(self.normal_equation_residual_norm_float64_hex)
        unsigned = self.model_dump(mode="json", exclude={"t0_snapshot_id"})
        if canonical_sha256(unsigned) != self.t0_snapshot_id:
            raise R03G1PreparationError("T0 snapshot identity mismatch")
        return self


def _solve_t0_parameters(
    feature_matrix: Sequence[Sequence[float]],
    target_e12: Sequence[int],
    *,
    t0_alpha_e1: int,
):
    """Use one numerical solve for development selection and deployment."""

    initialize_t0_numeric_runtime()
    import numpy as np
    import scipy.linalg

    matrix = np.asarray(feature_matrix, dtype=np.float64, order="C")
    if matrix.shape != (len(target_e12), len(T0_DESIGN_COLUMNS)) or not len(target_e12):
        raise R03G1PreparationError("T0 fit matrix shape mismatch")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in target_e12):
        raise R03G1PreparationError("T0 fit targets must be e12 integers")
    targets = np.asarray(target_e12, dtype=np.float64) / UTILITY_SCALE
    if not np.isfinite(matrix).all() or not np.isfinite(targets).all():
        raise R03G1PreparationError("T0 fit input contains non-finite values")
    x_mean = matrix.mean(axis=0, dtype=np.float64)
    y_mean = float(targets.mean(dtype=np.float64))
    centered_x = matrix - x_mean
    centered_y = targets - y_mean
    alpha = t0_alpha_from_e1(t0_alpha_e1)
    normal_matrix = centered_x.T @ centered_x
    normal_matrix += alpha * np.eye(len(T0_DESIGN_COLUMNS), dtype=np.float64)
    right_hand_side = centered_x.T @ centered_y
    condition = float(np.linalg.cond(normal_matrix))
    coefficients = scipy.linalg.solve(
        normal_matrix,
        right_hand_side,
        assume_a="pos",
        overwrite_a=False,
        overwrite_b=False,
        check_finite=True,
    )
    residual = normal_matrix @ coefficients - right_hand_side
    residual_norm = float(np.linalg.norm(residual, ord=2))
    intercept = y_mean - float(x_mean @ coefficients)
    if not np.isfinite(coefficients).all() or not math.isfinite(intercept) or not math.isfinite(condition) or not np.isfinite(residual).all() or not math.isfinite(residual_norm):
        raise R03G1PreparationError("T0 solve produced non-finite output")
    return coefficients, intercept, condition, residual_norm


def _fit_t0_snapshot(
    feature_matrix: Sequence[Sequence[float]],
    target_e12: Sequence[int],
    *,
    refit_at: datetime,
    training_frame: T0TrainingFrameIdentity,
    alpha_selection: T0AlphaSelection,
    runtime: T0RuntimeIdentity,
    protocol: T0ProtocolIdentity | None = None,
) -> T0SnapshotIdentity:
    """Fit one authorized-protocol snapshot; no alpha selection occurs here."""

    import numpy as np

    protocol = protocol or t0_protocol_identity()
    if training_frame.t0_protocol_id != protocol.protocol_sha256:
        raise R03G1PreparationError("training frame uses a different T0 protocol")
    if training_frame.row_count != len(target_e12):
        raise R03G1PreparationError("T0 fit rows do not match training-frame identity")
    t0_alpha_e1 = alpha_selection.selected_t0_alpha_e1
    coefficients, intercept, condition, residual_norm = _solve_t0_parameters(
        feature_matrix,
        target_e12,
        t0_alpha_e1=t0_alpha_e1,
    )
    coefficient_bytes = np.asarray(coefficients, dtype="<f8", order="C").tobytes(order="C")
    unsigned = {
        "schema_version": "r03-t0-snapshot-identity-v1",
        "t0_protocol_id": protocol.protocol_sha256,
        "alpha_selection_sha256": alpha_selection.selection_sha256,
        "t0_alpha_e1": t0_alpha_e1,
        "refit_at": refit_at,
        "training_frame_sha256": training_frame.training_frame_sha256,
        "runtime": runtime,
        "coefficient_float64_le_hex": coefficient_bytes.hex(),
        "t0_coefficient_sha256": sha256_hex(coefficient_bytes),
        "intercept_float64_le_hex": _little_endian_float64_hex(intercept),
        "normal_equation_condition_float64_hex": _float64_hex(condition),
        "normal_equation_residual_norm_float64_hex": _float64_hex(residual_norm),
    }
    candidate = T0SnapshotIdentity.model_construct(**unsigned, t0_snapshot_id="0" * 64)
    digest = canonical_sha256(candidate.model_dump(mode="json", exclude={"t0_snapshot_id"}))
    return T0SnapshotIdentity(**unsigned, t0_snapshot_id=digest)


def predict_t0(snapshot: T0SnapshotIdentity, feature_matrix: Sequence[Sequence[float]]):
    """Return float64 scores from persisted bytes; no refit path is involved."""

    initialize_t0_numeric_runtime()
    import numpy as np

    matrix = np.asarray(feature_matrix, dtype=np.float64, order="C")
    if matrix.ndim != 2 or matrix.shape[1] != len(T0_DESIGN_COLUMNS):
        raise R03G1PreparationError("T0 prediction matrix shape mismatch")
    coefficients = np.frombuffer(bytes.fromhex(snapshot.coefficient_float64_le_hex), dtype="<f8").astype(np.float64, copy=False)
    intercept = _little_endian_float64_from_hex(snapshot.intercept_float64_le_hex)
    predictions = matrix @ coefficients + intercept
    if not np.isfinite(predictions).all():
        raise R03G1PreparationError("T0 prediction produced non-finite values")
    return predictions


class T0DevelopmentCandidateRunIdentity(StrictModel):
    schema_version: Literal["r03-t0-development-candidate-run-v1"] = "r03-t0-development-candidate-run-v1"
    execution_status: Literal["BLOCKED_PENDING_SEPARATE_EXECUTION_AUTHORITY"] = T0_EXECUTION_STATUS
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    fold_end_year: int
    t0_alpha_e1: int
    runtime: T0RuntimeIdentity
    coverage_decision_count: int = Field(gt=0)
    coverage_decisions_sha256: str = Field(pattern=SHA256_PATTERN)
    refit_cutoffs_sha256: str = Field(pattern=SHA256_PATTERN)
    training_frame_sha256: tuple[str, ...]
    coefficient_sha256: tuple[str, ...]
    intercept_float64_le_hex: tuple[str, ...]
    condition_float64_hex: tuple[str, ...]
    residual_norm_float64_hex: tuple[str, ...]
    prediction_row_count: int = Field(gt=0)
    prediction_rows_sha256: str = Field(pattern=SHA256_PATTERN)
    run_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_run(self) -> "T0DevelopmentCandidateRunIdentity":
        if self.fold_end_year not in T0_FOLD_END_YEARS:
            raise R03G1PreparationError("unknown T0 development fold")
        t0_alpha_from_e1(self.t0_alpha_e1)
        count = len(self.training_frame_sha256)
        if not count or any(
            len(values) != count
            for values in (
                self.coefficient_sha256,
                self.intercept_float64_le_hex,
                self.condition_float64_hex,
                self.residual_norm_float64_hex,
            )
        ):
            raise R03G1PreparationError("development candidate refit identities misalign")
        for value in self.intercept_float64_le_hex:
            _little_endian_float64_from_hex(value)
        for values in (self.condition_float64_hex, self.residual_norm_float64_hex):
            for value in values:
                _float64_from_hex(value)
        unsigned = self.model_dump(mode="json", exclude={"run_sha256"})
        if canonical_sha256(unsigned) != self.run_sha256:
            raise R03G1PreparationError("development candidate run hash mismatch")
        return self


def fit_t0_development_fold_candidate(
    rows: Sequence[T0FitRowMetadata],
    feature_matrix: Sequence[Sequence[float]],
    target_e12: Sequence[int],
    *,
    validation_decisions: Sequence[datetime],
    fold_end_year: int,
    t0_alpha_e1: int,
    runtime: T0RuntimeIdentity | None = None,
    protocol: T0ProtocolIdentity | None = None,
) -> tuple[T0DevelopmentCandidateRunIdentity, dict[str, float]]:
    """Fit one frozen-grid alpha with deployment-identical monthly expansion."""

    if fold_end_year not in T0_FOLD_END_YEARS:
        raise R03G1PreparationError("unknown T0 development fold")
    t0_alpha_from_e1(t0_alpha_e1)
    protocol = protocol or t0_protocol_identity()
    decisions = tuple(validation_decisions)
    cutoffs = monthly_refit_cutoffs(decisions)
    if decisions[-1].year != fold_end_year or any(decision.year > fold_end_year for decision in decisions):
        raise R03G1PreparationError("development validation decisions exceed fold end")
    development_row_times = {row.decision_at for row in rows if row.split_name == "DEVELOPMENT"}
    if any(decision not in development_row_times for decision in decisions):
        raise R03G1PreparationError("every validation decision must belong to the development split")
    runtime = _resolve_t0_runtime(runtime)
    import numpy as np

    matrix = np.asarray(feature_matrix, dtype=np.float64, order="C")
    if matrix.shape != (len(rows), len(T0_DESIGN_COLUMNS)):
        raise R03G1PreparationError("development source matrix shape mismatch")
    if len(target_e12) != len(rows):
        raise R03G1PreparationError("development source target count mismatch")
    decision_set = set(decisions)
    prediction_indices = [index for index, row in enumerate(rows) if row.split_name == "DEVELOPMENT" and row.decision_at in decision_set]
    if not prediction_indices:
        raise R03G1PreparationError("development fold has no prediction rows")
    predictions: dict[str, float] = {}
    training_hashes = []
    coefficient_hashes = []
    intercept_hex = []
    condition_hex = []
    residual_hex = []
    for cutoff_index, cutoff in enumerate(cutoffs):
        next_cutoff = cutoffs[cutoff_index + 1] if cutoff_index + 1 < len(cutoffs) else None
        indices = eligible_fit_indices(rows, refit_at=cutoff, stage="DEVELOPMENT")
        if not indices:
            raise R03G1PreparationError("development candidate refit has no matured train rows")
        fit_rows = tuple(rows[index] for index in indices)
        fit_matrix = tuple(tuple(matrix[index].tolist()) for index in indices)
        fit_targets = tuple(target_e12[index] for index in indices)
        training_frame = build_training_frame_identity(
            fit_rows,
            fit_matrix,
            fit_targets,
            protocol=protocol,
        )
        coefficients, intercept, condition, residual_norm = _solve_t0_parameters(
            fit_matrix,
            fit_targets,
            t0_alpha_e1=t0_alpha_e1,
        )
        coefficient_bytes = np.asarray(coefficients, dtype="<f8", order="C").tobytes(order="C")
        training_hashes.append(training_frame.training_frame_sha256)
        coefficient_hashes.append(sha256_hex(coefficient_bytes))
        intercept_hex.append(_little_endian_float64_hex(intercept))
        condition_hex.append(_float64_hex(condition))
        residual_hex.append(_float64_hex(residual_norm))
        for index in prediction_indices:
            decision = rows[index].decision_at
            if decision < cutoff or (next_cutoff is not None and decision >= next_cutoff):
                continue
            if rows[index].row_id in predictions:
                raise R03G1PreparationError("development prediction row served twice")
            predictions[rows[index].row_id] = float(matrix[index] @ coefficients + intercept)
    expected_rows = tuple(sorted(rows[index].row_id for index in prediction_indices))
    if tuple(sorted(predictions)) != expected_rows or not all(math.isfinite(value) for value in predictions.values()):
        raise R03G1PreparationError("development prediction coverage is incomplete")
    unsigned = {
        "schema_version": "r03-t0-development-candidate-run-v1",
        "execution_status": T0_EXECUTION_STATUS,
        "t0_protocol_id": protocol.protocol_sha256,
        "fold_end_year": fold_end_year,
        "t0_alpha_e1": t0_alpha_e1,
        "runtime": runtime,
        "coverage_decision_count": len(decisions),
        "coverage_decisions_sha256": canonical_sha256([_utc_iso(decision) for decision in decisions]),
        "refit_cutoffs_sha256": canonical_sha256([_utc_iso(cutoff) for cutoff in cutoffs]),
        "training_frame_sha256": tuple(training_hashes),
        "coefficient_sha256": tuple(coefficient_hashes),
        "intercept_float64_le_hex": tuple(intercept_hex),
        "condition_float64_hex": tuple(condition_hex),
        "residual_norm_float64_hex": tuple(residual_hex),
        "prediction_row_count": len(predictions),
        "prediction_rows_sha256": canonical_sha256(expected_rows),
    }
    return (
        T0DevelopmentCandidateRunIdentity(**unsigned, run_sha256=canonical_sha256(unsigned)),
        predictions,
    )


class T0SnapshotInterval(StrictModel):
    effective_from: datetime
    effective_until: datetime
    t0_snapshot_id: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_interval(self) -> "T0SnapshotInterval":
        _require_aware(self.effective_from, "effective_from")
        _require_aware(self.effective_until, "effective_until")
        if self.effective_until <= self.effective_from:
            raise R03G1PreparationError("T0 snapshot interval must be nonempty")
        return self


class T0ModelSeriesIdentity(StrictModel):
    schema_version: Literal["r03-t0-model-series-identity-v1"] = "r03-t0-model-series-identity-v1"
    execution_status: Literal["BLOCKED_PENDING_SEPARATE_EXECUTION_AUTHORITY"] = T0_EXECUTION_STATUS
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    alpha_selection_sha256: str = Field(pattern=SHA256_PATTERN)
    t0_alpha_e1: int
    coverage_start_at: datetime
    coverage_end_exclusive_at: datetime
    coverage_decision_count: int = Field(gt=0)
    coverage_decisions_sha256: str = Field(pattern=SHA256_PATTERN)
    snapshots: tuple[T0SnapshotIdentity, ...]
    intervals: tuple[T0SnapshotInterval, ...]
    t0_model_series_id: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_series(self) -> "T0ModelSeriesIdentity":
        _require_aware(self.coverage_start_at, "coverage_start_at")
        _require_aware(self.coverage_end_exclusive_at, "coverage_end_exclusive_at")
        if self.coverage_end_exclusive_at <= self.coverage_start_at:
            raise R03G1PreparationError("T0 model-series coverage is empty")
        t0_alpha_from_e1(self.t0_alpha_e1)
        if not self.snapshots or len(self.snapshots) != len(self.intervals):
            raise R03G1PreparationError("T0 snapshots and intervals must align")
        if self.intervals[0].effective_from != self.coverage_start_at:
            raise R03G1PreparationError("T0 model series has an initial coverage gap")
        if self.intervals[-1].effective_until != self.coverage_end_exclusive_at:
            raise R03G1PreparationError("T0 model series has a terminal coverage gap")
        for index, (snapshot, interval) in enumerate(zip(self.snapshots, self.intervals)):
            if snapshot.t0_protocol_id != self.t0_protocol_id:
                raise R03G1PreparationError("T0 snapshot protocol drift")
            if snapshot.alpha_selection_sha256 != self.alpha_selection_sha256:
                raise R03G1PreparationError("T0 snapshot alpha-selection drift")
            if snapshot.t0_alpha_e1 != self.t0_alpha_e1:
                raise R03G1PreparationError("T0 snapshot alpha drift")
            if snapshot.refit_at != interval.effective_from:
                raise R03G1PreparationError("T0 refit/effective boundary mismatch")
            if snapshot.t0_snapshot_id != interval.t0_snapshot_id:
                raise R03G1PreparationError("T0 interval references the wrong snapshot")
            if index and self.intervals[index - 1].effective_until != interval.effective_from:
                raise R03G1PreparationError("T0 intervals overlap or leave a gap")
        unsigned = self.model_dump(mode="json", exclude={"t0_model_series_id"})
        if canonical_sha256(unsigned) != self.t0_model_series_id:
            raise R03G1PreparationError("T0 model-series identity mismatch")
        return self


def build_t0_model_series(
    snapshots: Sequence[T0SnapshotIdentity],
    *,
    coverage_decisions: Sequence[datetime],
    coverage_end_exclusive_at: datetime,
) -> T0ModelSeriesIdentity:
    if not snapshots or not coverage_decisions:
        raise R03G1PreparationError("T0 model series requires snapshots and decisions")
    decisions = tuple(coverage_decisions)
    if decisions != tuple(sorted(decisions)) or len(set(decisions)) != len(decisions):
        raise R03G1PreparationError("coverage decisions must be strictly increasing")
    for decision in decisions:
        _require_aware(decision, "coverage decision")
    _require_aware(coverage_end_exclusive_at, "coverage_end_exclusive_at")
    if coverage_end_exclusive_at <= decisions[-1]:
        raise R03G1PreparationError("coverage end must follow the final decision")
    ordered_snapshots = tuple(snapshots)
    refits = tuple(snapshot.refit_at for snapshot in ordered_snapshots)
    if refits != tuple(sorted(refits)) or len(set(refits)) != len(refits):
        raise R03G1PreparationError("T0 refit times must be strictly increasing")
    expected_refits = monthly_refit_cutoffs(decisions)
    if refits != expected_refits:
        raise R03G1PreparationError("T0 snapshots must refit on each month's first decision")
    intervals = tuple(
        T0SnapshotInterval(
            effective_from=snapshot.refit_at,
            effective_until=(ordered_snapshots[index + 1].refit_at if index + 1 < len(ordered_snapshots) else coverage_end_exclusive_at),
            t0_snapshot_id=snapshot.t0_snapshot_id,
        )
        for index, snapshot in enumerate(ordered_snapshots)
    )
    for decision in decisions:
        matches = [interval for interval in intervals if interval.effective_from <= decision < interval.effective_until]
        if len(matches) != 1 or matches[0].effective_from > decision:
            raise R03G1PreparationError("decision lacks one nonfuture T0 snapshot")
    first = ordered_snapshots[0]
    unsigned = {
        "schema_version": "r03-t0-model-series-identity-v1",
        "execution_status": T0_EXECUTION_STATUS,
        "t0_protocol_id": first.t0_protocol_id,
        "alpha_selection_sha256": first.alpha_selection_sha256,
        "t0_alpha_e1": first.t0_alpha_e1,
        "coverage_start_at": decisions[0],
        "coverage_end_exclusive_at": coverage_end_exclusive_at,
        "coverage_decision_count": len(decisions),
        "coverage_decisions_sha256": canonical_sha256([_utc_iso(decision) for decision in decisions]),
        "snapshots": ordered_snapshots,
        "intervals": intervals,
    }
    candidate = T0ModelSeriesIdentity.model_construct(**unsigned, t0_model_series_id="0" * 64)
    digest = canonical_sha256(candidate.model_dump(mode="json", exclude={"t0_model_series_id"}))
    return T0ModelSeriesIdentity(**unsigned, t0_model_series_id=digest)


def fit_t0_calibration_series(
    rows: Sequence[T0FitRowMetadata],
    feature_matrix: Sequence[Sequence[float]],
    target_e12: Sequence[int],
    *,
    calibration_decisions: Sequence[datetime],
    coverage_end_exclusive_at: datetime,
    alpha_selection: T0AlphaSelection,
    runtime: T0RuntimeIdentity | None = None,
    protocol: T0ProtocolIdentity | None = None,
) -> T0ModelSeriesIdentity:
    """Run only the frozen calibration monthly-expanding fixed-alpha protocol."""

    protocol = protocol or t0_protocol_identity()
    decisions = tuple(calibration_decisions)
    cutoffs = monthly_refit_cutoffs(decisions)
    calibration_row_times = {row.decision_at for row in rows if row.split_name == "CALIBRATION"}
    if any(decision not in calibration_row_times for decision in decisions):
        raise R03G1PreparationError("every served decision must belong to the calibration split")
    if alpha_selection.t0_protocol_id != protocol.protocol_sha256:
        raise R03G1PreparationError("calibration alpha selection protocol mismatch")
    runtime = _resolve_t0_runtime(runtime)
    import numpy as np

    matrix = np.asarray(feature_matrix, dtype=np.float64, order="C")
    if matrix.shape != (len(rows), len(T0_DESIGN_COLUMNS)):
        raise R03G1PreparationError("calibration source matrix shape mismatch")
    if len(target_e12) != len(rows):
        raise R03G1PreparationError("calibration source target count mismatch")
    snapshots = []
    for cutoff in cutoffs:
        indices = eligible_fit_indices(rows, refit_at=cutoff, stage="CALIBRATION")
        if not indices:
            raise R03G1PreparationError("monthly T0 refit has no matured train rows")
        fit_rows = tuple(rows[index] for index in indices)
        fit_matrix = tuple(tuple(matrix[index].tolist()) for index in indices)
        fit_targets = tuple(target_e12[index] for index in indices)
        training_frame = build_training_frame_identity(
            fit_rows,
            fit_matrix,
            fit_targets,
            protocol=protocol,
        )
        snapshots.append(
            _fit_t0_snapshot(
                fit_matrix,
                fit_targets,
                refit_at=cutoff,
                training_frame=training_frame,
                alpha_selection=alpha_selection,
                runtime=runtime,
                protocol=protocol,
            )
        )
    return build_t0_model_series(
        snapshots,
        coverage_decisions=decisions,
        coverage_end_exclusive_at=coverage_end_exclusive_at,
    )


def serving_snapshot(series: T0ModelSeriesIdentity, decision_at: datetime) -> T0SnapshotIdentity:
    _require_aware(decision_at, "decision_at")
    matches = [(snapshot, interval) for snapshot, interval in zip(series.snapshots, series.intervals) if interval.effective_from <= decision_at < interval.effective_until]
    if len(matches) != 1 or matches[0][0].refit_at > decision_at:
        raise R03G1PreparationError("decision lacks one nonfuture T0 snapshot")
    return matches[0][0]


def assert_g2_reuses_t0_series(g1_t0_model_series_id: str, g2_t0_model_series_id: str) -> None:
    if g1_t0_model_series_id != g2_t0_model_series_id:
        raise R03G1PreparationError("G2 must reuse the exact G1 T0 model series")


class T0DevelopmentWorkloadEstimate(StrictModel):
    fold_month_counts: dict[int, int]
    alpha_count: Literal[4] = len(T0_ALPHA_E1_GRID)
    expected_fit_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_estimate(self) -> "T0DevelopmentWorkloadEstimate":
        if set(self.fold_month_counts) != set(T0_FOLD_END_YEARS):
            raise R03G1PreparationError("workload estimate requires all development folds")
        if any(value <= 0 for value in self.fold_month_counts.values()):
            raise R03G1PreparationError("development fold month counts must be positive")
        expected = len(T0_ALPHA_E1_GRID) * sum(self.fold_month_counts.values())
        if self.expected_fit_count != expected:
            raise R03G1PreparationError("development fit-count estimate mismatch")
        return self


def estimate_development_fit_count(
    fold_month_counts: Mapping[int, int],
) -> T0DevelopmentWorkloadEstimate:
    counts = dict(fold_month_counts)
    return T0DevelopmentWorkloadEstimate(
        fold_month_counts=counts,
        expected_fit_count=len(T0_ALPHA_E1_GRID) * sum(counts.values()),
    )


def derive_g1_seed(preparation_commit_sha: str) -> str:
    if len(preparation_commit_sha) != 40 or any(character not in "0123456789abcdef" for character in preparation_commit_sha):
        raise R03G1PreparationError("preparation commit must be lowercase SHA-1 hex")
    material = G1_SEED_DOMAIN.encode("ascii") + b"\0" + preparation_commit_sha.encode("ascii")
    return hashlib.sha256(material).hexdigest()


def _stationary_bootstrap_means_e12(values_e12: tuple[int, ...], *, seed_sha256: str, label: str) -> tuple[int, ...]:
    """Delegate to the already-sealed R03 headroom bootstrap primitive."""

    initialize_t0_numeric_runtime()
    from v2.research.news_reasoning.r03_headroom import stationary_bootstrap_means_e12

    return stationary_bootstrap_means_e12(
        values_e12,
        seed_sha256=seed_sha256,
        label=label,
        resamples=G1_RESAMPLES,
        block_length=G1_BLOCK_LENGTH,
    )


class G1CostCellResult(StrictModel):
    cost_bps_per_side: int
    decision_count: int = Field(gt=0)
    paired_input_sha256: str = Field(pattern=SHA256_PATTERN)
    point_estimate_e12: int
    lower_95_e12: int
    upper_95_e12: int
    cell_result_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_cell(self) -> "G1CostCellResult":
        if self.cost_bps_per_side not in T0_COST_CELLS_BPS:
            raise R03G1PreparationError("G1 result uses an unregistered cost cell")
        if not self.lower_95_e12 <= self.point_estimate_e12 <= self.upper_95_e12:
            raise R03G1PreparationError("G1 confidence interval is malformed")
        unsigned = self.model_dump(mode="json", exclude={"cell_result_sha256"})
        if canonical_sha256(unsigned) != self.cell_result_sha256:
            raise R03G1PreparationError("G1 cost-cell result hash mismatch")
        return self


class G1PowerDisclosureCell(StrictModel):
    cost_bps_per_side: int
    decision_count: int = Field(gt=0)
    greedy_cost_bearing_lower_point_estimate_e12: int
    zero_cost_decoupled_upper_point_estimate_e12: int
    zero_cost_decoupled_upper_95_e12: int
    decision_band_width_e12: int = Field(ge=0)
    lower_exceeds_delta_star: bool
    upper_95_at_or_below_delta_star: bool
    band_undetermined: bool
    disclosure_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_disclosure(self) -> "G1PowerDisclosureCell":
        if self.cost_bps_per_side not in T0_COST_CELLS_BPS:
            raise R03G1PreparationError("G1 power disclosure uses an unregistered cost cell")
        lower = self.greedy_cost_bearing_lower_point_estimate_e12
        point = self.zero_cost_decoupled_upper_point_estimate_e12
        upper_95 = self.zero_cost_decoupled_upper_95_e12
        if not lower <= point <= upper_95:
            raise R03G1PreparationError("G1 power-disclosure bracket is malformed")
        if self.decision_band_width_e12 != upper_95 - lower:
            raise R03G1PreparationError("G1 power-disclosure width mismatch")
        lower_exceeds = lower > DELTA_STAR_E12
        upper_stops = upper_95 <= DELTA_STAR_E12
        if self.lower_exceeds_delta_star != lower_exceeds:
            raise R03G1PreparationError("G1 lower-bracket state mismatch")
        if self.upper_95_at_or_below_delta_star != upper_stops:
            raise R03G1PreparationError("G1 upper-bracket state mismatch")
        if self.band_undetermined != (not lower_exceeds and not upper_stops):
            raise R03G1PreparationError("G1 undetermined-band state mismatch")
        unsigned = self.model_dump(mode="json", exclude={"disclosure_sha256"})
        if canonical_sha256(unsigned) != self.disclosure_sha256:
            raise R03G1PreparationError("G1 power-disclosure hash mismatch")
        return self


class G1ExecutionRecord(StrictModel):
    schema_version: Literal["r03-g1-calibration-execution-record-v1"] = "r03-g1-calibration-execution-record-v1"
    preparation_commit_sha: str = Field(pattern=COMMIT_SHA_PATTERN)
    preparation_precedes_calibration_access: Literal[True] = True
    thread_environment_preconfigured_before_process_start: Literal[True]
    seed_domain: Literal["R03_G1_STATIONARY_BOOTSTRAP_V1"] = G1_SEED_DOMAIN
    seed_sha256: str = Field(pattern=SHA256_PATTERN)
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    t0_model_series_id: str = Field(pattern=SHA256_PATTERN)
    bound_certificate_root_sha256: str = Field(pattern=SHA256_PATTERN)
    gate_reconciliation_rule: Literal["ZERO_COST_TIME_DECOUPLED_SORTING_RELAXATION_MINUS_IDENTICAL_B0_T0_GOVERNS_STOP_GREEDY_COST_BEARING_FEASIBLE_BRACKET_DIAGNOSTIC_ONLY_V1"] = G1_GATE_RECONCILIATION_RULE
    pre_execution_power_prediction_rule: Literal["CONFIGURED_G1_EXPECTED_TO_RETURN_CONTINUE_WITH_NEAR_CERTAINTY_INSTRUMENT_PROPERTY_NOT_FINDING_V1"] = G1_PRE_EXECUTION_POWER_PREDICTION_RULE
    continue_evidential_weight_rule: Literal["G1_CONTINUE_NOT_SUPPORT_FOR_NEWS_TEXT_OR_LLM_CONTRIBUTION_AND_MUST_NOT_BE_CITED_AS_SUCH_V1"] = G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE
    sandwich_reporting_rule: Literal["REPORT_GREEDY_COST_BEARING_LOWER_AND_ZERO_COST_TIME_DECOUPLED_POINT_AND_UPPER_95_WITH_DECISION_BAND_WIDTH_AND_BAND_UNDETERMINED_BY_COST_CELL_V1"] = G1_SANDWICH_REPORTING_RULE
    bound_certificate_root_rule: Literal["CANONICAL_SHA256_ORDERED_TUPLE_OF_PER_DECISION_CERTIFICATE_SHA256_IN_DECISION_ORDER_V1"] = G1_BOUND_CERTIFICATE_ROOT_RULE
    g1_bootstrap_primitive: Literal["R03_HEADROOM_STATIONARY_BOOTSTRAP_MEANS_E12_V1"] = G1_BOOTSTRAP_PRIMITIVE
    g1_bootstrap_domain_seed_rule: Literal["SHA256_SEED_BYTES_CONCAT_LABEL_UTF8_NO_SEPARATOR_FIRST_16_BYTES_BIG_ENDIAN"] = G1_BOOTSTRAP_DOMAIN_SEED_RULE
    block_length: Literal[10] = G1_BLOCK_LENGTH
    resamples: Literal[10000] = G1_RESAMPLES
    cost_cells: tuple[G1CostCellResult, ...]
    power_disclosure_cells: tuple[G1PowerDisclosureCell, ...]
    governing_cost_cell_rule: Literal["MAX_UPPER_95_THEN_LARGER_COST_BPS"] = G1_GOVERNING_COST_CELL_RULE
    governing_cost_bps_per_side: int
    label: Literal["STOP_NO_ECONOMIC_HEADROOM", "G1_CONTINUE_NO_FUTILITY_PROOF"]
    band_undetermined: bool
    raw_news_access_attempts: Literal[0] = 0
    provider_calls: Literal[0] = 0
    network_attempts: Literal[0] = 0
    record_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_record(self) -> "G1ExecutionRecord":
        if self.seed_sha256 != derive_g1_seed(self.preparation_commit_sha):
            raise R03G1PreparationError("G1 seed is not derived from the preparation commit")
        if tuple(cell.cost_bps_per_side for cell in self.cost_cells) != T0_COST_CELLS_BPS:
            raise R03G1PreparationError("G1 execution requires ordered 5/10/15 bp cells")
        if tuple(cell.cost_bps_per_side for cell in self.power_disclosure_cells) != T0_COST_CELLS_BPS:
            raise R03G1PreparationError("G1 power disclosure requires ordered 5/10/15 bp cells")
        for result, disclosure in zip(self.cost_cells, self.power_disclosure_cells):
            if result.decision_count != disclosure.decision_count:
                raise R03G1PreparationError("G1 power-disclosure decision count mismatch")
            if result.point_estimate_e12 != disclosure.zero_cost_decoupled_upper_point_estimate_e12:
                raise R03G1PreparationError("G1 power-disclosure point estimate mismatch")
            if result.upper_95_e12 != disclosure.zero_cost_decoupled_upper_95_e12:
                raise R03G1PreparationError("G1 power-disclosure upper bound mismatch")
        governing = max(
            self.cost_cells,
            key=lambda cell: (cell.upper_95_e12, cell.cost_bps_per_side),
        )
        if self.governing_cost_bps_per_side != governing.cost_bps_per_side:
            raise R03G1PreparationError("G1 governing cost-cell mismatch")
        expected_label = "STOP_NO_ECONOMIC_HEADROOM" if governing.upper_95_e12 <= DELTA_STAR_E12 else "G1_CONTINUE_NO_FUTILITY_PROOF"
        if self.label != expected_label:
            raise R03G1PreparationError("G1 gate label mismatch")
        governing_disclosure = next(item for item in self.power_disclosure_cells if item.cost_bps_per_side == self.governing_cost_bps_per_side)
        if self.band_undetermined != governing_disclosure.band_undetermined:
            raise R03G1PreparationError("G1 governing undetermined-band state mismatch")
        unsigned = self.model_dump(mode="json", exclude={"record_sha256"})
        if canonical_sha256(unsigned) != self.record_sha256:
            raise R03G1PreparationError("G1 execution record hash mismatch")
        return self


def evaluate_g1_cost_cells(
    differences_by_cost_e12: Mapping[int, tuple[int, ...]],
    *,
    greedy_feasible_lower_by_cost_e12: Mapping[int, int],
    preparation_commit_sha: str,
    t0_model_series_id: str,
    bound_certificate_root_sha256: str,
    thread_environment_preconfigured_before_process_start: Literal[True],
    protocol: T0ProtocolIdentity | None = None,
) -> G1ExecutionRecord:
    protocol = protocol or t0_protocol_identity()
    if set(differences_by_cost_e12) != set(T0_COST_CELLS_BPS):
        raise R03G1PreparationError("G1 requires exact 5/10/15 bp paired series")
    if set(greedy_feasible_lower_by_cost_e12) != set(T0_COST_CELLS_BPS):
        raise R03G1PreparationError("G1 requires exact 5/10/15 bp greedy lower brackets")
    lengths = {len(values) for values in differences_by_cost_e12.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
        raise R03G1PreparationError("G1 paired cost-cell series must align and be nonempty")
    seed_sha256 = derive_g1_seed(preparation_commit_sha)
    cells = []
    for cost in T0_COST_CELLS_BPS:
        values = differences_by_cost_e12[cost]
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise R03G1PreparationError("G1 paired differences must be e12 integers")
        draws = sorted(
            _stationary_bootstrap_means_e12(
                values,
                seed_sha256=seed_sha256,
                label=f"{G1_SEED_DOMAIN}:COST_BPS={cost}",
            )
        )
        unsigned_cell = {
            "cost_bps_per_side": cost,
            "decision_count": len(values),
            "paired_input_sha256": canonical_sha256(values),
            "point_estimate_e12": _mean_e12(values),
            "lower_95_e12": draws[max(0, math.ceil(0.05 * len(draws)) - 1)],
            "upper_95_e12": draws[max(0, math.ceil(0.95 * len(draws)) - 1)],
        }
        cells.append(
            G1CostCellResult(
                **unsigned_cell,
                cell_result_sha256=canonical_sha256(unsigned_cell),
            )
        )
    disclosures = []
    for cell in cells:
        lower = greedy_feasible_lower_by_cost_e12[cell.cost_bps_per_side]
        if isinstance(lower, bool) or not isinstance(lower, int):
            raise R03G1PreparationError("G1 greedy lower brackets must be e12 integers")
        unsigned_disclosure = {
            "cost_bps_per_side": cell.cost_bps_per_side,
            "decision_count": cell.decision_count,
            "greedy_cost_bearing_lower_point_estimate_e12": lower,
            "zero_cost_decoupled_upper_point_estimate_e12": cell.point_estimate_e12,
            "zero_cost_decoupled_upper_95_e12": cell.upper_95_e12,
            "decision_band_width_e12": cell.upper_95_e12 - lower,
            "lower_exceeds_delta_star": lower > DELTA_STAR_E12,
            "upper_95_at_or_below_delta_star": cell.upper_95_e12 <= DELTA_STAR_E12,
            "band_undetermined": lower <= DELTA_STAR_E12 < cell.upper_95_e12,
        }
        disclosures.append(
            G1PowerDisclosureCell(
                **unsigned_disclosure,
                disclosure_sha256=canonical_sha256(unsigned_disclosure),
            )
        )
    governing = max(cells, key=lambda cell: (cell.upper_95_e12, cell.cost_bps_per_side))
    governing_disclosure = next(item for item in disclosures if item.cost_bps_per_side == governing.cost_bps_per_side)
    unsigned = {
        "schema_version": "r03-g1-calibration-execution-record-v1",
        "preparation_commit_sha": preparation_commit_sha,
        "preparation_precedes_calibration_access": True,
        "thread_environment_preconfigured_before_process_start": (thread_environment_preconfigured_before_process_start),
        "seed_domain": G1_SEED_DOMAIN,
        "seed_sha256": seed_sha256,
        "t0_protocol_id": protocol.protocol_sha256,
        "t0_model_series_id": t0_model_series_id,
        "bound_certificate_root_sha256": bound_certificate_root_sha256,
        "gate_reconciliation_rule": G1_GATE_RECONCILIATION_RULE,
        "pre_execution_power_prediction_rule": G1_PRE_EXECUTION_POWER_PREDICTION_RULE,
        "continue_evidential_weight_rule": G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE,
        "sandwich_reporting_rule": G1_SANDWICH_REPORTING_RULE,
        "bound_certificate_root_rule": G1_BOUND_CERTIFICATE_ROOT_RULE,
        "g1_bootstrap_primitive": G1_BOOTSTRAP_PRIMITIVE,
        "g1_bootstrap_domain_seed_rule": G1_BOOTSTRAP_DOMAIN_SEED_RULE,
        "block_length": G1_BLOCK_LENGTH,
        "resamples": G1_RESAMPLES,
        "cost_cells": tuple(cells),
        "power_disclosure_cells": tuple(disclosures),
        "governing_cost_cell_rule": G1_GOVERNING_COST_CELL_RULE,
        "governing_cost_bps_per_side": governing.cost_bps_per_side,
        "label": ("STOP_NO_ECONOMIC_HEADROOM" if governing.upper_95_e12 <= DELTA_STAR_E12 else "G1_CONTINUE_NO_FUTILITY_PROOF"),
        "band_undetermined": governing_disclosure.band_undetermined,
        "raw_news_access_attempts": 0,
        "provider_calls": 0,
        "network_attempts": 0,
    }
    return G1ExecutionRecord(**unsigned, record_sha256=canonical_sha256(unsigned))
