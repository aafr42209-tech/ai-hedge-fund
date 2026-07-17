"""Provider-free R02 D2c statistical and provider-budget freeze candidate."""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .arithmetic import round_ratio_half_even
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import StrictModel, SyntheticEpisode
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_candidates import prepare_provider_free_episode
from .r02_frame import (
    DEFAULT_R02_FRAME_ARTIFACT_ROOT,
    R02FrameManifest,
    R02FrameSeal,
    R02FrameStratum,
    R02_FRAME_CHALLENGE_COUNT,
    R02_FRAME_REPRESENTATIVE_COUNT,
)
from .r02_selector import build_selector_request


R02_DELTA_MIN_E12 = 50_000_000
R02_DELTA_TARGET_E12 = 100_000_000
R02_EVALUATION_BOOTSTRAP_RESAMPLES = 10_000
R02_SIMULATION_BOOTSTRAP_RESAMPLES = 2_000
R02_POWER_TRIALS = 1_000
R02_POWER_TARGET_PPM = 800_000
R02_OPPORTUNITY_TARGET_PPM = 900_000
R02_M_MIN = 46
R02_PER_EPISODE_ATTEMPT_CAP = 1
R02_RETRY_ATTEMPT_CAP = 0
R02_PER_ATTEMPT_TOKEN_RESERVE = 32_000
R02_INCREMENTAL_USD_CAP = 0
R02_STATS_SCHEMA_VERSION = "r02-d2c-statistical-freeze-v1"


class R02StatisticsError(RuntimeError):
    pass


class R02PowerScenario(StrictModel):
    schema_version: Literal["r02-power-scenario-v1"] = "r02-power-scenario-v1"
    scenario_id: str
    total_n: int = Field(ge=1)
    representative_n: int = Field(ge=1)
    challenge_n: int = Field(ge=1)
    representative_trigger_rate_bps: int = Field(ge=0, le=10_000)
    representative_candidate_collapse_rate_bps: int = Field(ge=0, le=10_000)
    valid_selector_rate_bps: int = Field(ge=0, le=10_000)
    fail_closed_rate_bps: int = Field(ge=0, le=10_000)
    conditional_standardized_mean_bps: int = Field(gt=0)
    conditional_distribution: Literal["BOUNDED_TWO_POINT_ZERO_OR_HIGH"] = (
        "BOUNDED_TWO_POINT_ZERO_OR_HIGH"
    )
    conditional_positive_probability_ppm: int = Field(gt=0, lt=1_000_000)
    delta_min_e12: Literal[R02_DELTA_MIN_E12] = R02_DELTA_MIN_E12
    delta_target_e12: Literal[R02_DELTA_TARGET_E12] = R02_DELTA_TARGET_E12
    conditional_mean_e12: int = Field(gt=0)
    conditional_sd_e12: int = Field(gt=0)
    conditional_high_e12: int = Field(gt=0)
    power_trials: Literal[R02_POWER_TRIALS] = R02_POWER_TRIALS
    simulation_bootstrap_resamples: Literal[R02_SIMULATION_BOOTSTRAP_RESAMPLES] = (
        R02_SIMULATION_BOOTSTRAP_RESAMPLES
    )
    supported_trials: int = Field(ge=0, le=R02_POWER_TRIALS)
    estimated_power_ppm: int = Field(ge=0, le=1_000_000)
    wilson_lower_power_ppm: int = Field(ge=0, le=1_000_000)
    wilson_upper_power_ppm: int = Field(ge=0, le=1_000_000)
    mean_simulated_theta_e12: int
    design_gate_scenario: bool

    @model_validator(mode="after")
    def validate_scenario(self) -> "R02PowerScenario":
        if self.total_n != self.representative_n + self.challenge_n:
            raise ValueError("power-scenario allocation mismatch")
        expected_power = round_ratio_half_even(
            self.supported_trials * 1_000_000,
            self.power_trials,
        )
        if self.estimated_power_ppm != expected_power:
            raise ValueError("power-scenario estimated power mismatch")
        if not (
            self.wilson_lower_power_ppm
            <= self.estimated_power_ppm
            <= self.wilson_upper_power_ppm
        ):
            raise ValueError("power estimate lies outside its Wilson interval")
        return self


