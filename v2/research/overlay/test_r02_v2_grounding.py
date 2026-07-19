from __future__ import annotations

import json

import pytest

from ._r02_v2_test_helpers import fixed_payload
from .r02_v2_contracts import R02V2FailureLabel
from .r02_v2_grounding import (
    parse_and_validate_grounding,
    R02V2GroundingError,
    resolve_pointer,
)


def _response(pointer: str, *, selected: str = "P00") -> str:
    return json.dumps(
        {
            "schema_version": "r02-overlay-v2-selector-response-draft-v1",
            "selected_candidate_id": selected,
            "confidence": 75,
            "reasons": [
                {
                    "code": "RISK_CONCENTRATION",
                    "field_refs": [pointer],
                }
            ],
        },
        separators=(",", ":"),
    )


def test_grounding_resolves_selected_candidate_pointer() -> None:
    payload = fixed_payload()
    response, resolved = parse_and_validate_grounding(
        payload,
        _response("/candidates/0/public_metrics/max_posttrade_asset_weight_bps"),
    )
    assert response.selected_candidate_id == "P00"
    assert len(resolved) == 1


@pytest.mark.parametrize(
    "pointer",
    [
        "/candidates/01/public_metrics",
        "/candidates/-/public_metrics",
        "/candidates/9/public_metrics",
        "/candidates/0/public_metrics/~2bad",
    ],
)
def test_grounding_rejects_invalid_rfc6901_paths(pointer: str) -> None:
    with pytest.raises(
        R02V2GroundingError,
        match=R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE.value,
    ):
        parse_and_validate_grounding(fixed_payload(), _response(pointer))


def test_grounding_rejects_wrong_candidate_scope() -> None:
    with pytest.raises(R02V2GroundingError, match="unselected candidate"):
        parse_and_validate_grounding(
            fixed_payload(),
            _response(
                "/candidates/1/public_metrics/non_hold_action_count",
                selected="P00",
            ),
        )


def test_pointer_decodes_escapes_exactly_once() -> None:
    payload = fixed_payload()
    with pytest.raises(R02V2GroundingError, match="missing object key"):
        resolve_pointer(payload, "/public_context/~0")
