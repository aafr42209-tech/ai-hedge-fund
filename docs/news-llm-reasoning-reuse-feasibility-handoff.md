# News-driven LLM-reasoning verification — feasibility & FinGPT reuse handoff

Date: 2026-07-19 (Asia/Seoul)

Status: **DESIGN-EXPLORATION HANDOFF — NOTHING FROZEN — NO AUTHORIZATION — NO DATA MOVEMENT — PROVIDER/LIVE NO-GO**

Phase identifier: provisional (unassigned; do not assume `r03` until a phase ID is chosen before drafting a real charter).

This document records (1) the established scoped results, (2) the verification the
user actually wants, (3) an inventory of reusable FinGPT news assets, and (4)
ranked reuse approaches with their constraints — for independent (Codex) review.
It authorizes no implementation, no data copy, no provider call, no commit, no push.

---

## 1. Why this handoff exists

The overlay research line (this repo, `r02` D3/D4/overlay-v2) and the FinGPT
project have each produced **rigorous but narrowly scoped null results**. Both
nulls sit on the most-verifiable, least-ambitious version of the original
question. The question the user originally cared about — *can an LLM reasoning
over unstructured news construct better portfolios* — has not been tested in
either project. This handoff scopes that question and asks whether FinGPT's
already-collected news evidence can accelerate answering it here.

## 2. Established results and their exact scope

### 2.1 This repo — candidate-selection selector (D3/D4)

- LLM selector reproduced a deterministic parsimony rule **124/124** (55 in D3,
  69 in D4 preregistered comparison).
- D4 labels: primary `REPLICATION_SUPPORTED_FRAGILE`; incremental LLM
  `NOT_IDENTIFIED_REDUNDANT_SELECTOR`.
- **Scope limit:** the selector saw only opaque candidates (action/quantity), no
  utility-relevant public state. "No identified LLM value" is a consequence of an
  unidentifiable design, not evidence about LLM capability. Overlay v2 (accepted
  preregistration, commit `245adc2`) is the first design that gives the LLM
  utility-relevant public state — but still as a **selector among 2–4
  deterministic-generator candidates in a synthetic, computable-oracle world**.

### 2.2 FinGPT — news sentiment factor (`text-minimal-block v1`)

Single-shot, preregistered, real data. What it actually tested:

- **Universe:** S&P 100, 2016–2025 (survivorship-biased; documented limitation).
- **Pipeline:** Alpaca news (`data.alpaca.markets/v1beta1/news`, `include_content`,
  ~436,916 fetched) → completeness PASS → FinBERT (`ProsusAI/finbert`,
  rev `4556d130…`, inference-locked) scored **301,541 events** → feature
  `sentiment_mean_3d` → 5-day-horizon (`h=5`) cross-sectional **rank IC** vs
  forward returns, plus cost-aware net spread.
- **PIT discipline:** `available_at = max(created_at, updated_at)`; text usable
  only after `available_at` (look-ahead controlled).
- **Verdict `no_signal`** (report `artifacts/news_main/text_block_report.json`,
  sha256 `35eb690a…`): pooled rank IC `−0.0025` (block-bootstrap CI
  `−0.011 … +0.006`, includes 0), pooled net spread `−31.3 bp/period` (CI
  `−41.7 … −20.5`, all negative), positive years `0/9`, positive phases `0/5`.
  Gates ①–④ failed; min-sample gate ⑥ far exceeded; `no_signal` veto fired;
  closed with no readjustment.
- FinGPT's own recorded nuance: IC CI includes 0 → this is **"absence of
  promotion basis," not proof of IC = 0**; but the after-cost net-spread
  inferiority **is** significant. FinBERT weights postdate the 2016 sample start
  → possible weight look-ahead → **exploratory only, no confirmatory claim**.

**What FinGPT rejected:** a fixed small-classifier sentiment score, aggregated as
a 3-day mean, used as a linear cross-sectional factor at a 5-day horizon in this
universe — cost-losing.

**What FinGPT did NOT test:** an LLM *reasoning over the news narrative itself*
(not a sentiment label) to inform portfolio decisions.

## 3. The verification the user wants

> Given point-in-time public information **plus the news available at decision
> time**, does an LLM that **reasons over the news narrative** add portfolio
> utility over the strongest preregistered deterministic public-information
> comparator **that already includes the news sentiment factor** — after costs,
> latency, look-ahead control, and multiple-comparison/overfitting discipline?

The sharp, attributable estimand: the comparator floor must contain the
already-null sentiment factor. If LLM-over-raw-news beats a comparator that
already has `sentiment_mean_3d` (and strong price/fundamental factors), the
increment is attributable to **reasoning over narrative beyond bag-of-sentiment**
— which is exactly the untested question.

