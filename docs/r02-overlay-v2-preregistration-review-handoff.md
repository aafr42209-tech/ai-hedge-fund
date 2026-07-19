# R02 overlay v2 preregistration draft review handoff

Status: **TECHNICAL VERIFICATION ACCEPTED — ORGANIZATIONAL INDEPENDENCE NOT ESTABLISHED — LIVE NO-GO**

Base commit: `6774e846652afe81981928a1b2d9755c1a0d9221`

Controlling handoff:
`docs/r02-overlay-v2-preregistration-design-handoff.md`

This review covers design drafts only. It does not authorize implementation,
fixture materialization, provider calls, pilot execution, confirmatory execution,
retry, replacement, resume, commit, or push.

## 0. Received technical review

- reviewer: `Claude (Fable 5)`;
- environment and date: same local repository environment, `2026-07-19`;
- reviewed state: base `6774e846652afe81981928a1b2d9755c1a0d9221`
  plus ten untracked drafts;
- reviewed handoff SHA-256:
  `1caa485dd6caa60c08476114ad80bd630557789d4c28ad61a2a3570c902b0ffd`;
- relationship: same session lineage that participated in D4 and v2 design;
- independence: technical verification only; organizational independence is not
  established;
- reproduced command: v2 verifier exit `0`, negative tests `5`, provider calls
  `0`, LIVE runs `0`;
- reviewed pins: all ten reviewed file hashes matched;
- disposition: zero blocking findings, three nonblocking findings, conditional
  acceptance.

Revision disposition:

1. power sensitivity grid: revised; discordance-conditional mean and variance
   grid is explicit and the least-powered included cell governs `GO/NO_GO`;
2. field references: revised; `maxLength=256`, single RFC 6901 decoding,
   `~0/~1` escapes, canonical in-bounds array indexes, and forbidden `-` token;
3. pilot operating characteristic: documented as an intentional conservative
   fail-safe, including exact `10%`-discordance `NO_GO` probability.

These revisions required re-verification and explicit acceptance. Conditional
acceptance was not treated as final acceptance.

Final technical disposition after re-verification:

- verifier marker reproduced with `negative_tests=7`, provider calls `0`, and
  LIVE runs `0`;
- power-grid cells, RFC 6901 constraints, Wilson thresholds, and the exact
  `828676ppm` pilot `NO_GO` probability were independently recalculated;
- all three nonblocking findings are closed;
- explicit verdict: `ACCEPT`;
- accepted pre-promotion review-handoff SHA-256:
  `b1782221e1463962b9179f0218ab4bac9971de867b349ce717598ff75d5ac52d`;
- commit and push of exactly these ten drafts are separately authorized;
- implementation, fixtures, provider calls, pilot, and LIVE remain unauthorized.

Implementation-planning status normalization (2026-07-19):

- the accepted commit `69bdac5bbad9c41f3ae1bd769a83faa699ead950`
  remains the immutable pre-normalization anchor;
- the nonblocking stale `analysis_status` observation was resolved by changing
  only the headroom/power component status to
  `TECHNICALLY_ACCEPTED_PROVIDER_FREE_IMPLEMENTATION_PLANNING_INPUT`;
- dependent preregistration and zero-call hashes were regenerated;
- scientific values and the accepted authorization boundary did not change;
- implementation planning is authorized, but implementation, fixture
  materialization, provider calls, LIVE, commit, and push remain unauthorized.

Implementation-plan final disposition (2026-07-19):

- Claude (Fable 5), same-session lineage and not organizationally independent,
  reproduced the implementation-plan verifier and returned `ACCEPT` with zero
  blocking findings and two informational implementation obligations;
- the accepted pre-promotion implementation-plan review-handoff SHA-256 is
  `9d9440d8e0b53a3734b963657a6d9e33b9defd2d97cecf32879165c6e8a0b830`;
- the user explicitly accepted the plan and authorized commit and push of the
  exact nine-file planning change set;
- implementation, fixtures, provider calls, private-data export, pilot, and
  LIVE remain unauthorized.

## 1. Reviewer provenance record

The reviewer must record:

- reviewer role or stable identifier;
- review environment and date;
- reviewed base commit and artifact digests;
- relationship to the drafting session;
- whether organizational independence is established;
- commands executed and exit codes;
- blocking and nonblocking findings.

An unidentified or same-session reproduction is technical verification, not an
organizationally independent review.

## 2. Pinned review set

- `docs/r02-overlay-v2-d3-d4-scope-annotation.md`:
  `375d65a4a95fece6de02138b88003d9593f1fac8bc38227eebf981bffcd2c283`
- `docs/r02-overlay-v2-deterministic-comparator-design.md`:
  `3952c505b998f397c9aa7b72f8ad0b6e8e48dd4081b297cdca2652a319705676`
- `docs/r02-overlay-v2-headroom-and-power-design.json`:
  `933de346ed9a1482521e1c35c18f367f494f5f9fa32458c575526dff1c2c1d94`
- `docs/r02-overlay-v2-payload-schema-draft.json`:
  `6a827af6ff6c56f2b4db1c575a1fe2890417ac8feba1ffbb0feb9bec3e1456d5`
- `docs/r02-overlay-v2-preregistration-draft.json`:
  `14503448dc6f5f7ca5b43ef093d6470852029089abb117fa06dcbfdfc43adc88`
- `docs/r02-overlay-v2-preregistration-draft.md`:
  `566f59fd6f5a98dca1f7af972bd1ce206c5c36b3ce9f3bc85dd6f9b86174f3d7`
