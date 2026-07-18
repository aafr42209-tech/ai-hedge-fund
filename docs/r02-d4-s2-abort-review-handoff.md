# R02 D4-S2 aborted-frame independent review handoff

## Required verdict boundary

This is an abort review, not a frame-admission review. The only passing verdict is
`PASS_ABORT_S2_NO_RETRY`. Do **not** issue `PASS_PROVIDER_FREE_FRAME_SEALED`:
the single authorized generation process received `SIGTERM` at its 295,000 ms
orchestration limit after writing the 200 fixtures and frozen scan but before
writing `frame_manifest.json` or either docs-level manifest/seal.

The partial root is quarantined. Review must be read-only. Do not complete,
delete, rename, regenerate, replay, replace, or reuse it. Do not run a provider,
Codex exec, micro-pilot, LIVE path, statistical freeze, budget derivation,
commit, or push.

## Starting state

- Branch: `codex/llm-overlay-research-01`
- HEAD/upstream before S2 writes:
  `a563fb4e6e83a51662fa41c166eeb3fa5f1a52f0`
- Accepted design commit:
  `d9f984866c8775153d9c1ac1aea9b49fc9647635`
- S1 seed artifact SHA-256:
  `a05f3b2da66dfda6ba3369effa1734f8c760e6c1735db80306b07f51a8abeef5`
- Slot-0 resolved seed:
  `0716a1b9c13aec596b29776f48b3d8d1fc0a9afacc1c5010bd2cf2a9629d0621`
- Intended frame: `r02-d4-frame-0716a1b9c13a`, n=200 (150/50)
- Generation attempts: 1; retry/replacement: 0/0
- Current result: `ABORTED_UNSEALED_PARTIAL_FRAME_QUARANTINED`

## Expected hashes

| Item | SHA-256 |
|---|---|
| `docs/r02-d4-s2-frame-intent.json` | `2a51770ba7a202c1973e1895925553597f5d7cb14ccbf21fa5a270c1f93c98df` |
| `docs/r02-d4-s2-abort-diagnostic.json` | `6f404821a35096eafc1cba060d52faa9d3bf0652ddb49580e98d07bbfa455e35` |
| `docs/r02-d4-s2-zero-call-manifest.json` | `d665fd6972c39197a62b2f94d7e160b11ceb26bc9c79daa1c528619edc4ea20e` |
| partial `challenge_scan.json` | `a316b32b5856564118700f4dee79067ce38b257f24eec5f85bc29915926ada9f` |
| `v2/research/overlay/r02_d4_s2_frame.py` | `178e9b5d943d2062517dfd5be746968e135b4a4bc1248092f17960b00e9786c3` |
| `scripts/r02_d4_s2_frame_generate.py` | `60a65942b1e1dfc926cde245717caac4dbda4dcdbbd299d47b8c6f07cf70f39c` |
| `scripts/r02_d4_s2_frame_verify.py` | `89cb49ea88d083cbb03672f13c728579044c6b7618c61d985fd5f2002972f38f` |
| `v2/research/overlay/test_r02_d4_s2_frame.py` | `636e36d32019c720f6454bd50748b3e006bbb7887a5b9be8602aa9ba4bdafb69` |
| unchanged D2c builder | `bc2d3c64d04b4b47d8a4bee81da24bd02c411cb299f09fa15747a7871a7a8f40` |
| unchanged candidate generator | `29c13547230d1729d8b9cec637ccb13335fbcae52c1360e63718359d993a320e` |
| unchanged fixture generator | `732ca6ff358590edd856ba68bcb6cefb612246da9d81b97aa08d12db786eabfe` |

## Twelve skeptical checks

1. Confirm HEAD remains `a563fb4e...52f0`, the branch is
   `codex/llm-overlay-research-01`, and no S2 commit or push exists.
2. Recompute every byte hash in the table. A mismatch is blocking.
3. Re-run `verify_intent(...)` only. Confirm the accepted design, S1 seed
   artifact, slot-0 seed, fixed 150/50 counts, scan start 150, limit 4096,
   zero retry/replacement, and source pins.
4. Confirm the partial root contains exactly 201 files: 150 representative
   fixtures, 50 challenge fixtures, and `challenge_scan.json`. Confirm there
   are no missing or extra numbered fixtures.
5. Confirm all three seal locations are absent:
   `.research_artifacts/r02-d4-frame-0716a1b9c13a/frame_manifest.json`,
   `docs/r02-d4-s2-frame-manifest.json`, and
   `docs/r02-d4-s2-frame-seal.json`.
6. Recompute the partial root using
   `r02_d3_preflight._filesystem_tree`: 201 files,
   806,977 bytes, tree SHA-256
   `2f15d7c9f0ff2e3e2314714a00384e110c45b0c468586c7f567aec0e7524d132`.
7. Parse, but do not regenerate, `challenge_scan.json`. Require source indexes
   150 through 560 contiguous (411 records); disposition counts ADMITTED=50,
   NOT_TRIGGERED=351, NO_POSITIVE_CANDIDATE_HEADROOM=10; 50 admitted indexes
   must exactly match ADMITTED records; first/last admitted indexes 152/560.
8. Confirm the scan pins the accepted seed and exact admission rule
   `TRIGGER_TRUE_AND_AT_LEAST_TWO_DEDUPLICATED_CANDIDATES_AND_POSITIVE_HEADROOM`,
   with provider_calls=0, live_execution=false, frame_scan=true, and
   outcome_shopping_fields_used=false.
9. Confirm the nine predecessor artifact child trees equal the values in the
   zero-call manifest. The additive protected-root state must be 3,485 files,
   50,076,968 bytes, SHA-256
   `ff678a35ab36ef21607f21d67ed6e614f7d5645e11b4ea61f939c53825b95441`.
10. Confirm `docs/r02-d3-successor-provider-free-posthoc.json` remains byte
    SHA-256 `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
    and its verdict remains `SUPPORTED` without reclassification.
11. Inspect the new builder/generation/verification sources for provider,
    network, subprocess, Codex exec, LIVE, retry, replacement, or alternate
    seed/count paths. Confirm pre-generation tests recorded 53 passed and that
    no second generation process was launched.
12. Confirm the diagnostic does not treat payload completeness as a seal:
    statistical freeze, provider budget, provider/LIVE use, partial completion,
    and root reuse must all remain prohibited.

Do not run `scripts/r02_d4_s2_frame_generate.py`; that would be an unauthorized
retry. Do not run the full frame verifier against this root; its missing-seal
failure is already the admitted state and adds no evidence.

## Verdict format

If all checks reproduce, report:

`PASS_ABORT_S2_NO_RETRY`

Then list the three docs hashes, the partial tree tuple, scan tuple, unchanged
predecessor/D3 evidence, zero-call accounting, and explicit confirmation that
no seal exists. If any check fails, report `BLOCKING_FINDINGS` with the exact
file, field, expected value, and observed value.

## What a pass means

A pass accepts only the fail-closed abort record. It does not admit a frame and
does not authorize remediation. Any future attempt requires an independent
abort pass plus separate user authorization for a newly named attempt and a
new artifact root; the quarantined root must never be completed or reused.
