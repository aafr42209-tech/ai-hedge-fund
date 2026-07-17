# R02 statistical design draft

Status: **PROVIDER-FREE DRAFT — NO SAMPLE OR TEST FROZEN**

Provider calls authorized: **no**

## 1. Analysis objective

Estimate the utility effect of the complete selective system, not merely the
effect among successful LLM calls. The complete system includes trigger-false
episodes, candidate collapse, schema fallback, and baseline execution.

This design prevents a low trigger rate from producing an apparently successful
conditional result while the system does almost nothing.

## 2. Notation

For fixture `i`:

- `B_i`: deterministic-baseline utility;
- `Y_i`: utility of the portfolio actually executed by the R02 system;
- `D_i = Y_i - B_i`: paired system utility delta;
- `T_i`: frozen trigger indicator;
- `E_i`: at least two distinct, valid candidates exist after deduplication;
- `V_i`: selector response is valid;
- `S_i`: frozen stratum, `REPRESENTATIVE` or `CHALLENGE_HEADROOM`.

When the system executes the baseline, `D_i = 0`, including no-call and
fail-closed fallback cases.

## 3. Primary estimand

The primary estimand is the fixed-stratum-weight paired mean:

```text
theta_system = sum_s w_s * mean(D_i | S_i = s)
```

The target weights `w_s` must be frozen before acquisition. Report both the
weighted estimate and each stratum estimate. Challenge fixtures may improve
power for mechanism testing but cannot silently redefine the target population.

The draft success margin is `delta_min`; its exact value and units are blocking
freeze fields. A zero margin tests any positive improvement. A positive margin
tests practical improvement and is preferred if it can be justified before
outcomes.

## 4. Secondary estimands

Secondary conditional effect:

```text
theta_triggered = mean(D_i | T_i = true and E_i = true)
```

Additional descriptive endpoints:

- raw trigger rate `mean(T_i)` by stratum;
- eligible-opportunity rate `mean(T_i and E_i)`;
- valid-selection rate `mean(V_i | T_i and E_i)`;
- baseline, no-change, and transformed-candidate selection frequencies;
- fail-closed fallback rate;
- per-stratum and candidate-family utility delta;
- provider calls avoided by the trigger.

Secondary endpoints cannot replace the primary system-level estimand. A
hierarchical confirmatory secondary claim is allowed only if its order and
multiplicity rule are frozen and the primary gate passes.

## 5. Sampling frame

Generate and freeze the entire fixture frame provider-free before the first
provider call. Store fixture identity, generation seed, stratum, baseline score,
oracle score, and headroom classification in the sealed frame manifest.

`REPRESENTATIVE` fixtures are drawn without oracle-headroom conditioning.
`CHALLENGE_HEADROOM` fixtures satisfy a frozen oracle-minus-baseline gap. Oracle
classification occurs in a separate provider-free path. Candidate generation
and prompts must be unable to read oracle or headroom fields.

The final plan must freeze:

- sampling distributions and exclusions;
- stratum sample counts and target weights;
- headroom threshold and tie behavior;
- fixture generator and oracle source hashes;
- duplicate and near-duplicate policy.

## 6. Replicates and dependence

The fixture is the analysis unit. Asset decisions within a response are not
independent. Multiple provider responses for one fixture are also not
independent.

If selector replicates are used, freeze the replicate count `R` and aggregate
their executed deltas to one fixture-level value before the primary test. Never
inflate N by treating assets or replicates as independent observations.

R01's 36/36 repeated action-quantity agreement is exploratory motivation for a
small R; it does not eliminate the need to freeze the R02 replicate policy.

## 7. Trigger-rate-aware sample sizing

Sample size must be selected by provider-free simulation over a prespecified
scenario grid. At minimum vary:

- trigger probability by stratum;
- candidate-collapse probability;
- valid-selector probability;
- conditional mean and variance of `D_i`;
- between-fixture variance and, if `R > 1`, within-fixture correlation;
- representative/challenge mixture weights;
- fail-closed rate.

