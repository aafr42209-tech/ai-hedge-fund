# R03 N1 reconciliation — code-only review handoff

## 1. Final disposition

Independent review of the isolated reconciliation contract and synthetic
evidence under `R03_N1_RECONCILIATION_CODE_ONLY_AUTHORIZED` is complete.

No raw rerun, retention reseal, frame/fixture creation, fit, gate, OOS access,
inference, model download, provider/network access, dependency change, commit,
or push is authorized by this handoff.

Disposition:

`INDEPENDENT_RECONCILIATION_CONTRACT_REVIEW_APPROVED`

The first independent review returned `CHANGES_REQUESTED`; the second returned
`APPROVED` after independently confirming that every demonstrated behavior-hash
blind spot and both HIGH findings were closed. Two non-blocking pre-commit
recommendations were then applied: the expanded input-byte acceptance contract
is versioned as v2, and runtime pin-calculation failures are normalized to
`R03ReconciliationError`.

## 2. Why this layer exists

The historical amendment carried pre-amendment census values into a v2
retention contract without executing that v2 contract against raw source. The
later authorized run was therefore the first v2 measurement, not a failed v2
reproduction. Its attestation canonically classifies the event as:

`FIRST_V2_RAW_MEASUREMENT_EXPOSED_UNVERIFIED_SEAL`

Neither the historical `90.53%` nor the first-run `95.55%` is selected as the
normative value here. The disposition remains
`UNRESOLVED_NO_VALUE_RESEALED`.

## 3. Temporal scopes

Three scopes are deliberately separate:

1. The historical amendment lineage and zero-call manifest describe the
   `PRE_RERUN_AMENDMENT_CODE_ONLY_SESSION` and remain byte-for-byte unchanged.
2. The rerun attestation describes
   `POST_AMENDMENT_AUTHORIZED_RERUN_ATTEMPTS`, including its nonzero traversal
   accounting and closed commit gate.
3. The new zero-call manifest describes only the current
   `N1_RECONCILIATION_CODE_ONLY_SESSION`.

The existing amendment verifier and its exact historical zero-set assertion
are unchanged. The new verifier layers the latter two scopes around that
historical verification instead of rewriting it.

## 4. Canonical classification

The normative classification path is:

`provenance_classification.classification`

with exact value:

`FIRST_V2_RAW_MEASUREMENT_EXPOSED_UNVERIFIED_SEAL`

`investigation_note.classification` is a non-normative causal-status field. It
may remain `UNRESOLVED_ADAPTER_OR_PRIOR_CENSUS_SEMANTICS_DIVERGENCE` while the
canonical provenance classification above stays fixed.

## 5. Runtime-bound contract

The new module does not modify the three historically pinned implementation
files. It imports and probes their actual behavior, then exposes executable
hashes that a future versioned permit must pin.

Pinned surfaces:

- `canonicalize_text`: preserve whitespace, CRLF/CR to LF, NFC, reject NUL;
- `R03ArticleRecord`: strict fields with no implicit text stripping;
- provider decoder: string-or-null only, preserving provider codepoints;
- version key: maximum `(available_at, updated_at, input_text_sha256,
  canonical_payload_text_sha256)`;
- retained predicate: the included flag is normative; included zero-byte and
  zero-source appearances remain countable and are separately diagnosed;
- input-byte measure and executable hash: appearance-weighted canonical
  headline/summary/content UTF-8 bytes before caps;
- paired-frame output schema, direct-identifier/raw-text exclusion, numeric
  quasi-identifier disclosure, and aggregate diagnostic counters.

`validate_reconciliation_permit` revalidates public fields through Pydantic,
checks the externally supplied permit pin, both reconciliation and embedded base
permit self-hashes, then compares every executable behavior hash. Root identity
is checked only after those contract checks. No callback or source traversal is
implemented in this code-only layer.

## 6. Paired-frame evidence schema

Any future reconciliation rerun must emit numeric pairs for every
session-cap-affected frame. Each pair contains only appearance counts and text
byte counts for the prior census and reconciliation paths. It contains no
ticker, date, article identifier, source locator, or text.

The numeric byte/count tuple can still act as a quasi-identifier for a reviewer
who already possesses the corpus. Canonical multiset sorting removes order-based
linkage but does not claim that numeric tuples are unlinkable.

The evidence contract requires:

- canonical numeric multiset ordering;
- affected-frame and derived-total consistency;
- old/new zero-frame counts;
- equal/changed frame counts;
- old/new retained-byte totals and delta;
- zero-source and included-zero-byte diagnostic counts;
- affected-frame count not exceeding total news-positive frames;
- reconciliation appearance/byte consistency, while prior-census inconsistency
  is preserved as a diagnostic rather than rejected;
