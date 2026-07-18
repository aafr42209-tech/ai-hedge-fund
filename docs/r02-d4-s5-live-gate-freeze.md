# R02 D4-S5 provider-free execution preflight and live-gate freeze

Date: 2026-07-18

Status: `PROVIDER_FREE_EXECUTION_PREFLIGHT_LIVE_GATE_PENDING_INDEPENDENT_REVIEW`

This freeze defines a future execution contract. It does not implement a D4
runner and does not authorize provider calls, Codex exec, micro-pilot, LIVE,
retry, replacement, resume, or commit/push of the S5 draft.

## 1. Execution identity preflight

Five D3-allowlisted local commands were replayed: version, login status,
baseline feature list, post-disable feature list, and `exec --help`. They made
no provider request and are not Codex exec invocations. All five matched the
sealed D3 identity:

- Codex CLI `0.144.1`;
- executable SHA-256 `cbacbb97...ab0e4`;
- ChatGPT authentication;
- feature catalog and definition hashes;
- four-entry post-disable active allowlist;
- provider `openai-codex-chatgpt-subscription`;
- requested model `gpt-5.6-sol`, reasoning effort `high`;
- D3 prompt and response-schema hashes;
- web search disabled and exec-help contract intact.

Any future drift requires a new provider-free preflight and review. Runtime
discovery may not silently replace the frozen identity.

## 2. Exact execution order

Only the 69 selector-eligible S2A fixtures may receive provider attempts. They
are ordered by ascending sealed `frame_ordinal`. The plan begins at frame
ordinal 2 (`development-0002`), contains 19 representative then 50 challenge
cases under the sealed frame order, and ends at ordinal 199
(`development-0560`). Its canonical SHA-256 is
`a5e461a74a594a7f54a4751c8cb330ab4032c23ce25bdcbbd0dda6599c6af7d1`.

No permutation, batching reorder, retry, replacement, or resume is allowed.

## 3. Budget ledger

The S4 budget is binding:

- provider attempts: 69;
- token reserve per attempt: 32,000;
- aggregate token cap: 2,208,000;
- retry/replacement/unsettled caps: 0.

Before launch, an attempt slot and the full token reservation must fit. The slot
is debited before launch. Successful terminal usage debits
`input_tokens + output_tokens`; missing or invalid usage debits 32,000 and
hard-stops unsettled. Attempted cases remain in ITT. Unused reservation cannot
create a new attempt.

## 4. Timeout

Local identity commands have a 30-second cap. A future provider attempt has a
900,000-ms cap, identical to D3. The theoretical provider-wait maximum for 69
attempts is 62,100,000 ms, but the first timeout debits one attempt and the full
reserve and immediately hard-stops as an unsettled invalid run. There is no
timeout retry.

## 5. Fail-closed rate

D3 allowed at most 5 settled fail-closed attempts among 55, a floor-reported
rate ceiling of 90,909 ppm. D4 selects the largest integer cap that does not
loosen that ceiling:

- `floor(6 × 1,000,000 / 69) = 86,956 ppm`;
- `floor(7 × 1,000,000 / 69) = 101,449 ppm`, which exceeds D3.

Therefore 6 is the primary settled fail-closed cap. Validly settled selector
fallbacks contribute zero e12 and increment this counter. The seventh would
hard-stop and label the run invalid. Identity, budget, timeout, missing usage,
unsettled, audit, order, retry/replacement, and authorization breaches are
immediate hard stops rather than ordinary settled fallbacks.

## 6. No micro-pilot

The frozen decision is `NO_MICRO_PILOT`: case count 0 and attempt cap 0. D3 has
already validated this transport and S5 revalidated the exact execution
identity provider-free. An interim D4 gate would add optional-stopping and
outcome-disclosure surfaces without answering the primary exact-replication
question.

If separately authorized later, execution is one continuous pass over all 69
eligible fixtures. Outcomes are unavailable during the pass. In the absence of
a frozen hard stop, the runner must continue to the next case. No discretionary
pause, second authorization, or resume after a hard stop is allowed.

## 7. What remains unbuilt and unauthorized

S5 does not create a D4 production runner, audit store, replay implementation,
provider preflight artifact, or LIVE authorization artifact. A future
provider-free runner phase must bind this order, ledger, identity, timeouts,
fallback counter, append-only persistence, and replay contract, then pass
independent review. LIVE requires another explicit user authorization after
that.

At S5 authoring closeout:

- allowlisted local identity commands: 5;
- provider calls: 0;
- Codex exec invocations: 0;
- micro-pilot/LIVE: false;
- retry/replacement: 0;
- S5 commit/push: false.
