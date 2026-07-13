"""Common finite action lattice shared by every R01 policy."""

from __future__ import annotations

from itertools import product
from typing import Iterator

from .contracts import ASSET_IDS, Decision, DecisionBatch, PublicEpisode


def hold_batch() -> DecisionBatch:
    return DecisionBatch(decisions={asset_id: Decision(action="hold", quantity=0, confidence=100, reasoning="hold") for asset_id in ASSET_IDS})


def asset_decisions(public: PublicEpisode, asset_id: str) -> tuple[Decision, ...]:
    asset = public.assets_by_id[asset_id]
    available_sell_lots = min(public.max_trade_lots, asset.holdings_shares // asset.lot_size_shares)
    choices: list[Decision] = []
    for lots in range(available_sell_lots, 0, -1):
        choices.append(
            Decision(
                action="sell",
                quantity=lots * asset.lot_size_shares,
                confidence=100,
                reasoning="lattice",
            )
        )
    choices.append(Decision(action="hold", quantity=0, confidence=100, reasoning="lattice"))
    for lots in range(1, public.max_trade_lots + 1):
        choices.append(
            Decision(
                action="buy",
                quantity=lots * asset.lot_size_shares,
                confidence=100,
                reasoning="lattice",
            )
        )
    return tuple(choices)


def iter_candidate_batches(public: PublicEpisode) -> Iterator[DecisionBatch]:
    choices = [asset_decisions(public, asset_id) for asset_id in ASSET_IDS]
    for combination in product(*choices):
        yield DecisionBatch(decisions=dict(zip(ASSET_IDS, combination, strict=True)))
