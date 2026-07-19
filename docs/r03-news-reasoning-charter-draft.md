# R03 news-driven LLM reasoning — research charter draft

Status: **P5 ACCEPTED WITH NONBLOCKING FINDINGS; NONBLOCKING CORRECTIONS APPLIED; PROVIDER-FREE RESEALED**
Phase: R03  
Created: 2026-07-19  
Execution authority: provider-free design only

## 1. Purpose

Test whether an LLM reasoning over point-in-time news narrative adds net
portfolio utility beyond a frozen non-LLM model that receives the same article
text. The research must distinguish raw-text access from reasoning method and
must stop before provider calls when economically meaningful success is not
feasible or statistically identifiable.

## 2. Prior evidence and claim boundary

- R02 D3/D4 established a redundant-selector null under an information-poor
  selector design; it did not test news reasoning.
- FinGPT established no promotion basis for a fixed FinBERT sentiment factor and
  significant after-cost inferiority for its tested construction; it did not
  test narrative reasoning.
- R03 therefore begins as a new research line. Neither prior null is evidence
  that R03 must fail or succeed.

## 3. Tier structure and estimands

- **T0:** frozen non-news price/risk/cost baseline.
- **T1:** T0 plus frozen FinBERT sentiment.
- **T2:** T0 plus a frozen non-LLM text model over the same raw text available to
  T3. The cheap-text futility model and T2 are one implementation.
- **T3:** T0 plus LLM reasoning over the same raw text.

Primary estimand: full-frame walk-forward ITT net-utility contrast `T3 - T2`.

Secondary estimands: `T1 - T0` and `T2 - T1`. They are descriptive/supporting
and cannot replace failure of the primary estimand.

## 4. Historical validity status

The 2016–2025 corpus is retrospective and exploratory because:

- modern LLM training may postdate and contain sample-period news or outcomes;
- FinBERT weights postdate part of the sample;
- the reused 2026 S&P 100 universe is survivorship-biased when projected back.

Confirmatory language is forbidden unless T3's documented training cutoff
precedes the evaluation window and the universe is point-in-time correct. The
preferred confirmatory design is prospective: pin the model first, then collect
future news and use a universe fixed at decision time.

## 5. Data posture

Follow `docs/r03-news-reasoning-data-reuse-decision.md`.

- Raw text remains in `C:\Users\User\Desktop\FinGPT\data\news_raw`.
- Access is read-only and local.
- No raw text is copied, committed, pushed, logged, or sent to an external
  provider.
- Tracked artifacts may contain schemas, counts, hashes, aggregate statistics,
  and non-reconstructable diagnostics only.

The provider-free full census is recorded in
`docs/r03-news-reasoning-provider-free-coverage-audit.json`. It found 436,916
query captures but 290,858 unique article IDs; 33.43% of captures were ticker-
query duplicates. After the frozen universe/relevance/headline filters, 247,976
unique articles produced 301,541 ticker-article events. Among eligible articles,
body content is present in 50.90%, summary in 29.33%, and 49.10% contain only a
headline. The earlier 60-page 68.1% body estimate was not corpus-representative.

Canonical missing-text rule:

- headline is required for an article record;
- `summary` and `content` are separate fields with explicit nulls and presence
  flags; neither is silently substituted for the other;
- body-missing records remain eligible and both T2/T3 receive byte-identical
  fields and flags;
- primary ITT includes all eligible decision frames;
- `BODY_PRESENT` versus `BODY_MISSING` is a preregistered secondary stratum and
  cannot rescue the primary verdict;
- exact aggregate coverage, payload-cap retention, and source hashes are pinned
  by the coverage-audit record.

## 6. Provider-free fail-only gates

All gates compare against a preregistered minimum economically meaningful effect
`delta_star`. Passing a gate is never positive evidence for T3.

1. **Constrained clairvoyant ceiling:** define incremental headroom as
   `U_clairvoyant_feasible - U_B0`, where `B0` is the best preregistered non-news
   deterministic baseline selected without evaluation leakage. Stop if this
   incremental headroom cannot exceed `delta_star`. Absolute clairvoyant utility
   is not the gate statistic.
