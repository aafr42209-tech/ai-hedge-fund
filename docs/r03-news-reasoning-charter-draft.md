# R03 news-driven LLM reasoning — research charter draft

Status: **DRAFT; PENDING INDEPENDENT REVIEW**  
Phase: R03  
Created: 2026-07-19  
Execution authority: provider-free design only

## 1. Purpose

Test whether an LLM reasoning over point-in-time news narrative adds net
portfolio utility beyond a frozen non-LLM model that receives the same article
text. The research must distinguish raw-text access from reasoning method and
must stop before provider calls when economically meaningful success is not
feasible or statistically identifiable.

## 2. Prior evidence and claim boundary

- R02 D3/D4 established a redundant-selector null under an information-poor
  selector design; it did not test news reasoning.
- FinGPT established no promotion basis for a fixed FinBERT sentiment factor and
  significant after-cost inferiority for its tested construction; it did not
  test narrative reasoning.
- R03 therefore begins as a new research line. Neither prior null is evidence
  that R03 must fail or succeed.

## 3. Tier structure and estimands

- **T0:** frozen non-news price/risk/cost baseline.
- **T1:** T0 plus frozen FinBERT sentiment.
- **T2:** T0 plus a frozen non-LLM text model over the same raw text available to
  T3. The cheap-text futility model and T2 are one implementation.
- **T3:** T0 plus LLM reasoning over the same raw text.

Primary estimand: full-frame walk-forward ITT net-utility contrast `T3 - T2`.

Secondary estimands: `T1 - T0` and `T2 - T1`. They are descriptive/supporting
and cannot replace failure of the primary estimand.

## 4. Historical validity status

The 2016–2025 corpus is retrospective and exploratory because:

- modern LLM training may postdate and contain sample-period news or outcomes;
- FinBERT weights postdate part of the sample;
- the reused 2026 S&P 100 universe is survivorship-biased when projected back.

Confirmatory language is forbidden unless T3's documented training cutoff
precedes the evaluation window and the universe is point-in-time correct. The
preferred confirmatory design is prospective: pin the model first, then collect
future news and use a universe fixed at decision time.

## 5. Data posture

Follow `docs/r03-news-reasoning-data-reuse-decision.md`.

- Raw text remains in `C:\Users\User\Desktop\FinGPT\data\news_raw`.
- Access is read-only and local.
- No raw text is copied, committed, pushed, logged, or sent to an external
  provider.
- Tracked artifacts may contain schemas, counts, hashes, aggregate statistics,
  and non-reconstructable diagnostics only.

Preliminary coverage audit (independent review sample; not a corpus census): 60
random pages / 2,810 articles had body content in 68.1%, headline in 100%, and
summary in 36.6%; non-empty body median length was approximately 4.3 KB. The
primary full-frame ITT must not silently select only body-present articles.

Canonical missing-text rule:

- headline is required for an article record;
- `summary` and `content` are separate fields with explicit nulls and presence
  flags; neither is silently substituted for the other;
- body-missing records remain eligible and both T2/T3 receive byte-identical
  fields and flags;
- primary ITT includes all eligible decision frames;
- `BODY_PRESENT` versus `BODY_MISSING` is a preregistered secondary stratum and
  cannot rescue the primary verdict;
- a provider-free full-corpus coverage census must confirm or replace the sample
  estimates before split dates and model inputs are frozen.

## 6. Provider-free fail-only gates

All gates compare against a preregistered minimum economically meaningful effect
`delta_star`. Passing a gate is never positive evidence for T3.

1. **Constrained clairvoyant ceiling:** define incremental headroom as
   `U_clairvoyant_feasible - U_B0`, where `B0` is the best preregistered non-news
   deterministic baseline selected without evaluation leakage. Stop if this
   incremental headroom cannot exceed `delta_star`. Absolute clairvoyant utility
   is not the gate statistic.
2. **Cheap-text learnability:** fit the prespecified T2 family with strict nested
   walk-forward. If the one-sided upper confidence bound of net utility on T2
   residuals is below `delta_star`, pause provider spending and require explicit
   user ratification to terminate. This is a budget/governance gate, not a
   validity claim that narrative-capable LLM reasoning has no value.
3. **Power:** use paired time-series utility differences, dependence-respecting
   blocks, and a one-sided test. Stop or extend the window if MDE exceeds
   `delta_star`.

`delta_star`, utility units, confidence level, cost schedule, block rule, and
worst-cell governance must be frozen before any gate runs.

## 7. Partial-parallel work plan

May proceed while overlay-v2 I0–I5 is underway:

- P0: license/provenance record and source identity;
- P1: schema, PIT timestamp, completeness, duplication, and coverage design;
- P2: estimand, utility, cost, latency, and action-space specification;
- P3: frozen T2 model-family and nested walk-forward specification;
- P4: futility/power formulas and decision labels;
- P5: charter/preregistration review and corrections.

The historical exploratory split topology is mandatory:

`development -> calibration -> one contiguous OOS evaluation, opened once`

Exact dates remain pending the provider-free coverage census. Dates, embargo,
purge, and access permissions must be frozen before text/return model fitting.
The OOS result remains retrospective exploratory evidence under §4.

Must wait until overlay-v2 I0–I5 is implemented, sealed, and reviewed:

- R03 contracts, payloads, grounding, scorers, replay, and gate code;
- fixture or frame materialization;
- any provider or model execution.

Overlay fixture/provider/LIVE completion is not an R03 prerequisite.

## 8. Leakage and independence barriers

- No return labels in prompts, candidate construction, or T3 payloads.
- `available_at = max(created_at, updated_at)` is inherited exactly.
- Split assignment precedes text/return feature development and is hash-bound.
- Development cannot inspect locked evaluation outcomes.
- Hyperparameter and representation selection occurs inside nested training
  windows only.
- Same-session technical review is not organizational independence and must be
  labelled accordingly.

## 9. Decisions still required before implementation

1. Exact `delta_star` and economic utility definition.
2. Exact T0 factor/cost specification.
3. Exact T2 representation, estimator, regularization grid, and abstention rule.
4. Exact dates, embargo, and purge rules within the mandatory development →
   calibration → single contiguous OOS topology, plus prospective confirmatory
   policy.
5. PIT universe source or explicit survivor-panel-only estimand.
6. Written permission/legal clearance before any external-provider transmission.
7. Full-corpus missing-body/summary census and canonical payload schema hash.

## 10. Charter exit criteria

The charter is ready for implementation planning only when:

- every item in §9 is resolved or explicitly blocks the affected phase;
- data identity and license boundaries are reviewed;
- all three futility gates have exact formulas and fail labels;
- the T2/T3 information sets are byte-equivalent apart from model method;
- historical exploratory and future confirmatory claims are separated;
- no raw article text exists in the repository or tracked artifacts;
- the exact charter/preregistration hashes pass independent technical review.

## 11. First charter review findings accepted

The first review round accepted four corrections:

- **F1:** record measured text coverage and freeze missing-text canonicalization;
- **F2:** treat G2 failure as a user-ratified provider-budget pause, never as
  evidence of T3 incapability;
- **F3:** define G1 on incremental headroom over frozen non-news baseline `B0`;
- **F4:** require development → calibration → one contiguous, one-open OOS
  topology even while exact dates remain pending.

Phase ID R03 and read-only, in-place FinGPT reuse were explicitly user-ratified
on 2026-07-19. This review acceptance authorizes no implementation or execution.
