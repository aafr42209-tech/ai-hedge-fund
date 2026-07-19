# R03 news-reasoning provider-free implementation plan (draft)

Status: `REVIEW_ACCEPTED_RESEALED_IMPLEMENTATION_STILL_NO_GO`

Phase: `R03`

Scope: historical option `(c)` only; survivor-panel evidence remains exploratory.

This document is a plan, not implementation authority. It authorizes no source-data scan, frame or fixture materialization, model fitting, gate execution, provider or local-model call, dependency change, commit, or push.

## 1. Decision context

R02 overlay-v2 I0–I5 is technically accepted at commit `52bf68805cb42f5b06c39de09cc6201e6e093834`. That satisfies the prerequisite for planning an R03 provider-free implementation against the sealed P5 design.

The user has already ratified prospective option `(d)`. That decision is not reopened here. Its design remains deferred until historical G1–G3 results exist and model-pin/operational inputs are separately resolved. No legal inquiry is a prerequisite for the already ratified local read-only/provider-free path. Legal or written-permission review becomes relevant only if a future path would transmit source text to an external provider, redistribute it, or use it outside the approved personal/non-commercial local boundary. Options `(a)` and `(b)` remain frozen; historical option `(c)` remains the current research frame.

The primary future estimand remains `T3 - T2`: incremental net utility from full-text LLM reasoning over an information-equal, non-LLM bag-of-words comparator. This plan does not implement or run T3. It prepares deterministic data, comparator, validation, audit, replay, and futility machinery needed before any T3 authorization can be considered.

## 2. Sealed inputs

All SHA-256 values below are hashes of the current filesystem bytes at planning time.

| Input | SHA-256 |
|---|---|
| `docs/r03-news-reasoning-charter-draft.md` | `e5527c13a14b86dbeba6a1ee9d7290ebcbd0eb53e5d0c1c8ae512672f2710724` |
| `docs/r03-news-reasoning-provider-free-preregistration-draft.md` | `629d282b71fc19f5db691de47c325f195d01c4ec1ae96686b3e4c7bb75f200a2` |
| `docs/news-llm-reasoning-reuse-feasibility-handoff.md` | `4fec8ae4afbd04147933068d3a34b844f9cc653df27658a4ae435fedea6b5c9d` |
| `docs/r03-news-reasoning-data-reuse-decision.md` | `097e6df5ed4aafccc1031cfb3ab7f0639dce439d84b5f57e968fb4462cd58a0a` |
| `docs/r03-news-reasoning-provider-free-coverage-audit.json` | `6275292839b9446825bc8d05cc334a82dc7fe865067501895fd0f2c15c821984` |
| `docs/r03-news-reasoning-p5-review-handoff.md` | `07cadebb5040e26d36f179a5ec190c23addc6001260f1ba54d784e0554516864` |
| `docs/r03-news-reasoning-p5-zero-call-manifest.json` | `b7488afd71ee0f30fe5cd0d10b782e88ecae5335385f55b8077920a4ff14d4e3` |
| `docs/r03-pit-universe-feasibility.md` | `0e3acae592ab80a3ffbf7744f59dce00a8fea505239759277c68dd51a63a2095` |
| `docs/r03-pit-universe-feasibility-evidence.json` | `4797ab56e451432ed82aa0f9155dbb8ceee426451736490a17aa9f8b062c24bf` |
| `docs/r02-overlay-v2-implementation-evidence.json` | `3af3a5c0bafec0888ce5ef2f434f8186ac71c18c074f70b2aed3cb4beeb3fbbc` |
| `docs/r02-overlay-v2-implementation-zero-call-manifest.json` | `76817f60c8b932ae0d9419213042bf0ba4c4706a6952976f02a765a3b31f8d23` |
| `docs/r02-overlay-v2-provider-free-implementation.md` | `3490c72154d03c038148f81f4d096150affcea2db5c40d863708b29d7f74f867` |
| `docs/r02-overlay-v2-implementation-review-handoff.md` | `d044f1773ad2fd66eba4900d8d94927a17c6ab0690cb5997cdaaa7ee31ef4f55` |
| `scripts/r02_overlay_v2_implementation_verify.py` | `33183170190cb20d0e0750141031693b0165ddde3c4a8cda9eaaabca7c4e4059` |

