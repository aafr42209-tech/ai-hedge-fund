"""Fixed in-memory vectors for overlay-v2 provider-free tests."""

from __future__ import annotations

from .contracts import ASSET_IDS, AssetState, CostSchedule, PublicEpisode, SIGNAL_IDS
from .r02_v2_contracts import (
    R02V2CandidateBatch,
    R02V2Decision,
    R02V2Payload,
    R02V2PresentedCandidate,
)
from .r02_v2_payload import public_context_from_episode, recompute_public_metrics


def fixed_public_episode() -> PublicEpisode:
    covariance = {row_id: {column_id: 100 if row_id == column_id else 0 for column_id in ASSET_IDS} for row_id in ASSET_IDS}
    assets = tuple(
        AssetState(
            asset_id=asset_id,
            price_cents=10_000 + index * 100,
            lot_size_shares=1,
            holdings_shares=10,
            signals_bps={signal_id: (index + 1) * (signal_index + 1) * 100 for signal_index, signal_id in enumerate(SIGNAL_IDS)},
            confidences_bps={signal_id: 8_000 - signal_index * 500 for signal_index, signal_id in enumerate(SIGNAL_IDS)},
            max_weight_bps=4_000,
            costs=CostSchedule(
                commission_cents=1,
                half_spread_bps=2,
                slippage_bps=3,
            ),
        )
        for index, asset_id in enumerate(ASSET_IDS)
    )
    invested = sum(asset.price_cents * asset.holdings_shares for asset in assets)
    return PublicEpisode(
        case_id="FIXED_IN_MEMORY_VECTOR",
        seed_hex="1" * 64,
        assets=assets,
        cash_cents=2_000_000 - invested,
        covariance_bp2=covariance,
        gross_limit_bps=10_000,
        lambda_ppm=100_000,
        max_trade_lots=2,
    )


def _candidate(
    changes: dict[str, tuple[str, int]],
) -> R02V2CandidateBatch:
    return R02V2CandidateBatch(
        decisions={
            asset_id: R02V2Decision(
                action=changes.get(asset_id, ("hold", 0))[0],
                quantity=changes.get(asset_id, ("hold", 0))[1],
            )
            for asset_id in ASSET_IDS
        }
    )


def fixed_payload() -> R02V2Payload:
    context = public_context_from_episode(fixed_public_episode())
    candidates = (
        _candidate({}),
        _candidate({"A0": ("buy", 1)}),
        _candidate({"A1": ("sell", 1), "A2": ("buy", 2)}),
    )
    return R02V2Payload(
        public_context=context,
        candidates=tuple(
            R02V2PresentedCandidate(
                presented_id=f"P{index:02d}",
                candidate=candidate,
                public_metrics=recompute_public_metrics(context, candidate),
            )
            for index, candidate in enumerate(candidates)
        ),
    )
