# R02 D1 candidate-generator and trigger freeze candidate

Status: **PROVIDER-FREE FREEZE CANDIDATE — INDEPENDENT REVIEW REQUIRED**

Provider calls: **0**

Production implementation and R02 execution: **not authorized**

## Decision

R02 D1 narrows the first selector experiment to transaction-cost exceptions.
The exact proposal combines Option A with one Option B transform:

1. exact deterministic baseline;
2. no change;
3. half of every baseline trade in integer lots;
4. baseline with its single highest-total-cost trade removed.

This scope does not claim to solve signal conflict or concentration exceptions.
Those candidate families are deferred rather than mixed into the first freeze.

## Exact trigger

Run `primary_deterministic` and its existing validator. For each non-hold cost
line compute:

```text
effective_cost_bps = ceil(total_cost_cents * 10000 / notional_cents)
```

Trigger exactly when at least one line exists and the maximum line value is at
least 50 bps. Commission, half-spread, and slippage are therefore all included.

The threshold is an explicitly post-hoc R01 design choice, not R02 evidence. In
the 40-case provider-free design frame, other traded cases ended at 23 bps while
the five traded high-cost cases began at 62 bps. Every integer threshold from 24
through 62 selects the same five cases; 50 bps is a round interior value, not an
empirically unique optimum. R02 must use newly generated fixtures and may not
retune this threshold after observing them.

## Exact candidates

`BASELINE` copies the deterministic baseline action and quantity.

`NO_CHANGE` is `hold/0` for A0 through A5.

`HALF_BASELINE_DELTA` divides each baseline trade's integer lot count by two
with floor-toward-zero rounding. A zero result becomes `hold/0`.

`DROP_MAX_COST_TRADE` removes the baseline cost-ledger line with greatest
`total_cost_cents`; a tie selects the lexicographically smallest asset ID.

All four raw batches must validate before deduplication. No repair is allowed.
Deduplication follows the listed role order, preserving the first role and
recording later roles as aliases. The resulting K is between one and four. A
provider call requires trigger true and `K >= 2`.

## Canonical identity and blinding

Candidate identity is SHA-256 over the frozen compact JSON payload containing
only `schema_version`, asset action, and quantity. Semantic roles are retained
in audit artifacts but hidden from the selector.

Presentation order uses HMAC sort keys, not an implementation-dependent PRNG.
The exact byte formula and root seed are in the machine freeze. Presented IDs
are `P00`, `P01`, and so on. Replay must recover the complete map.

## Information barrier

Trigger and candidate generation may read only the public fixture and
deterministic-baseline artifacts. They cannot read hidden expected returns,
oracle output, headroom, future returns, or provider output.

Challenge-stratum admission may inspect true candidate utility only after
trigger and candidate bytes are immutable. That admission record is sealed in
a separate frame-building path and is never exposed to the selector.

## Why this is still pending

This document and its JSON companion specify behavior but do not implement it.
R2-D1 becomes accepted only after independent hash/test-vector review and user
acceptance. R2-D2 would separately authorize production contracts, persistence,
replay, negative tests, and zero-call preflight.
