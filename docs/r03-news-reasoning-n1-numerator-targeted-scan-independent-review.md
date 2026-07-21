# R03 N1 — Numerator Targeted Scan Result v1: 독립 검토

- 검토 대상: `.research_artifacts/r03-news-reasoning/numerator-targeted-scan-result-v1.json`
- Permit: `numerator-targeted-scan-permit-v1.json` (`93bbaaf0…a4b8`)
- 실행 커밋 pin: `e9109913a2cf198e63f5fbd116abc91c58fc6ee2` (현재 HEAD 일치)
- 검토 방식: repo 모듈 **미임포트**. canonical JSON 직렬화·ledger 회계 불변식·파생 집계를 선언된 semantics로부터 stdlib만으로 재구현하여 대조
- 검토 스크립트(세션 스크래치패드, 산출물 아님):
  `independent_review_targeted_scan.py`, `rule_search.py`

## 판정

**APPROVED — 결과 아티팩트는 검증됨.**
단, 봉인값 provenance는 **여전히 미성립**. 정본 상태 `UNRESOLVED_NO_VALUE_RESEALED` 유지가 정당하며,
reseal 게이트는 계속 닫혀 있어야 함.

## 1. 신원·계보 (독립 재계산)

| 항목 | 값 | 결과 |
|---|---|---|
| result filesystem sha256 | `67214163…2aaa` | 일치 |
| result canonical sha256 (재계산) | `797a960e…8045` | 일치 |
| evidence canonical sha256 | `06a059b1…4109` | 일치 |
| ledger multiset sha256 | `43029119…6f75` | 일치 |
| permit self-hash | `93bbaaf0…a4b8` | 일치 |
| 직전 승인 rerun result 해시 | `6046eab6…65eb` = permit.accepted_result_sha256 | 일치 |
| paired evidence 해시 | `4669d706…7bdf` = permit.accepted_paired_evidence | 일치 |

## 2. Ledger 무결성 (664행 전수)

- `affected_frame_count` = `len(ledgers)` = **664** = permit 기대치 = `diagnostics.session_cap_affected_frames`
- 필드 집합 정확, 전 값 non-bool `int`, 자유 텍스트 필드 없음
- 정렬: `_ledger_key`(필드 **선언 순서**) 기준 canonical 정렬 확인. 중복행 0 → multiset 해시 순서 안정
- 프레임별 회계 불변식 전수 통과: appearance 분할, retained appearance 분할, zero-byte 상한,
  omitted/zero-byte trigger의 byte 금지, 컴포넌트 합 = retained, retained ≤ source, retained ≤ 131,072
- 분포: 622/664가 정확히 세션 캡 131,072, 최소 130,721 — session-cap 선별 의미와 정합

## 3. 산술 폐쇄성

파생 집계 6종 전부 ledger로부터 재계산 일치. 전역 항등식이 **바이트 단위로 정확히** 닫힘:

```
unaffected 1,428,361,110 + affected(V2) 87,025,931 = 1,515,387,041  (reconciliation retained)
unaffected 1,428,361,110 + sealed_implied  7,381,768 = 1,435,742,878  (sealed retained)
gap = 1,515,387,041 − 1,435,742,878 = 87,025,931 − 7,381,768 = 79,644,163
affected 분해: hs+trigger 6,725,808 + preceding content 80,300,123 = 87,025,931
잔여 계수분: 80,300,123 − 79,644,163 = 7,381,768 − 6,725,808 = 655,960
```

컴포넌트 내역: preceding headline 2,361,376 / summary 2,612,883 / content 80,300,123 / trigger 1,751,549.

→ **numerator 차이는 affected frame의 preceding-content 처리로 완전히 국소화됨.** 사용자 보고 수치와 일치.

## 4. 적대적 검증 — 봉인값 재현 규칙 탐색

봉인 암시값 7,381,768을 만드는 규칙을 능동적으로 탐색했고, **찾지 못함**:

- 6개 byte 컴포넌트의 부분집합 합 규칙 63종 전수 → 정확 일치 **0건**
- 프레임별 retained 상한 X 해 탐색 → 해 없음. 최근접 X=11,117에서 7,382,352 (**+584** 초과)
- preceding content에만 상한 X 적용 → 해 없음
- 잔여 655,960을 통째 프레임 content 합으로 설명 → 해당 프레임 0개, 최소 content 108,830,
  최소 5프레임 합 560,506 ≠ 655,960 → whole-frame prefix 설명 불성립

선언된 후보 5종의 signed gap도 전부 비영:
`hs_all −2,254,786` / `prec_h+trig −3,268,843` / `prec_hs+trig −655,960` / `prec_s+trig −3,017,336` / `trigger_only −5,630,219`.

→ 봉인값은 **재현 가능한 규칙이 확인되지 않은 상태**. fail-closed 유지가 옳음.

## 5. 봉쇄·부작용

