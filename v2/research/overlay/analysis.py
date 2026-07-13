"""Preregistered integer paired-bootstrap and prospective-power analysis."""

from __future__ import annotations

import hashlib
import numpy as np

from .arithmetic import PARTS_PER_MILLION, mean_int, round_ratio_half_even
from .contracts import BootstrapInterval, PowerResult

DEFAULT_BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_POWER_TRIALS = 1_000
DEFAULT_EVALUATION_CASES = 200


def _rounded_integer_means(sums: np.ndarray, denominator: int) -> np.ndarray:
    if denominator <= 0:
        raise ValueError("mean denominator must be positive")
    absolute = np.abs(sums)
    quotient, remainder = np.divmod(absolute, denominator)
    increment = (remainder * 2 > denominator) | ((remainder * 2 == denominator) & (quotient % 2 == 1))
    signed = quotient + increment.astype(np.int64)
    return np.where(sums < 0, -signed, signed).astype(np.int64)


def paired_percentile_ci(
    case_deltas_e12: tuple[int, ...] | list[int],
    *,
    seed: int,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
) -> BootstrapInterval:
    if not case_deltas_e12:
        raise ValueError("paired bootstrap requires at least one case")
    if seed < 0 or resamples <= 0:
        raise ValueError("seed and resample count must be nonnegative/positive")
    values = np.asarray(case_deltas_e12, dtype=np.int64)
    rng = np.random.Generator(np.random.PCG64(seed))
    indices = rng.integers(0, len(values), size=(resamples, len(values)), dtype=np.int64)
    sums = values[indices].sum(axis=1, dtype=np.int64)
    means = np.sort(_rounded_integer_means(sums, len(values)))
    lower_index = (25 * resamples + 999) // 1_000 - 1
    upper_index = (975 * resamples + 999) // 1_000 - 1
    return BootstrapInterval(
        lower_e12=int(means[lower_index]),
        upper_e12=int(means[upper_index]),
        resamples=resamples,
        lower_zero_based_index=lower_index,
        upper_zero_based_index=upper_index,
        seed=seed,
    )


def _derived_seed(power_seed: int, label: str, trial_index: int) -> int:
    payload = f"{label}|{power_seed}|{trial_index}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def estimate_power(
    development_effects_e12: tuple[int, ...] | list[int],
    *,
    delta_target_e12: int,
    delta_min_e12: int,
    power_seed: int,
    trials: int = DEFAULT_POWER_TRIALS,
    sample_size: int = DEFAULT_EVALUATION_CASES,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
) -> PowerResult:
    if not development_effects_e12:
        raise ValueError("development effects are required")
    if power_seed < 0 or trials <= 0 or sample_size <= 0 or bootstrap_resamples <= 0:
        raise ValueError("invalid power-analysis configuration")
    development = np.asarray(development_effects_e12, dtype=np.int64)
    shift = delta_target_e12 - mean_int(list(development_effects_e12))
    shifted = development + np.int64(shift)
    successes = 0
    for trial_index in range(trials):
        trial_rng = np.random.Generator(np.random.PCG64(_derived_seed(power_seed, "power-trial", trial_index)))
        trial = shifted[trial_rng.integers(0, len(shifted), size=sample_size, dtype=np.int64)]
        interval = paired_percentile_ci(
            [int(value) for value in trial],
            seed=_derived_seed(power_seed, "power-ci", trial_index),
            resamples=bootstrap_resamples,
        )
        successes += int(interval.lower_e12 > delta_min_e12)
    return PowerResult(
        successes=successes,
        trials=trials,
        power_e6=round_ratio_half_even(successes * PARTS_PER_MILLION, trials),
        sample_size=sample_size,
        bootstrap_resamples=bootstrap_resamples,
        power_seed=power_seed,
    )


def analysis_spec() -> dict[str, object]:
    return {
        "schema_version": "r01-analysis-v1",
        "numpy_version": np.__version__,
        "bit_generator": "PCG64",
        "bootstrap_resamples": DEFAULT_BOOTSTRAP_RESAMPLES,
        "power_trials": DEFAULT_POWER_TRIALS,
        "evaluation_cases": DEFAULT_EVALUATION_CASES,
        "percentile_rule": "nearest_rank",
        "lower_one_based_rank": 250,
        "upper_one_based_rank": 9_750,
        "integer_mean": "round_ratio_half_even(sum(values), count)",
        "trial_seed": "sha256('power-trial|<power_seed>|<zero_based_trial>')[:128]",
        "ci_seed": "sha256('power-ci|<power_seed>|<zero_based_trial>')[:128]",
    }
