# R02 D4-S5 provider-free execution preflight/live-gate independent review handoff

Date: 2026-07-18

## Required verdict boundary

Expected passing verdict:

`PASS_PROVIDER_FREE_S5_EXECUTION_PREFLIGHT_LIVE_GATE_FREEZE`

This review covers only the provider-free execution-identity snapshot and
future live-gate contract. A pass does not authorize or implement a provider
runner, provider call, Codex exec, micro-pilot, LIVE, retry/replacement, resume,
LIVE authorization artifact, or commit/push of S5.

## Starting lineage

- Branch: `codex/llm-overlay-research-01`
- S5 base commit: `f81909f82f3641da4b89d1e04bc0705b178f5a59`
- Upstream divergence at authoring closeout: `0/0`
- S3 freeze: `3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449`
- S4 budget: `722eb1aee9e115c76990387f7baf8a19dbfd66226ebaae4060acf29f1bf74e70`
- S2A frame ID: `r02-d4-s2a-frame-0716a1b9c13a`
- Frame manifest: `368e01509b04a53928df2d729f0914dbd0c1ee14c5221a6e189fbf7b8bfa4ba1`
- Frame seal: `40aec915d3d24598ad2cbc46713a949b8c8ee5401d5768695b9be918b8bb5838`
- Frame tree: 202 files /
  `65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29`

All S5 files must remain uncommitted and unpushed during review.

## Expected byte hashes

| File | SHA-256 |
|---|---|
| `docs/r02-d4-s5-live-gate-freeze.json` | `d931edfaa347165975a0edcff1a256f81cd7d56fc7268d7a2a19bf97379f50ab` |
| `docs/r02-d4-s5-live-gate-freeze.md` | `a13087898bc7177dbdd254c2885d727e5b7873a638ba1300bb6a1b270350a94b` |
| `docs/r02-d4-s5-focused-tests.json` | `5252ee06f1f1cb588d703292a2ccb2ffc484d11ab98eb4344fc9b0eaf460a07d` |
| `docs/r02-d4-s5-execution-identity-snapshot.json` | `248f3683db276d45f275b5a2c236bc02909f6b7bf1be4ff56f6886573b2df5dc` |
| `docs/r02-d4-s5-zero-call-manifest.json` | `27ea0cd562c0ca8f7c6e21c3bea06ebdbb7fd8c301927661df2b6d684684a108` |
| `v2/research/overlay/r02_d4_s5_live_gate.py` | `e22096aa5c8370a0c34dc488cfbc370cd8d425b1da7f2b487865741768942084` |
| `v2/research/overlay/test_r02_d4_s5_live_gate.py` | `0b6b8b6a9487580426b7c1e636a395e84af79053c7d5973bc3aa960b308711af` |
| `scripts/r02_d4_s5_live_gate_verify.py` | `c467785ec61ab5d8aa8a4ba4e96ebe8e69a449531183ce41abc412eb49e5a267` |

The handoff is not self-hashed. Any table mismatch is blocking.

## Frozen decisions

- Execution identity: exact D3 provider/model/prompt/schema/executable/features.
- Eligible cases: 69, in ascending sealed frame ordinal.
- Execution-plan SHA-256:
  `a5e461a74a594a7f54a4751c8cb330ab4032c23ce25bdcbbd0dda6599c6af7d1`.
- Budget: 69 attempts, 32,000 tokens/attempt, 2,208,000 aggregate.
- Retry/replacement/unsettled/resume: zero.
- Per-attempt LIVE timeout: 900,000 ms.
- Settled fail-closed cap: 6; derived 86,956 ppm.
- Micro-pilot: none; attempt cap and case count zero.
- Future authorized scope: one uninterrupted 69-case pass, hard stops only.
- LIVE authorization: `NOT_AUTHORIZED`; runner implementation: absent.

## Fifteen skeptical checks

1. Confirm HEAD `f81909f82f3641da4b89d1e04bc0705b178f5a59`, upstream
   `0/0`, no tracked diff, and only the nine S5 files, including this handoff,
   untracked. Confirm no S5 commit or push.
2. Recompute all eight table hashes. Confirm the verifier pins freeze,
   focused-tests, and identity snapshot; freeze pins its source and
   focused-tests; source pins the identity snapshot and sealed inputs.
3. Recompute S2A manifest/seal/tree and S3/S4 hashes. Require 150/50,
   representative/challenge eligible 19/50, total 69, retry/replacement zero,
   and S4 attempts/tokens 69/2,208,000.
4. Re-run only the five D3-allowlisted local identity commands: version, login
   status, baseline features, post-disable features, and `exec --help`. Confirm
   command argv hashes, stdout/stderr hashes, exits, and capture-summary SHA
   `6cb79e5f61d68032a4565a2eec66b6083bd34a4b69a6164c38da07d9f8ae7b23`.
   These are provider-free local checks; do not run an actual `codex exec`.
