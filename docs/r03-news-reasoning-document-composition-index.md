# R03 news-reasoning document composition index

Status: `INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY`  
Scope: additive discovery and composition record only

## Effective document pairs

Neither sealed base document is complete when read alone for the selected-payload
retention assertion. Readers must compose each base with its pinned amendment:

| Surface | Sealed base | Additive amendment |
|---|---|---|
| charter | `docs/r03-news-reasoning-charter-draft.md` | `docs/r03-news-reasoning-charter-v2-retention-amendment.md` |
| provider-free preregistration | `docs/r03-news-reasoning-provider-free-preregistration-draft.md` | `docs/r03-news-reasoning-provider-free-preregistration-v2-retention-amendment.md` |

The base files remain byte-for-byte unchanged. Their 90.53% statements are
historical, non-normative records after composition.

## Effective retention reference

The effective selected-payload retention value is:

> 1,515,387,041 / 1,585,976,846 text bytes = 95.55%, using
> `ROUND_HALF_EVEN_2DP`.

Precedence: `REPLACE_NOT_RECONCILE`. This is a replacement by the independently
approved V2 measurement, not a rounding correction or a reconciliation to the
historical 90.53% or P5-era 97.03% values.

The machine-readable contract is
`docs/r03-news-reasoning-n1-v2-effective-retention-contract.json`, canonical
SHA-256
`7277792e284aaa90d8ca7bcef828102e28f587950f8a2ca7951b5dae93136704`.

## Acceptance composition

The contract's embedded `PENDING_INDEPENDENT_REVIEW` status records its creation
time and is not edited in place. Its current review state is obtained by
composing it with:

- `docs/r03-news-reasoning-n1-v2-reference-propagation-independent-review.md`
  (filesystem SHA-256
  `f6e710159840a96e16720aab54d046a3bcf45d3dd1a7271a190bfa9886f6449b`);
- `docs/r03-news-reasoning-n1-v2-reference-propagation-acceptance-attestation.json`.

This append-only acceptance composition yields
`INDEPENDENT_TECHNICAL_REVIEW_ACCEPTED_NO_NEW_EXECUTION_AUTHORITY` while
preserving the reviewed contract identity.

## Non-authority

This index and its acceptance attestation do not authorize raw-source access,
frame or fixture creation, fitting, G1-G3, OOS access, inference or model
downloads, provider or network use, dependency changes, commits, or pushes.

