# R02 overlay v2 I0–I5 provider-free implementation — review handoff

## 0. Review provenance and disposition

Reviewer must record name/model or human identity, date, repository/worktree used, relationship to prior R02 work, commands executed, findings, and disposition. Same-session or same-lineage reproduction is technical verification only; do not label it organizationally independent. Current disposition: `PENDING_TECHNICAL_REVIEW`. Organizational independence: not established.

## 1. Scope and authority

The user authorized I0–I5 provider-free implementation only. The implementation contains no transport/provider module and has made zero provider calls, Codex executions, fixture/root materializations, pilot/confirmatory LIVE runs, retries, replacements, or resumes. Commit and push of this implementation are not authorized.

Base HEAD and upstream at implementation start: `245adc2d1f023a87d1cbfd86a7b726aec810bd78` on `codex/llm-overlay-research-01`.

Implementation change set: two modified dependency files plus 22 new files: eight implementation modules, nine test/helper files, and five implementation evidence/review files. Five enumerated R03/news paths are user-owned and excluded from R02 verification. Four were independently committed and pushed as `37009acf4b65232230b6d4b3fcf03428ba3c70da`; subsequent modifications to three of those paths and the new coverage-audit JSON remain separate concurrent R03 work. This R02 work used only their paths, status, and observed digests for separation checks; it did not interpret, edit, delete, stage, commit, or push them.

## 2. Pinned review artifacts

- implementation narrative: `docs/r02-overlay-v2-provider-free-implementation.md` — `33181409f44e0965b494c5773918138411bd13aaa0a44a4c9650c06ad1df153b`
- canonical evidence: `docs/r02-overlay-v2-implementation-evidence.json` — `adad6d3173a92d59234c527bd3ed6c697e189fe01951ba51bd232d1e172fdc35`
- zero-call manifest: `docs/r02-overlay-v2-implementation-zero-call-manifest.json` — `3a2a8665e74f9fb1e1a5bdd02bebaefef6d2133e86f2f54e343b4ad8ba648db4`
- provider-free verifier: `scripts/r02_overlay_v2_implementation_verify.py` — `401e2a08806c3992ca9855e883393c02b82780101a3b12405658270142c61b2e`

The canonical evidence pins all eight implementation modules, all nine test/helper files, `pyproject.toml`, `poetry.lock`, accepted schemas, preregistration, and accepted implementation-plan artifacts.

## 3. Reproduction commands

From repository root on Windows:

```powershell
.venv\Scripts\python.exe scripts\r02_overlay_v2_implementation_verify.py
.venv\Scripts\python.exe -m pytest -q v2/research/overlay/test_r02_v2_contracts.py v2/research/overlay/test_r02_v2_payload.py v2/research/overlay/test_r02_v2_grounding.py v2/research/overlay/test_r02_v2_comparator.py v2/research/overlay/test_r02_v2_selection.py v2/research/overlay/test_r02_v2_headroom.py v2/research/overlay/test_r02_v2_power.py v2/research/overlay/test_r02_v2_audit.py
.venv\Scripts\python.exe -m pytest -q --basetemp=C:\tmp\r02-v2-pytest-independent v2\research\overlay
```

Expected verifier marker:

```text
PASS_R02_OVERLAY_V2_PROVIDER_FREE_IMPLEMENTATION negative_tests=10 focused_tests=27 full_overlay_tests=433 provider_calls=0 live_runs=0 implementation_files=8
```

Expected test results: focused 27 passed; full overlay 433 passed. The full suite takes approximately eight minutes on the implementation host and needs an external temporary directory because existing historical tests materialize temporary audit roots.

## 4. Required technical review

1. Recompute every pin; confirm both JSON artifacts are canonical bytes.
2. Confirm the implementation diff is exactly the documented 24 files and excludes the four user-owned paths.
3. Re-run verifier, focused tests, and full overlay tests.
4. Confirm accepted payload/response schema byte parity and Draft 2020-12 metaschema validation; verify `jsonschema` is development-only.
5. Confirm payload construction exposes public context and candidates only, recomputes serialized metrics, and binds identical payload bytes to tier-2 and LLM-v2 policies.
6. Confirm strict JSON/duplicate-key handling, single RFC 6901 decoding, canonical array indexes, bounds, selected-candidate scope, and field-reference grounding.
7. Confirm exactly 19 deterministic scorer configurations, integer fixed-point arithmetic, canonical tie-breaking, and presented-order invariance.
8. Confirm all policy selections are sealed before hidden oracle utilities enter; oracle map must equal the full presented candidate set; splits must not overlap.
9. Confirm headroom labels, 3:1 stratum weighting, information floors, invalid-design path, diagnostics, deterministic bootstrap, 288-cell grid, worst-cell rule, Wilson pilot gate, and failure ITT behavior.
10. Confirm append-only audit replay and the complete 13-gate-to-test mapping.
11. Inspect all eight modules for provider, network, subprocess, credential, transport, and root-materialization capabilities.
12. Independently verify every zero-call counter and that no fixture/provider/LIVE authorization is implied.