class R02OpportunityProbability(StrictModel):
    schema_version: Literal["r02-opportunity-probability-v1"] = (
        "r02-opportunity-probability-v1"
    )
    scenario_id: str
    representative_n: Literal[R02_FRAME_REPRESENTATIVE_COUNT] = (
        R02_FRAME_REPRESENTATIVE_COUNT
    )
    challenge_n: Literal[R02_FRAME_CHALLENGE_COUNT] = R02_FRAME_CHALLENGE_COUNT
    representative_trigger_rate_bps: int = Field(ge=0, le=10_000)
    representative_candidate_collapse_rate_bps: int = Field(ge=0, le=10_000)
    m_min: Literal[R02_M_MIN] = R02_M_MIN
    exact_probability_ppb: int = Field(ge=0, le=1_000_000_000)


class R02ProviderBudgetFreeze(StrictModel):
    schema_version: Literal["r02-provider-budget-freeze-v1"] = (
        "r02-provider-budget-freeze-v1"
    )
    eligible_episode_count: int = Field(ge=1)
    per_episode_attempt_cap: Literal[R02_PER_EPISODE_ATTEMPT_CAP] = (
        R02_PER_EPISODE_ATTEMPT_CAP
    )
    retry_attempt_cap: Literal[R02_RETRY_ATTEMPT_CAP] = R02_RETRY_ATTEMPT_CAP
    provider_attempt_cap: int = Field(ge=1)
    per_attempt_token_reserve: Literal[R02_PER_ATTEMPT_TOKEN_RESERVE] = (
        R02_PER_ATTEMPT_TOKEN_RESERVE
    )
    aggregate_token_cap: int = Field(ge=1)
    incremental_usd_cap: Literal[R02_INCREMENTAL_USD_CAP] = R02_INCREMENTAL_USD_CAP
    maximum_draft_prompt_utf8_bytes: int = Field(ge=1)
    maximum_selector_payload_utf8_bytes: int = Field(ge=1)
    r01_observed_max_accounting_total_tokens: Literal[15_750] = 15_750
    budget_rationale: Literal[
        "R01_32000_RESERVE_REUSED_FOR_SMALLER_R02_SELECTOR_ONE_ATTEMPT_NO_RETRY"
    ] = "R01_32000_RESERVE_REUSED_FOR_SMALLER_R02_SELECTOR_ONE_ATTEMPT_NO_RETRY"
    zero_call_preflight_status: Literal["NOT_AUTHORIZED_NOT_FINALIZED"] = (
        "NOT_AUTHORIZED_NOT_FINALIZED"
    )
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False

    @model_validator(mode="after")
    def validate_budget(self) -> "R02ProviderBudgetFreeze":
        if self.provider_attempt_cap != (
            self.eligible_episode_count * self.per_episode_attempt_cap
        ):
            raise ValueError("provider attempt cap must cover each eligible episode once")
        if self.aggregate_token_cap != (
            self.provider_attempt_cap * self.per_attempt_token_reserve
        ):
            raise ValueError("aggregate token cap arithmetic mismatch")
        return self


