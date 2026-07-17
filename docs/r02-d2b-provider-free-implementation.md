# R02 D2b provider-free production implementation

Date: 2026-07-17

Status: `IMPLEMENTED_PROVIDER_FREE_REVIEW_CANDIDATE`

Base commit: `7f9a998a32bf6835fd5ef6b14ebc79d674727128`

## Selector boundary

`r02_selector.py` implements one scripted-only boundary. It accepts only an
eligible D2a preparation, reconstructs the frozen selector-safe payload, embeds
that payload exactly once, and marks the prompt `DRAFT_NOT_FROZEN`. Contract
validation rejects prompt text that exposes frozen candidate roles, canonical
IDs, the permutation seed or map, oracle data, headroom, or future returns.

The response parser accepts one JSON object with exactly four fields:

- `schema_version = r02-selector-response-v1`
- `selected_candidate_id = PNN`
- integer `confidence` in `[0, 100]`
- one to three unique frozen `reason_codes`

It rejects prose wrappers, duplicate JSON keys, non-finite constants, fractional
confidence, extra or missing fields, unknown enums, and non-object responses.

## Acceptance and fallback

The presented ID is mapped internally only after strict parsing. The selected
canonical candidate is revalidated against the public fixture. Raw-invalid,
validator-fallback, or executable-mismatch results produce
`ACCEPTANCE_VALIDATION_FAILED`. An unknown presented ID produces
`UNKNOWN_PRESENTED_ID`; a schema failure produces `SELECTOR_SCHEMA_INVALID`.

All three typed failures execute the frozen baseline candidate and therefore
record paired utility delta `0`. An accepted candidate is scored deterministically
and records `executed utility - baseline utility` in the frozen integer utility
unit.

The primary deterministic baseline being raw-invalid is an eligibility invariant
failure, not a selector no-call outcome. The path fails closed with
`primary baseline is not executable`; it does not synthesize or repair a baseline.

## Attempt and token accounting

The scripted client must continue the D2a attempt counter exactly. A scripted
exchange increments the counter once. The ledger separately records input,
cached input, output, and reasoning-output tokens, and verifies total accounting
as input plus output. Every request, ledger, transport, response, acceptance,
fallback, execution, and result carries or hashes evidence carrying the same R02
identity. External provider calls remain the literal value `0`.

## Append-only graph and replay

Terminal graphs persist, in order:

```text
public_fixture -> eligibility_decision -> candidate_set
  -> candidate_permutation -> preparation -> selector_request
  -> selector_token_ledger -> selector_transport -> selector_raw_response
  -> selector_response -> acceptance_gate -> [baseline_fallback]
  -> execution_decision -> episode_result -> selection_run
```

Replay validates every artifact reference and model, verifies the raw response,
reconstructs D2a preparation, reruns the scripted selector with the recorded
attempt and token inputs, and requires canonical byte equality for the complete
selection run. The graph is terminal, append-only, provider-free, and non-live.

Generic artifact stores are also rejected at persistence time when rooted in an
R01 sealed tree; callers cannot bypass the R02-specific constructor guard.

## Offline validation

- D2b focused tests: `27 passed`
- R02 D1/D2a/D2b focused tests: `64 passed`
- Full overlay suite: `191 passed`
- Pydantic models whose JSON schemas generate: `38/38`
- Provider calls: `0`
- Live executions: `0`

## Still not authorized

This implementation does not freeze the prompt, create a fixture frame, select
or freeze statistics or budget, finalize zero-call preflight, call a provider,
or run a live experiment.
