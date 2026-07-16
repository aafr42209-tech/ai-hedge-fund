from __future__ import annotations

import pytest
from pydantic import ValidationError

from ._test_helpers import episode
from .arithmetic import mean_int, median_int, round_ratio_half_even
from .canonical import (
    canonical_json_bytes,
    CanonicalizationError,
    DecisionParseError,
    parse_decision_batch,
    parse_json_object,
)
from .contracts import (
    ArtifactReference,
    CodexAttemptTransportArtifacts,
    Decision,
    MAX_REASONING_CODEPOINTS,
)
from .llm_policy import build_policy_input, SYSTEM_PROMPT_V1


def test_round_ratio_half_even_signed_ties() -> None:
    assert [round_ratio_half_even(value, 2) for value in (1, 3, 5, -1, -3, -5)] == [0, 2, 2, 0, -2, -2]
    assert mean_int([1, 2]) == 2
    assert mean_int([-1, -2]) == -2
    assert median_int([9, 1, 4]) == 4
    assert median_int([1, 2, 3, 4]) == 2


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


def test_parser_finds_balanced_object_after_invalid_prose_braces() -> None:
    fixture = episode()
    raw = "prefix {not json} then " + canonical_json_bytes(
        {
            "decisions": {
                asset_id: {
                    "action": "hold",
                    "quantity": 0,
                    "confidence": 50,
                    "reasoning": "literal { brace } text",
                }
                for asset_id in fixture.public.assets_by_id
            }
        }
    ).decode("utf-8")
    parsed = parse_decision_batch(raw)
    assert set(parsed.decisions) == set(fixture.public.assets_by_id)


def test_parser_recovers_after_unterminated_quote_in_earlier_braces() -> None:
    raw = 'Note: {"unterminated string here} {"decisions": {}}'
    assert parse_json_object(raw) == {"decisions": {}}


@pytest.mark.parametrize(
    "raw",
    (
        '{"decisions": {}} trailing {"other": true}',
        '{"decisions": {}} {"decisions": {}}',
    ),
)
def test_parser_rejects_multiple_outer_json_objects(raw: str) -> None:
    with pytest.raises(DecisionParseError, match="multiple unambiguous"):
        parse_json_object(raw)


def test_parser_accepts_one_object_with_non_json_trailing_prose() -> None:
    assert parse_json_object('prefix {"decisions": {}} trailing prose') == {"decisions": {}}


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


def test_reasoning_limit_is_visible_and_schema_enforced() -> None:
    Decision(
        action="hold",
        quantity=0,
        confidence=0,
        reasoning="x" * MAX_REASONING_CODEPOINTS,
    )
    with pytest.raises(ValidationError):
        Decision(
            action="hold",
            quantity=0,
            confidence=0,
            reasoning="x" * (MAX_REASONING_CODEPOINTS + 1),
        )
    assert str(MAX_REASONING_CODEPOINTS) in SYSTEM_PROMPT_V1


def test_b1_transport_artifact_schema_is_explicitly_versioned() -> None:
    reference = ArtifactReference(
        relative_path="b1/artifact.json",
        sha256="0" * 64,
        size_bytes=0,
    )
    bundle = CodexAttemptTransportArtifacts(
        command_spec=reference,
        stdout_jsonl=reference,
        stderr=reference,
        process_status=reference,
        provider_response=reference,
    )
    assert bundle.schema_version == "r01-codex-attempt-transport-artifacts-v1"