R02's acceptance status is `TECHNICALLY_ACCEPTED_PROVIDER_FREE_IMPLEMENTATION_FIXTURE_AND_LIVE_NO_GO`. R03 inherits that machinery as reviewed code, not as authority to run fixtures, LIVE paths, providers, or licensed source data.

## 3. Hard boundaries

### 3.1 Data and license boundary

- The approved FinGPT news corpus is read-only in place at `C:\Users\User\Desktop\FinGPT\data\news_raw`.
- Raw article text must never be copied into this repository, committed, pushed, emitted in logs, error messages, snapshots, test output, manifests, or review artifacts.
- No external provider transmission is approved. This plan also does not authorize an inference run. The ratified reuse decision nevertheless permits a future, separately chartered and implementation-authorized local inference path without a new legal prerequisite.
- Repository tests use synthetic in-memory text and temporary directories only.
- Future source readers fail closed unless the configured root matches the approved descriptor and the frozen aggregate inventory is verified.
- `documents.parquet` is metadata, not a substitute source for article bodies.

### 3.2 Capability boundary

The future R03 provider-free package may contain contracts, parsers, deterministic transformations, estimators, statistical gates, audit, and replay. It must contain no network transport, provider SDK, credential lookup, subprocess escape, browser automation, model download, remote URL, or implicit package installation.

T3 support is limited to:

1. deterministic request-envelope construction from the canonical payload;
2. strict response-schema and grounding validation;
3. replay of already sealed synthetic/offline responses; and
4. provider-call accounting whose only accepted value is zero.

If historical `(c)` later survives G1–G3 and receives a separate T3 implementation/run approval, the preferred first execution candidate is local inference so licensed text remains on the workstation. That future model identity must bind weight-file SHA-256 values, tokenizer and prompt-template hashes, quantization format/config, inference engine and version, numerical backend, context/window settings, decoding parameters, seed, and hardware/output-relevant runtime identity. A null would apply only to that pinned local model; it must not be generalized to frontier providers.

For prospective `(d)`, a future design may instead select a corpus whose terms expressly permit the intended external transmission. SEC filings, issuer releases, or public-agency materials are candidates for source-by-source rights review, not pre-cleared classes in this plan. Changing from financial news to filings or releases changes the corpus and potentially the estimand and therefore requires a new preregistration.

### 3.3 Research boundary

- The historical survivor panel and model-cutoff overlap prohibit confirmatory language.
- Development and calibration may be used only as preregistered. Procedural OOS is one-shot and remains unopened until a separate execution authorization.
- A gate pass is not evidence that T3 has signal. A G2 pause or user-ratified stop is not evidence that T3 cannot reason.
- No result from this plan changes the already ratified but deferred option `(d)`.

## 4. Binding to R02 I0–I5

R03 should import or thinly adapt reviewed public R02 machinery instead of forking it silently.

| R02 machinery | R03 binding | Permitted R03 deviation |
|---|---|---|
| strict Pydantic contracts, schema/metaschema and instance validation | R03 contracts compose the same strict/fail-closed patterns | News, frame, tier, model-identity, bound-certificate, and gate-result schemas are new |
| canonical payload and digest | same deterministic byte-first interface and digest discipline | article bundle schema, byte caps, availability and duplicate rules are R03-specific |
| RFC 6901 grounding | same pointer syntax, parse and validation discipline | pointers address news-payload fields and articles |
| deterministic comparator family | same config sealing, deterministic ties, public metrics | T0/T1/T2 tier definitions replace synthetic comparator scorers |
| seal selection before outcomes | same no-outcome-before-seal rule wherever an estimand permits it | G1 is explicitly perfect-foresight and therefore uses a separate bound contract, never the normal selector path |
| split, seed, power machinery | same nonoverlap, domain separation, PCG64 and Wilson/report patterns | calendar-session purges, h=5 phase books, stationary bootstrap and preregistered G3 proxy grid |
| append-only hash-chained audit and replay | same event-chain and evidence discipline | raw-text-free public events and model/training-frame identities |
| zero-call/static forbidden-capability verifier | same fail-closed concept and independent negative tests | adds licensed-text non-emission and source-root controls |

