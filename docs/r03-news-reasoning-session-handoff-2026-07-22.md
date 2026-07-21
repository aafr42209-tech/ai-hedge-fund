# R03 session handoff — 2026-07-22

State at end of session: **G1 executed and independently verified. G2 not
authorized.** Working tree clean at commit `ac146135e9fb029ecd2ba2854b055b7841e2cceb`.

## 1. Frozen anchors — do not re-derive

```
preparation_commit_sha  fecd81298e289c114e4954e3b2fca1e654594abd
seed_sha256             f36b6e123de6852d5e9b6b8316a653e38d128a5da4ccfb78a4a831feb62098ff
t0_protocol_id          b754d194339d0a4131d0832785991b2360d83513f99ff86379ffdcf898e29e53
runner_protocol_id      3880b9bfca4e06210d8d0db9f75c5758c265e11193ca003de4858f682608ac7c
t0_model_series_id      8e2210cc5106cb1f...  (full value in the execution record)
implementation commit   ac146135e9fb029ecd2ba2854b055b7841e2cceb  (identity only, NOT a seed anchor)
```

The seed is anchored to the preparation commit, not to the later fix commit,
because the first (failed) run had already reached `evaluate_g1_cost_cells()`.
Its values were computed in memory and never emitted, observed, or persisted —
audited across the reply and its full transcript — so the original seed remains
outcome-independent. **Any future re-run of G1 must reuse these anchors.**

## 2. G1 result

Record: `.research_artifacts/r03-news-reasoning/g1-stage2-execution-record-v1.json`
(SHA-256 `f210ab84b8d26332f200d35ca77cd74ee82a08ab6fe4731dd358455db23a3e93`)

| cost | n | point | lower 95 | upper 95 | upper ÷ delta_star |
|---|---|---|---|---|---|
| 5 bp | 498 | 1224.8 bp | 1076.7 | 1415.4 | 283x |
| 10 bp | 498 | 1227.6 bp | 1079.4 | 1422.1 | 284x |
| 15 bp | 498 | 1230.5 bp | 1084.4 | 1420.0 | 284x |

- label `G1_CONTINUE_NO_FUTILITY_PROOF`, governing cell 10 bp, `band_undetermined: false`
- selected `t0_alpha_e1 = 100` (alpha = 10.0)
- sessions 1762, burn-in 61, development decisions 1193, calibration decisions
  498, fit rows 164842, bound certificates 498
- boundary counters all zero; exactly two gateway asset reads
- runtime ~216 s

**This CONTINUE is not evidence for anything.** It was recorded before execution
that the configured gate returns CONTINUE with near-certainty because the
gate-bearing bound is the zero-cost, time-decoupled sorting relaxation. The
prediction held at 284x. Do not cite G1 as support for a news, text, or LLM
contribution claim; the amendment forbids it explicitly.

## 3. The one substantive signal in the G1 output

`U_T0` is **negative** over calibration (about -153.6 percentage points of
cumulative utility at 5 bp). Headroom is therefore large partly because the
baseline loses money, not only because clairvoyance is powerful.

This matters for G2 (`U_T2 - U_T0`): improvement over a losing baseline can mean
"loses less", not "makes money". Before G2 is authorized, the gate spec should
state how a G2 pass is to be interpreted when `U_T0 < 0`, and whether an
absolute economic-significance condition applies alongside the contrast. Fixing
that after seeing a G2 number would be a post-hoc specification change.

## 4. What is proven and what is not

Proven: the pipeline runs end to end on real pinned data under the frozen
protocol; gateway, hash pins, burn-in, refit protocol, alpha selection, bound
certificates, bootstrap, and record serialization all work and are reproducible
from the recorded anchors.

Not proven, and untouched: any claim about news, text, LLM reasoning, or
economic value. R02's finding stands — a trivial zero-activity rule reproduced
the LLM's selections 55/55, and nothing since has identified an LLM-specific
contribution.

## 5. Open items for the next session

1. **G2 specification gap (blocking, decide before authorizing G2)** — the
   `U_T0 < 0` interpretation question in section 3.
2. **T2 needs scikit-learn.** `fit_t2_after_separate_authorization` imports it
   and the venv has only numpy/scipy/pandas/pyarrow. A dependency authorization
   will be needed, with the same numpy/scipy version-invariance evidence used
   for pyarrow.
3. **Push has never happened.** All R03 work is local. Decide whether to push.
4. **Module size.** `r03_g1_execution.py` exceeds the 800-line repo norm; LOW,
   non-blocking.
5. **Seal simplification** was agreed but deferred: one generic
   `scripts/seal_verify.py` plus a single `docs/r03-ledger.md`, leaving the
   historical chain frozen as Tier B. Still not started.

## 6. Working agreements to carry forward

- Claude reviews and never implements R03 research code; Codex implements;
  the human issues authority strings and nothing else.
- Codex is driven through `.research_artifacts/r03-news-reasoning/handoff/`
  with `call-codex.sh`, which refuses to run without an explicit authority
  string and writes transcripts to files rather than into the reviewer context.
- New seal layers are budgeted at two files. Tier A gets fail-closed
  verification; Tier B is recorded only.
- On any gap the sealed corpus does not determine: stop and report. A halt with
  a named gap beats a completed run containing one silent choice. Three halts
  this session were correct and produced better specifications each time.
