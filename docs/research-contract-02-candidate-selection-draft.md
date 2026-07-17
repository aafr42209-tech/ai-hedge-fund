# R02 Research Contract Draft: Baseline-Anchored Candidate Selection

Status: **PROVIDER-FREE DRAFT — NOT PREREGISTERED OR FROZEN**

Contract identity: `R02-baseline-anchored-candidate-selection-v0-draft`

Provider calls authorized: **no**

R02 execution authorized: **no**

## 1. Separation from R01

R01 tested the technical path for direct LLM portfolio generation. R02 asks a
different question: can a constrained selector add value when a deterministic
baseline and deterministic generator define the complete action space?

R01 remains sealed. R02 receives no confirmatory credit from R01 and may use
R01 only as immutable provenance and exploratory design motivation.

## 2. Research question

Does a prespecified trigger plus an LLM candidate selector improve system-level
utility relative to always executing the deterministic baseline, when the LLM
cannot create or edit portfolio decisions?

## 3. Draft primary hypothesis

Across the frozen target mixture of representative and headroom-positive
challenge strata, the baseline-anchored selective system has positive paired
mean utility delta relative to the deterministic baseline while satisfying all
prespecified safety gates.

The exact minimum effect `delta_min`, confidence procedure, sample size, and
decision thresholds are unresolved and must be frozen provider-free.

## 4. Experimental unit and strata

The primary experimental unit is a fixture, not an asset decision and not a
provider response. Repeated selector calls for one fixture, if retained, form a
cluster and are aggregated before primary analysis.

The sampling frame has two prespecified strata:

- `REPRESENTATIVE`: sampled from the intended deployment-like synthetic
  distribution without conditioning on oracle headroom;
- `CHALLENGE_HEADROOM`: fixtures whose oracle-minus-baseline utility gap exceeds
  a frozen provider-free threshold.

Oracle output may classify strata and score outcomes. It may not generate
candidates, determine candidate order, enter selector prompts, or change the
trigger after the frame is frozen. Stratum mixture weights must be frozen before
the first provider call.

## 5. System under comparison

Control: execute the existing deterministic baseline.

Treatment system:

1. Evaluate a deterministic trigger using frozen observable inputs.
2. If false, do not call the provider and execute the baseline.
3. If true, generate a deterministic candidate set.
4. If fewer than two distinct valid candidates remain, do not call the provider
   and execute the baseline.
5. Deterministically anonymize and permute candidates.
6. Ask the LLM to select one candidate ID.
7. Validate the response fail-closed.
8. Execute the selected candidate or the baseline fallback.

Every no-call fixture is part of the primary estimand with utility delta zero.

## 6. Candidate-generator contract

The generator must satisfy the common invariants in
`docs/r02-candidate-generator-options.md`.

Required properties:

- deterministic source and configuration identity;
- exact baseline candidate mandatory;
- no-change candidate mandatory when distinct;
- integer-lot executable candidates only;
- no oracle, future, or outcome input;
- canonical deduplication before presentation;
- frozen cardinality bounds and deterministic tie-breakers;
- no silent validator repair.

The exact generator is deliberately unresolved in this draft. Its algorithm,
test vectors, source hash, configuration hash, and candidate-set invariants are
a blocking preregistration item.

## 7. Selector response schema

The selector cannot emit asset actions or quantities. Draft response shape:

```json
{
  "selected_candidate_id": "PRESENTED-ID",
  "confidence": 87,
  "reason_codes": ["LOWER_DOWNSIDE"]
}
```

Constraints:

- `selected_candidate_id` must be one of the presented opaque IDs;
- `confidence` is a JSON integer from 0 through 100;
- `reason_codes` contains one to three values from a frozen enum;
- unknown or missing fields fail closed;
- free-form portfolio edits, veto, and scale fields are forbidden.

Confidence is logged but has no execution effect unless a threshold is
independently preregistered. R01 supplies no validated threshold.