Every adapter must declare its upstream R02 public symbol, R02 source hash, R03 reason, and equivalence or deviation test. Undeclared copied logic is a verifier failure.

## 5. Proposed implementation surface

Names are reviewable proposals, not authorization to create files.

```text
v2/research/news_reasoning/
  __init__.py
  r03_contracts.py
  r03_source.py
  r03_payload.py
  r03_frames.py
  r03_tiers.py
  r03_headroom.py
  r03_power.py
  r03_audit.py
tests/
  test_r03_contracts.py
  test_r03_source.py
  test_r03_payload.py
  test_r03_frames.py
  test_r03_tiers.py
  test_r03_headroom.py
  test_r03_power.py
  test_r03_audit.py
scripts/
  r03_news_reasoning_implementation_verify.py
docs/
  r03-news-reasoning-provider-free-implementation.md
  r03-news-reasoning-provider-free-implementation-evidence.json
  r03-news-reasoning-provider-free-implementation-zero-call-manifest.json
  r03-news-reasoning-provider-free-implementation-review-handoff.md
```

No fixture, extracted frame, fitted model, cached vocabulary, article payload, provider response, or result table belongs in the proposed repository file set.

## 6. Implementation sequence and acceptance gates

Each stage requires its own focused tests and evidence entry. Implementation approval, if later granted, does not imply real-data execution approval.

### R03-I0 — contracts and authority boundary

Deliver:

- strict schemas for source descriptor, article record, canonical bundle metadata, split/frame record, tier config, training-frame identity, T0/T1/T2 model identity, outcome-bound certificate, G1/G2/G3 result, audit event, and zero-call evidence;
- schema/metaschema and positive/negative instance tests;
- explicit status lattice separating `PLAN`, `CODE_ONLY`, `DATA_MATERIALIZED`, `GATE_EXECUTED`, and `T3_AUTHORIZED` states;
- the numeric-representation contract in section 14, including exact e12/float64 boundaries and canonical float identity;
- a mandatory `pin_kind` on every digest-bearing field from the first schema version;
- static forbidden-capability scan.

Exit gate: malformed, extra-field, non-finite, timezone-naive, unhashed, unpinned, or authority-escalating objects fail closed.

### R03-I1 — read-only source, canonicalization, and retention

Deliver:

- a reader that accepts only the approved local root and never writes beside the corpus;
- deterministic census and aggregate-hash verification;
- `available_at = max(created_at, updated_at)`, 72-hour article window, early-close-aware decision clock, one-version rule and exact tie break;
- eligibility checks: headline present, 1–5 distinct source symbols, frozen-universe intersection;
- canonical UTF-8/NFC/LF/no-NUL payload with explicit nulls, fixed fields and ordering;
- article and ticker-session byte caps with valid UTF-8 body-prefix truncation;
- independent retention recomputation from raw source without raw-text output.

Frozen corpus anchors:

- 10,270 JSON files, 2,668,932,157 bytes;
- all-JSON aggregate SHA-256 `56f1a5567c1aa5ed5b327201d36f1ca5833381fd3b389279298acdd3a6c1e9d3`;
- page aggregate SHA-256 `4723720c1384723f09c26e9f77941f77a76f1c33d2620e466535eec133213bd9`;
- manifest aggregate SHA-256 `dbb5c4110cc2a198ed506cfb6f38b7db172805f46dc1237c5b6de58f9b7fb894`;
- 436,916 captures, 290,858 unique article IDs, 247,976 eligible unique articles, 301,541 eligible ticker-events;
- expected full-frame/article-appearance/text-byte retention: 99.06% / 99.06% / 97.03% under 32,768 bytes/article and 131,072 bytes/ticker-session.

Exit gate: canonical bytes and public counts/hashes replay exactly; any raw-text emission test fails closed.

### R03-I2 — calendar, frames, outcomes, T0 and T1

Deliver:

- actual-close-minus-30-minute decision clock capped at 15:30 America/New_York;
- development, purge, calibration, purge, one-shot procedural OOS, and label-only tail topology from the sealed P5 split;
- sector-relative split-adjusted close-to-close h=5 outcomes;
- five non-overlapping h=5 phase books;
- price/risk inputs cut at t-1;
- deterministic T0 feature transformation, imputation, clipping, sector demeaning and z-scoring;
- deterministic T1 addition of the frozen FinBERT three-day factor and availability flag;
- common buffered long-short constructor and transaction-cost accounting.

