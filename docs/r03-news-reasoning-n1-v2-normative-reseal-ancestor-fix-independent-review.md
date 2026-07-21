# R03 N1 — V2 Normative Reseal 상태전이 수정(ancestor check): 독립 검토

- 배경: 초기 승인 세트가 `c38bdc3b3fa93288a5fbb8d93c83ac4c95611445`로 커밋·push된 뒤,
  신규 verifier가 실행 시점 commit `e910991…`을 **현재 HEAD와 동일**해야 한다고 검사하여
  커밋 직후 자기 자신을 실패시키는 상태 전이 버그가 드러남
- 검토 대상: 로컬 미커밋 5파일 (evidence, zero-call-manifest, review-handoff, verifier, tamper tests)
- 검토 스크립트(스크래치패드): `review_fix.py` — 프로그램 체크 23건, **FAIL 0**

## 판정

**APPROVED — 수정 검증 완료. 5파일 stage·commit·push 진행 가능.**

## 1. 버그 재현 (보고 신뢰하지 않고 실측)

커밋된 `c38bdc3`의 verifier를 저장소 경로에서 그대로 실행:

```
VerificationError: observed execution surface mismatch   (exit 1)
```

원인 확인: 커밋 버전은 관측 execution surface를 `"execution_commit": git_head()`로 구성해
고정 pin `e910991…`과 직접 비교한다. HEAD가 `c38bdc3`으로 전진한 순간 필연적으로 불일치.
버그 진단은 정확하며, 재현도 성립.

## 2. 수정 로직 검토

```python
def execution_commit_is_ancestor(commit: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    return completed.returncode == 0
```

- `cwd=ROOT` 고정 → 호출 위치와 무관하게 대상 저장소를 평가
- `check=False` + `returncode == 0` → 오류(128 등)는 전부 False로 떨어져 **fail-closed**
- 커밋이 자기 자신의 조상이므로 커밋 전 상태에서도 그대로 통과 (게이트 약화 없음)
- 파일 해시 pin 6종은 종전대로 별도 검사되므로, 조상 판정 완화가 드리프트 탐지를 약화시키지 않음

### 술어 자체를 직접 가동 (신규 테스트가 monkeypatch로 우회하는 부분)

| 입력 | 기대 | 결과 |
|---|---|---|
| `e9109913…` (실제 조상) | True | True |
| 현재 HEAD `c38bdc3…` | True (자기조상) | True |
| 존재하지 않는 sha `000…0` | False | False |
| 형식 위반 `not-a-sha` | False | False |
| 실제 non-ancestor 커밋 `9ddec9b8…` | False | **False** |

즉 저장소 상태에 대한 실제 판정이 정상 동작함을 확인.

## 3. 봉인값 / 불변성

| 항목 | 값 | 결과 |
|---|---|---|
| Evidence canonical (신규) | `a170b0bd…2d6b` | 재계산 일치 |
| Manifest filesystem (신규) | `37ea72d5…5f14` | 일치 |
| Handoff filesystem (신규) | `7453eccf…a4c1` | 일치 |
| Verifier filesystem (신규) | `49995cff…2d9e` | 일치 |
| Lineage canonical | `8f3b3f0c…a719` | **불변** |
| Attestation canonical | `44002b7a…59f6` | **불변** |

- 정본 수치 불변: `1,515,387,041 / 1,585,976,846 = 95.55`
- raw targeted result 불변: canonical `797a960e…`, filesystem `67214163…`,
  disposition `COMPLETED_TARGETED_LEDGER_REVIEW_REQUIRED_NO_VALUE_RESEALED`
- evidence↔lineage/attestation 결속 유지, `artifact_sha256` 전 항목 디스크 실측 일치
  (수정된 verifier 자신도 pin됨)
- attestation의 `execution_commit`은 여전히 `e910991…` — HEAD로 다시 쓰지 **않음**.
  이것이 이번 수정의 핵심 의미(실행 시점 보존)이며 올바름

## 4. 게이트 재실행

| 게이트 | 결과 |
|---|---|
| 신규 reseal verifier (수정본) | exit 0 |
| 기존 verifier 3종 | exit 0 |
| tamper 테스트 파일 | **20 passed** |
| `pytest -k r03` | **155 passed** |
| black `--check` / isort `--check-only` | clean |
| `git diff --check` | clean |
| staging / upstream | 0 / `0 0` |

작업 트리는 검토 후 원상(수정 5파일)으로 복구됨 — 재현용 임시 파일 제거 확인.

## 5. 관찰 사항 (비차단)

- **LOW-1 — 실패 메시지 분해능.** 비조상 판정을 `execution_commit`에 `""`를 대입해
  최종 dict 비교로 흘려보내므로, 조상 위반과 파일 해시 드리프트가 **같은 메시지**
  (`observed execution surface mismatch`)로 보고된다. 진단 비용이 커지므로
  전용 메시지(예: `execution commit is not an ancestor of HEAD`) 분리 권고.
- **LOW-2 — 신규 회귀 테스트의 범위.** `test_execution_commit_must_be_an_ancestor_of_current_head`는
  `execution_commit_is_ancestor`를 monkeypatch로 False 고정한다. 즉 **소비 측**은 검증하지만
  git 술어 자체는 검증하지 않는다. 본 검토에서 술어를 직접 가동해 5케이스를 확인했으므로
  현 시점 리스크는 없으나, 술어 단위 케이스(존재하지 않는 sha → False)를 테스트에 추가 권고.
- **LOW-3 (이월)** — flake8 설정 부재로 무설정 실행 시 E501 발생. 기존 수락분과 동일 수준이며
  회귀 아님. 별도 chore로 `.flake8`(`max-line-length = 420`) 추가 권고.

## 6. 권고

1. 5파일 **stage·commit·push 진행**. 차단 사유 없음
2. 커밋 메시지에 상태 전이 버그와 수정 성격(equality → ancestor)을 명시하고,
   신규 evidence canonical `a170b0bd…`를 기록할 것
3. LOW-1/LOW-2는 후속 chore로 처리 가능 (본 수정 승인과 무관)