5. Confirm Codex CLI `0.144.1`, executable SHA `cbacbb97...ab0e4`, ChatGPT
   login, feature catalog/definition hashes, four post-disable active features,
   provider/model/reasoning effort, prompt hashes, response-schema hash, and
   web-search false all match D3.
6. Independently derive the execution plan from sealed eligible cases sorted by
   frame ordinal. Require 69 entries; ordinals exactly as frozen; first
   `development-0002`/2; last `development-0560`/199; plan hash above. Confirm
   no permutation, batching reorder, retry, replacement, or resume.
7. Reproduce the budget ledger: initial attempts 69, tokens 2,208,000, full
   32,000 reservation before launch, attempt debit before launch, ITT retention,
   actual successful usage debit, full reserve on invalid/missing usage, and no
   attempt credit from unused reserve.
8. Reproduce timeout arithmetic: local identity 30 seconds, provider attempt
   900,000 ms, theoretical 69-attempt provider wait 62,100,000 ms. Confirm the
   first timeout is unsettled, debits attempt+reserve, and hard-stops without
   retry.
9. Reproduce the failure cap from the accepted D3 rate ceiling. Require
   `floor(6e6/69)=86,956 <= 90,909` and
   `floor(7e6/69)=101,449 > 90,909`; therefore 6 is the maximal non-loosening
   integer cap. Attempt cap is primary; ppm is derived reporting.
10. Confirm settled selector fallback produces zero e12 and increments the
    fail-closed counter; the seventh settled fallback invalidates and stops.
    Confirm identity, budget, timeout, missing usage, unsettled, audit, order,
    authorization, retry/replacement, and resume breaches are immediate hard
    stops rather than ordinary settled fallbacks.
11. Confirm `NO_MICRO_PILOT`: case/attempt caps zero, no interim outcome
    disclosure, no discretionary pause, no second authorization after start,
    no outcome-dependent continuation, and full 69-case one-shot scope only if
    separately authorized later.
12. Confirm S5 creates no production runner, audit/replay implementation,
    provider call, or LIVE artifact. A future provider-free runner phase must
    bind source/command pins, order, ledger, timeouts, fallback counter,
    append-only audit, and replay before any LIVE request.
13. Run the exact frozen argv from `docs/r02-d4-s5-focused-tests.json`.
    Require eleven test-file hashes, exactly 121 collected tests, and all 121
    passing. Inspect negative tests for order, budget, timeout, failure cap,
    micro-pilot, LIVE authorization, runner creation, retry, test count, and
    test-source hash tampering.
14. Run the read-only verifier. Require
    `PASS_S5_EXECUTION_PREFLIGHT_LIVE_GATE_REPRODUCED`, identity revalidated,
    plan hash, attempts/tokens 69/2,208,000, failure cap/rate 6/86,956, timeout
    900,000, micro-pilot 0, provider calls/Codex exec 0, and LIVE not authorized.
15. Recompute protected root before/after: 3,687 files / 51,050,083 bytes /
    `692ced9177f71cbe1af45a8f3ce06b7ec1c690fba87a8c7de254a1dfc834f891`,
    with all 11 child roots unchanged. Reconfirm D3 post-hoc
    `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
    and `SUPPORTED`. Require local identity commands 5, `exec --help` 1, actual
    Codex exec 0, provider 0, micro-pilot/LIVE false, retry/replacement 0.

## Reproduction commands

```powershell
.venv\Scripts\python.exe scripts\r02_d4_s5_live_gate_verify.py --repo-root .
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_d3_posthoc_analysis.py v2/research/overlay/test_r02_d4_design.py v2/research/overlay/test_r02_d4_s1_seed.py v2/research/overlay/test_r02_d4_s1_reveal.py v2/research/overlay/test_r02_d4_s1_resolve.py v2/research/overlay/test_r02_d4_s2_frame.py v2/research/overlay/test_r02_d4_s2a_frame.py v2/research/overlay/test_r02_d4_s3_freeze.py v2/research/overlay/test_r02_d4_s4_budget.py v2/research/overlay/test_r02_d4_s5_live_gate.py -q
```

Use only these provider-free paths. Do not run a provider, actual Codex exec,
micro-pilot, runner, or LIVE command.

## Verdict format and meaning

Report the eight hashes, sealed lineage, identity capture, order hash, ledger,
timeout, failure-cap derivation, no-micro decision, 121-test/verifier results,
protected-root/D3 invariance, and zero-call state. Return either
`PASS_PROVIDER_FREE_S5_EXECUTION_PREFLIGHT_LIVE_GATE_FREEZE` or blocking
findings with file, field, observed value, expected value, and minimal fix.

A pass accepts only this provider-free freeze. The next possible phase is a
separately authorized provider-free D4 runner/audit/replay implementation and
review. LIVE remains later and separately authorized.
