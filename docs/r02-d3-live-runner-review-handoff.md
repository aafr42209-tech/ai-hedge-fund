# R02 D3 Production Live-Runner Readiness — Independent Review Handoff

## Review status

Provider-free LIVE-gate hardening only. Not staged, committed, pushed, or live
authorized. No external LIVE authorization artifact has been supplied. Provider
calls, live executions, micro-pilot executions, and full 6+49 executions remain
zero.

Base commit and accepted identities:

- base HEAD: `4f048df06c1b5c528dd048e8c6c313d3ba774b93`
- accepted live-gate freeze: `b650b8379d36292eaafd1d2df29f0f400df486da94d8c8e74f22348db2cd7b07`
- accepted live-gate preflight: `b1ec1eba58bedb959279af60067ff2d51610a9faa4c81ed9efb1146fcb73b529`
- accepted executable pin: `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`
- runner-readiness freeze: `a779a6b722870889128e58a9fbf4f149d78f88dc69535a7aabc7722a0e1957c6`

## New production source pins

- `RUNNER_CONTRACTS` — `v2/research/overlay/r02_d3_runner_contracts.py` — `4110fd3c2749d5fca533a50c0b6017d7aa8a999f21be8a99e36995324a74f628`
- `SELECTOR_TRANSPORT_ADAPTER` — `v2/research/overlay/r02_d3_live_selector_adapter.py` — `fa251e9308b6a245499802938cd8a41ff15618a6df8d43970c7858ea7c344b79`
- `FIFTY_FIVE_ATTEMPT_ORCHESTRATOR` — `v2/research/overlay/r02_d3_live_orchestrator.py` — `e7da7f5e9316eb840924dc5d246d68e2cb9ccf5055eec339db6288c305ddad1f`
- `APPEND_ONLY_AUDIT` — `v2/research/overlay/r02_d3_live_audit.py` — `2ad2965216d6ede1bb9a96438a651c115b31d2a8456c1684dfff5ddcb20140fa`
- `FAIL_CLOSED_REPLAY` — `v2/research/overlay/r02_d3_live_runner_replay.py` — `7b3b57b0d7744400aaf79a049f034c651a62ad27c7ef1b40c5b2029f76c0c1be`
- `ZERO_CALL_READINESS_SCRIPT` — `scripts/r02_d3_live_runner_readiness.py` — `6cffba8b80c1d408f1de1fb3998f89c6012f215b205d69262cd64918e55be8c4`

## Generated readiness artifacts

- selector output schema: `5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca`
- readiness freeze: `a779a6b722870889128e58a9fbf4f149d78f88dc69535a7aabc7722a0e1957c6`
- zero-call manifest: `5d5f6529744b28bb5936666326a8be19d8a0cf6d868e75d8b7409545345af8c0`
- readiness replay: `ccccd76c7e4fb0c9b915f6cde81310f1a43b4e7e57f44c3c3c49b38a9cc1a1b9`
- provider-free authorization: `7f02148097f4b634fd7be3ce7550f96137b2a62ed1cf915370c186b685815fb0`

## Post-review fixes

- Invalid UTF-8 in the readiness manifest is converted to typed
  `R02D3ReplayError` instead of escaping as raw `UnicodeDecodeError`.
- The accepted-selection invariant uses explicit
  `R02D3OrchestratorError`; it remains active under `python -O`.
- RUNNING checkpoint ledgers reconcile against their exact completed audit
  prefix, while terminal ledgers still reconcile against the complete graph.
  An episode-2 launch crash now replays and reaches
  `CRASH_AFTER_LAUNCH_UNSETTLED` sealing with zero resume calls.

## Provider-free LIVE-gate hardening under review

- `OFFLINE_FAKE` accepts only a runner declaring the `OFFLINE_FAKE` capability;
  a LIVE process capability or an unmarked runner is terminalized before launch.
- LIVE booleans cannot self-issue approval. A canonical external authorization
  artifact must be supplied outside repository/audit roots, match the run and
  freeze identities, and match the exact `authorization_sha256`. Its bytes are
  rechecked immediately before every run or resume.
- duplicate `bind_attempt` and runner-capability rejection create typed
  `prelaunch_failure`, `run_ledger`, and `run_terminal` audit nodes without a
  second process call.
