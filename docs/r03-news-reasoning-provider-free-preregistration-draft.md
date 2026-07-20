# R03 news-driven LLM reasoning — provider-free preregistration draft

Status: **P5 ACCEPTED WITH NONBLOCKING FINDINGS; NONBLOCKING CORRECTIONS APPLIED; PROVIDER-FREE RESEALED; NO EXECUTION AUTHORITY**
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
article-to-frame aggregation are frozen for review in §14. Gate execution remains
blocked until this corrected set is resealed and the implementation identities,
hashes, seeds, and verifier manifests in §7 are pinned.

Required chronological topology:

`development -> calibration -> one contiguous OOS evaluation, opened once`

Exact decision dates are frozen for review:

- development: 2016-01-04 through 2020-12-23; purge the final five 2020
  sessions (2020-12-24 and 2020-12-28 through 2020-12-31);
- calibration: 2021-01-04 through 2022-12-22; purge 2022-12-23 and 2022-12-27
  through 2022-12-30;
- single OOS: 2023-01-03 through 2025-12-23, opened once;
- later 2025 decisions lack an in-sample t+5 label and are excluded.

Only matured t+5 labels may enter a fit or monthly refit. Because the corpus and
modern-model cutoff overlap are historical, OOS denotes procedural separation,
not confirmatory validity.

## 4. Information sets

- T0 receives frozen non-news public features available at decision time.
- T1 receives T0 plus frozen FinBERT score aggregates.
- T2 and T3 receive byte-identical canonical raw-news payloads after
  `available_at`, plus the same T0 state.
- T2/T3 may not receive forward returns, oracle utility, future membership,
  post-decision updates, hidden source labels, or evaluation outcomes.

The full provider-free census found 247,976 eligible unique articles and 301,541
ticker-article events. Eligible coverage is headline 100%, summary 29.33%, body
50.90%, and headline-only 49.10%. The earlier 60-page estimate is superseded by
`docs/r03-news-reasoning-provider-free-coverage-audit.json`.

Canonical missing-text policy:

- headline is required;
- `summary` and `content` remain separate canonical fields;
- missing values are explicit nulls with presence flags;
- body-missing articles are not excluded from the primary full-frame ITT;
- T2 and T3 receive byte-identical values, nulls, ordering, and flags;
- body-present/body-missing effects are secondary strata only;
- the coverage-audit hash is frozen now; final implementation schema/model hashes
  remain prerequisites to gate execution.

## 5. T2 and cheap-text gate lock

One prespecified non-LLM model family serves both futility gate 2 and T2. P5
freezes the hash/TF-IDF/ridge family, grids, clipping, and monthly refit protocol
in §14 and the charter §12.

All fitting and hyperparameter choice occurs inside nested chronological training
windows. If the cheap-text gate does not pause, its exact fitted protocol becomes
T2. If it pauses, either user branch still preserves the same fitted T2 model ID;
no post-gate replacement or reselection is allowed.

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
paired time blocks. If the one-sided upper confidence bound is at or below
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

This analytical MDE is a diagnostic cross-check only. The simulation grid and
all-cell decision rule in §14.4 operationalize and govern G3; the formula cannot
override a failing §14.4 cell.

## 7. P5 freezes and remaining implementation pins

P5 freezes for independent review:

- `delta_star = 0.0005` net h=5 utility (5 bp);
- one-sided `alpha = 0.05`, power `0.80`, stationary block 10, 10,000 resamples;
- transaction-cost cells 5/10/15 bp per side, base 10;
- decision cutoff, h=5, T0/T1/T2 specifications, action constraints, splits,
  payload budgets, gate precedence, and labels in §14.

Execution remains forbidden until later implementation pins the canonical schema
hash, code/library identities, training-frame hashes, seeds, fitted T0/T1/T2
model IDs, and negative-test/zero-call manifests.

The implementation verifier must independently recompute the pinned payload
retention rates from the read-only raw source under the exact calendar and
canonicalization rules. Negative tests must fail closed after perturbing at least
the article byte cap, ticker-session byte cap, article ordering, early-close
cutoff, or duplicate-selection rule. It may report counts and hashes only, never
raw article text.

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

## 14. P5 frozen specification for independent review

### 14.1 Clock, news frame, and outcome

- `decision(t) = min(15:30 America/New_York, actual close - 30 minutes)`.
- Article window: `(decision(t) - 72h, decision(t)]`.
- `available_at = max(created_at, updated_at)`.
- One version/article: maximum available_at; exact tie uses lexicographic maximum
  `(updated_at, input_text_sha256)`.
- Eligibility: headline present, 1–5 distinct source symbols, at least one frozen-
  universe symbol; apply identically to every intersecting universe ticker.