- `inventory` / `source_counts` / `reconciliation_retention` / `diagnostics`: 승인된 rerun 결과와 **완전 동일**
- 실행 카운터: `completed_raw_source_scans = 1`, 그 외 12개 전부 0 (network/provider/model/fixture/oos 등)
- Raw-text 방출: 결과 내 문자열 leaf 19개 전부 해시·열거형·식별자 형태. 자유 텍스트 0
- `disposition = COMPLETED_TARGETED_LEDGER_REVIEW_REQUIRED_NO_VALUE_RESEALED`,
  `commit_gate = CLOSED_PENDING_INDEPENDENT_TARGETED_RESULT_REVIEW`
- 아티팩트는 git ignore 대상, staging 비어 있음, reseal 없음

## 6. 관찰 사항 (비차단)

- **O1 (MEDIUM)** — 결과에 `execution_surface` 블록이 없음. runner는 관측 해시를 permit과 대조하지만
  결과 아티팩트는 "무엇이 실행됐는지"를 자체 증언하지 않는다. 사후 검토자는 permit + 디스크 현재 상태를
  신뢰해야 함. 본 검토에서 module/runner/base-runner 파일 해시가 permit pin과 현재 일치함을 확인했고
  HEAD도 `execution_commit`과 일치하나, 향후 스키마에 실행표면 기록 추가 권고.
- **O2 (LOW)** — 결과 파일이 CRLF로 기록됨. filesystem sha256은 플랫폼 의존이며 Linux 재실행 시 달라진다.
  canonical 해시만 계약값으로 인용하고 filesystem 해시는 로컬 사본 식별자로 취급할 것.
- **O3 (LOW)** — `total_news_positive_frames = 151,820`은 `full_frames_total`(retained 아님)과 같다.
  분모 의미상 옳지만 이름이 오독을 부른다. 영향 프레임 비율은 664/151,820 = 0.437%.

## 7. 봉인값 생성 코드의 복구 가능성 (검토 중 추가 확인)

권고를 정하기 위해 "구 census 규칙을 코드로 되찾을 수 있는가"를 조사했고, **불가**로 확인:

- `1,435,742,878`은 외부 legacy 수치가 아니라 **최초 data check 실행 결과**
  (`read-only-data-check.json`, `r03-read-only-data-check-v1`, implementation_commit `4c47ec6`)
- 해당 아티팩트는 자기 자신을 이미 `COMPLETED_FAIL_CLOSED_N1_TEXT_RETENTION_MISMATCH`로 선언
  (`text_byte_retention_pct_exact 90.53` vs `expected 97.03`)
- 같은 아티팩트가 자체 HIGH 결함을 기록: `R03_PUBLIC_RETENTION_DENOMINATOR_CONFLATION`
- git 이력상 `1435742878`이 등장하는 커밋은 봉인 커밋 `e910991` 하나뿐. 생성 커밋 없음
- `4c47ec6` 시점 `public_retention`(당시 `r03_source.py` 소재)은 **행 단순 합산**에 불과.
  판별 로직(어떤 appearance를 어떤 바이트로 계수하는가)은 전부 **드라이버 쪽**에 있었음
- 그 v1 드라이버는 `.gitignore:71` `.research_artifacts/`로 미추적이며 v2 드라이버로 덮어써짐.
  `__pycache__`에도 v2 `.pyc`만 잔존 → **v1 생성 코드는 소실**

## 8. 다음 관문 권고

1. 정본 상태 `UNRESOLVED_NO_VALUE_RESEALED` 유지 — 본 검토는 이를 바꾸지 않음
2. 봉인값은 후속 판단에서 **입력으로 사용 금지**
3. **권고: (b) 개정 경로.** (a)는 권고하지 않음
   - **(a) 구 census 규칙 탐색 — 비권고.** 읽을 코드가 남아 있지 않으므로 (a)는
     "코드에서 규칙을 복원"이 아니라 "655,960을 맞히는 규칙을 사후 적합"으로 퇴화한다.
     §4에서 자연스러운 집계 규칙 전수가 이미 실패했으므로, 적합에 성공하는 규칙은 필연적으로
     인위적이며 "실제로 그 규칙이 돌았다"는 독립 증거를 가질 수 없다.
     이는 R02 D3에서 이미 겪은 post-hoc 과적합 실패 양식과 동일하다.
   - **(b) 봉인값 폐기 + V2 정본 승격 — 권고.** V2 측정은 semantics id·구현 해시로 완전 명세되어
     있고 독립 재검증이 2회(rerun, 본 targeted scan) 성립했으며 전역 항등식이 바이트 단위로 닫힌다.
     반면 폐기 대상은 **자기 자신이 FAIL_CLOSED로 선언하고 자체 HIGH 결함까지 기록한 최초 관측치**로,
     계약 지위를 가진 적이 없다. 증거를 잃는 것이 아니라 부적합 판정이 이미 붙은 산출물을 정리하는 것.
   - **(c) 동결 — 차선.** R03 retention 관련 하류 주장이 미해결 seal에 계속 묶인다.
4. (b) 진행 시 개정 문서가 남겨야 할 것: provenance를 추적했고 **복구 불가로 종결**했다는 기록
   (본 검토 §4·§7이 그 근거), 그리고 V2 수치는 구 수치에 *reconcile된 것이 아니라 대체한다*는 명시