Exit gate: split nonoverlap, purge length `>= h`, decision/label cutoffs, phase-book membership, score ties, no-trade conditions, and cost replay pass on synthetic calendars. No historical frame is materialized.

### R03-I3 — T2 comparator and identity

Deliver:

- residual-text training against the same byte-identical canonical payload later exposed to T3;
- frozen HashingVectorizer word 1–2 grams, `2^18` features, lowercase, `alternate_sign=false`;
- training-only smoothed sublinear TF-IDF with L2 normalization;
- deterministic LSQR ridge grid `{1,10,100,1000}`, tolerance `1e-6`, maximum 10,000 iterations;
- training-window 1/99 prediction clipping and monthly expanding updates using matured labels only;
- deterministic fold selection and tie rules;
- fail-closed T2 identity.

The T2 model ID must bind:

1. Python, NumPy, SciPy and scikit-learn identifiers and exact versions;
2. concrete HashingVectorizer, TfidfTransformer and ridge implementation identifiers;
3. solver name and every output-relevant solver parameter;
4. BLAS/LAPACK implementation and output-relevant runtime identity;
5. canonical schema/payload hash, training-frame hash, split hash, feature config, alpha choice, prediction-clip bounds and fitted-parameter digest.

Exit gate: model identity changes under any listed perturbation; identical identity and synthetic frame reproduce byte-identical predictions and selections.

### R03-I4 — real-data headroom replacement and G1

R02's computable per-candidate synthetic oracle does not exist for historical news. Independent review selected and froze `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1`. It is a valid but deliberately loose fail-only ceiling, not an oracle and not evidence for T3 when it does not stop.

For each calibration decision `t` within its h=5 phase book, use the exact T0-valid eligible set:

- fewer than 20 valid names: `bound_t = 0` under the common forced no-trade rule;
- otherwise sort names by e12-quantized sector-relative realized h=5 return descending, break exact ties ticker-ascending, and set `bound_t` to the mean return of the top 10 minus the mean return of the bottom 10;
- use equal leg weights, gross 1 per leg and net 0, matching the common book shape;
- remove transaction costs and decouple decisions across time, including removal of turnover-cost linkage and buffered-retention coupling.

Aggregate `U_bound` across the five phase books exactly as tier utilities are aggregated. The paired gate series is:

`D_G1,t = bound_t - U_T0,t`.

The sealed stationary block bootstrap uses block length 10, 10,000 resamples and a domain-separated PCG64 seed. Only an upper one-sided 95% limit `<= delta_star`, where `delta_star = 0.0005` net h=5 utility, yields `STOP_NO_ECONOMIC_HEADROOM`.

Upper-bound direction: for every feasible policy path, removing nonnegative transaction costs cannot reduce its objective. Maximizing each period over the uncoupled book superset cannot be smaller than that policy's buffered/coupled book. With 20 or more valid names, sorted top-10 minus bottom-10 spread is nonnegative, so it also dominates the no-trade value zero. Therefore the sum of the relaxed period maxima dominates every feasible realized net-utility path, including never trading.

The per-period `BoundCertificate` contains the valid-name-set digest, sorted-return-order digest and both selected legs. Replay re-sorts and must reproduce the legs and e12 `bound_t` byte-identically. Selection of the k largest and k smallest values exactly certifies the relaxed per-period optimum; no new solver, dependency, optimality gap or timeout tolerance exists. NaN or missing-return leakage into the valid set, digest mismatch, wrong leg size, overlap, sort/tie violation, or non-reproduction yields `G1_INVALID_NO_DECISION`, never a stop.

The G1 report must include a diagnostic-only feasible lower bracket: a greedy clairvoyant path using the full transaction costs and buffered constructor. `[greedy feasible, U_bound]` reports relaxation looseness; the lower bracket cannot govern G1.

Practicality disclosure: the perfect-foresight uncoupled spread is expected to make this ceiling loose and usually inert. A non-stop is only failure to prove futility, never support for T3. G2 and G3 remain the substantive provider-free filters.

The exact coupled MIP/DP optimizer branch was considered and deselected: its dependency and certification cost is not justified for this fail-only gate. It must not be reintroduced without a new reviewed plan amendment.