2. **Cheap-text learnability:** fit the prespecified T2 family with strict nested
   walk-forward. If the one-sided upper confidence bound of net utility on T2
   residuals is below `delta_star`, pause provider spending and require explicit
   user ratification to terminate. This is a budget/governance gate, not a
   validity claim that narrative-capable LLM reasoning has no value.
3. **Power:** use paired time-series utility differences, dependence-respecting
   blocks, and a one-sided test. Stop or extend the window if MDE exceeds
   `delta_star`.

`delta_star`, utility units, confidence level, cost schedule, block rule, and
worst-cell governance must be frozen before any gate runs.

## 7. Partial-parallel work plan

May proceed while overlay-v2 I0–I5 is underway:

- P0: license/provenance record and source identity;
- P1: schema, PIT timestamp, completeness, duplication, and coverage design;
- P2: estimand, utility, cost, latency, and action-space specification;
- P3: frozen T2 model-family and nested walk-forward specification;
- P4: futility/power formulas and decision labels;
- P5: charter/preregistration review and corrections.

The historical exploratory split topology is mandatory:

`development -> calibration -> one contiguous OOS evaluation, opened once`

P5 freezes the dates as follows:

- development decisions: 2016-01-04 through 2020-12-23;
- purged development sessions: 2020-12-24, 2020-12-28 through 2020-12-31;
- calibration decisions: 2021-01-04 through 2022-12-22;
- purged calibration sessions: 2022-12-23, 2022-12-27 through 2022-12-30;
- one-open OOS decisions: 2023-01-03 through 2025-12-23;
- later 2025 sessions are unavailable as h=5 decision labels and are excluded.

At every fit/re-fit time, only samples whose t+5 label has matured may enter
training. The OOS result remains retrospective exploratory evidence under §4.

Must wait until overlay-v2 I0–I5 is implemented, sealed, and reviewed:

- R03 contracts, payloads, grounding, scorers, replay, and gate code;
- fixture or frame materialization;
- any provider or model execution.

Overlay fixture/provider/LIVE completion is not an R03 prerequisite.

## 8. Leakage and independence barriers

- No return labels in prompts, candidate construction, or T3 payloads.
- `available_at = max(created_at, updated_at)` is inherited exactly.
- Split assignment precedes text/return feature development and is hash-bound.
- Development cannot inspect locked evaluation outcomes.
- Hyperparameter and representation selection occurs inside nested training
  windows only.
- Same-session technical review is not organizational independence and must be
  labelled accordingly.

## 9. P5 proposed freezes pending independent review

1. `delta_star = 0.0005` net return, or 5 bp per h=5 decision period.
2. T0/T1/T2, utility, costs, payload limits, and statistical rules in §12.
3. Exact split dates and purge rules in §7.
4. Historical endpoint remains survivor-panel exploratory; a PIT universe or
   prospective fixed universe is mandatory for confirmatory use.
5. Written permission/legal clearance remains mandatory before any external-
   provider transmission.
6. Final canonical payload **schema hash** and fitted model IDs remain blocked on
   later implementation planning; the field/order/limit contract is frozen here.

## 10. Charter exit criteria

The charter is ready for implementation planning only when:

- every item in §9 is resolved or explicitly blocks the affected phase;
- data identity and license boundaries are reviewed;
- all three futility gates have exact formulas and fail labels;
- the T2/T3 information sets are byte-equivalent apart from model method;
- historical exploratory and future confirmatory claims are separated;
- no raw article text exists in the repository or tracked artifacts;
- the exact charter/preregistration hashes pass independent technical review.

## 11. First charter review findings accepted

The first review round accepted four corrections:

- **F1:** record measured text coverage and freeze missing-text canonicalization;
- **F2:** treat G2 failure as a user-ratified provider-budget pause, never as
  evidence of T3 incapability;
- **F3:** define G1 on incremental headroom over frozen non-news baseline `B0`;
- **F4:** require development → calibration → one contiguous, one-open OOS
  topology even while exact dates remain pending.

