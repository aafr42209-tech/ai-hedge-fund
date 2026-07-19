from __future__ import annotations

import pytest

from v2.research.news_reasoning.r03_contracts import R03GateLabel
from v2.research.news_reasoning.r03_frames import (
    construct_buffered_book,
    net_book_utility_e12,
)
from v2.research.news_reasoning.r03_headroom import (
    evaluate_g1,
    greedy_feasible_lower_bracket_e12,
    make_bound_certificate,
    R03HeadroomError,
    replay_bound_certificate,
)

SEED = "1" * 64


def returns(n: int = 25) -> dict[str, int]:
    return {f"T{i:02d}": (n - i) * 100_000_000 for i in range(n)}


def test_sort_relaxation_certificate_is_exact_and_replays() -> None:
    values = returns()
    certificate = make_bound_certificate("d1", values)
    assert certificate.long_tickers == tuple(f"T{i:02d}" for i in range(10))
    assert certificate.short_tickers == tuple(f"T{i:02d}" for i in range(24, 14, -1))
    assert replay_bound_certificate(certificate, values)
    with pytest.raises(R03HeadroomError, match="replay mismatch"):
        replay_bound_certificate(certificate, {**values, "T00": values["T00"] + 1})


def test_sort_relaxation_forces_no_trade_below_twenty() -> None:
    certificate = make_bound_certificate("d1", returns(19))
    assert certificate.long_tickers == certificate.short_tickers == ()
    assert certificate.bound_e12 == 0


def test_sort_relaxation_upper_bounds_a_feasible_zero_cost_book() -> None:
    values = returns()
    bound = make_bound_certificate("d1", values).bound_e12
    book = construct_buffered_book({ticker: float(value) for ticker, value in values.items()})
    feasible = net_book_utility_e12(book, values, None, 5) + 1_000_000_000
    assert bound >= feasible


def test_g1_bootstrap_is_deterministic_and_uses_conservative_boundary() -> None:
    stop = evaluate_g1((100_000_000,) * 20, seed_sha256=SEED, resamples=50)
    go = evaluate_g1((1_000_000_000,) * 20, seed_sha256=SEED, resamples=50)
    assert stop.label == R03GateLabel.G1_STOP
    assert go.label == R03GateLabel.G1_CONTINUE
    assert go == evaluate_g1((1_000_000_000,) * 20, seed_sha256=SEED, resamples=50)


def test_g1_empty_input_is_invalid_no_decision() -> None:
    result = evaluate_g1((), seed_sha256=SEED, resamples=10)
    assert result.label == R03GateLabel.G1_INVALID
    assert result.upper_95_e12 is None


def test_greedy_feasible_lower_bracket_does_not_govern_bound() -> None:
    series = (returns(), returns())
    lower = greedy_feasible_lower_bracket_e12(series, cost_bps_per_side=10)
    upper = sum(make_bound_certificate(f"d{i}", row).bound_e12 for i, row in enumerate(series))
    assert lower <= upper
