"""Frozen R03 G1 zero-cost, time-decoupled sorting relaxation."""

from __future__ import annotations

import hashlib
import math

import numpy as np

from v2.research.overlay.canonical import canonical_sha256

from .r03_contracts import (
    DELTA_STAR_E12,
    mean_e12,
    R03BoundCertificate,
    R03ContractError,
    R03GateLabel,
    R03GateResult,
)
from .r03_frames import construct_buffered_book, net_book_utility_e12, R03PortfolioBook


class R03HeadroomError(R03ContractError):
    pass


def _certificate(
    decision_id: str,
    valid_names_sha256: str,
    order_sha256: str,
    longs: tuple[str, ...],
    shorts: tuple[str, ...],
    bound_e12: int,
) -> R03BoundCertificate:
    unsigned = {
        "schema_version": "r03-g1-bound-certificate-v1",
        "contract_name": "G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1",
        "decision_id": decision_id,
        "valid_name_set_sha256": valid_names_sha256,
        "sorted_return_order_sha256": order_sha256,
        "long_tickers": longs,
        "short_tickers": shorts,
        "bound_e12": bound_e12,
    }
    return R03BoundCertificate(**unsigned, certificate_sha256=canonical_sha256(unsigned))


def make_bound_certificate(decision_id: str, realized_returns_e12: dict[str, int]) -> R03BoundCertificate:
    if any(not isinstance(value, int) for value in realized_returns_e12.values()):
        raise R03HeadroomError("G1 returns must be e12 integers")
    valid_names = sorted(realized_returns_e12)
    valid_digest = canonical_sha256(valid_names)
    order = sorted(valid_names, key=lambda ticker: (-realized_returns_e12[ticker], ticker))
    order_digest = canonical_sha256([{"ticker": t, "return_e12": realized_returns_e12[t]} for t in order])
    if len(order) < 20:
        return _certificate(decision_id, valid_digest, order_digest, (), (), 0)
    longs, shorts = tuple(order[:10]), tuple(reversed(order[-10:]))
    bound = mean_e12([realized_returns_e12[t] for t in longs]) - mean_e12([realized_returns_e12[t] for t in shorts])
    return _certificate(decision_id, valid_digest, order_digest, longs, shorts, bound)


def replay_bound_certificate(certificate: R03BoundCertificate, realized_returns_e12: dict[str, int]) -> bool:
    expected = make_bound_certificate(certificate.decision_id, realized_returns_e12)
    if expected != certificate:
        raise R03HeadroomError("G1 certificate replay mismatch")
    return True


def _domain_seed(seed_sha256: str, label: str) -> int:
    if len(seed_sha256) != 64:
        raise R03HeadroomError("seed must be SHA-256 hex")
    return int.from_bytes(hashlib.sha256(bytes.fromhex(seed_sha256) + label.encode("utf-8")).digest()[:16], "big")


def stationary_bootstrap_means_e12(
    values_e12: tuple[int, ...],
    *,
    seed_sha256: str,
    label: str,
    block_length: int = 10,
    resamples: int = 10_000,
) -> tuple[int, ...]:
    if not values_e12 or block_length <= 0 or resamples <= 0:
        raise R03HeadroomError("invalid stationary bootstrap inputs")
    values = np.asarray(values_e12, dtype=np.int64)
    rng = np.random.Generator(np.random.PCG64(_domain_seed(seed_sha256, label)))
    n = len(values)
    result: list[int] = []
    restart = 1.0 / block_length
    for _ in range(resamples):
        indices = np.empty(n, dtype=np.int64)
        indices[0] = rng.integers(0, n)
        for index in range(1, n):
            indices[index] = rng.integers(0, n) if rng.random() < restart else (indices[index - 1] + 1) % n
        result.append(mean_e12(values[indices].tolist()))
    return tuple(result)


def evaluate_g1(
    differences_e12: tuple[int, ...],
    *,
    seed_sha256: str,
    resamples: int = 10_000,
) -> R03GateResult:
    input_sha = canonical_sha256({"gate": "G1", "differences_e12": differences_e12, "resamples": resamples})
    if not differences_e12:
        unsigned = {
            "gate": "G1",
            "label": R03GateLabel.G1_INVALID,
            "point_estimate_e12": None,
            "upper_95_e12": None,
            "lower_95_e12": None,
            "seed_sha256": seed_sha256,
            "input_sha256": input_sha,
        }
        return R03GateResult(**unsigned, result_sha256=canonical_sha256(unsigned))
    draws = sorted(stationary_bootstrap_means_e12(differences_e12, seed_sha256=seed_sha256, label="R03_G1", resamples=resamples))
    upper = draws[max(0, math.ceil(0.95 * len(draws)) - 1)]
    label = R03GateLabel.G1_STOP if upper <= DELTA_STAR_E12 else R03GateLabel.G1_CONTINUE
    unsigned = {
        "gate": "G1",
        "label": label,
        "point_estimate_e12": mean_e12(list(differences_e12)),
        "upper_95_e12": upper,
        "lower_95_e12": draws[max(0, math.ceil(0.05 * len(draws)) - 1)],
        "seed_sha256": seed_sha256,
        "input_sha256": input_sha,
    }
    return R03GateResult(**unsigned, result_sha256=canonical_sha256(unsigned))


def greedy_feasible_lower_bracket_e12(
    realized_by_decision: tuple[dict[str, int], ...],
    *,
    cost_bps_per_side: int,
) -> int:
    previous: R03PortfolioBook | None = None
    total = 0
    for returns in realized_by_decision:
        book = construct_buffered_book({ticker: float(value) for ticker, value in returns.items()}, previous)
        total += net_book_utility_e12(book, returns, previous, cost_bps_per_side)
        previous = book
    return total