## 5. Review outputs and next order

Record blocking and nonblocking findings in this handoff or a separately pinned acceptance artifact. If findings require changes, update pins and rerun all checks. If accepted, the user must separately authorize status promotion and commit/push. Implementation acceptance alone must not authorize fixture generation, provider calls, pilot LIVE, confirmatory LIVE, retry, replacement, or resume.

## 6. Technical review record (2026-07-19)

- Reviewer: Claude (Fable 5), Claude Code session on the implementation
  workstation, repository `C:\Users\User\Desktop\ai-hedge-fund-fresh`, branch
  `codex/llm-overlay-research-01` at base HEAD `245adc2` plus the uncommitted
  implementation change set.
- Relationship: same-session lineage as prior R02 acceptance work —
  **technical verification only; organizational independence NOT established.**
- Commands executed: full overlay regression
  (`python -m pytest -q v2/research/overlay/` → **432 passed in 528.04s**);
  verifier (`scripts/r02_overlay_v2_implementation_verify.py` → exact expected
  marker, exit 0); independent SHA-256 recomputation of all 19 `file_sha256`
  pins, all 7 `accepted_inputs` pins, and the manifest's
  evidence/verifier/implementation-doc cross-pins plus this handoff's manifest
  pin (`e05321f5…`) — **0 mismatches**; static import scan of all eight modules
  for network/provider/subprocess/credential capability and for
  wall-clock/non-derived randomness — 0 hits; diff-set audit — exactly 24
  files, four enumerated R03/news user paths untouched.
- Specification conformance (accepted headroom-and-power design +
  preregistration draft vs code): 19-scorer family identity and weight sums;
  integer half-even arithmetic; canonical-candidate-id tie-breaking; 3:1
  stratum weighting formula; stratified PCG64 bootstrap with domain-separated
  seed derivation; strict `lower_95 > 50_000_000` pass rule; information
  floors 150/50/5/5/20 routing to `HEADROOM_GATE_INCONCLUSIVE_LOW_INFORMATION`;
  `INVALID_DESIGN` paths; 288-cell grid with inclusion rule
  `rate×mean/1e6 ≥ 5e7`; least-powered-cell governance; Wilson pilot floors
  (2/2/5 with rate lower bounds); fail-closed confirmatory sizing; sealed
  selection before oracle attachment with exact candidate-set binding;
  five-split non-overlap; hash-chained append-only audit with replay. All
  conform.
- Blocking findings: **0**.
- Nonblocking findings: **1** — `simulate_cell_power.passes` uses the point
  estimate (`estimated_power_ppm ≥ 800_000`), not the Wilson lower bound; with
  1,000 trials the Monte-Carlo error (~1.3%p) allows a true-power ~79% cell to
  pass by chance. The accepted design does not specify the estimator, so this
  is not a violation; the estimator choice (point estimate vs Wilson lower)
  must be pinned in the preregistration language at the comparator/headroom
  freeze before any gate run.
- Disposition: `TECHNICAL_REVIEW_PASSED_NONBLOCKING_FINDINGS_RECORDED`.
  Status promotion beyond `IMPLEMENTED_PROVIDER_FREE_REVIEW_REQUIRED`,
  commit/push, fixture generation, and any provider/LIVE activity each remain
  separately user-authorized.

## 7. Authorized nonblocking-finding resolution (2026-07-19)

- User authorization: change the confirmatory power gate to require
  `two-sided 95% Wilson lower power >= 800,000 ppm`, add a boundary regression
  test, rerun focused and full overlay tests, and repin implementation evidence.
  Provider calls, fixture generation, LIVE work, commit, and push remained
  unauthorized.
- Code resolution: `simulate_cell_power.passes` now delegates only to the
  Wilson-lower rule. The point estimate remains descriptive and cannot govern
  the gate.
- Boundary control: 820 supported trials out of 1,000 have point estimate
  820,000 ppm but Wilson lower 794,978 ppm and must fail; 825/1,000 has Wilson
  lower 800,218 ppm and must pass.
- Reverification state: focused suite 27 passed; full overlay suite 433 passed
  in 564.84 seconds; repinned verifier emitted the exact expected marker with
  `negative_tests=9`, exit 0. Canonical evidence and zero-call manifest were
  regenerated and their current hashes are pinned in §2.
- Disposition: `REMEDIATED_RESEALED_PROVIDER_FREE_REVIEW_REQUIRED`.

## 8. Concurrent R03 isolation and status normalization (2026-07-19)

