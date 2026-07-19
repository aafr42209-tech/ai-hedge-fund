# R03 P5 provider-free charter hardening — review handoff

Status: **ACCEPTED_WITH_NONBLOCKING_FINDINGS; NONBLOCKING CORRECTIONS APPLIED; PROVIDER-FREE RESEALED**
Phase: R03-P5
Prepared: 2026-07-19
Authority exercised: local aggregate audit and design-document edits only

## 1. Review request

Review the exact pinned P5 set for scientific identification, PIT correctness,
economic meaning, statistical power, information parity, overfitting control,
data-license boundaries, and normalized governance labels.

This handoff requests no implementation, fixture/frame materialization, provider
call, raw-text export, commit, or push.

## 2. Exact review set

| Artifact | SHA-256 |
|---|---|
| `docs/r03-news-reasoning-data-reuse-decision.md` | `097e6df5ed4aafccc1031cfb3ab7f0639dce439d84b5f57e968fb4462cd58a0a` |
| `docs/r03-news-reasoning-charter-draft.md` | `e5527c13a14b86dbeba6a1ee9d7290ebcbd0eb53e5d0c1c8ae512672f2710724` |
| `docs/r03-news-reasoning-provider-free-preregistration-draft.md` | `629d282b71fc19f5db691de47c325f195d01c4ec1ae96686b3e4c7bb75f200a2` |
| `docs/r03-news-reasoning-provider-free-coverage-audit.json` | `6275292839b9446825bc8d05cc334a82dc7fe865067501895fd0f2c15c821984` |

Background feasibility record, unchanged in P5:
`docs/news-llm-reasoning-reuse-feasibility-handoff.md`, SHA-256
`4fec8ae4afbd04147933068d3a34b844f9cc653df27658a4ae435fedea6b5c9d`.

## 3. Provider-free evidence added

The full 2.67 GB corpus was read in place. No article text entered tracked files
or model context; only aggregate counts/hashes were emitted.

- 436,916 query captures; 290,858 unique article IDs.
- 146,058 duplicate ticker-query captures (33.43%).
- 247,976 eligible unique articles; 301,541 ticker-article events.
- Eligible coverage: headline 100%, summary 29.33%, body 50.90%, headline-only
  49.10%.
- Symbol relevance rejects 42,879 unique articles with more than five symbols;
  three more lack a headline.
- 2,514 market sessions; 151,820 news-positive ticker-sessions under the exact
  early-close-aware 72-hour window.
- A 32 KiB/article and 128 KiB/ticker-session text budget fully preserves 99.06%
  of news-positive frames and retains 97.03% of text bytes.
- Full raw JSON portable aggregate SHA-256:
  `56f1a5567c1aa5ed5b327201d36f1ca5833381fd3b389279298acdd3a6c1e9d3`.

The earlier 60-page 68.1% body estimate is superseded. Capture count is not an
independent article count.

## 4. P5 design freezes proposed

- Primary estimand remains full-frame `T3 - T2`.
- Decision clock: 15:30 ET or 30 minutes before an early close.
- News window 72h; outcome h=5; bars through t-1 for T0.
- Development 2016–2020, calibration 2021–2022, one-open OOS 2023–2025 with
  exact five-session purges and 747 evaluable OOS decisions.
- T0: frozen price/risk/liquidity ridge and buffered long-short constructor.
- T1: T0 plus frozen FinBERT sentiment.
- T2/G2: one hash→training-only TF-IDF→deterministic ridge residual model.
- T2/T3: byte-identical canonical news payload, explicit missing fields, fixed
  order and truncation budgets.
- `delta_star = 5 bp` net per h=5 period.
- Transaction costs: 10 bp/side base, 5/15 bp sensitivity; worst cell governs.
- One-sided alpha .05, power .80, stationary block 10, 10,000 resamples.
- G1 uses incremental clairvoyant utility over T0, never absolute utility.
- G2 pause is budget governance and requires a user stop/continue branch.
- Either G2 branch preserves the identical fitted T2 model ID.
- G3 proxy grid uses calibration T2−T0, SD multipliers 1/1.5/2, fail-closed
  rates 0/5%, and the planned 747-decision OOS length.

## 5. Prior nonblocking findings closed

1. Preregistration language now says G2 “does not pause,” not “does not stop.”
2. G2 branches are explicit:
   - `STOP_BUDGET_FUTILITY_USER_RATIFIED`;
   - `CONTINUE_AFTER_G2_PAUSE_USER_RATIFIED`.
3. Continuation is not provider authorization and cannot replace/reselect T2.

## 6. Questions for review

1. Is 5 bp net per h=5 period a defensible minimum economically meaningful
   T3−T2 increment under the 5/10/15 bp-per-side grid?
2. Is the proposed T0 sufficiently strong while remaining PIT-computable from
   the available bars, and is the monthly matured-label refit leakage-safe?
3. Does hashed word 1–2 gram TF-IDF plus deterministic ridge make an adequate
   same-text non-LLM comparator for “reasoning beyond bag-of-words”?
4. Are the 32 KiB/article and 128 KiB/frame budgets and newest-first ordering
   scientifically fair, deterministic, and provider-operable?
5. Do the exact development/calibration/OOS dates and five-session purges protect
   the one-open OOS boundary?
6. Is the G3 calibration-proxy variance grid conservative enough without making
   a provider-free no-go claim about T3 capability?
7. Are the survivor-panel and model-cutoff rules strong enough to prohibit any
   historical confirmatory claim?
8. Are any implementation-level identities being frozen prematurely before the
   overlay-v2 I0–I5 common machinery is sealed?

## 7. Hard boundaries

