# R02 D4-S8 provider-free two-artifact LIVE-authorization freeze

## Review status

Provider-free freeze prepared. This is not the 69-case LIVE execution approval.
No production root was materialized. No Codex execution, provider call, LIVE
run, micro-pilot, retry, replacement, or resume occurred. Commit and push remain
outside the current authorization scope.

## Fixed identity

- run id: `r02-d4-s8-20260719`
- current S7 commit: `3efd3b82cdb813383211a18a3a19482f734782c7`
- S6 independent-review handoff digest: `00c180968a51e37c97966af3bea970c536fbca29efd2d0583f7da0283504d549`
- S7 independent-review handoff digest: `4c8530325ccf1758824ca1b709fbc0b4f7db45855e53670aaf7c1f6a6d5a99aa`
- S7 contract digest: `c2b4b729e77690c3f02d28de503d4172e038d19b7230c954b8f2e4b167deb2b1`
- accepted S6 implementation commit: `c88bde40015d88bf31f4af25587c339359971f2e`

## Canonical authorization artifacts

| Artifact | Path | SHA-256 |
|---|---|---|
| S6 LIVE authorization | `docs/r02-d4-s6-live-authorization.json` | `5eb08e1994add052cf7994f56add7a40df2ef8531bdba32afbed0c9f493178d4` |
| S7 LIVE authorization | `docs/r02-d4-s7-live-authorization.json` | `c05bf7a733f6b8985e54bcd5170f6534112b7ed28e8addecfba9d9a16c9a5042` |

Both files are strict, sorted-key, separator-minimized canonical JSON. The S7
artifact binds the exact S6 artifact bytes. Both artifacts bind the same run id,
indivisible `INDIVISIBLE_ALL_69_LIVE` scope, and false micro-pilot,
retry/replacement, and resume permissions.

## Frozen execution contract

- 69 eligible attempts, one continuous run, frame-ordinal ascending order.
- Aggregate cap: 2,208,000 tokens; reserve: 32,000 per attempt.
- Per-attempt timeout: 900,000 ms.
- Settled failure cap: 6.
- Micro-pilot: 0; retry: 0; replacement: 0; resume: 0.
- Production/audit root: `.research_artifacts/r02-d4-s6-r02-d4-s8-20260719`.
- Transport evidence root: `.research_artifacts/r02-d4-s7-transport-r02-d4-s8-20260719`.
- The roots are distinct, share the run id, and remain absent/not materialized.

## Provider-free verification

Run:

```text
.venv\Scripts\python.exe scripts\r02_d4_s8_provider_free_verify.py
```

Expected result:
`PASS_R02_D4_S8_PROVIDER_FREE_TWO_ARTIFACT_FREEZE` with provider calls,
Codex exec invocations, live runs, and root materializations all equal to zero.
Seven declared negative tests cover noncanonical bytes, run-id drift, S6 digest
drift, S6/S7 review or contract digest drift, all three forbidden capability
paths, a nonempty temporary root, and dirty/wrong repository state. They do not
touch either production root.

The verifier is reproducible both before and after the S8 commit. Before commit,
it accepts only the pinned base HEAD plus exactly these six untracked S8 files.
After commit, it accepts only a clean descendant whose complete diff from the
pinned base consists of exactly the same six S8 files.

## Required independent review checks

1. Recompute both artifact hashes from raw bytes; verify S7 binds S6.
2. Recompute the S6/S7 handoff digests and S7 contract digest.
3. Confirm repository state is either the exact six-file pre-commit state at
   `3efd3b82cdb813383211a18a3a19482f734782c7`, or a clean S8-only descendant.
4. Confirm both production roots are absent or empty and no provider/Codex call occurred.
5. Confirm the required order below and reject any earlier execution action.

## Explicit next order

1. S8 independent review.
2. S8 file commit and push.
3. Separate, explicit approval for the indivisible 69-case LIVE execution.
4. Only after that approval: production-root materialization, then Codex/provider execution.

Recommended separate approval text:

> R02 D4-S8 provider-free two-artifact LIVE-authorization freeze 작성을 승인합니다. S6/S7 canonical authorization artifacts와 현재 S7 commit·독립 검토 digest·contract hash, 동일 run_id, 빈 production roots, 69-attempt/2,208,000-token budget, 실행 순서·timeout·failure cap·NO_MICRO_PILOT·no-retry/replacement/resume 계약을 봉인하고 독립 검토 handoff까지 작성하세요. Production root materialization, Codex exec, provider 호출, LIVE 실행, retry/replacement/resume, 커밋·푸시는 승인하지 않습니다.

That text approves this freeze only. It does not approve the later 69-case LIVE
execution; that approval must be explicit and separate.
