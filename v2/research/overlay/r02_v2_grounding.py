"""Strict response parsing and RFC 6901 grounding for R02 overlay v2."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import ValidationError

from .r02_v2_contracts import (
    R02V2FailureLabel,
    R02V2Payload,
    R02V2Reason,
    R02V2ReasonCode,
    R02V2Response,
)

FIELD_REF_PATTERN = re.compile(r"^/(public_context|candidates)(?:/(?:[^~/]|~0|~1)*)+$")
COMPARISON_REASON_CODES = frozenset(
    {
        R02V2ReasonCode.COST_TRADEOFF,
        R02V2ReasonCode.PARSIMONY,
        R02V2ReasonCode.TIE_BREAK,
    }
)


class R02V2GroundingError(ValueError):
    def __init__(self, label: R02V2FailureLabel, detail: str) -> None:
        self.label = label
        self.detail = detail
        super().__init__(f"{label.value}: {detail}")


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise R02V2GroundingError(
                R02V2FailureLabel.INVALID_JSON,
                f"duplicate key: {key}",
            )
        result[key] = value
    return result


def parse_response(raw: str | bytes) -> R02V2Response:
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    except UnicodeDecodeError as exc:
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_JSON,
            "response is not UTF-8",
        ) from exc
    if not isinstance(text, str):
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_JSON,
            "response must be text or bytes",
        )
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"invalid JSON constant: {token}")),
        )
    except R02V2GroundingError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_JSON,
            str(exc),
        ) from exc
    if not isinstance(value, dict):
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_JSON,
            "response root must be an object",
        )
    if set(value) != {
        "schema_version",
        "selected_candidate_id",
        "confidence",
        "reasons",
    }:
        raise R02V2GroundingError(
            R02V2FailureLabel.SCHEMA_INVALID,
            "response keys do not match the accepted schema",
        )
    reasons_value = value.get("reasons")
    if not isinstance(reasons_value, list):
        raise R02V2GroundingError(
            R02V2FailureLabel.SCHEMA_INVALID,
            "reasons must be an array",
        )
    try:
        reasons = tuple(
            R02V2Reason(
                code=R02V2ReasonCode(item["code"]),
                field_refs=tuple(item["field_refs"]),
            )
            for item in reasons_value
            if isinstance(item, dict) and set(item) == {"code", "field_refs"}
        )
        if len(reasons) != len(reasons_value):
            raise ValueError("reason keys do not match the accepted schema")
        response = R02V2Response(
            schema_version=value["schema_version"],
            selected_candidate_id=value["selected_candidate_id"],
            confidence=value["confidence"],
            reasons=reasons,
        )
        return response
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        label = R02V2FailureLabel.DUPLICATE_REASON_CODE if "reason codes must be unique" in str(exc) else R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE if "field reference" in str(exc) else R02V2FailureLabel.SCHEMA_INVALID
        raise R02V2GroundingError(label, str(exc)) from exc


def _decode_token(token: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(token):
        character = token[index]
        if character != "~":
            result.append(character)
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
            raise R02V2GroundingError(
                R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
                "only ~0 and ~1 escapes are valid",
            )
        result.append("~" if token[index + 1] == "0" else "/")
        index += 2
    return "".join(result)


def decode_pointer(pointer: str) -> tuple[str, ...]:
    if len(pointer) > 256 or not FIELD_REF_PATTERN.fullmatch(pointer):
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
            "field reference violates the accepted lexical contract",
        )
    return tuple(_decode_token(token) for token in pointer.split("/")[1:])


def _canonical_array_index(token: str, length: int) -> int:
    if token == "-" or not token.isascii() or not token.isdecimal():
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
            "array token must be a canonical nonnegative decimal index",
        )
    if len(token) > 1 and token.startswith("0"):
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
            "array indexes may not contain leading zeros",
        )
    index = int(token)
    if index >= length:
        raise R02V2GroundingError(
            R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
            "array index is out of bounds",
        )
    return index


def resolve_pointer(payload: R02V2Payload, pointer: str) -> Any:
    current: Any = payload.model_dump(mode="python")
    for token in decode_pointer(pointer):
        if isinstance(current, Mapping):
            if token not in current:
                raise R02V2GroundingError(
                    R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
                    f"missing object key: {token}",
                )
            current = current[token]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            current = current[_canonical_array_index(token, len(current))]
        else:
            raise R02V2GroundingError(
                R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
                "field reference traverses a scalar",
            )
    return current


def validate_grounding(
    payload: R02V2Payload,
    response: R02V2Response,
) -> dict[str, Any]:
    by_id = {candidate.presented_id: index for index, candidate in enumerate(payload.candidates)}
    if response.selected_candidate_id not in by_id:
        raise R02V2GroundingError(
            R02V2FailureLabel.UNKNOWN_PRESENTED_ID,
            response.selected_candidate_id,
        )
    selected_index = by_id[response.selected_candidate_id]
    resolved: dict[str, Any] = {}
    for reason in response.reasons:
        for pointer in reason.field_refs:
            tokens = decode_pointer(pointer)
            if tokens[0] == "candidates" and reason.code not in COMPARISON_REASON_CODES:
                if len(tokens) < 2:
                    raise R02V2GroundingError(
                        R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
                        "candidate reference lacks an index",
                    )
                referenced_index = _canonical_array_index(
                    tokens[1],
                    len(payload.candidates),
                )
                if referenced_index != selected_index:
                    raise R02V2GroundingError(
                        R02V2FailureLabel.INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE,
                        "reason references an unselected candidate",
                    )
            resolved[pointer] = resolve_pointer(payload, pointer)
    return resolved


def parse_and_validate_grounding(
    payload: R02V2Payload,
    raw: str | bytes,
) -> tuple[R02V2Response, dict[str, Any]]:
    response = parse_response(raw)
    return response, validate_grounding(payload, response)
