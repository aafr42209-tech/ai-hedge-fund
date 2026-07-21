# R03 T0 feature and label formula amendment

Status: `PRE_EXECUTION_SPECIFICATION_AMENDMENT_PENDING_INDEPENDENT_REVIEW_NO_EXECUTION_AUTHORITY`

This additive amendment fixes the raw T0 feature and h=5 label formulas that
the sealed provider-free preregistration names but does not algebraically
define. The sealed base document remains byte-for-byte unchanged. This
amendment was written before any R03 frame materialization, fitting, G1
calculation, calibration decision, or OOS access.

## 1. Scope and precedence

This amendment is normative only for the formulas, minimum-history rules, and
invalid-input behavior below. It does not change the frozen split dates,
purges, h=5 horizon, T0 alpha grid, development selection, monthly expanding
fixed-alpha refit protocol, action constraints, costs, or G1 decision rule.

The tracked composition entry point remains
`docs/r03-news-reasoning-document-composition-index.md`. This amendment is an
additive pre-execution specification overlay; it does not rewrite that sealed
index or any document reachable from it.

Protocol identifier:
`R03_T0_FEATURE_FORMULA_AMENDMENT_V1`.

Normative rule identities:

- `R03_T0_BETA_60_RULE=OLS_INTERCEPT_EQUAL_WEIGHT_UNIVERSE_RETURN_EXPLICIT_DEPARTURE_FROM_SEALED_SECTOR_BETA`;
- `R03_T0_BURN_IN_RULE=EXCLUDE_DECISION_SESSION_UNTIL_61_PRIOR_PINNED_BAR_SESSIONS`;
- `R03_T0_AGGREGATE_RULE=VALID_NAMES_ONLY_MINIMUM_COUNT_1`;
- `R03_T0_CLOSE_ADJUSTMENT_RULE=SHA_PINNED_CLOSE_ASSUMED_SPLIT_ADJUSTED_UNCERTIFIED`.

## 2. Frozen inputs and session indexing

Sessions are the strictly increasing distinct timestamps in the pinned
`market_bars_real.parquet`. Let session ordinal `s` index that sequence.
The market-bars ticker set must equal the pinned internal universe snapshot
ticker set exactly.

For ticker `i` and session `s`:

- `C[i,s]` is the positive finite `close` from the pinned bars, treated under
  the explicit split-adjustment assumption below;
- `V[i,s]` is the strictly positive finite volume from the pinned bars;
- `g(i)` is the sector in the pinned universe snapshot;
- `r[i,s] = log(C[i,s] / C[i,s-1])`.

No artifact or provenance record available to this Stage 2 protocol certifies
that the pinned bars' `close` field is split-adjusted. This amendment therefore
makes the explicit, uncertified assumption that `close` in the exact
SHA-256-pinned market-bars asset is split-adjusted. The risk is that any
unadjusted split discontinuity would create spurious returns and contaminate
features and labels. Results are conditional on this assumption and must not
describe the field as independently certified.

For each session, define equal-weight means over valid names:

- `sector_return[g,s] = mean(r[j,s] for valid j with g(j)=g)`;
- `universe_return[s] = mean(r[j,s] for valid j in the full pinned universe)`.

A name is valid for either mean only when its `r[j,s]` is available and finite.
Each mean requires at least one valid name and is undefined when its valid-name
count is zero. Missing names are skipped; they do not make an otherwise
non-empty mean undefined.

No capitalization or volume weights are used.

For decision session `t`, all features end at `t-1`. An N-session return
window is `s = t-N, ..., t-1`, contains exactly N one-session returns, and
therefore requires N+1 valid closes. Partial windows are prohibited.

A decision session with fewer than 61 prior pinned bar sessions is structural
burn-in and is excluded in full from preprocessing, fitting, refits,
predictions, and G1 utility. It is not retained as an all-missing row block and
is not made eligible by imputation. After burn-in, ticker-specific missing raw
features follow Section 4 and do not by themselves exclude the decision
session.

## 3. Raw T0 features

All calculations use float64, are unannualized, and apply no scaling beyond
the separately frozen same-date preprocessing.

### 3.1 Sector-relative log returns

For `N in {5,20,60}`:

