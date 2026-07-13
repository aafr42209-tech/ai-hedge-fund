"""Canonical candidate ordering shared by oracle and deterministic baselines."""

from __future__ import annotations

from .contracts import ASSET_IDS, ValidationReport


def candidate_tie_key(
    validation: ValidationReport,
) -> tuple[int, int, tuple[int, ...]]:
    """Order equal-objective candidates by cost, turnover, then canonical shares."""

    return (
        validation.cost_ledger.total_cost_cents,
        validation.cost_ledger.total_notional_cents,
        tuple(validation.executable.final_shares[asset_id] for asset_id in ASSET_IDS),
    )


def prefer_maximized_candidate(
    value: int,
    validation: ValidationReport,
    best_value: int | None,
    best_validation: ValidationReport | None,
) -> bool:
    if best_value is None:
        return True
    if value != best_value:
        return value > best_value
    if best_validation is None:
        raise RuntimeError("best candidate value lacks its validation record")
    return candidate_tie_key(validation) < candidate_tie_key(best_validation)


def prefer_minimized_candidate(
    value: int,
    validation: ValidationReport,
    best_value: int | None,
    best_validation: ValidationReport | None,
) -> bool:
    if best_value is None:
        return True
    if value != best_value:
        return value < best_value
    if best_validation is None:
        raise RuntimeError("best candidate value lacks its validation record")
    return candidate_tie_key(validation) < candidate_tie_key(best_validation)