- actual usage above the 32,000 reserve is preserved in settlement and terminal
  ledger values. Values beyond the signed 64-bit auditable bound become typed
  `USAGE_VALUE_OUT_OF_RANGE` unsettled hard stops rather than raw model errors.
- E2E coverage now includes duplicate attempt identities, anchor gaps, missing
  terminal anchors, the exact 32,000 boundary, over-reserve accounting, runner
  capability mismatch, and authorization artifact tamper/recheck.
- readiness refresh uses an explicit atomic replacement path; verification-only
  behavior remains the default.

No LIVE approval exists after these changes. A future LIVE run still requires a
separately supplied external artifact approving the indivisible 6+49 scope.

Operational scope notes:

- a crash between readiness temporary-file write and atomic replace leaves a
  fail-closed `.{name}.tmp`; an operator must inspect and remove that stale file
  before an explicit refresh retry;
- external authorization bytes are rechecked at each `run()`/resume entry, not
  between individual attempts. Mid-run authorization revocation is not part of
  this indivisible 6+49 contract.

## Required review scope

Review every new source, `test_r02_d3_live_runner.py`, and all new readiness
documents. Confirm:

1. The adapter reuses only the pinned capture/process protocol and strict JSONL
   parser, not R01 run identity or R01 acquisition semantics.
2. `render_live_argv`, the frozen prompt, and canonical selector output schema
   are used exactly; stdin contains no text beyond the frozen prompt.
3. The first six attempts are the frozen micro cases and, absent a hard stop,
   the remaining 49 run automatically in frame order. Utility outcomes never
   enter the continuation decision.
4. Reservation is persisted before `attempt_started`; a launched identity can
   never be called twice; missing/malformed usage debits 32,000 tokens and
   creates an unsettled hard stop; usage above 32,000 marks
   `INVALID_RUN_BUDGET_BREACH`.
5. Retry, replacement, case deletion, post-six discretionary pause, and second
   authorization are structurally unavailable.
6. Every attempt remains in ITT, and every selector fallback executes baseline
   with paired delta zero.
7. The append-only payload/node/checkpoint chain rejects tampering, gaps,
   partial files, orphan files, duplicate attempt identities, and missing
   terminal anchors.
8. No new production source directly imports network/provider/subprocess
   capabilities. The only runtime process capability is the injected
   `CodexProcessRunner` protocol wrapped by an explicit LIVE-only capability.
9. The zero-call command map contains no `exec`, `--output-schema`, or live argv.
10. Accepted R01/D1/D2c/D3/live-gate files are unchanged. The user-owned D2b
    Claude handoff was retired by its owner after the D2b review concluded.
11. LIVE construction and execution require exact external canonical artifact
    bytes outside repository/audit roots; locally set approval booleans and
    tampered bytes fail closed before any process call.

## Provider-free validation observed

- hardening target suite: `30 passed` (included in the full overlay run)
- full overlay suite: `257 passed`
- readiness replay: 6 source pins verified; accepted live-gate, executable,
  prompt/schema, freeze/manifest, and zero-call exclusions matched
- counters: provider calls `0`; live/micro/6+49 executions `0`

## Provider-free validation commands

Run from `C:\Users\User\Desktop\ai-hedge-fund-fresh`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay/test_r02_d3_live_runner.py
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay/test_r02_d3_live_gate.py v2/research/overlay/test_r02_d3_preflight.py v2/research/overlay/test_r02_d3_replay.py
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay
.\.venv\Scripts\python.exe scripts/r02_d3_live_runner_readiness.py --repo-root . --authorization docs/r02-d3-live-runner-provider-free-authorization.md --expected-executable-sha256 cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4 --verify-existing
git diff --check
git status --short
```

These commands are provider-free. Do not invoke `codex exec`, a live runner,
the micro-pilot, or any 6+49 continuation.

## Required reviewer response

Return findings first, ordered by severity. Use `P0`–`P3`, exact file and line,
failure mode, and a concrete fix. Then give explicit judgments for:

- accepted freeze preservation;
- adapter contract correctness;
- budget/crash/resume fail-closed behavior;
- append-only replay integrity;
- zero-call readiness;
- provider/live authorization status.

If no findings remain, state: `APPROVED FOR PROVIDER-FREE RUNNER READINESS ONLY`.
Do not state or imply approval for a provider call or live 6+49 run.
