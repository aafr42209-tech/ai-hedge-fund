# R02 overlay v2 provider-free preregistration-design handoff

Date: `2026-07-19` (Asia/Seoul)

Status: **HANDOFF ONLY — V2 PREREGISTRATION NOT STARTED — PROVIDER/LIVE NO-GO**

## 1. Purpose

This handoff defines the next provider-free design unit after the accepted R02 D4
closeout. It authorizes drafting an overlay v2 preregistration and its review
materials. It does not authorize schema implementation, fixture generation,
pilot execution, provider calls, Codex execution, LIVE execution, retry,
replacement, resume, commit, or push.

The next design must answer a narrower and identifiable question:

> Given exactly the same decision-time public-information payload, does an LLM
> selector add utility over the strongest preregistered deterministic
> public-information comparator, after accounting for cost, latency, and failure
> risk?

Overlay v2 is a new intervention. It is not a continuation of the frozen D2b
selector and must not be described as a direct replication of D3 or D4.

## 2. Authoritative repository state

- repository: `C:\Users\User\Desktop\ai-hedge-fund-fresh`
- branch: `codex/llm-overlay-research-01`
- accepted base commit: `1b810bdbe44a6c1b972207247bc012c3fcbfd3ba`
- upstream observed before the handoff commit:
  `1b810bdbe44a6c1b972207247bc012c3fcbfd3ba`
- worktree at handoff start: clean

Pinned evidence and implementation files:

- `docs/r02-d3-preregistration.json`:
  `5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4`
- `docs/r02-d4-live-posthoc.json`:
  `623b8888a90af34bf7f0be20cf45ff19691e8c1545de76d00534102643b71042`
- `docs/r02-d4-live-posthoc-independent-review.json`:
  `efc668d817f2b344568ad549550d2dadaa8aa918c6180d5cb6ca753eabd80496`
- `docs/r02-d4-replication-design-handoff.md`:
  `419631ded0c5edaf82469c670ac1d439aca84354d4f530ce4e928cb59ec9b4b9`
- `v2/research/overlay/scoring.py`:
  `c86b7ee61a0cc7a92557adda6826ab9f75e411f3bda9ec0219c5c1d6c96d8aff`
- `v2/research/overlay/r02_contracts.py`:
  `64a099560432152da875843d6cddb4d08acd3a402198adb14a5aec65ef0dab05`
- `v2/research/overlay/r02_selector.py`:
  `a90cc600ffc772c5fb4b1c964b5efc0a551de84a41eaa5c0a030b6d02b9b20f9`

Any mismatch is a stop condition. The next unit must report drift rather than
silently rebasing these conclusions.

## 3. Required D3/D4 interpretation

The v2 preregistration must record all three statements together:

1. D3 and D4 are not evidence that LLMs in general cannot add portfolio value.
2. The implemented D2b selector could not identify utility-aware LLM value
   because it did not expose utility-relevant public state to the model.
3. The implemented selector itself is operationally redundant: deterministic
   parsimony reproduced its selections `55/55` in D3 and `69/69` in the
   preregistered D4 comparison, so provider-free replacement of that specific
   implementation is supported.

D4 remains closed with these accepted labels:

- primary replication: `REPLICATION_SUPPORTED_FRAGILE`;
- deterministic parsimony: `PARSIMONY_POLICY_SUPPORTED`;
- incremental LLM: `NOT_IDENTIFIED_REDUNDANT_SELECTOR`;
- D4 LLM/parsimony agreement: `69/69`.

The fragile replication result and the redundant-selector result are separate.
Removing the LLM does not make the baseline-relative effect robust.

## 4. Completed provider-free identifiability audit

The audit result is **negative for the current D2b pipeline**.

### 4.1 Selector-visible information

The frozen selector-safe payload contains two to four opaque presented
candidates. Each candidate exposes only:

- `presented_id`;
- six asset decisions keyed `A0` through `A5`;
- per-asset `action` in `buy`, `sell`, or `hold`;
- per-asset nonnegative integer `quantity`.

