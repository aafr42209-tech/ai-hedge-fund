# R02 D3 Production Live-Runner Readiness — Independent Review Handoff

## Review status

Provider-free implementation only. Not staged, committed, pushed, or live
authorized. Provider calls, live executions, micro-pilot executions, and full
6+49 executions remain zero.

Base commit and accepted identities:

- base HEAD: `f55942308496afbf28a3a0ebea769b0fd753c8a2`
- accepted live-gate freeze: `b650b8379d36292eaafd1d2df29f0f400df486da94d8c8e74f22348db2cd7b07`
- accepted live-gate preflight: `b1ec1eba58bedb959279af60067ff2d51610a9faa4c81ed9efb1146fcb73b529`
- accepted executable pin: `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`
- runner-readiness freeze: `bcde3649af1ba52598d873cbd86c13ee1dbba582967c33ceb5d1a6b6b89164d2`

## New production source pins

- `RUNNER_CONTRACTS` — `v2/research/overlay/r02_d3_runner_contracts.py` — `e3768673c6b01bafe94219d0c06f9257bdbd59b280c888e89ab52b4d2a43d16c`
- `SELECTOR_TRANSPORT_ADAPTER` — `v2/research/overlay/r02_d3_live_selector_adapter.py` — `8b90569bde7f5ebed1689f4c93eb13982b16854c53b83c8787eeede51f253065`
- `FIFTY_FIVE_ATTEMPT_ORCHESTRATOR` — `v2/research/overlay/r02_d3_live_orchestrator.py` — `fd7bf726b90abfc401d57abf6798ff9c4db9771d582c57f073b077a53ebc385d`
- `APPEND_ONLY_AUDIT` — `v2/research/overlay/r02_d3_live_audit.py` — `2ad2965216d6ede1bb9a96438a651c115b31d2a8456c1684dfff5ddcb20140fa`
- `FAIL_CLOSED_REPLAY` — `v2/research/overlay/r02_d3_live_runner_replay.py` — `d8fd7dd6b1ab33d6d515f9509cc8281fba73a51af36229e9f0f8c32902a32d50`
- `ZERO_CALL_READINESS_SCRIPT` — `scripts/r02_d3_live_runner_readiness.py` — `9534a01b9a6fcc7428b6666cf26469250847e34e1600c09f8fe75bfeae005024`

## Generated readiness artifacts

- selector output schema: `5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca`
- readiness freeze: `bcde3649af1ba52598d873cbd86c13ee1dbba582967c33ceb5d1a6b6b89164d2`
- zero-call manifest: `e83471798b4b648532ef4666b1a454c3d2a5b9bebb08acdf312f14d0907364dc`
- readiness replay: `e68ec60b2179a09e48372fbfa0d5d5ebacfbbcc08202f648c7d67b74e0b2b045`
- provider-free authorization: `7f02148097f4b634fd7be3ce7550f96137b2a62ed1cf915370c186b685815fb0`

## Post-review fixes

- Invalid UTF-8 in the readiness manifest is converted to typed
  `R02D3ReplayError` instead of escaping as raw `UnicodeDecodeError`.
- The accepted-selection invariant uses explicit
  `R02D3OrchestratorError`; it remains active under `python -O`.

## Deferred LIVE-gate blockers

These are intentionally not closed by the provider-free readiness commit and
must be resolved before any LIVE authorization:

- prevent `OFFLINE_FAKE` from accepting a process runner capable of launching
  the frozen live argv;
- bind LIVE authorization to an externally supplied immutable authorization
  artifact rather than locally constructible booleans;
- terminalize duplicate `bind_attempt` rejection inside the audit chain;
- preserve actual over-reserve usage in the terminal ledger and validate usage
  upper bounds without uncaught model errors;
- expand E2E tamper coverage for duplicate attempts, anchor gaps, and missing
  terminal anchors, plus the exact 32,000-token boundary.

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
   `CodexProcessRunner` protocol.
9. The zero-call command map contains no `exec`, `--output-schema`, or live argv.
10. Accepted R01/D1/D2c/D3/live-gate files and the user-owned Claude handoff are
    unchanged.

## Provider-free validation commands

Run from `C:\Users\User\Desktop\ai-hedge-fund-fresh`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay/test_r02_d3_live_runner.py
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay/test_r02_d3_live_gate.py v2/research/overlay/test_r02_d3_preflight.py v2/research/overlay/test_r02_d3_replay.py
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
