# R03 news-reasoning provider-free CODE_ONLY implementation — independent review handoff

Status: `READY_FOR_INDEPENDENT_TECHNICAL_RE_REVIEW`

Phase: `R03`

Authority: `CODE_ONLY_AUTHORIZED`; every later ladder state remains no-go.

## 1. Exact review set

Base commit: `6da16688b3da581d1a919d7c75e285827ed10e85`

Accepted plan SHA-256: `324645be4e387a1706c5d40c5d188c4c01288163d72871700501475c745aa60d`

| Artifact | SHA-256 | Pin kind |
|---|---|---|
| `docs/r03-news-reasoning-provider-free-implementation-evidence.json` | `9f21b035997e3bcddd66c8718b4eb9c05a3bb8b64e0a6e4a8941839ebc071b18` | `filesystem_sha256` |
| `docs/r03-news-reasoning-provider-free-implementation.md` | `27bde97c85dcc2c4ae7a4c72ce0985a001505b7efabbc92ea4f8fcb1405e33fa` | `filesystem_sha256` |
| `scripts/r03_news_reasoning_implementation_verify.py` | `7b1b0d0851b22715f68050e5f41f7932670fb4754d33c0d13d8d1221cd652ff1` | `filesystem_sha256` |
| `docs/r03-news-reasoning-provider-free-implementation-zero-call-manifest.json` | `fa51f68b2f9223364e7ba77cd2a93b010cc665e5bf324e2dabc7b51397d162d1` | `filesystem_sha256` |

The canonical self-hash inside the evidence object is `f56b558f7f4c02b706fbf97e6aa61065d3ff9559491a272e626a6b2e6f49f050`.

The handoff remains outside its own pin set; report its final filesystem SHA-256 as the review-session anchor.

## 2. Intended path census

The worktree should contain exactly 22 untracked intended paths and no staged path:

- 9 package files: `v2/research/news_reasoning/__init__.py` plus the eight plan modules;
- 8 synthetic test files: `tests/test_r03_*.py` listed in the evidence;
- 1 verifier: `scripts/r03_news_reasoning_implementation_verify.py`;
- 4 implementation artifacts: narrative, evidence, zero-call manifest, and this handoff.

No dependency or lock file belongs in the delta.

## 3. Delivered behavior by stage

### I0

- strict frozen Pydantic contracts and generated schemas;
- nine-state authority lattice;
- e12 versus normalized binary64 identity boundary;
- mandatory pin-kind contract;
- fail-closed timestamp, split, hash, model-ID, gate, audit and zero-counter validation.

### I1

- permit-before-open raw-source boundary;
- exact portable corpus aggregate algorithm and frozen public anchors;
- canonical availability, eligibility, duplicate, ordering, UTF-8/NFC/LF, null and byte-cap rules;
- T2/T3 byte identity;
- strict provider-free T3 response and grounding validation;
- public retention aggregates and raw-text evidence rejection.

### I2

- early-close-aware decision clock;
- exact split topology, purges and h=5 phase books;
- feature/label/OOS guards;
- sector-relative h=5 e12 outcome;
- common buffered long-short book and transaction costs.

### I3

- T0 preprocessing and deterministic alpha selection;
- T1 frozen-sentiment join;
- frozen T2 component configuration and complete runtime/solver/BLAS identity;
- separate-authority T2 fitting adapter that fails before sklearn import under current authority.

### I4

- only `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1`;
- deterministic top/bottom-10 zero-cost time-decoupled certificate;
- replay, forced no-trade, upper-bound direction and bootstrap label mechanics;
- greedy feasible path restricted to diagnostic looseness;
- no MIP/DP or solver dependency.

### I5

- G2 pause/continue bootstrap;
- exact six-cell G3 grid, planned n=747, Wilson-lower rule and domain-separated PCG64;
- hash-chained raw-text-free audit/replay;
- zero-call and forbidden-capability verification;
- all eight mandatory negative tests by exact ID.

## 4. Reproduced results before handoff

- R03 focused: 49 passed, exit 0.
- R02 accepted API regression: 27 passed, exit 0.
- Full R02 overlay regression: 433 passed in 547.43 seconds, exit 0.
- Black/isort/repository-compatible flake8: exit 0/0/0.
- Evidence model validation and canonical self-hash: pass.
- Zero-call manifest JSON and counters/authority flags: pass; all zero/false.

