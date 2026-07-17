# R02 D2c provider-free frame and statistical-freeze report

Date: 2026-07-17

Status: `PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE`

Provider calls: `0`

Live executions: `0`

## Frozen frame identity

- Frame ID: `r02-d2c-frame-53be0c4bb060`
- Root seed:
  `53be0c4bb060051e16c13f913f93afcbd97aa2106b90c29d77a4fd6ebd78a93d`
- Seed derivation: SHA-256 over canonical JSON containing a fixed domain, the D1
  freeze SHA, the D1 manifest SHA, and D2b commit `0f670bb`.
- Representative cases: first 120 generator indexes, without outcome or headroom
  conditioning.
- Challenge cases: first 40 indexes after 119 satisfying trigger true, `K >= 2`,
  and strictly positive generated-candidate headroom.
- Duplicate policy: exact content or canonical public state excluding case ID and
  seed invalidates the frame; no skip or replacement is permitted.
- Local append-only tree: `162` files.
- Full tree SHA-256:
  `316eb5757b2eda3a04ec16f19a225df7a6e44fdf7f506482aa947b9cf77fb494`.

## New-frame observations

The representative stratum contains exactly 20 cases from each of the six frozen
regimes. The frozen 50-bps trigger fired in `15/120 = 12.5%`; all 15 had `K >= 2`.
No threshold or generator setting was changed after this observation.

The challenge scan covered the contiguous source indexes 120 through 513:

- scanned: `394`;
- not triggered: `339`;
- triggered with no positive candidate headroom: `15`;
- admitted: `40`;
- triggered candidate counts: `K2=13`, `K3=15`, `K4=27`.

All 40 admitted challenge cases are high-transaction-cost cases. This is an
observed consequence of the frozen admission rule, not an additional stratum
filter. The final frame has `55` eligible opportunities: 15 representative plus
40 challenge.

## Practical minimum effect

The scoring scale is `1e12`; one basis point of portfolio-level utility is
`100,000,000 e12`. The proposed thresholds are:

- `delta_min_e12 = 50,000,000`, equivalent to 0.5 bp of utility;
- `delta_target_e12 = 100,000,000`, equivalent to 1 bp of utility.

The new frame's provider-free oracle-selector upper-bound estimand is
`144,404,140 e12`, or about 1.444 bp. The minimum is 34.6250% and the design
target is 69.2501% of that upper bound. Reusing R01's `50,000,000,000 e12`
threshold would exceed the complete R02 candidate-set upper bound by over 300x
and is therefore not a meaningful R02 practical threshold.

Across the 55 eligible cases, candidate headroom has mean `420,084,770 e12`,
sample SD `381,049,791 e12`, and standardized mean `1.1024`. The registered
design scenario uses a more conservative conditional standardized mean of 1.0.

## Estimand and bootstrap

For every frozen fixture, including trigger-false, no-call, invalid response, and
baseline-fallback cases, define paired delta `D_i`; all non-intervention paths
contribute exactly zero. The primary estimand is the frozen-weight mean:

```text
theta = round_half_even(0.75 * mean(D_representative)
                        + 0.25 * mean(D_challenge))
```

The final interval resamples fixtures within each stratum, keeps the 120/40
allocation and 0.75/0.25 weights, uses PCG64 with the frozen seed, performs
10,000 resamples, and takes nearest-rank positions 250 and 9,750 for a two-sided
95% percentile interval.

`SUPPORTED` requires lower bound strictly greater than `delta_min`, `M >= 46`,
and all integrity and safety gates. `INCONCLUSIVE_LOW_TRIGGER` precedes effect
labels when `M < 46`.

## N and M_min simulation

Power simulation uses the identical frozen-weight estimator, within-stratum
bootstrap, percentile lower-bound rule, and zero-contribution mechanics. It uses
1,000 outer trials and 2,000 bootstrap resamples per operating scenario; the
registered evaluation interval remains 10,000 resamples. Conditional effects
use a bounded two-point distribution (`0` or a positive value) calibrated to the
specified mean and variance. Every positive support point is below the maximum
observed frame candidate headroom `1,722,160,500 e12`.

The design grid varies allocation, representative trigger rate, candidate
collapse, selector validity, fail-closed rate, and conditional variance.

- `N=120`, design-worst: power 77.9%, Wilson 95% lower 75.2243%; fails.
- `N=160`, design-worst: power 85.7%, Wilson 95% lower 83.3935%; passes.
- `N=160`, lower-SNR 0.8 sensitivity: power 79.0%, lower 76.3669%; fails.
- `N=200`, lower-SNR 0.8 sensitivity: power 87.4%, lower 85.1990%; passes.

The frozen design therefore selects `N=160`, allocated 120/40, under the
provider-free-grounded design SNR of 1.0. The lower-SNR result is retained as a
limitation: if the real selector behaves closer to 0.8, the study is expected to
be inconclusive more often and the threshold may not be retuned after outcomes.

`M_min=46` requires at least six representative opportunities in addition to
the 40 challenge opportunities. Under an 8% representative trigger rate and 5%
candidate-collapse rate, the exact probability of meeting it is 90.0568127%.
At the observed 12.5% trigger rate with 5% collapse it is 99.6899514%.

## Provider budget candidate

- Eligible episodes: `55`.
- Per-episode provider attempts: `1`.
- Retries: `0`.
- Global provider-attempt cap: `55`.
- Per-attempt token reserve: `32,000`.
- Aggregate token cap: `1,760,000`.
- Incremental USD cap: `0`.
- Maximum current draft prompt: `1,848` UTF-8 bytes.
- Maximum selector-safe payload: `1,320` UTF-8 bytes.
- Provider calls consumed by this work: `0`.

The 32,000-token reserve reuses the prior approved R01 accounting ceiling, which
was more than twice R01's observed maximum 15,750-token accounting total, while
the R02 selector request is materially smaller. This is an accounting ceiling,
not permission to call a provider. Zero-call preflight remains
`NOT_AUTHORIZED_NOT_FINALIZED`.

## Remaining gates

Independent review and explicit user acceptance are required before this frame
or statistical package becomes binding. Zero-call preflight and D3 remain
unauthorized even after acceptance of this candidate.
