# R02 D3 live-gate provider-free authorization

Status: `PROVIDER_FREE_IMPLEMENTATION_ONLY`

Authorization date: `2026-07-17`

Accepted D3 freeze commit:
`87da1d77d734d4687df40d5b2b561ea2fde7cc18`

The user approved the next sequential gate after accepting the D3 provider-free
freeze. This authorization is conservatively limited to an append-only,
provider-free freeze candidate for the six live prerequisites identified by
independent review:

1. an externally supplied Codex executable SHA-256 pin;
2. exact source pins for selector, R02 contracts, and token transport parsing;
3. an unambiguous micro-pilot-to-full continuation rule;
4. exact token measurement and settlement rules;
5. fail-closed ppm floor and attempt-cap precedence;
6. duplicate reason-code handling when the output schema lacks `uniqueItems`.

This authorization permits local hashing, schema generation, append-only local
artifacts, replay, offline tests, and a review handoff. It does not authorize a
provider call, `codex exec` without `--help`, live execution, a micro-pilot, the
remaining full evaluation, or any investment or utility claim.

Future live authorization must cite the accepted live-gate freeze identity and
must explicitly accept that, absent a registered hard stop after the six-case
micro-pilot, the remaining 49 eligible cases continue without a discretionary
pause or second approval.