The independent verifier reruns the 51 focused tests and 27 R02 API tests, checks the recorded 433-test full regression result, recomputes every implementation/test/verifier hash, scans AST imports and repository raw-artifact names, validates exact negative-test coverage, and enforces the 22-path pre-commit set.

Expected PASS marker:

`PASS_R03_NEWS_REASONING_PROVIDER_FREE_CODE_ONLY negative_tests=8 focused_tests=51 r02_api_tests=27 full_overlay_tests=433 provider_calls=0 local_inference_calls=0 raw_source_opens=0 research_gate_executions=0`

## 5. Important dependency boundary

The environment and lock do not contain scikit-learn. The user explicitly prohibited new dependencies. The implementation therefore freezes the sklearn component IDs and full future model identity, provides a delayed fit adapter, and rejects the fit path under current authority before importing sklearn. No model fitting occurred.

The reviewer must explicitly decide whether this is the correct code-only fail-closed implementation or a blocking completeness finding. Adding scikit-learn, executing the adapter, or weakening the guard is outside review authority.

## 6. Mandatory independent checks

1. Recompute the four §1 artifact hashes and all evidence source/test hashes.
2. Validate the evidence canonical self-hash and all pin-kind key coverage.
3. Confirm the worktree contains exactly the 22 intended untracked paths, no staged path and no dependency change.
4. Run the verifier without any raw-source or network access.
5. Confirm all eight negative-test IDs exactly match the P5 obligation set.
6. Confirm `READ_ONLY_DATA_CHECK_AUTHORIZED` is required before source traversal or callback execution.
7. Confirm no raw article field can enter audit/evidence/error output and no raw corpus artifact exists in Git scope.
8. Confirm canonical field order, availability, duplicate tie, caps, truncation and T2/T3 parity.
9. Confirm early-close timing, purges, phase books, t-1/label/OOS guards, common action and costs.
10. Confirm T0/T1/T2 configs and the model identity include runtime, libraries, components, solver parameters and BLAS/LAPACK.
11. Confirm the T2 fitting guard rejects current authority before attempting sklearn import or fit.
12. Re-prove G1's upper-bound direction and replay certificate; ensure the exact/MIP branch is absent.
13. Confirm G1 non-stop and G2 pause semantics do not become T3 evidence.
14. Confirm G3 uses all six cells and Wilson lower power rather than point power.
15. Confirm implementation modules import no provider, network, subprocess, model-download or local-inference stack.
16. Confirm synthetic gate unit calls are not mislabeled as historical research executions.

## 7. Review questions

1. Is I0–I5 complete enough for `CODE_ONLY_ACCEPTED`, with every data/inference state still no-go?
2. Is the generic decoder/callback boundary appropriate before authorized inspection of the real raw-page schema?
3. Does canonical payload construction preserve the plan's field-priority and information-equality contract under both byte caps?
4. Is e12/binary64 conversion and identity handling sufficient for replay?
5. Is the absent-scikit delayed adapter the only correct outcome under the no-new-dependency instruction?
6. Does the G1 certificate exactly implement `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1` and nothing tighter or weaker?
7. Is G3's provider-free simulation implementation faithful to the sealed proxy grid?
8. Are the negative tests strong enough, especially permit-before-callback and raw-text non-emission?
9. Does the verifier independently test rather than trust all material claims?
10. Does any code path accidentally authorize or access source data, frames, fitting, gates, OOS, inference, network, commit or push?

## 8. Expected review record

Return one verdict:

- `ACCEPTED`
- `ACCEPTED_WITH_NONBLOCKING_FINDINGS`
- `REVISE_AND_REVIEW`
- `BLOCKED`

For each finding provide severity, exact file/line or section, reproducible evidence, and replacement language or code requirement. Record independently recomputed hashes, path census, test counts, static-boundary result and zero-action counters. State explicitly that organizational independence is not established if the reviewer shares the same research lineage.

Review acceptance authorizes no data check, frame, fitting, gate, OOS, inference, provider, dependency, commit or push action. `READ_ONLY_DATA_CHECK_AUTHORIZED` remains a separate user decision after code-only acceptance.

