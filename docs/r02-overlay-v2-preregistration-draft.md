# R02 overlay v2 preregistration draft

Status: **TECHNICALLY ACCEPTED DRAFT — IMPLEMENTATION NOT AUTHORIZED — LIVE NO-GO**

Controlling handoff: `docs/r02-overlay-v2-preregistration-design-handoff.md`

Base commit: `6774e846652afe81981928a1b2d9755c1a0d9221`

Technical acceptance: `Claude (Fable 5)`, same-session-lineage verification,
`2026-07-19`. All blocking findings are closed and the three nonblocking findings
were revised and independently recalculated. Organizational independence is not
established. Acceptance authorizes this ten-file draft commit and push only; it
does not authorize implementation, fixture generation, provider calls, or LIVE
execution.

## 1. Scientific question

Given byte-identical decision-time public information, does LLM overlay v2 add
full-frame ITT utility over the strongest preregistered deterministic
public-information candidate selector?

This is a new intervention. It is not a direct D3/D4 replication.

## 2. Prior-result scope

The required interpretation is sealed in
`docs/r02-overlay-v2-d3-d4-scope-annotation.md`.

- D3/D4 do not establish general LLM incapability.
- D2b did not expose utility-relevant public context, so utility-aware LLM value
  was not identifiable.
- D2b itself is operationally redundant because parsimony reproduced `55/55`
  and `69/69` selections.
- D4 primary replication remains supported but fragile; selector replacement
  does not change that robustness label.

## 3. Information sets

### 3.1 Policy-visible public information

Both tier-2 deterministic scoring and LLM v2 receive the exact canonical bytes
defined by `docs/r02-overlay-v2-payload-schema-draft.json`.

| Payload field | Authoritative source | Treatment |
|---|---|---|
| asset price, lot size, holdings | `PublicEpisode.assets` | copied exactly |
| signals and signal confidences | `AssetState.signals_bps`, `confidences_bps` | copied exactly |
| asset cap and costs | `max_weight_bps`, `costs` | copied exactly |
| cash, covariance, gross limit, lambda, max trade lots | `PublicEpisode` | copied exactly |
| pretrade equity | `PublicEpisode.pretrade_equity_cents` | deterministic integer derivation |
| presented candidates | frozen candidate permutation | opaque IDs plus action/quantity |
| projected holdings | public holdings plus signed candidate quantity | deterministic integer derivation |
| transaction cost | existing validator cost ledger | deterministic integer derivation |
| gross/max weight | projected public holdings and prices | round-half-even integer derivation |
| variance numerator | projected weights and public covariance | deterministic integer derivation |

The final implementation contract must pin the exact formulas, units, rounding,
and source-code hashes for every derived metric before any frame is materialized.

### 3.2 Explicit exclusions

The payload excludes:

- `case_id` and `seed_hex`;
- hidden `regime`;
- hidden `expected_returns_bps`;
- oracle candidate IDs, utility, regret, rank, or headroom;
- split labels and fixture provenance;
- canonical candidate IDs and any presented-to-canonical mapping;
- credentials, secrets, provider metadata, or prior responses.

`score_episode` uses hidden expected returns, so oracle scoring is evaluation-only
and occurs strictly after policy selection.

### 3.3 Information parity

One canonical payload is written per fixture. Its SHA-256 is bound independently
to the deterministic scorer request and LLM request. Byte inequality, extra
repository reads, or hidden-field access is a hard stop.

### 3.4 Candidate population and generator

Overlay v2 retains the accepted D4 provider-free trigger and candidate generator
to isolate the selector intervention. A fixture is selector-eligible only when a
baseline trade exists and the maximum traded effective cost is at least `50bps`.

The generator proposes the same public-information roles before deduplication:

- deterministic baseline;
- no change;
- half baseline delta;
- drop the maximum-cost baseline trade.

Canonical deduplication leaves two to four candidates, followed by the accepted
opaque-ID permutation. The generator may not read hidden regime, expected
returns, or oracle scores.

Nontrigger fixtures make no provider call and contribute zero to selector
contrasts in the full-frame ITT. If this unchanged generator leaves inadequate
headroom, overlay v2 stops. Changing the trigger or candidate generator is a new
intervention version with new design and evaluation splits, not a post-gate
repair.

## 4. Response and grounding contract

The draft response schema permits only:

- schema version;
- one presented candidate ID;
- integer confidence in `0..100`;
- one to four structured reasons;
- one to six RFC 6901 payload-field references per reason.

Free text and portfolio edits are forbidden. Every field reference must resolve
against the exact bound payload and have the correct scope. Missing, invented,
duplicate, unknown, or wrong-scope references fail closed and count toward the
grounding-failure endpoint.

Each field reference is at most `256` characters. RFC 6901 decoding occurs
exactly once; only `~0` and `~1` escapes are accepted. Array tokens must be
in-bounds canonical nonnegative decimal indexes with no leading zeros. The `-`
append token is forbidden.

Candidate reason codes are:

- `RISK_CONCENTRATION`;
- `POSITION_ASYMMETRY`;
- `PUBLIC_SIGNAL_ALIGNMENT`;
- `CROSS_ASSET_INTERACTION`;
- `COST_TRADEOFF`;
- `PARSIMONY`;
- `TIE_BREAK`.

These remain draft values until independent review accepts the schema.

## 5. Policy hierarchy

1. `PARSIMONY_V1`, the accepted D4 deterministic selector;
2. `PUBLIC_SCORE_V2`, selected provider-free from the frozen family;
3. `LLM_OVERLAY_V2`, a new provider-backed intervention.

The primary comparator is tier 2. Parsimony is a continuity endpoint.

The proposed tier-2 family has 19 configurations: six signal-weight vectors
(equal plus one heavy vector per signal) crossed with forecast scales `150`,
`300`, and `600`, plus a zero-forecast minimum-risk/cost scorer. All use existing
integer validation, cost, risk, and `score_with_returns` arithmetic. Details and
tie-breaks are in
`docs/r02-overlay-v2-deterministic-comparator-design.md`.

## 6. Split firewall

Five independent roots and seeds are mandatory:

1. schema/generator development;
2. comparator selection;
3. provider-free headroom validation;
4. blinded LLM discordance pilot;
5. confirmatory LIVE evaluation.

No fixture is reused. The comparator family is frozen before split 2 and the
selected scorer is immutable before split 3. A failed headroom gate may not cause
reselection. Pilot fixtures are permanently excluded from confirmation.

Each frame requires a separate commitment, independent reveal, deterministic
resolution, materialization approval, and provenance review.

## 7. Deterministic comparator selection

The comparator-selection split chooses one scorer by target-stratum weighted
full-frame oracle-scored utility after each scorer makes its choice using public
payload bytes only.

Tie-break order:

1. lower oracle regret;
2. fewer invalid/fallback cases;
3. lower frozen complexity rank;
4. lower forecast scale;
5. ASCII scorer ID.

Only the selected scorer ID and configuration cross into headroom validation.

## 8. Provider-free headroom gate

On the untouched headroom-validation split, define fixture headroom as:

`hidden-oracle-optimal candidate utility - selected PUBLIC_SCORE_V2 utility`

Both candidates are restricted to the same presented candidate set. Oracle ties
use canonical candidate ID, never presented order.

Draft pass conditions:

- representative `N >= 150`, challenge `N >= 50`;
- at least 20 oracle/scorer disagreements total and 5 per stratum;
- target-weighted mean 95% stratified-bootstrap lower bound strictly greater than
  `50,000,000` e12;
- all validity checks pass;
- concentration, zero-nullification, literal leave-one-out, and 5%/10%
  winsorization diagnostics are reported.

Failure or low information stops overlay v2 with zero provider calls. Passing
shows only that public-information improvement is possible.

## 9. Prospective power

The primary minimum relevant incremental effect is provisionally `50,000,000`
e12, two-sided alpha is `0.05`, and minimum power is `0.80`.

Before pilot authorization, provider-free stratified simulation must determine a
utility-powered confirmatory sample size using only accepted historical evidence
and headroom-validation outcomes. Pilot utility is not disclosed and cannot
change utility-effect assumptions.

The blinded pilot estimates only LLM/comparator discordance. Wilson 95% lower
bounds by stratum feed a frozen sample-size rule that must support at least 20
total and 5 per-stratum discordances. The final sample is the greater of utility-
powered and discordance-powered sizes, rounded to the frozen 3:1 target-stratum
allocation, capped at `N=400`.

If the conservative rule cannot meet both power requirements within the cap, the
program stops before confirmatory LIVE authorization.

Utility power must be evaluated over a frozen sensitivity grid rather than one
unverifiable variance estimate. Draft grid axes are:

- discordance rate: `5%`, `10%`, `20%`;
- discordance-conditional mean effect: `250M`, `500M`, `1B`, `2B` e12;
- discordance-conditional standard deviation: `250M`, `500M`, `1B`, `2B` e12;
- challenge/representative mean ratio: `0.5`, `1.0`, `1.5`;
- fail-closed rate: `0%`, `5%`.

Only cells whose implied full-frame mean is at least `50M` e12 are relevant to
the minimum-effect claim. Every included cell must achieve at least `80%` power
within `N <= 400`; the least-powered included cell governs `GO/NO_GO`. Pilot
utility may not prune the grid or select a favorable cell.

## 10. Blinded micro-pilot draft

Candidate pilot size: `40` fixtures (`30` representative, `10`
`CHALLENGE_HEADROOM`). Minimum valid settled count: `38`, with at least `29`
representative and `9` challenge attempts valid and settled. Pilot fixtures never
enter confirmation.

Draft pilot budget: at most `40` external calls, `32,000` reserved tokens per
attempt, `1,280,000` total reserved tokens, `900,000ms` per attempt, at most `2`
settled failures, no unsettled attempt, and retry/replacement/resume all zero.

Before sample-size and go/no-go freeze, permitted disclosure is limited to valid
settled count and LLM/comparator discordance counts total and by stratum. Utility,
regret, fixture identity, and per-fixture outcomes remain blinded.

