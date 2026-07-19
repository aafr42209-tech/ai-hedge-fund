# R03 news-reasoning provider-free CODE_ONLY implementation

Status: `CODE_ONLY_IMPLEMENTED_REVIEW_REQUIRED_DATA_AND_INFERENCE_NO_GO`

Plan commit: `6da16688b3da581d1a919d7c75e285827ed10e85`

Accepted plan SHA-256: `324645be4e387a1706c5d40c5d188c4c01288163d72871700501475c745aa60d`

## 1. Outcome

R03-I0 through R03-I5 have been implemented as provider-free code with synthetic text only. The package contains strict contracts, source-access guards, canonical payload construction, calendar/frame/action mechanics, tier configuration and identity, the frozen G1 sorting relaxation, G2/G3 power machinery, raw-text-free audit/replay, and an independent verifier.

This is code-only evidence. No FinGPT file was opened or rescanned. No historical fixture or frame was created. No T0/T1/T2 model was fitted. No research G1/G2/G3 gate was executed. No OOS row was accessed. No local model or provider was invoked. No network or model download occurred.

## 2. Implementation surface

Provider-free package:

- `v2/research/news_reasoning/__init__.py`
- `v2/research/news_reasoning/r03_contracts.py`
- `v2/research/news_reasoning/r03_source.py`
- `v2/research/news_reasoning/r03_payload.py`
- `v2/research/news_reasoning/r03_frames.py`
- `v2/research/news_reasoning/r03_tiers.py`
- `v2/research/news_reasoning/r03_headroom.py`
- `v2/research/news_reasoning/r03_power.py`
- `v2/research/news_reasoning/r03_audit.py`

Synthetic focused tests:

- `tests/test_r03_contracts.py`
- `tests/test_r03_source.py`
- `tests/test_r03_payload.py`
- `tests/test_r03_frames.py`
- `tests/test_r03_tiers.py`
- `tests/test_r03_headroom.py`
- `tests/test_r03_power.py`
- `tests/test_r03_audit.py`

Independent verifier:

- `scripts/r03_news_reasoning_implementation_verify.py`

No fixture, extracted frame, fitted parameter, vocabulary, article payload, provider response, or result table was added to the repository.

## 3. I0 — contracts and authority

Implemented:

- R02 `StrictModel`-based fail-closed schemas for source descriptors, records, bundles, splits, frame identities, tier/model identities, G1 certificates, gate results, T3 contract-only responses, audit and zero counters;
- all nine authorization-ladder states without promoting the current state;
- mandatory pin kinds: Git blob, normalized LF, canonical JSON, filesystem, and aggregate inventory;
- e12 economic values and normalized binary64 bit identities;
- schema generation and metaschema validation;
- extra-field, naive-time, non-finite, negative-zero, hash, temporal and authority validation;
- static provider/network/process/model-download import rejection for implementation modules.

Economic contract quantities use e12. Model matrices, coefficients and raw predictions may use finite binary64. Normative float identity is the normalized 16-hex-digit big-endian IEEE-754 representation; epsilon identity is not permitted.

## 4. I1 — source boundary and canonical payload

The source module contains the frozen public corpus hashes/counts and exact portable aggregate algorithm:

`sha256(sorted_utf8(relative_path + NUL + decimal_size + NUL + file_sha256 + LF))`.

Every raw-source entry point validates a separately issued `READ_ONLY_DATA_CHECK_AUTHORIZED` permit and root identity before filesystem traversal or callback execution. Current tests prove the missing-permit path rejects before a synthetic callback can run.

Canonical payload behavior includes:

- timezone-aware `available_at = max(created_at, updated_at)`;
- `(decision - 72h, decision]` window;
- maximum available-at, then updated-at, then input-text-SHA duplicate rule;
- headline and 1–5-symbol eligibility;
- UTF-8, NFC, LF and no NUL;
- fixed article field order and explicit nulls;
- article ordering by availability descending then article ID ascending;
- 32,768-byte article and 131,072-byte ticker-session caps measured only across headline, summary and content UTF-8 bytes; canonical JSON syntax and metadata overhead are uncapped;
- headline then summary preservation, followed by the largest valid UTF-8 content prefix;
- session-level truncation makes that article final and omits every later article;
- exact T2/T3 payload digest parity;
- strict T3 response parsing, duplicate-key and non-finite-constant rejection, RFC6901 article grounding and ticker equality;
- public retention/count/hash outputs only.

Raw-text field names are rejected from audit/evidence structures.

## 5. I2 — calendar, frame and action mechanics

Implemented:

- actual-close-minus-30-minute decision clock capped at 15:30 America/New_York, including early closes;
- the sealed 2016–2025 development/purge/calibration/OOS/label-tail topology and five h=5 phase books;
- purge length and split nonoverlap validation;
- feature, label-maturity and OOS access guards;
- split-adjusted, sector-relative h=5 outcome conversion to e12;
- top/bottom-10, retain-through-20 buffered books with deterministic ticker ties;
- fewer-than-20 no-trade behavior;
- equal-weight long/short utility, turnover and 5/10/15 bp-per-side costs.

No historical frame builder was run and no frame artifact exists.

## 6. I3 — T0/T1/T2 code surface and identity

Implemented:

