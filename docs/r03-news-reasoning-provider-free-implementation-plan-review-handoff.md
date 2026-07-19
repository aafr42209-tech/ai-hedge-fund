# R03 news-reasoning provider-free implementation plan — independent review handoff

Status: `ACCEPTED_RESEALED_IMPLEMENTATION_STILL_NO_GO`

Phase: `R03`

Review target: historical option `(c)` provider-free implementation plan only.

## 1. Exact review set

| Artifact | SHA-256 | Role |
|---|---|---|
| `docs/r03-news-reasoning-provider-free-implementation-plan.md` | `324645be4e387a1706c5d40c5d188c4c01288163d72871700501475c745aa60d` | review-accepted resealed plan |
| `docs/r03-news-reasoning-provider-free-implementation-plan-zero-call-manifest.json` | `a6468bdbad7276d97c94d56278aeb79304a1c15ad7eec65ec160ec3109f7e9f6` | resealed authority/counter record |

Base commit: `52bf68805cb42f5b06c39de09cc6201e6e093834`

Branch: `codex/llm-overlay-research-01`

These two artifacts are uncommitted resealed candidates. Section 8 preserves the independent review record and original submission anchor. The handoff file remains outside its own pin set; its final filesystem SHA-256 is the reseal-session anchor.

## 2. What changed and why

R02 I0–I5 is now sealed, reviewed, accepted and promoted. The next ordered step is therefore an R03 code-implementation plan, not prospective option `(d)` design.

The plan:

- binds R03 to accepted R02 contracts, canonicalization, grounding, deterministic comparator, selection/replay, split/seed/power, audit and zero-call patterns;
- defines R03-I0 through I6 without authorizing implementation or data access;
- preserves T0–T3 information equality and the primary future estimand `T3 - T2`;
- freezes the P5 census, canonical payload, calendar/split, T0/T1/T2, action, cost, seed and gate obligations;
- carries all eight P5 negative-test obligations into the future verifier;
- requires a complete T2 model identity covering runtime, libraries, component implementations, solver and BLAS/LAPACK;
- separates code-only acceptance from raw-source checks, frame materialization, gate execution and T3 execution;
- prefers local inference as the later historical T3 candidate while leaving all inference outside current authority.

## 3. Scope and authority

The user has already ratified:

- R03 phase ID;
- read-only in-place reuse of the FinGPT news corpus;
- local analysis, aggregation, audit, T0/T1/T2 training and provider-free G1–G3 work within the approved local research boundary;
- prospective option `(d)` as the eventual PIT direction, with design deferred;
- options `(a)` and `(b)` frozen and historical option `(c)` retained as exploratory.

No new legal inquiry is required for that ratified local/provider-free path. A separate rights/legal decision is needed only if a future design transmits licensed source text to an external provider, redistributes it, or departs from the approved local personal/non-commercial boundary. A separately approved local inference path does not imply external transmission.

This handoff authorizes none of the following:

- implementation-file creation or modification;
- dependency or solver changes;
- opening or rescanning raw FinGPT article files;
- fixture or frame materialization;
- fitting T0, T1 or T2;
- G1, G2 or G3 execution;
- opening procedural OOS;
- local-model inference or model download;
- external provider/network use;
- commit or push.

## 4. Primary blocking review point — G1

The synthetic R02 headroom gate had a computable candidate-level oracle. Historical news has no equivalent oracle. The plan therefore introduces an R03 calibration-only `OutcomeBoundCase` with a replayable `BoundCertificate` and admits only:

1. an exact feasible perfect-foresight optimizer with independently replayable optimality certification; or
2. a mathematically proved relaxation that upper-bounds every feasible realized net-utility path.

An outcome-ranked or otherwise heuristic feasible portfolio is only a lower bound on the optimum and cannot govern the fail-only G1 stop. Timeout, numerical ambiguity, unacceptable optimality gap or certificate failure yields `G1_INVALID_NO_DECISION`.

The reviewer must not accept the plan for code implementation until one concrete formulation is chosen and frozen with:

- the objective and comparison to T0;
- eligible-set, long/short, cardinality, gross/net, buffer, phase-book, no-trade, liquidity, missingness and transaction-cost treatment;
- proof or certificate semantics establishing the upper-bound direction;
- numerical tolerances and failure states;
- solver/dependency and model identity requirements;
- synthetic constructive cases with known optima; and
- replay tests that reject invalid or downgraded certificates.

If neither exact certification nor a useful proved relaxation is practical, the correct finding is to block G1 implementation and require a preregistration amendment. The reviewer must not substitute a convenient heuristic.

## 5. Required independent checks

### 5.1 Artifact and lineage

