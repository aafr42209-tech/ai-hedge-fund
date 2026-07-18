# R02 D4 provider-free replication-design independent-review handoff

Date: 2026-07-18

Status: **DRAFT COMPLETE — INDEPENDENT REVIEW REQUIRED — LIVE NO-GO**

## Scope

Review only the new provider-free design artifacts listed below. The package
defines an outcome-independent seed protocol, prospective sizing, the exact
parsimony comparator and test vectors, estimand and label precedence, and a
zero-call boundary manifest.

Explicitly excluded and unauthorized:

- resolving a frame seed or nonce reveal;
- generating or scanning a frame;
- provider calls or `codex exec`;
- micro-pilot or LIVE execution;
- LIVE authorization artifact creation;
- retry, replacement, or alternate seed selection;
- edits or reclassification of sealed R02 D3 evidence;
- ambiguity-engineered candidate construction;
- commit or push.

## Draft conclusion to challenge

The package proposes `n=200` with 150 representative and 50 challenge fixtures,
`M_min=57`, estimated-power target 85%, and Wilson-lower target 80% under the
8,000-bps low-SNR condition. `n=160` fails both new raw sizing scenarios;
`n=200` and `n=240` pass, so the smallest passing size is 200.

The primary scientific value is exact system-versus-baseline replication. The
review must confirm the expectation-management statement: preserving the exact
candidate generator makes renewed 100% LLM-parsimony agreement plausible, and
`NOT_IDENTIFIED_REDUNDANT_SELECTOR` is an expected valid mechanism result, not a
failed replication. Ambiguity engineering remains a separate future study.

## Files and hashes

| File | SHA-256 |
| --- | --- |
| `docs/r02-d4-replication-design.md` | `b8356c70f35ae2a6663acad57a5a346b5d5dfbe2b237433d38578b41b86b935c` |
| `docs/r02-d4-replication-design.json` | `784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900` |
| `docs/r02-d4-seed-contract.json` | `7b670cc9613a16e6f170b613a3b05a24529699c379bad14cad911736e34792fa` |
| `docs/r02-d4-prospective-power-sizing.json` | `9df82bc59865de6856cf2417925e771a4afc2142baaae912a853b0ad0f01be17` |
| `docs/r02-d4-parsimony-test-vectors.json` | `a304d36b31b570e7ae28a0a9ec89d4e8c7e2ef1ec0eda5b8c854b40e85f4ea77` |
| `docs/r02-d4-zero-call-manifest.json` | `a8d6dd9d12fda29c9cbcef6c3f41d8dafdfc8fb59d5f8857a90c41175a5f856b` |
| `v2/research/overlay/r02_d4_design.py` | `56cfb806c79baa768524c76c655907bc55934d421c0566740ee0f9c75e9ea4d6` |
| `v2/research/overlay/test_r02_d4_design.py` | `d82f1839a53d9f7a17aa81c002cf7422a83ce4c4b689cd29e83eac6f66905d15` |
| `scripts/r02_d4_design_verify.py` | `0c6ca2915b5885d1c6a1c2b32c1c7618af95de8e628de11dd17f3ace1ee1c86b` |

This handoff is intentionally not self-hashed.

## Required skeptical checks

1. **Starting-state drift**
   - Confirm branch and base `ad8857b74a2276b9eb4248801b156a8e08d88742`.
   - Rerun the sealed post-hoc `--verify-existing` command.
   - Confirm post-hoc SHA-256 remains
     `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`.
   - Rerun the original nine focused tests. Any mismatch is blocking; do not
     repair sealed evidence in place.

2. **Scope separation**
   - Confirm the exact LLM system, deterministic parsimony policy, incremental
     LLM contrast, and agreement endpoint are four separate outputs.
   - Confirm ambiguity-engineered candidates are excluded from D4.
   - Confirm secondary results cannot rescue or reverse the primary label.

3. **Expectation management**
   - Confirm the package makes system-versus-baseline replication the primary
     value.
   - Confirm 100% selector agreement and `NOT_IDENTIFIED_REDUNDANT_SELECTOR`
     are treated as expected, valid, non-null-identifying outcomes.

