from __future__ import annotations

from ._test_helpers import episode, hold_batch
from .arithmetic import BASIS_POINTS, ceil_ratio
from .contracts import ASSET_IDS, Decision, DecisionBatch
from .validator import validate_batch


def _replace(batch: DecisionBatch, asset_id: str, decision: Decision) -> DecisionBatch:
    decisions = dict(batch.decisions)
    decisions[asset_id] = decision
    return DecisionBatch(decisions=decisions)


def test_hold_is_feasible_and_costless() -> None:
    fixture = episode()
    report = validate_batch(fixture.public, hold_batch())
    assert report.raw_valid and not report.fell_back
    assert report.cost_ledger.total_cost_cents == 0
    assert report.executable.cash_after_cents == fixture.public.cash_cents


def test_invalid_lot_causes_full_hold_fallback() -> None:
    fixture = episode()
    asset = fixture.public.assets_by_id["A0"]
    batch = _replace(
        hold_batch(),
        "A0",
        Decision(action="buy", quantity=asset.lot_size_shares + 1, confidence=50, reasoning="bad lot"),
    )
    report = validate_batch(fixture.public, batch)
    assert not report.raw_valid and report.fell_back
    assert {violation.code for violation in report.violations} == {"lot_multiple"}
    assert all(decision.action == "hold" for decision in report.executable.decisions.values())


def test_missing_asset_causes_schema_fallback() -> None:
    fixture = episode()
    payload = hold_batch().model_dump(mode="python")
    del payload["decisions"]["A5"]
    report = validate_batch(fixture.public, payload)
    assert not report.raw_valid and report.fell_back
    assert report.violations[0].code == "schema_invalid"


def test_trade_above_two_lots_fails_closed() -> None:
    fixture = episode()
    asset = fixture.public.assets_by_id["A0"]
    batch = _replace(
        hold_batch(),
        "A0",
        Decision(
            action="buy",
            quantity=3 * asset.lot_size_shares,
            confidence=50,
            reasoning="too many lots",
        ),
    )
    report = validate_batch(fixture.public, batch)
    assert not report.raw_valid and report.fell_back
    assert "max_trade_lots" in {violation.code for violation in report.violations}


def test_oversell_fails_closed() -> None:
    fixture = episode()
    asset = fixture.public.assets_by_id["A2"]
    assert asset.holdings_shares == 0
    batch = _replace(
        hold_batch(),
        "A2",
        Decision(
            action="sell",
            quantity=asset.lot_size_shares,
            confidence=50,
            reasoning="oversell",
        ),
    )
    report = validate_batch(fixture.public, batch)
    assert not report.raw_valid and report.fell_back
    assert "oversell" in {violation.code for violation in report.violations}


def test_joint_batch_limits_are_checked_after_simultaneous_execution() -> None:
    fixture = episode()
    batch = DecisionBatch(
        decisions={
            asset.asset_id: Decision(
                action="buy",
                quantity=2 * asset.lot_size_shares,
                confidence=50,
                reasoning="joint stress",
            )
            for asset in fixture.public.assets
        }
    )
    report = validate_batch(fixture.public, batch)
    codes = {violation.code for violation in report.violations}
    assert not report.raw_valid and report.fell_back
    assert {"negative_cash", "gross_exposure"} <= codes


def test_cost_ledger_uses_sealed_integer_formulas() -> None:
    fixture = episode()
    public = fixture.public
    for asset_id in ASSET_IDS:
        asset = public.assets_by_id[asset_id]
        batch = _replace(
            hold_batch(),
            asset_id,
            Decision(action="buy", quantity=asset.lot_size_shares, confidence=50, reasoning="cost"),
        )
        report = validate_batch(public, batch)
        if not report.raw_valid:
            continue
        line = report.cost_ledger.lines[0]
        assert line.half_spread_cents == ceil_ratio(line.notional_cents * asset.costs.half_spread_bps, BASIS_POINTS)
        assert line.slippage_cents == ceil_ratio(line.notional_cents * asset.costs.slippage_bps, BASIS_POINTS)
        assert line.total_cost_cents == (asset.costs.commission_cents + line.half_spread_cents + line.slippage_cents)
        assert report.executable.posttrade_equity_cents == (public.pretrade_equity_cents - line.total_cost_cents)
        return
    raise AssertionError("fixture contract promised a feasible non-hold action")


def test_decision_key_order_does_not_change_execution() -> None:
    fixture = episode()
    canonical = hold_batch()
    reversed_batch = DecisionBatch(decisions=dict(reversed(tuple(canonical.decisions.items()))))
    assert validate_batch(fixture.public, canonical).executable == validate_batch(fixture.public, reversed_batch).executable
