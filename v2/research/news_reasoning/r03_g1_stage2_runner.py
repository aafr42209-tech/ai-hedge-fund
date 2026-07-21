"""Fail-closed R03 G1 Stage 2 data-access gateway.

This module owns the only filesystem-reading function in the Stage 2 path.
Remediation tests must replace its filesystem and parquet calls with synthetic
test doubles. Real asset access remains separately authorized.
"""

from __future__ import annotations

import hashlib
import math
import os
import platform
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from v2.research.news_reasoning.r03_contracts import mean_e12
from v2.research.news_reasoning.r03_frames import (
    construct_buffered_book,
    frozen_splits,
    net_book_utility_e12,
    phase_book_for_session,
    sector_relative_outcomes_e12,
)
from v2.research.news_reasoning.r03_g1_execution import (
    assert_single_thread_environment,
    derive_g1_seed,
    evaluate_g1_cost_cells,
    fit_t0_calibration_series,
    fit_t0_development_fold_candidate,
    G1_BOUND_CERTIFICATE_ROOT_RULE,
    G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE,
    G1_GATE_RECONCILIATION_RULE,
    G1_MARKET_UNIVERSE_TICKER_RULE,
    G1_PRE_EXECUTION_POWER_PREDICTION_RULE,
    G1_SANDWICH_REPORTING_RULE,
    G1_SESSION_ORDINAL_RULE,
    G1_STAGE2_ASSET_ACCESS_RULE,
    G1ExecutionRecord,
    initialize_t0_numeric_runtime,
    predict_t0,
    preprocess_t0_cross_section,
    select_t0_alpha,
    serving_snapshot,
    T0_ALPHA_E1_GRID,
    T0_COST_CELLS_BPS,
    T0_FOLD_END_YEARS,
    t0_protocol_identity,
    T0_UNIVERSE_SNAPSHOT_FILE_SHA256,
    T0_UNIVERSE_SNAPSHOT_PATH,
    T0_UNIVERSE_SNAPSHOT_SHA256,
    T0_UNIVERSE_SOURCE_PATH,
    T0_UNIVERSE_SOURCE_SHA256,
    T0AlphaSelection,
    T0FitRowMetadata,
    T0ModelSeriesIdentity,
    T0RuntimeIdentity,
)
from v2.research.overlay.canonical import canonical_json_bytes, canonical_sha256
from v2.research.overlay.contracts import StrictModel

SHA256_PATTERN = r"^[0-9a-f]{64}$"
MARKET_BARS_PATH = "C:/Users/User/Desktop/FinGPT/data/raw/market_bars_real.parquet"
MARKET_BARS_SHA256 = "9ae1625de0fb91e0c6abaab18b0637a0798abc035368622e5f1aba84e0dec011"
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
UNIVERSE_SNAPSHOT_ABSOLUTE_PATH = os.path.abspath(os.path.join(WORKSPACE_ROOT, T0_UNIVERSE_SNAPSHOT_PATH))
NOMINAL_DECISION_TIME = "15:30:00_AMERICA_NEW_YORK"
G1_AGGREGATE_OUTPUT_PATH = ".research_artifacts/r03-news-reasoning/g1-stage2-execution-record-v1.json"
G1_AGGREGATE_SERIALIZATION_RULE = "CANONICAL_JSON_UTF8_SORTED_KEYS_NO_INSIGNIFICANT_WHITESPACE_EXACTLY_ONE_TRAILING_LF_CREATE_EXCLUSIVE_V1"
G1_REVIEWED_T0_PROTOCOL_ID = "b754d194339d0a4131d0832785991b2360d83513f99ff86379ffdcf898e29e53"
G1_REVIEWED_STAGE2_RUNNER_PROTOCOL_ID = "3880b9bfca4e06210d8d0db9f75c5758c265e11193ca003de4858f682608ac7c"
G1_EXECUTION_DATA_END_EXCLUSIVE_UTC = datetime(2022, 12, 31, tzinfo=timezone.utc)
G1_STRUCTURAL_BURN_IN_SESSIONS = 61
FORBIDDEN_RAW_COLUMN_TOKENS = frozenset({"body", "content", "headline", "raw_text", "summary", "text"})


class R03G1Stage2AccessError(RuntimeError):
    pass


class Stage2AssetPin(StrictModel):
    role: Literal["MARKET_BARS", "UNIVERSE_SNAPSHOT"]
    location: Literal["EXTERNAL", "INTERNAL"]
    absolute_path: str
    sha256: str = Field(pattern=SHA256_PATTERN)


def stage2_asset_pins() -> tuple[Stage2AssetPin, ...]:
    return (
        Stage2AssetPin(
            role="MARKET_BARS",
            location="EXTERNAL",
            absolute_path=MARKET_BARS_PATH,
            sha256=MARKET_BARS_SHA256,
        ),
        Stage2AssetPin(
            role="UNIVERSE_SNAPSHOT",
            location="INTERNAL",
            absolute_path=UNIVERSE_SNAPSHOT_ABSOLUTE_PATH.replace("\\", "/"),
            sha256=T0_UNIVERSE_SNAPSHOT_FILE_SHA256,
        ),
    )


def stage2_asset_pin(role: str) -> Stage2AssetPin:
    matches = tuple(pin for pin in stage2_asset_pins() if pin.role == role)
    if len(matches) != 1:
        raise R03G1Stage2AccessError("unknown Stage 2 asset role")
    return matches[0]


@dataclass
class Stage2AccessCounters:
    raw_news_access_attempts: int = 0
    disallowed_path_attempts: int = 0
    recursive_discovery_calls: int = 0
    provider_calls: int = 0
    network_calls: int = 0
    allowed_asset_reads: int = 0

    def assert_clean_before_read(self) -> None:
        if self.raw_news_access_attempts or self.disallowed_path_attempts or self.recursive_discovery_calls or self.provider_calls or self.network_calls:
            raise R03G1Stage2AccessError("Stage 2 access counters are contaminated")


class Stage2ZeroCallManifest(StrictModel):
    schema_version: Literal["r03-g1-stage2-zero-call-manifest-v1"] = "r03-g1-stage2-zero-call-manifest-v1"
    raw_news_access_attempts: Literal[0]
    disallowed_path_attempts: Literal[0]
    recursive_discovery_calls: Literal[0]
    provider_calls: Literal[0]
    network_calls: Literal[0]
    manifest_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_manifest_hash(self) -> "Stage2ZeroCallManifest":
        unsigned = self.model_dump(mode="json", exclude={"manifest_sha256"})
        if canonical_sha256(unsigned) != self.manifest_sha256:
            raise R03G1Stage2AccessError("Stage 2 zero-call manifest hash mismatch")
        return self


