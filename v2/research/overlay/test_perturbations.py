from __future__ import annotations

from ._test_helpers import episode, hold_batch
from .contracts import ASSET_IDS, DecisionBatch, SIGNAL_IDS
from .perturbations import (
    apply_signal_order,
    inverse_map_decisions,
    permutation_from_canonical_order,
    present_episode,
    render_presented_json,
    restore_episode,
    reverse_json_key_order,
)


def test_asset_permutation_round_trip_restores_canonical_episode() -> None:
    public = episode().public
    permutation = permutation_from_canonical_order(tuple(reversed(ASSET_IDS)))
    presented = present_episode(public, permutation)
    assert restore_episode(presented, permutation) == public


def test_inverse_mapping_restores_decision_asset_identity() -> None:
    permutation = permutation_from_canonical_order(tuple(reversed(ASSET_IDS)))
    presented = hold_batch()
    canonical = inverse_map_decisions(presented, permutation)
    assert canonical.decisions["A5"] == presented.decisions["A0"]
    assert set(canonical.decisions) == set(ASSET_IDS)


def test_signal_and_json_key_order_change_representation_not_semantics() -> None:
    public = episode().public
    permutation = permutation_from_canonical_order(ASSET_IDS)
    original = present_episode(public, permutation)
    perturbed = apply_signal_order(original, tuple(reversed(SIGNAL_IDS)))
    perturbed = reverse_json_key_order(perturbed)
    assert render_presented_json(original) != render_presented_json(perturbed)
    assert restore_episode(perturbed, permutation) == public