## 9. Independent technical review record (2026-07-19)

- Reviewer: Claude (Fable 5), same-session lineage — technical verification
  only; organizational independence NOT established.
- Independently reproduced: sealed hashes 3/3; evidence pins (9 source + 8
  test + verifier, all `filesystem_sha256` pin_kind) — 0 mismatches;
  manifest→evidence cross-pin; verifier **exit 0** with the exact PASS marker;
  focused suite **49/49**; full overlay regression **433 passed in 484.31s**;
  `git diff poetry.lock pyproject.toml` empty (no dependency change); exactly
  22 new untracked paths; forbidden-import, nondeterminism, and raw-source-
  path scans — 0 hits; sklearn confined to a lazy in-function import behind
  `R03DependencyUnavailable` with scikit-learn absent from the environment.
- Deep code review completed on `r03_contracts.py`, `r03_payload.py`,
  `r03_frames.py`, `r03_headroom.py`, `r03_power.py`, `r03_source.py`:
  - G1 exactly implements `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1` —
    sort-certificate with valid-set/order digests, full-recompute replay,
    `upper ≤ delta_star` boundary, `G1_INVALID_NO_DECISION` on empty input,
    greedy feasible bracket as diagnostic only. Nothing tighter or weaker.
  - G2 pause boundary unified at `≤ delta_star`; G3 is the sealed six-cell
    grid (SD ×{1,1.5,2} × fail {0,.05}), fail-closed draws zeroed, effect
    `delta_star·(1−fail)`, **cell pass governed by the Wilson lower bound**,
    stationary (Politis–Romano) bootstrap with domain-separated PCG64.
  - Contracts: e12/binary64 boundary with normalized `float64_hex` identity;
    T3 score transported as a binary64 hex identity (non-finite rejected at
    decode — NaN cannot enter); complete T2 model identity; `Literal[0]`
    zero-counters; frozen split table matches the independently verified
    session partition; OOS date guard fails closed.
  - Source boundary: permit-gated (authorization literal + permit hash +
    root-identity hash), frozen census anchors byte-exact with the sealed
    aggregate contract, digest-only error paths, raw-text-field emission
    rejector.
- **Verdict: `REVISE_AND_REVIEW`** — three payload-conformance deltas are
  required before reseal; all statistical, gating, and authority machinery is
  conformant as-is.
  1. (MEDIUM) `r03_payload.py:131` `select_latest_versions` keys on
     `(updated_at, input_text_sha256)` only; the sealed rule is **maximum
     `available_at`** first, ties by `(updated_at, input_text_sha256)`.
     Records with `created_at > updated_at` select the wrong version. Fix:
     key `(record.available_at, record.updated_at, record.input_text_sha256)`.
  2. (MEDIUM) Byte caps are enforced against **serialized article/payload
     JSON bytes** (metadata and syntax included); the sealed census and
     preregistration define 32,768/131,072 as **text bytes across
     headline/summary/content**. As written, the stage-4 N1 retention
     recomputation cannot reproduce the sealed 99.06%/97.03% aggregates. Fix:
     enforce caps on the summed UTF-8 byte lengths of the three text fields
     (article) and their per-session sum (frame), leaving serialization
     overhead uncapped, or obtain an explicit user-approved amendment of the
     sealed cap basis.
  3. (LOW) `build_canonical_bundle` continues appending smaller articles
     after a session-level truncation; the sealed rule is that the
     session-truncated article is the final includable one and later articles
     are omitted and counted. Fix: break after the first session-level
     truncation (distinguish it from article-cap truncation).
- Notes (no change required): (a) `parse_t3_response` lacks an R02-style
  `parse_constant` rejection — currently harmless because the response
  contract has no float fields; add for parity when convenient. (b) G3's 80%
  power is the sealed MDE-versus-zero criterion (§6 of the preregistration),
  not the probability of clearing `delta_star` at a true effect of exactly
  `delta_star`; record this interpretation to prevent overreading.
- Zero-action confirmation for this review: raw-source opens 0, inference 0,
  provider/network 0, implementation edits 0, staging/commit/push 0.
- Next order: apply deltas 1–3, rerun focused/full suites and the verifier,
  reseal evidence/manifest, then return for re-review. `CODE_ONLY_ACCEPTED`
  and `READ_ONLY_DATA_CHECK_AUTHORIZED` remain separate user decisions.

