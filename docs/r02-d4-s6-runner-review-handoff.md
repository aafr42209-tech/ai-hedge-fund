# R02 D4-S6 provider-free runner/audit/replay review handoff

## Review status and boundary

Provider-free implementation draft only. S5's accepted nine files were committed
and pushed as `bf8c293ab656be915b34c392133d77f3b8e748b2`; S6 is entirely untracked and
uncommitted. No provider call, Codex exec, production artifact-root execution,
micro-pilot, LIVE execution, retry, replacement, resume, S6 commit, or S6 push was
performed. No LIVE authorization artifact exists.

The S6 deliverable is the runner state machine, append-only audit, and independent
replay boundary. It intentionally contains only an injected transport protocol and
an `OFFLINE_FAKE` test implementation. A production provider adapter and production
entrypoint are not part of this approval and do not exist in the draft.

Accepted anchors:

- HEAD/base commit: `bf8c293ab656be915b34c392133d77f3b8e748b2`
- S5 LIVE-gate freeze: `d931edfaa347165975a0edcff1a256f81cd7d56fc7268d7a2a19bf97379f50ab`
- S5 identity snapshot: `248f3683db276d45f275b5a2c236bc02909f6b7bf1be4ff56f6886573b2df5dc`
- S4 budget freeze: `722eb1aee9e115c76990387f7baf8a19dbfd66226ebaae4060acf29f1bf74e70`
- S2A manifest/seal: `368e0150…4ba1` / `40aec915…5838`
- S2A tree: 202 files / `65c0acc67c2987997d3dfac8ce4fb861ddf4f439e7a4ce59c1eab79ac5d6ea29`
- S5 execution-plan digest: `a5e461a74a594a7f54a4751c8cb330ab4032c23ce25bdcbbd0dda6599c6af7d1`
- S6 full prepared-plan digest: `188c971db338d5456c72a1e6e71801119dd8f992dd90fd86c3952f09121cffc9`

## Draft byte identities

| File | SHA-256 |
|---|---|
| `docs/r02-d4-s6-runner-contract.json` | `edea01bf2dc6b3c110cf780bc5c774266871ae06b8d716685965fadf34f2f26f` |
| `docs/r02-d4-s6-runner-implementation.md` | `0c42f74513bb3432ffce0a2721195ecd7882a038f2aa2eaf63a3adeaab6da20e` |
| `docs/r02-d4-s6-focused-tests.json` | `63ca78cfcc61017044319f57578fef364388def02b0717cb5eaa6cd131c3c82b` |
| `docs/r02-d4-s6-zero-call-manifest.json` | `7b95ac842f761c532d117fc0182cb0f5f8069ea706b5ff94ac69975ba2772832` |
| `scripts/r02_d4_s6_verify.py` | `fc968f66b68fbc701fea3300c8a25df6e8554d3da53de56b9189b884174cf5d7` |
| `v2/research/overlay/r02_d4_s6_contracts.py` | `9cc3e3dcc07d635555729ba7d19800e349658a259e8592b0bddb52963d7cc433` |
| `v2/research/overlay/r02_d4_s6_audit.py` | `935cf31e779da3fe1b7d5b0e381080af5c9d3952e075b1bd7a92c495ee03971b` |
| `v2/research/overlay/r02_d4_s6_runner.py` | `8b33288f21a2b85825c5f101a40c5f0f1c7170cad0437fa342c5c255049e3eac` |
| `v2/research/overlay/r02_d4_s6_replay.py` | `eb22acbfa40917c3465fa2060dca0879d4f0b1decf32ba66c64e83db7ef1cd78` |
| `v2/research/overlay/test_r02_d4_s6_runner.py` | `285cbae5d920cf99433b324ffa45490a83a77d5a04121c8f6ec936f0966b5ceb` |

The handoff deliberately does not self-pin its own hash.

## Mandatory skeptical checks

Report `BLOCKING_FINDINGS` if any item fails. A PASS accepts only the provider-free
S6 draft.

1. **Git scope.** Confirm HEAD is the base commit above, upstream is `0/0`, tracked
   diff is empty, and exactly the eleven named S6 files (the ten in the table plus
   this handoff) are untracked. Confirm no S6 commit exists.
2. **Byte identities.** Recompute all ten table hashes. Confirm the contract JSON
   pins the four production source hashes and the zero-call manifest pins all nine
   non-handoff draft inputs.
3. **Accepted-input replay.** Recompute S5, S4, S3, S2A manifest/seal, frame-tree,
   execution-identity, and source pins. Confirm S2A remains 150/50 with 19/50
   eligible, total 69, and retry/replacement counts zero.
4. **Exact plan.** Independently rebuild the eligible cases by ascending frame
   ordinal. Confirm 69 unique cases, first `development-0002`/2, last
   `development-0560`/199, S5 plan hash `a5e461a7…f7d1`, and the complete prepared
   request plan hash `188c971d…ffc9`. Mutate an ordinal, fixture hash, preparation
   hash, or request hash and require rejection before transport.
5. **Authorization and capability boundary.** Confirm deterministic offline-fake
   authorization cannot carry provider, production-root, all-69 LIVE, micro-pilot,
   retry, replacement, or resume authority. Confirm in-memory LIVE flags are
   insufficient: a byte-identical canonical external authorization file is
   required before transport. Confirm capability mismatch stops before any call.
