# R02 overlay v2 — I0–I5 provider-free implementation

Status: `TECHNICALLY_ACCEPTED_PROVIDER_FREE_IMPLEMENTATION_FIXTURE_AND_LIVE_NO_GO`

Base and authority: implementation started from accepted implementation-plan commit `245adc2d1f023a87d1cbfd86a7b726aec810bd78` under the user's explicit I0–I5 provider-free implementation approval. This approval did not authorize fixture materialization, provider or Codex execution, private-data export, pilot or confirmatory LIVE work, retry/replacement/resume, or commit/push.

## Implemented boundary

- I0: strict Pydantic contracts, accepted payload/response schema byte pins, Draft 2020-12 metaschema and instance checks. `jsonschema` is a development-only dependency.
- I1: canonical public-only payload construction, metric recomputation, information-parity binding, strict JSON parsing, and single-decode RFC 6901 grounding.
- I2: the frozen 19-member deterministic public-information scorer family, integer arithmetic, canonical candidate identifiers, and candidate-order invariance.
- I3: policy selections sealed before hidden oracle utilities can be attached, exact candidate-set oracle binding, five-split non-overlap, deterministic scorer selection, append-only audit, and replay.
- I4: provider-free headroom labels and diagnostics, stratified bootstrap, information floors, complete 288-cell power grid, confirmatory power acceptance only when the two-sided 95% Wilson lower bound is at least 800,000 ppm, Wilson pilot gate, and fail-closed sizing.
- I5: 13-gate-to-test traceability, provider-capability static checks, focused tests, full overlay regression, canonical evidence, zero-call manifest, verifier, and review handoff.

Eight implementation modules were added under `v2/research/overlay/`; no transport or provider module was added. Runtime decision code receives public payload bytes only. Hidden oracle utility enters only after all compared selections are sealed and is evaluation-only.

## Verification result

- Focused I0–I5 suite: 27 passed, exit 0.
- Full `v2/research/overlay` suite: 433 passed, exit 0.
- Black check, isort check, and flake8 with repository-compatible `E501,E203,W503` ignores: exit 0.
- Provider calls, Codex executions, fixture/root materializations, pilot/confirmatory LIVE runs, retries, replacements, and resumes: all 0.

The machine-readable evidence is `docs/r02-overlay-v2-implementation-evidence.json`. Reproduction and independent technical review instructions are in `docs/r02-overlay-v2-implementation-review-handoff.md`.

## State and next order

The user technically accepted the provider-free I0–I5 implementation on
2026-07-19 after the clean verifier and 433-test review record. Organizational
independence is not established. This acceptance authorizes no fixture/root
materialization, private-data export, provider call, pilot or confirmatory LIVE
work, retry, replacement, or resume. Status-promotion commit/push remains a
separate authorization.
