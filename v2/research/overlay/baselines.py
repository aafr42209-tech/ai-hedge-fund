"""Preregistered deterministic and safety baselines for R01."""

from __future__ import annotations

import operator
from math import isqrt

from .arithmetic import BASIS_POINTS, UTILITY_SCALE, round_ratio_half_even
from .contracts import (
    ASSET_IDS,
    SIGNAL_IDS,
    BaselineConfig,
    PolicyResult,
    PublicEpisode,
    SyntheticEpisode,
    ValidationReport,
)
from .lattice import hold_batch, iter_candidate_batches
from .scoring import score_episode, score_with_returns
from .selection import prefer_candidate
from .validator import validate_batch


def inferred_returns(public: PublicEpisode, config: BaselineConfig) -> dict[str, int]:
    result: dict[str, int] = {}
    for asset in public.assets:
        numerator = sum(config.signal_weights_bps[signal_id] * asset.signals_bps[signal_id] * asset.confidences_bps[signal_id] for signal_id in SIGNAL_IDS)
        result[asset.asset_id] = round_ratio_half_even(
            numerator * config.forecast_scale_bps,
            BASIS_POINTS**3,
        )
    return result


def primary_deterministic(episode: SyntheticEpisode, config: BaselineConfig | None = None) -> PolicyResult:
    config = config or BaselineConfig()
    estimates = inferred_returns(episode.public, config)
    best_validation: ValidationReport | None = None
    best_estimated_score = None
    for batch in iter_candidate_batches(episode.public):
        validation = validate_batch(episode.public, batch)
        if not validation.raw_valid:
            continue
        estimated_score = score_with_returns(
            episode.public,
            estimates,
            validation.executable,
            validation.cost_ledger,
        )
        if prefer_candidate(
            estimated_score.utility_e12,
            validation,
            None if best_estimated_score is None else best_estimated_score.utility_e12,
            best_validation,
            operator.gt,
        ):
            best_validation = validation
            best_estimated_score = estimated_score
    if best_validation is None:
        raise RuntimeError("fixture has no feasible deterministic-baseline portfolio")
    return PolicyResult(
        name="primary_deterministic",
        validation=best_validation,
        score=score_episode(episode, best_validation),
    )


def hold_policy(episode: SyntheticEpisode) -> PolicyResult:
    validation = validate_batch(episode.public, hold_batch())
    if not validation.raw_valid:
        raise RuntimeError("fixture violates the hold-feasible contract")
    return PolicyResult(name="hold", validation=validation, score=score_episode(episode, validation))


def _require_nonnegative_remaining_gross(remaining_gross: int) -> None:
    if remaining_gross < 0:
        raise RuntimeError("equal-risk caps exceed the gross target")


def _ordered_complete_target(target: dict[str, int]) -> dict[str, int]:
    if set(target) != set(ASSET_IDS):
        raise RuntimeError("equal-risk target is incomplete")
    return {asset_id: target[asset_id] for asset_id in ASSET_IDS}


def _equal_risk_target(public: PublicEpisode) -> dict[str, int]:
    inverse_vol = {asset_id: UTILITY_SCALE // max(1, isqrt(public.covariance_bp2[asset_id][asset_id])) for asset_id in ASSET_IDS}
    caps = {asset.asset_id: round_ratio_half_even(asset.max_weight_bps * UTILITY_SCALE, BASIS_POINTS) for asset in public.assets}
    remaining = list(ASSET_IDS)
    target: dict[str, int] = {}
    remaining_gross = round_ratio_half_even(public.gross_limit_bps * UTILITY_SCALE, BASIS_POINTS)
    while remaining:
        denominator = sum(inverse_vol[asset_id] for asset_id in remaining)
        proposed = {asset_id: round_ratio_half_even(remaining_gross * inverse_vol[asset_id], denominator) for asset_id in remaining}
        capped = [asset_id for asset_id in remaining if proposed[asset_id] > caps[asset_id]]
        if not capped:
            target.update(proposed)
            break
        for asset_id in capped:
            target[asset_id] = caps[asset_id]
            remaining_gross -= caps[asset_id]
            _require_nonnegative_remaining_gross(remaining_gross)
            remaining.remove(asset_id)
    return _ordered_complete_target(target)


def equal_risk_policy(episode: SyntheticEpisode) -> PolicyResult:
    target = _equal_risk_target(episode.public)
    best_validation: ValidationReport | None = None
    best_distance: int | None = None
    for batch in iter_candidate_batches(episode.public):
        validation = validate_batch(episode.public, batch)
        if not validation.raw_valid:
            continue
        distance = sum(abs(validation.executable.weights_e12[asset_id] - target[asset_id]) for asset_id in ASSET_IDS)
        if prefer_candidate(
            distance,
            validation,
            best_distance,
            best_validation,
            operator.lt,
        ):
            best_distance = distance
            best_validation = validation
    if best_validation is None:
        raise RuntimeError("fixture has no feasible equal-risk portfolio")
    return PolicyResult(
        name="equal_risk",
        validation=best_validation,
        score=score_episode(episode, best_validation),
    )