### R03-I5 — G2, G3, audit, replay, and zero-call verification

Deliver:

- G2 `U_T2 - U_T0`, one-sided 95% stationary-bootstrap upper limit and exact pause/ratification labels;
- G3 proxy `U_T2 - U_T0` with the sealed 747-decision simulation grid, SD multipliers `{1, 1.5, 2}`, fail rates `{0, 0.05}`, effect `delta_star * (1 - fail_rate)`, power floor 0.80;
- analytical MDE as diagnostic only; the simulation grid governs;
- outcome-independent domain-separated PCG64 seeds, block length 10 and 10,000 resamples;
- append-only hash-chained audit events, replay report and public evidence;
- provider-call, local-inference-call, raw-text-emission and network-attempt counters, all required to be zero;
- static capability scan and the eight mandatory negative tests in section 12.

Exit gate: synthetic replay is byte-identical; counter and negative-test evidence is complete; no gate is executed on the historical corpus.

### R03-I6 — final provider-free code acceptance package

Deliver only after separate implementation authority and completion of I0–I5:

- exact-path implementation evidence and file hashes;
- focused and full regression results;
- zero-call manifest;
- independent-review handoff;
- explicit `FIXTURE_NO_GO`, `FRAME_NO_GO`, `GATE_EXECUTION_NO_GO`, `T3_NO_GO`, `PROVIDER_NO_GO`, and `LIVE_NO_GO` status.

Implementation acceptance cannot silently promote any no-go state.

## 7. Frozen split topology

| Segment | Sessions/dates |
|---|---|
| development | 2016-01-04 through 2020-12-23, 1,254 sessions |
| purge 1 | 2020-12-24, 2020-12-28 through 2020-12-31, 5 sessions |
| calibration | 2021-01-04 through 2022-12-22, 498 sessions |
| purge 2 | 2022-12-23, 2022-12-27 through 2022-12-30, 5 sessions |
| procedural OOS | 2023-01-03 through 2025-12-23, 747 decisions |
| label-only tail | 2025-12-24, 26, 29, 30, 31, 5 sessions |

OOS access is not needed for provider-free code acceptance. Tests must prove that development/calibration operations cannot read OOS rows or hashes beyond the sealed public topology metadata.

## 8. Canonical payload and information equality

The ordered canonical fields are:

`article_id`, `available_at`, `symbols`, `source`, `headline`, `summary`, `content`, `summary_present`, `content_present`, `content_truncated`.

Rules:

- explicit nulls; preserve case and HTML;
- article ordering: `available_at` descending, then `article_id` ascending;
- field priority within an article: headline, summary, body;
- body truncation only at a valid UTF-8 prefix;
- maximum 32,768 bytes/article and 131,072 bytes/ticker-session;
- T2 and any future T3 request must receive byte-identical canonical payload bytes and the same article set;
- canonical hash mismatch is fail closed before scoring or replay.

The implementation may expose counts, byte lengths, presence flags, digests, and rejection reason codes. It may not expose text values or text fragments.

## 9. Tier and action invariants

- T0: sealed price/risk baseline and frozen ridge selection.
- T1: T0 plus frozen FinBERT factor; it is not a substitute for T2.
- T2: the single frozen non-LLM bag-of-words comparator used by both the cheap-text gate and the primary T3 comparator.
- T3: schema/grounding/replay contract only in this provider-free plan; no inference.

All tiers share the same buffered portfolio constructor: enter top/bottom 10, retain through top/bottom 20, score-descending/ticker-ascending ties, equal-weight legs, gross 1 per leg and net 0. Fewer than 20 valid names yields no trade. Base cost is 10 bp/side; 5 and 15 bp/side are required sensitivities; the worst included cell governs.

## 10. Training and temporal safety

- Model selection uses development rolling-origin folds ending 2017, 2018, 2019 and 2020.
- T0 alpha grid is `{0.1, 1, 10, 100}`; choose highest worst-fold net utility, then larger alpha on ties.
- T2 alpha grid and tie rules are frozen in I3.
- Monthly expanding fits use only labels matured by the fit cutoff.
- Same-date preprocessing statistics are derived without future labels; all price/risk predictors stop at t-1.
- Training-frame, feature-frame, label-frame and decision-frame hashes are distinct and domain-labeled.
- Any fit whose maximum source timestamp or label-maturity timestamp exceeds its cutoff fails closed.

