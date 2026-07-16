# R01 D2 Resource Amendment 01

Status: `APPROVED`

Decision gate: `D2_RESOURCE_AMENDMENT_01`

Recorded date: `2026-07-16` (Asia/Seoul)

Provider attempts spent at recording: `4`

Conservative development-token charge at recording: `103623`

## Verbatim approval

> D2 자원 한도 amendment를 승인합니다. per-attempt token reserve는 64000, development token cap은 12800000으로 변경하고 development attempt cap 200과 추가 비용 $0 조건은 유지합니다. 64000을 초과하면 즉시 STOP_PHASE로 중단하며 추가 자동 상향은 허용하지 않습니다. 누적 4 attempts와 103623 conservative tokens를 이월합니다. 다음 provider 호출 전 aggregate carry-forward, 새 실험 identity·manifest·preflight와 독립 교차검증을 요구합니다.

## Frozen amendment

- Per-attempt total-token reserve: `64000`.
- Development total-token cap: `12800000`.
- Development provider-attempt cap: `200` unchanged.
- Incremental USD cap: `0` unchanged.
- A complete response above `64000` is settled for accounting, persisted as a
  post-response `STOP_PHASE`, and authorizes no later attempt.
- No automatic reserve or total-cap increase is permitted.
- Aggregate carry starts from four provider attempts and `103623`
  conservatively charged tokens.
- The prior `32000` reserve remains historical identity for ordinals 1 through
  4; it is not rewritten under the amendment.

## Authorization boundary

This amendment authorizes provider-free implementation, testing, aggregate
carry-forward construction, a new experiment identity and manifest, and a new
zero-call preflight. It does not authorize `b3-run` or another provider call.

Before any provider process starts, the new implementation commit and preflight
SHA-256 must be independently reviewed and explicitly approved by the user.
