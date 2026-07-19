"""Synthetic-safe R03 calendar, split, portfolio, and utility mechanics."""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from v2.research.overlay.arithmetic import round_ratio_half_even
from v2.research.overlay.canonical import canonical_sha256
from v2.research.overlay.contracts import StrictModel

from .r03_contracts import (
    e12_from_float,
    mean_e12,
    R03ContractError,
    R03FrameRow,
    R03SplitRecord,
)

NEW_YORK = ZoneInfo("America/New_York")
HORIZON_SESSIONS = 5
LEG_SIZE = 10
BUFFER_RANK = 20


class R03FrameError(R03ContractError):
    pass


class R03PortfolioBook(StrictModel):
    schema_version: str = "r03-buffered-book-v1"
    long_tickers: tuple[str, ...]
    short_tickers: tuple[str, ...]
    no_trade: bool
    book_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_book(self) -> "R03PortfolioBook":
        if self.no_trade:
            if self.long_tickers or self.short_tickers:
                raise R03FrameError("no-trade book must have empty legs")
        elif len(self.long_tickers) != LEG_SIZE or len(self.short_tickers) != LEG_SIZE:
            raise R03FrameError("trading book requires ten names per leg")
        if set(self.long_tickers) & set(self.short_tickers):
            raise R03FrameError("portfolio legs overlap")
        unsigned = self.model_dump(mode="json", exclude={"book_sha256"})
        if canonical_sha256(unsigned) != self.book_sha256:
            raise R03FrameError("book hash mismatch")
        return self


def frozen_splits() -> tuple[R03SplitRecord, ...]:
    return (
        R03SplitRecord(name="DEVELOPMENT", start=date(2016, 1, 4), end=date(2020, 12, 23), session_count=1254, permitted_use="FIT_SELECT"),
        R03SplitRecord(name="PURGE_1", start=date(2020, 12, 24), end=date(2020, 12, 31), session_count=5, permitted_use="PURGE"),
        R03SplitRecord(name="CALIBRATION", start=date(2021, 1, 4), end=date(2022, 12, 22), session_count=498, permitted_use="CALIBRATION_GATE"),
        R03SplitRecord(name="PURGE_2", start=date(2022, 12, 23), end=date(2022, 12, 30), session_count=5, permitted_use="PURGE"),
        R03SplitRecord(name="PROCEDURAL_OOS", start=date(2023, 1, 3), end=date(2025, 12, 23), session_count=747, permitted_use="SEALED_OOS"),
        R03SplitRecord(name="LABEL_ONLY", start=date(2025, 12, 24), end=date(2025, 12, 31), session_count=5, permitted_use="LABEL_ONLY"),
    )


def validate_split_topology(splits: tuple[R03SplitRecord, ...]) -> str:
    if tuple(split.name for split in splits) != ("DEVELOPMENT", "PURGE_1", "CALIBRATION", "PURGE_2", "PROCEDURAL_OOS", "LABEL_ONLY"):
        raise R03FrameError("split topology order mismatch")
    for left, right in zip(splits, splits[1:]):
        if left.end >= right.start:
            raise R03FrameError("split date ranges overlap")
    for split in splits:
        if split.permitted_use == "PURGE" and split.session_count < HORIZON_SESSIONS:
            raise R03FrameError("purge shorter than h=5")
    if splits[-1].session_count < HORIZON_SESSIONS:
        raise R03FrameError("label tail shorter than h=5")
    return canonical_sha256([split.model_dump(mode="json") for split in splits])


def decision_clock(actual_close: datetime) -> datetime:
    if actual_close.tzinfo is None or actual_close.utcoffset() is None:
        raise R03FrameError("actual close must be timezone-aware")
    local_close = actual_close.astimezone(NEW_YORK)
    fixed_cap = datetime.combine(local_close.date(), time(15, 30), tzinfo=NEW_YORK)
    return min(fixed_cap, local_close - timedelta(minutes=30))


def phase_book_for_session(session_ordinal: int) -> int:
    if session_ordinal < 0:
        raise R03FrameError("session ordinal must be nonnegative")
    return session_ordinal % HORIZON_SESSIONS


def assert_frame_row_available(row: R03FrameRow, as_of: datetime, *, permit_oos: bool = False) -> None:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise R03FrameError("as_of must be timezone-aware")
    if row.feature_cutoff_at >= row.decision_at or row.feature_cutoff_at > as_of:
        raise R03FrameError("feature leakage")
    if row.outcome_e12 is not None and row.label_maturity_at > as_of:
        raise R03FrameError("unmatured outcome access")
    if row.decision_at.date() >= date(2023, 1, 3) and not permit_oos:
        raise R03FrameError("procedural OOS access is not authorized")


