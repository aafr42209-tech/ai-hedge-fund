# R03 G1 gate-definition reconciliation amendment

Date: 2026-07-22  
Status: normative additive amendment, recorded before any G1 output existed

## 1. Scope and sealed conflict

This amendment does not edit or replace either sealed base document. It resolves
one contradiction inside `docs/r03-news-reasoning-provider-free-preregistration-draft.md`
before execution of G1.

The sealed Section 6 statement is, verbatim:

> Let `B0` be the best preregistered non-news deterministic baseline, selected
> without evaluation leakage. Compute:
>
> `H_clairvoyant = U_clairvoyant_feasible - U_B0`
>
> under the exact action, exposure, turnover, liquidity, cost, and latency
> constraints.

The sealed Section 14.4 statement is, verbatim:

> 1. G1 calibration `U_clairvoyant_feasible - U_T0`; upper 95% bound <=
>    delta_star → `STOP_NO_ECONOMIC_HEADROOM`.

These statements conflict in two ways: they name `B0` versus `T0` as the
baseline, and Section 6 describes a cost- and turnover-constrained clairvoyant
quantity while the sealed implementation defines a zero-cost, time-decoupled
sorting relaxation and separately exposes a cost-bearing greedy feasible
bracket.

## 2. Governing reconciliation

The G1 STOP decision is governed by the zero-cost, time-decoupled sorting
relaxation minus the frozen development-selected T0 baseline at each registered
T0 cost cell. A futility gate may stop the research line only when even this
generous ceiling fails to clear `delta_star`; using the conservative
cost-bearing greedy bracket could create a false futility stop. The greedy
feasible bracket is therefore a reported secondary diagnostic and is never
gate-bearing. `B0` and the frozen development-selected `T0` are the same object:
T0 is the preregistered non-news deterministic baseline selected without
evaluation leakage, so this identity preserves both sealed baseline statements.

The protocol identity must bind the exact rule string:

`R03_G1_GATE_RECONCILIATION_RULE=ZERO_COST_TIME_DECOUPLED_SORTING_RELAXATION_MINUS_IDENTICAL_B0_T0_GOVERNS_STOP_GREEDY_COST_BEARING_FEASIBLE_BRACKET_DIAGNOSTIC_ONLY_V1`

## 3. Fold validation windows

For fold end year `Y` in `{2017, 2018, 2019, 2020}`, the validation window is
every development decision session whose America/New_York calendar year is
exactly `Y`. Its first and last members are therefore the first and last frozen
development sessions in that calendar year. At every monthly refit within the
window, training is the expanding, strictly earlier development history whose
h=5 labels have matured by the refit timestamp. No future fold year, purge row,
calibration row, or OOS row may enter selection.

The protocol identity must bind the exact rule string:

`R03_T0_FOLD_VALIDATION_WINDOW_RULE=DEVELOPMENT_DECISION_SESSIONS_WITH_CALENDAR_YEAR_EQUAL_FOLD_END_YEAR_EXPANDING_STRICTLY_EARLIER_MATURED_HISTORY_BEFORE_EACH_MONTHLY_REFIT_V1`

## 4. Timestamps and row identity

The calendar date of a market-bar session is the UTC calendar date of its
pinned timestamp. For decision session ordinal `t`, `decision_at` is 15:30:00
America/New_York on session `t`; `feature_cutoff_at` is the same nominal clock
on session `t-1`; and `label_maturity_at` is the same nominal clock on session
`t+5`. These nominal timestamps order G1 data and do not assert an actual market
close time.

Every ticker row has the deterministic identity
`{split_name}|{decision_session_ordinal:06d}|{decision_date:YYYY-MM-DD}|{ticker}`.
Split names and tickers already obey their sealed enumerations, so this format is
unambiguous.

The protocol identity must bind these exact rule strings:

- `R03_T0_TIMESTAMP_RULE=UTC_SESSION_DATE_NOMINAL_1530_AMERICA_NEW_YORK_DECISION_T_FEATURE_T_MINUS_1_LABEL_T_PLUS_5_V1`
- `R03_T0_ROW_ID_RULE=SPLIT_PIPE_DECISION_ORDINAL_06D_PIPE_DECISION_DATE_YYYY_MM_DD_PIPE_TICKER_V1`

## 5. Bound certificate root

Certificates are constructed in strictly increasing calibration decision order.
Each certificate uses decision identity
`CALIBRATION|{decision_session_ordinal:06d}|{decision_date:YYYY-MM-DD}`.
The bound certificate root is `canonical_sha256(tuple(certificate_sha256 for
certificate in certificates))`, preserving that order. It is not a set hash,
Merkle root, file hash, or hash of realized-return content.

The protocol identity must bind the exact rule strings:

