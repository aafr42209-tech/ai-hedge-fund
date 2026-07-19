from __future__ import annotations

from v2.research.overlay.r02_d4_posthoc_analysis import _distribution, _winsorize


def test_distribution_counts_signs_and_rounds() -> None:
    value = _distribution((-2, 0, 2, 4))
    assert value["count"] == 4
    assert value["negative_count"] == 1
    assert value["zero_count"] == 1
    assert value["positive_count"] == 2
    assert value["mean_e12_round_half_even"] == 1


def test_winsorize_is_deterministic_integer_output() -> None:
    values = tuple(range(20))
    assert _winsorize(values, 50_000) == (1,) + tuple(range(1, 19)) + (18,)
