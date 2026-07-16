# R01 B3 Transport-v3 Token-Reserve Stop

Status: `STOP_PHASE`

Incident date: `2026-07-16` (Asia/Seoul)

No further provider call is authorized by this record.

## Authorized boundary

- Approved implementation commit: `af8381f`.
- Approved preflight SHA-256:
  `e86c75659b1dc54e16722d2ee37403e0c6fba3f59318d00103fb84ad79823d09`.
- Execution HEAD: `dbcab84`; the only commits after `af8381f` were reviewed or
  user-approval documents, with no overlay-code drift.
- User approval record: `docs/r01-b3-transport-v3-user-approval.md`, SHA-256
  `80124f9b177dc90d7c89d7a9aa7a38c100511e389831cdcfa8a7776accd1e630`.
- Experiment: `r01-b3-prompt-v1-transport-v3-20260716`.
- Planned acquisitions: `12`; maximum new provider attempts: `24`.
- Starting carry: one provider attempt and `32000` conservatively charged
  tokens.
- Incremental USD cap: `0`.

Immediately before execution, ChatGPT login, executable, account attestation,
carry document, preflight, feature gate, empty sandbox, clean worktree, and
approved-code identity all passed provider-free revalidation. The constructed
client reported zero provider calls.

## Live outcome

The replacement B3 made exactly three new provider calls:

| Global ordinal | Acquisition | Input | Cached input | Output | Reasoning output | Accounting total | Duration | Result |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 2 | `development-0005`, replicate 0 | 12307 | 7936 | 1308 | 1034 | 13615 | 36859 ms | completed and scored |
| 3 | `development-0005`, replicate 1 | 12307 | 7936 | 1049 | 752 | 13356 | 29765 ms | completed and scored |
| 4 | `development-0001`, replicate 0 | 41629 | 33024 | 3023 | 1418 | 44652 | 77063 ms | `STOP_PHASE`, unscored |

Ordinal 4 exceeded the approved `32000` per-attempt reserve by `12652` tokens.
The runner raised `per_attempt_token_reserve_exceeded` immediately after token
settlement. It made no retry and did not launch the remaining nine acquisitions.

All three processes exited 0, did not time out, emitted no tool event, and
matched the exact approved three-message diagnostic tuple. The transport did
not echo a verifiable model identity, which remains the already documented
limitation; each request used the pinned `gpt-5.6-sol` command spec and ChatGPT
subscription provider surface.

The third local user prompt was `2940` bytes versus `2926` bytes for each of the
first two attempts. That 14-byte difference does not explain the observed
provider input increase from `12307` to `41629` tokens. No causal explanation is
asserted; the evidence establishes that provider-visible input usage can vary
materially despite similarly sized local prompts.

## Budget closeout

- Global provider attempts: `4`.
- Complete responses in the replacement run: `3`.
- Prior failed or unsettled attempts: `1`.
- Settled actual tokens in the replacement run: `71623`.
- Prior observed unsettled actual tokens: `13651`.
- Observed actual tokens across both stopped experiments: `85274`.
- Conservative global charge after ordinal 4: `103623`.
- Provider calls after the reserve STOP: `0`.

The first two scores are partial stopped-run artifacts. Because no
`development_run_result` exists, they cannot be used to select a prompt, claim
B3 completion, or enter a later run.

## Immutable evidence

- Artifact root: `.research_artifacts/r01-b3-af8381f`.
- Files after STOP: `107`.
- Sorted tree-manifest SHA-256:
  `d1aa3867438872043b3d60b5fe55b71cd545925492066d5c066b0127432895c2`.
- Machine evidence: `docs/r01-b3-token-reserve-stop-evidence.json`, SHA-256
  `cd51330661e2f4a55627fd9464e681c763c16f80b0a3f43a5b3b59dd12ba80da`.
- Ordinal-4 command spec SHA-256:
  `b62385398e1d54b801043539203c08ee2b802c06daaf115b8d3b63b0c6dfe194`.
- Ordinal-4 stdout SHA-256:
  `883b69ee81bb9edeee285bb57160d68d5942646aca24eef4b3b8ed9de08cf9cb`.
- Ordinal-4 provider-response SHA-256:
  `a996315be3fce27782f9617032185e92c10c417d807d709c2096c982e6f09eca`.
- Ordinal-4 token-usage SHA-256:
  `2492ca1f43b2113e2dddf8a8ca92256b7c8e343afaf59c14222644d1180e8e77`.
- Sandbox entries after STOP: `0`.
- Missing run result: expected for the stopped phase.

The artifact root is left unchanged after the STOP. The tree digest above is
defined as SHA-256 of the compact JSON array of every file's sorted
`relative_path`, `size_bytes`, and `sha256` tuple, rooted at
`.research_artifacts/r01-b3-af8381f`.

## Newly exposed audit gap

The live runner correctly stopped but persisted the ordinal-4 raw response,
provider metadata, token usage, and complete transport before checking the
reserve. The check then raised outside the client-error catch that writes
`acquisition_failure.json`. Consequently, the immutable live root has complete
bytes but no durable artifact that records the STOP code and binds those bytes
as one terminal attempt graph. The traceback was the only direct STOP-code
record before this external evidence document.

The historical root is not backfilled. Prospective hardening instead:

- bumps new acquisition failures to `r01-acquisition-failure-v3` while retaining
  v2 parsing for historical records;
- adds `r01-codex-post-response-stop-artifacts-v1`;
- binds policy input, prompts, provider request, raw response, response
  metadata, token usage, and complete transport before raising the reserve
  `STOP_PHASE`;
- adds a regression test that verifies every bound reference.

The post-stop research-contract SHA-256 is
`6402fc1dadd93134da940193f3a695426645d0ec79eb16806b8c3be150b3d22c`.
The live manifest remains correctly bound to the pre-run contract SHA
`f0c29d0bb4c6e55673206f3d1c3415f82318cdc0fcb8208df568df00e528a5a1`.

## Required decision before any replacement

The approved `32000` reserve cannot be silently raised from this outcome.
Before another provider call, R01 requires all of the following:

1. a D2 resource amendment or an explicit decision to retain `32000` and stop
   or redesign provider-free;
2. an aggregate carry-forward contract that represents all four attempts and
   the `103623` conservative charge without mislabeling ordinal 4 as a transport
   failure;
3. a new experiment identity, contract-bound manifest, empty sandbox, and
   provider-free preflight;
4. independent review of the post-response STOP closure and the new budget
   chain;
5. explicit user approval of the new code/preflight pair.

Until those conditions pass, B3 remains incomplete and provider calls remain
blocked.

## Provider-free closure validation

- Focused B3 tests: `7 passed`.
- Full overlay suite: `125 passed`.
- `compileall`: passed.
- Black: all 36 overlay Python files passed.
- isort: passed.
- `git diff --check`: clean.
- Live artifact tree remains 107 files with tree-manifest SHA-256
  `d1aa3867438872043b3d60b5fe55b71cd545925492066d5c066b0127432895c2`.
- Sandbox remains empty.
- Provider calls after STOP remain `0`.
