# R02 D4 provider-free replication-design handoff

Date: 2026-07-18

Status: **HANDOFF ONLY — DESIGN NOT STARTED — LIVE NO-GO**

## 1. Purpose

The next research task is a provider-free design phase for a new-seed exact
replication of R02 D3. The working label is **R02 D4**. This handoff does not
authorize frame generation, provider calls, LIVE execution, retry, replacement,
or creation of a LIVE authorization artifact.

The replication must answer two distinct questions without conflating them:

1. Does the sealed R02 system-versus-baseline effect reproduce on a new,
   outcome-independent frame?
2. Does the LLM do anything different from the deterministic zero-activity
   parsimony selector on that new frame?

Changing the candidate generator to force ambiguous choices would no longer be
an exact replication. Such a mechanism-identification experiment must remain a
separate future study, provisionally outside R02 D4.

## 2. Authoritative repository state

- repository: `C:\Users\User\Desktop\ai-hedge-fund-fresh`
- branch: `codex/llm-overlay-research-01`
- handoff base commit: `ee6c7bb4d778b63b69373d0cfb00489d4fc19686`
- upstream at handoff preparation: `fork/codex/llm-overlay-research-01`, sync `0/0`
- R02 D3 successor implementation: `e5643a34bed91e7d9618ab434f9b695e127c4bfe`
- R02 D3 prelaunch package: `9d1b9525f85caf88b41beabf49e97928b2ec1ef6`
- R02 D3 independently reviewed closeout: `b27463460ade056c8e346a831ed734e1b44f3508`
- R02 D3 independently reviewed post-hoc package: `ee6c7bb4d778b63b69373d0cfb00489d4fc19686`

The handoff document itself is expected to be committed after the base commit;
the next session must inspect `HEAD` rather than assume the base commit remains
the branch tip.

## 3. Sealed R02 D3 result

Execution identity:

- run ID: `r02-d3-successor-84750652-20260718`
- readiness freeze: `847506528aa68b32bc1a7ec5ef0261d369ee638addc7c1590a3180369751bd54`
- authorization: `0053aa6191e7cc860c9a3968644e0c9968939f41cf7f730a1172f21635ac0f19`
- audit tree: `bca066c859ded362cc6f531c236a224cacce6f2a4f0f62a06f15f8cc0d950bc4`
- durable archive tree: `b3cc74da593975865cd42087bb18bdc3f82d1c5666df5d98c5eb8ff92119dbea`
- terminal: `COMPLETE`, anchor 774
- reserved/launched/settled/unsettled: `55/55/55/0`
- external provider calls: 55
- fallback and settlement failures: 0
- debit: 655,122 tokens

Frozen confirmatory result:

- full frame: 160 fixtures, target strata 120 representative / 40 challenge
- eligible paired fixtures: 55, with `M_min=46`
- positive / negative eligible deltas: 43 / 12
- theta: `92,928,891` e12
- frozen 95% bootstrap interval: `[51,470,259, 138,094,263]` e12
- `delta_min`: `50,000,000` e12
- `delta_target`: `100,000,000` e12
- lower-bound margin over `delta_min`: `1,470,259` e12
- verdict: `SUPPORTED`

This verdict is immutable. R02 D4 may replicate or fail to replicate it, but may
not relabel R02 D3.

## 4. Mechanism finding that changes the next design

The independently reviewed provider-free post-hoc analysis found:

- all 55 candidate sets had one unique zero-activity `NO_CHANGE` candidate;
- the LLM selected that candidate 55/55;
- a provider-free rule minimizing non-HOLD actions, then total absolute
  quantity, then canonical ID reproduced 55/55 selections;
- therefore the same rule reproduced 55/55 executions and paired deltas;
- LLM-specific incremental selection value versus that rule was not identified.

Robustness findings:

- single-fixture zero nullification retained the frozen threshold in 30/55
  cases and lost it in 25/55;
- literal leave-one-out retained it in 40/55 and lost it in 15/55;
- zeroing `development-0189` changed theta to `82,165,388` e12 and the interval
  to `[44,138,109, 121,518,868]` e12;
- 5% within-stratum winsorization retained the threshold;
- 10% winsorization did not;
- the combined delta distribution was right-skewed and heavy-tailed;
- the frozen n=160 low-SNR prospective scenario estimated 79.0% power with a
  76.3669% Wilson lower bound.

Current post-hoc pins:

- source: `v2/research/overlay/r02_d3_posthoc_analysis.py`
- source SHA-256: `45a54d6b260330031093756209c7950e400b57178bc93eadbd6efeaef36ed7b9`
- report: `docs/r02-d3-successor-provider-free-posthoc.json`
- report SHA-256: `1ab968ec5b4af153d12f87ed00c431155982c34ad8b938de629cda3e9d4edb73`
- research note: `docs/r02-d3-successor-research-note.md`