It exposes no prices, positions, concentration measures, covariance or
correlation structure, regime signal, transaction-cost context, fixture context,
or expected returns.

The frozen system prompt says:

> You are a constrained portfolio candidate selector. Compare only the opaque
> presented candidates supplied by the user. Return one strict JSON object.

The frozen reason vocabulary is limited to:

- `FEWER_NON_HOLD_ACTIONS`;
- `LOWER_TOTAL_QUANTITY`;
- `ZERO_ACTIVITY_PREFERENCE`;
- `ACTION_DIRECTION_PREFERENCE`;
- `TIE_BREAK_PREFERENCE`.

`ACTION_DIRECTION_PREFERENCE` does not create utility information. Without
public state, it can express only an intrinsic direction preference.

### 4.2 Hidden-oracle boundary

`v2/research/overlay/scoring.py::score_episode` passes
`episode.hidden.expected_returns_bps` into the evaluator. Hidden expected returns
are therefore an evaluation-only oracle input, not decision-time information.

The v2 contract must state explicitly:

- the oracle may score policies only after selection;
- hidden expected returns must never enter either policy payload;
- oracle output must never be a deployment comparator input;
- any oracle-derived design analysis must use a design-only split that is never
  reused for confirmatory evaluation.

### 4.3 Audit disposition

No current-pipeline probe LIVE run is scientifically authorized. Making the
fixtures harder while preserving the same payload and prompt cannot establish a
utility-aware incremental LLM effect. Provider calls remain zero until a distinct
v2 intervention is preregistered and passes all provider-free gates below.

## 5. Overlay v2 intervention boundary

The v2 draft must version and freeze, as one hash-linked intervention:

- selector input schema v2;
- exact public-field source mapping;
- canonical serialization;
- privacy and export classification for every field;
- system and user prompt templates;
- structured output schema v2;
- reason-code vocabulary;
- referenced-field validation rules;
- deterministic comparator family and selection rule;
- candidate generation and ordering contracts;
- parser, acceptance gate, fallback, and audit contracts;
- statistical estimands, power assumptions, and go/no-go rules.

Changing any item after a pilot begins creates a new intervention version. It may
not be treated as an amendment to the same confirmatory experiment.

## 6. Information parity and payload v2

The selected deterministic public-information scorer and LLM v2 must receive
byte-identical canonical payloads. The contract must pin one payload digest per
fixture and require both policies to bind to that digest.

The draft must inventory public state before choosing fields. Candidate fields
may include public, decision-time measures of position asymmetry, concentration,
cross-asset dependence, regime, cost, or risk, but only when each field has:

- an authoritative source in the public episode contract;
- deterministic derivation code;
- fixed units, rounding, range, and missing-value behavior;
- a no-hidden-information proof;
- a privacy/export classification;
- canonical byte representation.

No field may be included merely because it predicts the hidden oracle on a
design split. The generation rule, not individual evaluation fixtures, must be
frozen before confirmatory seed resolution.

## 7. Required policy hierarchy

The preregistration must compare three policy tiers:

1. frozen deterministic parsimony;
2. the selected deterministic public-information scorer;
3. LLM overlay v2.

The primary scientific comparator for LLM v2 is tier 2, not parsimony. The
parsimony contrast remains a secondary continuity endpoint.

The deterministic scorer may use only payload v2. It may not read hidden
expected returns, oracle scores, fixture IDs, split labels, seeds, or any field
withheld from the LLM.

## 8. Deterministic scorer selection without overfitting

The scorer family, hyperparameter grid, tie-breaking, complexity preference, and
selection metric must be frozen before inspecting scorer-selection outcomes.

At least two provider-free splits are required:

- **comparator-selection split:** choose one deterministic scorer from the frozen
  family;
- **headroom-validation split:** estimate oracle minus the already selected
  scorer without further tuning.

The same fixtures may not serve both purposes. If nested selection is proposed
instead, all folds, aggregation, and final refit rules must be frozen before
outcomes are inspected.

