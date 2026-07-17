# R01 confidence calibration technical report

Status: **EXPLORATORY — DESCRIPTIVE ONLY**

Provider calls performed for this report: **0**

R01 artifacts modified: **0**

## Purpose and boundary

This report asks a narrow post-run question: did the integer confidence values
from the completed R01 B3 micro-pilot track exact-oracle decision correctness?
It is not a confirmatory analysis, does not reopen R01, and does not authorize a
confidence gate for R02.

The source run is immutable
`r01-b3-prompt-v2-resource-v3-20260717`. Its `run_result.json` SHA-256 is
`c262fac9efd5b725138e9b89b92f9043f17ee5398012348957ecf6331fd6c349`.
The 299-file artifact graph reproduces canonical tree SHA-256
`6ecbab78625ced153cb4b446fc8e911890476c144f361769e2073c142fd5c30e`.

## Unit of analysis

The run contains 12 provider responses, 72 asset-level confidence values, and
six fixture pairs. The two replicates in every fixture pair produced identical
action and quantity for all six assets: 36/36 action-quantity pairs matched.
Confidence itself matched in only 3/36 asset pairs.

Therefore:

- 72 values are retained as raw descriptive observations;
- each fixture-pair/asset confidence is also collapsed to the arithmetic mean,
  yielding 36 descriptive asset observations;
- the effective inferential boundary is six fixture pairs, not 72 independent
  trials and not 36 independent trials;
- no confidence interval, significance test, fitted calibration curve, or
  optimized threshold is reported.

## Correctness definitions

`action_accuracy` means the LLM action equals the exact-oracle action for that
asset. `exact_accuracy` requires both action and quantity to equal the
exact-oracle decision. Oracle certificates were recomputed from the sealed
fixtures and all certificate hashes matched.

An oracle mismatch is a useful technical label, not a complete utility measure.
The oracle is a joint portfolio optimum; per-asset labels can hide near-ties and
interaction effects. Confidence was also not originally elicited as a formally
calibrated probability of exact-oracle agreement.

## Descriptive results

| View | n | Mean confidence | Action accuracy | Exact accuracy | Action Brier | Exact Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw responses | 72 | 89.139 | 58.33% | 50.00% | 0.312461 | 0.384961 |
| Fixture-pair collapsed | 36 | 89.139 | 58.33% | 50.00% | 0.310633 | 0.383133 |

Pair-collapsed bins:

| Mean-confidence bin | n | Action accuracy | Exact accuracy |
| --- | ---: | ---: | ---: |
| 0–49 | 0 | — | — |
| 50–59 | 0 | — | — |
| 60–69 | 3 | 0.00% | 0.00% |
| 70–79 | 1 | 0.00% | 0.00% |
| 80–89 | 10 | 60.00% | 60.00% |
| 90–100 | 22 | 68.18% | 54.55% |

The `high_transaction_cost` fixture pair is the sharpest warning: mean
confidence was 95.167 while action and exact accuracy were each 1/6. The sample
does not support a claim that high confidence reliably identifies safe
intervention.

## Threshold sensitivity — not threshold selection

| Pair-mean threshold | Retained n | Action accuracy | Exact accuracy |
| --- | ---: | ---: | ---: |
| >= 50 | 36 | 58.33% | 50.00% |
| >= 60 | 36 | 58.33% | 50.00% |
| >= 70 | 33 | 63.64% | 54.55% |
| >= 80 | 32 | 65.63% | 56.25% |
| >= 90 | 22 | 68.18% | 54.55% |

These rows reuse the same six fixture pairs and are descriptive sensitivity
checks. Selecting the best row would be post-hoc threshold optimization. R02
must either predeclare threshold candidates without fitting them to R01 or use
new provider-free/new-call-separated data under a new contract.

## Conclusion

Verdict: **NO_THRESHOLD_JUSTIFIED**.

R01 shows that confidence can be emitted in a stable integer schema, but does
not establish calibration. The allowed R02 use is design motivation only:
confidence may be logged, and a gate may be prespecified or calibrated on new
data, but no acceptance threshold may be derived from this sample.

Machine-readable results are in
`docs/r01-confidence-calibration-exploratory.json`.
