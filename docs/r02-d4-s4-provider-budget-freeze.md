# R02 D4-S4 provider-free provider-budget freeze

Date: 2026-07-18

Status: `PROVIDER_FREE_PROVIDER_BUDGET_FREEZE_PENDING_INDEPENDENT_REVIEW`

This document freezes arithmetic and debit rules only. It does not authorize a
provider call, Codex exec, micro-pilot, LIVE authorization or execution,
retry, replacement, or commit/push of the S4 draft.

## 1. Sealed basis

The accepted S3 statistical freeze requires a later provider budget to use the
sealed S2A selector-eligible count. That count is 69: 19 representative and 50
challenge fixtures within the fixed 150/50 frame. The remaining 131 fixtures
have a provider-attempt cap of zero.

The budget is outcome-independent. It uses only the sealed count, the accepted
one-attempt/no-retry formula, and provider-free request-size recomputation. No
LLM selection result or provider output was accessed.

## 2. Frozen numeric budget

| Quantity | Frozen value |
|---|---:|
| Eligible episodes | 69 |
| Attempts per eligible episode | 1 |
| Retry attempts | 0 |
| Replacement attempts/cases | 0 |
| Total provider-attempt cap | 69 |
| Token reserve per attempt | 32,000 |
| Aggregate token cap | 2,208,000 |
| Incremental USD cap | 0 |

The arithmetic is exact:

`69 eligible × 1 attempt × 32,000 tokens = 2,208,000 tokens`.

The `incremental_usd_cap=0` is restrictive. It does not permit a positive
provider charge. A path requiring a positive incremental charge needs a new
provider-budget freeze and separate review.

## 3. Request-size evidence

The accepted D2c calculation path was replayed over all 69 sealed eligible S2A
fixtures. For each fixture it builds the provider-free preparation and selector
request, then measures:

- UTF-8 bytes of `system_prompt + "\n" + user_prompt`: maximum 1,842;
- canonical selector-payload UTF-8 bytes: maximum 1,314.

This evidence does not convert bytes to tokens and does not reduce the 32,000
token reserve. The reserve remains conservative relative to the sealed R01
observed maximum accounting total of 15,750 tokens.

## 4. Reservation and debit rules

Before any future attempt launches, both one unused attempt slot and the full
32,000-token reservation must fit within the remaining caps. The attempt slot
is debited before launch. An attempted case remains in the ITT frame regardless
of provider success or fallback.

Successful accounting debits `input_tokens + output_tokens`. Cached input is a
subset of input and is not subtracted. Reasoning output is a subset of output
and is not added twice. Exactly one terminal usage event must contain cached
input, input, output, and reasoning-output fields.

Missing or invalid usage debits the attempt and the full 32,000-token reserve,
then hard-stops as unsettled. Reported usage above 32,000 tokens is an
`INVALID_RUN_BUDGET_BREACH`. Exhausting an attempt or token cap hard-stops the
run. Unused reservation cannot become a new attempt credit.

## 5. Retry and replacement closure

The S2A intent pins `generation_attempt_cap=1`. Both the frame manifest and
seal pin `frame_generation_count=1`, `retry_count=0`, and
`replacement_count=0`. S4 validates all six manifest/seal count fields
directly, including `seal.retry_count`, closing the nonblocking S3 review
observation. Provider retry, provider replacement, and unsettled-attempt caps
are also zero.

Negative tests alter each generation/retry/replacement field independently and
require fail-closed rejection. In particular, an in-memory
`seal.retry_count=1` must raise `R02D4S4BudgetError` before budget acceptance.

## 6. Exact-replication identity reference

This budget does not select a provider, model, prompt, or output schema. It
references the sealed D3 exact-replication identity by the D3 preregistration
hash. A future provider preflight and LIVE gate must revalidate the same
provider/model, reasoning effort, prompt hashes, output-schema hash, Codex
executable/features, frame order, and audit persistence. Any drift is
fail-closed.

The later LIVE gate must also freeze any failure-rate or continuation rule.
Those rules and any micro-pilot decision are deliberately not created here.

## 7. Frozen boundary

At S4 authoring closeout:

- provider calls: 0;
- Codex exec invocations: 0;
- micro-pilot executed: false;
- LIVE authorization/execution: false;
- retry/replacement: 0;
- S4 commit/push: false.

Independent review may reproduce hashes, request-size evidence, arithmetic,
typed-contract validation, protected-root invariance, and the frozen test suite
using read-only commands. A review pass accepts only this provider-budget
freeze. It does not authorize preflight, provider access, or LIVE execution.