- `R03_G1_BOUND_CERTIFICATE_DECISION_ID_RULE=CALIBRATION_PIPE_DECISION_ORDINAL_06D_PIPE_DECISION_DATE_YYYY_MM_DD_V1`
- `R03_G1_BOUND_CERTIFICATE_ROOT_RULE=CANONICAL_SHA256_ORDERED_TUPLE_OF_PER_DECISION_CERTIFICATE_SHA256_IN_DECISION_ORDER_V1`

## 6. Aggregate output contract

The reviewed driver writes exactly one aggregate record to
`.research_artifacts/r03-news-reasoning/g1-stage2-execution-record-v1.json`.
The file is UTF-8 canonical JSON with sorted keys, no insignificant whitespace,
and exactly one trailing LF. The driver must create the file exclusively and
must refuse to overwrite an existing record. No caller-selected output path or
serialization option exists.

The protocol identity must bind these exact values:

- `R03_G1_AGGREGATE_OUTPUT_PATH=.research_artifacts/r03-news-reasoning/g1-stage2-execution-record-v1.json`
- `R03_G1_AGGREGATE_SERIALIZATION_RULE=CANONICAL_JSON_UTF8_SORTED_KEYS_NO_INSIGNIFICANT_WHITESPACE_EXACTLY_ONE_TRAILING_LF_CREATE_EXCLUSIVE_V1`

## 7. Gateway rule scope

The exact-path, no-prefix, no-recursion gateway rule governs filesystem reads on
the genuine Stage 2 execution path. Synthetic test doubles and read-only
integrity hash inventories are explicitly outside that execution-path rule.
Execution counters remain mandatory and count genuine execution-path reads and
attempts. The five earlier reads—one integrity-inventory read and four synthetic
test-file reads—were correctly reported under the former over-broad wording;
this scope correction does not relabel that historical report.

The protocol identity must bind the exact rule string:

`R03_G1_STAGE2_ASSET_ACCESS_RULE=EXECUTION_PATH_EXACT_RESOLVED_ABSOLUTE_PATH_MATCH_ONLY_NO_PREFIX_NO_RECURSION_TEST_DOUBLES_AND_INTEGRITY_HASH_INVENTORIES_OUT_OF_SCOPE_V2`

## 8. Gate-power disclosure addendum

### 8.1 Pre-execution prediction

Under the registered configuration, G1 is expected to return
`G1_CONTINUE_NO_FUTILITY_PROOF` with near-certainty. This expectation is a
property of the instrument: the gate-bearing upper quantity is a
perfect-foresight, zero-cost, time-decoupled sorting relaxation, while
`delta_star` is 5 bp. A CONTINUE result is therefore expected before execution
and is not itself a research finding.

The protocol identity must bind the exact rule string:

`R03_G1_PRE_EXECUTION_POWER_PREDICTION_RULE=CONFIGURED_G1_EXPECTED_TO_RETURN_CONTINUE_WITH_NEAR_CERTAINTY_INSTRUMENT_PROPERTY_NOT_FINDING_V1`

### 8.2 Evidential weight

A G1 CONTINUE result is not support for any claim about news, text, or LLM
contribution. It must not be cited as support for such a claim in any downstream
document, abstract, or summary.

The protocol identity must bind the exact rule string:

`R03_G1_CONTINUE_EVIDENTIAL_WEIGHT_RULE=G1_CONTINUE_NOT_SUPPORT_FOR_NEWS_TEXT_OR_LLM_CONTRIBUTION_AND_MUST_NOT_BE_CITED_AS_SUCH_V1`

### 8.3 Sandwich reporting and middle-band state

For every registered cost cell, the aggregate execution record must report an
explicit power-disclosure pair. The lower end is the per-decision mean of the
cost-bearing greedy feasible utility minus the identical T0 utility. The upper
end reports both the point estimate and the upper 95% bound of the zero-cost,
time-decoupled relaxation minus that same T0 utility. The record must also carry
the width from the greedy lower end to the relaxation upper 95% bound.

The pair must expose whether the lower end exceeds `delta_star`, whether the
upper 95% bound is at or below `delta_star`, and whether the bracket straddles
`delta_star`. The sealed two-label gate remains unchanged. The middle band uses
the existing `G1_CONTINUE_NO_FUTILITY_PROOF` label together with the explicit
field `band_undetermined: true`; no third gate label is introduced.

The protocol identity must bind the exact rule string:

`R03_G1_SANDWICH_REPORTING_RULE=REPORT_GREEDY_COST_BEARING_LOWER_AND_ZERO_COST_TIME_DECOUPLED_POINT_AND_UPPER_95_WITH_DECISION_BAND_WIDTH_AND_BAND_UNDETERMINED_BY_COST_CELL_V1`

## 9. Timing attestation

This reconciliation was written before any G1 number or output existed. No G1
point estimate, confidence bound, cost-cell result, gate label, or other G1
value existed or influenced this choice.
