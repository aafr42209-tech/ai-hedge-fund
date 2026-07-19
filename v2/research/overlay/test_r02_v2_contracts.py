from __future__ import annotations

import pytest
from pydantic import ValidationError

from ._r02_v2_test_helpers import fixed_payload
from .r02_v2_contracts import (
    PAYLOAD_SCHEMA_SHA256,
    R02V2InformationParity,
    R02V2PolicyBinding,
    RESPONSE_SCHEMA_SHA256,
    validate_accepted_metaschemas,
    validate_payload_instance,
)


def test_accepted_schemas_pass_metaschema_and_payload_validation() -> None:
    assert validate_accepted_metaschemas() == (
        PAYLOAD_SCHEMA_SHA256,
        RESPONSE_SCHEMA_SHA256,
    )
    validate_payload_instance(fixed_payload())


def test_information_parity_requires_identical_payload_digest() -> None:
    digest = fixed_payload().sha256()
    parity = R02V2InformationParity(
        deterministic=R02V2PolicyBinding(
            policy_id="PUBLIC_SCORE_V2",
            payload_sha256=digest,
        ),
        llm=R02V2PolicyBinding(
            policy_id="LLM_OVERLAY_V2",
            payload_sha256=digest,
        ),
    )
    assert parity.deterministic.payload_sha256 == parity.llm.payload_sha256
    with pytest.raises(ValidationError, match="byte-identical"):
        R02V2InformationParity(
            deterministic=parity.deterministic,
            llm=R02V2PolicyBinding(
                policy_id="LLM_OVERLAY_V2",
                payload_sha256="f" * 64,
            ),
        )