## 10. Codex payload-delta reseal for re-review (2026-07-19)

Section 9 is preserved as the original first-review record. This section and the resealed §1 artifact set supersede its requested implementation actions without changing its verdict.

- F1 closed: `select_latest_versions` now selects the maximum `(available_at, updated_at, input_text_sha256)` tuple. A synthetic regression makes the later-available record win even when its `updated_at` is earlier.
- F2 closed: article and ticker-session caps count only canonical headline, summary and content UTF-8 bytes. `R03CanonicalBundle.text_bytes` is capped and replay-checked; `payload_bytes` records the uncapped canonical JSON size. Serialization metadata and syntax no longer consume the text allowance.
- F3 closed: session fitting returns an explicit truncation flag. The first session-truncated article is appended as the final article, and iteration stops before all later articles.
- Optional note closed: T3 JSON parsing now rejects NaN and Infinity through `parse_constant` before contract validation.
- Interpretation recorded: G3's Wilson-lower 80% requirement is the preregistered MDE-versus-zero power criterion, not a claim that an effect exactly equal to `delta_star` clears `delta_star` with 80% probability.

Reseal verification:

- R03 focused: 51/51, exit 0.
- R02 public API: 27/27, exit 0.
- Full R02 overlay: 433/433 in 547.43 seconds, exit 0.
- Black/isort/repository-compatible flake8: exit 0/0/0.
- Zero counters and authority boundaries remain unchanged; raw-source opens, fitting, gate execution, OOS access, inference, provider/network, dependency, staging, commit and push actions are all zero/not performed.

Expected verifier marker:

`PASS_R03_NEWS_REASONING_PROVIDER_FREE_CODE_ONLY negative_tests=8 focused_tests=51 r02_api_tests=27 full_overlay_tests=433 provider_calls=0 local_inference_calls=0 raw_source_opens=0 research_gate_executions=0`

This reseal requests lightweight independent re-review only. It does not grant `CODE_ONLY_ACCEPTED`, `READ_ONLY_DATA_CHECK_AUTHORIZED`, or any later authority state.

## 11. Second technical review record — payload deltas verified (2026-07-19)

- Reviewer: Claude (Fable 5), same-session lineage — technical verification
  only; organizational independence NOT established.
- Recomputed: handoff submission hash (`0958a2ae…`), all four §1 pins, all
  evidence source/test pins, and the evidence canonical self-hash — 0
  mismatches. Worktree: exactly the 22 intended untracked paths, staging 0,
  dependency diff 0.
- All three §9 deltas verified in code:
  1. F1 — `select_latest_versions` now keys on
     `(available_at, updated_at, input_text_sha256)`.
  2. F2 — caps now enforce summed UTF-8 text bytes of
     headline/summary/content per article and per session; the bundle
     carries `text_bytes` separately from serialized `payload_bytes` and
     both replay in `canonical_bundle_bytes`.
  3. F3 — `build_canonical_bundle` breaks after the first session-level
     truncation via an explicit `session_truncated` flag.
  Optional notes also applied: `parse_constant` now rejects NaN/Infinity;
  the G3 MDE-versus-zero interpretation is documented.
- Independently rerun: verifier **exit 0** with the exact 51-test marker;
  `tests/` suite **116 passed**. Full-overlay basis: the R03 payload deltas
  cannot affect the R02 overlay suite (imports flow R03→R02 only); the prior
  two independent 433/433 runs plus the recorded 547.43s run stand.
- §5 dependency-boundary question answered: the absent-scikit delayed
  adapter **is the correct code-only outcome** — adding scikit-learn now
  would be an unauthorized dependency change, fitting belongs to a later
  ladder state, and the required dependency review naturally attaches to
  the frame-and-fit authorization.
- Blocking findings: **0**. Nonblocking: none new.
- Disposition: **`TECHNICAL_RE_REVIEW_PASSED_RECOMMEND_CODE_ONLY_ACCEPTED`**.
  `CODE_ONLY_ACCEPTED`, the 22-path commit/push, and
  `READ_ONLY_DATA_CHECK_AUTHORIZED` remain separate user decisions.
