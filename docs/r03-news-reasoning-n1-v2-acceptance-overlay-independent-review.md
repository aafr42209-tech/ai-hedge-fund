# R03 N1 V2 acceptance-overlay independent technical review

Date: 2026-07-21
Reviewed handoff: `docs/r03-news-reasoning-n1-v2-reference-propagation-acceptance-review-handoff.md`
(filesystem SHA-256 `79367830a7ffc9d7…`)
Review basis: HEAD `605ef598446b851bce8def647f8769a885a6274c`, fifteen overlay paths
untracked and unstaged.

Disposition: `INDEPENDENT_ACCEPTANCE_OVERLAY_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY`

## 1. Scope

This review covers only the append-only acceptance layer: the composition index,
the acceptance attestation, the acceptance verifier, and its test module. The
underlying reference-propagation layer was accepted in
`docs/r03-news-reasoning-n1-v2-reference-propagation-independent-review.md`;
its gates were re-run here as a regression check, not re-reviewed.

The prior review document is now pinned by the artifact under review. It was
therefore left byte-for-byte untouched; this is a separate file.

## 2. Prior-review integrity (checked first)

The acceptance attestation asserts a disposition on behalf of the prior review.
As the author of that review, I read the on-disk document in full and confirm it
is content-intact: all nine sections present, the `Disposition:` line unchanged,
and both findings (MEDIUM discoverability, PROCEDURAL status-reseal) present
verbatim, with no appended or removed acceptance language.

Its pinned hash `f6e710159840a96e…` was independently recomputed from the file
and matches both the verifier constant and the attestation's
`independent_review.filesystem_sha256`.

## 3. Independently recomputed identities

- acceptance attestation canonical: recomputed
  `e9247117274a00365ea47e536c4ce338c9ccd38f59091ab01105f085863ab1aa` from the
  unsigned object — equals the self-hash field and the verifier constant.
- all thirteen pinned filesystem hashes (ten reviewed artifacts, two sealed base
  documents, composition index) recomputed from disk: zero mismatches.
- the reviewed-artifact set is exactly the ten paths supplied to the accepted
  review, including the review document itself.

## 4. Adversarial probes (independent, 27/27 behaved as required)

Beyond the submitted test module, the following were exercised:

- **Self-consistent re-signing, 13 variants** — disposition flip to rejected,
  mode flip to in-place reseal, authority swap, reviewed-HEAD swap, preservation
  flags flipped to "modified", non-zero boundary counter, non-authority flipped
  to grant raw-source access, retention reverted to 90.53, and pin swaps for
  review, index, reviewed artifacts, base documents, and contract. Every variant
  was rejected at the fixed canonical identity, so re-signing is inert.
- **Review-document tamper** — disposition marker removed, and content appended
  with a duplicate marker: both rejected on filesystem drift before the marker
  count is even reached, which is the stronger ordering.
- **Composition-index tamper** — amendment reference removed, legacy-role
  statement rewritten to "current", effective value reverted to 90.53: all
  rejected.
- **Reviewed-artifact drift** — a copied tree with one trailing byte added to the
  contract: rejected.
- **Ancestry** — the pinned reviewed HEAD verifies as an ancestor; a malformed
  ref and an unknown all-zero commit both return false rather than raising, and
  the root commit verifies as a sanity control.
- **Input immutability** — `assert_attestation` leaves its input unmutated.

Re-running the prior layer's probe set: 17/17 still rejected.

## 5. Reproduced gates

- six verifiers (`data_check`, `reconciliation`, `reconciliation_rerun`,
  `v2_normative_reseal`, `v2_reference_propagation`,
  `v2_reference_propagation_acceptance`): all `rc=0`.
- `pytest -k r03`: `206 passed, 65 deselected`.
- `tests/test_r03_v2_reference_propagation_acceptance_verify.py`: `27 passed`.
- black, isort, flake8 (`--max-line-length=420`) on both new Python files: clean.
- no network client imports in the new script or test.
- post-review git state: HEAD `605ef598…`, tracked diff `0`, staged `0`,
  untracked overlay paths unchanged.

The acceptance verifier's use of `subprocess` is limited to
`git merge-base --is-ancestor` with a validated 40-hex argument and
`check=False`; `OSError` returns false. No shell, no user-controlled argument.

## 6. Disposition of the prior review's findings

- **MEDIUM (discoverability) — substantially addressed.** The composition index
  states both document pairs, the effective value with `REPLACE_NOT_RECONCILE`,
  the contract canonical hash, and the 90.53% historical role, and the verifier
  enforces those fragments. Residual, unchanged: a reader still has to know the
  index exists. Base files legitimately cannot carry a backlink. Closing this
  fully requires the index to be reachable from a tracked entry point once these
  paths are committed.
- **PROCEDURAL (status reseal) — resolved as recommended, and better.** Rather
  than resealing the contract, acceptance is expressed by composing the immutable
  pending-status contract with the pinned review and attestation. No in-place
  edit occurred; the reviewed contract's canonical identity is unchanged.

## 7. Findings

**OBSERVATION — the attestation is authored by the implementing party.**
`accepted_disposition` is an implementer-written field; it is not a reviewer
signature. Its trustworthiness rests entirely on the pinned review document and
the exactly-once disposition marker, both of which are enforced. Any downstream
consumer must treat the pinned review as the binding evidence and re-read it,
not treat the attestation field as self-certifying. No change requested — the
construction is sound; this is a reading rule.

**LOW — ancestry check is coarse.** `reviewed_head_is_ancestor` accepts any
descendant of the reviewed HEAD, so the attestation stays valid across arbitrary
future commits. Artifact-hash pins carry the real integrity load here, so this is
acceptable; it is worth stating explicitly that ancestry is a staleness guard,
not a provenance proof.

**No blocking findings.**

## 8. Boundary counters for this review

`raw_source_traversals=0 provider_calls=0 network_attempts=0
dependency_changes=0 fixture_materializations=0 gate_executions=0 commits=0
pushes=0`

Repository writes by this review: this document only, left untracked. The ten
previously reviewed paths and both sealed base documents were re-hashed after the
review and are unchanged.