- Review follow-up identified one new concurrent R03 path,
  `docs/r03-news-reasoning-provider-free-coverage-audit.json`, and ongoing
  modifications to three already enumerated R03 documents.
- The exact excluded set is now five paths. Their committed, modified, or
  untracked state is ignored only for R02 change-set accounting; no R03 content
  is accepted as R02 evidence. Any sixth path still fails closed.
- Narrative, canonical evidence, and zero-call manifest now share
  `REMEDIATED_RESEALED_PROVIDER_FREE_REVIEW_REQUIRED`. A tenth negative test
  rejects regression to the stale pre-remediation status.
- No implementation code changed after the 433/433 full-overlay result.
  Focused tests and the repinned verifier were rerun after this isolation-only
  adjustment.

## 9. Second technical review record — remediation reseal (2026-07-19)

- Reviewer: Claude (Fable 5), same session lineage as §6 — technical
  verification only; organizational independence NOT established.
- Remediation verified:
  - `passes_power_gate()` (`r02_v2_power.py:117-120`) governs solely by
    `wilson_lower_power_ppm >= 800_000`; point estimate demoted to descriptive.
  - Boundary independently recomputed: 820/1,000 → 794,978 (fail),
    824/1,000 → 799,170 (fail), 825/1,000 → 800,218 (pass) — matches the
    sealed boundary control and the regression test
    `test_power_gate_uses_wilson_lower_not_point_estimate`.
  - Full overlay suite independently rerun: **433 passed in 616.53s** on the
    exact resealed code state (implementation mtimes precede the reseal; no
    code change after).
  - Focused suites re-verified; §2 pins, evidence `file_sha256` (19/19),
    manifest→evidence/verifier cross-pins all recomputed — 0 mismatches.
  - §8 state confirmed: evidence + manifest + narrative all carry
    `REMEDIATED_RESEALED_PROVIDER_FREE_REVIEW_REQUIRED`; negative tests = 10
    including `reject_point_estimate_power_gate_policy` and
    `reject_stale_reseal_status`; excluded R03 set = exactly five paths.
  - `docs/r03-news-reasoning-provider-free-coverage-audit.json` inspected:
    aggregate statistics only, `raw_text_emitted: false`, longest string
    127 chars — no licensed article text in the repository.
- Open operational finding (process, not code): the exact-worktree check is
  colliding with live concurrent R03 authoring. During this review a sixth
  R03 path (`docs/r03-news-reasoning-p5-review-handoff.md`) appeared and the
  verifier correctly failed closed on it. Enumerating paths one-by-one will
  not converge while R03 authoring continues. Resolution options:
  (a) freeze R03 file creation for the duration of a clean verifier run, or
  (b) user authorizes the R02 24-file commit, after which the descendant-mode
  worktree policy applies. Until one of these produces a reproducible PASS,
  acceptance remains open.
- Disposition: `REMEDIATION_TECHNICALLY_VERIFIED_PENDING_CLEAN_VERIFIER_RUN`.
  Status promotion, commit/push, fixture generation, and any provider/LIVE
  activity each remain separately user-authorized.

## 10. Clean verifier reproduction after R03-P5 seal (2026-07-19)

- User authorization was limited to adding the two newly committed R03-P5 paths
  to the R02 isolation set and resealing verifier evidence:
  - `docs/r03-news-reasoning-p5-review-handoff.md`;
  - `docs/r03-news-reasoning-p5-zero-call-manifest.json`.
- `scripts/r02_overlay_v2_implementation_verify.py`, canonical evidence, and the
  zero-call manifest now share the exact seven-path R03 exclusion set. §2 pins
  were regenerated. No implementation module, test, dependency, accepted input,
  or implementation narrative changed.
- The main worktree later acquired two separate untracked PIT-universe R03
  artifacts. The verifier correctly failed closed on those unapproved paths; they
  were not read as R02 evidence, modified, copied, staged, or enumerated into the
  R02 exclusion set.
- Clean reproduction used a local clone at HEAD
  `73e1d2dd8135050205de299f5114a27a996495b6`, created with
  `core.autocrlf=false`, then overlaid with exactly the 24 R02 implementation
  paths. Git status contained exactly those 24 paths and no R03 worktree entry.
- The repository verifier exited 0 with the exact marker:
  `PASS_R02_OVERLAY_V2_PROVIDER_FREE_IMPLEMENTATION negative_tests=10
  focused_tests=27 full_overlay_tests=433 provider_calls=0 live_runs=0
  implementation_files=8`.
- The focused I0–I5 suite independently passed 27/27 in that clean clone.
- The full overlay suite passed 433/433 in 467.97 seconds on the identical
  implementation-module state in the main workspace. Its sole sandbox-only
  identity failure was independently rerun with local credential-store access
  and passed; a single elevated run then produced the 433/433 result. This was a
  local zero-call identity check, not a provider call.