class R02StatisticalFreeze(StrictModel):
    schema_version: Literal["r02-d2c-statistical-freeze-v1"] = (
        R02_STATS_SCHEMA_VERSION
    )
    status: Literal["PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"] = (
        "PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"
    )
    frame_id: str
    frame_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frame_full_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    statistics_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    numpy_version: str
    bit_generator: Literal["PCG64"] = "PCG64"
    simulation_seed_hex: str = Field(pattern=r"^[0-9a-f]{64}$")
    representative_n: Literal[R02_FRAME_REPRESENTATIVE_COUNT] = (
        R02_FRAME_REPRESENTATIVE_COUNT
    )
    challenge_n: Literal[R02_FRAME_CHALLENGE_COUNT] = R02_FRAME_CHALLENGE_COUNT
    total_n: Literal[
        R02_FRAME_REPRESENTATIVE_COUNT + R02_FRAME_CHALLENGE_COUNT
    ] = R02_FRAME_REPRESENTATIVE_COUNT + R02_FRAME_CHALLENGE_COUNT
    representative_target_weight_numerator: Literal[3] = 3
    challenge_target_weight_numerator: Literal[1] = 1
    target_weight_denominator: Literal[4] = 4
    primary_estimand: Literal[
        "round_half_even(3/4*mean(D_REPRESENTATIVE)+1/4*mean(D_CHALLENGE))"
    ] = "round_half_even(3/4*mean(D_REPRESENTATIVE)+1/4*mean(D_CHALLENGE))"
    zero_contribution_rule: Literal[
        "TRIGGER_FALSE_NO_CALL_INVALID_RESPONSE_AND_BASELINE_FALLBACK_ALL_D_EQ_0"
    ] = "TRIGGER_FALSE_NO_CALL_INVALID_RESPONSE_AND_BASELINE_FALLBACK_ALL_D_EQ_0"
    delta_min_e12: Literal[R02_DELTA_MIN_E12] = R02_DELTA_MIN_E12
    delta_min_basis_point_equivalent_millionths: Literal[500_000] = 500_000
    delta_target_e12: Literal[R02_DELTA_TARGET_E12] = R02_DELTA_TARGET_E12
    delta_target_basis_point_equivalent_millionths: Literal[1_000_000] = 1_000_000
    oracle_selector_upper_bound_theta_e12: int = Field(gt=R02_DELTA_TARGET_E12)
    observed_eligible_candidate_headroom_mean_e12: int = Field(gt=0)
    observed_eligible_candidate_headroom_sample_sd_e12: int = Field(gt=0)
    observed_eligible_candidate_headroom_standardized_mean_bps: int = Field(gt=0)
    maximum_frame_candidate_headroom_e12: int = Field(gt=0)
    delta_min_fraction_of_upper_bound_ppm: int = Field(gt=0, le=1_000_000)
    delta_target_fraction_of_upper_bound_ppm: int = Field(gt=0, le=1_000_000)
    m_min: Literal[R02_M_MIN] = R02_M_MIN
    low_trigger_label: Literal["INCONCLUSIVE_LOW_TRIGGER"] = (
        "INCONCLUSIVE_LOW_TRIGGER"
    )
    evaluation_bootstrap_resamples: Literal[R02_EVALUATION_BOOTSTRAP_RESAMPLES] = (
        R02_EVALUATION_BOOTSTRAP_RESAMPLES
    )
    bootstrap_resampling_unit: Literal["FIXTURE_WITHIN_STRATUM"] = (
        "FIXTURE_WITHIN_STRATUM"
    )
    bootstrap_interval: Literal["TWO_SIDED_95_PERCENTILE_NEAREST_RANK"] = (
        "TWO_SIDED_95_PERCENTILE_NEAREST_RANK"
    )
    bootstrap_lower_one_based_rank: Literal[250] = 250
    bootstrap_upper_one_based_rank: Literal[9_750] = 9_750
    decision_rule: Literal[
        "SUPPORTED_IFF_LOWER_GT_DELTA_MIN_AND_M_GE_M_MIN_AND_ALL_GATES_PASS"
    ] = "SUPPORTED_IFF_LOWER_GT_DELTA_MIN_AND_M_GE_M_MIN_AND_ALL_GATES_PASS"
    label_precedence: tuple[str, ...] = (
        "INVALID_RUN",
        "INCONCLUSIVE_LOW_TRIGGER",
        "SUPPORTED",
        "NOT_SUPPORTED",
        "INCONCLUSIVE_EFFECT",
    )
    power_target_ppm: Literal[R02_POWER_TARGET_PPM] = R02_POWER_TARGET_PPM
    opportunity_target_ppm: Literal[R02_OPPORTUNITY_TARGET_PPM] = (
        R02_OPPORTUNITY_TARGET_PPM
    )
    design_conditional_standardized_mean_bps: Literal[10_000] = 10_000
    low_snr_sensitivity_standardized_mean_bps: Literal[8_000] = 8_000
    r_equals_one_no_within_fixture_correlation: Literal[True] = True
    power_scenarios: tuple[R02PowerScenario, ...] = Field(min_length=15, max_length=15)
    opportunity_probabilities: tuple[R02OpportunityProbability, ...] = Field(
        min_length=4,
        max_length=4,
    )
    selected_design_scenario_id: str
    selected_design_power_ppm: int = Field(ge=R02_POWER_TARGET_PPM)
    selected_design_wilson_lower_power_ppm: int = Field(ge=R02_POWER_TARGET_PPM)
    observed_representative_trigger_count: int = Field(ge=0)
    observed_representative_trigger_rate_bps: int = Field(ge=0, le=10_000)
    observed_total_eligible_count: int = Field(ge=R02_M_MIN)
    observed_trigger_recalibration: Literal[False] = False
    provider_budget: R02ProviderBudgetFreeze
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    zero_call_preflight_status: Literal["NOT_AUTHORIZED_NOT_FINALIZED"] = (
        "NOT_AUTHORIZED_NOT_FINALIZED"
    )

    @model_validator(mode="after")
    def validate_freeze(self) -> "R02StatisticalFreeze":
        if self.total_n != self.representative_n + self.challenge_n:
            raise ValueError("statistical freeze allocation mismatch")
        if self.delta_min_e12 >= self.delta_target_e12:
            raise ValueError("delta target must exceed delta minimum")
        if self.delta_target_e12 >= self.oracle_selector_upper_bound_theta_e12:
            raise ValueError("delta target must remain below provider-free oracle upper bound")
        expected_standardized_mean = round_ratio_half_even(
            self.observed_eligible_candidate_headroom_mean_e12 * 10_000,
            self.observed_eligible_candidate_headroom_sample_sd_e12,
        )
        if (
            self.observed_eligible_candidate_headroom_standardized_mean_bps
            != expected_standardized_mean
        ):
            raise ValueError("observed candidate-headroom standardized mean mismatch")
        if (
            self.design_conditional_standardized_mean_bps
            > self.observed_eligible_candidate_headroom_standardized_mean_bps
        ):
            raise ValueError("design SNR exceeds its provider-free grounding statistic")
        if max(
            scenario.conditional_high_e12 for scenario in self.power_scenarios
        ) > self.maximum_frame_candidate_headroom_e12:
            raise ValueError("power scenario exceeds the frozen frame headroom support")
        selected = next(
            (
                scenario
                for scenario in self.power_scenarios
                if scenario.scenario_id == self.selected_design_scenario_id
            ),
            None,
        )
        if selected is None or not selected.design_gate_scenario:
            raise ValueError("selected power scenario is not the registered design gate")
        if selected.total_n != self.total_n:
            raise ValueError("selected power scenario allocation mismatch")
        if self.selected_design_power_ppm != selected.estimated_power_ppm:
            raise ValueError("selected power estimate mismatch")
        if (
            self.selected_design_wilson_lower_power_ppm
            != selected.wilson_lower_power_ppm
        ):
            raise ValueError("selected Wilson lower bound mismatch")
        if self.observed_total_eligible_count != self.provider_budget.eligible_episode_count:
            raise ValueError("observed eligibility and provider budget mismatch")
        return self


