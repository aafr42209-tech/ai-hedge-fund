"""Fail-closed R03 G1 Stage 2 data-access gateway.

This module owns the only filesystem-reading function in the Stage 2 path.
Remediation tests must replace its filesystem and parquet calls with synthetic
test doubles. Real asset access remains separately authorized.
"""

from __future__ import annotations

import hashlib
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from v2.research.news_reasoning.r03_g1_execution import (
    G1_MARKET_UNIVERSE_TICKER_RULE,
    G1_SESSION_ORDINAL_RULE,
    G1_STAGE2_ASSET_ACCESS_RULE,
    initialize_t0_numeric_runtime,
    t0_protocol_identity,
    T0_UNIVERSE_SNAPSHOT_FILE_SHA256,
    T0_UNIVERSE_SNAPSHOT_PATH,
    T0_UNIVERSE_SNAPSHOT_SHA256,
    T0_UNIVERSE_SOURCE_PATH,
    T0_UNIVERSE_SOURCE_SHA256,
)
from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import StrictModel

SHA256_PATTERN = r"^[0-9a-f]{64}$"
MARKET_BARS_PATH = "C:/Users/User/Desktop/FinGPT/data/raw/market_bars_real.parquet"
MARKET_BARS_SHA256 = "9ae1625de0fb91e0c6abaab18b0637a0798abc035368622e5f1aba84e0dec011"
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
UNIVERSE_SNAPSHOT_ABSOLUTE_PATH = os.path.abspath(os.path.join(WORKSPACE_ROOT, T0_UNIVERSE_SNAPSHOT_PATH))
NOMINAL_DECISION_TIME = "15:30:00_AMERICA_NEW_YORK"
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
    schema_version: Literal["r03-g1-stage2-runner-protocol-v1"] = "r03-g1-stage2-runner-protocol-v1"
    t0_protocol_id: str = Field(pattern=SHA256_PATTERN)
    asset_access_rule: Literal["EXACT_RESOLVED_ABSOLUTE_PATH_MATCH_ONLY_NO_PREFIX_NO_RECURSION"]
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
        "schema_version": "r03-g1-stage2-runner-protocol-v1",
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