- Recompute the two pinned SHA-256 values.
- Confirm base commit and branch.
- Confirm all sealed P5 and accepted R02 input hashes listed in the plan and manifest.
- Confirm the working-tree delta contains only the three planning artifacts after this handoff is created.

### 5.2 Research design

- Confirm historical `(c)` is always labeled exploratory.
- Confirm prospective `(d)` is ratified but not designed or authorized here.
- Confirm T2 is the same cheap-text model used by G2 and the future primary T3 comparator.
- Confirm `T3 - T2` remains the primary future estimand and T3 has no implementation/transport in this plan.
- Confirm gate pass and pause/stop semantics do not overclaim T3 capability.

### 5.3 Data and time safety

- Confirm canonical field order, byte caps, sorting, truncation, duplicate rule and T2/T3 byte equality match P5.
- Confirm actual-close/early-close decision timing, 72-hour window, availability rule and t-1 price/risk cutoff.
- Confirm development/calibration/purge/OOS/label-tail topology and `block >= h`.
- Confirm no code-only step needs licensed raw text or materialized historical frames.
- Confirm no raw source text can enter logs, errors, snapshots, evidence or Git.

### 5.4 Models, statistics and action

- Confirm T0/T1/T2 specifications, tuning grids, matured-label updates and deterministic ties.
- Confirm the T2 identity detects Python/NumPy/SciPy/scikit-learn, component, solver and BLAS/LAPACK drift.
- Confirm the buffered long-short constructor, no-trade rule and cost sensitivities.
- Confirm G1/G2 boundary uses the conservative `upper one-sided 95% <= delta_star` rule.
- Confirm G3's sealed simulation grid governs and analytical MDE is diagnostic only.
- Confirm seed domain separation, PCG64, block length 10 and 10,000 resamples.

### 5.5 Verification and authority

- Confirm all eight mandatory negative tests appear by exact ID and have fail-closed semantics.
- Confirm the verifier has a corpus-free code-only mode and a separately authorized raw-source mode.
- Confirm static forbidden-capability checks cover provider SDKs, network, credentials, subprocess/model download and raw-text output.
- Confirm the authorization ladder cannot promote code acceptance into data, gate, inference, provider or LIVE authority.
- Confirm tracked hashes use an explicit Git-blob or normalized-byte policy rather than an unlabeled CRLF-sensitive pin.

## 6. Questions requiring explicit answers

1. `ACCEPT / REVISE / BLOCK`: Is the overall R03-I0–I6 decomposition implementation-ready after review deltas?
2. Which concrete G1 upper-bound formulation is accepted, and why is its bound direction valid?
3. Is the accepted G1 formulation computationally practical enough to be useful rather than merely valid but vacuous?
4. Which solver/dependency, certificate type, optimality tolerance and failure label must be frozen?
5. Are the R02 bindings narrow enough to prevent silent logic forks?
6. Are the canonical payload and T2/T3 byte-equality requirements executable and independently verifiable?
7. Is the T2 identity complete for output reproducibility?
8. Do the eight negative tests fully discharge P5's reseal obligations?
9. Does the local-inference preference preserve the legal/data boundary without implying current run authority?
10. Does any line accidentally reopen option `(d)`, authorize OOS, or generalize a future local-model null to frontier models?

## 7. Expected review output

Record:

- one overall verdict: `ACCEPTED`, `ACCEPTED_WITH_NONBLOCKING_FINDINGS`, `REVISE_AND_REVIEW`, or `BLOCKED`;
- findings ranked `BLOCKING`, `HIGH`, `MEDIUM`, `LOW`, or `NOTE`;
- direct section references and exact replacement language for every required change;
- the chosen G1 contract or an explicit statement that no acceptable contract was found;
- independently recomputed hashes and worktree path census;
- confirmation that raw-source opens, inference calls, provider calls, network attempts, implementation changes, staging, commits and pushes all remained zero.

Review acceptance does not authorize implementation. After accepted deltas are applied and the planning set is re-sealed, the user must separately authorize any R03 code work.

## 8. Independent technical review record (2026-07-19)

- Reviewer: Claude (Fable 5), same-session lineage — technical verification
  only; organizational independence NOT established.
- Recomputed: both §1 pins, this handoff's own submission hash (`523b3495…`),
  and **all 14 sealed-input pins in plan §2 — 0 mismatches**. Base commit
  `52bf688` and branch confirmed. Worktree delta = exactly the three planning
  artifacts. The eight P5 negative-test obligations were programmatically
  matched against the P5 zero-call manifest — exact ID coverage. Raw-source
  opens, inference calls, provider calls, network attempts, implementation
  changes, staging, commits, pushes during this review: all zero.

