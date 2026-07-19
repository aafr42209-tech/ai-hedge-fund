# R02 overlay v2 provider-free implementation plan

Date: 2026-07-19

Status: **TECHNICALLY ACCEPTED IMPLEMENTATION PLAN — IMPLEMENTATION NOT AUTHORIZED — LIVE NO-GO**

Base commit: `69bdac5bbad9c41f3ae1bd769a83faa699ead950`

## 1. Purpose and authority

This plan translates the technically accepted overlay v2 preregistration into
an exact future code-and-test boundary. It authorizes planning artifacts only.
It does not authorize implementation, research-fixture materialization,
provider or Codex execution, pilot or confirmatory LIVE execution, retry,
replacement, resume, commit, or push.

Technical acceptance was recorded on 2026-07-19 after Claude (Fable 5), in the
same local repository and same-session lineage, reproduced the provider-free
verifier and independently checked the nine-file diff and status-only scientific
normalization. The verdict was `ACCEPT` with zero blocking findings and two
informational implementation notes. Organizational independence is not
established. Acceptance authorizes commit and push of exactly this nine-file
planning change set; it does not authorize I0-I5 implementation or any fixture,
provider, private-data export, pilot, or LIVE action.

The accepted intervention remains new work, not a D3/D4 replication. D3/D4
showed that the old LLM selector was operationally redundant with parsimony
under an information set that exposed no utility-relevant public state. This
plan preserves that scoped interpretation.

## 2. Accepted inputs and status normalization

The immutable historical acceptance point is commit `69bdac5`. At that commit,
`docs/r02-overlay-v2-headroom-and-power-design.json` retained the stale
`DRAFT_PROVIDER_FREE_REVIEW_REQUIRED` analysis status even though the
preregistration package had been technically accepted. This planning layer
changes only that component status to
`TECHNICALLY_ACCEPTED_PROVIDER_FREE_IMPLEMENTATION_PLANNING_INPUT`, updates the
dependent preregistration pin, and rebuilds the zero-call/review hash chain.
Scientific values, power cells, pilot operating characteristics, thresholds,
budgets, and authorization boundaries remain unchanged.

Organizational independence remains unestablished. The recorded acceptance is
same-session-lineage technical verification.

## 3. Future implementation units

No listed file may be created until a separate implementation approval.

1. `r02_v2_contracts.py`
   - strict Pydantic models for payload v2, response v2, reason codes, policy
     identity, failure labels, and append-only record envelopes;
   - exact JSON Schema 2020-12 parity with the accepted schema drafts;
   - no provider client, process launcher, credential field, or network import.
2. `r02_v2_payload.py`
   - builds the canonical public payload from an already supplied public episode
     and accepted D4 candidate set;
   - recomputes every public metric with signed integer arithmetic;
   - rejects fixture IDs, seeds, split labels, hidden regime, hidden expected
     returns, oracle scores, and unexported repository state.
3. `r02_v2_grounding.py`
   - parses RFC 6901 pointers with exactly one decode;
   - accepts only `~0` and `~1`, canonical nonnegative array indexes, and
     in-bounds values;
   - rejects `-`, leading-zero indexes, missing targets, duplicate reasons,
     unknown codes, and wrong candidate scope.
4. `r02_v2_comparator.py`
   - implements all 19 frozen public-information scorer configurations;
   - consumes only the exact canonical payload bytes available to the LLM;
   - uses canonical candidate ID for every tie, never presented order.
5. `r02_v2_selection.py`
   - selects the public scorer on the comparator-selection split;
   - permits hidden oracle scoring only after each policy selection is sealed;
   - writes replayable selection summaries without crossing per-configuration
     outcomes into headroom validation.
6. `r02_v2_headroom.py`
   - evaluates oracle-minus-selected-public-scorer headroom on the untouched
     validation split;
   - implements information floors, stratified PCG64 bootstrap, zero
     nullification, literal leave-one-out, and 5/10 percent within-stratum
     winsorization diagnostics;
   - cannot materialize a frame or invoke a provider.
7. `r02_v2_power.py`
   - implements the full frozen sensitivity grid and least-powered-cell rule;
   - derives confirmatory sample size only from the accepted formulas and a
     future blinded pilot's permitted aggregate counts;
   - never consumes pilot utility.
8. `r02_v2_audit.py`
   - canonical append-only records, digest binding, replay, and typed hard-stop
     evidence for the provider-free implementation;
   - contains no provider-capable transport.

All modules live under `v2/research/overlay/`. Tests use matching
`test_r02_v2_*.py` names in the same package.

## 4. Arithmetic and canonicalization

- Number type: signed integer fixed point only.
- Canonical JSON: UTF-8, sorted keys, compact separators, no terminal newline.
- Digest: SHA-256 of canonical bytes.
- Division: `round_ratio_half_even`; intermediate rounding is forbidden unless
  the accepted formula explicitly calls for it.
- Transaction costs: commission plus separately ceiling-rounded half-spread and
  slippage.
