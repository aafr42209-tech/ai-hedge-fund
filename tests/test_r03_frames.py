from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from v2.research.news_reasoning.r03_contracts import R03FrameRow
from v2.research.news_reasoning.r03_frames import (
    assert_frame_row_available,
    construct_buffered_book,
    decision_clock,
    frozen_splits,
    net_book_utility_e12,
    phase_book_for_session,
    R03FrameError,
    sector_relative_outcomes_e12,
    transaction_cost_e12,
    validate_split_topology,
)

SHA = "a" * 64


def scores(n: int = 25) -> dict[str, float]:
    return {f"T{i:02d}": float(n - i) for i in range(n)}


def test_split_topology_and_phase_books_are_frozen() -> None:
    splits = frozen_splits()
    assert sum(split.session_count for split in splits) == 2514
    assert len(validate_split_topology(splits)) == 64
    assert tuple(phase_book_for_session(i) for i in range(10)) == (0, 1, 2, 3, 4, 0, 1, 2, 3, 4)


def test_reject_early_close_cutoff_perturbation() -> None:
    normal_close = datetime(2022, 6, 1, 20, 0, tzinfo=timezone.utc)
    early_close = datetime(2022, 11, 25, 18, 0, tzinfo=timezone.utc)
    normal = decision_clock(normal_close)
    early = decision_clock(early_close)
    assert (normal.hour, normal.minute) == (15, 30)
    assert (early.hour, early.minute) == (12, 30)
    assert early != normal.replace(year=early.year, month=early.month, day=early.day)


def test_frame_rejects_oos_and_unmatured_outcome() -> None:
    decision = datetime(2023, 1, 3, 20, tzinfo=timezone.utc)
    row = R03FrameRow(
        decision_id="oos",
        ticker="AAA",
        sector="TECH",
        decision_at=decision,
        feature_cutoff_at=decision - timedelta(days=1),
        label_maturity_at=decision + timedelta(days=7),
        phase_book=0,
        payload_sha256=SHA,
        outcome_e12=1,
    )
    with pytest.raises(R03FrameError, match="unmatured"):
        assert_frame_row_available(row, decision)
    with pytest.raises(R03FrameError, match="OOS"):
        assert_frame_row_available(row, decision + timedelta(days=10))


def test_buffered_constructor_is_deterministic_and_no_trade_below_twenty() -> None:
    first = construct_buffered_book(scores())
    assert first.long_tickers == tuple(f"T{i:02d}" for i in range(10))
    assert first.short_tickers == tuple(f"T{i:02d}" for i in range(24, 14, -1))
    assert construct_buffered_book(dict(reversed(list(scores().items())))) == first
    assert construct_buffered_book(scores(19)).no_trade is True


def test_buffer_retains_names_inside_rank_twenty() -> None:
    first = construct_buffered_book(scores())
    shifted = scores()
    shifted["T00"] = 8.5
    second = construct_buffered_book(shifted, first)
    assert "T00" in second.long_tickers


def test_cost_and_net_utility_use_common_e12_book() -> None:
    book = construct_buffered_book(scores(20))
    returns = {ticker: (20 - i) * 1_000_000_000 for i, ticker in enumerate(scores(20))}
    assert transaction_cost_e12(None, book, 10) == 2_000_000_000
    assert net_book_utility_e12(book, returns, None, 10) > 0
    with pytest.raises(R03FrameError):
        transaction_cost_e12(None, book, 7)


def test_sector_relative_outcomes_are_e12_and_sector_neutral() -> None:
    before = {"AAA": 100.0, "BBB": 100.0, "CCC": 100.0}
    after = {"AAA": 110.0, "BBB": 100.0, "CCC": 105.0}
    sectors = {"AAA": "TECH", "BBB": "TECH", "CCC": "HEALTH"}
    result = sector_relative_outcomes_e12(before, after, sectors)
    assert result["AAA"] == 50_000_000_000
    assert result["BBB"] == -50_000_000_000
    assert result["CCC"] == 0
