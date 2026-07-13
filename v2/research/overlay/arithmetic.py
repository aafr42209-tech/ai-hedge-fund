"""Exact integer arithmetic used by every authoritative R01 score."""

from __future__ import annotations

UTILITY_SCALE = 10**12
BASIS_POINTS = 10_000
PARTS_PER_MILLION = 1_000_000
COVARIANCE_BP2_SCALE = BASIS_POINTS**2


def round_ratio_half_even(numerator: int, denominator: int) -> int:
    """Return numerator / denominator rounded to nearest, ties to even.

    The implementation is integer-only and deliberately independent of
    Python's floating-point and Decimal contexts.
    """

    if isinstance(numerator, bool) or not isinstance(numerator, int):
        raise TypeError("numerator must be an integer")
    if isinstance(denominator, bool) or not isinstance(denominator, int):
        raise TypeError("denominator must be an integer")
    if denominator <= 0:
        raise ValueError("denominator must be positive")

    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2 == 1):
        quotient += 1
    return sign * quotient


def ceil_ratio(numerator: int, denominator: int) -> int:
    """Return ceil(numerator / denominator) for nonnegative integers."""

    if numerator < 0:
        raise ValueError("numerator must be nonnegative")
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (numerator + denominator - 1) // denominator


def mean_int(values: tuple[int, ...] | list[int]) -> int:
    """Authoritative R01 integer mean."""

    if not values:
        raise ValueError("cannot take the mean of an empty sequence")
    return round_ratio_half_even(sum(values), len(values))
