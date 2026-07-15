"""Deterministic portfolio-joint validation and fail-closed execution."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .arithmetic import BASIS_POINTS, ceil_ratio, round_ratio_half_even, UTILITY_SCALE
from .contracts import (
    ASSET_IDS,
    CostLedger,
    CostLine,
    DecisionBatch,
    ExecutableBatch,
    PublicEpisode,
    ValidationReport,
    Violation,
)
from .lattice import hold_batch


class ExecutableContractError(RuntimeError):
    """The fallback hold portfolio violated the fixture contract."""


def _trade_lattice_violations(
    public: PublicEpisode,
    batch: DecisionBatch,
) -> list[Violation]:
    violations: list[Violation] = []
    assets = public.assets_by_id
    for asset_id in ASSET_IDS:
        asset = assets[asset_id]
        decision = batch.decisions[asset_id]
        if decision.action == "hold":
            continue
        if decision.quantity % asset.lot_size_shares:
            violations.append(Violation(code="lot_multiple", asset_id=asset_id, detail="quantity is not a lot multiple"))
            continue
        lots = decision.quantity // asset.lot_size_shares
        if lots > public.max_trade_lots:
            violations.append(Violation(code="max_trade_lots", asset_id=asset_id, detail="quantity exceeds two lots"))
        if decision.action == "sell" and decision.quantity > asset.holdings_shares:
            violations.append(Violation(code="oversell", asset_id=asset_id, detail="sell exceeds current holdings"))
    return violations


def _apply_trades(
    public: PublicEpisode,
    batch: DecisionBatch,
) -> tuple[dict[str, int], int, CostLedger]:
    assets = public.assets_by_id
    final_shares = {asset_id: assets[asset_id].holdings_shares for asset_id in ASSET_IDS}
    cash_after = public.cash_cents
    lines: list[CostLine] = []
    for asset_id in ASSET_IDS:
        asset = assets[asset_id]
        decision = batch.decisions[asset_id]
        if decision.action == "hold":
            continue
        notional = asset.price_cents * decision.quantity
        half_spread = ceil_ratio(notional * asset.costs.half_spread_bps, BASIS_POINTS)
        slippage = ceil_ratio(notional * asset.costs.slippage_bps, BASIS_POINTS)
        total_cost = asset.costs.commission_cents + half_spread + slippage
        lines.append(
            CostLine(
                asset_id=asset_id,
                action=decision.action,
                quantity=decision.quantity,
                notional_cents=notional,
                commission_cents=asset.costs.commission_cents,
                half_spread_cents=half_spread,
                slippage_cents=slippage,
                total_cost_cents=total_cost,
            )
        )
        if decision.action == "buy":
            cash_after -= notional
            final_shares[asset_id] += decision.quantity
        else:
            cash_after += notional
            final_shares[asset_id] -= decision.quantity
        cash_after -= total_cost

    ledger = CostLedger(
        lines=tuple(lines),
        total_cost_cents=sum(line.total_cost_cents for line in lines),
        total_notional_cents=sum(line.notional_cents for line in lines),
    )
    return final_shares, cash_after, ledger


def _validate_portfolio_limits(
    public: PublicEpisode,
    batch: DecisionBatch,
    final_shares: dict[str, int],
    cash_after: int,
    ledger: CostLedger,
) -> tuple[ExecutableBatch | None, list[Violation]]:
    violations: list[Violation] = []
    assets = public.assets_by_id
    if cash_after < 0:
        violations.append(Violation(code="negative_cash", detail="post-trade cash is negative"))

    posttrade_equity = public.pretrade_equity_cents - ledger.total_cost_cents
    if posttrade_equity <= 0:
        violations.append(Violation(code="nonpositive_equity", detail="post-trade equity is not positive"))
        return None, violations

    weights_e12: dict[str, int] = {}
    gross_position_value = 0
    for asset_id in ASSET_IDS:
        asset = assets[asset_id]
        position_value = asset.price_cents * final_shares[asset_id]
        gross_position_value += position_value
        weights_e12[asset_id] = round_ratio_half_even(position_value * UTILITY_SCALE, posttrade_equity)
        if position_value * BASIS_POINTS > asset.max_weight_bps * posttrade_equity:
            violations.append(Violation(code="asset_weight", asset_id=asset_id, detail="post-trade asset cap exceeded"))
    if gross_position_value * BASIS_POINTS > public.gross_limit_bps * posttrade_equity:
        violations.append(Violation(code="gross_exposure", detail="post-trade gross limit exceeded"))

    if violations:
        return None, violations
    return (
        ExecutableBatch(
            decisions=batch.decisions,
            final_shares=final_shares,
            cash_after_cents=cash_after,
            posttrade_equity_cents=posttrade_equity,
            weights_e12=weights_e12,
        ),
        [],
    )


def _execute(
    public: PublicEpisode,
    batch: DecisionBatch,
) -> tuple[ExecutableBatch | None, CostLedger | None, list[Violation]]:
    violations = _trade_lattice_violations(public, batch)
    if violations:
        return None, None, violations
    final_shares, cash_after, ledger = _apply_trades(public, batch)
    executable, violations = _validate_portfolio_limits(
        public,
        batch,
        final_shares,
        cash_after,
        ledger,
    )
    return executable, ledger, violations


def _fallback(public: PublicEpisode, violations: list[Violation]) -> ValidationReport:
    batch = hold_batch()
    executable, ledger, hold_violations = _execute(public, batch)
    if executable is None or ledger is None or hold_violations:
        raise ExecutableContractError(f"hold fallback is infeasible: {hold_violations}")
    return ValidationReport(
        raw_valid=False,
        fell_back=True,
        violations=tuple(violations),
        executable=executable,
        cost_ledger=ledger,
    )


def fail_closed_hold(
    public: PublicEpisode,
    *,
    code: str,
    detail: str,
) -> ValidationReport:
    """Return the canonical hold fallback for an upstream response failure."""

    return _fallback(public, [Violation(code=code, detail=detail)])


def validate_batch(public: PublicEpisode, raw_batch: DecisionBatch | dict[str, Any]) -> ValidationReport:
    """Validate a complete order set; invalid raw input becomes a full hold."""

    if isinstance(raw_batch, DecisionBatch):
        batch = raw_batch
    else:
        try:
            batch = DecisionBatch.model_validate(raw_batch)
        except (ValidationError, ValueError) as exc:
            return _fallback(
                public,
                [Violation(code="schema_invalid", detail=str(exc))],
            )

    executable, ledger, violations = _execute(public, batch)
    if executable is None or ledger is None or violations:
        return _fallback(public, violations)
    return ValidationReport(
        raw_valid=True,
        fell_back=False,
        violations=(),
        executable=executable,
        cost_ledger=ledger,
    )