def stratified_weighted_mean_e12(
    representative_deltas: tuple[int, ...],
    challenge_deltas: tuple[int, ...],
) -> int:
    if not representative_deltas or not challenge_deltas:
        raise ValueError("both strata require at least one fixture")
    numerator = (
        3 * sum(representative_deltas) * len(challenge_deltas)
        + sum(challenge_deltas) * len(representative_deltas)
    )
    denominator = 4 * len(representative_deltas) * len(challenge_deltas)
    return round_ratio_half_even(numerator, denominator)


def stratified_bootstrap_interval_e12(
    representative_deltas: tuple[int, ...],
    challenge_deltas: tuple[int, ...],
    *,
    seed_hex: str,
    resamples: int = R02_EVALUATION_BOOTSTRAP_RESAMPLES,
) -> tuple[int, int]:
    if resamples != R02_EVALUATION_BOOTSTRAP_RESAMPLES:
        raise ValueError("evaluation bootstrap resample count is frozen")
    rng = np.random.Generator(np.random.PCG64(int(seed_hex, 16)))
    representative = np.asarray(representative_deltas, dtype=np.int64)
    challenge = np.asarray(challenge_deltas, dtype=np.int64)
    values = []
    for _ in range(resamples):
        rep_sample = representative[rng.integers(0, len(representative), len(representative))]
        challenge_sample = challenge[rng.integers(0, len(challenge), len(challenge))]
        values.append(
            stratified_weighted_mean_e12(
                tuple(int(value) for value in rep_sample),
                tuple(int(value) for value in challenge_sample),
            )
        )
    values.sort()
    return values[249], values[9_749]


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
    return (
        round((center - margin) * 1_000_000),
        round((center + margin) * 1_000_000),
    )


