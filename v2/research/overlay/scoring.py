"""Exact utility, regret, and repeated-decision metrics for R01."""

from __future__ import annotations

from itertools import combinations

from .arithmetic import (
    BASIS_POINTS,
    COVARIANCE_BP2_SCALE,
    mean_int,
    PARTS_PER_MILLION,
    round_ratio_half_even,
    UTILITY_SCALE,
)
from .contracts import (
    ASSET_IDS,
    CostLedger,
    DecisionBatch,
    EpisodeScore,
    ExecutableBatch,
    PublicEpisode,
    SyntheticEpisode,
    ValidationReport,
)


def score_with_returns(
    public: PublicEpisode,
    expected_returns_bps: dict[str, int],
    executable: ExecutableBatch,
    ledger: CostLedger,
) -> EpisodeScore:
    """Apply the sealed integer scoring DAG with no intermediate weight input."""

    assets = public.assets_by_id
    position_values = {asset_id: assets[asset_id].price_cents * executable.final_shares[asset_id] for asset_id in ASSET_IDS}
    equity = executable.posttrade_equity_cents
    return_numerator = sum(expected_returns_bps[asset_id] * position_values[asset_id] for asset_id in ASSET_IDS)
    return_e12 = round_ratio_half_even(
        return_numerator * UTILITY_SCALE,
        BASIS_POINTS * equity,
    )

    covariance_sum = 0
    for row_id in ASSET_IDS:
        for column_id in ASSET_IDS:
            covariance_sum += position_values[row_id] * public.covariance_bp2[row_id][column_id] * position_values[column_id]
    risk_e12 = round_ratio_half_even(
        public.lambda_ppm * covariance_sum * UTILITY_SCALE,
        PARTS_PER_MILLION * COVARIANCE_BP2_SCALE * equity * equity,
    )
    cost_e12 = round_ratio_half_even(
        ledger.total_cost_cents * UTILITY_SCALE,
        public.pretrade_equity_cents,
    )
    turnover_e12 = round_ratio_half_even(
        ledger.total_notional_cents * UTILITY_SCALE,
        public.pretrade_equity_cents,
    )
    return EpisodeScore(
        return_e12=return_e12,
        risk_e12=risk_e12,
        cost_e12=cost_e12,
        utility_e12=return_e12 - risk_e12 - cost_e12,
        turnover_e12=turnover_e12,
        total_cost_cents=ledger.total_cost_cents,
        weights_e12=executable.weights_e12,
    )


def score_episode(episode: SyntheticEpisode, validation: ValidationReport) -> EpisodeScore:
    return score_with_returns(
        episode.public,
        episode.hidden.expected_returns_bps,
        validation.executable,
        validation.cost_ledger,
    )


def normalized_regret_e12(policy_utility_e12: int, oracle_utility_e12: int, regret_scale_e12: int) -> int:
    if regret_scale_e12 <= 0:
        raise ValueError("regret_scale_e12 must be positive")
    return round_ratio_half_even(
        max(oracle_utility_e12 - policy_utility_e12, 0) * UTILITY_SCALE,
        regret_scale_e12,
    )


def primary_delta_e12(deterministic_regrets: list[int], llm_case_regrets: list[int]) -> int:
    if len(deterministic_regrets) != len(llm_case_regrets) or not deterministic_regrets:
        raise ValueError("paired nonempty case regrets are required")
    return mean_int([deterministic - llm for deterministic, llm in zip(deterministic_regrets, llm_case_regrets, strict=True)])


def modal_actions(batches: list[DecisionBatch]) -> dict[str, str]:
    """Per-asset modal action; any modal tie becomes ABSTAIN."""

    if not batches:
        raise ValueError("at least one batch is required")
    result: dict[str, str] = {}
    for asset_id in ASSET_IDS:
        counts: dict[str, int] = {}
        for batch in batches:
            action = batch.decisions[asset_id].action
            counts[action] = counts.get(action, 0) + 1
        best_count = max(counts.values())
        modes = [action for action, count in counts.items() if count == best_count]
        result[asset_id] = modes[0] if len(modes) == 1 else "ABSTAIN"
    return result


def pairwise_action_agreement_counts(batches: list[DecisionBatch]) -> tuple[int, int]:
    """Return exact numerator and denominator for pairwise micro agreement."""

    agreements = 0
    comparisons = 0
    for left, right in combinations(batches, 2):
        for asset_id in ASSET_IDS:
            comparisons += 1
            agreements += int(left.decisions[asset_id].action == right.decisions[asset_id].action)
    return agreements, comparisons


def invariance_flip_counts(reference_actions: dict[str, str], perturbed: DecisionBatch) -> tuple[int, int]:
    flips = sum(reference_actions[asset_id] != perturbed.decisions[asset_id].action for asset_id in ASSET_IDS)
    return flips, len(ASSET_IDS)
