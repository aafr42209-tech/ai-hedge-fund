from __future__ import annotations

import hashlib

from .r02_v2_headroom import evaluate_headroom, make_headroom_case


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _cases() -> tuple:
    cases = []
    for index in range(150):
        discordant = index < 20
        cases.append(
            make_headroom_case(
                anonymous_case_sha256=_sha(f"rep-{index}"),
                stratum="REPRESENTATIVE",
                oracle_candidate_id="a" * 64,
                selected_public_scorer_candidate_id=("b" * 64 if discordant else "a" * 64),
                oracle_utility_e12=(1_000_000_000 if discordant else 0),
                selected_public_scorer_utility_e12=0,
            )
        )
    for index in range(50):
        discordant = index < 10
        cases.append(
            make_headroom_case(
                anonymous_case_sha256=_sha(f"challenge-{index}"),
                stratum="CHALLENGE_HEADROOM",
                oracle_candidate_id="c" * 64,
                selected_public_scorer_candidate_id=("d" * 64 if discordant else "c" * 64),
                oracle_utility_e12=(1_000_000_000 if discordant else 0),
                selected_public_scorer_utility_e12=0,
            )
        )
    return tuple(cases)


def test_headroom_gate_is_deterministic_and_meets_information_floors() -> None:
    cases = _cases()
    first = evaluate_headroom(cases, seed_sha256="2" * 64, resamples=250)
    second = evaluate_headroom(cases, seed_sha256="2" * 64, resamples=250)
    assert first == second
    assert first.decision == "HEADROOM_GATE_PASS"
    assert first.effective_discordance_total == 30
    assert first.lower_95_e12 > 50_000_000


def test_headroom_gate_fails_closed_on_low_information() -> None:
    small = tuple(case for case in _cases() if case.anonymous_case_sha256 in {_sha("rep-0"), _sha("challenge-0")})
    report = evaluate_headroom(
        small,
        seed_sha256="3" * 64,
        resamples=20,
    )
    assert report.decision == "HEADROOM_GATE_INCONCLUSIVE_LOW_INFORMATION"
    assert report.validity_errors


def test_headroom_invalid_design_label_is_reachable() -> None:
    empty = evaluate_headroom((), seed_sha256="4" * 64, resamples=20)
    assert empty.decision == "INVALID_DESIGN"
    assert empty.validity_errors == ("EMPTY_HEADROOM_CASE_SET",)

    duplicate = (_cases()[0], _cases()[0])
    repeated = evaluate_headroom(duplicate, seed_sha256="4" * 64, resamples=20)
    assert repeated.decision == "INVALID_DESIGN"
    assert repeated.validity_errors == ("DUPLICATE_ANONYMOUS_CASE_SHA256",)