- Outcome: sector-relative split-adjusted close-to-close h=5 return.
- Price/risk inputs stop at t-1. Five h=5 phase books are evaluated.

### 14.2 Canonical equal-information payload

Strings use UTF-8, NFC, LF newlines, and no NUL; case and HTML remain unchanged.
Ordered fields are `article_id, available_at, symbols, source, headline, summary,
content, summary_present, content_present, content_truncated`. Null summary/body
is explicit. Sort articles by available_at descending, article_id ascending.

Headline is preserved before summary and body. Text budgets are 32,768 bytes per
article and 131,072 bytes per ticker-session; truncation takes the largest valid
UTF-8 body prefix. The final includable article may be body-truncated; later
articles are omitted and counted. T2/T3 canonical bytes and flags must match.

Coverage evidence: 247,976 eligible unique articles, 301,541 ticker-events,
50.90% body present, 29.33% summary present, 49.10% headline-only. The selected
budget fully preserves 150,394/151,820 news-positive frames (99.06%), retains
695,948/702,489 article appearances (99.07%), and retains
1,435,742,878/1,585,976,846 text bytes (90.53%), using round-half-even to two
decimal places. These N1 expectations are governed by
`r03-news-reasoning-data-check-amendment-lineage.json`, which supersedes the
P5-era 97.03% article-cap-only calculation without modifying the P5 artifact.

### 14.3 T0/T1/T2 and actions

T0 factors through t-1: sector-relative log return 5/20/60, volatility 20/60,
downside semideviation 20, sector beta 60, mean log dollar volume 20, volume
shock 5-versus-20, and missing flags. Same-date processing is sector then
universe median imputation, followed by 1/99 clipping, sector demeaning, and
z-score.

T0 is ridge on h=5 sector-relative return with alpha `{0.1,1,10,100}`. T1 adds
only frozen `sentiment_mean_3d` plus availability; missing sentiment is score 0
with availability 0. T2 adds a residual text model:

- hashing word 1–2 grams, 2^18 features, lowercase, no alternate sign;
- training-only smoothed sublinear TF-IDF with L2 norm;
- deterministic LSQR ridge alpha `{1,10,100,1000}`, tolerance 1e-6, at most
  10,000 iterations;
- prediction clipping at training-window 1/99 percentiles;
- monthly expanding refit using matured labels only.

At implementation time the T2 model ID must also bind exact Python, NumPy,
SciPy, and scikit-learn package identifiers and versions; the concrete
`HashingVectorizer`, `TfidfTransformer`, and ridge implementation identifiers;
and any solver/BLAS identity that can change fitted output.

Development rolling-origin folds end in 2017/2018/2019/2020. Highest worst-fold
net utility wins; larger alpha breaks ties. Calibration and OOS cannot reselect.

All tiers use the same buffered long-short constructor: enter top/bottom 10,
retain within top/bottom 20, score-descending/ticker-ascending ties, equal leg
weights, gross 1 per leg, net 0. Fewer than 20 valid names means no trade.

### 14.4 Utility and statistical rules

Period utility is gross long-short spread minus transaction cost and, for T3
when later authorized, measured provider cost converted at USD 1,000,000
reference capital. Transaction cost is 10 bp/side at base and 5/15 bp/side in
sensitivity cells. First establishment turnover is charged fully. Late/unsettled
T3 at 15:50 ET fails closed to T2.

`delta_star = 0.0005` net h=5 return. One-sided alpha is 0.05; power is 0.80.
Stationary block bootstrap uses block 10, 10,000 resamples, and a domain-separated
outcome-independent PCG64 seed. Worst included cost cell governs.

Gate statistics and precedence:

1. G1 calibration `U_clairvoyant_feasible - U_T0`; upper 95% bound <=
   delta_star → `STOP_NO_ECONOMIC_HEADROOM`.
2. G2 calibration `U_T2 - U_T0`; upper 95% bound <= delta_star →
   `PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION`.
3. User stop after G2 → `STOP_BUDGET_FUTILITY_USER_RATIFIED`.
4. User continue after G2 → `CONTINUE_AFTER_G2_PAUSE_USER_RATIFIED`; T2 model
   ID remains fixed and this label does not authorize provider use.
5. G3 uses calibration `D_proxy = U_T2 - U_T0`. Stationary block resamples have
   the planned 747-decision OOS length. Cross SD multipliers `{1,1.5,2}` with
   fail-closed rates `{0,0.05}`; test ITT effect
   `delta_star * (1 - fail_rate)` in every cell over 10,000 seeded resamples.
   Any cell below 80% power → `STOP_UNDERPOWERED` or extend the prospective
   window before provider use.

No gate pass is efficacy evidence. G2 pause/stop is budget governance, not a
claim that LLM narrative reasoning is incapable.
