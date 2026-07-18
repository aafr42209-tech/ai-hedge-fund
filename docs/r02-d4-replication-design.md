# R02 D4 new-seed exact-replication design

Date: 2026-07-18

Status: **PROVIDER-FREE DRAFT — PENDING INDEPENDENT REVIEW AND USER ACCEPTANCE — LIVE NO-GO**

Provider calls: **0**

Frame generation or scan: **0**

LIVE executions or authorization artifacts: **0**

## 1. Draft decision

R02 D4 should remain an exact replication of the accepted R02 D3 system. The
draft selects `n=200`, allocated 150 representative and 50 challenge fixtures,
subject to independent review. It keeps the 3:1 target weighting, the accepted
trigger and candidate generator, the full-frame ITT zero-contribution rule,
`delta_min=50,000,000 e12`, and the stratified nonparametric bootstrap.

The draft freezes two sizing targets under the 8,000-bps low-SNR condition:

- estimated power at least 85%;
- Wilson 95% lower power bound at least 80%.

`n=160` fails both new raw sizing scenarios. `n=200` passes both; `n=240`
also passes but is not the smallest passing size. The proposed information floor
is `M_min=57`, which has 94.3424% exact opportunity probability under the frozen
8% representative trigger and 5% candidate-collapse assumptions.

This is a design recommendation, not frame authorization. The frame root seed
is unresolved and no usable seed, frame ID, fixture, challenge scan, provider
budget, or LIVE authorization exists.

## 2. Verified starting state

The design started only after these fail-closed gates passed:

- branch `codex/llm-overlay-research-01` at
  `ad8857b74a2276b9eb4248801b156a8e08d88742`, upstream sync `0/0`;
- clean worktree before drafting;
- `scripts/r02_d3_successor_posthoc.py --verify-existing` returned success;
- post-hoc bytes remained SHA-256
  `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`;
- the required focused suite returned `9 passed`;
- provider calls, LIVE processes, and new audit roots remained zero.

The sealed R02 D3 verdict remains **SUPPORTED**. This draft does not edit,
recompute into a new label, or weaken that verdict.

## 3. Scientific questions and expectation management

The confirmatory value of D4 is question 1:

1. Does the accepted R02 system-versus-baseline effect reproduce on an
   outcome-independent new frame?

The other questions are prespecified mechanism diagnostics:

2. Does the deterministic zero-activity/parsimony selector outperform the same
   baseline on the same frame?
3. Does the LLM add incremental utility over parsimony, and how often do the
   selectors agree or disagree?

Because exact replication preserves the candidate generator, the D3 structure
may recur: one unique zero-activity candidate may dominate, LLM and parsimony
may agree 100%, and the incremental label may again be
`NOT_IDENTIFIED_REDUNDANT_SELECTOR`. That outcome is expected, valid, and not a
failed replication. It answers the mechanism question by showing that the exact
intervention provides insufficient discordance; it does not diminish D4's
primary system-versus-baseline replication value.

A study that removes zero-activity dominance or engineers ambiguous candidates
changes the intervention. It is a separate future mechanism study, not D4.

## 4. Exact-replication invariants

The future frame implementation must pin and independently verify:

- baseline: the same validated `primary_deterministic` baseline;
- trigger: maximum effective cost of an actual baseline trade is at least 50 bps;
- candidate roles and transforms: `BASELINE`, `NO_CHANGE`,
  `HALF_BASELINE_DELTA`, and `DROP_MAX_COST_TRADE`;
- validation, semantic deduplication, canonical IDs, and opaque permutation;
- candidate-generator source SHA-256
  `29c13547230d1729d8b9cec637ccb13335fbcae52c1360e63718359d993a320e`;
- fixture-generator source SHA-256
  `732ca6ff358590edd856ba68bcb6cefb612246da9d81b97aa08d12db786eabfe`;
- full-frame target weighting `3/4` representative plus `1/4` challenge;
- trigger-false, no-call, invalid-response, and baseline-fallback contributions
  all equal zero under the accepted ITT rule;
- no D3 fixture ID, delta, utility, rank, or influence value may enter the new
  seed preimage or new fixture admission rule.

The representative arm remains a deterministic prefix from the new root seed.
The challenge arm retains the accepted provider-free scan and admission rule:
trigger true, at least two deduplicated candidates, and positive candidate
headroom. This scan is not authorized in this design session.

## 5. Outcome-independent seed contract

The machine draft is `docs/r02-d4-seed-contract.json`. It deliberately contains
no nonce reveal, root seed, or frame ID.

