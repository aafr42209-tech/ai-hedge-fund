# R02 D3 successor runner independent review handoff

## Requested decision

Review and either approve or reject the provider-free successor readiness at
the exact source pins below. This handoff does not authorize LIVE execution.

Expected disposition before a separate external authorization is:

`READY_FOR_INDEPENDENT_REVIEW_NOT_LIVE_AUTHORIZED`

## Immutable predecessor boundary

- accepted closeout commit: `22d0d7c6defe668e9a39ecb807230aec83d8b480`
- sealed predecessor readiness freeze:
  `a779a6b722870889128e58a9fbf4f149d78f88dc69535a7aabc7722a0e1957c6`
- sealed predecessor run: no retry, replacement, or relabeling
- predecessor selector schema:
  `5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca`
- predecessor raw audit replay remains valid at terminal sequence 14,
  `HARD_STOP / contradictory_terminal_status`

The historical `r02_contracts.py`, `r02_d3_contracts.py`, and
`r02_d3_preflight.py` bytes remain unchanged. The provider-strict schema is a
new successor overlay rather than a mutation of the accepted live-gate
prerequisites.

## Successor corrections

1. `r02_d3_successor_contracts.py` removes the historical default annotation
   from `schema_version` and requires all four root properties. It recursively
   enforces `required == properties`, unique required entries, and
   `additionalProperties: false` for every object schema.
2. The D3 runtime rejects a response that omits an explicit `schema_version`,
   even though the historical Pydantic payload model retains its default for
   predecessor reproducibility.
3. The LIVE ledger increments `external_provider_calls` immediately after the
   append-only `attempt_started` launch boundary. It no longer depends on
   successful response or token parsing.
4. Replay reconciles successor LIVE provider-call accounting with launched
   attempts. The sole compatibility exception is the exact sealed predecessor
   freeze above, whose known ledger undercount remains historical evidence.
5. Readiness replay regenerates the selector schema from pinned source,
   validates provider-strict rules, verifies the exact source role/path set,
   and compares manifest pins with freeze pins.

## Canonical readiness artifacts

- provider-free authorization SHA-256:
  `698d5c0f325149e4073c6a5efcee3824ee500c5443bba63b30819ce3e7529160`
- successor selector schema SHA-256:
  `f8089e667cff113d600e3c9c726fbbff4f80c8f522804525e37d8693bbd36937`
- successor readiness freeze SHA-256:
  `847506528aa68b32bc1a7ec5ef0261d369ee638addc7c1590a3180369751bd54`
- readiness manifest SHA-256:
  `95d25f24e1e6269ad78ac1252eef5a2c0468b4eb679f64610e2b7de466740596`
- readiness replay SHA-256:
  `49a8d0597278e08dac6a40b7219f2d93dbb6a9847ca3fde512ab3e107f9986b1`
- expected executable SHA-256:
  `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`

The strict schema has properties and required entries for exactly
`schema_version`, `selected_candidate_id`, `confidence`, and `reason_codes`.
The `schema_version` property has no default annotation.

## Source pins

| Role | Path | SHA-256 |
| --- | --- | --- |
| SELECTOR_RESPONSE_CONTRACT | `v2/research/overlay/r02_contracts.py` | `64a099560432152da875843d6cddb4d08acd3a402198adb14a5aec65ef0dab05` |
| D3_SUCCESSOR_SELECTOR_SCHEMA_EXPORT | `v2/research/overlay/r02_d3_successor_contracts.py` | `bcd42cc171e71771878113a1bac6e9ca49c9a52908f695f09e91c82bd1593e6c` |
| RUNNER_CONTRACTS | `v2/research/overlay/r02_d3_runner_contracts.py` | `d5a70029f98140ba5cb400034e72774b12549f30bcf040602e2a427ddd95d86f` |
| SELECTOR_TRANSPORT_ADAPTER | `v2/research/overlay/r02_d3_live_selector_adapter.py` | `497ee163b8fed658c10a95ed0cebbe9cd9a2f511ddf910ae7f630777df04e4f7` |
| FIFTY_FIVE_ATTEMPT_ORCHESTRATOR | `v2/research/overlay/r02_d3_live_orchestrator.py` | `90d136202d385b025e0bf34b3e13429ee7a062cf1c9023115d2765828e0a10b2` |
| APPEND_ONLY_AUDIT | `v2/research/overlay/r02_d3_live_audit.py` | `2ad2965216d6ede1bb9a96438a651c115b31d2a8456c1684dfff5ddcb20140fa` |
| FAIL_CLOSED_REPLAY | `v2/research/overlay/r02_d3_live_runner_replay.py` | `8d5459e9824d13ffd709f2baa0e1e7d47eda43e915d06806ef5dd8e86cdf0fa6` |
| ZERO_CALL_READINESS_SCRIPT | `scripts/r02_d3_live_runner_readiness.py` | `9c8bd23f6e9e6a4b98b28950ad25fd861e2fbb8d27ed64a0a001df10614333f6` |

## Provider-free verification results

- historical live-gate: `9 passed`
- successor runner focused: `33 passed`
- full overlay: `260 passed`
- successor readiness verify-existing: PASS
- verified source pins: 8
- provider calls: 0
- live execution: false
- micro-pilot executed: false
- full 6+49 executed: false

## Reproduction

Run from `C:\Users\User\Desktop\ai-hedge-fund-fresh`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay/test_r02_d3_live_gate.py
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay/test_r02_d3_live_runner.py
.\.venv\Scripts\python.exe -m pytest -q v2/research/overlay
.\.venv\Scripts\python.exe scripts/r02_d3_live_runner_readiness.py --repo-root . --authorization docs/r02-d3-successor-runner-provider-free-authorization.md --expected-executable-sha256 cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4 --verify-existing
git diff --check
git status --short
```

These commands are provider-free. Do not invoke `codex exec`, a LIVE runner,
the micro-pilot, or the indivisible 6+49 continuation during review.

## Reviewer checklist

1. Recompute all five readiness artifact hashes and all eight source pins.
2. Confirm the strict schema is the predecessor payload contract with only the
   required/default metadata correction described above.
3. Confirm missing `schema_version` fails locally and malformed strict schemas
   fail readiness replay.
4. Confirm a fake LIVE transport failure records one launched provider call,
   while OFFLINE_FAKE failures remain zero-call.
5. Confirm the predecessor replay exception is keyed only to the exact sealed
   predecessor freeze and cannot exempt the successor.
6. Confirm zero-call command labels and argv contain no provider-capable LIVE
   command.

## Remaining LIVE gate

Independent approval of this provider-free freeze is necessary but not
sufficient for LIVE. Any successor LIVE run requires a new external
authorization artifact, a new run identity, and new explicit user approval.