### 3.1 Method: port overlay v2's structure to the real-news world

Reuse the overlay v2 machinery, changed only where real data forces it:

- **3-tier information-parity comparison** (all tiers see byte-identical public
  payload; only the LLM tier additionally sees raw news text at/after
  `available_at`):
  1. strong deterministic public-info scorer (price/risk/cost factors);
  2. that scorer **+ the FinBERT sentiment factor** (the null-but-cheap baseline
     to beat) — this is the primary comparator;
  3. LLM-overlay reasoning over the raw news narrative.
- **Primary endpoint:** full-frame walk-forward ITT utility contrast, tier 3 − tier 2.
- **Preserved from overlay v2:** preregistration, split/seed firewall, blinded
  pilot for feasibility (discordance/coverage), structured grounded output,
  fail-closed tier-2 execution on any LLM failure, model-identity pins.

### 3.2 The hard difference from overlay v2: no computable oracle

Overlay v2's decisive `headroom` gate needs `oracle − best-deterministic`, which
requires a **computable** optimum. Real forward returns are a noisy oracle, so
this gate does **not** transfer directly. Consequences to design for:

- Overfitting/backtest bias becomes the dominant adversary. The overlay-v2
  discipline (pre-registration, sensitivity grid, worst-cell governance, single
  shot) is necessary but must be extended with **strict walk-forward /
  out-of-sample separation** and event-count power on noisy returns.
- The "is there any headroom at all" question needs a real-data surrogate, e.g.
  a preregistered upper-bound analysis (post-hoc-optimal-with-hindsight utility)
  used **for power/feasibility only, never as a comparator input**.
- FinGPT already proved the *sentiment-factor* channel is cost-losing; tier 2
  encodes that. So the bar is explicit and high: LLM reasoning must extract from
  the same news what the sentiment factor could not, **net of cost and latency**.

## 4. FinGPT reusable assets (inventory)

All paths under `C:\Users\User\Desktop\FinGPT`. Total `data/` ≈ 3.8 GB.

| Asset | Path | What it is |
|---|---|---|
| Raw news pages (with content) | `data/news_raw/<TICKER>_<YEAR>/page_NNNN.json` | 10,270 local JSON files, 2,668,932,157 bytes; 1,000 complete ticker-year manifests; 436,916 declared articles; raw `content`/headline/summary plus source timestamps |
| Document metadata only | `data/raw/documents.parquet` | 987 rows; title/hash/source/PIT metadata only; **does not contain article body text and cannot serve R4** |
| Derived event table | `artifacts/news_main/article_events.parquet` | 301,541 scored events (ticker, timestamps) |
| Sentiment scores | `artifacts/news_main/sentiment_scores.parquet` (+ `…_metadata.json`) | FinBERT per-event scores → the null tier-2 factor |
| Completeness/verdict | `artifacts/news_main/{completeness_report,text_block_report}.json` | coverage + frozen `no_signal` verdict, run identity |
| Ingestion + PIT code | `src/market_signal/ingestion/{providers/alpaca_news.py,news_preflight.py}` | fetch + PIT/coverage preflight gate |
| Scoring code | `src/market_signal/textblock/finbert.py`, `docs/finbert-inference-lock.md` | inference-locked sentiment scoring |
| Universe | `configs/universe.json` | S&P 100, survivorship-biased, sha-pinned source |
| Price bars | `data/raw/market_bars_real.parquet` | real bars for the same universe/window (forward-return labels) |

## 5. Reuse constraints (READ FIRST — these gate everything)

1. **LICENSE / redistribution (dominant constraint).** Alpaca market data is
   under Alpaca ToS / Market Data Agreement; FinGPT's `docs/license-matrix.md`
   records its own policy as **personal research, local storage only, no
   redistribution, no commercial use**, and lists an *outstanding* legal review of
   the store/derivative/redistribution clauses. Implications:
   - Do **not** copy raw Alpaca article text into this repo's tracked tree, and
     **never commit/push it to any remote** — that is redistribution.
   - Derived, non-reconstructable artifacts (e.g. numeric sentiment scores, event
     timestamps without text) are lower-risk but still ToS-dependent; treat as
     local-only until the legal review clears them.
   - Any cross-project use should be **read-only, in place**, or via a local,
     git-ignored working path — not a committed data import.
2. **PIT discipline must be inherited, not re-derived loosely.** Reuse FinGPT's
   `available_at = max(created_at, updated_at)` stamping exactly; any new join to
   prices/labels must reproduce look-ahead control or the result is void.
3. **Look-ahead in scoring.** FinBERT weights postdate 2016 → sentiment tier is
   exploratory. An LLM tier has the same concern in stronger form (training cutoff
   ≥ sample) — this must be a stated validity limitation, not hidden.
