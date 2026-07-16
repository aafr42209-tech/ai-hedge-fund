# R01 B3 resource-v2 token-reserve STOP report

Date: 2026-07-17

Status: `STOPPED_NO_FURTHER_PROVIDER_CALLS_AUTHORIZED`

The approved B3 replacement micro-pilot stopped on its eleventh new provider
attempt when one complete response used `64023` accounting tokens, exceeding
the approved `64000` per-attempt reserve by `23`. The response was persisted but
was not parsed, scored, retried, or followed by another provider call.

## Approved execution boundary

- approved implementation commit: `f403e1a`;
- approved preflight SHA-256:
  `95130a039edbd43a9c610078ce6d904beb5e038bed65e9bf0252924b3bb04bde`;
- approved experiment ID:
  `r01-b3-prompt-v1-resource-v2-20260716`;
- execution HEAD: `74e7f66`, whose only post-review changes were documentation;
- user approval record:
  `docs/r01-b3-resource-v2-user-approval.md`, SHA-256
  `bdc69d07e1b97aca8b4015c15b3004e8a7843e2e61b0423cdf70e03d3ea3d97c`;
- approved new acquisitions: `12`;
- approved maximum new provider attempts: `24`;
- per-attempt reserve: `64000`;
- development token cap: `12800000`;
- development provider-attempt cap: `200`;
- incremental USD cap: `0`;
- no automatic reserve increase.

Immediately before `b3-run`, the live client construction path rechecked login,
feature gate, executable, account attestation, D2 amendment, aggregate carry,
preflight, command specs, and the empty external sandbox. It returned
`provider_calls: 0`, carry `4 / 103623`, and the exact approved preflight hash.

## Execution outcome

- New provider ordinals were exactly `5` through `15`, with no gaps.
- Every acquisition remained at attempt `1`; no transport retry occurred.
- All 11 Codex processes exited `0`; none timed out or reported a launch error.
- Ten responses reached disposition and scoring. All ten were
  `FAIL_CLOSED_SCORE` with reason `schema_invalid` and were scored as hold
  exactly once.
- Ordinal 15, `development-0003` replicate 0, completed transport and token
  settlement at `64023` accounting tokens. The runner persisted
  `r01-acquisition-failure-v3` with
  `per_attempt_token_reserve_exceeded / STOP_PHASE` before parsing or scoring.
- `development-0003` replicate 1 was not launched. No twelfth new provider
  attempt was made.
- No `development_run_result.json`, `token_budget_summary.json`, report, or
  replay verification exists. The ten partial scores cannot select a prompt,
  satisfy B3, or enter a later research result.
- The external pilot sandbox contained zero entries after STOP.

## Attempt ledger

| Ordinal | Case | Replicate | Input | Cached input | Output | Accounting total | Terminal treatment |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 5 | development-0005 | 0 | 12309 | 0 | 1463 | 13772 | `FAIL_CLOSED_SCORE`, hold |
| 6 | development-0005 | 1 | 12309 | 4864 | 1637 | 13946 | `FAIL_CLOSED_SCORE`, hold |
| 7 | development-0001 | 0 | 41240 | 25088 | 3019 | 44259 | `FAIL_CLOSED_SCORE`, hold |
| 8 | development-0001 | 1 | 12312 | 0 | 3836 | 16148 | `FAIL_CLOSED_SCORE`, hold |
| 9 | development-0000 | 0 | 12310 | 0 | 1443 | 13753 | `FAIL_CLOSED_SCORE`, hold |
| 10 | development-0000 | 1 | 12310 | 0 | 1447 | 13757 | `FAIL_CLOSED_SCORE`, hold |
| 11 | development-0004 | 0 | 12308 | 0 | 1777 | 14085 | `FAIL_CLOSED_SCORE`, hold |
| 12 | development-0004 | 1 | 12308 | 12032 | 1150 | 13458 | `FAIL_CLOSED_SCORE`, hold |
| 13 | development-0002 | 0 | 12306 | 0 | 2324 | 14630 | `FAIL_CLOSED_SCORE`, hold |
| 14 | development-0002 | 1 | 12306 | 0 | 1747 | 14053 | `FAIL_CLOSED_SCORE`, hold |
| 15 | development-0003 | 0 | 59849 | 25088 | 4174 | 64023 | unscored `STOP_PHASE` |

The eleven new responses used `235884` accounting tokens.

## Global budget after STOP

| Component | Carried before run | This run | Global after STOP |
| --- | ---: | ---: | ---: |
| Provider attempts | 4 | 11 | 15 |
| Settled complete responses | 3 | 11 | 14 |
| Failed or unsettled attempts | 1 | 0 | 1 |
| Actual settled tokens | 71623 | 235884 | 307507 |
| Conservative token charge | 103623 | 235884 | 339507 |

