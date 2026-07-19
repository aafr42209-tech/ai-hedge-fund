"""Provider-free oracle-headroom gate for the selected public scorer."""

from __future__ import annotations

import hashlib
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .arithmetic import round_ratio_half_even
from .canonical import canonical_sha256
from .contracts import StrictModel

MIN_REPRESENTATIVE_N = 150
MIN_CHALLENGE_N = 50
MIN_EFFECTIVE_TOTAL = 20
MIN_EFFECTIVE_BY_STRATUM = 5
MIN_MEAN_HEADROOM_E12 = 50_000_000
DEFAULT_BOOTSTRAP_RESAMPLES = 10_000

R02V2HeadroomDecision = Literal[
    "HEADROOM_GATE_PASS",
    "HEADROOM_GATE_FAIL",
    "HEADROOM_GATE_INCONCLUSIVE_LOW_INFORMATION",
    "INVALID_DESIGN",
]


class R02V2HeadroomError(RuntimeError):
    """Raised when headroom inputs violate the frozen provider-free contract."""


class R02V2HeadroomCase(StrictModel):
    anonymous_case_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stratum: Literal["REPRESENTATIVE", "CHALLENGE_HEADROOM"]
    oracle_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_public_scorer_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    oracle_utility_e12: int
    selected_public_scorer_utility_e12: int
    headroom_e12: int

    @model_validator(mode="after")
    def validate_headroom(self) -> "R02V2HeadroomCase":
        if self.headroom_e12 != (self.oracle_utility_e12 - self.selected_public_scorer_utility_e12):
            raise ValueError("headroom does not reproduce")
        return self

    @property
    def effective_discordance(self) -> bool:
        return self.oracle_candidate_id != self.selected_public_scorer_candidate_id


class R02V2HeadroomDiagnostics(StrictModel):
    minimum_single_fixture_zero_nullification_e12: int
    minimum_literal_leave_one_out_e12: int
    winsorized_5_percent_e12: int
    winsorized_10_percent_e12: int


class R02V2HeadroomReport(StrictModel):
    schema_version: Literal["r02-overlay-v2-headroom-report-v1"] = "r02-overlay-v2-headroom-report-v1"
    decision: R02V2HeadroomDecision
    representative_n: int = Field(ge=0)
    challenge_n: int = Field(ge=0)
    effective_discordance_total: int = Field(ge=0)
    effective_discordance_representative: int = Field(ge=0)
    effective_discordance_challenge: int = Field(ge=0)
    point_estimate_e12: int
    lower_95_e12: int
    upper_95_e12: int
    bootstrap_seed_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bootstrap_resamples: int = Field(gt=0)
    validity_errors: tuple[str, ...]
    diagnostics: R02V2HeadroomDiagnostics
    case_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report_hash(self) -> "R02V2HeadroomReport":
        expected = canonical_sha256({key: value for key, value in self.model_dump(mode="python").items() if key != "report_sha256"})
        if self.report_sha256 != expected:
            raise ValueError("headroom report hash mismatch")
        return self


def make_headroom_case(
    *,
    anonymous_case_sha256: str,
    stratum: Literal["REPRESENTATIVE", "CHALLENGE_HEADROOM"],
    oracle_candidate_id: str,
    selected_public_scorer_candidate_id: str,
    oracle_utility_e12: int,
    selected_public_scorer_utility_e12: int,
) -> R02V2HeadroomCase:
    return R02V2HeadroomCase(
        anonymous_case_sha256=anonymous_case_sha256,
        stratum=stratum,
        oracle_candidate_id=oracle_candidate_id,
        selected_public_scorer_candidate_id=(selected_public_scorer_candidate_id),
        oracle_utility_e12=oracle_utility_e12,
        selected_public_scorer_utility_e12=(selected_public_scorer_utility_e12),
        headroom_e12=(oracle_utility_e12 - selected_public_scorer_utility_e12),
    )


def _weighted_mean(rep: list[int], challenge: list[int]) -> int:
    if not rep or not challenge:
        raise R02V2HeadroomError("both headroom strata are required")
    numerator = 3 * sum(rep) * len(challenge) + sum(challenge) * len(rep)
    denominator = 4 * len(rep) * len(challenge)
    return round_ratio_half_even(numerator, denominator)


