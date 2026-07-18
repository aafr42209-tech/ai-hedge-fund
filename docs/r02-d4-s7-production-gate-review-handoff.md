# R02 D4-S7 Provider-Free Production Gate Review Handoff

## Review status

Provider-free production transport/entrypoint implementation only. S6 is
committed and pushed at
`c88bde40015d88bf31f4af25587c339359971f2e`. S7 is not staged, committed, or
pushed. No LIVE authorization artifact, production root, provider call, Codex
exec, micro-pilot, retry, replacement, or resume was created or performed.

Expected git state at handoff:

- branch: `codex/llm-overlay-research-01`;
- HEAD: `c88bde40015d88bf31f4af25587c339359971f2e`;
- upstream divergence: `0 0`;
- tracked diff: none;
- untracked files: the 12 S7 files in this handoff only.

## Byte identities

| Role | Relative path | SHA-256 |
|---|---|---|
| Contracts | `v2/research/overlay/r02_d4_s7_contracts.py` | `431d5d608bc8d0148ac49b7b4b8e7fd8648c5599e2237622e6bd1c6a1330f801` |
| Production transport | `v2/research/overlay/r02_d4_s7_transport.py` | `43dd65f05aafdbe7ec896db55ed4ae607de98638ffbb8c18d273cf3bb4b0388e` |
| Entrypoint gate | `v2/research/overlay/r02_d4_s7_entrypoint.py` | `4f84e67942d053662c1dfd260f7f2ed050999ca07bd974fd67d3a3fe27cd39c0` |
| Transport tests | `v2/research/overlay/test_r02_d4_s7_transport.py` | `280f675c3dd177e108883209b10196aa1fbc9aad5629ab6f0df58011fba89917` |
| Entrypoint tests | `v2/research/overlay/test_r02_d4_s7_entrypoint.py` | `be4a295c41fc48201ec86c26d90d5b16293c24d8a1c9e8a2286c027762ab8cc2` |
| Runtime output schema | `docs/r02-d4-s7-selector-output-schema.json` | `f8089e667cff113d600e3c9c726fbbff4f80c8f522804525e37d8693bbd36937` |
| Production-gate contract | `docs/r02-d4-s7-production-gate-contract.json` | `c2b4b729e77690c3f02d28de503d4172e038d19b7230c954b8f2e4b167deb2b1` |
| Design record | `docs/r02-d4-s7-production-transport-entrypoint-gate.md` | `8fa10fe8ec5a42d41eeadc9ce70f20e281345158753c165b8dfa732414c44a7b` |
| Focused tests | `docs/r02-d4-s7-focused-tests.json` | `31a2ae9421bb0b2ceac20e0906248ec6724f051df9164408958d8eb1973f3406` |
| Provider-free verifier | `scripts/r02_d4_s7_provider_free_verify.py` | `5fc0ad82b3667bda5f8936ad902cd6cdf0d5817a7b28f1f88120ed44ab1b9e9c` |
| Zero-call manifest | `docs/r02-d4-s7-zero-call-manifest.json` | `8320e52ead5e92510d441d5c1f0b8622aaaca72a996b637cfd7912ec5b1025bc` |

The review handoff itself is intentionally excluded from its own table.

## Required skeptical checks

### 1. Git and scope

Confirm HEAD/upstream/tracked state above and that exactly these 12 S7 files are
untracked. Confirm no S7 path appears in commit history.

### 2. Byte table and contract pins

Recompute all 11 table hashes. Parse the canonical production-gate contract,
recompute every `input_pins` and `source_pins` entry, and confirm the accepted
S6 commit is exactly `c88bde4...971f2e`.

### 3. S6 plan and execution contract

Independently rebuild the S6 provider-free plan. Confirm 69 unique eligible
cases in ascending frozen frame order, complete plan SHA
`188c971d...cffc9`, 32,000 tokens per reservation, 2,208,000 aggregate tokens,
900,000 ms timeout, six settled fail-closed maximum, and zero micro-pilot,
retry, replacement, and resume.

### 4. D3 execution identity bridge

Confirm the pinned D3 preregistration, model `gpt-5.6-sol`, high reasoning,
ChatGPT-subscription provider, executable hash `cbacbb97...ab0e4`, generated
feature disables, read-only/ephemeral/strict argv, and web-search false. If
re-running the five D3 zero-call local identity commands, confirm their hashes
reproduce the S5 snapshot and that no provider or Codex exec call occurs.

### 5. Dual schema identity