`339507 = 103623 + 235884`. The ordinal-15 response is a complete settled
response for token accounting even though it is a failed, unscored acquisition
for research execution. The earlier ordinal-1 unsettled attempt remains the one
carried failed-or-unsettled ledger entry.

## Response-schema finding

The first ten responses all contained one parseable outer JSON object with a
`decisions` member and all six asset decisions, but each supplied `confidence`
as a floating-point value between 0 and 1. The frozen contract requires a strict
integer from 0 through 100. Pydantic therefore reported six confidence type
errors per response, for 60 invalid fields total. Each complete invalid response
correctly produced one `schema_invalid` reason, one fail-closed executable hold,
and one hold score.

The frozen prompt showed an integer confidence example but did not explicitly
state the integer range. The systematic 10/10 mismatch is consistent with an
underspecified prompt wire contract; this is an inference about prompt design,
not a claim about the model's internal cause. Ordinal 15 stopped before decision
parsing, so its decision validity is not used in this finding.

No response emitted a tool event, and all persisted response metadata recorded
`tool_use_violation: false`. Transport model echo remained absent, so model
identity continues to rely on the reviewed command spec and executable boundary
rather than a provider-echo field.

## STOP evidence and artifact integrity

Machine-readable evidence is
`docs/r01-b3-resource-v2-stop-evidence.json`, SHA-256
`c0f6a084d2a151bde1aaef2b0265789ab4073655338b3a22759b7f62a0a7d41b`.

The immutable artifact root contains 268 files after STOP. A sorted list of
every relative path, byte size, and SHA-256 was canonicalized and hashes to:

`47db54ece1b05e5bad3d48c68c98bb0f402682603ba435bf6e5e6f7bc404d73c`.

All JSON files parse and use the canonical integer-only representation. Every
live command spec matches one of the six reviewed preflight command specs. The
ordinal-15 failure record binds its reservation, policy input, prompts, provider
request, raw response, response metadata, token usage, command spec, stdout,
stderr, process status, and parsed transport response. Core STOP hashes are:

- acquisition failure:
  `0ec69aa27e9316ea4506f1ca02e83bd2253c8c8b48d0328f24301344b5247127`;
- token reservation:
  `b683540043cbe08b1c91d6a58405b1e4bf388fbedada0f4f67bd090b6da50d12`;
- token usage:
  `e91fe34f358aa6c478cd81aa3bc497f24160ae5bc67d5c8db64d4841d34b0936`;
- command spec:
  `628a9450c238ac789b413132e1afea8db4404dfaa752c1be1ee38b83a25d13bf`;
- stdout JSONL:
  `9913e43fe7f9bd5ac092b3a77c7ae08589b929b0bd110721e3a48496c89ce4cd`;
- process status:
  `6092865ae715c79bfea59f15bf0a5d11aeb4a144f61d063e7aa811669c675629`;
- parsed provider response:
  `c5887138c8dd4234fc9f3830e7d8583c74d6dd30e676e978465689971a47a354`.

Because STOP prevented the normal run-result write, successful partial
acquisition artifacts are not adopted by one completed run-result graph. The
external tree digest above records their exact immutable bytes without
backfilling or mutating the live artifact root.

## Decision gate

No further provider call is authorized. In particular:

- the reserve must not be raised from `64000` automatically, even though the
  observed excess was only `23` tokens;
- the missing twelfth acquisition must not be resumed under this experiment ID;
- the ten partial hold scores must not be used for prompt selection or B3
  completion;
- any future work must first independently review this STOP report and evidence;
- a future live attempt would require a provider-free prompt/schema redesign,
  an aggregate carry-forward starting at 15 attempts and 339507 conservative
  tokens, a new experiment identity, manifest, preflight, independent review,
  and new explicit user approval.

The immediate provider-free decision is whether to stop R01 or redesign the
prompt so the confidence wire type and range are explicit while retaining the
64K hard stop. That decision is not made by this report.

## Independent cross-review questions

1. Do ordinals 5 through 15, process statuses, token-usage bytes, and the absence
   of ordinal 16 prove exactly 11 new provider attempts and no retry?
2. Did ordinal 15 persist the complete v3 post-response failure graph and stop
   before parsing, scoring, or another call?
3. Do the attempt table and carry reproduce global totals 15 attempts, 307507
   actual tokens, and 339507 conservative tokens?
4. Do all ten consumed responses fail only because six floating confidence
   values violate the strict integer 0-through-100 contract, and does each score
   as hold exactly once?
5. Does the 268-file tree reproduce the recorded canonical reference-list hash,
   with all reviewed command specs and STOP hashes intact?
6. Does the absence of a run result make every partial score ineligible for B3
   completion or prompt selection?
7. Are all future provider calls blocked pending a new carry, identity,
   preflight, independent review, and explicit user approval?
