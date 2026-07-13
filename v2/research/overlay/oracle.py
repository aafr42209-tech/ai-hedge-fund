"""Complete-enumeration exact oracle and certificate generation."""

from __future__ import annotations

import hashlib

from .canonical import canonical_json_bytes, canonical_sha256
from .contracts import OracleCertificate, OracleResult, SyntheticEpisode, ValidationReport
from .lattice import iter_candidate_batches
from .scoring import score_episode
from .selection import prefer_maximized_candidate
from .validator import validate_batch


def assert_oracle_bound(
    policy_name: str,
    policy_utility_e12: int,
    oracle: OracleResult,
) -> None:
    """Fail closed if any executable policy exceeds the exact oracle."""

    if policy_utility_e12 > oracle.score.utility_e12:
        raise RuntimeError(f"{policy_name} utility exceeds exact oracle")


def solve_oracle(episode: SyntheticEpisode) -> OracleResult:
    candidate_count = 0
    feasible_count = 0
    best_validation: ValidationReport | None = None
    best_score = None
    minimum_utility: int | None = None
    score_stream = hashlib.sha256()

    for batch in iter_candidate_batches(episode.public):
        candidate_count += 1
        validation = validate_batch(episode.public, batch)
        if not validation.raw_valid:
            continue
        feasible_count += 1
        score = score_episode(episode, validation)
        minimum_utility = score.utility_e12 if minimum_utility is None else min(minimum_utility, score.utility_e12)
        score_stream.update(
            canonical_json_bytes(
                {
                    "final_shares": validation.executable.final_shares,
                    "utility_e12": score.utility_e12,
                }
            )
        )
        score_stream.update(b"\n")
        if prefer_maximized_candidate(
            score.utility_e12,
            validation,
            None if best_score is None else best_score.utility_e12,
            best_validation,
        ):
            best_validation = validation
            best_score = score

    if best_validation is None or best_score is None or minimum_utility is None:
        raise RuntimeError("fixture has no feasible portfolio")

    certificate = OracleCertificate(
        candidate_count=candidate_count,
        feasible_count=feasible_count,
        best_batch_sha256=canonical_sha256(best_validation.executable),
        score_stream_sha256=score_stream.hexdigest(),
        best_utility_e12=best_score.utility_e12,
        minimum_utility_e12=minimum_utility,
        maximum_abs_utility_e12=max(abs(best_score.utility_e12), abs(minimum_utility)),
    )
    return OracleResult(validation=best_validation, score=best_score, certificate=certificate)
