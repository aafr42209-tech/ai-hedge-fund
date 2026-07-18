# R02 D4-S4 provider-free provider-budget independent review handoff

Date: 2026-07-18

## Required verdict boundary

This handoff requests independent review of the provider-free numeric budget
freeze only. The expected passing verdict is:

`PASS_PROVIDER_FREE_S4_PROVIDER_BUDGET_FREEZE`

A pass does not authorize provider access, Codex exec, micro-pilot, LIVE
authorization or execution, retry/replacement, provider preflight, or
commit/push of the S4 draft. It does not modify or reclassify R02 D3.

## Starting lineage

- Branch: `codex/llm-overlay-research-01`
- S4 base commit: `277d4e4d8f67f46572df073413c21b49f551f189`
- Upstream divergence at authoring closeout: `0/0`
- S3 freeze SHA-256:
  `3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449`
- Frame ID: `r02-d4-s2a-frame-0716a1b9c13a`
- S2A manifest SHA-256:
  `368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1`
- S2A seal SHA-256:
  `40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838`
- S2A tree: 202 files /
  `65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29`
- Sealed selector-eligible count: 69.

All S4 files listed below must remain uncommitted and unpushed during review.

## Expected byte hashes

| File | SHA-256 |
|---|---|
| `docs/r02-d4-s4-provider-budget-freeze.json` | `722eb1aee9e115c76990387f7baf8a19dbfd66226ebaae4060acf29f1bf74e70` |
| `docs/r02-d4-s4-provider-budget-freeze.md` | `c4f0a8c655fdcfed09b7b59fa183770ac6876c781805f618f9548d4622ae9902` |
| `docs/r02-d4-s4-focused-tests.json` | `c1505d9e36b02bf1c4bb6263a2811ab338bc35278cb563bec8942ea445fe58e8` |
| `docs/r02-d4-s4-zero-call-manifest.json` | `1692984f7a3c3205990492956d294fb49b6751d472652fb9fc8d3dfcdd4df1e5` |
| `v2/research/overlay/r02_d4_s4_budget.py` | `8e9f3ca75d448ab69a1a0f21c810dd112e75c015673ce5bb1cc3a2c52a1b7a19` |
| `v2/research/overlay/test_r02_d4_s4_budget.py` | `94d24c1668d8c87514949ae03a91a99e14881554f1b11b0e1a04ad9b8c5b8650` |
| `scripts/r02_d4_s4_budget_verify.py` | `2ebaf55349be1fc3e705b1623dcd9ab957cc7835ebc46394b9697b8fb3361523` |

The handoff is not self-hashed. Any table mismatch is blocking.

## Frozen budget

| Quantity | Required value |
|---|---:|
| Eligible episodes | 69 |
| Ineligible episodes | 131 |
| Attempts per eligible episode | 1 |
| Retry cap | 0 |
| Replacement cap | 0 |
| Unsettled-attempt cap | 0 |
| Provider-attempt cap | 69 |
| Per-attempt token reserve | 32,000 |
| Aggregate token cap | 2,208,000 |
| Incremental USD cap | 0 |
| Maximum draft prompt UTF-8 bytes | 1,842 |
| Maximum canonical selector payload bytes | 1,314 |

The exact arithmetic is `69 × 1 × 32,000 = 2,208,000`. Ineligible fixtures
receive no provider-attempt allowance. The byte measurements are evidence only
and do not reduce the token reserve.

## Thirteen skeptical checks

1. Confirm branch, HEAD, and upstream. Require HEAD
   `277d4e4d8f67f46572df073413c21b49f551f189`, upstream `0/0`, no tracked
   diff, and only the eight S4 draft files, including this handoff, untracked.
   Confirm there is no S4 commit or push.
2. Recompute all seven byte hashes in the table. Confirm the verifier pins the
   budget freeze and focused-test manifest; confirm the freeze pins its source
   and focused-test manifest.
3. Recompute all sealed input hashes. Require the exact S2A frame ID, 150/50
   composition, 19/50 eligible counts, total 69, manifest/seal identities, and
   202-file tree hash above. Confirm S3 requires the later budget to use 69.
4. Exercise `verify_generation_retry_contract` with independent mutations.
   Require intent `generation_attempt_cap=1`; manifest and seal
   `frame_generation_count=1`; manifest and seal `retry_count=0`; manifest and
   seal `replacement_count=0`. Specifically mutate `seal.retry_count` to 1 and
   require `R02D4S4BudgetError`. This closes the S3 LOW observation.