### 8.1 Verdict

**`ACCEPTED_WITH_NONBLOCKING_FINDINGS`** — with the G1 contract in §8.2 chosen
and to be frozen verbatim into the plan at reseal. No blocking finding remains
once §8.2 is adopted.

### 8.2 Chosen G1 contract (answers §6-2/3/4) — freeze this formulation

**Name:** `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1`.

**Objective.** For each calibration decision `t` (per h=5 phase book), over the
exact T0-valid eligible set at `t`:

- if fewer than 20 valid names: `bound_t = 0` (forced no-trade);
- else `bound_t` = mean sector-relative h=5 realized return of the top-10
  names minus the mean of the bottom-10 names, names sorted by realized
  return descending with ties broken ticker-ascending (equal leg weights,
  gross 1/leg, net 0 — identical book shape to the shared constructor).

`U_bound = Σ_t bound_t` aggregated across the five phase books exactly as the
tier utilities are aggregated. `D_G1,t = bound_t − U_T0,t` is the paired
series; the sealed stationary block bootstrap (block 10, 10,000 resamples,
domain-separated PCG64) yields the one-sided 95% upper limit; upper limit
`<= delta_star` → `STOP_NO_ECONOMIC_HEADROOM`.

**Upper-bound proof (direction).** For any feasible policy π with book
`B_t^π` (or no-trade): realized net utility
`U(π) = Σ_t spread_t(B_t^π)·1{trade} − c·turnover_t ≤ Σ_t max_B spread_t(B)
= U_bound`, because (i) transaction costs are nonnegative and are dropped
(objective can only increase); (ii) the per-period maximum is taken over a
feasible-book superset that contains `B_t^π`, and `spread_t ≥ 0` whenever 20+
valid names exist (sorted top-10 mean ≥ bottom-10 mean) so the no-trade
branch (0) is also dominated. Both relaxations — cost removal and temporal
decoupling (turnover-cost linkage, buffer retention) — are monotone
objective-increasing. The bound therefore dominates every feasible realized
net-utility path, including never-trading.

**Certificate.** Exact optimality of the *relaxed* per-period objective is
established by selection-of-k-largest: the certificate per period is the
valid-name set digest, the sorted-return order digest, and the two selected
legs. Replay re-sorts and must reproduce the legs byte-identically. **No new
solver or dependency is required** (deterministic sort only), hence no
optimality-gap or timeout tolerance exists; the only failure states are
NaN/missing-return leakage into the valid set, digest mismatch, or leg
non-reproduction — each yields `G1_INVALID_NO_DECISION`.

**Looseness disclosure (mandatory in the G1 report).** Report alongside the
bound a *diagnostic-only* feasible lower bracket: the greedy clairvoyant path
(per-period argmax with full transaction costs, buffered constructor). The
interval [greedy feasible, U_bound] quantifies relaxation looseness. The
lower bracket cannot govern G1.

**Practicality assessment (answers §6-3).** The bound is valid and cheap but
**expected to be loose** — per-period perfect-foresight top/bottom-10 spread
on ~100 names at h=5 will typically exceed `delta_star + U_T0` by orders of
magnitude, so G1 will likely never stop the program. This is acceptable for a
fail-only ceiling and must be documented in the preregistration so a non-stop
G1 is read as "inert valve," never as supporting evidence. Do **not** invest
in a MIP/DP formulation of the coupled problem to tighten it: the exact
coupled optimum has no practical certificate at this state-space size, a
solver dependency would violate §14 parsimony, and the binding provider-free
filters are G2/G3 by design. The plan's "exact feasible perfect-foresight
optimizer" branch should be recorded as **considered and deselected** to
prevent future scope creep.

### 8.3 Answers to remaining §6 questions

1. **ACCEPT** — the I0–I6 decomposition is implementation-ready once §8.2 is
   frozen; the authorization ladder (§15) is well-formed and cannot silently
   promote.
5. R02 bindings are narrow and testable: the adapter declaration rule
   (upstream symbol + source hash + equivalence/deviation test, undeclared
   copy = verifier failure) prevents silent forks.
6. Byte-equality is executable and independently verifiable via canonical
   bytes + digest comparison; the payload contract matches P5 exactly
   (fields, order, caps, truncation, tie rule).
7. T2 identity is complete for output reproducibility and drift detection —
   it meets and exceeds the P5 `t2_model_id_implementation_requirements`.
8. The eight negative tests discharge the P5 reseal obligations — exact-ID
   match verified programmatically.
9. The local-inference preference preserves the legal/data boundary: text
   stays on-workstation, run authority is explicitly outside this plan
   (ladder states 8/9), and the local-model-null non-generalization caveat is
   stated in §3.2.