## 11. Audit and replay contract

Every future run produces a raw-text-free, append-only event chain with at least:

- plan/input commit and schema hashes;
- source descriptor and aggregate inventory hashes;
- calendar, split, universe and sector-map identities;
- canonical bundle hashes and public retention aggregates;
- tier configs, runtime/library/solver/BLAS identities and fitted-model hashes;
- seed domain, bootstrap/simulation parameters and counter state;
- selection hashes, public utility aggregates, bound certificate identity and gate label;
- previous-event hash and current-event hash.

Replay independently reconstructs public metrics from sealed non-text evidence. Any operation requiring raw text must recompute in place and compare only digests/counts. Evidence serialization is canonical UTF-8 JSON with sorted keys, finite numbers and LF endings.

## 12. Mandatory negative-test matrix

The implementation verifier must execute and report all eight P5 obligations. A test passes only when the mutated path is rejected and no raw text appears in stdout, stderr, exception text, temporary evidence, or repository files.

| ID | Required test | Expected fail-closed behavior |
|---|---|---|
| N1 | `recompute_payload_retention_from_read_only_raw_source` | independent exact-calendar/canonicalization recomputation matches sealed public aggregates; mismatch rejects |
| N2 | `reject_article_byte_cap_perturbation` | any cap other than 32,768 changes identity and is rejected |
| N3 | `reject_ticker_session_byte_cap_perturbation` | any cap other than 131,072 changes identity and is rejected |
| N4 | `reject_article_ordering_perturbation` | ordering deviation fails canonical digest/validation |
| N5 | `reject_early_close_cutoff_perturbation` | fixed-close or late article inclusion fails decision-clock validation |
| N6 | `reject_duplicate_selection_perturbation` | version/tie-rule deviation fails article-set identity |
| N7 | `reject_raw_text_emission` | log/error/evidence/snapshot containing source text is rejected and sanitized |
| N8 | `reject_nonzero_provider_counter` | any provider, local-inference, transport, or network counter above zero fails verification |

Additional required tests cover schema extras, naive datetimes, split overlap, label leakage, T2/T3 payload inequality, T2 identity omissions, nondeterministic ties, seed reuse across domains, invalid G1 certificate direction, solver gap/timeout, audit-chain mutation, and unexpected repository artifacts.

## 13. Independent verifier requirements

The verifier must be provider-free and runnable without the licensed corpus for code-only acceptance. It must:

1. pin the exact intended implementation and evidence paths;
2. validate schemas and public test vectors;
3. run focused R03 tests and relevant R02 regression tests;
4. inspect the Python AST/import graph and repository diff for forbidden capabilities;
5. prove provider/local-inference/network counters are zero;
6. prove no raw corpus payload or extracted frame entered the repository;
7. validate the eight negative-test result objects;
8. validate T2 identity completeness;
9. validate G1 bound-certificate tests without treating a heuristic as an upper bound;
10. validate hash-chain replay and exact status labels;
11. fail if the worktree contains paths outside the separately approved set; and
12. emit one deterministic PASS marker only after every gate passes.

Raw-source retention recomputation is a separate data-access verifier mode. It cannot run during code-only acceptance unless separately authorized. Its output is restricted to public aggregates, hashes, reason codes, elapsed time and zero-call counters.

## 14. Numeric, dependency and portability policy

### 14.1 Numeric representation

- Price-derived realized returns are converted once at the frame-contract boundary to signed e12 fixed-point integers using decimal `ROUND_HALF_EVEN`; overflow and non-finite inputs fail closed.
- Transaction costs, per-decision gross/net utilities, `bound_t`, `U_T0,t`, every paired gate-difference series and `delta_star` use e12 fixed-point. G1 sorting uses the e12 realized-return values, so its certificate and upper-bound proof operate in the same utility space.
- Equal-leg means use the frozen leg size and deterministic `ROUND_HALF_EVEN` back to e12. Both the feasible constructor and relaxed bound use the identical rule.
- Bootstrap inputs remain e12 integers. Resample sums and gate comparisons use exact integer/rational representations wherever possible; presentation decimals are non-normative.
- TF-IDF matrices, normalization, ridge coefficients, raw predictions, Wilson calculations and power-simulation internals use IEEE-754 binary64. NaN and infinities are rejected; negative zero is normalized to positive zero at contract boundaries.
- Every output-bearing float64 identity is the lowercase 16-hex-digit big-endian IEEE-754 bit pattern after negative-zero normalization. Arrays bind dtype, shape, order and normalized byte digest. Human-readable decimal rendering is non-normative and cannot govern equality or a gate.
- No epsilon equality is permitted for sealed identities. Economic values compare as e12 integers; numerical model artifacts compare by normalized binary64 identity.