The selected scorer becomes immutable before any LLM pilot call.

## 9. Provider-free headroom gate

The decisive pre-provider gate is:

> hidden oracle utility minus the selected deterministic public-information
> scorer utility on an untouched headroom-validation split.

The preregistration draft must prospectively define:

- the minimum economically meaningful headroom;
- uncertainty interval construction;
- minimum fixture and stratum counts;
- concentration and leave-one-out diagnostics;
- treatment of invalid or tied oracle candidates;
- a strict pass/fail label.

If the gate does not show adequate positive headroom, overlay v2 stops with zero
provider calls. Oracle minus parsimony is descriptive and cannot substitute for
this gate.

Passing this gate establishes only that public-information policy improvement is
possible. It does not establish that an LLM can realize that improvement.

## 10. Split and seed firewall

The draft must define independent, nonreusable seeds and artifact roots for:

1. schema and generator development fixtures;
2. deterministic comparator selection;
3. provider-free headroom validation;
4. blinded LLM discordance pilot;
5. confirmatory LIVE evaluation.

Pilot fixtures are permanently excluded from confirmatory evaluation. No fixture,
derived outcome, candidate order, provider response, or hidden oracle result may
cross those boundaries except through a preregistered aggregate used by an
explicit decision rule.

Seed commitment, independent reveal, resolution, and review must occur before
materializing the corresponding confirmatory frame.

## 11. Blinded discordance pilot contract

A micro-pilot may be proposed for v2 even though D4 froze `NO_MICRO_PILOT`.
Because v2 is a new intervention, that change must be explicit and prospective.

Before any pilot call, freeze:

- payload, schema, prompts, reason codes, comparator, parser, and fallback;
- pilot fixture count and provider/token budget;
- timeout, settled-failure cap, and no-retry/no-replacement/no-resume policy;
- expected discordance-rate range;
- total and per-stratum discordance floors;
- sample-size adaptation rule;
- go/no-go rule;
- maximum pilot-to-confirmatory time interval;
- observable model-identity and executable pins.

Pilot disclosure must be blinded to utility. Before the confirmatory sample size
and go/no-go decision are frozen, the coordinator may receive only the aggregates
explicitly required by the adaptation rule, such as valid-call count and
LLM-versus-comparator discordance count by stratum.

After observing pilot aggregates, the only permitted changes are:

- confirmatory sample size as determined mechanically by the frozen rule;
- go or no-go.

Payload, schema, prompts, reason vocabulary, comparator, parser, fixture generator,
estimands, and thresholds may not change. Any such change starts a new version
and a new pilot.

## 12. Model identity and drift

Pilot and confirmatory execution must pin the same observable identity:

- requested model ID;
- executable path and SHA-256;
- CLI/package version and relevant feature flags;
- command template and output-schema digest;
- provider/model/version metadata when exposed;
- sampling and reasoning parameters;
- system and user prompt digests.

Matching requested model ID and executable hash cannot prove that provider-side
weights or routing are unchanged. The preregistration must record this limitation,
pin every observable metadata field, and make any observable mismatch a hard
stop. Absence of provider version metadata must be recorded as an explicit
validity limitation, not silently interpreted as identity.

## 13. Structured output and mechanical grounding

Free-form portfolio edits and unrestricted rationales remain forbidden. The v2
response should contain only a selected presented ID, confidence, structured
reason codes, and machine-checkable references to payload fields.

Candidate reason domains may include:

- `RISK_CONCENTRATION`;
- `POSITION_ASYMMETRY`;
- `REGIME_SENSITIVITY`;
- `CROSS_ASSET_INTERACTION`;
- `COST_TRADEOFF`.

These names are design candidates, not frozen enum values. The draft must define
their semantics and allowed field-reference types.

The parser must fail closed when:

- an unknown or duplicate key is present;
- the selected ID is not presented;
- a reason code is unknown or duplicated;
- a referenced field is absent from the exact payload;
- a field reference has the wrong type or candidate scope;
- confidence is missing, nonintegral, or outside `0..100`;
- schema, payload, prompt, model, or executable pins drift;
- transport is unsettled, timed out, nonzero-exit, or unparsable.