- A full-suite attempt inside the clean clone was non-acceptance diagnostic only:
  it lacked ignored historical `.research_artifacts` roots and therefore failed
  99 legacy fixture-dependent tests. Those roots were deliberately not copied or
  materialized because fixture/root materialization remains unauthorized.
- Provider calls, Codex executions, fixture/root materializations, pilot or
  confirmatory LIVE runs, retries, replacements, and resumes remain zero. Main
  worktree staging, commit, and push remain zero for the R02 set.
- Disposition: `CLEAN_VERIFIER_REPRODUCED_PROVIDER_FREE_PENDING_USER_ACCEPTANCE`.
  Implementation acceptance and the exact 24-file commit/push remain separate
  user decisions. Organizational independence remains not established.

## 11. PIT-universe path isolation follow-up (2026-07-19)

- After the exact 24-file R02 implementation commit
  `8bf074818bb780baa3a2954685af74659bc19f3b`, two separately reviewed R03
  feasibility artifacts remained untracked:
  - `docs/r03-pit-universe-feasibility-evidence.json`;
  - `docs/r03-pit-universe-feasibility.md`.
- The user explicitly authorized adding exactly those two paths to the R02
  isolation set, resealing the verifier/evidence/manifest/handoff four-file set,
  and committing and pushing that exact follow-up. This does not accept either
  R03 file as R02 evidence or authorize staging, editing, or committing it.
- The R03 isolation set is now exactly nine paths. Evidence and zero-call
  manifest arrays match the verifier set; §2 contains the regenerated byte
  hashes. No implementation module, test, dependency, accepted input, or
  implementation narrative changed.
- The verifier's post-commit policy intentionally rejects dirty intended R02
  paths, so the official post-commit run occurs only after the exact four-file
  follow-up commit. Push is conditional on its exit-0 PASS marker.
- Provider calls, Codex executions, fixture/root materializations, pilot or
  confirmatory LIVE runs, retries, replacements, and resumes remain zero.
- After the exact four-file follow-up commit, the main-worktree verifier ignored
  only the nine enumerated R03 paths, exited 0, and emitted the exact provider-
  free PASS marker with `negative_tests=10`, `focused_tests=27`,
  `full_overlay_tests=433`, `provider_calls=0`, `live_runs=0`, and
  `implementation_files=8`. The only remaining worktree entries were the two
  untracked PIT-universe artifacts, both covered by the isolation set.
- Final disposition:
  `PIT_PATH_ISOLATION_RESEALED_POST_COMMIT_VERIFIER_PASS`.

## 11. Third technical review record — clean reproduction verified (2026-07-19)

- Reviewer: Claude (Fable 5), same session lineage as §6/§9 — technical
  verification only; organizational independence NOT established.
- §2 pins (all four artifacts) and evidence `file_sha256` (19/19) recomputed —
  0 mismatches. Manifest cross-pins verified. Implementation-module mtimes
  confirm no code change since the independently reproduced 433/433 runs
  (528.04s and 616.53s in the main workspace).
- Manifest inspection: seven-path R03 exclusion set matches exactly the
  user-authorized addition (the two committed R03-P5 seal paths); the two
  untracked PIT-universe artifacts were correctly NOT enumerated and fail
  closed in the main worktree (independently confirmed, exit 1 on exactly
  those two paths). `worktree_policy` now
  `BASE_OR_DESCENDANT…POST_COMMIT_DIFF_MUST_ADD_EXACT_TWENTY_FOUR…`.
- **Independent clean-clone reproduction (not a re-run of Codex's clone):**
  fresh `git clone -c core.autocrlf=false` of the repository at
  `73e1d2d`, overlaid with exactly the 24 R02 paths copied from the main
  worktree; `git status --porcelain` showed exactly 24 entries. Verifier:
  **exit 0** with the exact expected marker
  (`negative_tests=10 focused_tests=27 full_overlay_tests=433
  provider_calls=0 live_runs=0 implementation_files=8`). Focused suite in the
  clone: **27 passed**. Incidental probe: a stray `verif.log` inside the clone
  correctly failed the exact-worktree check before it was moved out —
  fail-closed behavior confirmed live.
- Full-suite basis: 433/433 accepted from the two prior independent main-
  workspace runs on byte-identical modules; the clean clone intentionally
  omits ignored historical `.research_artifacts` roots (materialization
  unauthorized), so a clone full-suite run is diagnostic-only, as §10 states.
- Blocking findings: **0**. Nonblocking: none new.
- Disposition: **`TECHNICAL_REVIEW_COMPLETE_RECOMMEND_ACCEPTANCE`** — the §9
  pending condition (reproducible clean verifier PASS) is satisfied.
  Implementation acceptance, status promotion, and the exact 24-file
  commit/push remain user decisions; fixture/provider/LIVE work stays
  separately gated and is not implied by acceptance.
