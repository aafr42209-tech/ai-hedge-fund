"""Complete-enumeration exact oracle and certificate generation."""

from __future__ import annotations

import hashlib

from .canonical import canonical_json_bytes, canonical_sha256
from .contracts import OracleCertificate, OracleResult, SyntheticEpisode, ValidationReport
from .lattice import iter_candidate_batches
from .scoring import score_episode
from .validator import validate_batch


def _tie_key(validation: ValidationReport) -> tuple[int, int, tuple[int, ...]]:
    return (
        validation.cost_ledger.total_cost_cents,
        validation.cost_ledger.total_notional_cents,
        tuple(validation.executable.final_shares[asset_id] for asset_id in sorted(validation.executable.final_shares)),
    )


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
        if best_score is None or score.utility_e12 > best_score.utility_e12 or (score.utility_e12 == best_score.utility_e12 and best_validation is not None and _tie_key(validation) < _tie_key(best_validation)):
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
