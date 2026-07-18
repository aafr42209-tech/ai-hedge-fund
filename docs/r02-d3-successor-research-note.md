# R02 D3 sealed-run research note

Date: 2026-07-18

Status: **PROVIDER-FREE EXPLORATORY COMPLETE — INDEPENDENTLY REVIEWED**

## Abstract

R02 D3 tested a fail-closed LLM candidate-selection overlay against a sealed
deterministic baseline. The first authorized LIVE run stopped on its first
attempt because the provider rejected a nonconforming strict output schema. The
run was sealed without retry. Provider-free successor work corrected the schema,
moved provider-call accounting to launch time, expanded replay reconciliation,
and froze a new execution identity. One newly authorized successor run then
completed all 55 eligible episodes with no fallback, failure, retry, replacement,
or unsettled attempt.

The preregistered system-level result was `SUPPORTED`: theta was 92,928,891 e12
and the frozen 95% bootstrap interval was
`[51,470,259, 138,094,263]` e12, above `delta_min=50,000,000` by a lower-bound
margin of 1,470,259 e12. The operational and confirmatory claims are fully
replayable from sealed evidence.

Post-hoc mechanism analysis materially narrows the interpretation. Every one of
the 55 candidate sets contained a unique zero-activity `NO_CHANGE` candidate,
and the LLM selected it 55/55 times. A provider-free rule minimizing non-HOLD
actions and then total absolute quantity reproduces all 55 selections, executed
candidates, and paired deltas. The run therefore supports this sealed system
against its baseline, but does not identify an incremental LLM selection effect
over the deterministic zero-activity rule.

## 1. Evidence and analysis boundary

Confirmatory closeout:

- successor evidence: `docs/r02-d3-successor-live-evidence.json`
- successor result: `docs/r02-d3-successor-live-result.md`
- closeout commit: `b274634`
- run: `r02-d3-successor-84750652-20260718`
- terminal: `COMPLETE`, anchor 774
- accounting: reserved/launched/settled/unsettled = `55/55/55/0`
- provider calls: 55
- fallback and settlement failures: 0
- debit: 655,122 tokens

Provider-free post-hoc package:

