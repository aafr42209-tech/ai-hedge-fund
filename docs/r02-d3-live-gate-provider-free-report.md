# R02 D3 live-gate provider-free report

Status: `FREEZE_CANDIDATE_NOT_LIVE_AUTHORIZATION`

Accepted D3 commit: `87da1d77d734d4687df40d5b2b561ea2fde7cc18`

Live-gate freeze SHA-256:
`b650b8379d36292eaafd1d2df29f0f400df486da94d8c8e74f22348db2cd7b07`

Preflight SHA-256:
`b1ec1eba58bedb959279af60067ff2d51610a9faa4c81ed9efb1146fcb73b529`

Provider calls: `0`

Live executions: `0`

Micro-pilot executions: `0`

## 1. External executable trust anchor

Every build and replay requires an explicit
`--expected-executable-sha256` argument. The freeze candidate pins:

`cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`

The argument is compared with the freeze constant before the executable is
read, and then compared with the observed bytes. At live time the accepted
freeze document, not runtime discovery, is the authority for this value.

## 2. Live source pins

- selector acceptance and fallback:
  `r02_selector.py` = `a90cc600ffc772c5fb4b1c964b5efc0a551de84a41eaa5c0a030b6d02b9b20f9`
- typed R02 contracts:
  `r02_contracts.py` = `64a099560432152da875843d6cddb4d08acd3a402198adb14a5aec65ef0dab05`
- Codex JSONL and token parser:
  `codex_exec_client.py` = `4b3bb2e5bc9d1f406105bc7fd589bbfcb7541d259ebaf209252cb42ed329a1bd`
- D3 frozen contracts:
  `r02_d3_contracts.py` = `978d4fcf2cb2775a40ac515276a4c0c69899284dc05096360b5a661b2ab2ef47`
- D3 preflight and future live argv:
  `r02_d3_preflight.py` = `2376c5a4773de506aa577387397e4f59a497e623b7cfc262edbbbf9b1deb32a7`
- D3 preflight replay:
  `r02_d3_replay.py` = `bff977ef81e8ca8bcd828ab9b39bd2070cd761f9a22eee718adf412c05030850`

Any mismatch stops before a provider attempt.

The freeze also embeds a typed snapshot read from the accepted D3
preregistration. A model-level validator requires the continuation, token
reserve, fail-closed attempt/rate, fallback delta, and selector schema values to
match that snapshot. The accepted preregistration hash is checked before the
snapshot is constructed, so the new contracts cannot silently diverge from the
accepted D3 premises.

## 3. Continuation contract

Future live authorization must cover one indivisible 55-attempt protocol:
the registered six-case micro-pilot plus automatic continuation through the
remaining 49 eligible cases in frame order when no registered hard stop occurs.
There is no discretionary pause and no second authorization after a no-stop
micro-pilot. Micro-pilot utility outcomes are unavailable to this gate.

This document does not grant that authorization. It defines what a future
authorization must explicitly accept.

## 4. Token measurement and settlement

Usage is read only from exactly one `turn.completed.usage` object. The required
nonnegative integer fields are `cached_input_tokens`, `input_tokens`,
`output_tokens`, and `reasoning_output_tokens`.

Accounting total is `input_tokens + output_tokens`. Cached input is already a
subset of input and is not subtracted. Reasoning output is already a subset of
output and is not added a second time. Missing, malformed, negative, or
internally inconsistent usage debits the attempt and its full 32,000-token
reservation, marks the attempt unsettled, and hard-stops. A reported total over
the reservation is `INVALID_RUN_BUDGET_BREACH`.

## 5. Fail-closed rate convention

The primary boundary is five fail-closed attempts out of the fixed 55-attempt
ITT protocol. The ppm value is derived reporting only:

`floor(5 * 1,000,000 / 55) = 90,909 ppm`.

The attempt cap takes precedence; ppm rounding cannot admit a sixth failure.

## 6. Missing `uniqueItems`

The frozen selector output schema does not emit `uniqueItems` for
`reason_codes`. The pinned local parser independently requires uniqueness.
Duplicate reason codes are never repaired or deduplicated; they produce
`SELECTOR_SCHEMA_INVALID`, execute the typed baseline fallback with paired
delta zero, and count as a fail-closed attempt.

## Provider-free replay

The append-only local tree contains freeze, preflight, and audit-graph nodes.
The freeze also embeds the live-gate implementation and preflight-script source
hashes, so replay cannot rely on the external manifest alone. Replay verifies
all three artifact hashes, canonical bytes, accepted D3 identities, external
executable pin, live source pins, and complete freeze/preflight recomputation.
The local tree is three files with canonical SHA-256:

`58228ac0ce9b954dc60e5e371543ee27287d8467f8dd6650c8a0e257ae816870`.

Passing this gate is necessary but not sufficient for live execution.
Independent review, explicit user freeze acceptance, a commit identity, and a
separate authorization explicitly covering the 6+49 continuation are required.
