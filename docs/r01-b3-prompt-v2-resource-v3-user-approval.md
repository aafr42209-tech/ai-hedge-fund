# R01 B3 Prompt-v2/Resource-v3 User Approval Record

Status: `APPROVED`

Decision: prompt-v2/resource-v3 replacement B3 live micro-pilot

Recorded date: `2026-07-17` (Asia/Seoul)

Provider attempts spent at recording: `15`

Conservative development-token charge at recording: `339507`

## Verbatim approval

> 사용자도 b3-run 실행을 승인함.

The approval immediately follows the independent cross-review conclusion that
the exact `1f65106` implementation commit plus
`5937161ac9c2bb9c22172d0be27a5a730cc2a3dc1c8bf51044270b65ee68353e`
preflight pair passed all seven review questions without running `b3-run` or
making a provider call.

## Authorization boundary

- Approved implementation commit: `1f65106`.
- Approved preflight SHA-256:
  `5937161ac9c2bb9c22172d0be27a5a730cc2a3dc1c8bf51044270b65ee68353e`.
- Approved experiment ID: `r01-b3-prompt-v2-resource-v3-20260717`.
- Approved planned acquisitions: `12`.
- Approved maximum new provider attempts: `24`.
- Carried global provider attempts: `15`.
- Carried conservative token charge: `339507`.
- Per-attempt token reserve: `128000`.
- Development token cap: `12800000`.
- Development provider-attempt cap: `200`.
- Incremental USD cap: `0`.
- A response above `128000` is detected after token settlement and becomes
  immediate non-retryable, unscored `STOP_PHASE`; no automatic upward amendment
  or follow-up call is authorized.
- Any login, account, executable, feature, sandbox, manifest, command-spec,
  carry, amendment, or preflight drift stops before the next provider process.
- Any other fail-closed condition stops the phase and authorizes no further
  provider attempt under this approval.

The approved review scope is `90f0406..7a83805`. The independent reviewer
recomputed the preflight SHA, complete 53-file artifact graph, carry chain,
bound source hashes, executable hash, prompt-v2 command specs, empty sandbox,
and provider-call count. This approval-record commit changes documentation only
and does not change the reviewed implementation or preflight pair.
