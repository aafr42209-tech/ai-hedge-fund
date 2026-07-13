"""Deterministic, synthetic-only R01 fixture generation."""

from __future__ import annotations

import hashlib
import hmac
import random
from collections.abc import Iterable

from .arithmetic import BASIS_POINTS, round_ratio_half_even
from .canonical import canonical_sha256
from .contracts import (
    ASSET_IDS,
    SIGNAL_IDS,
    AssetState,
    CostSchedule,
    Decision,
    DecisionBatch,
    GeneratorConfig,
    HiddenEpisodeState,
    PublicEpisode,
    Regime,
    SyntheticEpisode,
)
from .lattice import hold_batch
from .validator import validate_batch

REGIMES: tuple[Regime, ...] = (
    "signal_consensus",
    "signal_conflict",
    "high_transaction_cost",
    "concentration_pressure",
    "existing_position_asymmetry",
    "noisy_confidence",
)


class FixtureGenerationError(RuntimeError):
    """The deterministic generator could not satisfy its contract."""


def derive_seed(root_seed: str | bytes, namespace: str, index: int) -> bytes:
    if index < 0:
        raise ValueError("fixture index must be nonnegative")
    key = root_seed.encode("utf-8") if isinstance(root_seed, str) else root_seed
    return hmac.new(key, f"{namespace}:{index}".encode("utf-8"), hashlib.sha256).digest()


def _regime_order(root_seed: str | bytes) -> tuple[Regime, ...]:
    key = root_seed.encode("utf-8") if isinstance(root_seed, str) else root_seed
    return tuple(
        sorted(
            REGIMES,
            key=lambda regime: hmac.new(key, f"regime:{regime}".encode(), hashlib.sha256).digest(),
        )
    )


def development_regime(root_seed: str | bytes, index: int) -> Regime:
    order = _regime_order(root_seed)
    return order[index % len(order)]


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def _covariance(rng: random.Random, regime: Regime) -> dict[str, dict[str, int]]:
    loadings: dict[str, tuple[int, int]] = {}
    idiosyncratic: dict[str, int] = {}
    for asset_id in ASSET_IDS:
        if regime == "concentration_pressure" and asset_id in {"A0", "A1"}:
            loadings[asset_id] = (2_200, 800 if asset_id == "A0" else 900)
        else:
            loadings[asset_id] = (rng.randint(-1_500, 1_500), rng.randint(-1_500, 1_500))
        idiosyncratic[asset_id] = rng.randint(800, 2_500)
    return {row_id: {column_id: (loadings[row_id][0] * loadings[column_id][0] + loadings[row_id][1] * loadings[column_id][1] + (idiosyncratic[row_id] ** 2 if row_id == column_id else 0)) for column_id in ASSET_IDS} for row_id in ASSET_IDS}


def _signal_state(rng: random.Random, regime: Regime, config: GeneratorConfig) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]], dict[str, int]]:
    signals: dict[str, dict[str, int]] = {}
    confidences: dict[str, dict[str, int]] = {}
    expected_returns: dict[str, int] = {}
    latents = {asset_id: rng.randint(-8_500, 8_500) for asset_id in ASSET_IDS}
    if regime == "concentration_pressure":
        latents["A0"], latents["A1"] = 8_500, 8_200

    for asset_id in ASSET_IDS:
        asset_signals: dict[str, int] = {}
        asset_confidences: dict[str, int] = {}
        for signal_index, signal_id in enumerate(SIGNAL_IDS):
            direction = -1 if regime == "signal_conflict" and signal_index % 2 else 1
            asset_signals[signal_id] = _clamp(
                direction * latents[asset_id] + rng.randint(-1_200, 1_200),
                -BASIS_POINTS,
                BASIS_POINTS,
            )
            asset_confidences[signal_id] = rng.randint(config.min_confidence_bps, BASIS_POINTS)
        if regime == "noisy_confidence":
            confidence_values = list(reversed(asset_confidences.values()))
            asset_confidences = dict(zip(SIGNAL_IDS, confidence_values, strict=True))
        signals[asset_id] = asset_signals
        confidences[asset_id] = asset_confidences

        if regime == "signal_conflict":
            signal_level = round_ratio_half_even(
                sum(asset_signals[s] * asset_confidences[s] for s in SIGNAL_IDS),
                sum(asset_confidences.values()),
            )
        else:
            signal_level = round_ratio_half_even(sum(asset_signals.values()), len(SIGNAL_IDS))
        forecast_scale = 75 if regime == "high_transaction_cost" else config.forecast_scale_bps
        expected_returns[asset_id] = _clamp(
            round_ratio_half_even(signal_level * forecast_scale, BASIS_POINTS) + rng.randint(-config.hidden_noise_bps, config.hidden_noise_bps),
            -config.forecast_scale_bps,
            config.forecast_scale_bps,
        )
    return signals, confidences, expected_returns


def _cost_schedule(rng: random.Random, regime: Regime, config: GeneratorConfig) -> CostSchedule:
    if regime == "high_transaction_cost":
        return CostSchedule(
            commission_cents=rng.randint(config.high_cost_commission_min_cents, config.high_cost_commission_max_cents),
            half_spread_bps=rng.randint(config.high_cost_bps_min, config.high_cost_bps_max),
            slippage_bps=rng.randint(config.high_cost_bps_min, config.high_cost_bps_max),
        )
    return CostSchedule(
        commission_cents=rng.randint(0, config.normal_commission_max_cents),
        half_spread_bps=rng.randint(1, config.normal_cost_bps_max),
        slippage_bps=rng.randint(1, config.normal_cost_bps_max),
    )


