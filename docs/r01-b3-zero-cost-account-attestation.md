# R01 B3 Zero-Cost Account Attestation

Status: `ATTESTED_NO_AUTOMATIC_PAID_CREDIT_PATH`

Observation date: `2026-07-16` (Asia/Seoul)

Provider calls made at attestation: `0`

## User-observed account state

- Account context displayed: personal ChatGPT `Pro` plan.
- Purchased credit balance displayed: `KRW 0`.
- Included weekly plan usage remained available.
- The Auto top-up settings dialog displayed proposed values only: target
  `KRW 29,000`, minimum balance `KRW 7,250`, and no monthly recharge limit.
- The user did not press `Save`; the user closed the dialog with `X` and
  confirmed that Auto top-up was not enabled.
- No Business or other organization workspace credit pool was displayed or
  selected in the observed personal Pro billing context.

## Execution rule

R01 may consume only usage already included in the personal Pro plan. It may
not purchase credits, draw purchased or shared credits, enable Auto top-up,
fall back to API-key billing, or continue after the included plan limit is
reached.

The live subprocess environment removes secret-bearing environment-variable
names before launch so an API key cannot silently replace ChatGPT subscription
authentication. The provider-free identity preflight must still report
`Logged in using ChatGPT` immediately before the reviewed B3 command is made.

Any billing prompt, credit-purchase prompt, authentication-mode drift, account
context drift, or inability to re-establish these facts is `STOP_PHASE` before
another provider call. This attestation does not authorize a command whose
hash differs from the reviewed B3 preflight.