After disclosure, only mechanically determined confirmatory sample size and
`GO/NO_GO` may change. Payload, schemas, prompts, reason codes, comparator,
parser, fallback, generator, estimands, and thresholds are immutable.

The pilot and confirmatory run must be no more than 72 hours apart and match all
observable model, executable, CLI, command, schema, prompt, sampling, and
reasoning pins. Observable drift is a hard stop. Matching pins do not prove
provider-side weights or routing are unchanged; missing provider metadata is an
explicit limitation.

This draft does not authorize the pilot or any provider call.

The `40`-fixture pilot is intentionally a conservative fail-safe. Assuming every
attempt is valid and the true discordance rate is independently `10%` in both
strata, the frozen Wilson/max-`N` rule requires at least `5` discordances total,
`2` representative, and `2` challenge. Its exact binomial `NO_GO` probability is
approximately `0.828676`; observing `4/40` yields a Wilson lower bound near
`0.039580`, supporting only about `16` discordances at `N=400`. No second-stage
pilot or pilot-size adaptation is authorized in this version.

## 11. Confirmatory endpoints

### 11.1 Primary

Full-frame target-weighted ITT:

`LLM_OVERLAY_V2 utility - PUBLIC_SCORE_V2 utility`

Agreement contributes zero. On LLM transport, schema, grounding, acceptance, or
other fail-closed paths, the executed policy is `PUBLIC_SCORE_V2` and incremental
utility is zero. Failures are never dropped. Provider cost and failure remain
separate operational endpoints.

### 11.2 Secondary

- LLM v2 minus parsimony full-frame ITT;
- PUBLIC_SCORE_V2 minus parsimony;
- agreement and total/per-stratum discordance with intervals;
- evaluation-only oracle regret for all tiers;
- invalid, grounding-failure, fallback, timeout, and unsettled rates;
- tokens, latency, and monetary/operational cost;
- confidence calibration for selecting an oracle-optimal presented candidate.

Discordant-only utility is descriptive because discordance is policy-selected.

Calibration uses hidden oracle information only after selection. Oracle ties,
proper scoring rule, bins, and minimum sample count must be frozen before pilot.

## 12. Execution and failure boundaries

Future pilot and confirmatory contracts must independently freeze:

- provider-attempt and token caps;
- per-attempt timeout;
- settled-failure and unsettled hard stops;
- exactly one continuous execution sequence per authorization;
- retry, replacement, and resume counts at zero;
- append-only payload/node/anchor audit;
- transport evidence and terminal replay;
- separate explicit private-data export and LIVE approvals.

Unknown fields, missing references, payload drift, prompt/schema drift, candidate
mapping drift, model/executable drift, nonzero exit, timeout, parse error,
unsettled attempt, audit mismatch, or budget breach fails closed.

## 13. Ordered authorization gates

1. independent review and acceptance of these drafts;
2. separate schema/comparator implementation approval;
3. provider-free tests and implementation review;
4. comparator-selection frame freeze and materialization approval;
5. comparator selection and independent replay;
6. headroom-validation frame freeze and materialization approval;
7. provider-free headroom gate execution and review;
8. pilot freeze and budget review;
9. explicit private-data export and pilot LIVE approval;
10. pilot blind-aggregate review and mechanical sample-size freeze;
11. confirmatory frame/budget/identity/authorization freezes;
12. explicit private-data export and confirmatory LIVE approval.

No later gate is implied by an earlier approval.

## 14. Draft pins

- controlling handoff:
  `e889e954bc6841e5cccedcb212d48f401b78818bd3929dc6010989c35ac0baa8`;
- D3/D4 scope annotation:
  `8d9526f4d288487d410b511b6dc127c076446e4d15489ce2e40d6b1d345889cd`;
- payload schema draft:
  `6a827af6ff6c56f2b4db1c575a1fe2890417ac8feba1ffbb0feb9bec3e1456d5`;
- response schema draft:
  `963a7fb8ddfa002402e44e94518c6fd4ba3aa964b5a5d353eae09480bd9859c1`;
- deterministic comparator design:
  `3952c505b998f397c9aa7b72f8ad0b6e8e48dd4081b297cdca2652a319705676`;
- headroom and power design:
  `30f79b7b87580586b44a9b829f32ec97c59f263db45c7b22e133b54e7e55d356`.

These are draft pins. Any review change requires regeneration of downstream pins
and a fresh zero-call manifest.

## 15. Accepted technical-review decisions

The technical reviewer accepted the following draft choices after the recorded
revisions:

- the 19-member scorer family;
- `50,000,000` e12 headroom and incremental-effect thresholds;
- `40`-fixture pilot and `38` valid-settled floor;
- 72-hour pilot/confirmatory identity window;
- `N=400` confirmatory cap;
- 20 total and 5 per-stratum discordance floors;
- derived public candidate metrics and exact integer formulas;
- reason-code semantics and permitted field-reference scopes;
- utility power simulation assumptions and calibration scoring rule.

Exact derived-metric formulas, metaschema validation, and implementation source
pins remain implementation-phase obligations. Provider calls and LIVE execution
remain zero until their later ordered gates and explicit approvals.
