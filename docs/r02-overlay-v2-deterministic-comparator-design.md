# R02 overlay v2 deterministic public-information comparator design

Status: **DRAFT — PROVIDER-FREE — REVIEW REQUIRED**

## Objective

Select the strongest deterministic candidate selector that uses exactly the same
canonical payload v2 bytes as the LLM. The selected scorer becomes the primary
scientific comparator and is immutable before any LLM pilot.

The hidden oracle is evaluation-only. It may rank scorer configurations on the
comparator-selection split but may never enter scorer inputs.

Overlay v2 retains the accepted D4 50bps effective-cost trigger and the
provider-free baseline/no-change/half-delta/drop-max-cost candidate generator.
The scorer ranks only the resulting deduplicated presented set. It does not alter
candidate actions or generate a new portfolio.

## Policy tiers

1. `PARSIMONY_V1`: lexicographic minimum of non-hold action count, total
   quantity, and canonical candidate ID. Continuity comparator only.
2. `PUBLIC_SCORE_V2`: selected member of the frozen family below. Primary LLM
   comparator.
3. `LLM_OVERLAY_V2`: new provider-backed intervention, not authorized here.

## Frozen-family proposal

Every scorer validates each presented candidate against the public episode,
constructs the same cost ledger, and applies the existing integer
`score_with_returns` arithmetic using only a deterministic public return proxy.

Candidate family:

- signal-weight vectors:
  - `EQUAL`: `[2000, 2000, 2000, 2000, 2000]` for `S0..S4`;
  - `S0_HEAVY` through `S4_HEAVY`: selected signal weight `4000`, each other
    signal weight `1500`;
- forecast-scale basis points: `150`, `300`, `600`;
- one `ZERO_FORECAST_MIN_RISK_COST` scorer using zero returns and the existing
  public risk/cost arithmetic.

This yields 19 proposed scorer configurations. These values are draft candidates
and become immutable only when the preregistration is accepted.

For nonzero configurations, the public return proxy is the existing integer
formula:

```text
round_half_even(
  sum(signal_weight_bps[S] * signals_bps[S] * confidences_bps[S])
  * forecast_scale_bps
  / 10000^3
)
```

Candidate tie-breaking is by canonical candidate ID, never presented order.

## Information parity

The scorer must parse the same canonical payload bytes sent to the LLM. It may
not load `SyntheticEpisode`, fixture IDs, seeds, split labels, hidden regime,
hidden expected returns, oracle scores, or unexported repository state. Public
candidate metrics must be recomputed and matched before use.

## Selection split

The scorer family and selection rule are frozen before materializing the
comparator-selection split. For each scorer:

- select one candidate per fixture;
- score that selection with the hidden oracle after selection;
- compute the preregistered target-stratum full-frame ITT utility;
- compute oracle regret, invalid/fallback rate, and concentration diagnostics.

Select the scorer with the greatest weighted full-frame oracle-scored utility.
Tie-break in this order:

1. lower oracle regret;
2. lower settled invalid/fallback count;
3. lower scorer complexity rank: zero forecast, equal weights, heavy variants;
4. lower forecast scale;
5. ASCII scorer ID.

Only the selected scorer ID and its frozen configuration cross into the untouched
headroom-validation split. Per-configuration selection outcomes do not.

## Overfitting firewall

Comparator-selection and headroom-validation fixtures, seeds, roots, and hidden
outcomes are disjoint. A failed headroom gate may not trigger scorer reselection.
Changing the family, selection metric, tie-break, or payload starts a new design
version with fresh splits.

## Required implementation tests before any provider call

- identical payload digest for deterministic and LLM paths;
- hidden-field access raises a typed hard stop;
- candidate-order permutation invariance;
- integer arithmetic and tie-break reproducibility;
- public metric recomputation equality;
- split-root non-overlap;
- scorer-selection replay from append-only artifacts;
- negative tests for fixture ID, seed, hidden regime, expected-return, and oracle
  leakage.