Invalid field references are a preregistered hallucination/grounding failure
endpoint, even when the selection would otherwise be syntactically valid.

## 14. Statistical endpoints

The v2 preregistration must define, before pilot execution:

### 14.1 Primary confirmatory endpoint

Full-frame ITT utility contrast:

`LLM_V2_UTILITY - SELECTED_DETERMINISTIC_PUBLIC_INFO_SCORER_UTILITY`

Agreement contributes zero. Invalid response, transport failure, parser failure,
acceptance failure, and any frozen fail-closed path must receive the prospectively
defined ITT value rather than being dropped.

### 14.2 Required secondary endpoints

- LLM v2 minus parsimony full-frame ITT;
- deterministic public-information scorer minus parsimony;
- LLM/comparator agreement and discordance counts;
- total and per-stratum discordance rates with intervals;
- oracle regret for all three policy tiers, evaluation-only;
- provider failure and fallback rates;
- token, latency, and monetary/operational cost summaries;
- structured-reference validity rate;
- confidence calibration against selection of the hidden oracle-optimal candidate.

Discordant-only utility summaries are descriptive. They cannot replace the
full-frame ITT endpoint because discordance is policy-selected.

The calibration target, binning or proper scoring rule, minimum sample size, and
handling of oracle ties must be frozen. Hidden oracle information may be used to
score calibration only after selection and may never enter either policy input.

## 15. Prospective power and information gate

The design must show that the discordance floor is reachable before confirmatory
LIVE authorization. It must freeze:

- expected discordance rate and uncertainty source;
- minimum total discordance;
- minimum discordance per target stratum;
- confirmatory sample-size rule;
- maximum sample and provider budget;
- low-information label;
- no-go rule when the conservative discordance estimate cannot support the floor.

Pilot sample-size adaptation must use a conservative interval bound, not a point
estimate. The design must also power the primary incremental-utility endpoint;
powering discordance alone is insufficient.

## 16. Escalation policy is deferred

The intended deployment architecture is potentially:

```text
ordinary case -> deterministic public-information scorer
frozen trigger ON -> LLM escalation
otherwise -> zero provider calls
```

No escalation trigger is authorized in the initial v2 preregistration. Trigger
design begins only if confirmatory v2 establishes reproducible discordance and a
positive incremental-utility lower bound over tier 2.

A later trigger study must preregister trigger prevalence, precision, recall,
trigger-ON stratum effects, false-negative cost, and population reweighting. The
current evidence does not identify escalation value.

## 17. Ordered provider-free work plan

The next session should perform only these steps:

1. verify the base commit, upstream, clean worktree, and pinned source digests;
2. write the D3/D4 scope-limitation research-log annotation;
3. inventory eligible public episode fields and hidden-field exclusions;
4. draft payload v2 and structured response schemas;
5. draft information-parity and byte-binding contracts;
6. define the deterministic scorer family and split firewall;
7. draft the provider-free headroom gate and prospective power method;
8. draft the blinded pilot, model-identity, and post-pilot immutability contracts;
9. draft confirmatory estimands, failure accounting, and decision labels;
10. write a zero-call manifest and independent-review handoff.

Do not implement the schemas or scorers during that session unless separately
authorized. Do not generate design, pilot, or confirmatory fixtures. Do not query
model availability or provider metadata.

## 18. Expected next-session deliverables

Recommended draft artifacts:

- `docs/r02-overlay-v2-d3-d4-scope-annotation.md`;
- `docs/r02-overlay-v2-preregistration-draft.md`;
- `docs/r02-overlay-v2-preregistration-draft.json`;
- `docs/r02-overlay-v2-payload-schema-draft.json`;
- `docs/r02-overlay-v2-response-schema-draft.json`;
- `docs/r02-overlay-v2-deterministic-comparator-design.md`;
- `docs/r02-overlay-v2-headroom-and-power-design.json`;
- `docs/r02-overlay-v2-zero-call-manifest.json`;
- `docs/r02-overlay-v2-preregistration-review-handoff.md`.