def build_zero_call_manifest(counters: Stage2AccessCounters) -> Stage2ZeroCallManifest:
    counters.assert_clean_before_read()
    unsigned = {
        "schema_version": "r03-g1-stage2-zero-call-manifest-v1",
        "raw_news_access_attempts": 0,
        "disallowed_path_attempts": 0,
        "recursive_discovery_calls": 0,
        "provider_calls": 0,
        "network_calls": 0,
    }
    return Stage2ZeroCallManifest(
        **unsigned,
        manifest_sha256=canonical_sha256(unsigned),
    )


class TickerSectorEntry(StrictModel):
    ticker: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")
    sector: str = Field(min_length=1)


class UniverseSnapshot(StrictModel):
    schema_version: Literal["r03-g1-universe-snapshot-v1"]
    source_path: Literal["C:/Users/User/Desktop/FinGPT/configs/universe.json"]
    source_sha256: str = Field(pattern=SHA256_PATTERN)
    ticker_sector_mapping: tuple[TickerSectorEntry, ...]
    snapshot_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_snapshot(self) -> "UniverseSnapshot":
        tickers = tuple(entry.ticker for entry in self.ticker_sector_mapping)
        if len(tickers) != 100 or tickers != tuple(sorted(tickers)) or len(set(tickers)) != 100:
            raise R03G1Stage2AccessError("universe snapshot requires 100 sorted unique tickers")
        if self.source_sha256 != T0_UNIVERSE_SOURCE_SHA256:
            raise R03G1Stage2AccessError("universe source hash pin mismatch")
        unsigned = self.model_dump(mode="json", exclude={"snapshot_sha256"})
        if canonical_sha256(unsigned) != self.snapshot_sha256:
            raise R03G1Stage2AccessError("universe snapshot hash mismatch")
        return self


class Stage2AssetLoadReceipt(StrictModel):
    schema_version: Literal["r03-g1-stage2-asset-load-receipt-v1"] = "r03-g1-stage2-asset-load-receipt-v1"
    role: Literal["MARKET_BARS", "UNIVERSE_SNAPSHOT"]
    resolved_path: str
    sha256: str = Field(pattern=SHA256_PATTERN)
    byte_count: int = Field(gt=0)
    row_count: int = Field(ge=0)
    column_names: tuple[str, ...]
    receipt_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_receipt_hash(self) -> "Stage2AssetLoadReceipt":
        unsigned = self.model_dump(mode="json", exclude={"receipt_sha256"})
        if canonical_sha256(unsigned) != self.receipt_sha256:
            raise R03G1Stage2AccessError("Stage 2 asset receipt hash mismatch")
        return self


@dataclass(frozen=True)
class LoadedStage2Asset:
    payload: object
    receipt: Stage2AssetLoadReceipt


def _normalized_lexical_path(value: str | os.PathLike[str]) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(value)))


def _reject_path(
    requested_path: str | os.PathLike[str],
    counters: Stage2AccessCounters,
    message: str,
) -> None:
    counters.disallowed_path_attempts += 1
    counters.raw_news_access_attempts += 1
    raise R03G1Stage2AccessError(message)


def _validate_market_bars_table(table: object) -> tuple[int, tuple[str, ...]]:
    import pyarrow as pa

    expected = ("ticker", "timestamp", "open", "high", "low", "close", "volume")
    columns = tuple(table.column_names)
    if columns != expected:
        raise R03G1Stage2AccessError("market-bars schema or column order mismatch")
    schema = table.schema
    if not pa.types.is_string(schema.field("ticker").type):
        raise R03G1Stage2AccessError("market-bars ticker must be string")
    timestamp_type = schema.field("timestamp").type
    if not pa.types.is_timestamp(timestamp_type) or timestamp_type.tz != "UTC":
        raise R03G1Stage2AccessError("market-bars timestamp must be timezone-aware UTC")
    for name in ("open", "high", "low", "close"):
        if not pa.types.is_float64(schema.field(name).type):
            raise R03G1Stage2AccessError(f"market-bars {name} must be float64")
    if not pa.types.is_int64(schema.field("volume").type):
        raise R03G1Stage2AccessError("market-bars volume must be int64")
    return table.num_rows, columns


def _validate_article_events_table(table: object) -> tuple[int, tuple[str, ...]]:
    columns = tuple(table.column_names)
    lowered = {column.lower() for column in columns}
    if "ticker" not in lowered:
        raise R03G1Stage2AccessError("article-events table requires ticker")
    if lowered & FORBIDDEN_RAW_COLUMN_TOKENS:
        raise R03G1Stage2AccessError("article-events table exposes a raw-text column")
    if not any("timestamp" in column or column.endswith("_at") for column in lowered):
        raise R03G1Stage2AccessError("article-events table requires a timestamp column")
    return table.num_rows, columns


