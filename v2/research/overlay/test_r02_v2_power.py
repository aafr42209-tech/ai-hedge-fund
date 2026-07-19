from __future__ import annotations

from .r02_v2_power import (
    blinded_pilot_go_no_go,
    confirmatory_sample_size,
    passes_power_gate,
    sensitivity_grid,
    simulate_cell_power,
    wilson_interval_ppm,
)


def test_full_sensitivity_grid_and_registered_wilson_value() -> None:
    grid = sensitivity_grid()
    assert len(grid) == 288
    assert all(cell.included == (cell.full_frame_expected_effect_e12 >= 50_000_000) for cell in grid)
    assert wilson_interval_ppm(4, 40)[0] == 39_580


def test_power_gate_uses_wilson_lower_not_point_estimate() -> None:
    lower_820, _ = wilson_interval_ppm(820, 1_000)
    lower_825, _ = wilson_interval_ppm(825, 1_000)
    assert 820_000 >= 800_000 and lower_820 == 794_978
    assert not passes_power_gate(lower_820)
    assert lower_825 == 800_218
    assert passes_power_gate(lower_825)


def test_power_cell_simulation_is_domain_separated_and_reproducible() -> None:
    cell = next(cell for cell in sensitivity_grid() if cell.included)
    first = simulate_cell_power(
        cell,
        total_n=200,
        seed_sha256="4" * 64,
        effect_bounds_e12=(-2_000_000_000, 4_000_000_000),
        trials=4,
        bootstrap_resamples=20,
    )
    second = simulate_cell_power(
        cell,
        total_n=200,
        seed_sha256="4" * 64,
        effect_bounds_e12=(-2_000_000_000, 4_000_000_000),
        trials=4,
        bootstrap_resamples=20,
    )
    assert first == second


def test_pilot_and_confirmatory_rules_fail_closed() -> None:
    assert (
        blinded_pilot_go_no_go(
            representative_successes=1,
            representative_trials=30,
            challenge_successes=1,
            challenge_trials=10,
        )
        == "PILOT_NO_GO"
    )
    assert (
        confirmatory_sample_size(
            utility_power_n=200,
            representative_discordance_lower_ppm=1,
            challenge_discordance_lower_ppm=1,
            pooled_discordance_lower_ppm=1,
        )
        is None
    )
