# R01 B3 Resource-v2 User Approval Record

Status: `APPROVED`

Decision: amended-resource replacement B3 live micro-pilot

Recorded date: `2026-07-17` (Asia/Seoul)

Provider attempts spent at recording: `4`

Conservative development-token charge at recording: `103623`

## Verbatim approval

> 코드 커밋 f403e1a와 B3 preflight SHA 95130a039edbd43a9c610078ce6d904beb5e038bed65e9bf0252924b3bb04bde 쌍을 최종 승인합니다. 누적 4 attempts와 103623 conservative tokens를 이월한 상태에서 r01-b3-prompt-v1-resource-v2-20260716 micro-pilot 12건, 최대 24 provider attempts 실행을 승인합니다. per-attempt reserve 64000, development token cap 12800000, attempt cap 200, 추가 비용 $0 조건을 유지합니다. 64000 초과 또는 다른 fail-closed 조건이 발생하면 즉시 중단하며 자동 상향을 허용하지 않습니다.

## Authorization boundary

- Approved implementation commit: `f403e1a`.
- Approved preflight SHA-256:
  `95130a039edbd43a9c610078ce6d904beb5e038bed65e9bf0252924b3bb04bde`.
- Approved experiment ID: `r01-b3-prompt-v1-resource-v2-20260716`.
- Approved planned acquisitions: `12`.
- Approved maximum new provider attempts: `24`.
- Carried global provider attempts: `4`.
- Carried conservative token charge: `103623`.
- Per-attempt token reserve: `64000`.
- Development token cap: `12800000`.
- Development provider-attempt cap: `200`.
- Incremental USD cap: `0`.
- A response above `64000` is detected after token settlement and becomes
  immediate non-retryable, unscored `STOP_PHASE`; no automatic upward amendment
  or follow-up call is authorized.
- Any login, account, executable, feature, sandbox, manifest, command-spec,
  carry, amendment, or preflight drift stops before the next provider process.

The approval follows independent review of `49a27bd..807dc97`, which reported
all six resource-v2 review questions passed without running `b3-run` or making
a provider call. The approved review pair remains `f403e1a` plus the exact
preflight SHA above; this approval-record commit changes documentation only.