## 8. Candidate anonymization and order

Presentation order is derived deterministically from:

```text
derive_seed(
  root_seed,
  "r02-candidate-order-v1",
  fixture_content_sha256,
  overlay_spec_sha256
)
```

The artifact graph records the seed label/hash, canonical candidate IDs,
original order, presented opaque IDs, presented order, and reversible
permutation map. Semantic roles are hidden from the selector but recoverable by
replay.

## 9. Primary and secondary estimands

Primary system-level estimand:

```text
Delta_system = weighted mean over all frozen fixtures of
               utility(executed treatment system) - utility(baseline)
```

No-trigger, candidate-collapse, and fail-closed fallback fixtures contribute
zero if the baseline is executed.

Secondary conditional estimand:

```text
Delta_triggered = mean paired utility delta among trigger-true fixtures
```

The secondary estimand describes selector behavior where intervention was
available. It cannot replace a failed or inconclusive primary result.

## 10. Trigger-rate and futility rule

Expected trigger rates by stratum, total N, and minimum triggered-fixture count
`M_min` must be jointly chosen by provider-free simulation.

If the realized eligible triggered count is below `M_min`, the result is
`INCONCLUSIVE_LOW_TRIGGER`, never PASS. Candidate collapse and transport failure
do not count as informative triggered selections unless the final statistical
plan explicitly says otherwise.

## 11. Safety and fail-closed behavior

Any of the following executes the baseline and records a typed disposition:

- trigger or generator schema drift;
- invalid, duplicate-only, or out-of-bound candidate set;
- candidate validation failure;
- permutation or identity mismatch;
- selector schema failure or unknown candidate ID;
- tool, transport, token, budget, or provenance violation;
- replay mismatch.

Whether a provider failure counts as zero-delta ITT or invalidates the run must
be frozen in the final statistical plan. It may not be decided after outcomes
are observed.

## 12. Claims

Permitted after a fully preregistered and completed evaluation:

- system-level utility effect for the frozen synthetic target mixture;
- trigger rate, candidate-selection frequency, and fallback rate;
- conditional triggered effect labeled secondary;
- structural validity and auditability.

Prohibited:

- live investment-performance or real-market claims;
- candidate-generator improvement claims not separately estimated;
- treating challenge-stratum results as population-wide results;
- thresholds, triggers, or candidates tuned on sealed outcomes and relabeled as
  preregistered;
- importing R01 development results as R02 confirmatory observations.

## 13. Audit and provenance

R02 inherits the validated append-only store, hash references, transport
capture, budget ledger, replay, and fail-closed principles from R01. It adds
first-class trigger, candidate-set, permutation, no-call, selection, and final
execution artifacts described in `docs/r02-audit-schema-draft.md`.

The schema reserves a nullable provider model-echo field. Command-spec identity
remains mandatory while transport echo is unavailable.

## 14. Gates

| Gate | Requirement | Current state |
| --- | --- | --- |
| R2-D0 | Contract, generator, statistics, and audit drafts reviewed | Open |
| R2-D1 | Exact generator and trigger frozen provider-free | Not authorized |
| R2-D2 | Implementation, tests, and zero-call preflight reviewed | Not authorized |
| R2-D3 | Explicit live micro-pilot approval against commit + preflight hash | Not authorized |
| R2-D4 | Sealed evaluation approval | Not authorized |

No draft in this package satisfies or bypasses a live gate.

## 15. Blocking freeze fields

- target distributions, stratum weights, and headroom threshold;
- trigger predicate and expected trigger rate by stratum;
- candidate-generator option, exact transforms, K, and tie-breakers;
- selector reason-code enum and any confidence-use rule;
- replicate policy and fixture clustering rule;
- `delta_min`, alpha/coverage, power, N, and `M_min`;
- treatment of fail-closed provider attempts in the estimand;
- model, transport, token, attempt, and cost budgets;
- implementation commit, manifest, preflight, and independent review hashes.