- Public forecast for each asset:

  ```text
  RHE(
    sum(weight_bps[S] * signal_bps[S] * confidence_bps[S])
    * forecast_scale_bps,
    10000^3
  )
  ```

- Nonzero scorer utility reuses `score_with_returns` exactly:
  `return_e12 - risk_e12 - cost_e12`.
- The zero-forecast scorer uses zero public returns and the same risk/cost DAG.
- Public metrics must reproduce from payload bytes and candidate decisions;
  serialized metrics are assertions, not trusted inputs.

Any formula, unit, rounding point, scorer family member, or tie-break change
requires preregistration v2 replacement before implementation continues.

## 5. Information parity and oracle isolation

The deterministic scorer and LLM v2 must receive byte-identical payloads and
independently bind the same SHA-256. The deterministic path may not read any
extra fixture object or repository state.

The hidden oracle is evaluation-only. The implementation must enforce separate
types and call boundaries:

1. policy selection returns a candidate ID and sealed policy record;
2. only then may an evaluation function receive hidden expected returns;
3. hidden values may not influence payload construction, scorer ranking within
   a fixture, response parsing, fallback, or candidate generation;
4. a failed headroom gate cannot trigger scorer-family reselection.

## 6. Ordered implementation phases

Each phase is provider-free and requires its own clean evidence before the next.

1. **I0 — contracts and schema parity**
   - implement strict models and local schema validation;
   - freeze generated-schema hashes against the accepted drafts.
2. **I1 — canonical payload and grounding**
   - implement public metric recomputation, hidden-field guards, canonical bytes,
     payload digest binding, and response grounding;
   - add malformed-pointer and wrong-scope negative matrices.
3. **I2 — deterministic scorer family**
   - implement 19 configurations, permutation invariance, integer arithmetic,
     candidate-ID tie-breaking, and frozen scorer IDs.
4. **I3 — selection, audit, and replay**
   - implement split-scoped scorer selection records and exact replay;
   - prove selection/headroom split non-overlap without generating research
     frames.
5. **I4 — headroom and power engines**
   - implement gate labels, diagnostics, PCG64 domain-separated seeds, sensitivity
     grid, Wilson bounds, and sample-size rule;
   - execute only unit/property tests on fixed in-memory vectors.
6. **I5 — provider-free integration review**
   - run focused and full overlay suites;
   - seal implementation source/test hashes and a zero-call manifest;
   - hand off for technical review.

Implementation approval may authorize I0–I5 code and fixed in-memory test
vectors. It must not be interpreted as permission to materialize schema,
comparator-selection, headroom, pilot, or confirmatory research fixtures.

## 7. Required tests

- schema/metaschema validation and generated-schema byte equality;
- canonical JSON and digest reproducibility;
- payload information parity and forbidden-field rejection;
- public metric recomputation against fixed hand-calculated vectors;
- all 19 scorer identities and forecast formulas;
- candidate-order permutation invariance and canonical-ID ties;
- strict RFC 6901 escape/index/bounds/scope matrix;
- response fail-closed behavior, confidence bounds, unique reasons, and no free
  text or portfolio edits;
- hidden-oracle type and call-order isolation;
- comparator-selection replay and split-root non-overlap;
- headroom information floors and all decision labels;
- deterministic bootstrap and diagnostic indexing;
- complete power sensitivity grid, no pilot-utility pruning, and worst-cell
  governance;
- failure ITT values and no dropped failures;
- import/static scan proving no provider client, network call, credential read,
  subprocess launch, or production-root materialization.

Negative tests must fail for the intended typed reason, not any exception.

## 8. Evidence and commit design

Future implementation evidence must include:

- exact approved plan hash and accepted preregistration commit;
- source and test hashes;
- generated schema hashes;
- focused and full-suite commands with exit codes;
- provider/LIVE/fixture/production-root counters fixed at zero;
- append-only replay report;
- reviewer provenance and independence label.

Suggested implementation commits, each separately approved:

1. `feat: add R02 overlay v2 contracts and canonical payload`
2. `feat: add R02 overlay v2 public comparator and grounding`
3. `feat: add R02 overlay v2 provider-free headroom and power engines`
4. `docs: seal R02 overlay v2 provider-free implementation review`

No commit or push is authorized by this plan draft.

## 9. Stop conditions

Stop provider-free implementation on any schema mismatch, hidden-field reach,
payload-byte divergence, floating-point arithmetic, unresolved formula,
presented-order tie, split overlap, nonreplayable artifact, provider-capable
import, research-fixture write, or unexpected repository change.

Provider calls remain zero regardless of implementation readiness. A later
headroom execution requires separately frozen fixture generation and seed
material, and any pilot requires separate private-data export and LIVE approval.

## 10. Review handoff

Review must verify scientific invariants, exact code scope, arithmetic formulas,
test completeness, status normalization, hash bindings, and all zero-call
boundaries. Acceptance of this plan would authorize neither implementation nor
commit/push; those remain separate user decisions.
