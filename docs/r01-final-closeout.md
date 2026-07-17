# R01 final closeout

Status: **SEALED — PROVIDER-FREE CLOSEOUT**

Closeout manifest SHA-256:
`a9bb04131d9214a17b99a6423900e3b83f1a7345e4bf63c3ca760553654b3ada`

Provider calls performed during closeout: **0**

## Final disposition

R01 is closed. Closeout means the run, evidence, and conclusions are preserved;
it does not mean the work is discarded.

| Question | Final label |
| --- | --- |
| Audit and execution infrastructure | **PASS** |
| Direct-generation structural stability | **PASS** |
| Utility-improvement hypothesis | **NOT TESTED** |
| Investment claim | **NONE** |
| Exploratory reuse | **ALLOWED WITH PROVENANCE** |
| Result relabeling or confirmatory reuse | **PROHIBITED** |

The utility hypothesis was not formally rejected or supported. The sealed B3
work was development-stage evidence and its contract prohibited confirmatory
use. The precise closeout statement is:

> Utility-improvement hypothesis: NOT TESTED (confirmatory test not run;
> development technical evidence was unfavorable in 10 of 12 acquisitions
> relative to the deterministic baseline).

## What R01 established

The final prompt-v2/resource-v3 run completed 12/12 acquisitions with no retry,
transport failure, tool violation, or fail-closed disposition. All 72 confidence
values were valid integers and all 36 repeated action-quantity decisions were
identical across replicate pairs. Replay, ledger, preflight, transport, and
artifact-integrity controls were independently reproduced.

The infrastructure therefore supports bounded, fail-closed, auditable research
execution. It does not establish that direct LLM portfolio generation improves
the deterministic baseline.

## Sealed identity

- implementation commit: `1f65106`;
- live authorization commit: `dd52092`;
- result commit: `24a0277774c01a745a058bde58d4d308eade51fe`;
- experiment: `r01-b3-prompt-v2-resource-v3-20260717`;
- preflight SHA-256:
  `5937161ac9c2bb9c22172d0be27a5a730cc2a3dc1c8bf51044270b65ee68353e`;
- run-result SHA-256:
  `c262fac9efd5b725138e9b89b92f9043f17ee5398012348957ecf6331fd6c349`;
- canonical 299-file tree SHA-256:
  `6ecbab78625ced153cb4b446fc8e911890476c144f361769e2073c142fd5c30e`;
- final resource ledger: 27 provider attempts and 511,148 conservative tokens.

The machine-readable manifest binds the complete source list and hashes.

## Reuse policy

Permitted reuse:

- immutable R01 evidence cited with its experiment and hash identity;
- exploratory analysis clearly labeled as exploratory;
- fail-closed runner, ledger, preflight, replay, and provenance design patterns;
- R01 observations used to motivate a separately preregistered R02 design.

Prohibited reuse:

- changing or backfilling existing R01 artifacts;
- treating B3 development results as a confirmatory test;
- replacing the R01 hypothesis after observing results;
- fitting a confidence threshold to R01 and presenting it as validated;
- relabeling the sealed R01 verdict after an R02 outcome.

R02 is a different hypothesis: a deterministic baseline proposes constrained
candidates and an LLM may select among them only under a prespecified trigger.
R02 must have a new contract, experiment identity, manifest, preflight,
independent review, and separate execution authorization.

## Calibration appendix status

The provider-free calibration appendix reports 72 raw confidence observations,
36 fixture-pair-collapsed asset observations, and an inferential boundary of six
fixture pairs. Its conclusion is **NO_THRESHOLD_JUSTIFIED**. It is bound into
the closeout manifest but does not modify any R01 artifact or verdict.

## Gate state

- R01 provider calls: **not authorized**;
- D3: **not authorized**;
- R02 execution: **not authorized**;
- existing R01 artifact mutation: **not authorized**.

Any future live work requires a new explicit authorization against a reviewed
R02 implementation commit and preflight hash.
