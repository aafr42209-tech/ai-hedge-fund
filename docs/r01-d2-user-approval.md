# R01 D2 User Approval Record

Status: `APPROVED`

Decision gate: `D2`

Recorded date: `2026-07-16` (Asia/Seoul)

Provider calls made at recording: `0`

Development attempts spent at recording: `0`

## Verbatim approval

> D2를 승인합니다. 모델은 gpt-5.6-sol, reasoning effort는 high, service tier는 provider default로 동결합니다. timeout 900000ms, per-attempt reserve 32000, development token cap 6400000, attempt cap 200, 추가 비용 $0 조건을 승인합니다. 첫 nonzero는 즉시 STOP_PHASE, transport 실패는 attempt 2까지만 허용합니다. delta_min_e12=50000000000, target_headroom_e12=50000000000, delta_target_e12=100000000000, variance 보정 없음, high-cost stratum의 6/7 zero-gap을 그대로 수용합니다.

## Normalized decision

The unqualified opening approval accepts the complete recommendation in
`docs/r01-d2-decision-package.md`; the enumerated values freeze the variable
rows and do not amend any other row in that package.

- exact model: `gpt-5.6-sol`
- reasoning effort: `high`
- service tier: provider default; no `priority` or `fast` request
- temperature and top-p: `provider_managed_not_exposed`
- model fallback: prohibited
- transport model echo: absence accepted as an identity limitation; any
  observed mismatch is `STOP_PHASE`
- live process timeout: `900000` ms
- per-attempt total-token reserve: `32000`
- development total-token cap: `6400000`
- development provider-attempt cap: `200`
- incremental USD cap: `0`; no API key, metered overage, purchased-credit
  drawdown, automatic top-up, or other automatic billing fallback
- attempt-1 nonzero without a complete response: immediate `STOP_PHASE`
- consecutive `RETRY_TRANSPORT` failures: at most attempts 1 and 2; the second
  failure becomes `STOP_PHASE` before attempt 3
- `delta_min_e12`: `50000000000`
- `target_headroom_e12`: `50000000000`
- `delta_target_e12`: `100000000000`
- two-versus-five replicate variance correction: none; both known bias
  mechanisms remain reportable limitations
- `high_transaction_cost` stratum: accept unchanged with six of seven
  oracle-hold gaps equal to zero and carry the resulting power cost
- minimal non-tool allowlist: exactly `resize_all_images`,
  `terminal_resize_reflow`, `tool_search_always_defer_mcp_tools`, and
  `tui_app_server`, relying on the pinned exact-tag removed/no-op source proof

## Authorization boundary after approval

This record resolves decision gate D2. It does not by itself prove that a live
provider call can satisfy the approved zero-incremental-cost constraint, nor
does it substitute for the missing B3 live-run command, deterministic six-case
anchor manifest, or token reservation and actual-usage ledger.

Before the first provider process starts, preflight must establish all of the
following without consuming a provider attempt:

1. no purchased-credit balance or shared workspace credit pool can be drawn;
2. automatic credit top-up is disabled;
3. the live B3 runner, command spec, deterministic anchor manifest, and token
   ledger are implemented, hashed, reviewed, and fail closed;
4. the pinned CLI, package, native executable, feature catalog, authentication
   mode, model request, and all referenced contract identities still match.

Until those operational conditions pass, provider calls and development
attempts remain `0`. Failure to prove the zero-cost account state is
`STOP_PHASE`, not permission to spend.
