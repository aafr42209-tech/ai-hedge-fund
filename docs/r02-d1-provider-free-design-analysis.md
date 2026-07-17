# R02 D1 provider-free design analysis

Status: **EXPLORATORY DESIGN INPUT — NOT R02 OUTCOME EVIDENCE**

Provider calls: **0**

## Data boundary

The analysis reuses the sealed 40-case R01 development frame without modifying
it. This is allowed exploratory design use. No R01 fixture may become an R02
confirmatory observation; R02 requires newly generated, separately frozen
frames.

## Candidate-family check

All four proposed raw candidates validated on all 40 fixtures. After canonical
deduplication, K was 1 for two fixtures, 2 for three, 3 for seven, and 4 for 28.
The half-scale candidate added distinct content in 31 cases; the cost-drop
candidate added a new fourth role in 32 cases.

This confirms the integer-lot rules are executable under the current synthetic
contract. It does not substitute for D2 production contracts or negative tests.

## Trigger selection

An initial rule based on total portfolio cost or concentration utilization
triggered 12/40 cases, but only three had any candidate better than baseline.
It also opened concentration cases without a dedicated concentration transform.
That rule was rejected before freeze.

The selected rule uses the maximum effective cost of an actual baseline trade:

```text
ceil(total_cost_cents * 10000 / notional_cents) >= 50
```

It triggered 5/40 cases, all in the high-transaction-cost regime. Their values
ranged from 62 to 119 bps. The largest nontrigger traded value was 23 bps, so 50
bps lies inside a wide observed gap rather than on an individual outcome.

This is still a post-hoc design choice: every integer threshold from 24 through
62 selects the same five observed cases. The round value 50 is frozen as an
interior representative of that equivalence band. It requires new-frame
validation and cannot be retuned after those fixtures are observed.

## Candidate headroom diagnostic

Among the five triggered cases, a generated alternative beat baseline in four;
one case correctly required selecting baseline. The oracle-selector upper-bound
delta averaged `268,383,759 e12` with sample SD `261,774,908 e12`.

This is deliberately labeled an upper bound. It uses hidden true utility after
candidate bytes are fixed and says nothing about the LLM's achievable effect.
It just verifies that the frozen selector task contains both intervention and
refusal cases.

## N and M_min recommendation

Recommended for the later statistical freeze, not frozen here:

- total N: 160;
- representative: 120 with target weight 0.75;
- headroom-positive challenge: 40 with target weight 0.25;
- `M_min`: 46 eligible trigger opportunities.

Challenge admission requires trigger true, `K >= 2`, and positive candidate-set
headroom, all determined provider-free before acquisition. With representative
trigger rate 8%, the exact binomial probability of `M >= 46` is 92.47%; at the
observed 12.5% design rate it is 99.83%.

Under a conservative normal approximation with 5% selector failure and
conditional standardized effect 0.4, primary power ranges from 83.1% at an 8%
representative trigger rate to 86.5% at 12.5%.

These figures do not complete the statistical freeze. The final package still
needs utility-unit `delta_min`, a stratified bootstrap simulation matching the
registered estimator, a provider budget, and new-frame trigger-rate
verification. The 50-bps trigger may not be retuned after that new frame is
observed; a material rate miss leads to redesign under a new identity.
