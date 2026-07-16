# R01 D2 Resource Amendment 02

Status: `APPROVED_FOR_PROVIDER_FREE_IMPLEMENTATION_ONLY`

Recorded date: `2026-07-17` (Asia/Seoul)

## Verbatim approval

> D2 Resource Amendment 02의 provider-free 구현을 승인합니다. per-attempt token reserve는 128000으로 변경하고 development token cap 12800000, development attempt cap 200, 추가 비용 $0 조건은 유지합니다. 128000 초과 시 즉시 STOP_PHASE로 중단하며 추가 자동 상향은 허용하지 않습니다. 누적 15 attempts와 339507 conservative tokens를 이월합니다. confidence를 0부터 100까지의 JSON 정수로 명시하고 소수형을 금지한 prompt v2, 새 aggregate carry·experiment identity·manifest·preflight를 provider 호출 없이 준비합니다. 이 승인은 provider 호출을 승인하지 않으며, 새 preflight의 독립 교차검증과 별도 최종 실행 승인을 요구합니다.

## Frozen implementation boundary

- Per-attempt token reserve: `128000`.
- Development token cap: `12800000`.
- Development provider-attempt cap: `200`.
- Incremental USD cap: `0`.
- A complete response above `128000` is immediate non-retryable, unscored
  `STOP_PHASE` after settlement.
- No automatic reserve or total-cap increase is authorized.
- Aggregate carried provider attempts: `15`.
- Aggregate conservative token charge: `339507`.
- Prompt v2 must require each `confidence` value to be a JSON integer in
  `[0, 100]` and explicitly reject fractional or decimal forms.
- Preparation of a new aggregate carry, experiment identity, manifest, command
  specs, and preflight must make zero provider calls.
- This document does not authorize `b3-run` or any other provider process.
- A new preflight requires independent review and a separate explicit user
  execution approval.

## Evidence basis

- Resource-v2 STOP report:
  `docs/r01-b3-resource-v2-token-reserve-stop.md`, SHA-256
  `a2adfce4a048286c132c96840668b2801b57d798bb5e5fec3e75b523f613b5a3`.
- Resource-v2 machine evidence:
  `docs/r01-b3-resource-v2-stop-evidence.json`, SHA-256
  `c0f6a084d2a151bde1aaef2b0265789ab4073655338b3a22759b7f62a0a7d41b`.
- Prior aggregate carry:
  `docs/r01-b3-aggregate-budget-carry-forward.json`, SHA-256
  `002cc7b8e726e3d5041bc1d888e2a7da15ea258aa661ff1dd17ecb9de9397953`.
- Approved resource-v2 preflight SHA-256:
  `95130a039edbd43a9c610078ce6d904beb5e038bed65e9bf0252924b3bb04bde`.
- Resource-v2 STOP failure SHA-256:
  `0ec69aa27e9316ea4506f1ca02e83bd2253c8c8b48d0328f24301344b5247127`.

The 128K reserve is a deterministic doubling of the reviewed 64K boundary, not
an adjustment to the observed `64023` value. With the carried charge and the
existing B3 maximum of 24 provider attempts, the prospective worst-case charge
is `339507 + 24 * 128000 = 3411507`, below the unchanged `12800000` development
cap. This arithmetic does not authorize a provider call.