Names may change only to match an established repository phase identifier chosen
before drafting. JSON artifacts must be canonical and cross-pinned. Draft status
must remain provider/LIVE no-go.

The review record must identify reviewer provenance to the extent available:
reviewer role or identifier, review environment, review date, reviewed commit and
digests, relationship to the drafting session, and whether organizational
independence is actually established. A same-session or unidentified technical
reproduction may be recorded as verification, but it must not be labeled an
organizationally independent review without supporting provenance.

## 19. Hard boundaries

Until separate approvals are given, all of the following remain forbidden:

- external provider calls;
- Codex/provider process execution;
- pilot or confirmatory LIVE execution;
- schema or comparator implementation;
- fixture or production-root materialization;
- hidden expected returns in any policy payload;
- reuse of D3/D4 outcomes to choose v2 evaluation fixtures;
- retry, replacement, or resume;
- secret or credential inspection;
- commit or push.

No approval may be inferred from this handoff. Headroom validation, pilot freeze,
pilot execution, confirmatory freeze, and confirmatory LIVE execution require
separate ordered approvals.

## 20. Initial verification commands

```powershell
git status --short --branch
git rev-parse HEAD
git rev-parse '@{upstream}'
git merge-base --is-ancestor `
  1b810bdbe44a6c1b972207247bc012c3fcbfd3ba HEAD
git diff --name-only `
  1b810bdbe44a6c1b972207247bc012c3fcbfd3ba..HEAD
git diff --check

.venv\Scripts\python.exe scripts\r02_d4_posthoc.py
.venv\Scripts\python.exe scripts\r02_d4_posthoc_verify.py
.venv\Scripts\python.exe -m pytest -q `
  v2\research\overlay\test_r02_d4_posthoc_analysis.py
```

Expected state:

- HEAD and upstream are equal to each other;
- accepted base commit `1b810bdbe44a6c1b972207247bc012c3fcbfd3ba`
  is an ancestor of HEAD;
- the committed diff from the accepted base contains exactly
  `docs/r02-overlay-v2-preregistration-design-handoff.md`;
- worktree is clean before drafting;
- accepted D4 report reproduces byte-for-byte;
- independent verifier passes;
- focused tests pass;
- provider calls, LIVE runs, retries, replacements, and resumes remain zero.

## 21. Success criteria for the next session

The preregistration-design session is complete only when:

- the D3/D4 interpretation is recorded without generalizing to LLM capability;
- hidden-oracle dependence and evaluation-only use are explicit;
- LLM and deterministic scorer input bytes are contractually identical;
- comparator selection and headroom validation use separate frozen splits;
- the headroom gate can stop the program before any provider call;
- pilot utility blinding and post-pilot immutability are explicit;
- observable model identity and provider-side identity limitations are explicit;
- full-frame ITT, discordance power, grounding failures, and calibration are
  prospectively defined;
- all artifacts remain drafts pending independent review;
- no implementation, fixture generation, provider call, LIVE evidence, commit,
  or push occurred.

## 22. Copy-verbatim next-session prompt

> R02 overlay v2 provider-free preregistration design drafting is approved. Use
> `docs/r02-overlay-v2-preregistration-design-handoff.md` as the controlling
> handoff. Record the bounded D3/D4 interpretation, inventory public versus hidden
> information, and draft the payload v2, structured response, information-parity,
> deterministic comparator, split firewall, provider-free headroom gate,
> prospective power, blinded micro-pilot, model-identity, parser hard-stop,
> full-frame ITT, calibration, and decision-label contracts. Produce canonical
> draft artifacts, a zero-call manifest, and an independent-review handoff.
> Provider calls, Codex/provider execution, schema or comparator implementation,
> fixture materialization, pilot/LIVE execution, retry/replacement/resume, commit,
> and push are not approved.