Confirm the historical D3 preregistration still carries `5466a24d...b2eca` and
the accepted successor export is byte-exact `f8089e66...6937`. Confirm S7 pins
both for their distinct roles and passes the absolute successor schema path to
`--output-schema`.

### 6. Prompt, command, and attempt binding

Using a fake process runner, independently verify system/user prompt bytes,
stdin, argv, selector-request hash, fixture ID, attempt ID, timeout, model, and
schema. Mutate each and require failure before a process call where applicable.
Confirm a duplicate attempt ID cannot cause a second process invocation.

### 7. Transport parsing and hard stops

Probe success, timeout, launch exception, nonzero exit, malformed JSONL,
duplicate/missing terminal usage, invalid usage subsets, tool use, and model
echo drift. Confirm unsettled cases return no scoreable raw response and enter
the existing S6 full-reserve hard stop; no retry path exists.

### 8. Full-capture persistence

Confirm exclusive-create plus fsync, full stdout/stderr bytes and hashes,
prompt/argv identities, process status, usage-event count, parse disposition,
and conservative provider-call accounting are persisted before a successful
transport result returns. Tamper evidence and require independent detection.

### 9. Closed S6 replay and separate S7 root

Prove that adding transport evidence beneath the S6 audit root is rejected as
an orphan by S6 replay. Confirm the implementation instead uses the exact
sibling root `.research_artifacts/r02-d4-s7-transport-{run_id}`, while S6 keeps
`.research_artifacts/r02-d4-s6-{run_id}`. Both must be absent/empty before
materialization; either nonempty root blocks retry/resume.

### 10. Two-artifact LIVE authorization

Use temp-only synthetic fixtures. Confirm the S7 artifact binds the exact S6
authorization bytes, accepted S6 review and commit, future accepted S7 commit
and independent review, and contract hash. Noncanonical, mismatched, missing,
or cross-run artifacts must fail before materialization. Confirm the authorized
S7 commit is compared with the actual Git HEAD and the worktree must be clean.
Confirm no real LIVE authorization artifact exists in the repository.

### 11. Entrypoint preparation vs materialization

Confirm `prepare_production_entrypoint` is read-only and returns both
materialization flags false. A fake capability must not materialize a root.
Confirm future `materialize` requires explicit LIVE process capability and
re-runs Git commit/clean state, current identity, and executable-byte
verification immediately before constructing the transport/S6 runner. Confirm
no standalone LIVE CLI exists.

### 12. Complete fake 69-case behavior

Run the S7 full fake test. Confirm 69 calls, 69 S7 evidence files, S6 terminal
`COMPLETE`, 2,208,000 tokens reserved, external provider calls zero, and a
successful independent S6 replay. All roots must be pytest temporary roots.

### 13. Frozen tests

Verify all 14 test-file hashes and collect exactly 150 tests from the manifest.
The author obtained exit code 0 in two deterministic partitions:

- predecessor frozen partition: `133 passed in 196.64s`;
- S7 transport partition: `9 passed in 150.47s`;
- S7 entrypoint partition: `8 passed in 52.17s`.

The manifest also supplies the single combined argv over the same 150 tests.

### 14. Provider-free verifier

Run:

```powershell
.venv\Scripts\python.exe scripts\r02_d4_s7_provider_free_verify.py
```

Require:
`PASS_S7_PROVIDER_FREE_PRODUCTION_GATE_REPRODUCED attempts=69 tokens=2208000 timeout_ms=900000 tests=150`.

### 15. Protected evidence and D3 verdict

Using `r02_d3_preflight._filesystem_tree`, confirm before/after protected tree:
3,687 files, 51,050,083 bytes, 11 child roots, SHA-256
`692ced91...f891`. Re-run D3 post-hoc `--verify-existing`; require byte hash
`1ab968ec...db73` and `confirmatory_result_preserved.verdict = SUPPORTED`.

### 16. Zero-call and final state

Confirm provider calls 0, Codex exec 0, local identity commands in authoring 0,
LIVE/micro-pilot false, retry/replacement/resume 0, no production S6/S7 roots,
no S7 commit/push, HEAD unchanged, upstream 0/0, tracked diff empty, and only
the 12 S7 files untracked.

## Verdict format

Return exactly one of:

- `PASS_PROVIDER_FREE_S7_PRODUCTION_GATE`; or
- `BLOCKING_FINDINGS` with each file, field/line, reproduction, impact, and
  minimum provider-free fix.

A pass accepts only this provider-free S7 draft. It does not authorize commit,
push, LIVE authorization creation, production-root materialization, Codex exec,
provider calls, micro-pilot, retry, replacement, resume, or the 69-case LIVE
run.
