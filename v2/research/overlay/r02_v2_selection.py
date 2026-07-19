"""Two-stage public-scorer selection with post-seal oracle evaluation."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from .arithmetic import round_ratio_half_even
from .canonical import canonical_sha256
from .contracts import StrictModel
from .r02_v2_comparator import (
    all_scorer_selections,
    R02V2ComparatorSelection,
    scorer_by_id,
)
from .r02_v2_contracts import R02V2Payload

R02V2Stratum = Literal["REPRESENTATIVE", "CHALLENGE_HEADROOM"]


class R02V2SelectionError(RuntimeError):
    """Raised when scorer selection crosses the oracle or split boundary."""


class R02V2SealedSelectionCase(StrictModel):
    schema_version: Literal["r02-overlay-v2-sealed-selection-case-v1"] = "r02-overlay-v2-sealed-selection-case-v1"
    anonymous_case_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stratum: R02V2Stratum
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selections: tuple[R02V2ComparatorSelection, ...]
    sealed_case_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_seal(self) -> "R02V2SealedSelectionCase":
        if len(self.selections) != 19:
            raise ValueError("sealed case must contain all 19 scorer selections")
        if len({item.scorer_id for item in self.selections}) != 19:
            raise ValueError("sealed scorer IDs must be unique")
        if any(item.payload_sha256 != self.payload_sha256 for item in self.selections):
            raise ValueError("all scorers must bind the same payload")
        expected = canonical_sha256(
            {
                "schema_version": self.schema_version,
                "anonymous_case_sha256": self.anonymous_case_sha256,
                "stratum": self.stratum,
                "payload_sha256": self.payload_sha256,
                "selections": self.selections,
            }
        )
        if self.sealed_case_sha256 != expected:
            raise ValueError("sealed selection case hash mismatch")
        return self


class R02V2ScorerOutcome(StrictModel):
    scorer_id: str
    selected_canonical_candidate_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    oracle_utility_e12: int
    oracle_regret_e12: int = Field(ge=0)
    fell_back: bool = False


class R02V2EvaluatedSelectionCase(StrictModel):
    schema_version: Literal["r02-overlay-v2-evaluated-selection-case-v1"] = "r02-overlay-v2-evaluated-selection-case-v1"
    anonymous_case_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stratum: R02V2Stratum
    sealed_case_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    oracle_best_utility_e12: int
    outcomes: tuple[R02V2ScorerOutcome, ...]
    evaluation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_evaluation(self) -> "R02V2EvaluatedSelectionCase":
        if len(self.outcomes) != 19 or len({item.scorer_id for item in self.outcomes}) != 19:
            raise ValueError("evaluated case must contain 19 unique scorers")
        if any(outcome.oracle_regret_e12 != max(self.oracle_best_utility_e12 - outcome.oracle_utility_e12, 0) for outcome in self.outcomes):
            raise ValueError("oracle regret does not reproduce")
        expected = canonical_sha256(
            {
                "schema_version": self.schema_version,
                "anonymous_case_sha256": self.anonymous_case_sha256,
                "stratum": self.stratum,
                "sealed_case_sha256": self.sealed_case_sha256,
                "oracle_best_utility_e12": self.oracle_best_utility_e12,
                "outcomes": self.outcomes,
            }
        )
        if self.evaluation_sha256 != expected:
            raise ValueError("evaluation hash mismatch")
        return self


class R02V2ScorerAggregate(StrictModel):
    scorer_id: str
    weighted_full_frame_utility_e12: int
    weighted_oracle_regret_e12: int
    settled_fallback_count: int = Field(ge=0)
    complexity_rank: int = Field(ge=0)
    forecast_scale_bps: int = Field(ge=0)


class R02V2ScorerSelectionReport(StrictModel):
    schema_version: Literal["r02-overlay-v2-scorer-selection-report-v1"] = "r02-overlay-v2-scorer-selection-report-v1"
    evaluated_case_sha256s: tuple[str, ...]
    selected_scorer_id: str
    aggregates: tuple[R02V2ScorerAggregate, ...]
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report_hash(self) -> "R02V2ScorerSelectionReport":
        expected = canonical_sha256(
            {
                "schema_version": self.schema_version,
                "evaluated_case_sha256s": self.evaluated_case_sha256s,
                "selected_scorer_id": self.selected_scorer_id,
                "aggregates": self.aggregates,
            }
        )
        if self.report_sha256 != expected:
            raise ValueError("scorer-selection report hash mismatch")
        return self


def seal_policy_selections(
    *,
    anonymous_case_sha256: str,
    stratum: R02V2Stratum,
    payload: R02V2Payload,
) -> R02V2SealedSelectionCase:
    selections = all_scorer_selections(payload)
    body = {
        "schema_version": "r02-overlay-v2-sealed-selection-case-v1",
        "anonymous_case_sha256": anonymous_case_sha256,
        "stratum": stratum,
        "payload_sha256": payload.sha256(),
        "selections": selections,
    }
    return R02V2SealedSelectionCase(
        **body,
        sealed_case_sha256=canonical_sha256(body),
    )


def attach_oracle_evaluation(
    sealed: R02V2SealedSelectionCase,
    oracle_utility_by_candidate: dict[str, int],
) -> R02V2EvaluatedSelectionCase:
    presented_ids = {item.canonical_candidate_id for item in sealed.selections[0].candidate_scores}
    if set(oracle_utility_by_candidate) != presented_ids:
        raise R02V2SelectionError("oracle evaluation must contain exactly the sealed presented set")
    oracle_best = max(oracle_utility_by_candidate.values())
    outcomes = tuple(
        R02V2ScorerOutcome(
            scorer_id=selection.scorer_id,
            selected_canonical_candidate_id=(selection.selected_canonical_candidate_id),
            oracle_utility_e12=(utility := oracle_utility_by_candidate[selection.selected_canonical_candidate_id]),
            oracle_regret_e12=max(oracle_best - utility, 0),
        )
        for selection in sealed.selections
    )
    body = {
        "schema_version": "r02-overlay-v2-evaluated-selection-case-v1",
        "anonymous_case_sha256": sealed.anonymous_case_sha256,
        "stratum": sealed.stratum,
        "sealed_case_sha256": sealed.sealed_case_sha256,
        "oracle_best_utility_e12": oracle_best,
        "outcomes": outcomes,
    }
    return R02V2EvaluatedSelectionCase(
        **body,
        evaluation_sha256=canonical_sha256(body),
    )


def _weighted_stratum_mean(
    representative: list[int],
    challenge: list[int],
) -> int:
    if not representative or not challenge:
        raise R02V2SelectionError("selection requires both representative and challenge strata")
    return round_ratio_half_even(
        3 * sum(representative) * len(challenge) + sum(challenge) * len(representative),
        4 * len(representative) * len(challenge),
    )


def assert_split_nonoverlap(
    split_memberships: dict[str, set[str]],
) -> None:
    required = {
        "SCHEMA_GENERATOR_DEVELOPMENT",
        "COMPARATOR_SELECTION",
        "HEADROOM_VALIDATION",
        "BLINDED_LLM_PILOT",
        "CONFIRMATORY_LIVE",
    }
    if set(split_memberships) != required:
        raise R02V2SelectionError("all five frozen splits are required")
    owners: dict[str, str] = {}
    for split_name, anonymous_case_sha256s in split_memberships.items():
        for case_sha256 in anonymous_case_sha256s:
            if case_sha256 in owners:
                raise R02V2SelectionError(f"split overlap: {owners[case_sha256]} and {split_name}")
            owners[case_sha256] = split_name


def select_public_scorer(
    cases: tuple[R02V2EvaluatedSelectionCase, ...],
) -> R02V2ScorerSelectionReport:
    if len({case.anonymous_case_sha256 for case in cases}) != len(cases):
        raise R02V2SelectionError("selection cases must be unique")
    utilities: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    regrets: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    fallbacks: dict[str, int] = defaultdict(int)
    for case in cases:
        for outcome in case.outcomes:
            utilities[outcome.scorer_id][case.stratum].append(outcome.oracle_utility_e12)
            regrets[outcome.scorer_id][case.stratum].append(outcome.oracle_regret_e12)
            fallbacks[outcome.scorer_id] += int(outcome.fell_back)
    aggregates: list[R02V2ScorerAggregate] = []
    for config_id in sorted(utilities):
        config = scorer_by_id(config_id)
        aggregates.append(
            R02V2ScorerAggregate(
                scorer_id=config_id,
                weighted_full_frame_utility_e12=_weighted_stratum_mean(
                    utilities[config_id]["REPRESENTATIVE"],
                    utilities[config_id]["CHALLENGE_HEADROOM"],
                ),
                weighted_oracle_regret_e12=_weighted_stratum_mean(
                    regrets[config_id]["REPRESENTATIVE"],
                    regrets[config_id]["CHALLENGE_HEADROOM"],
                ),
                settled_fallback_count=fallbacks[config_id],
                complexity_rank=config.complexity_rank,
                forecast_scale_bps=config.forecast_scale_bps,
            )
        )
    selected = min(
        aggregates,
        key=lambda item: (
            -item.weighted_full_frame_utility_e12,
            item.weighted_oracle_regret_e12,
            item.settled_fallback_count,
            item.complexity_rank,
            item.forecast_scale_bps,
            item.scorer_id,
        ),
    )
    ordered_aggregates = tuple(sorted(aggregates, key=lambda item: item.scorer_id))
    body = {
        "schema_version": "r02-overlay-v2-scorer-selection-report-v1",
        "evaluated_case_sha256s": tuple(case.evaluation_sha256 for case in cases),
        "selected_scorer_id": selected.scorer_id,
        "aggregates": ordered_aggregates,
    }
    return R02V2ScorerSelectionReport(
        **body,
        report_sha256=canonical_sha256(body),
    )


def replay_scorer_selection(
    cases: tuple[R02V2EvaluatedSelectionCase, ...],
    expected: R02V2ScorerSelectionReport,
) -> bool:
    return select_public_scorer(cases) == expected