## 5. Recommended R02 D4 scientific scope

### 5.1 Exact replication arm

Preserve the accepted R02 intervention as closely as possible:

- same baseline definition;
- same trigger semantics;
- same candidate generator and candidate roles;
- same opaque presentation/permutation principle;
- same strict selector response contract unless a provider-free compatibility
  change is independently justified and frozen;
- same system-level ITT zero-contribution rule;
- same primary estimand and `delta_min` unless a design review explicitly
  rejects exact replication and renames the study;
- new outcome-independent seed and new immutable frame;
- no fixture selection using R02 D3 fixture IDs, deltas, or utility outcomes.

The deterministic parsimony selector must be evaluated locally on the same
candidate sets. It is a comparator and mechanism diagnostic, not a replacement
for the LLM arm in the exact replication.

### 5.2 Required estimands and labels

Freeze separate estimands before any new outcome is observed:

1. **Primary replication estimand:** R02 LLM-selected system utility minus the
   deterministic baseline, using the accepted target-stratum ITT weighting.
2. **Deterministic-policy estimand:** parsimony-selected system utility minus the
   same baseline.
3. **Incremental LLM estimand:** LLM-selected utility minus parsimony-selected
   utility on the same fixtures.
4. **Agreement endpoint:** candidate-level agreement rate and discordant count
   between the LLM and parsimony selector.

The design must freeze a minimum informative-discordance rule. If the LLM and
parsimony rule agree on every case, or discordance is below the frozen minimum,
the incremental LLM label should be `NOT_IDENTIFIED_REDUNDANT_SELECTOR`, not
`SUPPORTED` and not `NO_EFFECT`.

### 5.3 Robustness label

Do not replace the accepted bootstrap primary test with a post-hoc robust
statistic. Instead, preregister a separate robustness classification, for
example:

- `REPLICATION_SUPPORTED_ROBUST`;
- `REPLICATION_SUPPORTED_FRAGILE`;
- `REPLICATION_NOT_SUPPORTED`;
- `INVALID_RUN`;
- `INCONCLUSIVE_LOW_INFORMATION`.

The provider-free design must decide in advance which diagnostics determine
`ROBUST` versus `FRAGILE`. Candidate inputs include:

- single-fixture zero-nullification stability;
- literal leave-one-out stability;
- frozen 5% and 10% within-stratum winsorization sensitivity;
- maximum fixture influence;
- minimum discordant count for the incremental LLM estimand.

These labels may qualify the new replication result but cannot revise R02 D3.

### 5.4 Prospective sizing

Run provider-free power simulations before selecting the frame size. At minimum:

- preserve the 3:1 representative/challenge target weighting;
- evaluate n=160, n=200, and larger outcome-independent candidates;
- include the accepted 8,000-bps low-SNR condition;
- include heavy-tail and high-influence conditions motivated by the sealed
  aggregate diagnostics, without reusing individual outcomes to select cases;
- require a frozen power target and Wilson lower-bound target;
- freeze provider-attempt and token caps from the selected eligible count.

The existing freeze showed n=200 low-SNR estimated power 87.4% with an 85.1990%
Wilson lower bound, while n=160 low-SNR fell below 80%. This makes n=200 or
larger the natural starting point, not a preapproved final choice.

### 5.5 Deferred mechanism-identification study

Do not modify R02 D4 candidate sets merely to make the LLM useful. A study that
removes unique zero-activity dominance, introduces tied parsimony features, or
constructs genuinely ambiguous candidates changes the intervention. Design it
later as a separately named and separately frozen experiment after exact
replication design is complete.

## 6. Provider-free design deliverables

The next session should produce drafts only, with zero provider calls:

1. `docs/r02-d4-replication-design.md`
2. `docs/r02-d4-replication-design.json`
3. a deterministic seed-contract draft with an outcome-independent preimage;
4. a prospective power/sizing report covering low-SNR and heavy-tail cases;
5. exact parsimony-selector comparator semantics and test vectors;
6. proposed primary, incremental, agreement, and robustness labels;
7. a zero-call manifest proving no frame generation, provider call, or LIVE run;
8. `docs/r02-d4-replication-design-review-handoff.md` for skeptical independent
   review.

Do not create the new frame during the design session. Frame generation begins
only after the design, seed preimage, statistical rules, and comparator are
independently reviewed and explicitly accepted.

## 7. Hard boundaries

Until a later explicit authorization, the next session must not:

- call any provider or invoke `codex exec`;
- run a micro-pilot or LIVE episode;
- create a canonical LIVE authorization artifact;
- generate or scan the new replication frame;
- select a new seed using R02 D3 outcomes;
- modify, delete, or reclassify sealed R02 D3 evidence;
- change the R02 D3 `SUPPORTED` verdict;
- merge exact replication with an ambiguity-engineered mechanism study;
- make investment, trading, or deployment claims;
- commit or push new design artifacts unless the user separately requests it.

## 8. Initial verification commands

Run these read-only checks before design work:

```powershell
Set-Location C:\Users\User\Desktop\ai-hedge-fund-fresh
git status --short --branch
git rev-parse HEAD
git rev-list --left-right --count '@{upstream}...HEAD'

.venv\Scripts\python.exe scripts\r02_d3_successor_posthoc.py `
  --repo-root C:\Users\User\Desktop\ai-hedge-fund-fresh `
  --output C:\Users\User\Desktop\ai-hedge-fund-fresh\docs\r02-d3-successor-provider-free-posthoc.json `
  --verify-existing

.venv\Scripts\python.exe -m pytest -q `
  v2/research/overlay/test_r02_d3_posthoc_analysis.py `
  v2/research/overlay/test_r02_statistics.py
```

Expected verification:

- current post-hoc report regenerates byte-for-byte;
- 9 focused tests pass;
- provider calls remain 0;
- no LIVE process or new audit root is created;
- the working tree is clean before drafting.

## 9. Required source reading

Read these before proposing a design:

- `docs/r02-d3-successor-live-evidence.json`
- `docs/r02-d3-successor-live-result.md`
- `docs/r02-d3-successor-provider-free-posthoc.json`
- `docs/r02-d3-successor-research-note.md`
- `docs/r02-d2c-statistical-freeze.json`
- `docs/r02-d3-preregistration.json`
- `v2/research/overlay/r02_statistics.py`
- `v2/research/overlay/r02_d3_posthoc_analysis.py`
- `v2/research/overlay/r02_candidates.py`
- `v2/research/overlay/r02_frame.py`

If any pin, replay, or report regeneration differs, stop with a fail-closed
diagnosis. Do not repair sealed evidence in place.

## 10. Success criteria for the next session

The provider-free design phase is complete only when:

- exact replication and future mechanism-identification scopes are separated;
- all new hypotheses, estimands, comparators, labels, and precedence are explicit;
- the parsimony comparator is deterministic and covered by test vectors;
- seed derivation is outcome-independent and reviewable before frame generation;
- power and budget choices are justified under low-SNR and heavy-tail scenarios;
- no new outcomes, frames, provider calls, or LIVE evidence exist;
- all drafts identify themselves as pending independent review;
- a skeptical reviewer can reproduce every design calculation from pinned
  provider-free sources.

## 11. Copy-verbatim next-session prompt

```text
작업 저장소: C:\Users\User\Desktop\ai-hedge-fund-fresh
브랜치: codex/llm-overlay-research-01

R02 D4 새-seed exact replication의 provider-free 설계 착수를 승인합니다.
이번 세션의 승인은 설계 문서, outcome-independent seed contract 초안,
prospective power/sizing 분석, deterministic parsimony comparator 정의와
테스트 벡터, zero-call manifest, 독립 검토 handoff 작성까지만 포함합니다.

새 frame 생성·scan, provider 호출, codex exec, micro-pilot, LIVE 실행,
LIVE authorization artifact 생성, retry/replacement은 승인하지 않습니다.
R02 D3의 봉인 증거와 SUPPORTED verdict를 수정하거나 재분류하지 마세요.

먼저 docs/r02-d4-replication-design-handoff.md를 전부 읽고, 명시된 git
상태·post-hoc byte replay·9개 focused test를 확인하세요. drift가 있으면
fail-closed 진단만 작성하고 진행을 중단하세요.

설계에서는 다음을 반드시 분리하세요:
1) 동일 후보 생성기를 유지하는 exact replication의 system-vs-baseline,
2) deterministic zero-activity/parsimony selector-vs-baseline,
3) LLM-vs-parsimony incremental effect와 agreement/discordance,
4) 별도 미래 연구인 ambiguity-engineered mechanism study.

비정규·heavy-tail, 좁은 하한 마진, dev-0189 영향, 5%/10% winsorization,
동결 8,000-bps low-SNR 결과를 반영해 n=160, n=200 이상을 provider-free로
비교하고 power target·Wilson lower target·robust/fragile label을 사전 고정할
수 있는 설계를 제안하세요. individual R02 D3 outcome으로 새 seed나 fixture를
고르지 마세요.

완료물은 provider-free draft와 review handoff로 남기고, 실제 frame 생성이나
LIVE 승인을 요청하지 마세요. 새 파일의 커밋·푸시는 별도 사용자 승인 전까지
하지 마세요.
```
