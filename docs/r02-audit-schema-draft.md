# R02 audit schema draft

Status: **PROVIDER-FREE DATA-DESIGN DRAFT — NOT IMPLEMENTED**

Machine-readable catalog: `docs/r02-audit-schema-draft.json`

## Objective

R02 must audit episodes where the LLM is not called as carefully as episodes
where it is called. Triggering, candidate construction, candidate order, LLM
selection, baseline fallback, and final scoring are separate immutable events.

This draft extends R01's append-only hash graph. It does not replace the R01
transport, token ledger, replay, or fail-closed artifacts.

## Required episode graphs

### Trigger false

```text
fixture
  -> eligibility_decision(triggered=false)
  -> no_call_record
  -> baseline execution
  -> episode_result(delta=0)
```

The no-call record proves the provider-attempt counter did not change and that
request, response, and transport artifacts are absent.

### Trigger true but candidates collapse

```text
fixture
  -> eligibility_decision(triggered=true)
  -> candidate_set(K below frozen minimum after deduplication)
  -> no_call_record(reason=CANDIDATE_COLLAPSE)
  -> baseline execution
  -> episode_result(delta=0)
```

### Provider selection path

```text
fixture
  -> eligibility_decision
  -> candidate_set
  -> candidate_permutation
  -> selector_request + R01 transport/ledger graph
  -> selector_response
  -> execution_decision
  -> episode_result
```

## Pre-selection information barrier

The trigger, generator, permutation, and selector request must not contain:

- oracle decisions or utilities;
- oracle-baseline headroom values;
- hidden future returns;
- candidate oracle ranks;
- unblinded candidate-role labels in the selector request.

Provider-free stratum classification may use oracle headroom in a separate
sealed frame-building path. The artifact graph must prove that classification
output is unavailable to candidate generation and prompt construction except
for an opaque fixture identity already fixed before selection.

## Candidate identity

Each executable batch receives a canonical content hash and canonical candidate
ID before anonymization. The candidate-set artifact records semantic roles for
audit. The selector request receives only opaque presented IDs.

Permutation uses the frozen seed label `r02-candidate-order-v1`, fixture content
hash, and overlay-spec hash. Replay must recover both directions of the map and
prove every candidate occurs exactly once.

## No-call accounting

No-call episodes are first-class observations, not missing data. Every no-call
record must prove:

- why no call occurred;
- provider attempt count before and after;
- exact baseline and executed batch identity;
- absence of selector request, selector response, and transport artifacts;
- paired utility delta zero in the episode result.

Suggested reason-code enum:

- `TRIGGER_FALSE`;
- `CANDIDATE_COLLAPSE`;
- `PRE_PROVIDER_BUDGET_STOP`;
- `PRE_PROVIDER_INTEGRITY_STOP`.

Post-provider failures are not no-calls. They consume an attempt, retain the
full transport graph, and produce a typed baseline-fallback execution decision.

## Model identity

The selector-response graph keeps R01's requested-model, command-spec, executable
hash, and feature-gate evidence. A nullable `provider_model_echo` field is
reserved so an authenticated transport echo can be adopted without changing
the conceptual graph. Absence of echo must remain an explicit limitation.

## Replay invariants

Replay must fail closed unless all of these hold:

1. Every frozen fixture has exactly one terminal episode result.
2. Trigger decisions reproduce from frozen observable inputs.
3. Candidate sets reproduce from the frozen generator and configuration.
4. Baseline is present exactly and candidates are unique and valid.
5. Permutations reproduce from frozen seed inputs.
6. Selector responses map to one presented candidate or a typed baseline
   fallback.
7. The executed batch is byte-identical to a candidate; no later edit exists.
8. Provider-attempt and token ledgers reconcile with call and no-call episodes.
9. Oracle fields appear only after terminal selection/no-call identity exists.
10. Primary summaries include every fixture and assign zero delta to baseline
    executions.

## Implementation work still required

The JSON catalog is a field-level design, not executable validation. Before an
R02 preflight it must be converted into versioned Pydantic/JSON-schema contracts,
canonical serialization, append-only persistence, replay validators, and
negative tests for every forbidden edge and identity mismatch.

That implementation requires a separate user authorization and does not
authorize provider calls.