def load_stage2_asset(
    role: Literal["MARKET_BARS", "UNIVERSE_SNAPSHOT"],
    requested_path: str | os.PathLike[str],
    counters: Stage2AccessCounters,
) -> LoadedStage2Asset:
    """The only Stage 2 function permitted to read a filesystem asset."""

    counters.assert_clean_before_read()
    pin = stage2_asset_pin(role)
    if _normalized_lexical_path(requested_path) != _normalized_lexical_path(pin.absolute_path):
        _reject_path(requested_path, counters, "asset path is not an exact allowlist match")
    try:
        resolved = Path(requested_path).resolve(strict=True)
    except OSError as exc:
        raise R03G1Stage2AccessError("allowlisted asset is unavailable") from exc
    if _normalized_lexical_path(resolved) != _normalized_lexical_path(pin.absolute_path):
        _reject_path(requested_path, counters, "resolved asset path differs from its pin")

    digest = hashlib.sha256()
    byte_count = 0
    chunks: list[bytes] = []
    with open(resolved, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
            chunks.append(chunk)
    if digest.hexdigest() != pin.sha256:
        raise R03G1Stage2AccessError("allowlisted asset content hash mismatch")

    if role == "UNIVERSE_SNAPSHOT":
        payload: object = UniverseSnapshot.model_validate_json(b"".join(chunks))
        row_count = len(payload.ticker_sector_mapping)
        column_names = ("ticker", "sector")
    else:
        import pyarrow as pa
        import pyarrow.parquet as parquet

        payload = parquet.read_table(pa.BufferReader(b"".join(chunks)))
        row_count, column_names = _validate_market_bars_table(payload)

    counters.allowed_asset_reads += 1
    unsigned_receipt = {
        "schema_version": "r03-g1-stage2-asset-load-receipt-v1",
        "role": role,
        "resolved_path": str(resolved).replace("\\", "/"),
        "sha256": pin.sha256,
        "byte_count": byte_count,
        "row_count": row_count,
        "column_names": column_names,
    }
    receipt = Stage2AssetLoadReceipt(
        **unsigned_receipt,
        receipt_sha256=canonical_sha256(unsigned_receipt),
    )
    return LoadedStage2Asset(payload=payload, receipt=receipt)


class Stage2IORuntimeIdentity(StrictModel):
    schema_version: Literal["r03-g1-stage2-io-runtime-v1"] = "r03-g1-stage2-io-runtime-v1"
    python_version: str
    pyarrow_version: str
    t0_numeric_runtime_sha256: str = Field(pattern=SHA256_PATTERN)
    runtime_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_runtime_hash(self) -> "Stage2IORuntimeIdentity":
        unsigned = self.model_dump(mode="json", exclude={"runtime_sha256"})
        if canonical_sha256(unsigned) != self.runtime_sha256:
            raise R03G1Stage2AccessError("Stage 2 I/O runtime hash mismatch")
        return self


def installed_stage2_io_runtime_identity() -> Stage2IORuntimeIdentity:
    numeric = initialize_t0_numeric_runtime()
    import pyarrow

    unsigned = {
        "schema_version": "r03-g1-stage2-io-runtime-v1",
        "python_version": platform.python_version(),
        "pyarrow_version": pyarrow.__version__,
        "t0_numeric_runtime_sha256": numeric.runtime_sha256,
    }
    return Stage2IORuntimeIdentity(
        **unsigned,
        runtime_sha256=canonical_sha256(unsigned),
    )


class Stage2RunnerProtocolIdentity(StrictModel):
    schema_version: Literal["r03-g1-stage2-runner-protocol-v2"] = "r03-g1-stage2-runner-protocol-v2"
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    asset_access_rule: Literal["EXECUTION_PATH_EXACT_RESOLVED_ABSOLUTE_PATH_MATCH_ONLY_NO_PREFIX_NO_RECURSION_TEST_DOUBLES_AND_INTEGRITY_HASH_INVENTORIES_OUT_OF_SCOPE_V2"]
    external_asset_pins: tuple[Stage2AssetPin]
    universe_source_path: Literal["C:/Users/User/Desktop/FinGPT/configs/universe.json"]
    universe_source_sha256: str = Field(pattern=SHA256_PATTERN)
    universe_snapshot_path: str
    universe_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    universe_snapshot_file_sha256: str = Field(pattern=SHA256_PATTERN)
    session_ordinal_rule: Literal["PINNED_MARKET_BAR_SESSION_ORDINALS_NOMINAL_1530_ET_EARLY_CLOSE_DEFERRED_TO_T2_T3"]
    market_universe_ticker_rule: Literal["EXACT_TICKER_SET_EQUALITY_MARKET_BARS_TO_PINNED_UNIVERSE_SNAPSHOT"]
    nominal_decision_time: Literal["15:30:00_AMERICA_NEW_YORK"]
    real_early_close_schedule_in_scope: Literal[False]
    gate_reconciliation_rule: Literal["ZERO_COST_TIME_DECOUPLED_SORTING_RELAXATION_MINUS_IDENTICAL_B0_T0_GOVERNS_STOP_GREEDY_COST_BEARING_FEASIBLE_BRACKET_DIAGNOSTIC_ONLY_V1"]
    pre_execution_power_prediction_rule: Literal["CONFIGURED_G1_EXPECTED_TO_RETURN_CONTINUE_WITH_NEAR_CERTAINTY_INSTRUMENT_PROPERTY_NOT_FINDING_V1"]
    continue_evidential_weight_rule: Literal["G1_CONTINUE_NOT_SUPPORT_FOR_NEWS_TEXT_OR_LLM_CONTRIBUTION_AND_MUST_NOT_BE_CITED_AS_SUCH_V1"]
    sandwich_reporting_rule: Literal["REPORT_GREEDY_COST_BEARING_LOWER_AND_ZERO_COST_TIME_DECOUPLED_POINT_AND_UPPER_95_WITH_DECISION_BAND_WIDTH_AND_BAND_UNDETERMINED_BY_COST_CELL_V1"]
    bound_certificate_root_rule: Literal["CANONICAL_SHA256_ORDERED_TUPLE_OF_PER_DECISION_CERTIFICATE_SHA256_IN_DECISION_ORDER_V1"]
    driver_entrypoint: Literal["run_g1_stage2"]
    aggregate_output_path: Literal[".research_artifacts/r03-news-reasoning/g1-stage2-execution-record-v1.json"]
    aggregate_serialization_rule: Literal["CANONICAL_JSON_UTF8_SORTED_KEYS_NO_INSIGNIFICANT_WHITESPACE_EXACTLY_ONE_TRAILING_LF_CREATE_EXCLUSIVE_V1"]
    runner_protocol_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_protocol_hash(self) -> "Stage2RunnerProtocolIdentity":
        unsigned = self.model_dump(mode="json", exclude={"runner_protocol_sha256"})
        if canonical_sha256(unsigned) != self.runner_protocol_sha256:
            raise R03G1Stage2AccessError("Stage 2 runner protocol hash mismatch")
        return self


def stage2_runner_protocol_identity() -> Stage2RunnerProtocolIdentity:
    pins = stage2_asset_pins()
    unsigned = {
        "schema_version": "r03-g1-stage2-runner-protocol-v2",
        "t0_protocol_id": t0_protocol_identity().protocol_sha256,
        "asset_access_rule": G1_STAGE2_ASSET_ACCESS_RULE,
        "external_asset_pins": pins[:1],
        "universe_source_path": T0_UNIVERSE_SOURCE_PATH,
        "universe_source_sha256": T0_UNIVERSE_SOURCE_SHA256,
        "universe_snapshot_path": T0_UNIVERSE_SNAPSHOT_PATH,
        "universe_snapshot_sha256": T0_UNIVERSE_SNAPSHOT_SHA256,
        "universe_snapshot_file_sha256": T0_UNIVERSE_SNAPSHOT_FILE_SHA256,
        "session_ordinal_rule": G1_SESSION_ORDINAL_RULE,
        "market_universe_ticker_rule": G1_MARKET_UNIVERSE_TICKER_RULE,
        "nominal_decision_time": NOMINAL_DECISION_TIME,
        "real_early_close_schedule_in_scope": False,
        "gate_reconciliation_rule": G1_GATE_RECONCILIATION_RULE,
        "pre_execution_power_prediction_rule": G1_PRE_EXECUTION_POWER_PREDICTION_RULE,
        "continue_evidential_weight_rule": G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE,
        "sandwich_reporting_rule": G1_SANDWICH_REPORTING_RULE,
        "bound_certificate_root_rule": G1_BOUND_CERTIFICATE_ROOT_RULE,
        "driver_entrypoint": "run_g1_stage2",
        "aggregate_output_path": G1_AGGREGATE_OUTPUT_PATH,
        "aggregate_serialization_rule": G1_AGGREGATE_SERIALIZATION_RULE,
    }
    return Stage2RunnerProtocolIdentity(
        **unsigned,
        runner_protocol_sha256=canonical_sha256(unsigned),
    )


@dataclass(frozen=True)
class G1Stage2LoadedInputs:
    market_bars: object
    universe_snapshot: UniverseSnapshot
    receipts: tuple[Stage2AssetLoadReceipt, Stage2AssetLoadReceipt]


def _assert_exact_market_universe_tickers(
    market_bars: object,
    universe_snapshot: UniverseSnapshot,
) -> None:
    market_tickers = set(market_bars.column("ticker").to_pylist())
    universe_tickers = {entry.ticker for entry in universe_snapshot.ticker_sector_mapping}
    if market_tickers != universe_tickers:
        raise R03G1Stage2AccessError("market-bars and universe ticker sets differ")


def load_g1_stage2_inputs(counters: Stage2AccessCounters) -> G1Stage2LoadedInputs:
    """Load only G1's pinned non-news inputs through the single gateway."""

    market = load_stage2_asset("MARKET_BARS", MARKET_BARS_PATH, counters)
    universe = load_stage2_asset(
        "UNIVERSE_SNAPSHOT",
        UNIVERSE_SNAPSHOT_ABSOLUTE_PATH,
        counters,
    )
    _assert_exact_market_universe_tickers(market.payload, universe.payload)
    return G1Stage2LoadedInputs(
        market_bars=market.payload,
        universe_snapshot=universe.payload,
        receipts=(market.receipt, universe.receipt),
    )


class G1FoldValidationWindowIdentity(StrictModel):
    fold_end_year: int
    first_validation_at: datetime
    last_validation_at: datetime
    decision_count: int = Field(gt=0)
    decisions_sha256: str = Field(pattern=SHA256_PATTERN)
    window_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_window(self) -> "G1FoldValidationWindowIdentity":
        if self.fold_end_year not in T0_FOLD_END_YEARS:
            raise R03G1Stage2AccessError("unknown development fold window")
        if self.first_validation_at.year != self.fold_end_year:
            raise R03G1Stage2AccessError("fold first validation year mismatch")
        if self.last_validation_at.year != self.fold_end_year:
            raise R03G1Stage2AccessError("fold last validation year mismatch")
        if self.last_validation_at < self.first_validation_at:
            raise R03G1Stage2AccessError("fold validation window is reversed")
        unsigned = self.model_dump(mode="json", exclude={"window_sha256"})
        if canonical_sha256(unsigned) != self.window_sha256:
            raise R03G1Stage2AccessError("fold validation window hash mismatch")
        return self


class G1GreedyFeasibleDiagnostic(StrictModel):
    cost_bps_per_side: int
    decision_count: int = Field(gt=0)
    total_utility_e12: int
    t0_total_utility_e12: int
    lower_headroom_point_estimate_e12: int
    gate_bearing: Literal[False] = False
    diagnostic_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_diagnostic(self) -> "G1GreedyFeasibleDiagnostic":
        if self.cost_bps_per_side not in T0_COST_CELLS_BPS:
            raise R03G1Stage2AccessError("greedy diagnostic cost cell mismatch")
        expected_lower = int((Decimal(self.total_utility_e12 - self.t0_total_utility_e12) / Decimal(self.decision_count)).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
        if self.lower_headroom_point_estimate_e12 != expected_lower:
            raise R03G1Stage2AccessError("greedy diagnostic lower-headroom mismatch")
        unsigned = self.model_dump(mode="json", exclude={"diagnostic_sha256"})
        if canonical_sha256(unsigned) != self.diagnostic_sha256:
            raise R03G1Stage2AccessError("greedy diagnostic hash mismatch")
        return self


class G1Stage2AggregateRecord(StrictModel):
    schema_version: Literal["r03-g1-stage2-aggregate-record-v1"] = "r03-g1-stage2-aggregate-record-v1"
    output_path: Literal[".research_artifacts/r03-news-reasoning/g1-stage2-execution-record-v1.json"] = G1_AGGREGATE_OUTPUT_PATH
    serialization_rule: Literal["CANONICAL_JSON_UTF8_SORTED_KEYS_NO_INSIGNIFICANT_WHITESPACE_EXACTLY_ONE_TRAILING_LF_CREATE_EXCLUSIVE_V1"] = G1_AGGREGATE_SERIALIZATION_RULE
    runner_protocol_sha256: str = Field(pattern=SHA256_PATTERN)
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    io_runtime_sha256: str = Field(pattern=SHA256_PATTERN)
    asset_receipts: tuple[Stage2AssetLoadReceipt, Stage2AssetLoadReceipt]
    zero_call_manifest: Stage2ZeroCallManifest
    allowed_asset_reads: Literal[2]
    session_count_through_calibration_labels: int = Field(gt=0)
    structural_burn_in_session_count: Literal[61]
    fit_row_count: int = Field(gt=0)
    development_decision_count: int = Field(gt=0)
    calibration_decision_count: int = Field(gt=0)
    fold_validation_windows: tuple[G1FoldValidationWindowIdentity, ...]
    alpha_selection_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_t0_alpha_e1: int
    t0_model_series_id: str = Field(pattern=SHA256_PATTERN)
    bound_certificate_count: int = Field(gt=0)
    bound_certificate_root_sha256: str = Field(pattern=SHA256_PATTERN)
    greedy_feasible_diagnostics: tuple[G1GreedyFeasibleDiagnostic, ...]
    g1_execution_record: G1ExecutionRecord
    aggregate_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_aggregate(self) -> "G1Stage2AggregateRecord":
        protocol = stage2_runner_protocol_identity()
        if self.runner_protocol_sha256 != protocol.runner_protocol_sha256:
            raise R03G1Stage2AccessError("aggregate runner protocol mismatch")
        if self.t0_protocol_id != protocol.t0_protocol_id:
            raise R03G1Stage2AccessError("aggregate T0 protocol mismatch")
        if tuple(window.fold_end_year for window in self.fold_validation_windows) != T0_FOLD_END_YEARS:
            raise R03G1Stage2AccessError("aggregate fold-window coverage mismatch")
        if tuple(item.cost_bps_per_side for item in self.greedy_feasible_diagnostics) != T0_COST_CELLS_BPS:
            raise R03G1Stage2AccessError("aggregate greedy diagnostic coverage mismatch")
        if self.g1_execution_record.t0_protocol_id != self.t0_protocol_id:
            raise R03G1Stage2AccessError("aggregate G1/T0 protocol mismatch")
        if self.g1_execution_record.t0_model_series_id != self.t0_model_series_id:
            raise R03G1Stage2AccessError("aggregate G1/T0 series mismatch")
        if self.g1_execution_record.bound_certificate_root_sha256 != self.bound_certificate_root_sha256:
            raise R03G1Stage2AccessError("aggregate bound-certificate root mismatch")
        unsigned = self.model_dump(mode="json", exclude={"aggregate_sha256"})
        if canonical_sha256(unsigned) != self.aggregate_sha256:
            raise R03G1Stage2AccessError("aggregate record hash mismatch")
        return self


@dataclass(frozen=True)
class G1PreparedFrame:
    session_dates: tuple[date, ...]
    rows: tuple[T0FitRowMetadata, ...]
    row_tickers: tuple[str, ...]
    feature_matrix: tuple[tuple[float, ...], ...]
    target_e12: tuple[int, ...]
    decision_ordinals: Mapping[datetime, int]
    realized_by_decision: Mapping[datetime, dict[str, int]]
    development_decisions: tuple[datetime, ...]
    calibration_decisions: tuple[datetime, ...]
    calibration_coverage_end_exclusive_at: datetime
    fold_validation_windows: tuple[G1FoldValidationWindowIdentity, ...]


def _nominal_decision_at(session_date: date) -> datetime:
    return datetime.combine(
        session_date,
        time(15, 30),
        tzinfo=ZoneInfo("America/New_York"),
    )


def _split_name(session_date: date) -> str:
    matches = tuple(split.name for split in frozen_splits() if split.start <= session_date <= split.end)
    if len(matches) != 1:
        raise R03G1Stage2AccessError("session date lacks one frozen split")
    return matches[0]


def t0_row_id(
    split_name: str,
    decision_session_ordinal: int,
    decision_date: date,
    ticker: str,
) -> str:
    if decision_session_ordinal < 1 or "|" in split_name or "|" in ticker:
        raise R03G1Stage2AccessError("invalid T0 row-id component")
    return f"{split_name}|{decision_session_ordinal:06d}|" f"{decision_date.isoformat()}|{ticker}"


def g1_bound_decision_id(decision_session_ordinal: int, decision_date: date) -> str:
    if decision_session_ordinal < 1:
        raise R03G1Stage2AccessError("invalid bound-certificate decision ordinal")
    return f"CALIBRATION|{decision_session_ordinal:06d}|{decision_date.isoformat()}"


def _validate_session_topology(session_dates: tuple[date, ...]) -> None:
    splits = frozen_splits()[:4]
    if len(session_dates) != sum(split.session_count for split in splits):
        raise R03G1Stage2AccessError("G1 session count through calibration labels mismatch")
    for split in splits:
        members = tuple(value for value in session_dates if split.start <= value <= split.end)
        if len(members) != split.session_count:
            raise R03G1Stage2AccessError(f"{split.name} session count mismatch")
        if members[0] != split.start or members[-1] != split.end:
            raise R03G1Stage2AccessError(f"{split.name} session boundary mismatch")


def _g1_market_arrays(
    market_bars: object,
    universe_snapshot: UniverseSnapshot,
) -> tuple[tuple[date, ...], tuple[str, ...], object, object]:
    import numpy as np
    import pyarrow as pa
    import pyarrow.compute as pc

    timestamp_type = market_bars.schema.field("timestamp").type
    cutoff = pa.scalar(G1_EXECUTION_DATA_END_EXCLUSIVE_UTC, type=timestamp_type)
    filtered = market_bars.filter(pc.less(market_bars.column("timestamp"), cutoff))
    columns = filtered.select(("ticker", "timestamp", "close", "volume")).to_pydict()
    timestamps = tuple(columns["timestamp"])
    distinct_timestamps = tuple(sorted(set(timestamps)))
    if not distinct_timestamps:
        raise R03G1Stage2AccessError("G1 market panel is empty")
    if any(value.tzinfo is None or value.utcoffset() is None for value in distinct_timestamps):
        raise R03G1Stage2AccessError("G1 market session timestamp is naive")
    session_dates = tuple(value.astimezone(timezone.utc).date() for value in distinct_timestamps)
    if len(set(session_dates)) != len(session_dates):
        raise R03G1Stage2AccessError("multiple pinned timestamps map to one UTC session date")
    _validate_session_topology(session_dates)

    tickers = tuple(entry.ticker for entry in universe_snapshot.ticker_sector_mapping)
    ticker_index = {ticker: index for index, ticker in enumerate(tickers)}
    session_index = {value: index for index, value in enumerate(distinct_timestamps)}
    closes = np.full((len(session_dates), len(tickers)), np.nan, dtype=np.float64)
    volumes = np.full((len(session_dates), len(tickers)), np.nan, dtype=np.float64)
    seen: set[tuple[int, int]] = set()
    for ticker, timestamp, close, volume in zip(
        columns["ticker"],
        columns["timestamp"],
        columns["close"],
        columns["volume"],
    ):
        if ticker not in ticker_index or timestamp not in session_index:
            raise R03G1Stage2AccessError("G1 market row escapes pinned panel")
        key = (session_index[timestamp], ticker_index[ticker])
        if key in seen:
            raise R03G1Stage2AccessError("duplicate ticker-session market row")
        seen.add(key)
        close_value = float(close)
        volume_value = float(volume)
        if math.isfinite(close_value) and close_value > 0:
            closes[key] = close_value
        if math.isfinite(volume_value) and volume_value > 0:
            volumes[key] = volume_value
    return session_dates, tickers, closes, volumes


def _raw_t0_features(
    returns: object,
    closes: object,
    volumes: object,
    sector_returns: Mapping[str, object],
    universe_returns: object,
    *,
    ticker_index: int,
    sector: str,
    decision_index: int,
) -> dict[str, float | None]:
    import numpy as np

    def complete(values: object, expected: int) -> bool:
        array = np.asarray(values, dtype=np.float64)
        return len(array) == expected and bool(np.isfinite(array).all())

    result: dict[str, float | None] = {}
    for window in (5, 20, 60):
        own = returns[decision_index - window : decision_index, ticker_index]
        peers = sector_returns[sector][decision_index - window : decision_index]
        value = float(np.sum(own - peers)) if complete(own, window) and complete(peers, window) else None
        result[f"sector_relative_log_return_{window}"] = value
    for window in (20, 60):
        own = returns[decision_index - window : decision_index, ticker_index]
        result[f"volatility_{window}"] = float(np.std(own, ddof=0)) if complete(own, window) else None
    downside = returns[decision_index - 20 : decision_index, ticker_index]
    result["downside_semideviation_20"] = float(np.sqrt(np.mean(np.minimum(downside, 0.0) ** 2))) if complete(downside, 20) else None
    own_60 = returns[decision_index - 60 : decision_index, ticker_index]
    market_60 = universe_returns[decision_index - 60 : decision_index]
    beta: float | None = None
    if complete(own_60, 60) and complete(market_60, 60):
        centered_market = market_60 - np.mean(market_60)
        denominator = float(centered_market @ centered_market)
        if denominator > 0:
            beta = float(centered_market @ (own_60 - np.mean(own_60)) / denominator)
    result["sector_beta_60"] = beta
    close_20 = closes[decision_index - 20 : decision_index, ticker_index]
    volume_20 = volumes[decision_index - 20 : decision_index, ticker_index]
    result["mean_log_dollar_volume_20"] = float(np.mean(np.log(close_20 * volume_20))) if complete(close_20, 20) and complete(volume_20, 20) else None
    volume_5 = volumes[decision_index - 5 : decision_index, ticker_index]
    result["volume_shock_5_vs_20"] = float(np.log(np.mean(volume_5) / np.mean(volume_20))) if complete(volume_5, 5) and complete(volume_20, 20) else None
    return result


def _fold_validation_windows(
    development_decisions: tuple[datetime, ...],
) -> tuple[G1FoldValidationWindowIdentity, ...]:
    windows = []
    for fold_end_year in T0_FOLD_END_YEARS:
        decisions = tuple(value for value in development_decisions if value.year == fold_end_year)
        if not decisions:
            raise R03G1Stage2AccessError("development fold validation window is empty")
        unsigned = {
            "fold_end_year": fold_end_year,
            "first_validation_at": decisions[0],
            "last_validation_at": decisions[-1],
            "decision_count": len(decisions),
            "decisions_sha256": canonical_sha256(tuple(value.isoformat() for value in decisions)),
        }
        candidate = G1FoldValidationWindowIdentity.model_construct(
            **unsigned,
            window_sha256="0" * 64,
        )
        hash_input = candidate.model_dump(mode="json", exclude={"window_sha256"})
        windows.append(
            G1FoldValidationWindowIdentity(
                **unsigned,
                window_sha256=canonical_sha256(hash_input),
            )
        )
    return tuple(windows)


def build_g1_prepared_frame(
    market_bars: object,
    universe_snapshot: UniverseSnapshot,
) -> G1PreparedFrame:
    """Materialize only development/calibration T0 rows from pinned non-news bars."""

    import numpy as np

    session_dates, tickers, closes, volumes = _g1_market_arrays(
        market_bars,
        universe_snapshot,
    )
    sectors = {entry.ticker: entry.sector for entry in universe_snapshot.ticker_sector_mapping}
    returns = np.full_like(closes, np.nan)
    valid_pairs = np.isfinite(closes[1:]) & np.isfinite(closes[:-1])
    returns[1:][valid_pairs] = np.log(closes[1:][valid_pairs] / closes[:-1][valid_pairs])
    universe_returns = np.full(len(session_dates), np.nan, dtype=np.float64)
    sector_returns = {sector: np.full(len(session_dates), np.nan, dtype=np.float64) for sector in sorted(set(sectors.values()))}
    sector_indices = {sector: tuple(index for index, ticker in enumerate(tickers) if sectors[ticker] == sector) for sector in sector_returns}
    for session_index in range(len(session_dates)):
        values = returns[session_index]
        valid = values[np.isfinite(values)]
        if len(valid):
            universe_returns[session_index] = float(np.mean(valid))
        for sector, indices in sector_indices.items():
            sector_values = values[list(indices)]
            sector_valid = sector_values[np.isfinite(sector_values)]
            if len(sector_valid):
                sector_returns[sector][session_index] = float(np.mean(sector_valid))

    rows: list[T0FitRowMetadata] = []
    row_tickers: list[str] = []
    feature_matrix: list[tuple[float, ...]] = []
    targets: list[int] = []
    decision_ordinals: dict[datetime, int] = {}
    realized_by_decision: dict[datetime, dict[str, int]] = {}
    development_decisions: list[datetime] = []
    calibration_decisions: list[datetime] = []
    for decision_index, decision_date in enumerate(session_dates):
        if decision_index < G1_STRUCTURAL_BURN_IN_SESSIONS:
            continue
        if decision_index + 5 >= len(session_dates):
            continue
        split_name = _split_name(decision_date)
        if split_name not in {"DEVELOPMENT", "CALIBRATION"}:
            continue
        decision_at = _nominal_decision_at(decision_date)
        ordinal = decision_index + 1
        raw_rows = {
            ticker: _raw_t0_features(
                returns,
                closes,
                volumes,
                sector_returns,
                universe_returns,
                ticker_index=ticker_index,
                sector=sectors[ticker],
                decision_index=decision_index,
            )
            for ticker_index, ticker in enumerate(tickers)
        }
        processed = preprocess_t0_cross_section(raw_rows, sectors)
        closes_t = {ticker: float(closes[decision_index, ticker_index]) for ticker_index, ticker in enumerate(tickers) if math.isfinite(float(closes[decision_index, ticker_index]))}
        closes_t5 = {ticker: float(closes[decision_index + 5, ticker_index]) for ticker_index, ticker in enumerate(tickers) if math.isfinite(float(closes[decision_index + 5, ticker_index]))}
        outcomes = sector_relative_outcomes_e12(closes_t, closes_t5, sectors)
        if len(outcomes) < 20:
            raise R03G1Stage2AccessError("fewer than 20 valid h=5 outcomes")
        feature_cutoff_at = _nominal_decision_at(session_dates[decision_index - 1])
        label_maturity_at = _nominal_decision_at(session_dates[decision_index + 5])
        for ticker in sorted(outcomes):
            rows.append(
                T0FitRowMetadata(
                    row_id=t0_row_id(split_name, ordinal, decision_date, ticker),
                    decision_at=decision_at,
                    feature_cutoff_at=feature_cutoff_at,
                    label_maturity_at=label_maturity_at,
                    decision_session_ordinal=ordinal,
                    feature_session_ordinal=ordinal - 1,
                    label_session_ordinal=ordinal + 5,
                    split_name=split_name,
                    phase_book=phase_book_for_session(ordinal),
                )
            )
            row_tickers.append(ticker)
            feature_matrix.append(processed[ticker])
            targets.append(outcomes[ticker])
        decision_ordinals[decision_at] = ordinal
        realized_by_decision[decision_at] = outcomes
        if split_name == "DEVELOPMENT":
            development_decisions.append(decision_at)
        else:
            calibration_decisions.append(decision_at)

    development = tuple(development_decisions)
    calibration = tuple(calibration_decisions)
    if not development or not calibration:
        raise R03G1Stage2AccessError("G1 prepared frame lacks required decisions")
    purge_2_start = frozen_splits()[3].start
    return G1PreparedFrame(
        session_dates=session_dates,
        rows=tuple(rows),
        row_tickers=tuple(row_tickers),
        feature_matrix=tuple(feature_matrix),
        target_e12=tuple(targets),
        decision_ordinals=decision_ordinals,
        realized_by_decision=realized_by_decision,
        development_decisions=development,
        calibration_decisions=calibration,
        calibration_coverage_end_exclusive_at=_nominal_decision_at(purge_2_start),
        fold_validation_windows=_fold_validation_windows(development),
    )


def _scores_from_predictions(
    prepared: G1PreparedFrame,
    predictions: Mapping[str, float],
    decisions: Sequence[datetime],
) -> dict[datetime, dict[str, float]]:
    decision_set = set(decisions)
    scores = {decision: {} for decision in decisions}
    for row, ticker in zip(prepared.rows, prepared.row_tickers):
        if row.decision_at not in decision_set:
            continue
        if row.row_id not in predictions:
            raise R03G1Stage2AccessError("prediction coverage misses a prepared row")
        value = float(predictions[row.row_id])
        if not math.isfinite(value):
            raise R03G1Stage2AccessError("T0 prediction is non-finite")
        scores[row.decision_at][ticker] = value
    if any(len(scores[decision]) < 20 for decision in decisions):
        raise R03G1Stage2AccessError("T0 scoring decision has fewer than 20 names")
    return scores


def _t0_utility_series(
    prepared: G1PreparedFrame,
    decisions: Sequence[datetime],
    scores: Mapping[datetime, Mapping[str, float]],
    *,
    cost_bps_per_side: int,
) -> tuple[int, ...]:
    previous_by_phase: dict[int, object] = {}
    utilities = []
    for decision in decisions:
        ordinal = prepared.decision_ordinals[decision]
        phase = phase_book_for_session(ordinal)
        previous = previous_by_phase.get(phase)
        book = construct_buffered_book(dict(scores[decision]), previous)
        utilities.append(
            net_book_utility_e12(
                book,
                prepared.realized_by_decision[decision],
                previous,
                cost_bps_per_side,
            )
        )
        previous_by_phase[phase] = book
    return tuple(utilities)


def select_g1_development_alpha(
    prepared: G1PreparedFrame,
    *,
    runtime: T0RuntimeIdentity,
) -> T0AlphaSelection:
    utilities: dict[int, dict[tuple[int, int], int]] = {}
    run_hashes: dict[int, dict[int, str]] = {}
    for alpha in T0_ALPHA_E1_GRID:
        utilities[alpha] = {}
        run_hashes[alpha] = {}
        for window in prepared.fold_validation_windows:
            decisions = tuple(value for value in prepared.development_decisions if value.year == window.fold_end_year)
            run, predictions = fit_t0_development_fold_candidate(
                prepared.rows,
                prepared.feature_matrix,
                prepared.target_e12,
                validation_decisions=decisions,
                fold_end_year=window.fold_end_year,
                t0_alpha_e1=alpha,
                runtime=runtime,
            )
            run_hashes[alpha][window.fold_end_year] = run.run_sha256
            scores = _scores_from_predictions(prepared, predictions, decisions)
            for cost in T0_COST_CELLS_BPS:
                series = _t0_utility_series(
                    prepared,
                    decisions,
                    scores,
                    cost_bps_per_side=cost,
                )
                utilities[alpha][(window.fold_end_year, cost)] = mean_e12(list(series))
    return select_t0_alpha(utilities, run_hashes)


def _calibration_scores(
    prepared: G1PreparedFrame,
    model_series: T0ModelSeriesIdentity,
) -> dict[datetime, dict[str, float]]:
    predictions: dict[str, float] = {}
    for decision in prepared.calibration_decisions:
        indices = tuple(index for index, row in enumerate(prepared.rows) if row.decision_at == decision)
        snapshot = serving_snapshot(model_series, decision)
        values = predict_t0(
            snapshot,
            tuple(prepared.feature_matrix[index] for index in indices),
        )
        for index, value in zip(indices, values):
            predictions[prepared.rows[index].row_id] = float(value)
    return _scores_from_predictions(
        prepared,
        predictions,
        prepared.calibration_decisions,
    )


def _greedy_diagnostics(
    prepared: G1PreparedFrame,
    t0_utilities_by_cost_e12: Mapping[int, tuple[int, ...]],
) -> tuple[G1GreedyFeasibleDiagnostic, ...]:
    from v2.research.news_reasoning.r03_headroom import (
        greedy_feasible_lower_bracket_e12,
    )

    realized = tuple(prepared.realized_by_decision[decision] for decision in prepared.calibration_decisions)
    if set(t0_utilities_by_cost_e12) != set(T0_COST_CELLS_BPS):
        raise R03G1Stage2AccessError("greedy diagnostics require exact 5/10/15 bp T0 series")
    diagnostics = []
    for cost in T0_COST_CELLS_BPS:
        t0_utilities = t0_utilities_by_cost_e12[cost]
        if len(t0_utilities) != len(realized):
            raise R03G1Stage2AccessError("greedy/T0 diagnostic series length mismatch")
        greedy_total = greedy_feasible_lower_bracket_e12(
            realized,
            cost_bps_per_side=cost,
        )
        t0_total = sum(t0_utilities)
        lower_headroom = int((Decimal(greedy_total - t0_total) / Decimal(len(realized))).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
        unsigned = {
            "cost_bps_per_side": cost,
            "decision_count": len(realized),
            "total_utility_e12": greedy_total,
            "t0_total_utility_e12": t0_total,
            "lower_headroom_point_estimate_e12": lower_headroom,
            "gate_bearing": False,
        }
        diagnostics.append(
            G1GreedyFeasibleDiagnostic(
                **unsigned,
                diagnostic_sha256=canonical_sha256(unsigned),
            )
        )
    return tuple(diagnostics)


def _build_aggregate_record(
    *,
    runner_protocol: Stage2RunnerProtocolIdentity,
    io_runtime: Stage2IORuntimeIdentity,
    inputs: G1Stage2LoadedInputs,
    counters: Stage2AccessCounters,
    prepared: G1PreparedFrame,
    alpha_selection: T0AlphaSelection,
    model_series: T0ModelSeriesIdentity,
    bound_certificate_root_sha256: str,
    greedy_diagnostics: tuple[G1GreedyFeasibleDiagnostic, ...],
    execution_record: G1ExecutionRecord,
) -> G1Stage2AggregateRecord:
    if counters.allowed_asset_reads != 2:
        raise R03G1Stage2AccessError("execution path must perform exactly two pinned reads")
    manifest = build_zero_call_manifest(counters)
    unsigned = {
        "schema_version": "r03-g1-stage2-aggregate-record-v1",
        "output_path": G1_AGGREGATE_OUTPUT_PATH,
        "serialization_rule": G1_AGGREGATE_SERIALIZATION_RULE,
        "runner_protocol_sha256": runner_protocol.runner_protocol_sha256,
        "t0_protocol_id": runner_protocol.t0_protocol_id,
        "io_runtime_sha256": io_runtime.runtime_sha256,
        "asset_receipts": inputs.receipts,
        "zero_call_manifest": manifest,
        "allowed_asset_reads": counters.allowed_asset_reads,
        "session_count_through_calibration_labels": len(prepared.session_dates),
        "structural_burn_in_session_count": G1_STRUCTURAL_BURN_IN_SESSIONS,
        "fit_row_count": len(prepared.rows),
        "development_decision_count": len(prepared.development_decisions),
        "calibration_decision_count": len(prepared.calibration_decisions),
        "fold_validation_windows": prepared.fold_validation_windows,
        "alpha_selection_sha256": alpha_selection.selection_sha256,
        "selected_t0_alpha_e1": alpha_selection.selected_t0_alpha_e1,
        "t0_model_series_id": model_series.t0_model_series_id,
        "bound_certificate_count": len(prepared.calibration_decisions),
        "bound_certificate_root_sha256": bound_certificate_root_sha256,
        "greedy_feasible_diagnostics": greedy_diagnostics,
        "g1_execution_record": execution_record,
    }
    candidate = G1Stage2AggregateRecord.model_construct(**unsigned, aggregate_sha256="0" * 64)
    hash_input = candidate.model_dump(mode="json", exclude={"aggregate_sha256"})
    return G1Stage2AggregateRecord(**unsigned, aggregate_sha256=canonical_sha256(hash_input))


def serialize_g1_stage2_aggregate(record: G1Stage2AggregateRecord) -> bytes:
    payload = canonical_json_bytes(record.model_dump(mode="json"))
    if payload.endswith(b"\n"):
        raise R03G1Stage2AccessError("canonical aggregate unexpectedly ends with LF")
    return payload + b"\n"


def _write_g1_stage2_aggregate(record: G1Stage2AggregateRecord) -> None:
    output_path = Path(WORKSPACE_ROOT, G1_AGGREGATE_OUTPUT_PATH)
    try:
        with output_path.open("xb") as handle:
            handle.write(serialize_g1_stage2_aggregate(record))
    except FileExistsError as exc:
        raise R03G1Stage2AccessError("refusing to overwrite G1 aggregate record") from exc


def run_g1_stage2(preparation_commit_sha: str) -> G1Stage2AggregateRecord:
    """Run the reviewed G1 execution path and write its fixed aggregate record."""

    assert_single_thread_environment()
    derive_g1_seed(preparation_commit_sha)
    runner_protocol = stage2_runner_protocol_identity()
    t0_protocol = t0_protocol_identity()
    if t0_protocol.protocol_sha256 != G1_REVIEWED_T0_PROTOCOL_ID:
        raise R03G1Stage2AccessError("reviewed T0 protocol identity mismatch")
    if runner_protocol.runner_protocol_sha256 != G1_REVIEWED_STAGE2_RUNNER_PROTOCOL_ID:
        raise R03G1Stage2AccessError("reviewed runner protocol identity mismatch")
    if runner_protocol.t0_protocol_id != t0_protocol.protocol_sha256:
        raise R03G1Stage2AccessError("runner/T0 protocol identity mismatch")
    counters = Stage2AccessCounters()
    inputs = load_g1_stage2_inputs(counters)
    expected_pins = stage2_asset_pins()
    if tuple(receipt.role for receipt in inputs.receipts) != tuple(pin.role for pin in expected_pins):
        raise R03G1Stage2AccessError("execution receipt role coverage mismatch")
    if tuple(receipt.sha256 for receipt in inputs.receipts) != tuple(pin.sha256 for pin in expected_pins):
        raise R03G1Stage2AccessError("execution receipt pin mismatch")
    io_runtime = installed_stage2_io_runtime_identity()
    prepared = build_g1_prepared_frame(inputs.market_bars, inputs.universe_snapshot)
    runtime = initialize_t0_numeric_runtime()
    alpha_selection = select_g1_development_alpha(prepared, runtime=runtime)
    model_series = fit_t0_calibration_series(
        prepared.rows,
        prepared.feature_matrix,
        prepared.target_e12,
        calibration_decisions=prepared.calibration_decisions,
        coverage_end_exclusive_at=prepared.calibration_coverage_end_exclusive_at,
        alpha_selection=alpha_selection,
        runtime=runtime,
        protocol=t0_protocol,
    )
    scores = _calibration_scores(prepared, model_series)
    from v2.research.news_reasoning.r03_headroom import make_bound_certificate

    certificates = tuple(
        make_bound_certificate(
            g1_bound_decision_id(
                prepared.decision_ordinals[decision],
                decision.date(),
            ),
            prepared.realized_by_decision[decision],
        )
        for decision in prepared.calibration_decisions
    )
    certificate_root = canonical_sha256(tuple(certificate.certificate_sha256 for certificate in certificates))
    differences_by_cost = {}
    t0_utilities_by_cost = {}
    for cost in T0_COST_CELLS_BPS:
        t0_utilities = _t0_utility_series(
            prepared,
            prepared.calibration_decisions,
            scores,
            cost_bps_per_side=cost,
        )
        t0_utilities_by_cost[cost] = t0_utilities
        differences_by_cost[cost] = tuple(certificate.bound_e12 - t0_utility for certificate, t0_utility in zip(certificates, t0_utilities))
    greedy_diagnostics = _greedy_diagnostics(prepared, t0_utilities_by_cost)
    execution_record = evaluate_g1_cost_cells(
        differences_by_cost,
        greedy_feasible_lower_by_cost_e12={item.cost_bps_per_side: item.lower_headroom_point_estimate_e12 for item in greedy_diagnostics},
        preparation_commit_sha=preparation_commit_sha,
        t0_model_series_id=model_series.t0_model_series_id,
        bound_certificate_root_sha256=certificate_root,
        thread_environment_preconfigured_before_process_start=True,
        protocol=t0_protocol,
    )
    aggregate = _build_aggregate_record(
        runner_protocol=runner_protocol,
        io_runtime=io_runtime,
        inputs=inputs,
        counters=counters,
        prepared=prepared,
        alpha_selection=alpha_selection,
        model_series=model_series,
        bound_certificate_root_sha256=certificate_root,
        greedy_diagnostics=greedy_diagnostics,
        execution_record=execution_record,
    )
    _write_g1_stage2_aggregate(aggregate)
    return aggregate