Phase ID R03 and read-only, in-place FinGPT reuse were explicitly user-ratified
on 2026-07-19. This review acceptance authorizes no implementation or execution.

## 12. P5 exact design freeze proposal

Everything in this section is frozen **for review**, not execution. Independent
review may reject or amend it before an implementation plan exists.

### 12.1 Decision frame

- Universe: the reused 100-name survivor panel; exploratory claims only.
- Decision time: `min(15:30 America/New_York, actual close - 30 minutes)`.
- News window: `(decision(t) - 72 hours, decision(t)]`.
- Article availability: `max(created_at, updated_at) <= decision(t)`.
- Outcome: sector-relative split-adjusted close-to-close return at h=5.
- Price/risk inputs: daily bars through session `t-1`; no full-session t OHLCV.
- Portfolio evaluation: five deterministic h=5 phase books, as in FinGPT.
- Every tier runs on the same decision frame; missing news means no news
  increment, not frame deletion.

### 12.2 Canonical T2/T3 news payload

Eligibility and deduplication:

1. headline non-null/non-empty;
2. `1 <= distinct source symbols <= 5`;
3. at least one symbol intersects the frozen universe;
4. select one record per article ID with maximum `available_at`; exact ties use
   lexicographic maximum `(updated_at, input_text_sha256)`;
5. assign the article identically to every intersecting universe ticker.

Canonical string normalization is UTF-8, Unicode NFC, CRLF/CR to LF, and NUL
removal. Case and HTML are preserved. Ordered article fields are:

`article_id, available_at, symbols, source, headline, summary, content,
summary_present, content_present, content_truncated`.

`summary` and `content` use explicit nulls. Articles sort by `available_at`
descending then `article_id` ascending. Text budgets are:

- 32,768 UTF-8 bytes per article across headline/summary/content;
- 131,072 UTF-8 text bytes per ticker-session frame.

Headline is preserved first, then summary, then the largest valid UTF-8 content
prefix. If the frame limit is reached, the final includable article may have only
its content truncated; later articles are omitted and counted. The census shows
this policy fully preserves 99.06% of news-positive frames, retains 99.06% of
article appearances, and retains 97.03% of text bytes. T2 and T3 receive the
same canonical bytes and truncation flags.

The implementation verifier must recompute all three retention rates directly
from the read-only raw source under the exact early-close calendar and payload
rules. It must fail closed in negative tests that perturb the article cap, frame
cap, article ordering, early-close cutoff, or duplicate-selection rule; verifier
output may contain aggregates and hashes only.

### 12.3 T0 non-news comparator

All T0 features use bars through t-1:

- sector-relative log returns over 5, 20, and 60 sessions;
- realized volatility over 20 and 60 sessions;
- 20-session downside semideviation;
- 60-session beta to the equal-weight sector return;
- 20-session mean log dollar volume;
- 5-versus-20-session log-volume shock;
- explicit missingness flags.

Per decision date, missing values use the same-date sector median, then the same-
date universe median if needed. Continuous features are then cross-sectionally
clipped at the 1st/99th percentiles, sector-demeaned, and z-scored.

The scorer is ridge regression on h=5 sector-relative return. Candidate alpha is
`{0.1, 1, 10, 100}`. Development uses expanding rolling-origin folds ending in
2017, 2018, 2019, and 2020; the highest worst-fold net utility wins, with larger
alpha as the deterministic tie-break. No calibration/OOS reselection is allowed.
Weights refit on the first session of each month using only matured h=5 labels.

All tiers share one portfolio constructor: score descending/ticker ascending,
enter the top and bottom 10 valid names, retain existing names while they remain
inside the corresponding top/bottom 20, equal-weight each leg, long gross 1,
short gross 1, net 0. Fewer than 20 valid names causes a no-trade frame.

### 12.4 T1 sentiment comparator

T1 adds only frozen FinGPT `sentiment_mean_3d` and a sentiment-available flag to
the T0 design matrix. FinBERT identity and inference lock remain unchanged.
`sentiment_count_3d` is diagnostic only. T1 uses the same ridge selection,
monthly refit, and portfolio constructor as T0. Missing sentiment is encoded as
score 0 with availability 0.

