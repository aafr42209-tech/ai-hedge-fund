# R03 charter — V2 normative retention amendment

Authority: `R03_N1_V2_NORMATIVE_REFERENCE_PROPAGATION_CODE_AUTHORIZED`

## 1. Additive scope

This amendment overlays only the selected-payload retention assertion in
`r03-news-reasoning-charter-draft.md`. The base charter remains byte-for-byte
unchanged. Every other charter clause retains its existing meaning and review
status.

Base charter filesystem SHA-256:
`a96766f5b15fdecc839c07d3f66a1cc78e40d778050a3eae2623d77ffdb90329`.

The superseded assertion is identified by exact UTF-8 clause SHA-256:
`4ce3cb4f72abf0af9e551cb3cd68a5a0895da8739a07c1e328e3652c28932cf4`.

## 2. Effective replacement

Disposition: `REPLACE_NOT_RECONCILE`.

For all future R03 decisions, the selected-payload retention assertion shall be
read as:

> The pinned V2 contract fully preserves 150,394/151,820 news-positive frames
> (99.06%), retains 695,948/702,489 article appearances (99.07%), and retains
> 1,515,387,041/1,585,976,846 text bytes (95.55%). Percent displays use
> round-half-even to two decimal places.

The effective value is a replacement, not a reconciliation to either earlier
number. The P5-era 97.03% and legacy fail-closed 90.53% values remain historical
provenance and are not decision inputs.

## 3. Normative source

- V2 retention canonical SHA-256:
  `8b659ac03fb4481ebbbcdc3579e484f5630d8e490d6981c0b4a7a2c3c02c1019`.
- V2 reseal lineage canonical SHA-256:
  `8f3b3f0c25b3dd8b7c12af4232f6fb22b19db62e71b752d1555b9c114457a719`.
- V2 reseal attestation canonical SHA-256:
  `44002b7a56e3c2432b4b4abf62088241d83c397d96c1a7e33828f03eeb3659f6`.
- Corrected V2 reseal evidence canonical SHA-256:
  `a170b0bdabf967cef8f606a96bcce3f395bd90ada92a954b76bc0eeb1a7b2d6b`.
- Effective-contract machine record:
  `r03-news-reasoning-n1-v2-effective-retention-contract.json`.

## 4. Non-authority

This amendment authorizes no raw access, frame or fixture creation, fitting,
G1-G3 execution, OOS access, inference, model download, provider/network use,
dependency change, commit, or push.
