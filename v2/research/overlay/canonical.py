"""Canonical JSON, hashes, and strict raw-decision parsing for R01."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ValidationError


class CanonicalizationError(ValueError):
    """Raised when a value cannot enter the canonical R01 identity."""


class DecisionParseError(ValueError):
    """Raised when raw provider text violates the decision wire contract."""


class DuplicateKeyError(DecisionParseError):
    """Raised before JSON object pairs can silently overwrite each other."""


def _plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _plain(value.model_dump(mode="python"))
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        raise CanonicalizationError("floating-point values are prohibited")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("canonical JSON keys must be strings")
            result[key] = _plain(item)
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_plain(item) for item in value]
    raise CanonicalizationError(f"unsupported canonical type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize an integer-only object with one stable byte representation."""

    return json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_hex(canonical_json_bytes(value))


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _candidate_sources(raw: str) -> Iterator[tuple[str, int]]:
    """Yield source text and object offsets without allocating suffix copies."""

    stripped = raw.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        first_newline = stripped.find("\n")
        if first_newline != -1:
            yield stripped[first_newline + 1 : -3].strip(), 0
    for index, char in enumerate(stripped):
        if char == "{":
            yield stripped, index


def parse_json_object(raw: str) -> dict[str, Any]:
    """Extract the first strict JSON object without losing duplicate keys."""

    if not isinstance(raw, str):
        raise DecisionParseError("raw response must be text")
    decoder = json.JSONDecoder(object_pairs_hook=_reject_duplicates)
    last_error: Exception | None = None
    for source, offset in _candidate_sources(raw):
        try:
            value, _end = decoder.raw_decode(source, offset)
        except DuplicateKeyError:
            raise
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            continue
        if not isinstance(value, dict):
            last_error = DecisionParseError("top-level JSON value must be an object")
            continue
        return value
    raise DecisionParseError(f"no valid JSON object found: {last_error}")


def parse_decision_batch(raw: str):
    """Parse raw text into the strict DecisionBatch model."""

    from .contracts import DecisionBatch

    try:
        return DecisionBatch.model_validate(parse_json_object(raw))
    except (ValidationError, ValueError) as exc:
        if isinstance(exc, DecisionParseError):
            raise
        raise DecisionParseError(str(exc)) from exc