10. No line reopens option `(d)`, authorizes OOS access, or generalizes a
    local-model null to frontier providers.

### 8.4 Nonblocking findings

1. (MEDIUM) **Numeric-representation policy is unstated.** R02 used integer
   e12 fixed-point throughout; R03 tiers necessarily produce float64
   (ridge/TF-IDF). At I0, freeze an explicit policy: which quantities are
   integer fixed-point (utilities, costs, bound values — recommended e12, as
   in R02) versus float64 with a canonical serialization/rounding rule at the
   contract boundary. Replay byte-identity (§11) is unverifiable without it.
2. (LOW) Plan §6-I4's exact-optimizer branch: record as considered/deselected
   per §8.2 rather than leaving both branches open at reseal.
3. (NOTE) Plan §14's pin-labeling requirement (Git-blob vs normalized vs
   filesystem) resolves the known CRLF portability finding from the R02 line —
   carry it into the R03 verifier from I0, not as an afterthought.

### 8.5 Boundary confirmation

This review acceptance authorizes nothing beyond recording itself: no
implementation-file creation, dependency change, raw-source open, fixture or
frame materialization, model fitting, gate execution, OOS access, local
inference, provider or network use, commit, or push. Next order: apply §8.2
and §8.4 deltas, re-seal the planning set, then obtain separate user
authorization for `CODE_ONLY_AUTHORIZED`.

## 9. Codex reseal resolution

Date: 2026-07-19

Section 8 remains the original independent technical review record. The following accepted deltas have now been applied; this section supersedes earlier pre-review instructions only where they conflict with the frozen outcome.

### 9.1 G1 contract frozen

Plan R03-I4 now freezes `G1_DECOUPLED_ZERO_COST_SORT_RELAXATION_V1` exactly as selected in §8.2:

- calibration-only, T0-valid names and h=5 phase books;
- fewer than 20 names forces `bound_t = 0`;
- otherwise deterministic realized-return top/bottom-10 spread, zero transaction costs and no temporal/buffer coupling;
- e12 paired series `D_G1,t = bound_t - U_T0,t` with the sealed stationary bootstrap;
- valid-name, sorted-order and selected-leg certificate replay;
- no new solver, dependency, gap or timeout tolerance;
- every invalid certificate state maps to `G1_INVALID_NO_DECISION`;
- greedy full-cost/buffered path retained only as a diagnostic lower looseness bracket;
- a G1 non-stop explicitly labeled an expected inert-valve outcome, not T3 evidence.

The exact coupled MIP/DP branch is recorded as considered and deselected. Reintroduction requires a separately reviewed amendment.

### 9.2 Nonblocking findings closed

1. Numeric representation: plan §14.1 now freezes e12 for realized returns at the frame boundary, costs, utilities, bounds, paired gate inputs and `delta_star`; model/numerical internals use finite normalized IEEE-754 binary64. Contract float identity uses a lowercase 16-hex-digit big-endian bit representation, arrays bind shape/dtype/order/digest, and no epsilon identity is allowed.
2. Exact optimizer: the formerly open branch is closed as described in §9.1.
3. Pin labeling: plan I0 and §14.2 require `pin_kind` from the first schema version. The resealed manifest labels its plan and all 14 inherited inputs as `filesystem_sha256`; future tracked implementation artifacts must use the applicable Git-blob, normalized-LF or canonical-JSON kind.

### 9.3 Resealed artifacts

| Artifact | SHA-256 | Pin kind |
|---|---|---|
| `docs/r03-news-reasoning-provider-free-implementation-plan.md` | `324645be4e387a1706c5d40c5d188c4c01288163d72871700501475c745aa60d` | `filesystem_sha256` |
| `docs/r03-news-reasoning-provider-free-implementation-plan-zero-call-manifest.json` | `a6468bdbad7276d97c94d56278aeb79304a1c15ad7eec65ec160ec3109f7e9f6` | `filesystem_sha256` |

The manifest remains valid JSON, its 14 sealed-input hash keys exactly match its 14 pin-kind keys, all counters remain zero and all authority flags remain false. The final handoff hash is intentionally reported outside this file to avoid self-reference.

### 9.4 Final state and next authority

Planning state: `REVIEW_ACCEPTED_RESEALED_IMPLEMENTATION_STILL_NO_GO`.

No implementation, dependency change, raw-source open, fixture/frame materialization, model fit, gate execution, OOS access, local inference, provider/network call, staging, commit, or push occurred during reseal. The next possible transition is `CODE_ONLY_AUTHORIZED`, which still requires explicit user approval and remains restricted to synthetic text with no raw-source access.
