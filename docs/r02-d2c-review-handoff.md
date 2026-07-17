# R02 D2c provider-free frame and statistical-freeze review handoff

Date: 2026-07-17

Review status: `UNCOMMITTED_REVIEW_CANDIDATE`

Branch: `codex/llm-overlay-research-01`

Base commit: `5dae53a166e621ecb6eea0b3dab4ee844daa3e1d`

## Scope

Review only the new provider-free frame builder, frame seal, statistical and
budget freeze candidate, tests, and D2c documents. Provider calls, live
execution, zero-call preflight, and D3 are out of scope and unauthorized.

The unrelated untracked file `docs/claude-d2b-multi-reviewer-handoff.md` is not a
D2c deliverable and must not be modified, staged, or included in review hashes.

## Review files

- `v2/research/overlay/r02_frame.py`
- `v2/research/overlay/r02_statistics.py`
- `v2/research/overlay/test_r02_frame.py`
- `v2/research/overlay/test_r02_statistics.py`
- `docs/r02-d2c-provider-free-authorization.md`
- `docs/r02-d2c-provider-free-frame-statistical-report.md`
- `docs/r02-d2c-frame-manifest.json`
- `docs/r02-d2c-frame-seal.json`
- `docs/r02-d2c-statistical-freeze.json`
- `docs/r02-d2c-freeze-manifest.json`
- `docs/r02-d2c-review-handoff.md`

Production source SHA-256:

- `r02_frame.py`:
  `bc2d3c64d04b4b47d8a4bee81da24bd02c411cb299f09fa15747a7871a7a8f40`
- `r02_statistics.py`:
  `9e051dbe7a64f434811fcafc1c1ce26013c14076214e959d884fb961a3d771fb`

Generated artifact SHA-256 values and sizes are recorded in
`docs/r02-d2c-freeze-manifest.json`.

## Reproduction

From the repository root:

```powershell
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_statistics.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_acceptance.py v2/research/overlay/test_r02_candidates.py v2/research/overlay/test_r02_audit_replay.py v2/research/overlay/test_r02_selector.py v2/research/overlay/test_r02_selection_audit_replay.py v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_statistics.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay -q
git diff --check
```

Expected:

- D2c focused: `12 passed`
- all R02 focused: `76 passed`
- full overlay: `203 passed`
- provider calls: `0`
- live executions: `0`

Full frame reproduction is intentionally expensive because it recomputes 160
complete-enumeration oracles. Use a new temporary output root; never overwrite
the sealed root:

```powershell
.venv\Scripts\python.exe -m v2.research.overlay.r02_frame --artifact-root C:\tmp\r02-d2c-review-frame --seal-output C:\tmp\r02-d2c-review-seal.json --manifest-copy-output C:\tmp\r02-d2c-review-manifest.json
```

Compare the reproduced manifest canonical hash, payload tree hash, file count,
and full tree hash with the committed frame manifest and seal. Do not regenerate
with another seed.

## Required review questions

1. Is the root seed determined only from immutable identities, with no seed
   search or observed-outcome adjustment?
2. Are the representative 120 cases an unconditional prefix and balanced across
   the six frozen regimes without filtering?
3. Does challenge classification freeze trigger and candidate bytes before
   reading hidden utility, admit the first 40 strict positive-headroom cases, and
   keep all classification evidence selector-inaccessible?
4. Do exact duplicates or canonical public-state near-duplicates invalidate the
   frame instead of being silently skipped or replaced?
5. Is the 50-bps trigger unchanged, and do the `15/120`, scan-394, and eligible-55
   observations reproduce?
6. Are the 162 local files, manifest reference, payload tree, and full tree all
   append-only and tamper-evident?
7. Is `delta_min=50,000,000 e12` correctly interpreted as 0.5 bp-equivalent and
   below both `delta_target` and the provider-free upper-bound estimand?
8. Does the registered estimator include every frozen fixture with all no-call
   and fallback paths contributing zero, using exact 0.75/0.25 weights?
9. Does the final bootstrap resample fixtures only within strata for 10,000
   draws, use the frozen percentile ranks, and enforce lower `> delta_min`?
10. Does the bounded power simulation reproduce N=120 failure, N=160 design-gate
    success, and the disclosed N=160 low-SNR failure without using provider data?
11. Is `M_min=46` supported by the exact 90.0568127% worst registered opportunity
    probability and the observed `M=55`?
12. Does the budget reconcile to 55 one-shot attempts, no retries, 32,000 tokens
    per attempt, 1,760,000 aggregate tokens, and zero incremental USD?
13. Are D1, the D2a generator, sealed R01 artifacts, zero-call preflight, and D3
    untouched?
14. Does every production and generated-artifact hash match the freeze manifest,
    and is the unrelated Claude review file excluded?

Report findings as `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`, with exact file
and line evidence. Do not modify, stage, commit, or push D2c files during review.