- a pair-multiset SHA-256 and evidence self-hash;
- successful `reject_raw_text_emission` validation.

This allows the suspected whole-frame-zeroing behavior to be confirmed or
rejected without publishing reconstructable frame identities.

## 7. Synthetic negative coverage

The 28-case synthetic suite covers:

- decoder and record whitespace preservation;
- literal runtime pin values;
- permit round-trip and root identity;
- `model_copy(update=...)` literal forgery with re-signing;
- re-signed forgery of every executable/schema hash pin;
- NFC-to-NFKC and non-ASCII-whitespace normalization drift;
- embedded base-permit self-hash tampering;
- every deterministic version-key precedence stage and priority-order drift;
- acceptance and diagnostics for included/zero-byte and zero-source appearances,
  with rejection of omitted/nonzero-byte appearances;
- executable input-byte measurement with whitespace preservation, non-null
  source exclusion, and empty headline acceptance;
- three-pair canonical ordering probes that detect reverse and constant pair
  keys;
- direct-identifier/raw-text-free paired evidence, numeric quasi-identifier
  disclosure, canonical derivations, and self-hash;
- tampered paired evidence rejection;
- separation of canonical provenance and non-normative cause paths.

All tests use synthetic records and temporary paths only.

## 8. Artifact pins

| Artifact | Filesystem SHA-256 |
|---|---|
| `v2/research/news_reasoning/r03_reconciliation.py` | `cdc0a7044ea542567bec7028ad01daf81c7ffbd03f0542c3c9342a3556d9e05f` |
| `tests/test_r03_reconciliation.py` | `0fede185f719577f904485de9603e7d04fdd7d404a3d7d82582244a956ed26d7` |
| `scripts/r03_news_reasoning_reconciliation_verify.py` | `6d50bb91c15d4ae8a3359457d94910cc582cf4642b5492752c1d2117b9594ccb` |
| `docs/r03-news-reasoning-data-check-rerun-attestation.json` | `680e4634a40d2eaf96a19cc75dfa37db8e66375368e04cf05cc3d1a989c01c2a` |
| `docs/r03-news-reasoning-n1-reconciliation-lineage.json` | `8f2db652f49466022f3b8c5acc5ba57d3fc08d0e52b88f5c2694767e56da0af1` |
| `docs/r03-news-reasoning-n1-reconciliation-code-only-evidence.json` | `3512e5813a72110bcbd9010476f62f052f688b26eb5c378ac1c3ad5a24610f84` |
| `docs/r03-news-reasoning-n1-reconciliation-zero-call-manifest.json` | `35e62777d98e94723660dcdc86983b3d96743dd65c1fa7953216eea4b56d6d76` |

Canonical identities:

- reconciliation lineage: `60bbbd2d2e16235689f2df5cb3871f891ac8d92b7f2260cc13bb116947833aa8`;
- reconciliation evidence: `f5fe43827ad228405c83416ffdb26241cad8cba701dbe8c3c0307bdee3f79514`;
- rerun attestation: `a21be7bc0a614b6b87ceef9ac3bf9cc89d25d40215dc67d7344994ce834034a0`.

## 9. Review checklist

Please independently confirm:

1. historical amendment artifacts and verifier remain unchanged and pass;
2. temporal zero counters cannot be confused with rerun attempt counters;
3. behavior hashes change for NFC-to-NFKC, source inclusion, every version-key
   precedence swap, and reversed or constant pair-key mutations;
4. the final payload-text hash resolves otherwise exact version-key ties;
5. included zero-byte and zero-source appearances are counted and diagnosed;
6. paired-frame rows expose no direct identifiers or text, disclose numeric
   quasi-identifier risk, and recompute all derived totals and cross-invariants;
7. classification authority is attached only to the canonical provenance path;
8. no retention candidate is selected or resealed;
9. no source callback, raw adapter, or rerun permit instance exists;
10. working tree remains unstaged and uncommitted.

## 10. Non-blocking review notes

Two LOW observations remain non-blocking and do not weaken permit-wide drift
detection: the input-byte probe does not independently distinguish NFC from
NFKC because the normalization pin supplies that layer, and appearance
eligibility is intentionally outside `measure_input_text_bytes` but its upstream
enforcement point is not yet named in this contract document.

## 11. Remaining authority gates

Independent acceptance of this code-only contract does not authorize a rerun.
A later `READ_ONLY_DATA_CHECK_RECONCILIATION_RERUN_AUTHORIZED` permit must pin
the exact base permit, every runtime behavior hash, the paired-diff schema, root,
calendar, early closes, caps, ordering, and externally supplied permit hash.

Only a successful separately reviewed rerun may propose a new normative N1
retention value. Resealing and commit remain distinct user gates.