4. **Survivorship bias.** The S&P-100-as-of-2026 universe applied back to 2016 is
   survivorship-biased (FinGPT-documented). Any reuse inherits it; state it.
5. **Provenance / independence.** Same-session-lineage technical verification is
   not organizational independence (carried over from overlay v2 discipline).

## 6. Candidate reuse approaches (ranked; each needs review)

- **R1 — Port the PIT/preflight *code*, not the data (lowest risk, high value).**
  Reuse `news_preflight.py` + `alpaca_news.py` patterns to re-fetch under this
  repo's own credentials/policy, so provenance and license posture are clean here.
  Cost: re-fetch time; benefit: no cross-repo data-redistribution question.
- **R2 — Reuse derived sentiment scores as the tier-2 comparator floor
  (medium risk).** `sentiment_scores.parquet` is exactly the already-null factor
  tier 2 must contain. Lets us stand up the comparator without re-scoring. Gate on
  license (numeric derivative) + identity pin to FinGPT's inference lock.
- **R3 — Reuse the event table as an LLM-trigger index (medium risk).**
  `article_events.parquet` (timestamps/tickers, no text) defines *when there is
  news to reason about* — an escalation trigger for the LLM tier, cheap and
  text-free.
- **R4 — Reuse raw article text to feed LLM reasoning (highest value, highest
  risk).** The actual narrative for tier 3. **Local-only, never committed**; blocked
  until the Alpaca ToS legal review clears local derivative use, and only through
  a git-ignored path. This is the crux asset and the crux constraint.
- **R5 — Reuse price bars + universe for forward-return labels (low/medium
  risk).** `market_bars_real.parquet` + `configs/universe.json` give the noisy
  oracle and the frame; same license/survivorship caveats.

## 7. Open questions for independent (Codex) review

1. Is the tier-2-includes-sentiment estimand the right isolation of "reasoning
   value," or should sentiment be a separate tier to measure both increments?
2. Without a computable oracle, what real-data feasibility gate replaces overlay
   v2's headroom gate — and can it stop the program provider-free before any LLM
   call?
3. What walk-forward + power design controls backtest overfitting on ~301k events
   / ~2,508 periods, and what is the minimum detectable net-of-cost effect?
4. Which reuse approach (R1–R5) is legally and scientifically cleanest as a
   first step, and does R4 require an explicit user/legal decision before any use?
5. How is LLM-training-cutoff look-ahead bounded or disclosed on 2016–2025 news?
6. Does survivorship bias in the reused universe invalidate the primary endpoint,
   or is it a bounded stated limitation?

## 8. Hard boundaries (until separate, explicit approvals)

Forbidden by this handoff: copying/committing/pushing Alpaca raw news text;
cross-repo data redistribution; provider or Codex execution; LLM/pilot/
confirmatory LIVE runs; fixture materialization; implementation of any scorer,
payload, or news pipeline in this repo; retry/replacement/resume; commit or push.
No provider budget, data-export approval, or LIVE authorization is implied.

This is a feasibility/design record only. A real research charter, preregistration,
and provider-free verifier would each be separate, separately-approved units.

## 9. Next order

1. ~~Independent (Codex) review of this feasibility handoff against §7.~~ **DONE
   2026-07-19 — see §10.**
2. ~~Decide whether to duplicate the FinGPT raw-news corpus into this repo.~~
   **DONE 2026-07-19: do not copy. Reuse the existing local corpus read-only,
   in place.** This avoids a second 2.67 GB copy and reduces license/provenance
   risk. Raw-text provider transmission remains blocked; see the R03 data-reuse
   decision.
3. ~~Assign a phase identifier and begin charter + provider-free
   preregistration drafts.~~ **STARTED 2026-07-19 as R03**, incorporating §10.
4. Review the R03 charter/preregistration drafts. Provider-free R03 code waits
   until overlay-v2 I0–I5 is implemented, sealed, and reviewed. Fixture, pilot,
   provider, and confirmatory work remain separately approved later steps.

## 10. Codex review outcome (2026-07-19) — ACCEPTED REVISIONS

Codex reviewed this handoff against §7. Verdict: **conditional proceed** — the
research line is sound and honestly scoped, but the §3.1 design as written does
not identify "LLM-reasoning-specific value." All points below are accepted and
**supersede §3.1–§3.2 for any future charter**. This section is the review
record; the handoff body above is left as reviewed.

### 10.1 Tier structure (answers §7-1) — SUPERSEDES §3.1

The 3-tier design confounds two increments in `tier3 − tier2`: (a) access to
raw text, (b) LLM reasoning over it. Revised 4-tier structure:

- **T0** — non-news baseline (price/risk/cost factors).
- **T1** — T0 + FinBERT sentiment factor (the known-null cheap channel).
- **T2** — T0 + a **frozen non-LLM text model over the same raw text**
  (e.g. TF-IDF/hashed or frozen text representation, strict nested
  walk-forward).
- **T3** — T0 + LLM reasoning over the same raw text.

**Primary estimand: `T3 − T2`** (isolates reasoning *method* given equal
information access). `T1 − T0` and `T2 − T1` are preregistered secondary
estimands.

### 10.2 Provider-free futility gates (answers §7-2) — SUPERSEDES §3.2's surrogate

A single hindsight-oracle upper bound is rejected: post-hoc optimization
manufactures headroom even from pure noise. Replacement — a **triple
provider-free futility gate**, each fail-only (can stop the program, never
counts as pass evidence), against a preregistered minimum economic effect `δ*`:

1. **Constrained clairvoyant ceiling** — hindsight-optimal policy under real
   trading/exposure/turnover/latency constraints; if even this ≤ `δ*`, stop.
2. **Cheap-text learnability gate** — non-LLM text representation evaluated by
   strict nested walk-forward on T2 residuals; if the one-sided upper CI of net
   utility < `δ*`, stop.
3. **Power gate** — if MDE (from independent time-series blocks) > `δ*`, the
   experiment cannot answer; stop or extend the window.

### 10.3 Walk-forward & power design (answers §7-3)

~301k events are **not** the sample size; overlapping `h=5` returns and
date/ticker clustering shrink the effective N below ~2,508 decision periods.
Required structure:

- Splits: development (rules/features/cost model) → calibration (thresholds,
  execution stability only) → **one final contiguous OOS evaluation, evaluated
  once**.
- Inference unit: **paired portfolio-utility time series**, not events.
- Uncertainty: date-level clustering + block bootstrap/HAC with block ≥ `h=5`.
- `MDE = (z(1−α) + z(power)) × HAC_SE`; success requires statistical
  superiority **and** the preregistered net economic threshold `δ*` jointly.

### 10.4 Reuse ranking & R4 legal scope (answers §7-4)

R1 (port code, re-fetch under own credentials) is the cleanest first step —
but re-fetching cleans **provenance/redistribution only, not the underlying
Alpaca ToS scope**. The R4 legal decision must explicitly cover: local
analysis; derivative creation/retention; **transmitting article text to an
external LLM provider**; storage/sharing/redistribution of outputs. User
approval alone does not create legal permission. If scope stays unclear,
boundary = **local inference only**.

### 10.5 LLM training-cutoff look-ahead (answers §7-5) — validity rule

Masking dates/tickers does not fix memorization of 2016–2025 articles and
outcomes. Only two confirmatory-capable options:

- evaluate only news **after** the model's documented training cutoff, or
- **pin the model first, collect data prospectively**.

Otherwise every historical-window result MUST be labeled
`retrospective exploratory capability test` — never confirmatory.

### 10.6 Survivorship (answers §7-6) — endpoint rule

The 2026-constituent universe back-applied to 2016 is **not** a bounded minor
limitation: without PIT constituent history, the primary endpoint must be
downgraded to "retrospective results on the 2026 survivor panel." PIT
reconstruction restores a normal primary endpoint.

### 10.7 Charter preconditions (Codex's three mandatory fixes)

Before any charter/preregistration:

1. Add the same-raw-text non-LLM tier (T2) so information access and reasoning
   method are separated (→ §10.1).
2. Replace the hindsight upper bound with the fail-only ceiling + cheap-text
   futility + MDE gates (→ §10.2).
3. Explicitly forbid calling historical-LLM evaluation or the
   survivorship-biased universe "confirmatory" (→ §10.5, §10.6).

### 10.8 Accepted sequencing decision (2026-07-19)

Use partial parallelism:

- R03 design, license/provenance review, data inventory, charter, and
  provider-free preregistration may proceed now.
- R03 scorer/payload/news-pipeline implementation waits for overlay-v2 I0–I5 to
  be implemented, sealed, and reviewed, so shared contracts, grounding, replay,
  split/seed, power, and zero-call machinery have one stable implementation.
- Overlay fixture/provider/LIVE completion is **not** a prerequisite for later
  R03 provider-free implementation.
- The frozen cheap-text model used by futility gate 2 becomes T2 if the gate
  survives; it must not be reselected after gate results are known.

### 10.9 Explicit user ratification (2026-07-19)

The user explicitly approved:

- phase identifier **R03**; and
- FinGPT news reuse **read-only and in place**, with no raw-news copy into this
  repository.

This ratification does not authorize external-provider transmission, commercial
use, redistribution, implementation, fixture materialization, provider calls,
commit, or push.
