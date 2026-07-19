# R03 news-driven LLM reasoning — provider-free preregistration draft

Status: **DRAFT; NOT ACCEPTED; NO EXECUTION AUTHORITY**  
Phase: R03  
Created: 2026-07-19

## 1. Research question

Given identical point-in-time raw news and identical non-news public state, does
T3 LLM reasoning improve full-frame after-cost portfolio utility over frozen T2
non-LLM text modeling?

## 2. Hypotheses

Primary null:

`H0: E[U_T3 - U_T2] <= delta_star`

Primary promotion requires the one-sided lower confidence bound for the paired
full-frame ITT contrast to exceed `delta_star` under every governing cost/latency
sensitivity cell. A positive point estimate or rejection against zero alone is
insufficient.

Secondary contrasts are `T1 - T0` and `T2 - T1`. No secondary result rescues a
failed primary result.

## 3. Units and frame

- Decision unit: a frozen portfolio decision timestamp, not an article.
- Inference series: paired period-level net-utility differences.
- Article count is never used as the independent sample size.
- Overlapping forward horizons, shared dates, issuers, and duplicate stories are
  handled through date-level aggregation and dependence-respecting blocks.
- Full-frame ITT includes no-news periods, abstentions, parse failures, timeouts,
  and unavailable model results. T3 failures execute T2.

Exact decision clock, horizon, rebalance schedule, exposure constraints, and
article-to-frame aggregation remain `PENDING_REVIEW` and block gate execution.

Required chronological topology:

`development -> calibration -> one contiguous OOS evaluation, opened once`

Exact dates, embargo, and purge remain pending the provider-free coverage
census. They must be frozen before any text/return model fitting. Because the
corpus and modern-model cutoff overlap are historical, the OOS label denotes
procedural separation, not confirmatory validity.

## 4. Information sets

- T0 receives frozen non-news public features available at decision time.
- T1 receives T0 plus frozen FinBERT score aggregates.
- T2 and T3 receive byte-identical canonical raw-news payloads after
  `available_at`, plus the same T0 state.
- T2/T3 may not receive forward returns, oracle utility, future membership,
  post-decision updates, hidden source labels, or evaluation outcomes.

Preliminary independent-review sample: 60 random pages / 2,810 articles yielded
body content in 68.1%, headline in 100%, and summary in 36.6%; non-empty body
median was approximately 4.3 KB. These are sample estimates, not a census.

Canonical missing-text policy:

- headline is required;
- `summary` and `content` remain separate canonical fields;
- missing values are explicit nulls with presence flags;
- body-missing articles are not excluded from the primary full-frame ITT;
- T2 and T3 receive byte-identical values, nulls, ordering, and flags;
- body-present/body-missing effects are secondary strata only;
- a full-corpus provider-free census and the final payload schema/hash must be
  frozen before gate execution.

## 5. T2 and cheap-text gate lock

One prespecified non-LLM model family serves both futility gate 2 and T2. The
initial candidate is a deterministic hashed bag-of-words representation with a
regularized linear residual-utility model. Exact tokenizer, hash dimension,
n-grams, regularization grid, loss, clipping, calibration, and abstention must be
frozen after provider-free schema/coverage review and before outcome evaluation.

All fitting and hyperparameter choice occurs inside nested chronological training
windows. If the cheap-text gate does not stop, its exact fitted protocol becomes
T2; no post-gate model replacement is allowed.

## 6. Triple futility gate

### G1 — constrained clairvoyant ceiling

Let `B0` be the best preregistered non-news deterministic baseline, selected
without evaluation leakage. Compute:

`H_clairvoyant = U_clairvoyant_feasible - U_B0`

under the exact action, exposure, turnover, liquidity, cost, and latency
constraints. Absolute clairvoyant utility is not compared with `delta_star`.
This is a fail-only ceiling. If the preregistered population upper bound for
`H_clairvoyant` is at or below `delta_star`, label
`STOP_NO_ECONOMIC_HEADROOM`.

### G2 — cheap-text learnability

Evaluate T2 on baseline-residual utility using strict nested walk-forward and
paired time blocks. If the one-sided upper confidence bound is below
`delta_star`, label `PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION` and
spend no provider budget. Termination requires explicit user ratification; if
ratified, record `STOP_BUDGET_FUTILITY_USER_RATIFIED`.

Failure to pause is not proof that T3 contains signal. Pausing or user-ratified
termination is not evidence that a narrative-capable T3 is unable to add value;
G2 is an economic/governance decision under limited provider budget, not a
validity theorem about LLM capability.

### G3 — power

Estimate the paired contrast standard error using a frozen HAC or block-bootstrap
rule with block length no shorter than the maximum overlapping outcome horizon.

`MDE = (z_(1-alpha) + z_(power)) * SE_paired`

If `MDE > delta_star`, label `STOP_UNDERPOWERED` or extend the prospective
window before any provider call.

## 7. Required freezes

The following values are unresolved and all gate execution is forbidden until
they are accepted and hash-bound:

- `delta_star` and utility units;
- one-sided `alpha` and target power;
- cost/latency schedule and sensitivity grid;
- decision horizon and block/HAC rule;
- T0 factor set and candidate/action constraints;
- T2 model specification and nested tuning grid;
- split dates and embargo/purge rule;
- full-corpus text-coverage census, canonical missing-text schema/hash,
  duplicate-story, multi-ticker, and update handling;
- promotion precedence and exact normalized labels.

## 8. Historical and prospective separation

All 2016–2025 results are retrospective exploratory evidence. They may stop the
program for futility but cannot establish a confirmatory T3 claim with a modern
model whose training cutoff may overlap the sample.

A confirmatory T3 run requires either:

1. a documented model training cutoff strictly before the locked evaluation
   window plus a point-in-time universe; or
2. a model pin followed by prospective data collection and a universe fixed at
   each decision time.

## 9. Multiplicity and researcher degrees of freedom

- One primary contrast and one primary utility definition.
- A finite preregistered sensitivity grid with worst-cell governance.
- No choosing the best horizon, cost cell, prompt, model, or text representation
  after evaluation outcomes are visible.
- Any exploratory alternatives are labelled and cannot alter the frozen primary
  verdict.
- No retry, replacement, or selective omission of T3 failures.

## 10. Data and provider boundary

- Read FinGPT raw pages in place; never copy them into this repository.
- Never place article text in tracked outputs, logs, fixtures, or test vectors.
- External-provider transmission is forbidden pending explicit written/legal
  clearance and a separately accepted provider-data contract.
- This preregistration authorizes no implementation, frame materialization,
  provider call, LIVE run, commit, or push.

## 11. Dependency on overlay-v2

R03 design review may proceed now. R03 implementation planning must bind to the
sealed overlay-v2 I0–I5 contracts, canonicalization, grounding, replay, split/
seed, power, status, and zero-call machinery. It must explicitly document every
real-data deviation, especially replacement of the computable-oracle headroom
gate.

## 12. Review exit

Acceptance requires exact formulas, values, schemas, split policy, source hashes,
negative tests, and normalized verdict precedence in a later revision. Until
then this file is a design scaffold only.

## 13. First review disposition

Accepted into this draft:

- F1 sampled content coverage and explicit missing-text/full-frame rules;
- F2 G2 as a user-ratified provider-budget pause rather than a validity stop;
- F3 G1 as incremental clairvoyant headroom over `B0`;
- F4 mandatory development → calibration → one contiguous, one-open OOS
  topology.

Phase ID R03 and read-only, in-place FinGPT reuse were explicitly user-ratified
on 2026-07-19. No implementation, gate run, provider call, commit, or push is
authorized by that ratification.
