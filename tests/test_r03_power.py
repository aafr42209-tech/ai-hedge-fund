from __future__ import annotations

import pytest

from v2.research.news_reasoning.r03_contracts import (
    R03G2IncrementalAxis,
    R03GateLabel,
    R03T2AbsoluteProfitabilityFlag,
)
from v2.research.news_reasoning.r03_power import (
    evaluate_g2,
    evaluate_g3_grid,
    G2_ABSOLUTE_BOOTSTRAP_LABEL,
    G2_CONTRAST_BOOTSTRAP_LABEL,
    g3_cells,
    simulate_g3_cell,
)

SEED = "2" * 64


@pytest.mark.parametrize(
    ("difference_e12", "absolute_e12", "label", "incremental_axis", "absolute_flag"),
    (
        (
            1_000_000_000,
            100_000_000,
            R03GateLabel.G2_CONTINUE,
            R03G2IncrementalAxis.G2_INCREMENTAL_PASS,
            R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_POSITIVE,
        ),
        (
            1_000_000_000,
            -100_000_000,
            R03GateLabel.G2_CONTINUE,
            R03G2IncrementalAxis.G2_INCREMENTAL_PASS,
            R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_NEGATIVE,
        ),
        (
            100_000_000,
            100_000_000,
            R03GateLabel.G2_PAUSE,
            R03G2IncrementalAxis.G2_INCREMENTAL_FAIL,
            R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_POSITIVE,
        ),
        (
            100_000_000,
            -100_000_000,
            R03GateLabel.G2_PAUSE,
            R03G2IncrementalAxis.G2_INCREMENTAL_FAIL,
            R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_NEGATIVE,
        ),
    ),
)
def test_g2_records_all_two_axis_combinations(
    difference_e12: int,
    absolute_e12: int,
    label: R03GateLabel,
    incremental_axis: R03G2IncrementalAxis,
    absolute_flag: R03T2AbsoluteProfitabilityFlag,
) -> None:
    result = evaluate_g2(
        (difference_e12,) * 20,
        (absolute_e12,) * 20,
        seed_sha256=SEED,
        resamples=50,
    )
    assert result.label == label
    assert result.incremental_axis == incremental_axis
    assert result.absolute_profitability_flag == absolute_flag


def test_g2_absolute_profitability_is_non_gate_bearing() -> None:
    contrast = (1_000_000_000,) * 20
    positive = evaluate_g2(contrast, (100_000_000,) * 20, seed_sha256=SEED, resamples=50)
    negative = evaluate_g2(contrast, (-100_000_000,) * 20, seed_sha256=SEED, resamples=50)
    assert positive.label.value.encode("utf-8") == negative.label.value.encode("utf-8")
    assert positive.incremental_axis.value.encode("utf-8") == negative.incremental_axis.value.encode("utf-8")
    assert positive.absolute_profitability_flag != negative.absolute_profitability_flag


def test_g2_absolute_zero_point_estimate_is_negative() -> None:
    result = evaluate_g2(
        (1_000_000_000,) * 20,
        (0,) * 20,
        seed_sha256=SEED,
        resamples=50,
    )
    assert result.t2_absolute_point_estimate_e12 == 0
    assert result.t2_absolute_lower_95_e12 == 0
    assert result.absolute_profitability_flag == R03T2AbsoluteProfitabilityFlag.T2_ABSOLUTE_PROFITABILITY_NEGATIVE


def test_g2_result_hash_is_deterministic_and_covers_absolute_fields() -> None:
    contrast = (1_000_000_000,) * 20
    absolute = (100_000_000,) * 20
    first = evaluate_g2(contrast, absolute, seed_sha256=SEED, resamples=50)
    repeated = evaluate_g2(contrast, absolute, seed_sha256=SEED, resamples=50)
    perturbed = evaluate_g2(
        contrast,
        absolute[:-1] + (100_000_001,),
        seed_sha256=SEED,
        resamples=50,
    )
    assert first == repeated
    assert first.result_sha256 == repeated.result_sha256
    assert first.result_sha256 != perturbed.result_sha256


def test_g2_bootstrap_domains_and_sealed_label_values_are_fixed() -> None:
    assert G2_CONTRAST_BOOTSTRAP_LABEL != G2_ABSOLUTE_BOOTSTRAP_LABEL
    assert R03GateLabel.G2_CONTINUE.value == "G2_CONTINUE_CHEAP_TEXT_SUPPORT"
    assert R03GateLabel.G2_PAUSE.value == "PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION"


def test_g3_grid_contains_exact_six_preregistered_cells() -> None:
    cells = g3_cells()
    assert len(cells) == 6
    assert {cell.sd_multiplier_ppm for cell in cells} == {1_000_000, 1_500_000, 2_000_000}
    assert {cell.fail_rate_ppm for cell in cells} == {0, 50_000}
    assert all(cell.planned_n == 747 for cell in cells)


def test_g3_simulation_is_domain_separated_and_reproducible() -> None:
    proxy = tuple((-1 if i % 2 else 1) * 100_000_000 for i in range(40))
    first = simulate_g3_cell(proxy, g3_cells()[0], seed_sha256=SEED, trials=20)
    assert first == simulate_g3_cell(proxy, g3_cells()[0], seed_sha256=SEED, trials=20)
    other = simulate_g3_cell(proxy, g3_cells()[1], seed_sha256=SEED, trials=20)
    assert first.result_sha256 != other.result_sha256


def test_g3_grid_uses_wilson_lower_for_all_cells() -> None:
    proxy = tuple((-1 if i % 2 else 1) * 50_000_000 for i in range(40))
    results = tuple(simulate_g3_cell(proxy, cell, seed_sha256=SEED, trials=20) for cell in g3_cells())
    grid = evaluate_g3_grid(results)
    assert grid.label in (R03GateLabel.G3_CONTINUE, R03GateLabel.G3_STOP)
    assert (grid.label == R03GateLabel.G3_CONTINUE) == all(result.passes for result in results)