### 14.2 Dependency and pin portability

- Reuse existing reviewed dependencies where possible. `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1` uses deterministic sorting and adds no solver or package.
- Model identity captures exact runtime and numerical backend as described in I3.
- Every digest field has a mandatory `pin_kind` from I0. At minimum the schema distinguishes `git_blob_sha256`, `normalized_lf_sha256`, `canonical_json_sha256`, `filesystem_sha256`, and `aggregate_inventory_sha256`.
- Tracked-artifact sealing uses Git blob identity or an explicitly normalized LF-byte policy so a fresh clone is verifiable across `core.autocrlf` settings.
- Local licensed-source aggregates remain labeled filesystem or aggregate-inventory hashes and never become Git objects.
- Missing, unknown, or context-incompatible `pin_kind` values are verifier failures. Pin-kind enforcement is an I0 contract and test obligation, not a later reseal cleanup.

## 15. Planned authorization ladder

Nothing below is approved by this document. Each transition requires explicit user authority after the previous evidence is reviewed.

1. `PLAN_REVIEWED`: independent review accepts this plan, especially I4.
2. `CODE_ONLY_AUTHORIZED`: create R03 modules/tests/verifier using synthetic text only.
3. `CODE_ONLY_ACCEPTED`: code, tests and zero-call evidence independently accepted.
4. `READ_ONLY_DATA_CHECK_AUTHORIZED`: inspect approved in-place corpus and recompute public census/retention only.
5. `FRAME_MATERIALIZATION_AUTHORIZED`: build sealed local-only frames under an approved ignored artifact root.
6. `G1_G2_G3_EXECUTION_AUTHORIZED`: fit T0/T1/T2 and execute historical gates under frozen identities.
7. `PROSPECTIVE_D_DESIGN_AUTHORIZED`: design option `(d)` using gate results plus resolved model-pin/operations inputs.
8. `LOCAL_T3_INFERENCE_AUTHORIZED`: separate charter, implementation and run decision within the ratified local boundary; no external-provider permission is implied.
9. `EXTERNAL_PROVIDER_AUTHORIZED`: separate future decision requiring the applicable legal/written-permission review before source-text transmission; never implied by any prior state.

## 16. Independent-review questions

The reviewer must answer all questions before recommending code implementation:

1. Does the plan preserve the P5 estimands, historical/exploratory status and option boundaries?
2. Are all R02 I0–I5 bindings and R03 deviations explicit and testable?
3. Is the proposed G1 replacement a valid fail-only upper-bound design, and which exact/certified-relaxation formulation should be frozen?
4. Does the G1 certificate remain valid under transaction costs, buffered retention, five phase books, missing names and no-trade sessions?
5. Are T2 and future T3 information-equal at the byte level?
6. Is the T2 identity sufficient to reproduce numerical outputs and detect runtime/solver/BLAS drift?
7. Do the eight mandatory negative tests meet the P5 reseal obligations?
8. Can code-only verification complete without reading licensed raw text or materializing a frame?
9. Are raw-text non-emission and zero-call claims independently testable?
10. Does any planned step accidentally authorize OOS access, local inference, provider use, or prospective option `(d)` design?

## 17. Plan exit criterion

Independent technical review recorded `ACCEPTED_WITH_NONBLOCKING_FINDINGS`, selected `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1`, and supplied the three reseal deltas now incorporated in this document. The planning state is therefore `REVIEW_ACCEPTED_RESEALED_IMPLEMENTATION_STILL_NO_GO`. Advancing to `CODE_ONLY_AUTHORIZED` still requires explicit user approval after the resealed hashes are verified.
