# R02 D2a provider-free production implementation

Status: **IMPLEMENTED FOR OFFLINE VALIDATION — NO PROVIDER OR LIVE AUTHORITY**

Acceptance authority is recorded in `docs/r02-d1-final-acceptance.json` and is
bound to the accepted D1 commit, freeze SHA-256, and manifest SHA-256. The D1
freeze and manifest remain byte-unchanged.

## Production modules

- `v2/research/overlay/r02_contracts.py`: strict, frozen Pydantic contracts and
  cross-artifact invariants;
- `v2/research/overlay/r02_candidates.py`: freeze verification, exact trigger,
  four raw candidates, validate-before-dedup, canonical IDs, HMAC order,
  selector-safe payload, and provider-free episode preparation;
- `v2/research/overlay/r02_audit.py`: R02-specific append-only artifact store
  that rejects `.research_artifacts/r01` and every `r01-*` root or descendant,
  plus graph persistence;
- `v2/research/overlay/r02_replay.py`: fail-closed hash, topology, identity,
  no-call, candidate, permutation, and deterministic replay verification.

The candidate generator accepts only public fixture state plus the baseline
validation report. It does not accept the baseline score, oracle state,
headroom, future returns, or provider output. The selector-safe payload contains
only opaque presented IDs and action/quantity candidate contents.

## Provider-free terminal graphs

Trigger false:

```text
public_fixture -> eligibility_decision -> no_call_record
  -> execution_decision(BASELINE) -> episode_result(delta=0) -> preparation
```

Triggered candidate integrity failure:

```text
public_fixture -> eligibility_decision
  -> no_call_record(PRE_PROVIDER_INTEGRITY_STOP)
  -> execution_decision(BASELINE) -> episode_result(delta=0) -> preparation
```

Triggered candidate collapse retains the candidate-set node before the no-call
record. Triggered `K >= 2` preparation stops after candidate permutation in
`SELECTOR_ELIGIBLE_NOT_CALLED`; it creates no selector request, response,
transport, execution, or result artifact.

## Offline validation

Focused tests cover the six frozen D1 vectors, exact 49/50 bps boundary,
validate-before-dedup behavior, identity and HMAC mutations, selector blinding,
no-call accounting, append-only persistence, tampering, wrong anchors, wrong
fixtures, replay, acceptance boundaries, and unchanged frozen R01 source
identities.

Run:

```text
.venv/Scripts/python.exe -m pytest v2/research/overlay -q
```

## Still not authorized

This implementation does not finalize zero-call preflight, generate a new
fixture frame, freeze statistics or provider budget, call a provider, or run a
live R02 experiment.