`sector_relative_log_return_N[i,t] =
sum(r[i,s] - sector_return[g(i),s], s=t-N,...,t-1)`.

### 3.2 Volatility

For `N in {20,60}`, let
`r_bar = mean(r[i,s], s=t-N,...,t-1)`.

`volatility_N[i,t] =
sqrt(mean((r[i,s] - r_bar)^2, s=t-N,...,t-1))`.

This is the population standard deviation: `ddof=0`. It is not annualized.

### 3.3 Downside semideviation

`downside_semideviation_20[i,t] =
sqrt(mean(min(r[i,s],0)^2, s=t-20,...,t-1))`.

The threshold is exactly zero. Positive returns contribute zero, and the
denominator is exactly 20.

### 3.4 Sixty-session beta

The sealed preregistration names this field "sector beta 60". This amendment
deliberately departs from that quantity: because the roughly 100-name pinned
universe is divided across many sectors, small sector membership would make a
sector-return regressor unstable. The historical field name
`sector_beta_60` is retained only for schema compatibility. Consistent with
`R03_T0_BETA_60_RULE`, its normative formula is the intercept-including OLS
slope on the equal-weight universe return, not on `sector_return[g(i),s]`.

For `s=t-60,...,t-1`, let `m[s]=universe_return[s]`,
`m_bar=mean(m[s])`, and `r_bar=mean(r[i,s])`.

`sector_beta_60[i,t] =
sum((m[s]-m_bar)*(r[i,s]-r_bar)) /
sum((m[s]-m_bar)^2)`.

If the denominator is zero, the feature is missing. No ridge, clipping, or
fallback is applied inside this formula.

### 3.5 Mean log dollar volume

`mean_log_dollar_volume_20[i,t] =
mean(log(C[i,s] * V[i,s]), s=t-20,...,t-1)`.

Every close and volume in the window must be strictly positive and finite.

### 3.6 Volume shock

Let `mean_volume_N[i,t] =
mean(V[i,s], s=t-N,...,t-1)`.

`volume_shock_5_vs_20[i,t] =
log(mean_volume_5[i,t] / mean_volume_20[i,t])`.

Both windows must be complete and every included volume must be strictly
positive and finite. No epsilon, winsorization, or alternate ratio is allowed.

## 4. Missingness

A raw feature is missing when any required observation, sector mean, or
universe mean is unavailable or non-finite; when its complete window is not
available; when a required close or volume is non-positive; or when the beta
denominator is zero.

Missing raw features enter the already-frozen same-date processing unchanged:
sector then universe median imputation, 1/99 clipping, sector demeaning,
ddof=0 z-scoring, and an unscaled `_missing=1` flag. A valid raw feature has
`_missing=0`. No partial-window value may be imputed before the raw feature
is marked missing.

## 5. h=5 label

For decision session `t` and label session `t+5`:

`q[i,t] = C[i,t+5] / C[i,t] - 1`.

The label is the simple, not logarithmic, split-adjusted return minus the
same-session equal-weight sector mean:

`y[i,t] = q[i,t] - mean(q[j,t] for j with g(j)=g(i))`.

The sector mean uses the same valid-name rule as the feature aggregates: names
with unavailable or non-finite `q[j,t]` are skipped, and the mean is undefined
only when the sector has zero valid names. A name with unavailable or
non-finite `q[i,t]` has no label. Both endpoint closes must be positive and
finite. The label is a price return; cash dividends are neither included nor
reinvested. The same fixed universe snapshot and sector membership used by the
features govern the label.
The label matures at session ordinal `t+5`; no earlier observation may enter
fitting.

## 6. Clock boundary

G1 uses market-bar session ordinals. Decision and maturity timestamps use the
nominal `15:30 America/New_York` convention only to provide a deterministic
within-date ordering. Actual early-close times do not alter feature windows,
label ordinals, monthly refit membership, or G1 utility, and are deferred to
the separately authorized T2/T3 news-session assignment contract.

## 7. Non-authority

Independent review disposition is pending. All execution-dependent identities
remain `BLOCKED_PENDING_SEPARATE_EXECUTION_AUTHORITY`.

This amendment authorizes no parquet access, frame creation, fitting, G1
execution, OOS access, inference, provider/network use, commit, or push.