def _book(long_tickers: tuple[str, ...], short_tickers: tuple[str, ...], no_trade: bool) -> R03PortfolioBook:
    unsigned = {
        "schema_version": "r03-buffered-book-v1",
        "long_tickers": list(long_tickers),
        "short_tickers": list(short_tickers),
        "no_trade": no_trade,
    }
    return R03PortfolioBook(
        long_tickers=long_tickers,
        short_tickers=short_tickers,
        no_trade=no_trade,
        book_sha256=canonical_sha256(unsigned),
    )


def construct_buffered_book(
    scores: dict[str, float],
    previous: R03PortfolioBook | None = None,
) -> R03PortfolioBook:
    clean: dict[str, float] = {}
    for ticker, score in scores.items():
        score = float(score)
        if math.isfinite(score):
            clean[ticker] = 0.0 if score == 0.0 else score
    if len(clean) < 2 * LEG_SIZE:
        return _book((), (), True)
    descending = sorted(clean, key=lambda ticker: (-clean[ticker], ticker))
    ascending = sorted(clean, key=lambda ticker: (clean[ticker], ticker))
    previous_longs = () if previous is None or previous.no_trade else previous.long_tickers
    previous_shorts = () if previous is None or previous.no_trade else previous.short_tickers
    long_buffer = set(descending[:BUFFER_RANK])
    short_buffer = set(ascending[:BUFFER_RANK])
    longs = [ticker for ticker in descending if ticker in previous_longs and ticker in long_buffer]
    longs.extend(ticker for ticker in descending if ticker not in longs)
    longs = longs[:LEG_SIZE]
    shorts = [ticker for ticker in ascending if ticker in previous_shorts and ticker in short_buffer and ticker not in longs]
    shorts.extend(ticker for ticker in ascending if ticker not in shorts and ticker not in longs)
    shorts = shorts[:LEG_SIZE]
    if len(longs) != LEG_SIZE or len(shorts) != LEG_SIZE:
        return _book((), (), True)
    return _book(tuple(longs), tuple(shorts), False)


def turnover_e12(previous: R03PortfolioBook | None, current: R03PortfolioBook) -> int:
    def weights(book: R03PortfolioBook | None) -> dict[str, int]:
        if book is None or book.no_trade:
            return {}
        unit = 10**12 // LEG_SIZE
        return {**{ticker: unit for ticker in book.long_tickers}, **{ticker: -unit for ticker in book.short_tickers}}

    before, after = weights(previous), weights(current)
    return sum(abs(after.get(ticker, 0) - before.get(ticker, 0)) for ticker in set(before) | set(after))


def transaction_cost_e12(previous: R03PortfolioBook | None, current: R03PortfolioBook, cost_bps_per_side: int) -> int:
    if cost_bps_per_side not in (5, 10, 15):
        raise R03FrameError("cost sensitivity must be 5, 10, or 15 bps/side")
    return round_ratio_half_even(turnover_e12(previous, current) * cost_bps_per_side, 10_000)


def net_book_utility_e12(
    book: R03PortfolioBook,
    realized_returns_e12: dict[str, int],
    previous: R03PortfolioBook | None,
    cost_bps_per_side: int,
) -> int:
    if book.no_trade:
        return -transaction_cost_e12(previous, book, cost_bps_per_side)
    try:
        gross = mean_e12([realized_returns_e12[t] for t in book.long_tickers]) - mean_e12([realized_returns_e12[t] for t in book.short_tickers])
    except KeyError as exc:
        raise R03FrameError("realized return missing for selected name") from exc
    return gross - transaction_cost_e12(previous, book, cost_bps_per_side)


def sector_relative_outcomes_e12(
    adjusted_close_t: dict[str, float],
    adjusted_close_t_plus_h: dict[str, float],
    sectors: dict[str, str],
) -> dict[str, int]:
    """Compute split-adjusted h=5 returns minus same-sector mean return."""

    common = sorted(set(adjusted_close_t) & set(adjusted_close_t_plus_h) & set(sectors))
    raw: dict[str, float] = {}
    for ticker in common:
        before = float(adjusted_close_t[ticker])
        after = float(adjusted_close_t_plus_h[ticker])
        if before > 0 and after > 0 and math.isfinite(before) and math.isfinite(after):
            raw[ticker] = after / before - 1.0
    by_sector: dict[str, list[float]] = {}
    for ticker, value in raw.items():
        by_sector.setdefault(sectors[ticker], []).append(value)
    means = {sector: sum(values) / len(values) for sector, values in by_sector.items()}
    return {ticker: e12_from_float(value - means[sectors[ticker]]) for ticker, value in raw.items()}