- frozen T0 features, imputation, 1/99 clipping, sector demeaning, z-scoring, folds and alpha tie rule;
- deterministic same-date T0 cross-sectional preprocessing;
- T1 FinBERT-factor and availability-flag join with missing score zero;
- single frozen T2 HashingVectorizer/TF-IDF/LSQR-ridge configuration;
- worst-fold alpha selection and exact T2/T3 payload parity;
- complete T2 identity fields covering Python, NumPy, SciPy, scikit-learn, component IDs, LSQR parameters, BLAS/LAPACK, schema/payload/training/split/config hashes, clip bits and parameter digest;
- a future fitting adapter that checks a separate frame-and-fit authorization before importing sklearn or fitting.

The existing environment and lock contain no scikit-learn. The user prohibited new dependencies, so none was added. `installed_t2_runtime()` and the future fit adapter fail closed in the current environment. Tests exercise configuration, preprocessing, identity and pre-import authorization rejection only; they do not fit a model. A later dependency and fitting decision remains separate authority.

## 7. I4 — G1 frozen bound

Only `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1` is implemented:

- use the exact T0-valid names per calibration decision;
- fewer than 20 names yields `bound_t = 0`;
- otherwise sort e12 realized returns deterministically and select top/bottom 10;
- remove transaction costs and temporal/buffer coupling;
- certify valid-name digest, sorted-order digest and both legs;
- replay by re-sorting and byte-identical certificate reproduction;
- use the sealed stationary bootstrap and conservative upper-95%-at-or-below-delta stop rule;
- map every empty/invalid/certificate mismatch path to no decision;
- retain the full-cost buffered greedy path only as a diagnostic lower bracket.

No solver or dependency was added. The exact coupled MIP/DP branch remains deselected. Synthetic tests establish deterministic certificate replay, forced no-trade, feasible-path domination, boundary labels and diagnostic-bracket direction. No historical G1 result was produced.

## 8. I5 — G2/G3, audit and verifier

Implemented:

- G2 paired stationary-bootstrap pause/continue labels;
- exact six-cell G3 grid over SD multipliers 1/1.5/2 and fail rates 0/5%, planned n=747 and Wilson-lower 80% MDE-versus-zero rule (not probability of clearing delta-star when the true effect equals delta-star);
- domain-separated PCG64 simulation;
- append-only canonical hash-chained audit and replay;
- zero-only provider, local-inference, network, model-download, raw-source, materialization, gate and OOS counters;
- exact mandatory negative-test ID coverage;
- static forbidden-capability and raw-source-artifact scans;
- pre-commit exact-path and future post-commit exact-path modes.

Synthetic unit calls to gate functions are algorithm tests, not research gate executions. The zero research-gate counter remains accurate.

## 9. Mandatory negative tests

All eight P5 obligations are implemented under their exact IDs:

1. `recompute_payload_retention_from_read_only_raw_source`
2. `reject_article_byte_cap_perturbation`
3. `reject_ticker_session_byte_cap_perturbation`
4. `reject_article_ordering_perturbation`
5. `reject_early_close_cutoff_perturbation`
6. `reject_duplicate_selection_perturbation`
7. `reject_raw_text_emission`
8. `reject_nonzero_provider_counter`

The first test is code-only: it proves authorization rejection precedes callback or source access. It does not claim the separately authorized 2.67 GB retention recomputation has run.

## 10. Verification results

- R03 synthetic focused suite: 51 passed, exit 0.
- Accepted R02 public-API regression: 27 passed, exit 0.
- Full R02 overlay regression: 433 passed in 547.43 seconds, exit 0.
- Black check: exit 0.
- isort check: exit 0.
- flake8 with repository-compatible `E501,E203,W503` ignores: exit 0.
- Provider calls: 0.
- Local inference calls: 0.
- Network attempts/model downloads: 0/0.
- Raw-source opens: 0.
- Fixture/frame materializations: 0/0.
- Research gate executions/OOS accesses: 0/0.

The focused and full test commands, exact source/test/verifier hashes, pin kinds, stage-to-test mapping and canonical evidence self-hash are recorded in `docs/r03-news-reasoning-provider-free-implementation-evidence.json`.

The first independent review's three payload findings are closed in this reseal:

- F1: duplicate selection now orders by `(available_at, updated_at, input_text_sha256)`;
- F2: article/session caps now count only canonical headline, summary and content UTF-8 bytes, while `payload_bytes` continues to record the uncapped canonical serialization size;
- F3: the first session-truncated article is final and every later article is omitted.

Regression tests separately lock F1 and F3, while the cap test locks exact text-byte accounting and proves serialization overhead is excluded. The optional JSON `parse_constant` parity guard was also added; NaN and Infinity tokens now fail closed.

## 11. Residual no-go states

This implementation does not authorize or establish:

- `CODE_ONLY_ACCEPTED`;
- `READ_ONLY_DATA_CHECK_AUTHORIZED`;
- licensed-source census or retention recomputation;
- fixture or frame materialization;
- scikit-learn dependency installation;
- T0/T1/T2 fitting;
- G1/G2/G3 research execution;
- procedural OOS access;
- local inference or model download;
- provider or network transport;
- prospective option `(d)` design;
- commit or push;
- organizational independence.

The next step is independent technical review of this code-only set. Even an accepted review does not grant read-only data-check authority.