5. Reconstruct `R02ProviderBudgetFreeze`. Require eligible count 69,
   provider-attempt cap 69, one attempt per eligible case, retry zero, 32,000
   reserve, aggregate cap 2,208,000, and incremental USD cap zero. Mutate the
   attempt cap and aggregate cap independently and require typed validation
   failure.
6. Independently recompute request-size evidence over all 69 sealed eligible
   fixtures using `prepare_provider_free_episode` and
   `build_selector_request`. Require maximum prompt bytes 1,842 and canonical
   selector-payload bytes 1,314. Confirm no provider process is started and the
   32,000 reserve is not reduced by this evidence.
7. Confirm token accounting exactly: `input_tokens + output_tokens`; cached
   input is not subtracted; reasoning output is not added twice; exactly one
   terminal usage event; missing/invalid usage debits the full 32,000 reserve
   and hard-stops unsettled; over-reserve usage is an invalid-run budget breach.
8. Confirm reservation/debit ordering: one attempt slot and the full 32,000
   reservation must fit before launch, the attempt slot is debited before
   launch, attempted cases remain in ITT, no unused reservation creates another
   attempt, and exhaustion hard-stops without retry or replacement.
9. Confirm outcome independence. Budget inputs must be only the sealed count,
   accepted one-attempt/zero-retry formula, 32,000 reserve, and structural
   provider-free request-size evidence. No individual provider outputs or
   selector outcomes may have been used.
10. Confirm the D3 provider/model/prompt/output-schema reference is byte-pinned
    but reference-only. This S4 freeze must not select or execute a provider.
    Confirm executable/features, identity, frame order, audit persistence,
    failure-rate/continuation, and any micro-pilot decision remain requirements
    for a separately reviewed future gate.
11. Run the exact argv in `docs/r02-d4-s4-focused-tests.json`. Require ten test
    files, every source hash matching, exactly 97 collected tests, and 97
    passing. Inspect the S4 negative tests for generation count, manifest/seal
    retry and replacement counts, attempt/token arithmetic, focused-test count,
    and focused-test source hash.
12. Run the read-only verifier with `--repo-root .`. Require
    `PASS_S4_PROVIDER_BUDGET_FREEZE_REPRODUCED`, attempts 69, aggregate tokens
    2,208,000, prompt/payload bytes 1,842/1,314, and
    `seal_retry_count_verified=true`. Inspect S4 sources for provider, network,
    subprocess, Codex exec, micro-pilot, or LIVE execution paths.
13. Recompute the protected root with
    `r02_d3_preflight._filesystem_tree`. Require before/after 3,687 files /
    51,050,083 bytes /
    `692ced9177f71cbe1af45a8f3ce06b7ec1c690fba87a8c7de254a1dfc834f891`
    and all 11 child roots unchanged. Reconfirm D3 post-hoc
    `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
    and verdict `SUPPORTED`. Require provider calls/Codex exec 0,
    micro-pilot/LIVE false, retry/replacement 0, and no S4 commit/push.

## Reproduction commands

Run only read-only verification from the repository root:

```powershell
.venv\Scripts\python.exe scripts\r02_d4_s4_budget_verify.py --repo-root .
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_d3_posthoc_analysis.py v2/research/overlay/test_r02_d4_design.py v2/research/overlay/test_r02_d4_s1_seed.py v2/research/overlay/test_r02_d4_s1_reveal.py v2/research/overlay/test_r02_d4_s1_resolve.py v2/research/overlay/test_r02_d4_s2_frame.py v2/research/overlay/test_r02_d4_s2a_frame.py v2/research/overlay/test_r02_d4_s3_freeze.py v2/research/overlay/test_r02_d4_s4_budget.py -q
```

Do not run provider preflight, provider, Codex exec, micro-pilot, or LIVE paths.

## Verdict format

Report:

- all seven byte hashes;
- sealed frame and eligible-count reproduction;
- retry/replacement field-level and negative-test results;
- exact budget arithmetic and request-size evidence;
- token reservation/debit contract reproduction;
- exact 97-test and verifier results;
- protected-root and D3 invariance;
- zero-call/no-S4-commit-push confirmation;
- either `PASS_PROVIDER_FREE_S4_PROVIDER_BUDGET_FREEZE` or blocking findings
  with file, field, observed value, expected value, and minimal fix.

## What a pass means

A pass accepts only the provider-free S4 numeric budget freeze. A later
provider preflight or LIVE authorization requires separate user authorization,
new artifacts, and independent review. No part of this handoff grants that
authority.