def _scenario_seed(simulation_seed_hex: str, scenario_id: str) -> int:
    return int.from_bytes(
        hashlib.sha256(
            f"r02-power|{simulation_seed_hex}|{scenario_id}".encode("utf-8")
        ).digest()[:16],
        "big",
    )


def _simulate_scenario(
    *,
    simulation_seed_hex: str,
    total_n: int,
    representative_trigger_rate_bps: int,
    representative_candidate_collapse_rate_bps: int,
    valid_selector_rate_bps: int,
    fail_closed_rate_bps: int,
    conditional_standardized_mean_bps: int,
    scenario_label: str,
    design_gate_scenario: bool,
) -> R02PowerScenario:
    representative_n = total_n * 3 // 4
    challenge_n = total_n - representative_n
    scenario_id = f"n{total_n}-{scenario_label}"
    p_trigger = representative_trigger_rate_bps / 10_000
    p_not_collapsed = 1 - representative_candidate_collapse_rate_bps / 10_000
    p_valid = valid_selector_rate_bps / 10_000
    p_not_failed = 1 - fail_closed_rate_bps / 10_000
    active_weight = (
        0.75 * p_trigger * p_not_collapsed * p_valid * p_not_failed
        + 0.25 * p_valid * p_not_failed
    )
    conditional_mean = round(R02_DELTA_TARGET_E12 / active_weight)
    conditional_sd = round(
        conditional_mean * 10_000 / conditional_standardized_mean_bps
    )
    standardized_mean = conditional_standardized_mean_bps / 10_000
    positive_probability = standardized_mean**2 / (1 + standardized_mean**2)
    conditional_high = round(conditional_mean / positive_probability)
    rng = np.random.Generator(
        np.random.PCG64(_scenario_seed(simulation_seed_hex, scenario_id))
    )
    supported = 0
    theta_sum = 0
    lower_rank_index = math.ceil(
        0.025 * R02_SIMULATION_BOOTSTRAP_RESAMPLES
    ) - 1
    for _ in range(R02_POWER_TRIALS):
        representative_active = (
            (rng.random(representative_n) < p_trigger)
            & (rng.random(representative_n) < p_not_collapsed)
            & (rng.random(representative_n) < p_valid)
            & (rng.random(representative_n) < p_not_failed)
        )
        challenge_active = (
            (rng.random(challenge_n) < p_valid)
            & (rng.random(challenge_n) < p_not_failed)
        )
        representative = np.where(
            representative_active & (rng.random(representative_n) < positive_probability),
            conditional_high,
            0,
        ).astype(np.int64)
        challenge = np.where(
            challenge_active & (rng.random(challenge_n) < positive_probability),
            conditional_high,
            0,
        ).astype(np.int64)
        theta_sum += stratified_weighted_mean_e12(
            tuple(int(value) for value in representative),
            tuple(int(value) for value in challenge),
        )
        representative_indexes = rng.integers(
            0,
            representative_n,
            size=(R02_SIMULATION_BOOTSTRAP_RESAMPLES, representative_n),
        )
        challenge_indexes = rng.integers(
            0,
            challenge_n,
            size=(R02_SIMULATION_BOOTSTRAP_RESAMPLES, challenge_n),
        )
        representative_sums = representative[representative_indexes].sum(axis=1)
        challenge_sums = challenge[challenge_indexes].sum(axis=1)
        bootstrap_numerators = (
            3 * representative_sums * challenge_n
            + challenge_sums * representative_n
        )
        lower_numerator = np.partition(
            bootstrap_numerators,
            lower_rank_index,
        )[lower_rank_index]
        threshold_numerator = (
            R02_DELTA_MIN_E12 * 4 * representative_n * challenge_n
        )
        supported += int(lower_numerator > threshold_numerator)
    estimated_power_ppm = round_ratio_half_even(
        supported * 1_000_000,
        R02_POWER_TRIALS,
    )
    lower_ppm, upper_ppm = _wilson_interval_ppm(supported, R02_POWER_TRIALS)
    return R02PowerScenario(
        scenario_id=scenario_id,
        total_n=total_n,
        representative_n=representative_n,
        challenge_n=challenge_n,
        representative_trigger_rate_bps=representative_trigger_rate_bps,
        representative_candidate_collapse_rate_bps=(
            representative_candidate_collapse_rate_bps
        ),
        valid_selector_rate_bps=valid_selector_rate_bps,
        fail_closed_rate_bps=fail_closed_rate_bps,
        conditional_standardized_mean_bps=conditional_standardized_mean_bps,
        conditional_positive_probability_ppm=round(positive_probability * 1_000_000),
        conditional_mean_e12=conditional_mean,
        conditional_sd_e12=conditional_sd,
        conditional_high_e12=conditional_high,
        supported_trials=supported,
        estimated_power_ppm=estimated_power_ppm,
        wilson_lower_power_ppm=lower_ppm,
        wilson_upper_power_ppm=upper_ppm,
        mean_simulated_theta_e12=round_ratio_half_even(theta_sum, R02_POWER_TRIALS),
        design_gate_scenario=design_gate_scenario,
    )


