"""Provider-free R02 D4 replication-design calculations and comparator.

This module contains no frame builder, provider, network, subprocess, or LIVE
execution capability.  It is a design-only source for deterministic comparator
test vectors, opportunity sizing, and prospective synthetic power stress tests.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .canonical import canonical_json_bytes, sha256_hex

R02_D4_SCHEMA_VERSION = "r02-d4-provider-free-design-calculations-v1"
R02_D4_STATUS = "DRAFT_PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"
R02_D4_FRAME_SIZES = (160, 200, 240)
R02_D4_SELECTED_FRAME_SIZE = 200
R02_D4_REPRESENTATIVE_WEIGHT_NUMERATOR = 3
R02_D4_CHALLENGE_WEIGHT_NUMERATOR = 1
R02_D4_WEIGHT_DENOMINATOR = 4
R02_D4_DELTA_MIN_E12 = 50_000_000
R02_D4_DELTA_TARGET_E12 = 100_000_000
R02_D4_POWER_TARGET_PPM = 850_000
R02_D4_WILSON_LOWER_TARGET_PPM = 800_000
R02_D4_OPPORTUNITY_TARGET_PPM = 900_000
R02_D4_LOW_SNR_BPS = 8_000
R02_D4_REPRESENTATIVE_TRIGGER_RATE_BPS = 800
R02_D4_CANDIDATE_COLLAPSE_RATE_BPS = 500
R02_D4_VALID_SELECTOR_RATE_BPS = 9_500
R02_D4_FAIL_CLOSED_RATE_BPS = 500
R02_D4_GAMMA_SHAPE = 1.85
R02_D4_MIN_DISCORDANT_TOTAL = 20
R02_D4_MIN_DISCORDANT_PER_STRATUM = 5
R02_D4_DESIGN_OUTER_TRIALS = 1_000
R02_D4_DESIGN_BOOTSTRAP_RESAMPLES = 2_000
R02_D4_FRAME_SEED_STATUS = "UNRESOLVED_DRAFT_NO_SEED_CREATED"
R02_D4_FRAME_GENERATION = False
R02_D4_PROVIDER_CALLS = 0
R02_D4_LIVE_EXECUTION = False

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class R02D4DesignError(RuntimeError):
    """Fail-closed design or comparator error."""


@dataclass(frozen=True)
class ParsimonyFeatures:
    non_hold_action_count: int
    total_absolute_quantity: int
    zero_activity: bool


@dataclass(frozen=True)
class ParsimonySelection:
    canonical_candidate_id: str
    features: ParsimonyFeatures
    ranking_key: tuple[int, int, str]


@dataclass(frozen=True)
class PowerScenarioResult:
    scenario_id: str
    total_n: int
    representative_n: int
    challenge_n: int
    distribution: str
    winsor_fraction_ppm: int
    conditional_standardized_mean_bps: int
    gamma_shape_decimal: str | None
    outer_trials: int
    bootstrap_resamples: int
    supported_trials: int
    estimated_power_ppm: int
    wilson_lower_power_ppm: int
    wilson_upper_power_ppm: int
    sizing_gate: bool
    passes_power_target: bool
    passes_wilson_lower_target: bool


def candidate_activity_features(candidate_record: Mapping[str, Any]) -> ParsimonyFeatures:
    """Return the frozen byte-visible activity features for one candidate.

    The caller must first verify the accepted candidate-set integrity and its
    canonical IDs.  This comparator never reads roles, presented positions,
    utility, costs, regime, fixture identity, or outcome data.
    """

    candidate = candidate_record.get("candidate")
    decisions = candidate.get("decisions") if isinstance(candidate, Mapping) else None
    if not isinstance(decisions, Mapping) or not decisions:
        raise R02D4DesignError("PARSIMONY_CANDIDATE_DECISIONS_MISSING")
    non_hold = 0
    total_quantity = 0
    for asset_id, decision in decisions.items():
        if not isinstance(asset_id, str) or not asset_id:
            raise R02D4DesignError("PARSIMONY_ASSET_ID_INVALID")
        if not isinstance(decision, Mapping):
            raise R02D4DesignError("PARSIMONY_DECISION_INVALID")
        action = decision.get("action")
        quantity = decision.get("quantity")
        if not isinstance(action, str) or type(quantity) is not int:
            raise R02D4DesignError("PARSIMONY_ACTION_OR_QUANTITY_INVALID")
        non_hold += int(action != "hold" or quantity != 0)
        total_quantity += abs(quantity)
    return ParsimonyFeatures(
        non_hold_action_count=non_hold,
        total_absolute_quantity=total_quantity,
        zero_activity=non_hold == 0 and total_quantity == 0,
    )


def select_parsimony_candidate(
    candidate_records: Sequence[Mapping[str, Any]],
) -> ParsimonySelection:
    """Choose lexicographic min(activity count, absolute quantity, canonical ID)."""

    if not candidate_records:
        raise R02D4DesignError("PARSIMONY_CANDIDATE_SET_EMPTY")
    featured: list[tuple[tuple[int, int, str], ParsimonyFeatures]] = []
    seen_ids: set[str] = set()
    for record in candidate_records:
        candidate_id = record.get("canonical_candidate_id")
        if not isinstance(candidate_id, str) or not _HEX_64.fullmatch(candidate_id):
            raise R02D4DesignError("PARSIMONY_CANONICAL_ID_INVALID")
        if candidate_id in seen_ids:
            raise R02D4DesignError("PARSIMONY_CANONICAL_ID_DUPLICATE")
        seen_ids.add(candidate_id)
        features = candidate_activity_features(record)
        key = (
            features.non_hold_action_count,
            features.total_absolute_quantity,
            candidate_id,
        )
        featured.append((key, features))
    key, features = min(featured, key=lambda value: value[0])
    return ParsimonySelection(
        canonical_candidate_id=key[2],
        features=features,
        ranking_key=key,
    )


def _candidate(candidate_id: str, decisions: Mapping[str, tuple[str, int]]) -> dict[str, Any]:
    return {
        "canonical_candidate_id": candidate_id,
        "candidate": {
            "decisions": {
                asset_id: {"action": action, "quantity": quantity}
                for asset_id, (action, quantity) in decisions.items()
            }
        },
    }


def parsimony_test_vectors() -> list[dict[str, Any]]:
    """Return deterministic, role-blind comparator vectors."""

    a, b, c = "a" * 64, "b" * 64, "c" * 64
    vectors: list[dict[str, Any]] = [
        {
            "vector_id": "unique-zero-activity-wins",
            "candidates": [
                _candidate(a, {"A0": ("buy", 3), "A1": ("hold", 0)}),
                _candidate(b, {"A0": ("hold", 0), "A1": ("hold", 0)}),
            ],
            "expected_selected_canonical_id": b,
        },
        {
            "vector_id": "fewer-non-hold-actions-wins",
            "candidates": [
                _candidate(a, {"A0": ("buy", 1), "A1": ("sell", -1)}),
                _candidate(b, {"A0": ("buy", 100), "A1": ("hold", 0)}),
            ],
            "expected_selected_canonical_id": b,
        },
        {
            "vector_id": "lower-total-absolute-quantity-wins",
            "candidates": [
                _candidate(a, {"A0": ("buy", 9)}),
                _candidate(b, {"A0": ("sell", -3)}),
            ],
            "expected_selected_canonical_id": b,
        },
        {
            "vector_id": "canonical-id-breaks-feature-tie",
            "candidates": [
                _candidate(c, {"A0": ("buy", 4)}),
                _candidate(a, {"A0": ("sell", -4)}),
            ],
            "expected_selected_canonical_id": a,
        },
        {
            "vector_id": "hold-with-nonzero-quantity-is-active",
            "candidates": [
                _candidate(a, {"A0": ("hold", 2)}),
                _candidate(b, {"A0": ("hold", 0)}),
            ],
            "expected_selected_canonical_id": b,
        },
        {
            "vector_id": "non-hold-with-zero-quantity-is-active",
            "candidates": [
                _candidate(a, {"A0": ("buy", 0)}),
                _candidate(b, {"A0": ("hold", 0)}),
            ],
            "expected_selected_canonical_id": b,
        },
        {
            "vector_id": "permutation-invariant-forward",
            "candidates": [
                _candidate(c, {"A0": ("buy", 2)}),
                _candidate(a, {"A0": ("sell", -2)}),
                _candidate(b, {"A0": ("buy", 5)}),
            ],
            "expected_selected_canonical_id": a,
        },
        {
            "vector_id": "permutation-invariant-reverse",
            "candidates": [
                _candidate(b, {"A0": ("buy", 5)}),
                _candidate(a, {"A0": ("sell", -2)}),
                _candidate(c, {"A0": ("buy", 2)}),
            ],
            "expected_selected_canonical_id": a,
        },
    ]
    return vectors


def expected_m_min(total_n: int) -> int:
    if total_n <= 0 or total_n % 4:
        raise R02D4DesignError("FRAME_SIZE_MUST_BE_POSITIVE_AND_DIVISIBLE_BY_FOUR")
    return math.floor(total_n * 46 / 160)


def exact_m_min_probability_ppm(total_n: int, m_min: int | None = None) -> int:
    if total_n <= 0 or total_n % 4:
        raise R02D4DesignError("FRAME_SIZE_MUST_BE_POSITIVE_AND_DIVISIBLE_BY_FOUR")
    representative_n = total_n * 3 // 4
    challenge_n = total_n - representative_n
    floor = expected_m_min(total_n) if m_min is None else m_min
    required_representative = max(0, floor - challenge_n)
    p = (
        R02_D4_REPRESENTATIVE_TRIGGER_RATE_BPS
        * (10_000 - R02_D4_CANDIDATE_COLLAPSE_RATE_BPS)
        / 100_000_000
    )
    probability = sum(
        math.comb(representative_n, k)
        * p**k
        * (1 - p) ** (representative_n - k)
        for k in range(required_representative, representative_n + 1)
    )
    return round(probability * 1_000_000)


def _round_ratio_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(abs(numerator), denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2):
        quotient += 1
    return quotient if numerator >= 0 else -quotient


def _wilson_interval_ppm(successes: int, trials: int) -> tuple[int, int]:
    z = 1.959963984540054
    probability = successes / trials
    denominator = 1 + z * z / trials
    center = (probability + z * z / (2 * trials)) / denominator
    margin = (
        z
        * math.sqrt(probability * (1 - probability) / trials + z * z / (4 * trials**2))
        / denominator
    )
    return round((center - margin) * 1_000_000), round((center + margin) * 1_000_000)


def _simulation_root_seed() -> str:
    return sha256_hex(
        canonical_json_bytes(
            {
                "domain": "r02-d4-provider-free-design-simulation-v1",
                "frame_sizes": list(R02_D4_FRAME_SIZES),
                "delta_min_e12": R02_D4_DELTA_MIN_E12,
                "delta_target_e12": R02_D4_DELTA_TARGET_E12,
                "low_snr_bps": R02_D4_LOW_SNR_BPS,
                "gamma_shape_millionths": round(R02_D4_GAMMA_SHAPE * 1_000_000),
                "outer_trials": R02_D4_DESIGN_OUTER_TRIALS,
                "bootstrap_resamples": R02_D4_DESIGN_BOOTSTRAP_RESAMPLES,
            }
        )
    )


def _scenario_seed(scenario_id: str) -> int:
    return int.from_bytes(
        hashlib.sha256(
            f"r02-d4-power|{_simulation_root_seed()}|{scenario_id}".encode("utf-8")
        ).digest()[:16],
        "big",
    )


def _draw_conditional_effects(
    rng: np.random.Generator,
    count: int,
    *,
    distribution: str,
    conditional_mean_e12: int,
    conditional_sd_e12: int,
) -> np.ndarray:
    if distribution == "BOUNDED_TWO_POINT_ZERO_OR_HIGH":
        standardized_mean = R02_D4_LOW_SNR_BPS / 10_000
        positive_probability = standardized_mean**2 / (1 + standardized_mean**2)
        high = round(conditional_mean_e12 / positive_probability)
        return np.where(rng.random(count) < positive_probability, high, 0).astype(np.int64)
    if distribution == "CENTERED_GAMMA_HEAVY_RIGHT_TAIL":
        shape = R02_D4_GAMMA_SHAPE
        standardized = (rng.gamma(shape=shape, scale=1.0, size=count) - shape) / math.sqrt(shape)
        return np.rint(conditional_mean_e12 + conditional_sd_e12 * standardized).astype(np.int64)
    raise R02D4DesignError("POWER_DISTRIBUTION_UNSUPPORTED")


def _winsorize(values: np.ndarray, fraction_ppm: int) -> np.ndarray:
    if fraction_ppm == 0:
        return values
    fraction = fraction_ppm / 1_000_000
    lower, upper = np.quantile(values, [fraction, 1.0 - fraction], method="linear")
    return np.rint(np.clip(values, lower, upper)).astype(np.int64)


def simulate_power_scenario(
    *,
    total_n: int,
    distribution: str,
    winsor_fraction_ppm: int = 0,
    outer_trials: int = R02_D4_DESIGN_OUTER_TRIALS,
    bootstrap_resamples: int = R02_D4_DESIGN_BOOTSTRAP_RESAMPLES,
) -> PowerScenarioResult:
    if total_n not in R02_D4_FRAME_SIZES:
        raise R02D4DesignError("POWER_FRAME_SIZE_NOT_IN_FROZEN_GRID")
    if winsor_fraction_ppm not in {0, 50_000, 100_000}:
        raise R02D4DesignError("POWER_WINSOR_FRACTION_NOT_FROZEN")
    if distribution == "BOUNDED_TWO_POINT_ZERO_OR_HIGH" and winsor_fraction_ppm:
        raise R02D4DesignError("BOUNDED_SCENARIO_DOES_NOT_USE_WINSORIZATION")
    representative_n = total_n * 3 // 4
    challenge_n = total_n - representative_n
    suffix = {
        "BOUNDED_TWO_POINT_ZERO_OR_HIGH": "bounded-low-snr",
        "CENTERED_GAMMA_HEAVY_RIGHT_TAIL": "gamma-heavy-tail-low-snr",
    }[distribution]
    if winsor_fraction_ppm:
        suffix += f"-winsor-{winsor_fraction_ppm // 10_000:02d}pct"
    scenario_id = f"n{total_n}-{suffix}"
    rng = np.random.Generator(np.random.PCG64(_scenario_seed(scenario_id)))
    p_trigger = R02_D4_REPRESENTATIVE_TRIGGER_RATE_BPS / 10_000
    p_not_collapsed = 1 - R02_D4_CANDIDATE_COLLAPSE_RATE_BPS / 10_000
    p_valid = R02_D4_VALID_SELECTOR_RATE_BPS / 10_000
    p_not_failed = 1 - R02_D4_FAIL_CLOSED_RATE_BPS / 10_000
    rep_active_probability = p_trigger * p_not_collapsed * p_valid * p_not_failed
    challenge_active_probability = p_valid * p_not_failed
    active_weight = 0.75 * rep_active_probability + 0.25 * challenge_active_probability
    conditional_mean = round(R02_D4_DELTA_TARGET_E12 / active_weight)
    conditional_sd = round(conditional_mean * 10_000 / R02_D4_LOW_SNR_BPS)
    lower_rank_index = math.ceil(0.025 * bootstrap_resamples) - 1
    threshold_numerator = (
        R02_D4_DELTA_MIN_E12 * 4 * representative_n * challenge_n
    )
    supported = 0
    for _ in range(outer_trials):
        representative_active = rng.random(representative_n) < rep_active_probability
        challenge_active = rng.random(challenge_n) < challenge_active_probability
        representative = np.zeros(representative_n, dtype=np.int64)
        challenge = np.zeros(challenge_n, dtype=np.int64)
        representative[representative_active] = _draw_conditional_effects(
            rng,
            int(representative_active.sum()),
            distribution=distribution,
            conditional_mean_e12=conditional_mean,
            conditional_sd_e12=conditional_sd,
        )
        challenge[challenge_active] = _draw_conditional_effects(
            rng,
            int(challenge_active.sum()),
            distribution=distribution,
            conditional_mean_e12=conditional_mean,
            conditional_sd_e12=conditional_sd,
        )
        representative = _winsorize(representative, winsor_fraction_ppm)
        challenge = _winsorize(challenge, winsor_fraction_ppm)
        representative_indexes = rng.integers(
            0,
            representative_n,
            size=(bootstrap_resamples, representative_n),
        )
        challenge_indexes = rng.integers(
            0,
            challenge_n,
            size=(bootstrap_resamples, challenge_n),
        )
        representative_sums = representative[representative_indexes].sum(axis=1)
        challenge_sums = challenge[challenge_indexes].sum(axis=1)
        bootstrap_numerators = (
            3 * representative_sums * challenge_n
            + challenge_sums * representative_n
        )
        lower_numerator = np.partition(bootstrap_numerators, lower_rank_index)[
            lower_rank_index
        ]
        supported += int(lower_numerator > threshold_numerator)
    estimated = _round_ratio_half_even(supported * 1_000_000, outer_trials)
    lower, upper = _wilson_interval_ppm(supported, outer_trials)
    sizing_gate = distribution in {
        "BOUNDED_TWO_POINT_ZERO_OR_HIGH",
        "CENTERED_GAMMA_HEAVY_RIGHT_TAIL",
    } and winsor_fraction_ppm == 0
    return PowerScenarioResult(
        scenario_id=scenario_id,
        total_n=total_n,
        representative_n=representative_n,
        challenge_n=challenge_n,
        distribution=distribution,
        winsor_fraction_ppm=winsor_fraction_ppm,
        conditional_standardized_mean_bps=R02_D4_LOW_SNR_BPS,
        gamma_shape_decimal=(
            format(R02_D4_GAMMA_SHAPE, ".2f")
            if distribution == "CENTERED_GAMMA_HEAVY_RIGHT_TAIL"
            else None
        ),
        outer_trials=outer_trials,
        bootstrap_resamples=bootstrap_resamples,
        supported_trials=supported,
        estimated_power_ppm=estimated,
        wilson_lower_power_ppm=lower,
        wilson_upper_power_ppm=upper,
        sizing_gate=sizing_gate,
        passes_power_target=estimated >= R02_D4_POWER_TARGET_PPM,
        passes_wilson_lower_target=lower >= R02_D4_WILSON_LOWER_TARGET_PPM,
    )


def build_power_report(
    *,
    outer_trials: int = R02_D4_DESIGN_OUTER_TRIALS,
    bootstrap_resamples: int = R02_D4_DESIGN_BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    scenarios: list[PowerScenarioResult] = []
    for total_n in R02_D4_FRAME_SIZES:
        scenarios.append(
            simulate_power_scenario(
                total_n=total_n,
                distribution="BOUNDED_TWO_POINT_ZERO_OR_HIGH",
                outer_trials=outer_trials,
                bootstrap_resamples=bootstrap_resamples,
            )
        )
        for winsor_fraction_ppm in (0, 50_000, 100_000):
            scenarios.append(
                simulate_power_scenario(
                    total_n=total_n,
                    distribution="CENTERED_GAMMA_HEAVY_RIGHT_TAIL",
                    winsor_fraction_ppm=winsor_fraction_ppm,
                    outer_trials=outer_trials,
                    bootstrap_resamples=bootstrap_resamples,
                )
            )
    sizing_pass = {
        total_n: all(
            item.passes_power_target and item.passes_wilson_lower_target
            for item in scenarios
            if item.total_n == total_n and item.sizing_gate
        )
        for total_n in R02_D4_FRAME_SIZES
    }
    return {
        "schema_version": R02_D4_SCHEMA_VERSION,
        "status": R02_D4_STATUS,
        "provider_calls": R02_D4_PROVIDER_CALLS,
        "frame_generation": R02_D4_FRAME_GENERATION,
        "live_execution": R02_D4_LIVE_EXECUTION,
        "simulation_seed_sha256": _simulation_root_seed(),
        "targets": {
            "estimated_power_ppm": R02_D4_POWER_TARGET_PPM,
            "wilson_lower_power_ppm": R02_D4_WILSON_LOWER_TARGET_PPM,
            "opportunity_probability_ppm": R02_D4_OPPORTUNITY_TARGET_PPM,
            "low_snr_bps": R02_D4_LOW_SNR_BPS,
        },
        "opportunity_grid": [
            {
                "total_n": total_n,
                "representative_n": total_n * 3 // 4,
                "challenge_n": total_n // 4,
                "m_min": expected_m_min(total_n),
                "exact_probability_ppm": exact_m_min_probability_ppm(total_n),
            }
            for total_n in R02_D4_FRAME_SIZES
        ],
        "scenario_results": [asdict(item) for item in scenarios],
        "sizing_gate_pass_by_n": {str(key): value for key, value in sizing_pass.items()},
        "draft_selected_n": R02_D4_SELECTED_FRAME_SIZE,
        "selection_rule": (
            "SMALLEST_N_GE_200_PASSING_ESTIMATED_POWER_850000_AND_"
            "WILSON_LOWER_800000_IN_BOTH_8000_BPS_RAW_SIZING_SCENARIOS"
        ),
        "winsor_scenarios_are_diagnostic_not_primary": True,
    }


def build_test_vector_report() -> dict[str, Any]:
    vectors = parsimony_test_vectors()
    results = []
    for vector in vectors:
        selected = select_parsimony_candidate(vector["candidates"])
        results.append(
            {
                "vector_id": vector["vector_id"],
                "expected_selected_canonical_id": vector[
                    "expected_selected_canonical_id"
                ],
                "actual_selected_canonical_id": selected.canonical_candidate_id,
                "ranking_key": list(selected.ranking_key),
                "passed": selected.canonical_candidate_id
                == vector["expected_selected_canonical_id"],
            }
        )
    return {
        "schema_version": "r02-d4-parsimony-test-vectors-v1",
        "status": R02_D4_STATUS,
        "policy": (
            "MIN_NON_HOLD_ACTION_COUNT_THEN_MIN_TOTAL_ABSOLUTE_QUANTITY_"
            "THEN_CANONICAL_ID"
        ),
        "provider_calls": 0,
        "frame_generation": False,
        "live_execution": False,
        "vectors": vectors,
        "results": results,
        "all_passed": all(value["passed"] for value in results),
    }


def canonical_report_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def report_sha256(value: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_report_bytes(value))


def forbidden_capability_names() -> set[str]:
    """Names forbidden by the design-only source audit test."""

    return {
        "anthropic",
        "http",
        "httpx",
        "openai",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }


def iter_sizing_gate_scenarios(
    report: Mapping[str, Any],
) -> Iterable[Mapping[str, Any]]:
    values = report.get("scenario_results")
    if not isinstance(values, list):
        raise R02D4DesignError("POWER_REPORT_SCENARIOS_MISSING")
    return (
        value
        for value in values
        if isinstance(value, Mapping) and value.get("sizing_gate") is True
    )
