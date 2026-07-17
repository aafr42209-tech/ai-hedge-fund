# R01 B3 prompt-v2/resource-v3 live micro-pilot result

Date: 2026-07-17

Status: `COMPLETED_DEVELOPMENT_ONLY_NOT_SEALED`

Provider-call gate: `CLOSED`

The independently reviewed B3 micro-pilot completed all 12 approved
acquisitions. No retry, failure, `FAIL_CLOSED_SCORE`, `STOP_PHASE`, tool event,
constraint violation, timeout, nonzero process exit, or reserve excess occurred.
No further provider call is authorized by this result.

## Authorization and execution identity

- approved implementation commit: `1f65106`;
- approved preflight SHA-256:
  `5937161ac9c2bb9c22172d0be27a5a730cc2a3dc1c8bf51044270b65ee68353e`;
- experiment ID: `r01-b3-prompt-v2-resource-v3-20260717`;
- execution HEAD:
  `dd52092e5a2567c598505a7708b0871f3ea407f9`;
- user-approval document SHA-256:
  `690f54031f1c4eb25a4cc0c37a7a3a64bf35555d8ae0321c0614e6794d1d9587`;
- execution-approval commit: `dd52092`;
- execution command wall time: `503.5` seconds;
- machine evidence: `docs/r01-b3-prompt-v2-resource-v3-live-evidence.json`,
  SHA-256
  `423bc4833ff39aa0e6b771c628ba3770b955b4a05c1686048e1c979b8a24836c`.

`1f65106..dd52092` changes only documentation and the overlay README; Python
execution code is unchanged from the approved implementation commit.

## Completion and structural quality

- planned acquisitions: `12`;
- completed acquisitions: `12`;
- provider attempts: `12`, ordinals `16` through `27`;
- attempt-2 retries: `0`;
- acquisition failures: `0`;
- normal scored responses: `12`;
- raw-valid decision batches: `12/12`;
- fallback batches: `0/12`;
- fail-closed scores: `0/12`;
- phase stops: `0/12`;
- tool-use violations: `0/12`;
- executable constraint violations: `0/12`;
- process-status violations: `0/12`;
- integer confidences: `72/72` decisions;
- fractional confidences: `0/72`;
- identical-repeat action agreement: `36/36` asset comparisons;
- identical-repeat action-plus-quantity agreement: `36/36`;
- full-agreement fixture pairs: `6/6`.

Prompt v2 therefore repaired the observed confidence-schema failure: every
decision used a JSON integer in `[0, 100]`, and every response reached the normal
scoring path without hold fallback. Both replicates of every fixture produced
identical actions and quantities.

## Token and process accounting

Cached input is a subset of input tokens, and reasoning output is a subset of
output tokens. The accounting total is input plus output.

| Ordinal | Fixture | Replicate | Input | Cached | Output | Reasoning | Total |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | development-0005 | 0 | 12,516 | 4,864 | 1,269 | 1,034 | 13,785 |
| 17 | development-0005 | 1 | 12,516 | 4,864 | 1,403 | 1,155 | 13,919 |
| 18 | development-0001 | 0 | 12,519 | 4,864 | 3,161 | 2,928 | 15,680 |
| 19 | development-0001 | 1 | 12,519 | 4,864 | 3,231 | 2,977 | 15,750 |
| 20 | development-0000 | 0 | 12,517 | 4,864 | 1,224 | 982 | 13,741 |
| 21 | development-0000 | 1 | 12,517 | 4,864 | 1,481 | 1,243 | 13,998 |
| 22 | development-0004 | 0 | 12,515 | 7,936 | 1,747 | 1,515 | 14,262 |
| 23 | development-0004 | 1 | 12,515 | 0 | 2,140 | 1,912 | 14,655 |
| 24 | development-0002 | 0 | 12,513 | 7,936 | 1,087 | 841 | 13,600 |
| 25 | development-0002 | 1 | 12,513 | 7,936 | 1,223 | 960 | 13,736 |
| 26 | development-0003 | 0 | 12,537 | 0 | 1,348 | 1,131 | 13,885 |
| 27 | development-0003 | 1 | 12,537 | 4,864 | 2,093 | 1,841 | 14,630 |
| **Total** |  |  | **150,234** | **57,856** | **21,407** | **18,519** | **171,641** |

- minimum attempt total: `13,600`;
- maximum attempt total: `15,750`;
- minimum headroom under the `128,000` reserve: `112,250`;
- process duration range: `29,203` to `65,828` ms;
- summed process duration: `498,016` ms.

Global budget after the run is:

- provider attempts: `27 / 200`;
- successful settled responses: `26`;
- failed or unsettled historical attempts: `1`;
- actual settled tokens: `479,148`;
- conservatively charged tokens: `511,148 / 12,800,000`.

The current run added exactly 12 attempts and `171,641` settled tokens to the
carried 15-attempt / `339,507`-token state. No 128K conservative reservation was
retained for these successful responses; each settled response charged its
actual accounting total.

## Transport and identity evidence

- process exit zero: `12/12`;
- timeout false: `12/12`;
- empty stderr: `12/12`;
- unique request IDs: `12/12`;
- provider-response schema: `r01-provider-response-v4`;
- recorded model ID: `gpt-5.6-sol`;
- model mismatch: `0`;
- transport model echo present: `0/12`;
- transport identity evidence: `transport_echo_absent` for all 12.

