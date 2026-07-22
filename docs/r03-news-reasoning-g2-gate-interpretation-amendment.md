# R03 G2 gate-interpretation amendment

Date: 2026-07-22  
Status: normative additive amendment, recorded before any G2 output existed

## 1. Scope and the interpretation gap

This amendment does not edit or replace any sealed base document. It closes one
interpretation gap in `docs/r03-news-reasoning-provider-free-preregistration-draft.md`
before execution of G2, and resolves open item 1 of
`docs/r03-news-reasoning-session-handoff-2026-07-22.md`.

The sealed Section 6 statement is, verbatim:

> Evaluate T2 on baseline-residual utility using strict nested walk-forward and
> paired time blocks. If the one-sided upper confidence bound is at or below
> `delta_star`, label `PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION` and
> spend no provider budget.

The sealed Section 14.4 statement is, verbatim:

> 2. G2 calibration `U_T2 - U_T0`; upper 95% bound <= delta_star →
>    `PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION`.

Both sealed statements gate on the **contrast** `U_T2 - U_T0` only. Neither
states how a non-pause (incremental) result is to be interpreted when the
baseline utility `U_T0` is negative.

G1 established empirically that `U_T0 < 0` over calibration (about -153.6
percentage points of cumulative utility at 5 bp; see
`.research_artifacts/r03-news-reasoning/g1-stage2-execution-record-v1.json`).
Because the baseline loses money, a contrast `U_T2 - U_T0` above `delta_star`
can mean either that the T2-augmented strategy **loses less** (`U_T2` still
negative) or that it **makes money** (`U_T2 > 0`). The sealed gate cannot
distinguish these. Recording an interpretation rule after observing a G2 number
would be a post-hoc specification change; it is fixed here first.

## 2. Governing decision — two independent axes

The user-ratified resolution keeps the sealed contrast gate as the sole
pass/fail authority and adds a report-only absolute-profitability flag. The two
axes are independent and are never combined into a joint gate.

### 2.1 Primary axis — incremental gate (unchanged authority)

The sealed one-sided upper-95% bound of `U_T2 - U_T0` versus `delta_star`
remains the only gate-bearing quantity. Its outcome is named on the incremental
axis:

- `G2_INCREMENTAL_FAIL` — the sealed pause condition holds (upper 95% bound of
  `U_T2 - U_T0` at or below `delta_star`); equivalent to the sealed
  `PAUSE_NO_CHEAP_TEXT_SUPPORT_PENDING_USER_DECISION`.
- `G2_INCREMENTAL_PASS` — the sealed pause condition does not hold; incremental
  headroom over `T0` is not ruled out.

`G2_INCREMENTAL_PASS` is a **futility/budget-governance non-pause, not efficacy
evidence.** It carries the same evidential ceiling the sealed preregistration
already imposes: no gate pass is efficacy evidence, and no G2 result is proof
that a narrative-capable T3 can add value. These incremental-axis names are a
semantic label on the existing sealed outcome; they do not add, remove, or
rename any sealed gate label.

The protocol identity must bind the exact rule string:

`R03_G2_INCREMENTAL_PRIMARY_GATE_RULE=SEALED_UPPER_95_BOUND_OF_U_T2_MINUS_U_T0_VERSUS_DELTA_STAR_IS_SOLE_GATE_PASS_IS_NON_PAUSE_FAIL_IS_SEALED_PAUSE_NOT_EFFICACY_V1`

### 2.2 Secondary axis — absolute-profitability flag (report-only)

For every registered cost cell, the G2 execution record must carry a recorded
absolute-profitability flag on the T2 absolute net utility `U_T2`:

- `T2_ABSOLUTE_PROFITABILITY_POSITIVE` — the recorded point estimate of `U_T2`
  is strictly greater than zero.
- `T2_ABSOLUTE_PROFITABILITY_NEGATIVE` — otherwise.

The record must also carry, per cost cell, the `U_T2` point estimate and its
one-sided 95% bound relative to zero as auxiliary fields, so the flag can be
audited without exposing it to the gate. This flag is **never gate-bearing**: it
does not change, override, gate, or veto the primary incremental decision under
any value. It exists solely to prevent a `G2_INCREMENTAL_PASS` from being read
as profitability.

The protocol identity must bind the exact rule string:

`R03_G2_ABSOLUTE_PROFITABILITY_FLAG_RULE=SECONDARY_RECORDED_SIGN_OF_U_T2_POINT_ESTIMATE_WITH_ONE_SIDED_BOUND_VERSUS_ZERO_PER_REGISTERED_COST_CELL_REPORT_ONLY_NEVER_GATE_BEARING_V1`

### 2.3 Cost cells

The secondary absolute-profitability flag is recorded for every registered cost
cell (5/10/15 bp per side). Which cell governs the primary incremental decision
is not restated here: it follows the sealed rule unchanged
("Worst included cost cell governs", `docs/r03-news-reasoning-provider-free-preregistration-draft.md`).
This amendment adds no cost-cell governance rule.

## 3. Mandatory interpretation of a pass over a losing baseline

When the primary axis is `G2_INCREMENTAL_PASS` and the secondary axis is
`T2_ABSOLUTE_PROFITABILITY_NEGATIVE`, the result means only that T2 improves
incrementally over a losing baseline — "loses less" — and does **not** mean T2 is
profitable. This combination must not be cited, in any downstream document,
abstract, or summary, as evidence that T2, news, text, or LLM reasoning makes
money or adds economic value.

The protocol identity must bind the exact rule string:

`R03_G2_LOSES_LESS_INTERPRETATION_RULE=INCREMENTAL_PASS_WITH_T2_ABSOLUTE_PROFITABILITY_NEGATIVE_MEANS_LOSES_LESS_OVER_LOSING_BASELINE_NOT_PROFITABILITY_AND_MUST_NOT_BE_CITED_AS_MAKING_MONEY_V1`

## 4. Non-authority and residual G2 gaps

This amendment fixes only the interpretation rule. It does not authorize G2
execution, raw-source access, fitting, provider or network use, dependency
changes, commits, or pushes. Two sealed G2 prerequisites remain open and
unaffected by this amendment:

- `fit_t2_after_separate_authorization` requires scikit-learn, which the venv
  does not yet provide; a dependency authorization with the same version-
  invariance evidence used for pyarrow is still required.
- G2 execution authority itself has not been issued.

## 5. Timing attestation

This interpretation was written before any G2 number or output existed. No G2
point estimate, `U_T2` value, contrast, confidence bound, cost-cell result, gate
label, or absolute-profitability flag existed or influenced this choice. The G1
observation that `U_T0 < 0` is a G1 output and is the motivating condition; no
G2 quantity was consulted.
