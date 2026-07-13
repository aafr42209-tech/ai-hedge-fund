from __future__ import annotations

import pytest
from pydantic import ValidationError

from ._test_helpers import episode
from .arithmetic import mean_int, round_ratio_half_even
from .canonical import (
    CanonicalizationError,
    DecisionParseError,
    canonical_json_bytes,
    parse_decision_batch,
)
from .contracts import Decision
from .llm_policy import build_policy_input


def test_round_ratio_half_even_signed_ties() -> None:
    assert [round_ratio_half_even(value, 2) for value in (1, 3, 5, -1, -3, -5)] == [0, 2, 2, 0, -2, -2]
    assert mean_int([1, 2]) == 2
    assert mean_int([-1, -2]) == -2


def test_canonical_json_is_sorted_and_integer_only() -> None:
    assert canonical_json_bytes({"b": 2, "a": [1, True]}) == b'{"a":[1,true],"b":2}'
    with pytest.raises(CanonicalizationError):
        canonical_json_bytes({"float": 1.0})


def test_strict_models_refuse_coercion() -> None:
    with pytest.raises(ValidationError):
        Decision(action="hold", quantity="0", confidence=0, reasoning="x")


def test_duplicate_json_keys_are_rejected_before_validation() -> None:
    with pytest.raises(DecisionParseError, match="duplicate JSON key"):
        parse_decision_batch('{"decisions":{},"decisions":{}}')


def test_policy_input_cannot_contain_hidden_state() -> None:
    fixture = episode()
    payload = build_policy_input(fixture.public)
    rendered = canonical_json_bytes(payload)
    assert b"expected_returns" not in rendered
    assert b"regime" not in rendered
    assert fixture.hidden.regime.encode() not in rendered


def test_decision_extra_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Decision(action="hold", quantity=0, confidence=0, reasoning="x", extra="no")
