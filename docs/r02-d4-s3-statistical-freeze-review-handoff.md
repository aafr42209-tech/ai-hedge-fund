# R02 D4-S3 provider-free statistical-freeze independent review handoff

Date: 2026-07-18

## Required verdict boundary

This handoff requests independent review of a provider-free statistical-freeze
draft only. The expected passing verdict is:

`PASS_PROVIDER_FREE_S3_STATISTICAL_FREEZE`

A pass does not authorize a provider budget, provider calls, Codex exec,
micro-pilot, LIVE authorization or execution, retry/replacement, or commit/push
of the S3 draft. It does not modify or reclassify the sealed R02 D3 evidence or
its `SUPPORTED` verdict.

## Starting lineage

- Branch: `codex/llm-overlay-research-01`
- Freeze base commit: `c4fb28c66404fc783cfbc33d125012e1dff2c76e`
- Upstream divergence at authoring closeout: `0/0`
- S2A frame ID: `r02-d4-s2a-frame-0716a1b9c13a`
- S2A manifest SHA-256:
  `368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1`
- S2A seal SHA-256:
  `40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838`
- S2A tree tuple: 202 files / 973,115 bytes /
  `65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29`
- S2A composition: 150 representative / 50 challenge; 19 / 50
  selector-eligible; 69 total selector-eligible.
- S2A generation attempt cap: 1, with one completed generation attempt and no
  retry or replacement.
- Accepted design SHA-256:
  `784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900`