- analysis source: `v2/research/overlay/r02_d3_posthoc_analysis.py`
- source SHA-256: `45a54d6b260330031093756209c7950e400b57178bc93eadbd6efeaef36ed7b9`
- structured report: `docs/r02-d3-successor-provider-free-posthoc.json`
- report SHA-256: `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
- provider calls: 0
- LIVE executions: 0

All analyses below are secondary or exploratory unless explicitly identified as
the unchanged frozen confirmatory calculation. They cannot revise the sealed
`SUPPORTED` label.

Independent review reproduced the pre-status-transition report byte-for-byte,
recomputed the zero-activity rule 55/55 without using this module, and matched
the reported sensitivity values including the `development-0189` diagnostic.
The reviewed pre-status source and report hashes were respectively
`4b6faa50080aa9770326a2a078bb360a1067e3b053325f22e462ec7f3aca819a` and
`773474dfcf2cccabb544998d39f4034d8a8354d8134c5bbe4ef21938d15bdb03`.
The current hashes include only the independently reviewed status record and
the generator's fail-closed refresh option; all analytical values are unchanged.

## 2. Two-run fail-closed method result

The predecessor run demonstrated the failure path. Its first provider
submission returned HTTP 400 because the strict schema's `required` array did
not contain `schema_version`. The audit preserved the raw transport evidence,
the run hard-stopped, and the no-retry contract prevented outcome-driven repair
inside the authorized run. Review also found that provider-call accounting was
incremented too late, after response parsing, which caused the predecessor
terminal ledger to undercount the actual submission.

The successor was prepared without provider calls. Its output schema required
every property, the strict-schema invariant was validated before launch, and
external calls were accounted at `attempt_started`. A new source-pinned
readiness freeze, external authorization artifact, clean detached worktree, and
launch-time executable hash bound the second run. The successor then completed
55/55 and strict replay reconciled every launch, settlement, outcome, ledger,
and terminal record.

This pair of runs supports a methodological claim independent of investment
performance: the same architecture preserved auditable evidence under both a
provider-side rejection and a complete execution, while preventing retries or
silent relabeling.

## 3. Frozen confirmatory result

The accepted primary estimand was
`round_half_even(3/4*mean(D_REPRESENTATIVE) + 1/4*mean(D_CHALLENGE))` over the
full 160-fixture frame. The 55 eligible fixtures contributed observed paired
deltas and 105 trigger-false fixtures contributed the preregistered zero.

| Quantity | Frozen result |
| --- | ---: |
| Full frame | 160 |
| Eligible paired fixtures, M | 55 |
| Minimum M | 46 |
| Positive / negative eligible deltas | 43 / 12 |
| theta e12 | 92,928,891 |
| Bootstrap lower e12 | 51,470,259 |
| Bootstrap upper e12 | 138,094,263 |
| delta_min e12 | 50,000,000 |
| delta_target e12 | 100,000,000 |
| Frozen verdict | **SUPPORTED** |

The lower bound exceeds `delta_min`, but only by 1,470,259 e12, approximately
2.94% of the threshold. The point estimate is also below `delta_target`. The
correct confirmatory interpretation is therefore positive but narrow.

## 4. What the selector selected

Candidate-set sizes were 2 candidates in 15 episodes, 3 in 13, and 4 in 27.
The 55 baseline canonical IDs were all distinct, while the selected canonical
ID was always:

`11eb14e46d7e2bd45610d4e4c92945332a947dae5f2be307d8ccfd3458e3ec11`

That candidate contains six `hold, quantity=0` decisions and has primary role
`NO_CHANGE`. It was the unique zero-activity candidate in every candidate set.

| Selection diagnostic | Matches |
| --- | ---: |
| LLM selected `NO_CHANGE` | 55/55 |
| Selected minimum non-HOLD action count | 55/55 |
| Selected minimum total absolute quantity | 55/55 |
| Selected unique zero-activity candidate | 55/55 |
| Provider-free parsimony rule reproduced selection | 55/55 |

Every provider response reported confidence 100. Reason codes were
`FEWER_NON_HOLD_ACTIONS` 55 times, `ZERO_ACTIVITY_PREFERENCE` 55 times, and
`LOWER_TOTAL_QUANTITY` 53 times. Conditional presentation-position counts do
not show a simple fixed-position preference: for size 2 they were 8/7, for size
3 they were 2/6/5, and for size 4 they were 8/3/8/8.

### Mechanism conclusion

The LLM behaved as a perfectly consistent parsimony selector, but the relevant
rule was mechanically recoverable from the candidate bytes. A deterministic
policy choosing the unique all-HOLD candidate would have executed the same
candidate and produced the same paired utility delta in all 55 episodes with
zero provider calls.

Thus:

- **identified:** the executed no-change policy outperformed the sealed
  deterministic baseline under the frozen system-level test;
- **not identified:** an incremental benefit from using an LLM instead of the
  provider-free zero-activity rule.

This is not a defect in the sealed verdict; it is a limitation on its mechanism
and generalization.

## 5. Delta distribution

The 55 eligible deltas are neither normal nor uniform. They are centrally
concentrated, right-skewed, and heavy-tailed.

| Diagnostic | All 55 | Representative 15 | Challenge 40 |
| --- | ---: | ---: | ---: |
| Mean e12 | 270,338,593 | 200,771,058 | 296,426,419 |
| Median e12 | 193,055,374 | 94,322,799 | 208,089,609 |
| Sample SD e12 | 468,881,122 | 623,364,866 | 402,934,211 |
| Bias-corrected skew | 0.811 | 0.485 | 1.471 |
| Excess kurtosis | 1.985 | 0.752 | 3.196 |
| Shapiro-Wilk p | 0.0045 | 0.7382 | 0.0011 |

The challenge stratum drives most of the non-normality. The frozen primary
analysis used a stratified nonparametric bootstrap and therefore did not assume
normal deltas. The distribution diagnostics remain descriptive because the
frame was stratified and the 55 cases were not an IID convenience sample.

## 6. Exploratory robustness

### 6.1 Single-fixture influence

Two diagnostics were computed with the same 10,000-resample seed:

1. Fixed-frame zero nullification replaced one eligible observed delta with the
   preregistered zero contribution while retaining all 160 fixtures.
2. Literal leave-one-out deleted one eligible fixture from its stratum. This
   changes the frozen design and is diagnostic only.

| Diagnostic | Still above delta_min | Below delta_min |
| --- | ---: | ---: |
| Single-fixture zero nullification | 30/55 | 25/55 |
| Literal leave-one-out | 40/55 | 15/55 |

The most influential positive case was `development-0189`, challenge stratum,
with delta 1,722,160,500 e12. Nullifying it reduced theta to 82,165,388 e12 and
the bootstrap interval to `[44,138,109, 121,518,868]`, which no longer satisfied
the frozen threshold. This does not change the confirmatory verdict; it shows
that the narrow lower-bound margin is not leave-one-observation robust.

### 6.2 Upper-tail and winsorization diagnostics

Nullifying only the largest positive delta already moved the lower bound below
`delta_min`. Nullifying the top five reduced theta to 52,354,883 e12 and the
lower bound to 23,614,206 e12.

Within-stratum winsorization produced:

| Two-sided fraction | theta e12 | Bootstrap interval e12 | Threshold diagnostic |
| --- | ---: | ---: | --- |
| 1% | 91,772,604 | [56,211,562, 130,360,807] | above |
| 5% | 77,850,721 | [52,658,992, 104,421,662] | above |
| 10% | 66,923,725 | [45,368,419, 88,632,443] | below |

The result tolerates modest 5% clipping but not 10% clipping. This is consistent
with a real central positive tendency plus material support from the right tail.

### 6.3 Frozen prospective low-SNR scenario

The accepted provider-free power freeze estimated 85.7% power for the selected
`n160-design-worst` scenario, with Wilson lower bound 83.3935%. Its prespecified
8,000-bps low-SNR sensitivity estimated 79.0% power, with Wilson interval
`[76.3669%, 81.4111%]`. This is prospective design evidence, not an observed-
outcome reclassification.

## 7. Conclusions

Three conclusions can coexist without contradiction:

1. **Operational success:** the successor runner and fail-closed evidence chain
   worked end to end.
2. **Confirmatory research success:** the sealed system-level hypothesis is
   `SUPPORTED` under its preregistered rule.
3. **Mechanism and robustness limitation:** the LLM exactly reproduced a simple
   no-change rule, and the positive lower-bound margin is sensitive to a subset
   of large positive fixtures.

The next scientifically valuable experiment is not an immediate rerun. It is a
new-seed preregistered replication that adds an explicit deterministic
zero-activity comparator or ablation. That design can separate:

- baseline versus no-change policy effect;
- no-change rule versus LLM selector effect;
- frame-specific success versus replication-stable success.

A replication requires a new frame, preregistration, freeze, independent review,
and explicit LIVE authorization. None is granted by this note.

## 8. Reproduction and review handoff

Provider-free generation:

```powershell
.venv\Scripts\python.exe scripts\r02_d3_successor_posthoc.py `
  --repo-root C:\Users\User\Desktop\ai-hedge-fund-fresh `
  --output C:\Users\User\Desktop\ai-hedge-fund-fresh\docs\r02-d3-successor-provider-free-posthoc.json `
  --verify-existing
```

Focused tests:

```powershell
.venv\Scripts\python.exe -m pytest -q `
  v2/research/overlay/test_r02_d3_posthoc_analysis.py
```

Independent review completed all requested checks with no blocking finding. The
current artifact can be reverified with the commands above; the confirmatory
`SUPPORTED` verdict remains explicitly unchanged.
