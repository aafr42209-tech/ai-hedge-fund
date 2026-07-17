# R02 D2b provider-free implementation review handoff

Date: 2026-07-17

Review status: `UNCOMMITTED_REVIEW_CANDIDATE`

Base commit: `7f9a998a32bf6835fd5ef6b14ebc79d674727128`

Branch: `codex/llm-overlay-research-01`

## Scope and fixed identities

This review covers only the authorized D2b scripted selector, deterministic
acceptance gate, triggered execution and paired scoring, accounting, append-only
audit graph, and replay implementation.

- D1 freeze SHA-256:
  `2d5961806b5051ff56c874b8b05933df014136bacb98717c4846f2b48f645778`
- D1 manifest SHA-256:
  `81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf`
- D2a base commit:
  `7f9a998a32bf6835fd5ef6b14ebc79d674727128`

The selector prompt is deliberately `DRAFT_NOT_FROZEN`. Reviewing this change
does not freeze its wording.

## Review files

Modified:

- `v2/research/overlay/r02_contracts.py`
- `v2/research/overlay/r02_audit.py`
- `v2/research/overlay/r02_replay.py`

New:

- `v2/research/overlay/r02_selector.py`
- `v2/research/overlay/test_r02_selector.py`
- `v2/research/overlay/test_r02_selection_audit_replay.py`
- `docs/r02-d2b-provider-free-authorization.md`
- `docs/r02-d2b-provider-free-implementation.md`
- `docs/r02-d2b-review-handoff.md`

The D1 freeze, D1 vectors and manifest, D2a candidate generator, and every R01
artifact are excluded and must remain byte-identical.

Production module SHA-256 values for this review candidate:

- `r02_contracts.py`:
  `64a099560432152da875843d6cddb4d08acd3a402198adb14a5aec65ef0dab05`
- `r02_selector.py`:
  `17485e8c5c0a547ebaad63694682eadfedfb33d0305e394773f6840d952d9192`
- `r02_audit.py`:
  `b3a365838b11b11211423c8a76e352d058357ff2b669414b9a5d94da1e755626`
- `r02_replay.py`:
  `19d9661228c43357d91975e9effe7a538e92c3f06128e840e4a32944e4f31a6d`

## Reproduction commands

From the repository root on Windows:

```powershell
git status --short --branch
git diff --check
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_selector.py v2/research/overlay/test_r02_selection_audit_replay.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_acceptance.py v2/research/overlay/test_r02_candidates.py v2/research/overlay/test_r02_audit_replay.py v2/research/overlay/test_r02_selector.py v2/research/overlay/test_r02_selection_audit_replay.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay -q
```

Expected results:

- D2b focused: `27 passed`
- all R02 focused: `64 passed`
- full overlay: `191 passed`
- `git diff --check`: no output
- provider calls: `0`
- live executions: `0`

## Required review questions

1. Does the prompt receive only the frozen selector-safe payload and keep roles,
   canonical IDs, seed, map, oracle, headroom, and hidden outcomes inaccessible?
2. Is prompt status still draft and explicitly not frozen?
3. Does strict parsing reject all non-contract response forms without repair?
4. Do invalid schema, unknown presented ID, and acceptance revalidation failure
   each produce an explicit typed baseline fallback?
5. Does acceptance independently revalidate the chosen frozen candidate before
   execution, with no mutation or auto-repair?
6. Is paired utility delta computed exactly from deterministic executed and
   baseline scores, including fallback delta `0`?
7. Do attempt and token ledgers reconcile exactly and remain bound to R02 identity?
8. Does the append-only graph include request, raw response, parsed response,
   transport, fallback when present, execution, and score evidence in fixed order?
9. Does replay fail on anchor, fixture, artifact-byte, or canonical-run mismatch?
10. Are provider clients, network/process transports, live execution, new fixtures,
    statistical freeze, budget freeze, and zero-call preflight absent?
11. Are D1 identities, the D2a candidate generator, and all R01 sealed artifacts
    unchanged?

Report findings as `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`, with file and
line evidence. Do not commit or push during review.