def _power_scenarios(simulation_seed_hex: str) -> tuple[R02PowerScenario, ...]:
    templates = (
        ("design-worst", 800, 500, 9_500, 500, 10_000, True),
        ("observed-rate", 1_250, 500, 9_500, 500, 10_000, False),
        ("clean", 800, 0, 10_000, 0, 10_000, False),
        ("low-snr-sensitivity", 800, 500, 9_500, 500, 8_000, False),
        ("high-snr-sensitivity", 800, 500, 9_500, 500, 12_000, False),
    )
    return tuple(
        _simulate_scenario(
            simulation_seed_hex=simulation_seed_hex,
            total_n=total_n,
            representative_trigger_rate_bps=trigger,
            representative_candidate_collapse_rate_bps=collapse,
            valid_selector_rate_bps=valid,
            fail_closed_rate_bps=fail_closed,
            conditional_standardized_mean_bps=standardized_mean,
            scenario_label=label,
            design_gate_scenario=design_gate,
        )
        for total_n in (120, 160, 200)
        for (
            label,
            trigger,
            collapse,
            valid,
            fail_closed,
            standardized_mean,
            design_gate,
        ) in templates
    )


def _binomial_tail_probability(n: int, probability: float, minimum: int) -> float:
    return sum(
        math.comb(n, value)
        * probability**value
        * (1 - probability) ** (n - value)
        for value in range(minimum, n + 1)
    )


