from __future__ import annotations

from .analysis import analysis_spec, estimate_power, paired_percentile_ci
from .canonical import canonical_sha256
from .specs import analysis_spec_sha256, scoring_spec, scoring_spec_sha256

EFFECTS = [-3_000_000_000, -1_000_000_000, 2_000_000_000, 4_000_000_000]


def test_paired_percentile_ci_fixed_seed_golden_hash() -> None:
    interval = paired_percentile_ci(EFFECTS, seed=7, resamples=1_000)
    assert interval.lower_zero_based_index == 24
    assert interval.upper_zero_based_index == 974
    assert canonical_sha256(interval) == "e2e7eebe3056512e86475e3f8989e3cf6e4d4f04ef84ef79c1133ba39ed0f386"


def test_power_simulation_samples_empirical_effects_with_replacement() -> None:
    power = estimate_power(
        EFFECTS,
        delta_target_e12=2_000_000_000,
        delta_min_e12=500_000_000,
        power_seed=11,
        trials=20,
        sample_size=20,
        bootstrap_resamples=200,
    )
    assert power.successes == 11
    assert canonical_sha256(power) == "fb4936767f22f21f574e29970505557b704e7abe498954371add2a75a4416486"


def test_analysis_spec_pins_production_counts_and_rng() -> None:
    spec = analysis_spec()
    assert spec["bit_generator"] == "PCG64"
    assert spec["bootstrap_resamples"] == 10_000
    assert spec["power_trials"] == 1_000
    assert spec["lower_one_based_rank"] == 250
    assert spec["upper_one_based_rank"] == 9_750


def test_machine_specs_have_stable_canonical_identities() -> None:
    assert analysis_spec_sha256() == canonical_sha256(analysis_spec())
    assert scoring_spec_sha256() == canonical_sha256(scoring_spec())
    assert scoring_spec()["oracle_optimality_tolerance_e12"] == 0
