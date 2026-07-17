# R02 D3 live-gate provider-free review handoff

Review base: `87da1d77d734d4687df40d5b2b561ea2fde7cc18`

Candidate state: `UNCOMMITTED_REVIEW_CANDIDATE_PROVIDER_FREE`

Authoritative freeze SHA-256:
`b650b8379d36292eaafd1d2df29f0f400df486da94d8c8e74f22348db2cd7b07`

Provider calls/live execution/micro-pilot: `0/0/0`

## Scope

Review only the append-only live-gate prerequisite freeze. The accepted D3
files at commit `87da1d7` must remain byte-identical. This review cannot grant
live execution or accept the future 6+49 continuation on the user's behalf.
Do not modify or stage `docs/claude-d2b-multi-reviewer-handoff.md`.

This reseal resolves both HIGH findings from the first multi-review. Source
pins now cover all six live-path modules, including D3 contracts, preflight/live
argv, and replay. The freeze also binds its four new contracts to a typed
snapshot loaded from the hash-accepted D3 preregistration. Diff-limited review
should verify these two changes and the regenerated hash chain.

## Review files

- `v2/research/overlay/r02_d3_live_gate.py`
- `scripts/r02_d3_live_gate_preflight.py`
- `v2/research/overlay/test_r02_d3_live_gate.py`
- `docs/r02-d3-live-gate-provider-free-authorization.md`
- `docs/r02-d3-live-gate-freeze-candidate.json`
- `docs/r02-d3-live-gate-preflight.json`
- `docs/r02-d3-live-gate-preflight-anchors.json`
- `docs/r02-d3-live-gate-preflight-replay.json`
- `docs/r02-d3-live-gate-manifest.json`
- `docs/r02-d3-live-gate-provider-free-report.md`
- `docs/r02-d3-live-gate-review-handoff.md`

## Source identities

- `r02_d3_live_gate.py`:
  `458468bb861e89d097b6d2da418af0c4ab25d489b25f3844d621fe1e115abd8e`
- `scripts/r02_d3_live_gate_preflight.py`:
  `5d6fc2d39dfefeb22ac740549c8ab1ce0839adb935abcb33ac5c4bb781c26c01`
- `test_r02_d3_live_gate.py`:
  `4c711306d8603b78b808e712795fc216ea012f961031aad1b0c488d201edc28c`

## Reproduction

```powershell
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_d3_live_gate.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay/test_r02_acceptance.py v2/research/overlay/test_r02_candidates.py v2/research/overlay/test_r02_audit_replay.py v2/research/overlay/test_r02_selector.py v2/research/overlay/test_r02_selection_audit_replay.py v2/research/overlay/test_r02_frame.py v2/research/overlay/test_r02_statistics.py v2/research/overlay/test_r02_d3_preflight.py v2/research/overlay/test_r02_d3_replay.py v2/research/overlay/test_r02_d3_live_gate.py -q
.venv\Scripts\python.exe -m pytest v2/research/overlay -q
.venv\Scripts\python.exe scripts/r02_d3_live_gate_preflight.py --repo-root C:\Users\User\Desktop\ai-hedge-fund-fresh --authorization C:\Users\User\Desktop\ai-hedge-fund-fresh\docs\r02-d3-live-gate-provider-free-authorization.md --expected-executable-sha256 cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4 --verify-existing
```

Expected:

- live-gate focused: `9 passed`
- all R02 focused: `100 passed`
- full overlay: `227 passed`
- Pydantic JSON Schema generation: `72/72`
- replay: `verified_artifacts=3`, `all_hashes_match=true`
- provider/live/micro-pilot: `0/false/false`

## Required review questions

1. Are accepted D3 commit, preregistration, preflight, manifest, and bootstrap
   seed identities unchanged?
2. Is executable SHA supplied externally and checked before runtime observation?
3. Do selector, R02 contracts, Codex token parser, D3 contracts, D3
   preflight/live argv, and D3 replay match their exact pins?
4. Does no stop after six cases require the remaining 49 in frame order?
5. Must future live authorization explicitly cover the indivisible 6+49 scope?
6. Are utility outcomes unavailable to the continuation gate, with a direct
   test and a binding to the accepted preregistration field?
7. Is usage accepted only from exactly one `turn.completed.usage` object with
   all four exact fields?
8. Are cached input and reasoning output counted exactly once?
9. Does invalid usage debit one attempt plus 32,000 tokens and hard-stop?
10. Is five attempts the primary fail-closed boundary with floor-derived
    `90,909 ppm` reporting only?
11. Do duplicate reason codes trigger typed baseline fallback without repair
    despite the output schema lacking `uniqueItems`?
12. Are all three append-only nodes hash-checked and byte-replayed, with the
    live-gate implementation and preflight-script hashes embedded in freeze?
13. Is every provider/live/micro-pilot literal still zero or false?
14. Do manifest, source, generated-artifact, and local-tree hashes all match?
15. Are accepted D3/R01/D2c artifacts and the unrelated Claude document
    untouched?

Report CRITICAL/HIGH/MEDIUM/LOW findings with file and line. State whether the
candidate is acceptable for user freeze acceptance. A passing review is not
live authorization.
