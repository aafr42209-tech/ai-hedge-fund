# R02 deterministic candidate-generator options

Status: **PROVIDER-FREE DESIGN DRAFT — NOT FROZEN**

Implementation authorized: **no**

Provider calls authorized: **no**

## Role of the generator

The candidate generator, not the LLM, constructs executable portfolios. It is
a deterministic algorithm owned by the research implementation. The LLM may
only select one presented `candidate_id`.

Every candidate set must include the exact deterministic baseline. The
no-change/current-portfolio candidate is also mandatory whenever it differs
from the baseline. A separate veto field is unnecessary: selecting the
baseline or no-change candidate supplies the safe refusal behavior.

The generator may use only data available to the deterministic baseline and
the frozen trigger. Oracle output, future returns, oracle-baseline headroom,
and post-outcome labels are forbidden inputs.

## Common invariants

All design options must satisfy these rules:

1. Generate integer-lot, validator-valid executable batches.
2. Include `BASELINE` exactly, byte-for-byte equivalent after canonicalization.
3. Include `NO_CHANGE` when distinct; it executes current holdings with zero
   trade delta.
4. Materialize every scale-down as a concrete candidate. No continuous
   `scale_down` field is exposed to the LLM.
5. Deduplicate canonical executable batches before anonymization.
6. Require at least two distinct candidates before a provider call; otherwise
   execute the baseline and record a no-call candidate-collapse reason.
7. Derive candidate IDs from canonical content, not semantic labels.
8. Deterministically permute presentation order from fixture content hash,
   overlay-spec hash, and a frozen seed label.
9. Hide canonical role labels such as `BASELINE` from the selector.
10. Persist generator source hash, configuration hash, candidate-set hash,
    original order, presented order, and permutation map.

## Option A — minimal intervention

Candidate family:

- exact baseline;
- no-change/current portfolio;
- 50% baseline-delta candidate, with each signed trade delta transformed as
  `sign(delta_lots) * floor(abs(delta_lots) / 2)`;
- 25% baseline-delta candidate using the same rule with divisor four.

Advantages: smallest implementation surface, transparent integer arithmetic,
and direct control over unnecessary turnover. Weakness: it cannot change trade
direction or resolve a baseline error caused by nonlinear signal interaction.

## Option B — risk-control transforms

Candidate family:

- exact baseline;
- no-change/current portfolio;
- turnover-reduced baseline under a frozen transaction-cost or traded-notional
  cap;
- concentration-reduced baseline under a frozen post-trade concentration cap.

The transform must use a frozen deterministic priority rule, including all
tie-breakers. For example, turnover reduction may shrink or remove trades in
descending estimated-cost order, while concentration reduction may shrink the
largest post-trade position first. Exact caps and tie-breakers remain blocking
draft decisions.

Advantages: directly targets R01's unfavorable high-cost and concentration
regimes. Weakness: more implementation and proof burden; a poorly specified
priority rule can silently become a second portfolio optimizer.

## Option C — exception-specific alternatives

Candidate family:

- exact baseline;
- no-change/current portfolio;
- one or more deterministic alternatives selected by the frozen trigger reason,
  such as signal-conflict, transaction-cost, or concentration transforms.

Advantages: expressive and call-efficient. Weakness: the trigger and generator
can become jointly overfit to R01. Every trigger-specific transform would need
new-data validation and a strict prohibition on oracle-derived design tuning.

## Recommended starting draft

Start provider-free implementation review with **Option A plus at most one
Option B risk-control transform**. This yields a small candidate set with exact
baseline and no-change protection while testing whether constrained selection
can avoid damaging interventions.

Recommended initial cardinality after deduplication: `2 <= K <= 5`. This is a
draft recommendation, not a freeze. Exact transforms, caps, tie-breakers, and K
must be approved with a candidate-generator specification hash before any R02
provider call.

## Blocking decisions before implementation freeze

- chosen option and exact candidate family;
- integer rounding rule for every transform;
- validation and repair policy — recommended: reject, never repair silently;
- deterministic tie-breakers;
- candidate cardinality bounds and collapse behavior;
- generator source/config hash contract;
- trigger-to-transform mapping, if any;
- proof that oracle and outcome data cannot enter generator inputs.