def _has_nonhold_action(public: PublicEpisode) -> bool:
    base = hold_batch().decisions
    for asset_id in ASSET_IDS:
        asset = public.assets_by_id[asset_id]
        candidates = [Decision(action="buy", quantity=asset.lot_size_shares, confidence=100, reasoning="probe")]
        if asset.holdings_shares >= asset.lot_size_shares:
            candidates.append(Decision(action="sell", quantity=asset.lot_size_shares, confidence=100, reasoning="probe"))
        for decision in candidates:
            decisions = dict(base)
            decisions[asset_id] = decision
            if validate_batch(public, DecisionBatch(decisions=decisions)).raw_valid:
                return True
    return False


def _generate_assets(
    config: GeneratorConfig,
    rng: random.Random,
    regime: Regime,
    signals: dict[str, dict[str, int]],
    confidences: dict[str, dict[str, int]],
) -> tuple[AssetState, ...]:
    assets: list[AssetState] = []
    for asset_id in ASSET_IDS:
        price = rng.randint(config.min_price_cents, config.max_price_cents)
        lot_notional_bps = rng.randint(
            config.min_lot_notional_bps,
            config.max_lot_notional_bps,
        )
        lot_target = config.pretrade_equity_cents * lot_notional_bps // BASIS_POINTS
        lot_size = max(1, lot_target // price)
        holding_lots = rng.randint(0, config.max_trade_lots)
        if regime == "existing_position_asymmetry" and asset_id in {"A0", "A1"}:
            holding_lots = config.max_trade_lots
        cap = rng.randint(config.min_asset_cap_bps, config.max_asset_cap_bps)
        if regime == "concentration_pressure" and asset_id in {"A0", "A1"}:
            cap = config.min_asset_cap_bps
        assets.append(
            AssetState(
                asset_id=asset_id,
                price_cents=price,
                lot_size_shares=lot_size,
                holdings_shares=holding_lots * lot_size,
                signals_bps=signals[asset_id],
                confidences_bps=confidences[asset_id],
                max_weight_bps=cap,
                costs=_cost_schedule(rng, regime, config),
            )
        )
    return tuple(assets)


def _attempt_episode(
    config: GeneratorConfig,
    root_seed: str | bytes,
    index: int,
    regime: Regime,
    attempt: int,
) -> SyntheticEpisode | None:
    base_seed = derive_seed(root_seed, "development", index)
    attempt_seed = hmac.new(base_seed, f"attempt:{attempt}".encode(), hashlib.sha256).digest()
    rng = random.Random(int.from_bytes(attempt_seed, "big"))
    signals, confidences, expected_returns = _signal_state(rng, regime, config)
    covariance = _covariance(rng, regime)
    gross_limit = rng.randint(config.min_gross_limit_bps, config.max_gross_limit_bps)

    assets = _generate_assets(config, rng, regime, signals, confidences)

    holdings_value = sum(asset.price_cents * asset.holdings_shares for asset in assets)
    if holdings_value > config.pretrade_equity_cents:
        return None
    cash = config.pretrade_equity_cents - holdings_value
    try:
        public = PublicEpisode(
            case_id=f"development-{index:04d}",
            seed_hex=base_seed.hex(),
            assets=assets,
            cash_cents=cash,
            covariance_bp2=covariance,
            gross_limit_bps=gross_limit,
            lambda_ppm=config.lambda_ppm,
            max_trade_lots=config.max_trade_lots,
        )
    except ValueError:
        return None
    if not validate_batch(public, hold_batch()).raw_valid or not _has_nonhold_action(public):
        return None
    hidden = HiddenEpisodeState(regime=regime, expected_returns_bps=expected_returns)
    content_sha256 = canonical_sha256({"public": public, "hidden": hidden})
    return SyntheticEpisode(public=public, hidden=hidden, content_sha256=content_sha256)


def generate_episode(
    config: GeneratorConfig,
    root_seed: str | bytes,
    index: int,
    *,
    split: str = "development",
) -> SyntheticEpisode:
    if split != "development":
        raise ValueError("Phase A may generate development fixtures only")
    regime = development_regime(root_seed, index)
    for attempt in range(config.max_generation_attempts):
        episode = _attempt_episode(config, root_seed, index, regime, attempt)
        if episode is not None:
            return episode
    raise FixtureGenerationError(f"failed to generate development fixture {index} after {config.max_generation_attempts} attempts")


def generate_development_episodes(
    config: GeneratorConfig,
    root_seed: str | bytes,
    count: int = 40,
) -> tuple[SyntheticEpisode, ...]:
    if count <= 0:
        raise ValueError("development fixture count must be positive")
    return tuple(generate_episode(config, root_seed, index) for index in range(count))


def regime_counts(episodes: Iterable[SyntheticEpisode]) -> dict[str, int]:
    counts = {regime: 0 for regime in REGIMES}
    for episode in episodes:
        counts[episode.hidden.regime] += 1
    return counts