### 12.5 T2 cheap-text comparator

T2 predicts the matured h=5 sector-relative return residual left by T0 using the
canonical payload:

- `HashingVectorizer`: `n_features=2^18`, word `(1,2)`-grams, lowercase,
  `alternate_sign=false`, `norm=null`, token pattern `(?u)\b\w\w+\b`;
- `TfidfTransformer`: L2 norm, smoothed IDF, sublinear TF; IDF fits on the
  training window only;
- deterministic ridge: solver `lsqr`, alpha in `{1, 10, 100, 1000}`, tolerance
  `1e-6`, maximum 10,000 iterations;
- development selection: highest worst-fold net utility, then larger alpha;
- monthly expanding refit with matured labels only.

The T2 score is `T0_prediction + clipped_text_residual_prediction`; clipping uses
the training-window 1st/99th residual-prediction percentiles. The exact spec,
training-frame hash, fitted TF-IDF state, coefficients, and intercept form the
T2 model ID. At implementation time that ID must additionally bind the exact
Python, NumPy, SciPy, and scikit-learn package identifiers and versions; the
concrete `HashingVectorizer`, `TfidfTransformer`, and ridge implementation
identifiers; and any solver/BLAS identity that can change fitted output.

The same T2 family is G2 and the later T3 comparator. After G2 it cannot be
reselected, replaced, or refit under a changed protocol.

### 12.6 Utility, costs, and minimum effect

Primary period utility is sector-neutral long-short spread return minus realized
turnover cost. Turnover is the sum of absolute weight changes across both legs;
the first rebalance charges full establishment turnover.

- Base transaction cost: 10 bp/side, inherited from FinGPT.
- Sensitivity grid: 5, 10, and 15 bp/side; the worst included cell governs.
- `delta_star`: 5 bp net utility per h=5 period (`0.0005`).
- Provider monetary cost, when later authorized, is converted to return at a
  fixed USD 1,000,000 reference capital and subtracted from T3 utility.
- T3 results not settled by 15:50 ET fail closed to T2 and remain in ITT.

The 5 bp threshold is fixed before any T2 fitting or T3 call. It is not reduced
because a smaller effect is statistically significant.

### 12.7 Statistical and governance rules

- One-sided alpha: 0.05; target power: 0.80.
- Stationary block bootstrap: block length 10 sessions, 10,000 resamples,
  outcome-independent domain-separated PCG64 seed.
- G1 statistic: `U_clairvoyant_feasible - U_T0`, on calibration only. Its
  one-sided 95% upper bound at or below `delta_star` yields
  `STOP_NO_ECONOMIC_HEADROOM`.
- G2 statistic: `U_T2 - U_T0`, on calibration only. Upper bound at or below
  `delta_star` yields `PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION`.
- G2 user termination yields `STOP_BUDGET_FUTILITY_USER_RATIFIED`.
- G2 user continuation yields `CONTINUE_AFTER_G2_PAUSE_USER_RATIFIED`; this
  authorizes no provider call by itself and leaves the exact T2 model ID fixed.
- Under either G2 user branch, the T2 model ID remains fixed; termination archives
  it as the comparator record and continuation carries that identical ID forward.
- G3 uses the full-frame calibration series `D_proxy = U_T2 - U_T0`. A
  stationary block bootstrap draws series of the planned 747 OOS decisions.
  The preregistered grid crosses centered-series SD multipliers `{1, 1.5, 2}`
  with fail-closed rates `{0, 0.05}`; the latter dilutes the tested ITT effect to
  `delta_star * (1 - fail_rate)`. Every cell must reach 80% one-sided power in
  10,000 seeded resamples. Otherwise label `STOP_UNDERPOWERED` or extend the
  prospective window before provider use.

Passing any provider-free gate is not evidence that T3 works. G2 pause/stop is
not evidence that narrative reasoning is incapable; it is budget governance.