def _domain_seed(seed_sha256: str, label: str) -> int:
    if len(seed_sha256) != 64 or any(character not in "0123456789abcdef" for character in seed_sha256):
        raise R02V2HeadroomError("seed must be lowercase SHA-256 hex")
    return int.from_bytes(
        hashlib.sha256(f"r02-overlay-v2|{label}|{seed_sha256}".encode("ascii")).digest()[:16],
        "big",
    )


def _bootstrap_interval(
    representative: list[int],
    challenge: list[int],
    *,
    seed_sha256: str,
    resamples: int,
) -> tuple[int, int]:
    if resamples <= 0:
        raise R02V2HeadroomError("bootstrap resamples must be positive")
    rng = np.random.Generator(np.random.PCG64(_domain_seed(seed_sha256, "headroom-bootstrap")))
    rep = np.asarray(representative, dtype=np.int64)
    challenge_values = np.asarray(challenge, dtype=np.int64)
    estimates: list[int] = []
    for _ in range(resamples):
        sampled_rep = rep[rng.integers(0, len(rep), size=len(rep))]
        sampled_challenge = challenge_values[
            rng.integers(
                0,
                len(challenge_values),
                size=len(challenge_values),
            )
        ]
        estimates.append(
            _weighted_mean(
                [int(value) for value in sampled_rep],
                [int(value) for value in sampled_challenge],
            )
        )
    ordered = sorted(estimates)
    lower_index = max(math.ceil(0.025 * resamples) - 1, 0)
    upper_index = min(math.ceil(0.975 * resamples) - 1, resamples - 1)
    return ordered[lower_index], ordered[upper_index]


def _winsorize(values: list[int], fraction_ppm: int) -> list[int]:
    ordered = sorted(values)
    count = len(ordered) * fraction_ppm // 1_000_000
    if count <= 0 or count * 2 >= len(ordered):
        return list(values)
    lower = ordered[count]
    upper = ordered[-count - 1]
    return [min(max(value, lower), upper) for value in values]


def _diagnostics(rep: list[int], challenge: list[int]) -> R02V2HeadroomDiagnostics:
    zeroed: list[int] = []
    for stratum, values in (("rep", rep), ("challenge", challenge)):
        for index in range(len(values)):
            changed = list(values)
            changed[index] = 0
            zeroed.append(
                _weighted_mean(
                    changed if stratum == "rep" else rep,
                    changed if stratum == "challenge" else challenge,
                )
            )
    leave_one_out: list[int] = []
    for stratum, values in (("rep", rep), ("challenge", challenge)):
        if len(values) <= 1:
            continue
        for index in range(len(values)):
            changed = values[:index] + values[index + 1 :]
            leave_one_out.append(
                _weighted_mean(
                    changed if stratum == "rep" else rep,
                    changed if stratum == "challenge" else challenge,
                )
            )
    return R02V2HeadroomDiagnostics(
        minimum_single_fixture_zero_nullification_e12=min(zeroed),
        minimum_literal_leave_one_out_e12=(min(leave_one_out) if leave_one_out else _weighted_mean(rep, challenge)),
        winsorized_5_percent_e12=_weighted_mean(
            _winsorize(rep, 50_000),
            _winsorize(challenge, 50_000),
        ),
        winsorized_10_percent_e12=_weighted_mean(
            _winsorize(rep, 100_000),
            _winsorize(challenge, 100_000),
        ),
    )


def _invalid_design_report(
    cases: tuple[R02V2HeadroomCase, ...],
    *,
    seed_sha256: str,
    resamples: int,
    validity_errors: tuple[str, ...],
) -> R02V2HeadroomReport:
    representative = [case for case in cases if case.stratum == "REPRESENTATIVE"]
    challenge = [case for case in cases if case.stratum == "CHALLENGE_HEADROOM"]
    effective_rep = sum(case.effective_discordance for case in representative)
    effective_challenge = sum(case.effective_discordance for case in challenge)
    zero_diagnostics = R02V2HeadroomDiagnostics(
        minimum_single_fixture_zero_nullification_e12=0,
        minimum_literal_leave_one_out_e12=0,
        winsorized_5_percent_e12=0,
        winsorized_10_percent_e12=0,
    )
    body = {
        "schema_version": "r02-overlay-v2-headroom-report-v1",
        "decision": "INVALID_DESIGN",
        "representative_n": len(representative),
        "challenge_n": len(challenge),
        "effective_discordance_total": effective_rep + effective_challenge,
        "effective_discordance_representative": effective_rep,
        "effective_discordance_challenge": effective_challenge,
        "point_estimate_e12": 0,
        "lower_95_e12": 0,
        "upper_95_e12": 0,
        "bootstrap_seed_sha256": seed_sha256,
        "bootstrap_resamples": resamples,
        "validity_errors": validity_errors,
        "diagnostics": zero_diagnostics,
        "case_set_sha256": canonical_sha256(cases),
    }
    return R02V2HeadroomReport(
        **body,
        report_sha256=canonical_sha256(body),
    )


