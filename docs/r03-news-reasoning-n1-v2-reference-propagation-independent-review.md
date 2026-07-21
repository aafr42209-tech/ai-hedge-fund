# R03 N1 V2 reference-propagation independent technical review

Date: 2026-07-21
Reviewed handoff: `docs/r03-news-reasoning-n1-v2-reference-propagation-review-handoff.md`
(filesystem SHA-256 `f1162f53a8a1dd5b…`)
Review basis: HEAD `605ef598446b851bce8def647f8769a885a6274c`, working tree with the
nine new paths untracked and unstaged.

Disposition: `INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY`

## 1. Scope and method

The review did not rely on the submitted verifier alone. Each load-bearing claim
was recomputed from primary artifacts with independent code, and the fail-closed
behavior was probed with mutations the submitted test module does not contain.
No repository file was written, staged, committed, or pushed during the review;
all mutations were in-memory or on copied text.

## 2. Independently recomputed identities

| Claim | Independent recomputation | Result |
|---|---|---|
| effective contract canonical SHA-256 | `json.dumps(sort_keys, separators=(",",":"), ensure_ascii=False)` over the unsigned object | `7277792e284aaa90d8ca7bcef828102e28f587950f8a2ca7951b5dae93136704` — matches pin and self-hash |
| effective retention canonical SHA-256 | same canonicalization over the unsigned retention block | `8b659ac03fb4481ebbbcdc3579e484f5630d8e490d6981c0b4a7a2c3c02c1019` — matches |
| `1,515,387,041 / 1,585,976,846` | `Decimal` division, `ROUND_HALF_EVEN`, 2dp | `95.55` |
| legacy `1,435,742,878 / 1,585,976,846` | same rule | `90.53` — the superseded clause is arithmetically self-consistent, so the change is a replacement, not a correction of a stale rounding |

The canonicalizer used by the verifier (`v2/research/overlay/canonical.py`)
rejects floats and non-string keys, so the identity is byte-stable for the
integer-only payloads in scope.

## 3. Trust root: pins resolve to committed artifacts

The submitted verifier is itself untracked, so its constants are not a trust
anchor. Every `normative_source` pin was therefore recomputed from the
**committed** V2 reseal artifacts, not from the new overlay:

- reseal lineage `8f3b3f0c…`, attestation `44002b7a…`, evidence `a170b0bd…` —
  recomputed canonical hashes equal both the pinned value and each artifact's
  own self-hash field.
- reseal manifest `37ea72d5…` and ancestor-fix review `4c20f452…` — recomputed
  filesystem hashes match.
- all five pinned artifacts are tracked in git (`git ls-files --error-unmatch`).

So the 95.55% value entering the overlay is the one already approved upstream,
not a value minted inside this overlay.

## 4. Base-document preservation

- `git hash-object` of both base documents equals `git rev-parse HEAD:<path>` —
  byte-identical to the committed blobs, stronger than a filesystem-hash match
  against a constant declared by the same change set.
- `git diff --stat HEAD` over `docs scripts tests v2`: empty.
- `90.53` occurs exactly once in each base document; `95.55` occurs zero times.

## 5. Adversarial probes (independent, 17/17 rejected as required)

Self-consistently re-signed mutations were rejected in every case:

| Probe | Rejection |
|---|---|
| contract effective value reverted to 90.53 and re-signed | contract identity mismatch |
| contract `precedence.action` → `RECONCILE` and re-signed | contract identity mismatch |
| contract base-document identity replaced and re-signed | contract identity mismatch |
| contract amendment pin replaced and re-signed | contract identity mismatch |
| lineage `raw_source_traversals` → 1 and re-signed | lineage identity mismatch |
| lineage `replacement_mode` → `RECONCILE` and re-signed | lineage identity mismatch |
| evidence artifact pin corrupted and re-signed | evidence artifact pin mismatch |
| manifest `provider_calls` → 1 | manifest counters are not zero |
| valid lineage checked against a re-signed contract | contract pin mismatch (cross-pin holds) |
| base text with a direct 95.55% edit | old clause must remain exactly once |
| base text with the clause removed | old clause must remain exactly once |

Re-signing therefore cannot move the effective value, the precedence mode, the
base identity, or the zero-call boundary: the pinned constants and the committed
upstream chain both have to be broken, and the base clause hash is checked
against the constant itself before use.

## 6. Reproduced gates

- five verifiers (`data_check`, `reconciliation`, `reconciliation_rerun`,
  `v2_normative_reseal`, `v2_reference_propagation`): all `rc=0`, PASS lines
  reproduced, `raw_source_traversals=0`.
- `pytest -k r03`: `179 passed, 65 deselected`.
- `tests/test_r03_v2_reference_propagation_verify.py`: `24 passed`.
- black, isort, flake8 (`--max-line-length=420`) on both new Python files: clean.
- new script and test import no network, provider, or subprocess surface.
- post-review git state unchanged: HEAD `605ef598…`, nine paths untracked,
  staged `0`, unstaged tracked diff `0`.

Note: the reported gates required the project virtualenv
(`.venv/Scripts/python.exe`); the bare system interpreter has no pytest or lint
tooling installed. This is an environment fact, not a defect in the submission.

## 7. Answers to the handoff's review questions

1. **Composition unambiguous?** Yes at the machine layer. Each amendment pins the
   base filesystem hash and the exact superseded clause hash, declares
   `REPLACE_NOT_RECONCILE`, and states the replacement text once. 95.55% is
   effective; 90.53% and the P5-era 97.03% are historical only.
2. **Reproducible fail-closed pin chain?** Yes. Contract → lineage → evidence →
   manifest cross-pin, and the chain terminates in committed reseal artifacts
   that were independently rehashed.
3. **Adversarial coverage sufficient?** Yes, per section 5; re-signing is inert.
4. **Disposition warranted?** Yes —
   `INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY`.
   No new execution, raw-source, fitting, provider, or gate authority follows
   from this acceptance.

## 8. Findings

**MEDIUM — amendment discoverability from the base documents.**
Neither base document contains any reference to its amendment (`grep` count 0),
which is a necessary consequence of byte-for-byte preservation. A reader opening
only `r03-news-reasoning-charter-draft.md` will read 90.53% as normative. The
machine layer is safe, the human layer is not. Suggested mitigation, additive
and outside this change set: a tracked composition index that lists, for each
sealed base document, its active amendments and the effective contract path.

**PROCEDURAL — accepting the review changes the contract's own identity.**
`status` is `EFFECTIVE_V2_RETENTION_REFERENCE_OVERLAY_PENDING_INDEPENDENT_REVIEW`
and is inside the canonical hash. Recording acceptance in the contract will
change `effective_contract_sha256`, hence the lineage, evidence, and manifest
pins and the verifier constants. This must be executed as one atomic reseal, not
an in-place status edit, and it needs its own authorization.

**Not a defect.** `r03_news_reasoning_implementation_verify.py` still reports the
known `r03_source.py` snapshot mismatch. The handoff's framing is accurate: it is
a historical CODE_ONLY seal, not a current composition gate.

## 9. Boundary counters for this review

`raw_source_traversals=0 provider_calls=0 network_attempts=0
dependency_changes=0 fixture_materializations=0 gate_executions=0 commits=0
pushes=0`

Repository writes by this review: this document only, left untracked.