6. **Artifact-root boundary.** Confirm offline fake roots inside the repository or
   `.research_artifacts` are rejected before transport. Confirm every test and the
   verifier use only pytest/tempfile roots. Confirm no `r02-d4-s6-*` production root
   exists. Confirm any pre-existing file rejects a second run, retry, or resume.
7. **Attempt and token ledger.** Reproduce 69 pre-launch reservations of 32,000,
   aggregate 2,208,000. Confirm the reservation and `attempt_started` nodes persist
   before each transport invocation, attempted cases remain ITT, successful debit
   is exactly input plus output, and unused reserve never creates attempt credit.
8. **Timeout and usage.** Confirm the transport receives exactly 900,000 ms each
   time. Timeout, nonzero exit, launch error, missing/duplicate/invalid usage, or
   invalid subset arithmetic must debit the full 32,000 and hard-stop unsettled.
   Usage above 32,000 must hard-stop as invalid budget. No later call is allowed.
9. **Settled fallback cap.** Drive six settled parse/acceptance fallbacks and confirm
   continuation with delta zero. Drive the seventh and confirm
   `SETTLED_FAIL_CLOSED_COUNT_WOULD_EXCEED_6`, invalid terminal status, seven ITT
   attempts, and no eighth transport invocation.
10. **NO_MICRO_PILOT and continuation.** Confirm micro count/cap remains zero,
    utility outcomes are persisted only for terminal analysis and never consulted by
    continuation, there is no interim disclosure or second authorization, and only
    the ten S5 hard stops can prevent the next frozen case.
11. **Append-only graph.** For every append verify canonical payload, node, and full
    checkpoint anchor are exclusive writes with `fsync`; verify sequence, previous
    hash, payload reference, node history, and terminal structure. A complete run
    must have 418 nodes and 1,254 files under the temporary audit root.
12. **Independent replay and tamper rejection.** Replay without the runner's cached
    prepared data. Rebuild the sealed inputs, recompute settled selection,
    validation, paired utility, counters, continuation, and terminal ledger. Require
    failure for byte tamper, noncanonical JSON, missing/orphan files, reordered or
    duplicate identities, checkpoint gaps, and terminal drift.
13. **Frozen tests.** Recompute every test-source hash, collect exactly 133 tests,
    and execute the exact manifest argv. Expected: `133 passed`. Confirm the 12 S6
    scenarios use fake transport and temporary roots only.
14. **Verifier.** Run `scripts/r02_d4_s6_verify.py`. Expected:
    `PASS_S6_PROVIDER_FREE_RUNNER_AUDIT_REPLAY_REPRODUCED`, 69 attempts,
    2,208,000 reserved tokens, 418 nodes, provider 0, Codex exec 0, LIVE false.
15. **Protected evidence and zero-call closeout.** Recompute `.research_artifacts`
    before/after as 3,687 files / 51,050,083 bytes /
    `692ced9177f71cbe1af45a8f3ce06b7ec1c690fba87a8c7de254a1dfc834f891`
    with `r02_d3_preflight._filesystem_tree`. Confirm all 11 child roots are
    unchanged, D3 post-hoc remains `1ab968ec…db73`, verdict remains `SUPPORTED`, and
    provider/Codex exec/LIVE/micro/retry/replacement/resume/S6 commit/push are zero.

## Reproduction

From the repository root:

```powershell
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_d4_s6_runner.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_d3_posthoc_analysis.py v2/research/overlay/test_r02_d4_design.py v2/research/overlay/test_r02_d4_s1_seed.py v2/research/overlay/test_r02_d4_s1_reveal.py v2/research/overlay/test_r02_d4_s1_resolve.py v2/research/overlay/test_r02_d4_s2_frame.py v2/research/overlay/test_r02_d4_s2a_frame.py v2/research/overlay/test_r02_d4_s3_freeze.py v2/research/overlay/test_r02_d4_s4_budget.py v2/research/overlay/test_r02_d4_s5_live_gate.py v2/research/overlay/test_r02_d4_s6_runner.py -q
.venv\Scripts\python.exe scripts/r02_d4_s6_verify.py
git diff --check
```

Observed authoring results:

- S6 focused: `12 passed in 70.25s`
- frozen full set: `133 passed in 142.94s`
- verifier: `PASS_S6_PROVIDER_FREE_RUNNER_AUDIT_REPLAY_REPRODUCED attempts=69 reserved_tokens=2208000 nodes=418 provider_calls=0 codex_exec=0 live=false`

## Required verdict format

- Success: `PASS_PROVIDER_FREE_S6_RUNNER_AUDIT_REPLAY`
- Failure: `BLOCKING_FINDINGS <count>` followed by exact file, field or line, observed
  value, expected value, impact, and minimal correction.

A PASS does not authorize commit/push, a provider adapter, production entrypoint,
LIVE authorization artifact, provider call, Codex exec, production artifact-root
execution, micro-pilot, retry, replacement, or resume. If accepted, the next action
requires a separate user decision: first commit/push S6, then separately scope any
provider-free production transport/entrypoint gate. Do not request or perform LIVE
execution from this handoff.