def evaluate_headroom(
    cases: tuple[R02V2HeadroomCase, ...],
    *,
    seed_sha256: str,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
) -> R02V2HeadroomReport:
    _domain_seed(seed_sha256, "headroom-input-validation")
    if resamples <= 0:
        raise R02V2HeadroomError("bootstrap resamples must be positive")
    if not cases:
        return _invalid_design_report(
            cases,
            seed_sha256=seed_sha256,
            resamples=resamples,
            validity_errors=("EMPTY_HEADROOM_CASE_SET",),
        )
    if len({case.anonymous_case_sha256 for case in cases}) != len(cases):
        return _invalid_design_report(
            cases,
            seed_sha256=seed_sha256,
            resamples=resamples,
            validity_errors=("DUPLICATE_ANONYMOUS_CASE_SHA256",),
        )
    representative = [case.headroom_e12 for case in cases if case.stratum == "REPRESENTATIVE"]
    challenge = [case.headroom_e12 for case in cases if case.stratum == "CHALLENGE_HEADROOM"]
    if not representative or not challenge:
        return _invalid_design_report(
            cases,
            seed_sha256=seed_sha256,
            resamples=resamples,
            validity_errors=("BOTH_HEADROOM_STRATA_REQUIRED",),
        )
    effective_rep = sum(case.effective_discordance for case in cases if case.stratum == "REPRESENTATIVE")
    effective_challenge = sum(case.effective_discordance for case in cases if case.stratum == "CHALLENGE_HEADROOM")
    validity_errors: list[str] = []
    if len(representative) < MIN_REPRESENTATIVE_N:
        validity_errors.append("REPRESENTATIVE_N_BELOW_150")
    if len(challenge) < MIN_CHALLENGE_N:
        validity_errors.append("CHALLENGE_N_BELOW_50")
    if effective_rep < MIN_EFFECTIVE_BY_STRATUM:
        validity_errors.append("REPRESENTATIVE_EFFECTIVE_DISCORDANCE_BELOW_5")
    if effective_challenge < MIN_EFFECTIVE_BY_STRATUM:
        validity_errors.append("CHALLENGE_EFFECTIVE_DISCORDANCE_BELOW_5")
    if effective_rep + effective_challenge < MIN_EFFECTIVE_TOTAL:
        validity_errors.append("TOTAL_EFFECTIVE_DISCORDANCE_BELOW_20")
    point = _weighted_mean(representative, challenge)
    lower, upper = _bootstrap_interval(
        representative,
        challenge,
        seed_sha256=seed_sha256,
        resamples=resamples,
    )
    if validity_errors:
        decision: R02V2HeadroomDecision = "HEADROOM_GATE_INCONCLUSIVE_LOW_INFORMATION"
    elif lower > MIN_MEAN_HEADROOM_E12:
        decision = "HEADROOM_GATE_PASS"
    else:
        decision = "HEADROOM_GATE_FAIL"
    body = {
        "schema_version": "r02-overlay-v2-headroom-report-v1",
        "decision": decision,
        "representative_n": len(representative),
        "challenge_n": len(challenge),
        "effective_discordance_total": effective_rep + effective_challenge,
        "effective_discordance_representative": effective_rep,
        "effective_discordance_challenge": effective_challenge,
        "point_estimate_e12": point,
        "lower_95_e12": lower,
        "upper_95_e12": upper,
        "bootstrap_seed_sha256": seed_sha256,
        "bootstrap_resamples": resamples,
        "validity_errors": tuple(validity_errors),
        "diagnostics": _diagnostics(representative, challenge),
        "case_set_sha256": canonical_sha256(cases),
    }
    return R02V2HeadroomReport(
        **body,
        report_sha256=canonical_sha256(body),
    )
