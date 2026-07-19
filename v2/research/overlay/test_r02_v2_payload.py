from __future__ import annotations

import pytest
from pydantic import ValidationError

from ._r02_v2_test_helpers import fixed_payload, fixed_public_episode
from .r02_v2_contracts import R02V2Payload
from .r02_v2_payload import (
    assert_public_metrics_reproduce,
    FORBIDDEN_PAYLOAD_KEYS,
    public_context_from_episode,
    R02V2PayloadError,
)


def test_payload_is_canonical_public_only_and_reproducible() -> None:
    first = fixed_payload()
    second = fixed_payload()
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.sha256() == second.sha256()
    assert first.public_context == public_context_from_episode(fixed_public_episode())
    text = first.canonical_bytes().decode("utf-8")
    assert all(f'"{key}"' not in text for key in FORBIDDEN_PAYLOAD_KEYS)
    assert_public_metrics_reproduce(first)


def test_serialized_public_metrics_are_assertions_not_trusted_inputs() -> None:
    payload = fixed_payload()
    data = payload.model_dump(mode="python")
    data["candidates"][1]["public_metrics"]["estimated_transaction_cost_cents"] += 1
    tampered = R02V2Payload.model_validate(data)
    with pytest.raises(R02V2PayloadError, match="public metric drift"):
        assert_public_metrics_reproduce(tampered)


def test_payload_rejects_noncontiguous_presented_ids() -> None:
    payload = fixed_payload()
    data = payload.model_dump(mode="python")
    data["candidates"][1]["presented_id"] = "P03"
    with pytest.raises(ValidationError, match="contiguous"):
        R02V2Payload.model_validate(data)