def _opportunity_probabilities() -> tuple[R02OpportunityProbability, ...]:
    scenarios = (
        ("rep-8pct-collapse-0pct", 800, 0),
        ("rep-8pct-collapse-5pct", 800, 500),
        ("rep-12.5pct-collapse-0pct", 1_250, 0),
        ("rep-12.5pct-collapse-5pct", 1_250, 500),
    )
    required_representative = R02_M_MIN - R02_FRAME_CHALLENGE_COUNT
    return tuple(
        R02OpportunityProbability(
            scenario_id=scenario_id,
            representative_trigger_rate_bps=trigger_bps,
            representative_candidate_collapse_rate_bps=collapse_bps,
            exact_probability_ppb=round(
                _binomial_tail_probability(
                    R02_FRAME_REPRESENTATIVE_COUNT,
                    (trigger_bps / 10_000) * (1 - collapse_bps / 10_000),
                    required_representative,
                )
                * 1_000_000_000
            ),
        )
        for scenario_id, trigger_bps, collapse_bps in scenarios
    )


def _prompt_budget_evidence(
    manifest: R02FrameManifest,
    store: R02AppendOnlyArtifactStore,
) -> tuple[int, int]:
    prompt_sizes = []
    payload_sizes = []
    for case in manifest.cases:
        if not case.eligible_opportunity:
            continue
        episode = SyntheticEpisode.model_validate_json(
            store.read_bytes(case.fixture_artifact)
        )
        preparation = prepare_provider_free_episode(
            episode,
            experiment_id=manifest.frame_id,
            provider_attempt_count=0,
        )
        request = build_selector_request(preparation)
        prompt_sizes.append(
            len(
                (
                    request.prompt.system_prompt
                    + "\n"
                    + request.prompt.user_prompt
                ).encode("utf-8")
            )
        )
        payload_sizes.append(len(canonical_json_bytes(request.selector_payload)))
    if len(prompt_sizes) != manifest.total_eligible_count:
        raise R02StatisticsError("prompt budget evidence did not cover every eligible case")
    return max(prompt_sizes), max(payload_sizes)


def _statistics_source_sha256() -> str:
    return sha256_hex(Path(__file__).read_bytes())


