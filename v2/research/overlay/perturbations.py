"""Semantics-preserving perturbations and inverse mappings for R01 audits."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Protocol

from .contracts import ASSET_IDS, SIGNAL_IDS, DecisionBatch, PublicEpisode


@dataclass(frozen=True)
class AssetPermutation:
    """Bijection from presented anonymous IDs back to canonical IDs."""

    presented_to_canonical: dict[str, str]

    def __post_init__(self) -> None:
        if set(self.presented_to_canonical) != set(ASSET_IDS):
            raise ValueError("permutation must map every presented asset ID")
        if set(self.presented_to_canonical.values()) != set(ASSET_IDS):
            raise ValueError("permutation values must be a bijection over canonical IDs")

    @property
    def canonical_to_presented(self) -> dict[str, str]:
        return {canonical: presented for presented, canonical in self.presented_to_canonical.items()}


def permutation_from_canonical_order(order: tuple[str, ...]) -> AssetPermutation:
    if len(order) != len(ASSET_IDS) or set(order) != set(ASSET_IDS):
        raise ValueError("asset order must contain A0 through A5 exactly once")
    return AssetPermutation(dict(zip(ASSET_IDS, order, strict=True)))


def identity_permutation() -> AssetPermutation:
    return permutation_from_canonical_order(ASSET_IDS)


def present_episode(public: PublicEpisode, permutation: AssetPermutation) -> dict[str, Any]:
    assets = public.assets_by_id
    presented_assets: list[dict[str, Any]] = []
    for presented_id in ASSET_IDS:
        canonical_id = permutation.presented_to_canonical[presented_id]
        payload = assets[canonical_id].model_dump(mode="python")
        payload["asset_id"] = presented_id
        presented_assets.append(payload)
    covariance = {presented_row: {presented_column: public.covariance_bp2[permutation.presented_to_canonical[presented_row]][permutation.presented_to_canonical[presented_column]] for presented_column in ASSET_IDS} for presented_row in ASSET_IDS}
    return {
        "schema_version": public.schema_version,
        "case_id": public.case_id,
        "seed_hex": public.seed_hex,
        "assets": presented_assets,
        "cash_cents": public.cash_cents,
        "covariance_bp2": covariance,
        "gross_limit_bps": public.gross_limit_bps,
        "lambda_ppm": public.lambda_ppm,
        "max_trade_lots": public.max_trade_lots,
    }


def restore_episode(payload: dict[str, Any], permutation: AssetPermutation) -> PublicEpisode:
    restored = deepcopy(payload)
    for asset in restored["assets"]:
        asset["asset_id"] = permutation.presented_to_canonical[asset["asset_id"]]
    restored["assets"].sort(key=lambda asset: asset["asset_id"])
    restored["assets"] = tuple(restored["assets"])
    restored_covariance = {permutation.presented_to_canonical[presented_row]: {permutation.presented_to_canonical[presented_column]: value for presented_column, value in row.items()} for presented_row, row in restored["covariance_bp2"].items()}
    restored["covariance_bp2"] = restored_covariance
    return PublicEpisode.model_validate(restored)


def inverse_map_decisions(presented: DecisionBatch, permutation: AssetPermutation) -> DecisionBatch:
    return DecisionBatch(decisions={permutation.presented_to_canonical[presented_id]: decision for presented_id, decision in presented.decisions.items()})


def apply_signal_order(payload: dict[str, Any], order: tuple[str, ...]) -> dict[str, Any]:
    if len(order) != len(SIGNAL_IDS) or set(order) != set(SIGNAL_IDS):
        raise ValueError("signal order must contain S0 through S4 exactly once")
    result = deepcopy(payload)
    for asset in result["assets"]:
        asset["signals_bps"] = {signal_id: asset["signals_bps"][signal_id] for signal_id in order}
        asset["confidences_bps"] = {signal_id: asset["confidences_bps"][signal_id] for signal_id in order}
    return result


def reverse_json_key_order(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: reverse_json_key_order(value[key]) for key in reversed(tuple(value.keys()))}
    if isinstance(value, list):
        return [reverse_json_key_order(item) for item in value]
    return value


def render_presented_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


class RepresentationTransform(Protocol):
    """Phase B freezes the final wording/numeric-format implementation."""

    transform_id: str

    def render(self, payload: dict[str, Any]) -> str:
        ...
