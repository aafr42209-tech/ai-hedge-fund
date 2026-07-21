# R03 preregistration — V2 normative retention amendment

Authority: `R03_N1_V2_NORMATIVE_REFERENCE_PROPAGATION_CODE_AUTHORIZED`

## 1. Additive scope

This amendment overlays only the selected-payload retention expectation in
`r03-news-reasoning-provider-free-preregistration-draft.md`. The base
preregistration remains byte-for-byte unchanged. All frozen estimands, gates,
splits, models, and stop rules retain their existing meaning and review status.

Base preregistration filesystem SHA-256:
`741fc091e689ac4a848cd2ea43fc99f26295b632831d33426028769b31bde211`.

The superseded assertion is identified by exact UTF-8 clause SHA-256:
`5ab3b69d651b6c4cb456aabf1675c8bceaa152b04cdc97c8a1a03c7653cf4cc7`.

## 2. Effective replacement

Disposition: `REPLACE_NOT_RECONCILE`.

For all future R03 preregistered decisions, the selected-payload retention
expectation shall be read as:

> The pinned V2 contract fully preserves 150,394/151,820 news-positive frames
> (99.06%), retains 695,948/702,489 article appearances (99.07%), and retains
> 1,515,387,041/1,585,976,846 text bytes (95.55%), using round-half-even to two
> decimal places.

The effective value replaces the legacy assertion. It is not fitted or
reconciled to the historical 90.53% value. The P5-era 97.03% and legacy
fail-closed 90.53% values remain immutable provenance and are forbidden as
future gate inputs.

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