The proposed contract uses two-party commit/reveal after design acceptance and
after a separate frame-generation authorization:

1. Freeze the accepted design commit and design-manifest hash.
2. The coordinator commits to a CSPRNG 32-byte nonce without revealing it.
3. An independent reviewer commits to a separate CSPRNG 32-byte nonce.
4. Both reveal exactly once; each reveal must match its prior commitment.
5. Hash canonical JSON containing the fixed design pins, counts, generator pins,
   both nonce commitments, and both verified reveals under domain
   `R02-D4-EXACT-REPLICATION-FRAME-SEED-V1`.
6. Resolve slot 0 once. No rejected seed, alternate slot, retry, replacement,
   or scan-before-acceptance is allowed. Failure creates no seed and requires a
   newly named design review, not a replacement draw.

R02 D3 evidence hashes and individual outcomes are forbidden preimage fields.
This draft does not generate the nonces; therefore it cannot be used to scan a
frame.

Evaluation and robustness bootstrap seeds use separate domains and are derived
only after a future frame is sealed, from the accepted design freeze and sealed
frame manifest. They cannot be changed after outcomes are observed.

## 6. Prospective sizing

### 6.1 Accepted frozen reference

The accepted D2c freeze remains reference evidence:

| Scenario | Estimated power | Wilson lower |
| --- | ---: | ---: |
| n=160, design-worst 10,000 bps | 85.7% | 83.3935% |
| n=160, low-SNR 8,000 bps | 79.0% | 76.3669% |
| n=200, low-SNR 8,000 bps | 87.4% | 85.1990% |

The n=160 low-SNR failure motivates a larger replication; it does not alter D3.

### 6.2 New provider-free grid

The new calculation uses 1,000 outer trials, 2,000 within-stratum bootstrap
resamples per trial, PCG64, the accepted zero-contribution mechanics, and a
fixed design-simulation seed. Two raw distributions are sizing gates:

- the accepted bounded zero-or-high 8,000-bps family;
- a centered gamma family with shape 1.85, selected from the sealed aggregate
  challenge diagnostics (skew about 1.47, excess kurtosis about 3.20), without
  replaying individual D3 deltas.

| N | Raw bounded power / lower | Raw gamma power / lower | Sizing gate |
| ---: | ---: | ---: | --- |
| 160 | 76.8% / 74.0842% | 79.9% / 77.3039% | fail |
| 200 | 87.1% / 84.8796% | 89.0% / 86.9095% | pass |
| 240 | 91.9% / 90.0443% | 94.4% / 92.7977% | pass |

Within-full-stratum 5% and 10% winsorized gamma scenarios are diagnostic, not
sizing gates. Their low pass probabilities are expected because the
representative arm is sparse and 10% clipping can remove rare positive support.
They reinforce the need for a separate observed-result robustness label; they
do not replace the accepted primary test.

The machine report is `docs/r02-d4-prospective-power-sizing.json`. The draft
selects the smallest `N >= 200` passing both raw sizing scenarios: `N=200`.

## 7. Frozen estimand draft

All deltas use the same 150/50 full-frame target weighting and round-half-even
integer arithmetic.

1. **Primary replication estimand**: LLM-selected system utility minus the
   deterministic baseline. Label family: replication labels in section 8.
2. **Deterministic-policy estimand**: parsimony-selected system utility minus the
   same baseline. This is prespecified secondary mechanism evidence, not a
   replacement for the primary LLM arm.
3. **Incremental LLM estimand**: LLM-selected utility minus
   parsimony-selected utility on each fixture, with zero contribution on
   selector agreement and on all primary ITT zero-contribution cases.
4. **Agreement endpoint**: exact candidate-ID agreement rate, discordant count,
   stratum counts, and Wilson 95% interval among selector-eligible cases.

The primary and deterministic-policy estimands retain
`delta_min=50,000,000 e12`. The primary label is evaluated first. Secondary and
incremental results cannot rescue or reverse the primary replication label.

## 8. Label and precedence draft

Run-level precedence:

1. `INVALID_RUN` for identity, integrity, settlement, provider-accounting,
   attempt/token-cap, replay, or sealed-tree failure.
2. `INCONCLUSIVE_LOW_INFORMATION` when the valid frame has `M < 57`.
3. `REPLICATION_NOT_SUPPORTED` when the valid primary bootstrap lower bound is
   not strictly greater than `delta_min`.
4. A primary pass is `REPLICATION_SUPPORTED_ROBUST` only if every condition
   below passes; otherwise it is `REPLICATION_SUPPORTED_FRAGILE`.

