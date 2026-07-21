# R03 N1 V2 reference-propagation acceptance-overlay review handoff

Date: 2026-07-21  
Authority:
`R03_N1_V2_REFERENCE_PROPAGATION_ACCEPTANCE_ATTESTATION_AND_COMPOSITION_INDEX_CODE_AUTHORIZED`  
Requested disposition:
`INDEPENDENT_ACCEPTANCE_OVERLAY_TECHNICAL_REVIEW_REQUESTED_NO_NEW_EXECUTION_AUTHORITY`

## 1. Review claim

This append-only code/document overlay records the accepted independent review
without changing the reviewed contract or any of its nine submitted artifacts.
It also supplies the separately requested human-discovery composition index.

The reviewed contract retains its creation-time status
`EFFECTIVE_V2_RETENTION_REFERENCE_OVERLAY_PENDING_INDEPENDENT_REVIEW`. Its
current state is derived by composing that immutable contract with the pinned
independent review and acceptance attestation, yielding
`INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY`.

No in-place acceptance reseal occurred.

## 2. New artifact identities

| Artifact | Canonical SHA-256 | Filesystem SHA-256 |
|---|---|---|
| document composition index | n/a | `923d06768141df9f7c0a275aa39ac415a77c5bc3765ce2c0765bf7a6971a92c5` |
| acceptance attestation | `e9247117274a00365ea47e536c4ce338c9ccd38f59091ab01105f085863ab1aa` | `c7955a9160be66a926c9a865a29651d163d2adaaa8225e98c660dd495956364e` |
| fail-closed acceptance verifier | n/a | `479fdd5c11a31644313ccf54facabf40d5bb7e31051670bccb65051bad829600` |
| adversarial acceptance tests | n/a | `102448d77741ecddec56d7386dde482d3962457b652b6ca6ff0a27c420f19f49` |

The acceptance attestation pins:

- reviewed contract canonical
  `7277792e284aaa90d8ca7bcef828102e28f587950f8a2ca7951b5dae93136704`
  and filesystem
  `d3081ef09d2f789671c75765374392ab01ea17333c594e40b5e1de2999313fa2`;
- independent review filesystem
  `f6e710159840a96e16720aab54d046a3bcf45d3dd1a7271a190bfa9886f6449b`;
- all ten files in the accepted review set, both sealed base documents, and the
  new composition index.

## 3. Discoverability and effective composition

`docs/r03-news-reasoning-document-composition-index.md` tells a human reader
to compose:

- the sealed charter with its V2 retention amendment;
- the sealed provider-free preregistration with its V2 retention amendment;
- the immutable pending-status contract with the independent review and
  acceptance attestation.

It states the effective retention as
1,515,387,041 / 1,585,976,846 = 95.55%, with
`REPLACE_NOT_RECONCILE` precedence. The preserved 90.53% statements remain
historical and non-normative. Neither base file was edited to add a backlink.

## 4. Fail-closed behavior

The new verifier executes the prior reference-propagation verifier first. It
then verifies:

- acceptance-attestation self-hash and fixed canonical identity;
- reviewed HEAD `605ef598446b851bce8def647f8769a885a6274c` is an ancestor
  of current HEAD, with malformed commits, non-ancestors, and process errors
  failing closed;
- exact independent-review disposition and filesystem hash;
- all reviewed-artifact, base-document, contract, and index pins;
- exact effective retention, precedence, preservation, zero counters, and
  non-authority;
- absence of raw-text emission from the JSON attestation.

The tests include self-consistently re-signed tampering of authority, mode,
disposition, reviewed HEAD, contract, retention, precedence, preservation,
boundary counters, non-authority, review/index pins, reviewed artifact pins, and
base pins. They also test index/reference removal, review marker removal,
filesystem drift, propagation-gate failure, ancestry failures, and input
immutability.

## 5. Reproduced gates

- data-check amendment verifier: PASS
- reconciliation verifier: PASS
- reconciliation-rerun verifier: PASS
- V2 normative-reseal verifier: PASS
- V2 reference-propagation verifier: PASS
- V2 reference-propagation acceptance verifier: PASS
- fifteen R03 test modules: `206 passed`
- focused acceptance test module: included above, `27 passed`
- black, isort, and flake8 with `--max-line-length=420`: PASS

The historical `r03_news_reasoning_implementation_verify.py` remains outside
the current composition gates because its sealed pre-amendment source snapshot
does not include later authorized reconciliation work. It was not modified.

## 6. Preservation and boundary

The ten paths supplied to the accepted independent review were rehashed after
implementation: 10/10 match their pre-work filesystem SHA-256 values. The
tracked base documents also remain at their pinned hashes.

For this acceptance-overlay session:

- raw-source traversals or copies: 0
- frame or fixture materializations: 0
- fitting, G1-G3, OOS, inference, or model downloads: 0
- provider or network calls: 0
- dependency changes: 0
- staging, commits, or pushes: 0

This acceptance overlay grants no new execution authority.

## 7. Independent-review questions

1. Does append-only composition record the accepted disposition without
   altering or ambiguously superseding the reviewed contract?
2. Does the composition index adequately resolve the prior human-discoverability
   finding while preserving both sealed base documents?
3. Does the verifier bind the acceptance to the exact independent review,
   reviewed artifact set, contract, effective 95.55% value, and zero-call
   boundary?
4. Do self-consistent re-signing and ancestry/process-failure tests close the
   material bypass paths?
5. Is
   `INDEPENDENT_ACCEPTANCE_OVERLAY_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY`
   warranted?

