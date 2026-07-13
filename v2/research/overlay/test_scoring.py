from __future__ import annotations

import pytest

from . import baselines, runner
from ._test_helpers import episode, hold_batch
from .arithmetic import UTILITY_SCALE, round_ratio_half_even
from .baselines import equal_risk_policy, hold_policy, primary_deterministic
from .contracts import ASSET_IDS, Decision, DecisionBatch
from .oracle import assert_oracle_bound, solve_oracle
from .scoring import (
    invariance_flip_counts,
    modal_actions,
    normalized_regret_e12,
    pairwise_action_agreement_counts,
    score_episode,
)
from .selection import candidate_tie_key
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


def test_oracle_bound_fails_closed_and_tie_key_uses_canonical_asset_order() -> None:
    fixture = episode(1)
    oracle = solve_oracle(fixture)
    with pytest.raises(RuntimeError, match="exceeds exact oracle"):
        assert_oracle_bound("bad policy", oracle.score.utility_e12 + 1, oracle)
    validation = validate_batch(fixture.public, hold_batch())
    reversed_executable = validation.executable.model_copy(update={"final_shares": dict(reversed(tuple(validation.executable.final_shares.items())))})
    reversed_validation = validation.model_copy(update={"executable": reversed_executable})
    assert candidate_tie_key(validation) == candidate_tie_key(reversed_validation)


def test_baseline_bundle_enforces_oracle_bound(monkeypatch) -> None:
    fixture = episode(2)
    oracle = solve_oracle(fixture)
    policy = primary_deterministic(fixture)
    bad_policy = policy.model_copy(update={"score": policy.score.model_copy(update={"utility_e12": oracle.score.utility_e12 + 1})})
    monkeypatch.setattr(runner, "primary_deterministic", lambda _episode: bad_policy)
    with pytest.raises(RuntimeError, match="primary_deterministic utility"):
        runner._baseline_utilities(fixture, oracle)


def test_equal_risk_internal_invariants_fail_closed() -> None:
    with pytest.raises(RuntimeError, match="caps exceed"):
        baselines._require_nonnegative_remaining_gross(-1)
    with pytest.raises(RuntimeError, match="target is incomplete"):
        baselines._ordered_complete_target({"A0": 0})
    complete = {asset_id: index for index, asset_id in enumerate(ASSET_IDS)}
    assert tuple(baselines._ordered_complete_target(complete)) == ASSET_IDS


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
