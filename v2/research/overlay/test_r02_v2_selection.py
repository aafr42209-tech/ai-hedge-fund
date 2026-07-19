from __future__ import annotations

import hashlib

import pytest

from ._r02_v2_test_helpers import fixed_payload
from .r02_v2_payload import canonical_candidate_id
from .r02_v2_selection import (
    assert_split_nonoverlap,
    attach_oracle_evaluation,
    R02V2SelectionError,
    replay_scorer_selection,
    seal_policy_selections,
    select_public_scorer,
)


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def test_oracle_evaluation_occurs_only_after_sealed_selections() -> None:
    payload = fixed_payload()
    sealed = seal_policy_selections(
        anonymous_case_sha256=_sha("representative"),
        stratum="REPRESENTATIVE",
        payload=payload,
    )
    candidate_ids = [canonical_candidate_id(item.candidate) for item in payload.candidates]
    utilities = {candidate_id: index * 100_000_000 for index, candidate_id in enumerate(candidate_ids)}
    evaluated = attach_oracle_evaluation(sealed, utilities)
    assert evaluated.sealed_case_sha256 == sealed.sealed_case_sha256
    with pytest.raises(R02V2SelectionError, match="exactly the sealed presented set"):
        attach_oracle_evaluation(sealed, {})


def test_scorer_selection_replays_and_split_roots_do_not_overlap() -> None:
    payload = fixed_payload()
    candidate_ids = [canonical_candidate_id(item.candidate) for item in payload.candidates]
    utilities = {candidate_id: index * 100_000_000 for index, candidate_id in enumerate(candidate_ids)}
    cases = tuple(
        attach_oracle_evaluation(
            seal_policy_selections(
                anonymous_case_sha256=_sha(label),
                stratum=stratum,
                payload=payload,
            ),
            utilities,
        )
        for label, stratum in (
            ("representative", "REPRESENTATIVE"),
            ("challenge", "CHALLENGE_HEADROOM"),
        )
    )
    report = select_public_scorer(cases)
    assert replay_scorer_selection(cases, report)
    memberships = {
        "SCHEMA_GENERATOR_DEVELOPMENT": {_sha("s0")},
        "COMPARATOR_SELECTION": {_sha("s1")},
        "HEADROOM_VALIDATION": {_sha("s2")},
        "BLINDED_LLM_PILOT": {_sha("s3")},
        "CONFIRMATORY_LIVE": {_sha("s4")},
    }
    assert_split_nonoverlap(memberships)
    memberships["CONFIRMATORY_LIVE"].add(_sha("s0"))
    with pytest.raises(R02V2SelectionError, match="split overlap"):
        assert_split_nonoverlap(memberships)