`ROBUST` requires:

- unmodified lower-bound margin at least `5,000,000 e12`;
- maximum absolute fixed-frame single-fixture theta shift no greater than 10%
  (`100,000 ppm`) of the absolute unmodified theta;
- every fixed-frame single-fixture zero-nullification lower bound above
  `delta_min`;
- every literal leave-one-out lower bound above `delta_min`;
- both 5% and 10% within-full-stratum winsorized lower bounds above `delta_min`.

This classification directly anticipates D3's narrow 1,470,259-e12 margin,
`development-0189` influence, 30/55 zero-nullification stability, 40/55 literal
leave-one-out stability, 5% pass, and 10% failure. It qualifies only the new D4
result and never reclassifies D3.

The deterministic-policy estimand uses separate secondary labels:
`PARSIMONY_POLICY_INCONCLUSIVE_LOW_INFORMATION` when `M < 57`,
`PARSIMONY_POLICY_SUPPORTED` when its lower bound is strictly above
`delta_min`, and `PARSIMONY_POLICY_NOT_SUPPORTED` otherwise. These labels are
never substitutes for the primary replication label.

Incremental label precedence:

- fewer than 20 total discordances, or fewer than five in either target
  stratum: `NOT_IDENTIFIED_REDUNDANT_SELECTOR`;
- otherwise, lower bound above zero: `INCREMENTAL_LLM_SUPPORTED`;
- otherwise, upper bound below zero: `INCREMENTAL_LLM_HARM`;
- otherwise: `INCREMENTAL_LLM_INCONCLUSIVE`.

`NOT_IDENTIFIED_REDUNDANT_SELECTOR` means insufficient intervention contrast,
not evidence of no effect.

## 9. Deterministic parsimony comparator

For each validated, deduplicated candidate, calculate only byte-visible fields:

```text
non_hold_action_count = count(action != "hold" OR quantity != 0)
total_absolute_quantity = sum(abs(quantity))
ranking_key = (non_hold_action_count, total_absolute_quantity, canonical_candidate_id)
selection = lexicographic minimum ranking_key
```

The comparator may not read candidate roles, aliases, presented positions,
costs, regime, fixture IDs, headroom, utility, provider output, or outcomes.
Malformed actions or quantities, empty candidate sets, invalid canonical IDs,
and duplicate canonical IDs fail closed. Canonical candidate integrity remains
the generator boundary and must be verified before comparator entry.

`v2/research/overlay/r02_d4_design.py` implements the rule. Eight machine test
vectors cover unique zero activity, each tie-break level, inconsistent
action/quantity activity, and presentation-order invariance. Four additional
pytest cases cover empty, malformed, duplicate-ID, and boolean-quantity stops.

## 10. Deferred ambiguity-engineered mechanism study

The following are forbidden inside D4 and reserved for a separately named,
separately frozen future study:

- removing the unique zero-activity candidate;
- forcing ties on activity and quantity;
- adding semantically ambiguous candidates;
- changing prompt semantics to prefer activity;
- selecting fixtures because D3 or D4 outcomes make the LLM look different.

Such a study asks whether the LLM resolves genuine candidate ambiguity. D4 asks
whether the accepted system effect replicates. The two studies must not share a
verdict or intervention identity.

## 11. Future budget formula, not authorization

After a separately authorized frame is generated and independently sealed:

- provider attempt cap = sealed selector-eligible episode count;
- per-episode attempt cap = 1;
- retry and replacement cap = 0;
- per-attempt token reserve = 32,000;
- token cap = eligible count multiplied by 32,000;
- every attempted case remains in ITT and debits the cap;
- utility outcomes remain unavailable to continuation decisions.

No numeric provider cap is finalized now because the eligible count does not
exist. This formula is not a LIVE authorization request.

## 12. Current hard boundary

Until later explicit acceptance and authorization, do not:

- resolve or reveal a frame seed;
- generate or scan a frame;
- call a provider or invoke `codex exec`;
- run a micro-pilot or LIVE episode;
- create a LIVE authorization artifact;
- retry, replace, or seed-shop;
- modify sealed R02 D3 evidence or its `SUPPORTED` verdict;
- commit or push these drafts.

## 13. Provider-free reproduction

```powershell
.venv\Scripts\python.exe -m pytest -q `
  v2/research/overlay/test_r02_d4_design.py
```

The independent reviewer should also rerun the handoff's post-hoc byte replay
and original nine focused tests before evaluating these drafts.
