# R02 D4-S6 provider-free runner, audit, and replay

## Scope

This draft implements the D4 execution state machine without opening an execution
capability. It creates no provider adapter, production entrypoint, LIVE
authorization artifact, provider call, Codex exec call, micro-pilot, retry,
replacement, resume, or production artifact-root run. The only executable test
boundary is an injected `OFFLINE_FAKE` transport writing to a temporary directory.

The accepted S5 freeze remains the authority. S6 binds its 69-case order,
2,208,000-token aggregate cap, 32,000-token pre-launch reservation, 900,000 ms
per-attempt timeout, settled fail-closed cap of 6, `NO_MICRO_PILOT`, and all ten
hard-stop conditions. It adds no discretionary continuation decision.

## State machine

Before transport invocation, the runner verifies S5 and sealed-frame identities,
rebuilds the exact 69 selector requests, checks the full prepared-plan digest,
persists the attempt reservation, and persists an `attempt_started` record. One
attempt slot and the full 32,000-token reserve must fit before launch. Reservations
are never recycled into attempt credit.

A settled response requires exactly one terminal usage event, nonnegative integer
usage, cached input no greater than input, reasoning output no greater than output,
exit code zero, no timeout, and `input_tokens + output_tokens <= 32,000`. Successful
usage debits that exact sum. Selector parse or acceptance failure is a settled
baseline fallback with paired delta zero; the seventh such fallback invalidates the
run. Timeout, nonzero exit, launch error, missing/invalid usage, or an over-reserve
report debits the full reserve and immediately invalidates the run. No later case,
retry, replacement, or resume is allowed.

The runner calculates and seals paired utilities but continuation never consults
them. Without a frozen hard stop it proceeds immediately to the next eligible case
in frame order; it never exposes interim outcomes or asks for a second authorization.

## Capability and root boundary

`OFFLINE_FAKE` authorization is a deterministic digest over the run ID and accepted
S5 freeze. It cannot carry provider, production-root, all-69 LIVE, micro-pilot,
retry, replacement, or resume authority. Its audit root must be outside the
repository, which makes every S6 test a temporary-root test.

The code defines the schema for a future external LIVE authorization, but S6 does
not create one. A future LIVE invocation would require both the embedded canonical
artifact and the byte-identical external file, a `LIVE_PROVIDER_PROCESS` transport,
and the exact single production root. No such transport implementation or
production entrypoint exists in this draft.

## Append-only audit

Each append writes, exclusively and with `fsync`, the canonical payload, its
hash-chain node, and a checkpoint anchor containing the full node history. A
complete run has this graph:

```text
run_authorization -> contract_binding -> run_plan
  -> (token_reservation -> attempt_started -> transport_result
      -> attempt_outcome -> continuation_decision -> run_ledger) x attempted cases
  -> run_terminal
```

An existing file rejects a new run. This is the concrete no-retry/no-resume guard,
not merely an accounting field.

## Replay

Replay rejects noncanonical JSON, missing files, orphan files, gaps, reordered
nodes, hash-chain drift, checkpoint drift, duplicate payload references, attempt
identity drift, reservation arithmetic drift, transport-call accounting drift,
continuation drift, and terminal-ledger drift. It rebuilds the sealed 69-case plan
and recomputes every settled selector acceptance, executed candidate, validation
hash, and paired utility. The runner does not return a terminal result until replay
matches it exactly.

## Interpretation boundary

This is provider-free implementation readiness only. It does not imply that a LIVE
run is authorized or that the incremental LLM effect will be identifiable. Exact
replication keeps the same candidate generator, so another 100% LLM-parsimony
agreement and `NOT_IDENTIFIED_REDUNDANT_SELECTOR` remains an expected, valid
outcome. The primary value of D4 remains system-vs-baseline replication; an
ambiguity-engineered mechanism study remains separate future research.
