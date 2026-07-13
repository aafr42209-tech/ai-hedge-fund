from __future__ import annotations

from ._test_helpers import episode, hold_batch
from .arithmetic import UTILITY_SCALE, round_ratio_half_even
from .baselines import equal_risk_policy, hold_policy, primary_deterministic
from .contracts import ASSET_IDS, Decision, DecisionBatch
from .oracle import solve_oracle
from .scoring import (
    invariance_flip_counts,
    modal_actions,
    normalized_regret_e12,
    pairwise_action_agreement_counts,
    score_episode,
)
from .validator import validate_batch


def test_hold_score_matches_raw_integer_dag() -> None:
    fixture = episode()
    report = validate_batch(fixture.public, hold_batch())
    score = score_episode(fixture, report)
    values = {asset_id: fixture.public.assets_by_id[asset_id].price_cents * report.executable.final_shares[asset_id] for asset_id in ASSET_IDS}
    expected_return = round_ratio_half_even(
        sum(fixture.hidden.expected_returns_bps[a] * values[a] for a in ASSET_IDS) * UTILITY_SCALE,
        10_000 * report.executable.posttrade_equity_cents,
    )
    assert score.return_e12 == expected_return
    assert score.cost_e12 == 0
    assert score.utility_e12 == score.return_e12 - score.risk_e12


def test_exact_oracle_bounds_all_preregistered_baselines() -> None:
    fixture = episode(1)
    first = solve_oracle(fixture)
    second = solve_oracle(fixture)
    assert first == second
    assert first.certificate.oracle_optimality_tolerance_e12 == 0
    for policy in (primary_deterministic(fixture), hold_policy(fixture), equal_risk_policy(fixture)):
        assert policy.score.utility_e12 <= first.score.utility_e12


def test_normalized_regret_is_exact_integer_ratio() -> None:
    assert normalized_regret_e12(90, 100, 20) == UTILITY_SCALE // 2
    assert normalized_regret_e12(110, 100, 20) == 0


def test_modal_tie_fails_closed_to_abstain() -> None:
    actions = ["buy", "buy", "sell", "sell", "hold"]
    batches = []
    fixture = episode()
    for action in actions:
        decisions = dict(hold_batch().decisions)
        asset = fixture.public.assets_by_id["A0"]
        quantity = 0 if action == "hold" else asset.lot_size_shares
        decisions["A0"] = Decision(action=action, quantity=quantity, confidence=50, reasoning="mode")
        batches.append(DecisionBatch(decisions=decisions))
    reference = modal_actions(batches)
    assert reference["A0"] == "ABSTAIN"
    flips, total = invariance_flip_counts(reference, batches[-1])
    assert flips >= 1 and total == 6


def test_pairwise_agreement_counts_micro_pairs() -> None:
    batches = [hold_batch(str(index)) for index in range(5)]
    agreements, comparisons = pairwise_action_agreement_counts(batches)
    assert comparisons == 10 * 6
    assert agreements == comparisons