- `docs/r02-overlay-v2-response-schema-draft.json`:
  `963a7fb8ddfa002402e44e94518c6fd4ba3aa964b5a5d353eae09480bd9859c1`
- `docs/r02-overlay-v2-zero-call-manifest.json`:
  `65a3fc3f7634b80e25a765054752690608e0f65818d39dc50d62f670f815d151`
- `scripts/r02_overlay_v2_preregistration_verify.py`:
  `611bed57203ffc6bfe3fb3609b08b3932947f02845395dc6791d278c3820c0ad`

The controlling handoff SHA-256 is
`e889e954bc6841e5cccedcb212d48f401b78818bd3929dc6010989c35ac0baa8`.

## 3. Required review questions

### 3.1 Scope and interpretation

- Does the annotation avoid generalizing D3/D4 to LLM capability?
- Does it still preserve the operational redundancy finding for D2b?
- Are fragile replication and selector redundancy kept separate?

### 3.2 Information boundary

- Do both policies receive byte-identical payload v2 bytes?
- Is every payload field sourced from `PublicEpisode` or a deterministic public
  derivation?
- Are hidden regime, hidden expected returns, fixture identity, seeds, split
  labels, oracle outputs, and canonical mappings absent?
- Are privacy/export classifications adequate for a future explicit LIVE export
  approval?

### 3.3 Payload and response schemas

- Are all field units, ranges, ordering, and missing-value rules unambiguous?
- Can every public candidate metric be reproduced with integer arithmetic?
- Are reason-code semantics and allowed RFC 6901 reference scopes sufficiently
  narrow?
- Do missing, invented, duplicate, and wrong-scope references fail closed?
- Is confidence observational only until separately validated?

The repository environment has no installed `jsonschema` or `fastjsonschema`
package. The included verifier checks canonical JSON, local `$ref` resolution,
required draft invariants, and cross-pins; it does not perform full external
Draft 2020-12 metaschema validation. The reviewer should perform an independent
metaschema review or explicitly record that limitation before schema acceptance.

### 3.4 Candidate population

- Does retaining the D4 50bps trigger and four public candidate roles isolate the
  selector intervention appropriately?
- Is zero full-frame ITT contribution for nontrigger fixtures correct?
- Is stopping rather than modifying the generator after a failed headroom gate
  sufficiently explicit?

### 3.5 Deterministic comparator

- Is the 19-member family finite, reproducible, and free of hidden inputs?
- Is the scorer-selection objective scientifically appropriate?
- Are complexity and tie-break rules outcome-independent?
- Are comparator-selection and headroom-validation splits truly disjoint?
- Is one selection split adequate, or is a frozen nested design required?

### 3.6 Headroom and power

- Is oracle headroom measured against the selected tier-2 scorer within the same
  candidate set?
- Is a `50,000,000` e12 lower-bound gate economically and statistically justified?
- Are 150/50 minimum stratum sizes and 20/5 discordance floors justified?
- Does the utility-power simulation avoid using blinded pilot utility?
- Is `N=400` a defensible cap?
- Are concentration diagnostics sufficient to prevent another unqualified robust
  claim?

### 3.7 Blinded pilot and identity

- Are `40` pilot fixtures and a `38` valid-settled floor adequate?
- Can disclosed aggregates support the frozen sample-size rule without tuning?
- Is the 72-hour pilot-to-confirmatory limit operationally realistic?
- Are all observable model and executable pins captured?
- Is provider-side identity uncertainty stated without overclaiming?

### 3.8 Estimands and failure accounting

- Is full-frame ITT LLM minus tier-2 the correct primary endpoint?
- Is zero incremental utility on agreement and fail-closed tier-2 execution the
  correct system estimand?
- Are provider cost, latency, failure, grounding, and calibration endpoints kept
  separate?
- Are discordant-only summaries clearly nonconfirmatory?

## 4. Reproduction commands

```powershell
.venv\Scripts\python.exe scripts\r02_overlay_v2_preregistration_verify.py

git status --short
git diff --check
git rev-parse HEAD
git rev-parse '@{upstream}'
```

Expected verifier marker:

```text
PASS_R02_OVERLAY_V2_PROVIDER_FREE_PREREGISTRATION_DRAFT negative_tests=7 provider_calls=0 live_runs=0
```

Expected repository state before any review edit:

- HEAD and upstream equal
  `6774e846652afe81981928a1b2d9755c1a0d9221`;
- exactly ten draft/verifier files are untracked;
- all source and artifact pins reproduce;
- provider calls and LIVE runs remain zero.

## 5. Decisions requiring explicit disposition

The reviewer must accept, revise, or reject each item:

1. payload public-field inventory and derived metrics;
2. response reason vocabulary and field-reference semantics;
3. 19-member deterministic scorer family;
4. comparator-selection rule and split design;
5. `50,000,000` e12 headroom and incremental thresholds;
6. 150/50 headroom minimum frame;
7. `40` pilot fixtures and `38` valid-settled floor;
8. 72-hour identity window;
9. 20 total/5 per-stratum discordance floors;
10. `N=400` confirmatory cap;
11. utility-power assumptions and calibration method;
12. technical-verification versus organizational-independence label.

## 6. Required next order

1. provenance-recorded review of these drafts;
2. correction and re-verification of every blocking finding;
3. explicit draft acceptance;
4. separately authorized commit and push;
5. separately authorized implementation planning;
6. implementation only after its own approval.

No provider budget, pilot authorization, private-data export approval, or LIVE
authorization may be inferred from draft acceptance.