- Raw Alpaca/Benzinga text stays read-only in FinGPT.
- No raw text in repository, prompts, logs, fixtures, or provider requests.
- No R03 implementation or fitted T0/T1/T2 model exists.
- No outcome gate has run; the census used content metadata only.
- No external provider/model call or data transmission occurred.
- Same-session lineage is not organizational independence.
- Historical 2016–2025 evidence is exploratory, including the procedural OOS.

## 8. Requested review disposition

Return one of:

- `ACCEPTED_FOR_IMPLEMENTATION_PLANNING`;
- `ACCEPTED_WITH_NONBLOCKING_FINDINGS`;
- `REVISE_AND_REVIEW_AGAIN`;
- `INVALID_DESIGN`.

List every finding with severity, exact artifact/section, rationale, and required
correction. Verify the hashes in §2 before reviewing content.

## 9. Next order after review

1. Correct findings and regenerate exact hashes.
2. Seal a provider-free zero-call review manifest.
3. Obtain separate user approval for the corrected documentation commit/push.
4. Wait for overlay-v2 I0–I5 implementation, sealing, and review.
5. Draft a separate R03 provider-free implementation plan; do not implement it
   without another explicit approval.

## 10. Independent technical review record (2026-07-19)

- Reviewer: Claude (Fable 5), same-session lineage — technical verification
  only; organizational independence NOT established.
- §2 hashes verified before content review; this handoff's own pre-review hash
  (`a8ab49d3…`) verified against the submission.
- **Census independently reproduced from the raw corpus (full 2.67 GB rescan,
  provider-free, no text emitted):** 436,916 captures; 290,858 unique IDs;
  146,058 duplicates (33.43%); 247,976 eligible; 301,541 ticker-events;
  body 126,217 (50.90%); summary 72,729 (29.33%); headline-only 121,759
  (49.10%); rejects 3 headline-missing + 42,879 over-five-symbols; 0
  out-of-window. **Every figure matches exactly.** Additional check:
  summary-without-body = 0, so the `headline_only` label is precise.
  301,541 equals FinGPT's scored-event count. The superseded 68.1% sample
  matches the capture-level rate (66.22%), explaining the discrepancy.
- **Splits independently reproduced from `market_bars_real.parquet`:** 2,514
  sessions (2016-01-04 → 2025-12-31); dev 1,254 + purge 5 (exact named
  sessions) + calibration 498 + purge 5 (exact named sessions) + OOS **747**
  (2023-01-03 → 2025-12-23) + 5 post-OOS label sessions = 2,514, a complete
  partition. The last OOS decision's h=5 label matures exactly on the final
  five sessions (12-24, 12-26, 12-29, 12-30, 12-31).
- Answers to §6: (1) `delta_star` = 5 bp/h5 ≈ ~2.5%/yr net increment —
  defensible under the 5/10/15 bp grid; (2) T0 is PIT-safe (t−1 bars,
  same-date cross-sectional imputation/clipping, matured-label monthly refit,
  development-only alpha selection); (3) hashed 1–2-gram TF-IDF + ridge is an
  adequate same-text bag-of-words comparator for the "beyond bag-of-words"
  estimand; (4) budgets/ordering are deterministic, fair, and
  provider-operable; (5) split dates and five-session purges verified exact;
  (6) the G3 proxy grid (SD ×{1,1.5,2}, fail-closed {0,.05}, worst cell
  governs) is acceptably conservative and correctly framed as non-capability
  evidence; (7) survivor/cutoff confirmatory prohibitions are strong;
  (8) no premature implementation freeze — schema hash and model IDs correctly
  deferred.
- Blocking findings: **0**. Nonblocking findings:
  1. (MEDIUM) prereg §3 still says decision clock/horizon/aggregation "remain
     `PENDING_REVIEW`" — stale after §14 froze them; reword to "frozen for
     review in §14; gate execution blocked until acceptance and implementation
     pins."
  2. (LOW) prereg §6-G3 (formula MDE) vs §14.4-G3 (simulation grid): add a
     clarifier that §14.4 operationalizes and governs.
  3. (LOW) boundary asymmetry: G1 stops at "at or below" (≤ δ*) while G2
     pauses "below" (< δ*); unify or document as intentional.
  4. (NOTE) payload-retention figures (99.06% frames / 97.03% bytes) were not
     independently recomputed (inputs verified, methodology plausible); the
     later implementation verifier should recompute them as a negative test.
  5. (NOTE) T2 pins name library-specific components; the library identity and
     version must become part of the T2 model ID at implementation time.
- Disposition: **`ACCEPTED_WITH_NONBLOCKING_FINDINGS`**. This acceptance
  authorizes no implementation, fixture/frame materialization, provider call,
  gate execution, commit, or push.

### 10.1 Nonblocking-finding disposition (2026-07-19)

The review record above is preserved verbatim. Codex applied the five requested
nonblocking corrections without expanding authority:

1. prereg §3 now points to the §14 review freeze and retains the implementation-
   pin execution block;
2. prereg §6 states that the §14.4 simulation grid operationalizes and governs
   G3, while the analytical MDE formula is diagnostic only;
3. G1 and G2 now share the conservative `upper bound <= delta_star` boundary;
4. charter §12.2 and prereg §7 require the implementation verifier to recompute
   payload retention and fail closed under cap, ordering, early-close, and
   duplicate-selection perturbations without emitting raw text;
5. charter §12.5 and prereg §14.3 require the T2 model ID to bind exact runtime,
   library, component, and output-relevant solver identities and versions.

These documentation corrections authorize no implementation, fixture/frame
materialization, provider call, gate execution, commit, or push. Corrected hashes
are pinned in §2 and the companion zero-call manifest seals this corrected set;
technical acceptance is not upgraded to organizational independence.
