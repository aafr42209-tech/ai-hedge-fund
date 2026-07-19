from __future__ import annotations

from ._r02_v2_test_helpers import fixed_payload
from .r02_v2_comparator import (
    all_scorer_selections,
    public_return_proxy_bps,
    scorer_by_id,
    scorer_configurations,
    select_with_scorer,
)
from .r02_v2_contracts import R02V2Payload, R02V2PresentedCandidate


def test_frozen_family_contains_exactly_nineteen_scorers() -> None:
    configs = scorer_configurations()
    assert len(configs) == len({item.scorer_id for item in configs}) == 19
    assert sum(item.scorer_id == "ZERO_FORECAST_MIN_RISK_COST" for item in configs) == 1
    assert len(all_scorer_selections(fixed_payload())) == 19


def test_public_proxy_and_zero_forecast_are_integer_reproducible() -> None:
    payload = fixed_payload()
    zero = public_return_proxy_bps(
        payload,
        scorer_by_id("ZERO_FORECAST_MIN_RISK_COST"),
    )
    equal = public_return_proxy_bps(
        payload,
        scorer_by_id("PUBLIC_EQUAL_SCALE_0150"),
    )
    assert set(zero.values()) == {0}
    assert all(isinstance(value, int) for value in equal.values())
    assert equal == public_return_proxy_bps(
        payload,
        scorer_by_id("PUBLIC_EQUAL_SCALE_0150"),
    )


def test_selection_is_invariant_to_presented_order() -> None:
    payload = fixed_payload()
    scorer_id = "PUBLIC_S0_HEAVY_SCALE_0300"
    original = select_with_scorer(payload, scorer_id)
    reordered = R02V2Payload(
        public_context=payload.public_context,
        candidates=tuple(
            R02V2PresentedCandidate(
                presented_id=f"P{index:02d}",
                candidate=candidate.candidate,
                public_metrics=candidate.public_metrics,
            )
            for index, candidate in enumerate(reversed(payload.candidates))
        ),
    )
    changed = select_with_scorer(reordered, scorer_id)
    assert original.selected_canonical_candidate_id == changed.selected_canonical_candidate_id