4. **Seed independence and anti-shopping**
   - Confirm every seed field is unresolved and no frame ID exists.
   - Confirm no D3 fixture ID, delta, utility, rank, or influence order is an
     allowed frame-seed preimage field.
   - Challenge the two-party commit/reveal ordering, single slot, zero retry,
     and abort semantics.
   - Confirm actual seed resolution requires later design acceptance plus
     separate frame-generation authorization.

5. **Sizing and power**
   - Recompute all 12 scenarios from source.
   - Confirm 1,000 outer trials, 2,000 within-stratum bootstrap resamples,
     fixed PCG64 seed, 8,000-bps low SNR, and 3:1 weighting.
   - Confirm gamma shape 1.85 uses only sealed aggregate diagnostics and does
     not replay individual deltas.
   - Confirm `n=160` fails, `n=200` and `n=240` pass both raw gates, and 200 is
     the smallest allowed passing size.
   - Confirm winsor scenarios are diagnostics, not substituted primary tests.
   - Challenge whether 85% estimated and 80% Wilson-lower targets are adequate.

6. **Information floor and budget boundary**
   - Recompute `M_min` as `[46,57,69]` for `[160,200,240]` and exact worst-case
     opportunity probabilities `[90.0568%,94.3424%,93.5090%]`.
   - Confirm the future provider-attempt cap remains a formula based on the
     not-yet-existing eligible count and does not authorize a provider call.

7. **Robust/fragile classification**
   - Confirm `INVALID_RUN` and low-information precedence.
   - Challenge the 5,000,000-e12 minimum margin and the all-case
     zero-nullification/leave-one-out requirements.
   - Confirm 5% and 10% winsor diagnostics qualify only D4 and cannot relabel D3.

8. **Parsimony comparator**
   - Verify lexicographic ordering by non-HOLD count, absolute quantity, and
     canonical ID.
   - Confirm the comparator is blind to role, position, cost, utility, fixture,
     and outcomes.
   - Rerun all eight positive vectors and four fail-closed classes.
   - Confirm malformed or duplicate candidate identities stop rather than fall
     back to a different comparator rule.

9. **Zero-call boundary**
   - Confirm design and verifier sources import no provider, network, process,
     or frame-builder capability.
   - Recompute the `.research_artifacts` inventory with
     `v2.research.overlay.r02_d3_preflight._filesystem_tree`. The recorded
     before/after values must remain 3,284 files, 49,269,991 bytes, SHA-256
     `3a7ed6ede78176affb13a2b49590ecfe49d5a7156a0c2467d4302021345c7279`.
   - Confirm no new audit root, seed artifact, frame, LIVE artifact, commit, or
     push exists.

## Read-only reproduction commands

```powershell
Set-Location C:\Users\User\Desktop\ai-hedge-fund-fresh

git status --short --branch
git rev-parse HEAD
git rev-list --left-right --count '@{upstream}...HEAD'

.venv\Scripts\python.exe scripts\r02_d3_successor_posthoc.py `
  --repo-root C:\Users\User\Desktop\ai-hedge-fund-fresh `
  --output C:\Users\User\Desktop\ai-hedge-fund-fresh\docs\r02-d3-successor-provider-free-posthoc.json `
  --verify-existing

.venv\Scripts\python.exe -m pytest -q `
  v2/research/overlay/test_r02_d3_posthoc_analysis.py `
  v2/research/overlay/test_r02_statistics.py

.venv\Scripts\python.exe -m pytest -q `
  v2/research/overlay/test_r02_d4_design.py

.venv\Scripts\python.exe scripts\r02_d4_design_verify.py `
  --repo-root C:\Users\User\Desktop\ai-hedge-fund-fresh
```

Expected D4 verifier terminal status:

```text
PASS_PROVIDER_FREE_DRAFT_REPRODUCED
```

## Required review disposition

Return one of:

- `PASS_PROVIDER_FREE_DESIGN` with reproduced hashes, sizing results, seed-zero
  state, and zero-call boundary; or
- `BLOCKING_FINDINGS` with exact file, field, and reason.

A pass accepts only the design draft. It does not authorize seed resolution,
frame generation or scan, provider calls, LIVE work, commit, or push.