Choose total N and stratum allocation to satisfy both:

1. target power for the primary `theta_system > delta_min` rule under the
   minimum effect of interest; and
2. high probability of at least `M_min` eligible opportunities
   (`sum(T_i and E_i) >= M_min`).

Draft targets for review are at least 80% primary power and at least 90%
probability of meeting `M_min`. These are proposals, not frozen values.

## 8. Low-trigger and candidate-collapse futility

Before looking at utility deltas, apply the frozen opportunity-count rule:

```text
M = sum_i (T_i and E_i)
```

If `M < M_min`, the final label is `INCONCLUSIVE_LOW_TRIGGER`. It can never be
PASS, even if the few selected episodes have positive utility.

The final plan should also freeze a maximum candidate-collapse rate. Exceeding
it may produce `INCONCLUSIVE_CANDIDATE_COLLAPSE` or invalidate the run,
depending on whether collapse reflects the intended system or implementation
drift.

## 9. Proposed primary interval and decision rule

Draft procedure:

1. Compute fixture-level `D_i`.
2. Compute the frozen-weight stratified mean.
3. Resample fixtures within each stratum with a frozen PRNG seed and 10,000
   bootstrap draws.
4. Form a two-sided 95% percentile interval for `theta_system`.

Draft labels:

- `SUPPORTED`: lower bound is greater than `delta_min`, all safety/quality gates
  pass, and `M >= M_min`;
- `NOT_SUPPORTED`: upper bound is at or below `delta_min` with all gates valid;
- `INCONCLUSIVE_EFFECT`: interval crosses `delta_min`;
- `INCONCLUSIVE_LOW_TRIGGER`: opportunity rule fails;
- `INVALID_RUN`: preregistered integrity or execution gate fails.

The bootstrap method, coverage, draw count, `delta_min`, and label precedence
must be confirmed by simulation and frozen. Changing them after outcomes is
prohibited.

## 10. Provider and fallback failures

Recommended conservative policy:

- trigger false or candidate collapse before a provider call: baseline executes,
  `D_i = 0`, no-call artifact required;
- provider attempted but response fails closed: baseline executes, `D_i = 0`,
  attempt remains in the ITT denominator and failure-rate gate;
- exceeding a frozen aggregate failure-rate cap: `INVALID_RUN`, not selective
  deletion of failed fixtures.

The exact failure-rate cap and whether specified transport-wide incidents allow
a full preregistered rerun are blocking decisions.

## 11. Confidence analysis

Confidence is a structural field and exploratory diagnostic by default. R01's
calibration report concludes `NO_THRESHOLD_JUSTIFIED`.

R02 may use confidence operationally only if one of these is frozen before
calls:

- a threshold chosen independently of R01 outcomes;
- a threshold grid evaluated as secondary exploratory analysis on R02;
- a calibration/development split that never reuses calibration fixtures for
  confirmatory evaluation.

No post-hoc threshold may be used to redefine the primary treatment system.

## 12. Safety endpoints

Before acquisition, define hard portfolio validity gates and at least one
downside gate. Candidate safety options include a maximum per-fixture utility
loss, a lower-tail quantile constraint, or noninferiority on risk/turnover.

These gates must be computed for the executed system and cannot be replaced by
average utility alone. Exact margins and multiplicity treatment remain open.

## 13. Required provider-free power package

The next statistical deliverable must contain:

- scenario-grid source and configuration;
- deterministic simulation seed and software hash;
- power and `P(M >= M_min)` surfaces;
- selected N, stratum allocation, weights, `delta_min`, and `M_min`;
- sensitivity to trigger and failure rates;
- frozen analysis script with test vectors;
- machine-readable statistical freeze referenced by the R02 preflight.

That package is analysis preparation only and does not authorize provider use.