The last item is the pre-existing known limitation: the command spec and pinned
model request provide identity evidence, but these transports did not echo the
model independently. No mismatch was observed.

## Replay and artifact integrity

The externally pinned result identities are:

- run result SHA-256:
  `c262fac9efd5b725138e9b89b92f9043f17ee5398012348957ecf6331fd6c349`;
- run plan SHA-256:
  `72e5d356b811393203f66449d1c6db6b53876f1e463e8b41672a445a9eddbf20`;
- token-budget-summary SHA-256:
  `2c942c46a2bf73a02b089c8358be36266b4ef1580f28c1f8948e91dd5111508c`;
- development-report JSON SHA-256:
  `5ceaa2b4157981ca9a9250db6482d8768ef8d2738a73a18190161a4751c1fd86`;
- development-report Markdown SHA-256:
  `b1275f71c0ff94b5d24c22999747c03752050103beda9632e1d1a19e7860a88b`;
- replay-verification SHA-256:
  `a915ffbbd75e74aaa545cf91ea8ee7a904903609f04b03b1bd954c6fe3b31339`.

Both `replay` and `verify` independently returned:

- schema `r01-replay-verification-v1`;
- verified acquisitions: `12`;
- `all_hashes_match: true`;
- provider calls: `0`.

The preflight, run result, and replay-verification files were treated as three
external roots. Recursive reference verification found:

- actual files: `299`;
- reachable files: `299`;
- missing or unreferenced files: `0`;
- size or SHA-256 mismatches: `0`;
- root escapes: `0`;
- canonical tree SHA-256:
  `6ecbab78625ced153cb4b446fc8e911890476c144f361769e2073c142fd5c30e`.

The tree hash is SHA-256 over sorted
`relative_path NUL size NUL file_sha256` records joined by newline. The external
sandbox remained empty after the run.

## Descriptive development metrics

These values are recorded because B3 measures utility and delta, but the frozen
B4 rule expressly prohibits using performance, regret, delta, or oracle
proximity to select a prompt. They are development-only and support no
investment claim.

- mean LLM utility: `222,264,794 e12`;
- mean deterministic-baseline utility: `2,485,225,382 e12`;
- mean LLM-minus-deterministic delta: `-2,262,960,588 e12`;
- mean oracle-minus-LLM regret: `2,669,101,490 e12`;
- mean hold utility: `-406,485,544 e12`;
- LLM above / equal / below deterministic: `2 / 0 / 10` acquisitions.

| Regime | N | Mean LLM − deterministic e12 | Mean oracle − LLM e12 |
| --- | ---: | ---: | ---: |
| signal_consensus | 2 | -481,956,848 | 784,870,622 |
| signal_conflict | 2 | -1,609,282,359 | 1,734,922,898 |
| high_transaction_cost | 2 | -5,349,191,822 | 5,572,440,014 |
| concentration_pressure | 2 | -2,506,775,842 | 2,567,939,492 |
| existing_position_asymmetry | 2 | 7,938,866 | 1,460,022,388 |
| noisy_confidence | 2 | -3,638,495,524 | 3,894,413,527 |

The micro-pilot is a structural success but not evidence of incremental utility:
prompt v2 was valid, deterministic, and tool-free, while its descriptive
utility trailed the deterministic baseline on five of six fixture pairs.

## Prompt-selection and next gate

Prompt v2 satisfies the first four frozen structural observations needed for
B4 review:

1. no tool-use or executable violation;
2. parse-plus-fallback rate `0/12`;
3. identical-repeat action agreement `36/36`;
4. measured accounting tokens `171,641` across 12 responses.

The earlier prompt-v1 evidence contained repeated fractional-confidence schema
failures; prompt v2 removed that failure mode. Formal final-prompt selection has
not been recorded, and D3 has not been approved. No B4 tuning call, B5 call,
Phase C seal, evaluation call, or investment verdict is authorized.

The next safe action is independent cross-review of this result and evidence.
After review, the user may decide whether to select prompt v2 without another
prompt call and open D3, request a provider-free closeout, or stop R01 because
the descriptive utility signal is weak. This report itself authorizes none of
those choices.

## Independent cross-review questions

1. Does execution HEAD `dd52092` preserve the approved Python code at
   `1f65106`, and does the approval document bind the exact preflight pair?
2. Do ordinals `16..27`, 12 token reservations, 12 usages, 12 scored responses,
   and zero failures/retries reconcile with the carried state and final ordinal
   `27`?
3. Does `307507 + 171641 = 479148` actual and
   `339507 + 171641 = 511148` conservative accounting reproduce the summary?
4. Are all 72 confidences integer, all 12 batches raw-valid, all dispositions
   normal, and all 36 repeated actions and quantities identical?
5. Do the 299-file graph, external result hashes, replay output, and empty
   sandbox reproduce without mismatch or provider call?
6. Are the descriptive utility numbers reported accurately while remaining
   excluded from prompt selection and confirmatory claims?
7. Is the correct next boundary independent result review followed by an
   explicit D3/closeout decision, with no current provider-call authorization?
