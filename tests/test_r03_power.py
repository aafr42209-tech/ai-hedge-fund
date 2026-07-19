from __future__ import annotations

from v2.research.news_reasoning.r03_contracts import R03GateLabel
from v2.research.news_reasoning.r03_power import (
    evaluate_g2,
    evaluate_g3_grid,
    g3_cells,
    simulate_g3_cell,
)

SEED = "2" * 64


def test_g2_pause_and_continue_labels_are_deterministic() -> None:
    pause = evaluate_g2((100_000_000,) * 20, seed_sha256=SEED, resamples=50)
    go = evaluate_g2((1_000_000_000,) * 20, seed_sha256=SEED, resamples=50)
    assert pause.label == R03GateLabel.G2_PAUSE
    assert go.label == R03GateLabel.G2_CONTINUE
    assert go == evaluate_g2((1_000_000_000,) * 20, seed_sha256=SEED, resamples=50)


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