- D3 post-hoc SHA-256:
  `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
  and verdict `SUPPORTED`, unchanged.

All S3 files listed below must remain uncommitted and unpushed during this
review.

## Expected byte hashes

| File | SHA-256 |
|---|---|
| `docs/r02-d4-s3-statistical-freeze.json` | `3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449` |
| `docs/r02-d4-s3-statistical-freeze.md` | `112646a9dc412fb04cdfc9e13e25ee8c1a26dc3093837d6f0f3a0ffaa4c05c43` |
| `docs/r02-d4-s3-focused-tests.json` | `a5dbf246e109ffcb907456c8ab16673d48bbd10638a7620555679d6d8c825716` |
| `docs/r02-d4-s3-zero-call-manifest.json` | `a25f1dd3744e9ae4500c429c5e5e4e4082a163ead504561df00eff1931375afd` |
| `v2/research/overlay/r02_d4_s3_freeze.py` | `b80221af86a7db365c00d67d33378597c10f70b14c856c4080c94a7c2bbac7c2` |
| `v2/research/overlay/test_r02_d4_s3_freeze.py` | `6e74d88f5876566c0cce662620a449f392f529d200c22763fc0b19c0afc519c2` |
| `scripts/r02_d4_s3_freeze_verify.py` | `9f0e514b6b5a21e372413db59d0e2c95502b8ee581169af4b90988358c3dcd7c` |

The handoff itself is not self-hashed. Recompute every table entry from bytes;
any mismatch is blocking.

## Frozen statistical contract

### Estimand separation and priority

1. Primary exact-replication estimand: LLM-selected system utility minus the
   deterministic baseline.
2. Deterministic parsimony-policy estimand: parsimony-selected system utility
   minus the same baseline.
3. Incremental LLM estimand: LLM-selected utility minus parsimony-selected
   utility.
4. Agreement endpoint: exact candidate-ID agreement and discordance counts
   among the 69 selector-eligible fixtures, with a two-sided 95% Wilson interval.

All ITT estimands retain the sealed full-frame 150/50 composition and 3:1
target weighting with round-half-even integer e12 arithmetic. Trigger false,
no-call, invalid response, and baseline-fallback primary cases contribute zero.
The primary label is evaluated first. Secondary or incremental evidence cannot
rescue, reverse, or relabel the primary result. The ambiguity-engineered
mechanism study remains a separate future study.

### Primary and secondary thresholds

- `delta_min_e12 = 50,000,000`.
- Information gate `M_min = 57`; the sealed frame has `M = 69` and is
  prequalified before provider outcomes exist.
- Primary precedence: `INVALID_RUN`, `INCONCLUSIVE_LOW_INFORMATION`,
  `REPLICATION_NOT_SUPPORTED`, then either
  `REPLICATION_SUPPORTED_ROBUST` or `REPLICATION_SUPPORTED_FRAGILE`.
- Primary support requires bootstrap lower bound strictly greater than
  `delta_min_e12`.
- Parsimony is separately labeled invalid, low-information, supported, or not
  supported using its own interval; it cannot replace the primary.
- Incremental labels use a zero threshold only. Lower bound greater than zero
  supports incremental benefit; upper bound below zero identifies harm;
  otherwise the result is inconclusive.
- Incremental identification additionally requires at least 20 discordances
  overall and at least 5 in each stratum. Below that floor, the mandatory label
  is `NOT_IDENTIFIED_REDUNDANT_SELECTOR`. Repeated 100% agreement is therefore a
  valid, expected exact-replication result, not an execution failure.

### Bootstrap and robustness pins

- 10,000 resamples within each stratum with replacement, retaining 150/50 and
  the 3:1 target weight.
- NumPy 1.26.4 `PCG64`; reinitialize the generator for each analysis.
- Two-sided 95% nearest-rank positions: zero-based 249 and 9749.
- Outcome-independent bootstrap seed SHA-256:
  `ab143af338e991209a9c3fb387623d126ab8399aba268285758234eb15f71804`.
- Seed integer:
  `77381240907582846253313109133161309130450043096931343042213491421713473673220`.
- Runtime pins: Python 3.11.15, NumPy 1.26.4, SciPy 1.17.1, Pydantic 2.12.2.

`ROBUST` requires every condition below; primary support with any failure is
`FRAGILE`:

- unmodified lower-bound margin at least 5,000,000 e12 above `delta_min_e12`;
- maximum absolute one-eligible-fixture zero-nullification theta shift no more
  than 100,000 ppm of absolute unmodified theta;
- all 69 single-fixture zero-nullification lower bounds strictly above
  `delta_min_e12`;
- all 69 literal leave-one-out lower bounds strictly above `delta_min_e12`;
- both 5% and 10% full-stratum winsorized lower bounds strictly above
  `delta_min_e12`.

The prospective design reference preserves the frozen 8,000-bps low-SNR
setting, 85% power target, and 80% Wilson-lower target. `n=160` fails, `n=200`
is the smallest passing candidate (bounded 87.1% / 84.8796%; gamma 89.0% /
86.9095%), and `n=240` passes but is not minimal. Winsorized sizing scenarios
remain diagnostics, not sizing gates. The prespecified opportunity probability
at `M_min=57` is 94.3424%.

## Twelve skeptical checks

1. Confirm branch, HEAD, and upstream. Require HEAD exactly
   `c4fb28c66404fc783cfbc33d125012e1dff2c76e`, upstream `0/0`, no tracked
   diff, and only the eight S3 draft files, including this handoff, untracked.
   Confirm no S3 commit or push exists.
2. Recompute all seven byte hashes in the table. Confirm the freeze JSON pins
   the focused-test manifest and freeze-source hashes, and the standalone
   verifier pins the freeze JSON and focused-test manifest hashes.
3. Independently verify the sealed S2A manifest, seal, and tree identities;
   require 150/50, 19/50 eligible, total 69, and the exact frame ID above.
   Recompute `generation_attempt_cap=1` across intent, manifest, and seal.
4. Run the S3 source verifier directly and through the additive read-only
   script. Expected script verdict:
   `PASS_S3_STATISTICAL_FREEZE_REPRODUCED`. Confirm it performs no frame write,
   scan, provider, process-spawn, or network action.
5. Recompute the bootstrap seed from the canonical JSON preimage. Confirm the
   SHA-256, decimal integer, PCG64/runtime pins, 10,000 resamples, within-stratum
   scheme, and rank indexes 249/9749 exactly.
6. Confirm the four estimands are separate, the full-frame ITT and zero-
   contribution rules are fixed, primary precedence is exact, and no secondary
   endpoint can rescue or reverse the primary label.
7. Exercise the label comparators at equality boundaries. All support tests are
   strict. Verify primary invalid/low-information/not-supported precedence,
   separate parsimony labels, and incremental benefit/harm/inconclusive labels.
8. Exercise the robustness comparator. Confirm every listed gate is required,
   all 69 zero-nullification and all 69 literal-LOO intervals must pass, 5% and
   10% winsorization both must pass, and supported-but-not-robust maps only to
   `REPLICATION_SUPPORTED_FRAGILE`.
9. Confirm incremental identification requires discordance total 20,
   representative 5, and challenge 5. Confirm exact agreement uses candidate
   IDs over 69 eligible fixtures and Wilson Decimal precision 50 with
   round-half-even ppm output. Check endpoints 69/69 = [947263, 1000000] ppm
   and 0/69 = [0, 52737] ppm.
10. Recompute the protected artifact root before and after with
    `r02_d3_preflight._filesystem_tree`. Require both tuples to equal 3,687
    files / 51,050,083 bytes /
    `692ced9177f71cbe1af45a8f3ce06b7ec1c690fba87a8c7de254a1dfc834f891`,
    with all 11 protected child roots unchanged. Reconfirm the D3 post-hoc hash
    and `SUPPORTED` verdict above.
11. Run the exact frozen test argv from
    `docs/r02-d4-s3-focused-tests.json`. Require each of the nine test-file
    hashes, exact collection count 77, and all 77 tests passing. Confirm the two
    S2A LOW observations are closed by negative tamper tests: altered
    `generation_attempt_cap` is rejected, and altered expected test count is
    rejected.
12. Inspect zero-call accounting. Require provider calls 0, Codex exec 0,
    micro-pilot false, LIVE false, provider budget false, LIVE authorization
    false, frame generation/scan false, retry/replacement 0, and S3 commit/push
    false. Confirm no outcome data was accessed while authoring the freeze.

## Reproduction commands

Run from the repository root with the pinned virtual environment:

```powershell
.venv\Scripts\python.exe scripts\r02_d4_s3_freeze_verify.py --repo-root .
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_d3_posthoc_analysis.py v2/research/overlay/test_r02_d4_design.py v2/research/overlay/test_r02_d4_s1_seed.py v2/research/overlay/test_r02_d4_s1_reveal.py v2/research/overlay/test_r02_d4_s1_resolve.py v2/research/overlay/test_r02_d4_s2_frame.py v2/research/overlay/test_r02_d4_s2a_frame.py v2/research/overlay/test_r02_d4_s3_freeze.py -q
```

Use read-only verification paths only. Do not run generation, scan, provider,
Codex exec, micro-pilot, or LIVE scripts.

## Verdict format

Report:

- reproduced hashes for all seven table entries;
- S2A identity/count/cap verification;
- bootstrap seed and comparator reproduction;
- exact 77-test result;
- protected-root and D3 invariance;
- zero-call and no-S3-commit/push confirmation;
- either `PASS_PROVIDER_FREE_S3_STATISTICAL_FREEZE` or explicit blocking
  findings with file, field, observed value, expected value, and minimal fix.

## What a pass means

A pass accepts only the provider-free S3 statistical-freeze draft. The next
possible phase is a separately authorized numeric provider-budget freeze based
on the sealed eligible count of 69, followed by another independent review.
Provider calls and LIVE remain separately gated after that. A reviewer must not
request or perform those future phases as part of this handoff.
