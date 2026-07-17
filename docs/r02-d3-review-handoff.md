# R02 D3 provider-free preregistration and zero-call preflight review handoff

Review base: `4c45654d81efa07aa31a97e41f49ce16b29e0939`

Candidate state: `UNCOMMITTED_PATH_B_RESEAL_REVIEW_CANDIDATE`

Provider calls: `0`

Live executions: `0`

## Scope

Review the D3 freeze-candidate contracts, zero-call transport capture,
append-only persistence, exact recapture replay, tests, manifest, and report.
Provider access, live execution, and micro-pilot execution are outside scope and
remain unauthorized.

## Diff-limited reseal context

The first multi-review passed all 15 handoff questions and recommended path B
before freeze acceptance. This candidate applies only those two prioritized
duplication fixes:

1. `scripts/r02_d3_zero_call_preflight.py` now uses
   `R02AppendOnlyArtifactStore.write_bytes`; its local `_write_new` copy is gone.
2. The five zero-call command tuples are defined only by
   `r02_d3_contracts.build_zero_call_commands`. Snapshot validation and the
   model-identity wrapper both delegate to it.

The bootstrap seed digest remains
`319dea85b61187c07089deedb525d4d927ffc03dc7ea2026e4be8022f2df9f68`.
Provider calls, live execution, and micro-pilot execution remain zero. Review
these changed source bytes and the regenerated hash chain; all original 15
questions remain binding.

Do not modify or stage `docs/claude-d2b-multi-reviewer-handoff.md`; it is an
unrelated untracked user file and is excluded from every candidate hash.

## Review files

- `v2/research/overlay/r02_d3_contracts.py`
- `v2/research/overlay/r02_d3_preflight.py`
- `v2/research/overlay/r02_d3_replay.py`
- `scripts/r02_d3_zero_call_preflight.py`
- `v2/research/overlay/test_r02_d3_preflight.py`
- `v2/research/overlay/test_r02_d3_replay.py`
- `docs/r02-d3-provider-free-authorization.md`
- `docs/r02-d3-preregistration.json`
- `docs/r02-d3-zero-call-preflight.json`
- `docs/r02-d3-zero-call-preflight-anchors.json`
- `docs/r02-d3-zero-call-preflight-replay.json`
- `docs/r02-d3-preflight-manifest.json`
- `docs/r02-d3-provider-free-preflight-report.md`
- `docs/r02-d3-review-handoff.md`

## Source identities

- `r02_d3_contracts.py`:
  `978d4fcf2cb2775a40ac515276a4c0c69899284dc05096360b5a661b2ab2ef47`
- `r02_d3_preflight.py`:
  `2376c5a4773de506aa577387397e4f59a497e623b7cfc262edbbbf9b1deb32a7`
- `r02_d3_replay.py`:
  `bff977ef81e8ca8bcd828ab9b39bd2070cd761f9a22eee718adf412c05030850`
- `scripts/r02_d3_zero_call_preflight.py`:
  `ba29f5f7ce6d7bdf3dec3c7c3473c114774565f3551fb9763db861c8cdecc302`
- `test_r02_d3_preflight.py`:
  `42bb473bc01e5028ef8542beeff8bac964e58ff03e1b368db006651da5b677db`
- `test_r02_d3_replay.py`:
  `2c51571687ea8250a74234e4a0abb2aece2070f8a34ac65e2d4d6705e579863f`

Generated artifact hashes and sizes are recorded in
`docs/r02-d3-preflight-manifest.json`.

## Reproduction

```powershell
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_d3_preflight.py v2/research/overlay/test_r02_d3_replay.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_acceptance.py v2/research/overlay/test_r02_candidates.py v2/research/overlay/test_r02_audit_replay.py v2/research/overlay/test_r02_selector.py v2/research/overlay/test_r02_selection_audit_replay.py v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_statistics.py v2/research/overlay/test_r02_d3_preflight.py v2/research/overlay/test_r02_d3_replay.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay -q
.venv\Scripts\python.exe scripts/r02_d3_zero_call_preflight.py --repo-root C:\Users\User\Desktop\ai-hedge-fund-fresh --authorization C:\Users\User\Desktop\ai-hedge-fund-fresh\docs\r02-d3-provider-free-authorization.md --verify-existing
```

Expected:

- D3 focused: `15 passed`
- all R02 focused: `91 passed`
- full overlay: `218 passed`
- Pydantic JSON Schema generation: `61/61`
- replay `verified_artifacts=6`, `transport_recaptured=true`
- provider calls: `0`
- live executions: `0`
- micro-pilot executions: `0`

## Required review questions

1. Is the evaluation bootstrap seed derived from the complete domain-separated
   canonical preimage, with no outcome-dependent input or digest truncation?
2. Does the prompt reproduce the D2b selector-safe template exactly and embed
   one canonical safe payload without exposing forbidden fields?
3. Does the strict output schema preserve selected presented ID, integer
   confidence, and unique frozen reason-code constraints?
4. Is model `gpt-5.6-sol` selected only by sealed R01 continuity, with command
   identity mandatory, echo absence explicit, and any present mismatch fatal?
5. Does the zero-call snapshot bind the executable bytes, CLI version, auth
   mode, 92-feature catalog, disable list, and `exec --help` surface?
6. Can any non-help `codex exec` command enter the zero-call runner allowlist?
7. Is future live argv fixed to read-only/ephemeral/no-user-config/no-rules,
   high reasoning, web disabled, strict schema, and JSONL stdin?
8. Are the six micro-pilot fixtures selected only by stratum, trigger, K,
   fixture ID, and frame ordinal, with no hidden utility/headroom input?
9. Do attempted micro-pilot cases debit the full 55-attempt ITT budget and
   prohibit retries, replacements, and selective deletion?
10. Do 6/192,000 and 55/1,760,000 budgets reconcile exactly at 32,000 tokens per
    one-shot attempt with zero retry and zero incremental USD?
11. Are one micro-pilot fallback, five full-evaluation fail-closed attempts,
    zero unsettled attempts, and every listed hard-stop condition enforced as
    `INVALID_RUN` boundaries?
12. Does append-only persistence write the exact five-node order and graph last,
    while rejecting R01 roots and duplicate paths?
13. Does replay verify every stored hash/canonical byte, rebuild every contract,
    and recapture all five local transport commands byte-for-byte?
14. Are D1, accepted D2c source/artifact identities, the 162-file D2c frame, and
    the sealed 299-file R01 tree unchanged?
15. Do every source/generated-artifact hash and all zero-call/no-live literals
    match the manifest, with no path that authorizes or executes D3?

Report CRITICAL/HIGH/MEDIUM/LOW findings with file and line. State whether this
candidate is acceptable for user freeze acceptance. Do not infer D3 live
authorization from a passing review.