def build_statistical_freeze(
    manifest: R02FrameManifest,
    seal: R02FrameSeal,
    store: R02AppendOnlyArtifactStore,
) -> R02StatisticalFreeze:
    if canonical_sha256(manifest) != seal.frame_manifest.sha256:
        raise R02StatisticsError("frame manifest does not match its seal reference")
    representative = tuple(
        case.candidate_headroom_e12 or 0
        for case in manifest.cases
        if case.stratum is R02FrameStratum.REPRESENTATIVE
    )
    challenge = tuple(
        case.candidate_headroom_e12 or 0
        for case in manifest.cases
        if case.stratum is R02FrameStratum.CHALLENGE_HEADROOM
    )
    upper_bound = stratified_weighted_mean_e12(representative, challenge)
    simulation_seed_hex = sha256_hex(
        canonical_json_bytes(
            {
                "domain": "r02-d2c-statistical-simulation-v1",
                "frame_manifest_sha256": seal.frame_manifest.sha256,
                "frame_full_tree_sha256": seal.full_tree_sha256,
                "delta_min_e12": R02_DELTA_MIN_E12,
                "delta_target_e12": R02_DELTA_TARGET_E12,
            }
        )
    )
    power_scenarios = _power_scenarios(simulation_seed_hex)
    maximum_frame_headroom = max(
        case.candidate_headroom_e12 or 0 for case in manifest.cases
    )
    if max(scenario.conditional_high_e12 for scenario in power_scenarios) > (
        maximum_frame_headroom
    ):
        raise R02StatisticsError("power scenario exceeds the frozen frame headroom support")
    selected = next(
        scenario
        for scenario in power_scenarios
        if scenario.scenario_id == "n160-design-worst"
    )
    n120 = next(
        scenario
        for scenario in power_scenarios
        if scenario.scenario_id == "n120-design-worst"
    )
    if n120.wilson_lower_power_ppm >= R02_POWER_TARGET_PPM:
        raise R02StatisticsError("N=120 unexpectedly passes the frozen design grid")
    if selected.wilson_lower_power_ppm < R02_POWER_TARGET_PPM:
        raise R02StatisticsError("N=160 fails the frozen design power target")
    opportunities = _opportunity_probabilities()
    worst_opportunity = next(
        item for item in opportunities if item.scenario_id == "rep-8pct-collapse-5pct"
    )
    if worst_opportunity.exact_probability_ppb < R02_OPPORTUNITY_TARGET_PPM * 1_000:
        raise R02StatisticsError("M_min fails the frozen opportunity-probability target")
    maximum_prompt_bytes, maximum_payload_bytes = _prompt_budget_evidence(
        manifest,
        store,
    )
    eligible_headrooms = tuple(
        case.candidate_headroom_e12
        for case in manifest.cases
        if case.candidate_headroom_e12 is not None
    )
    headroom_sum = sum(eligible_headrooms)
    headroom_mean = round_ratio_half_even(headroom_sum, len(eligible_headrooms))
    sample_variance = (
        sum(value * value for value in eligible_headrooms)
        - headroom_sum * headroom_sum / len(eligible_headrooms)
    ) / (len(eligible_headrooms) - 1)
    headroom_sample_sd = round(math.sqrt(sample_variance))
    budget = R02ProviderBudgetFreeze(
        eligible_episode_count=manifest.total_eligible_count,
        provider_attempt_cap=manifest.total_eligible_count,
        aggregate_token_cap=(
            manifest.total_eligible_count * R02_PER_ATTEMPT_TOKEN_RESERVE
        ),
        maximum_draft_prompt_utf8_bytes=maximum_prompt_bytes,
        maximum_selector_payload_utf8_bytes=maximum_payload_bytes,
    )
    return R02StatisticalFreeze(
        frame_id=manifest.frame_id,
        frame_manifest_sha256=seal.frame_manifest.sha256,
        frame_full_tree_sha256=seal.full_tree_sha256,
        statistics_source_sha256=_statistics_source_sha256(),
        numpy_version=np.__version__,
        simulation_seed_hex=simulation_seed_hex,
        oracle_selector_upper_bound_theta_e12=upper_bound,
        observed_eligible_candidate_headroom_mean_e12=headroom_mean,
        observed_eligible_candidate_headroom_sample_sd_e12=headroom_sample_sd,
        observed_eligible_candidate_headroom_standardized_mean_bps=(
            round_ratio_half_even(headroom_mean * 10_000, headroom_sample_sd)
        ),
        maximum_frame_candidate_headroom_e12=maximum_frame_headroom,
        delta_min_fraction_of_upper_bound_ppm=round_ratio_half_even(
            R02_DELTA_MIN_E12 * 1_000_000,
            upper_bound,
        ),
        delta_target_fraction_of_upper_bound_ppm=round_ratio_half_even(
            R02_DELTA_TARGET_E12 * 1_000_000,
            upper_bound,
        ),
        power_scenarios=power_scenarios,
        opportunity_probabilities=opportunities,
        selected_design_scenario_id=selected.scenario_id,
        selected_design_power_ppm=selected.estimated_power_ppm,
        selected_design_wilson_lower_power_ppm=selected.wilson_lower_power_ppm,
        observed_representative_trigger_count=manifest.representative_trigger_count,
        observed_representative_trigger_rate_bps=round_ratio_half_even(
            manifest.representative_trigger_count * 10_000,
            manifest.representative_count,
        ),
        observed_total_eligible_count=manifest.total_eligible_count,
        provider_budget=budget,
    )


def _write_new(path: Path, value: StrictModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical_json_bytes(value))
        handle.write(b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--frame-manifest",
        type=Path,
        default=Path("docs/r02-d2c-frame-manifest.json"),
    )
    parser.add_argument(
        "--frame-seal",
        type=Path,
        default=Path("docs/r02-d2c-frame-seal.json"),
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_R02_FRAME_ARTIFACT_ROOT,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = R02FrameManifest.model_validate_json(args.frame_manifest.read_bytes())
    seal = R02FrameSeal.model_validate_json(args.frame_seal.read_bytes())
    store = R02AppendOnlyArtifactStore(args.artifact_root)
    freeze = build_statistical_freeze(manifest, seal, store)
    _write_new(args.output, freeze)
    print(canonical_json_bytes(freeze).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
