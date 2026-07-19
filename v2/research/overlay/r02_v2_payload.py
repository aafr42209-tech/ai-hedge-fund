"""Canonical public-information payload construction for R02 overlay v2."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .arithmetic import BASIS_POINTS, round_ratio_half_even
from .canonical import canonical_sha256
from .contracts import (
    ASSET_IDS,
    AssetState,
    CostSchedule,
    Decision,
    DecisionBatch,
    PublicEpisode,
)
from .r02_contracts import R02CandidateBatch, R02CandidatePermutation
from .r02_v2_contracts import (
    R02V2Asset,
    R02V2CandidateBatch,
    R02V2CostSchedule,
    R02V2Decision,
    R02V2Payload,
    R02V2PresentedCandidate,
    R02V2PublicContext,
    R02V2PublicMetrics,
)
from .validator import validate_batch

FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "case_id",
        "fixture_id",
        "seed",
        "seed_hex",
        "split",
        "split_label",
        "regime",
        "expected_returns_bps",
        "oracle_score",
        "content_sha256",
    }
)


class R02V2PayloadError(RuntimeError):
    """Raised when a payload cannot be reproduced from public information."""


def public_context_from_episode(public: PublicEpisode) -> R02V2PublicContext:
    assets = tuple(
        R02V2Asset(
            asset_id=asset_id,
            price_cents=public.assets_by_id[asset_id].price_cents,
            lot_size_shares=public.assets_by_id[asset_id].lot_size_shares,
            holdings_shares=public.assets_by_id[asset_id].holdings_shares,
            signals_bps=dict(public.assets_by_id[asset_id].signals_bps),
            confidences_bps=dict(public.assets_by_id[asset_id].confidences_bps),
            max_weight_bps=public.assets_by_id[asset_id].max_weight_bps,
            costs=R02V2CostSchedule(**public.assets_by_id[asset_id].costs.model_dump(mode="python")),
        )
        for asset_id in ASSET_IDS
    )
    return R02V2PublicContext(
        assets=assets,
        cash_cents=public.cash_cents,
        covariance_bp2={row_id: {column_id: public.covariance_bp2[row_id][column_id] for column_id in ASSET_IDS} for row_id in ASSET_IDS},
        gross_limit_bps=public.gross_limit_bps,
        lambda_ppm=public.lambda_ppm,
        max_trade_lots=public.max_trade_lots,
        pretrade_equity_cents=public.pretrade_equity_cents,
    )


def public_episode_from_context(context: R02V2PublicContext) -> PublicEpisode:
    """Reconstruct the existing public arithmetic type using inert identifiers."""

    return PublicEpisode(
        case_id="R02_V2_PUBLIC_PAYLOAD",
        seed_hex="0" * 64,
        assets=tuple(
            AssetState(
                asset_id=asset.asset_id,
                price_cents=asset.price_cents,
                lot_size_shares=asset.lot_size_shares,
                holdings_shares=asset.holdings_shares,
                signals_bps=dict(asset.signals_bps),
                confidences_bps=dict(asset.confidences_bps),
                max_weight_bps=asset.max_weight_bps,
                costs=CostSchedule(**asset.costs.model_dump(mode="python")),
            )
            for asset in context.assets
        ),
        cash_cents=context.cash_cents,
        covariance_bp2={row_id: dict(context.covariance_bp2[row_id]) for row_id in ASSET_IDS},
        gross_limit_bps=context.gross_limit_bps,
        lambda_ppm=context.lambda_ppm,
        max_trade_lots=context.max_trade_lots,
    )


def v2_candidate_from_r02(candidate: R02CandidateBatch) -> R02V2CandidateBatch:
    return R02V2CandidateBatch(
        schema_version=candidate.schema_version,
        decisions={
            asset_id: R02V2Decision(
                action=candidate.decisions[asset_id].action,
                quantity=candidate.decisions[asset_id].quantity,
            )
            for asset_id in ASSET_IDS
        },
    )


def decision_batch_from_v2(candidate: R02V2CandidateBatch) -> DecisionBatch:
    return DecisionBatch(
        decisions={
            asset_id: Decision(
                action=candidate.decisions[asset_id].action,
                quantity=candidate.decisions[asset_id].quantity,
                confidence=100,
                reasoning="r02-v2:public-metric-recompute",
            )
            for asset_id in ASSET_IDS
        }
    )


def canonical_candidate_id(candidate: R02V2CandidateBatch) -> str:
    return canonical_sha256(candidate)


def recompute_public_metrics(
    context: R02V2PublicContext,
    candidate: R02V2CandidateBatch,
) -> R02V2PublicMetrics:
    public = public_episode_from_context(context)
    validation = validate_batch(public, decision_batch_from_v2(candidate))
    if not validation.raw_valid or validation.fell_back:
        raise R02V2PayloadError("presented candidate is not publicly executable")
    executable = validation.executable
    position_values = {asset_id: (public.assets_by_id[asset_id].price_cents * executable.final_shares[asset_id]) for asset_id in ASSET_IDS}
    equity = executable.posttrade_equity_cents
    gross_value = sum(position_values.values())
    gross_weight_bps = round_ratio_half_even(
        gross_value * BASIS_POINTS,
        equity,
    )
    max_weight_bps = max(
        round_ratio_half_even(
            position_values[asset_id] * BASIS_POINTS,
            equity,
        )
        for asset_id in ASSET_IDS
    )
    covariance_sum = sum(position_values[row_id] * public.covariance_bp2[row_id][column_id] * position_values[column_id] for row_id in ASSET_IDS for column_id in ASSET_IDS)
    if covariance_sum < 0:
        raise R02V2PayloadError("public variance numerator is negative")
    return R02V2PublicMetrics(
        non_hold_action_count=sum(candidate.decisions[asset_id].action != "hold" for asset_id in ASSET_IDS),
        total_quantity_shares=sum(candidate.decisions[asset_id].quantity for asset_id in ASSET_IDS),
        estimated_transaction_cost_cents=validation.cost_ledger.total_cost_cents,
        projected_holdings_shares=dict(executable.final_shares),
        posttrade_gross_weight_bps=gross_weight_bps,
        max_posttrade_asset_weight_bps=max_weight_bps,
        posttrade_variance_numerator=covariance_sum,
    )


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        forbidden = FORBIDDEN_PAYLOAD_KEYS.intersection(value)
        if forbidden:
            raise R02V2PayloadError(f"forbidden payload fields: {','.join(sorted(forbidden))}")
        for nested in value.values():
            _assert_no_forbidden_keys(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_no_forbidden_keys(nested)


def build_payload(
    public: PublicEpisode,
    permutation: R02CandidatePermutation,
) -> R02V2Payload:
    context = public_context_from_episode(public)
    candidates = tuple(
        R02V2PresentedCandidate(
            presented_id=presented.presented_id,
            candidate=(candidate := v2_candidate_from_r02(presented.candidate)),
            public_metrics=recompute_public_metrics(context, candidate),
        )
        for presented in permutation.presented_candidates
    )
    payload = R02V2Payload(public_context=context, candidates=candidates)
    _assert_no_forbidden_keys(payload.model_dump(mode="python"))
    return payload


def assert_public_metrics_reproduce(payload: R02V2Payload) -> None:
    for presented in payload.candidates:
        expected = recompute_public_metrics(
            payload.public_context,
            presented.candidate,
        )
        if presented.public_metrics != expected:
            raise R02V2PayloadError(f"public metric drift: {presented.presented_id}")
