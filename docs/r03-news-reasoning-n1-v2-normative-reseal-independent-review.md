# R03 N1 — V2 Normative Reseal: 독립 검토

- 검토 대상: `r03-news-reasoning-n1-v2-normative-reseal-{lineage,attestation,evidence,zero-call-manifest}.json`,
  `…-review-handoff.md`, `scripts/r03_news_reasoning_v2_normative_reseal_verify.py`,
  `tests/test_r03_v2_normative_reseal_verify.py`
- 상태: `V2_NORMATIVE_RESEALED_PENDING_INDEPENDENT_REVIEW`
- HEAD: `e9109913a2cf198e63f5fbd116abc91c58fc6ee2` (변경 없음), staging 0
- 검토 방식: repo 모듈 미임포트. canonical 직렬화를 stdlib로 재구현해 5개 봉인값을 재계산하고,
  선언된 게이트(verifier 4종·pytest·black·git diff --check)를 **직접 재실행**
- 검토 스크립트(스크래치패드, 산출물 아님): `review_reseal.py` — 프로그램 체크 48건

## 판정

**APPROVED — reseal 세트 검증 완료. commit/push 진행 가능.**
직전 검토의 MEDIUM 관찰(O1 execution surface 미기록)은 해소됨. 차단 사유 없음.

## 1. 봉인값 독립 재계산 (5/5 일치)

| 대상 | 값 | 결과 |
|---|---|---|
| Lineage canonical | `8f3b3f0c…a719` | 일치 |
| Attestation canonical | `44002b7a…59f6` | 일치 |
| Evidence canonical | `fab57196…ac29` | 일치 |
| Manifest filesystem | `3147d55a…8db0` | 일치 |
| Handoff filesystem | `0b0a39d4…49cd` | 일치 |

각 아티팩트의 자체 `*_sha256` 필드도 재계산과 일치. 체인 결속 확인:
attestation→lineage, evidence→lineage, evidence→attestation 전부 정합.
`evidence.artifact_sha256` 맵 6개 항목 전부 디스크 실측과 일치(본 검토자의 직전 검토 문서 pin 포함).

## 2. 정본 수치

- `1,515,387,041 / 1,585,976,846`, ROUND_HALF_EVEN 2dp → **95.55** 재계산 일치
- normative retention 블록이 승인된 rerun 결과·targeted 결과의 retention 블록과 **완전 동일**
  (수치를 새로 만든 것이 아니라 이미 독립 재현된 블록을 승격)
- 간극 회계 승계 확인: `v2_minus_legacy = 79,644,163`, `unexplained preceding content = 655,960`,
  `1,515,387,041 − 1,435,742,878 = 79,644,163` 정확

## 3. REPLACE_NOT_RECONCILE 이행

- legacy 아티팩트 byte-for-byte 보존: filesystem `1a725db6…`, canonical(unsigned) `24423b02…` 모두 일치.
  `1,435,742,878`과 `90.53`이 원본에 그대로 남아 있음
- legacy 상태·HIGH 결함이 attestation에 그대로 전재:
  `COMPLETED_FAIL_CLOSED_N1_TEXT_RETENTION_MISMATCH`, `R03_PUBLIC_RETENTION_DENOMINATOR_CONFLATION`
- `action = REPLACE_NOT_RECONCILE`, `legacy_value_status = HISTORICAL_NON_NORMATIVE_UNREPRODUCIBLE`,
  `legacy_value_forbidden_as_future_decision_input = true`,
  `lost_v1_driver_recovery = CLOSED_UNRECOVERABLE`, `post_hoc_fit_to_655960_forbidden = true`
- 선행 계보(P5-era amendment, reconciliation)의 supersede pin 6종도 unsigned canonical 규약으로 재계산 일치.
  즉 97.03(P5-era article-cap-only) → 90.53(legacy fail) → 95.55(정본) 세 수치의 계보가 모두 pin되어 있음

## 4. raw 결과 불변 / 범위 봉쇄

- targeted raw result: canonical `797a960e…`, filesystem `67214163…` 모두 직전 검토 시점과 동일.
  `disposition`도 `COMPLETED_TARGETED_LEDGER_REVIEW_REQUIRED_NO_VALUE_RESEALED` 그대로 (재봉인 없음)
- attestation의 result pin 4종이 라이브 아티팩트와 일치
- 현 범위 카운터 전부 0: raw traversal/copy, commit, push, network, provider, model fit, gate 등
- 신규 아티팩트에 자유 텍스트 누출 없음 (긴 문자열은 verification command 1건, manifest statement 1건뿐)

## 5. 직전 MEDIUM 관찰 해소

attestation에 `execution_surface` 블록 신설: `execution_commit` + 파일 해시 6종.
`execution_commit`이 현재 HEAD와 일치하고, 대조 가능한 pin 3종(targeted module, targeted runner,
base runner)이 디스크 실측과 일치. **O1 해소로 판단.**
직전 LOW(O2)도 `filesystem_hashes_are_review_session_anchors: true` 선언으로 주장 범위가 올바르게 한정됨.

## 6. 게이트 재실행 (보고 신뢰하지 않고 직접 수행)

| 게이트 | 결과 |
|---|---|
| 신규 reseal verifier | `PASS_R03_N1_V2_NORMATIVE_RESEAL` (exit 0) |
| 기존 verifier 3종 | exit 0 |
| `pytest -k r03` | **154 passed** |
| `black --check` (신규 2파일) | unchanged |
| `git diff --check` | clean |
| staging / HEAD | 0 / `e9109913` 불변 |

적대적 테스트는 **재서명(re-signed) tamper** 형태 — 변조 후 해시를 다시 맞춘 입력에도 실패하도록
설계되어 있어 자기일관성만 보는 검증기로는 통과할 수 없다. 커버: ledger partition, multiset ordering,
frame-count semantic alias, evidence artifact pin, nonzero scope counters, lineage/attestation semantic tamper.

## 7. 관찰 사항 (비차단)

- **LOW-1 — lint 주장 재현 불가.** 저장소에 flake8 설정 파일이 없어(`pyproject`의 `line-length = 420`은
  black 전용) 무설정 `flake8`은 기본 79열을 적용하며 신규 2파일에서 E501이 발생한다. 단, **이미 수락된
  기존 verifier도 동일하게 위반**하므로 회귀가 아니라 저장소 관례 문제다. 커밋 메시지에 "flake8 통과"를
  적으려면 실제 사용한 인자를 함께 고정하거나 `.flake8`에 `max-line-length = 420`을 추가할 것.
- **LOW-2 — 파일시스템 해시의 플랫폼 의존성.** manifest/handoff pin은 CRLF 포함 로컬 앵커다.
  evidence가 이를 명시적으로 선언하고 있으므로 문제는 없으나, 인용 시 canonical 값을 우선할 것.

## 8. 권고

1. 현 상태로 **commit/push 진행**. 차단 사유 없음
2. 커밋 메시지에는 정본 canonical 3종(lineage/attestation/evidence)과 `95.55` 정본 수치,
   그리고 `REPLACE_NOT_RECONCILE`을 명시할 것
3. LOW-1은 별도 chore로 `.flake8` 추가 권고 (본 봉인과 무관하게 처리 가능)
