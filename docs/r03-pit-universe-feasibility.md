# R03 PIT universe 복원 가능성 조사

**상태:** feasibility 결과 / 독립 기술 검토 전 / 실행 승인 아님  
**기준일:** 2026-07-19  
**범위:** 공개 문서 열람과 로컬 read-only 집계만. universe 변경, 데이터 수집·구매, 구현, 커밋은 범위 밖이다.

## 1. 결론

판정은 다음과 같다.

1. **2016–2025 S&P 100 membership의 복원은 조건부로 가능하다.** OEF의 SEC 공시에서 2016Q1–2025Q4 분기말 40/40을 찾았고, S&P DJI 공개 변경 공지는 발표일과 발효일의 근거가 될 수 있다. 그러나 OEF 공시만으로는 분기 중 변경시점을 알 수 없고, OEF가 representative sampling을 쓰므로 펀드 holdings를 지수 membership과 동일시할 수 없다.
2. **정확한 일별 PIT ledger의 acceptance 경로는 아직 닫히지 않았다.** 최선은 S&P DJI 공식 historical constituent/change product의 schema·coverage·권리를 견적과 sample로 확인하는 것이다. 대안은 권한 있는 Compustat `idxcst_his`의 from/thru coverage를 확인하고 S&P 공지와 EDGAR 40개 분기말로 대조하는 것이다. 완전 무료 경로는 가능성이 높지만, 모든 분기 중 공지의 완전성을 입증해야 한다.
3. **membership보다 더 큰 제약은 데이터 공백이다.** 2016-01-01부터 2026-01-01까지 11개 annual revision snapshot의 관측 union은 134 ticker labels다. 2026-06-30 로컬 100-symbol panel과 비교하면 historical-only label이 39개다. annual snapshot이 놓치는 intrayear round trip을 감안한 운영 계획치는 distinct 134–136+, gap 39–41+다. 이들에 대한 전용 뉴스 manifests와 완전한 bars가 현재 자산에 없다.
4. **membership-only 교집합은 endpoint를 정상화하지 못한다.** 미래 편입종목을 편입 전 날짜에서 제거하는 개선은 있지만, 이탈·합병·상장폐지 종목을 누락한 survivor conditioning, 왜곡된 sector benchmark와 cross-sectional rank가 남는다.
5. **정식 권고는 옵션 (d), model pin 후 prospective PIT 설계다.** 현행 2016–2025 결과는 옵션 (c) survivor-panel exploratory로 보존하고, membership ledger가 검증되면 옵션 (b)를 secondary sensitivity로만 추가할 수 있다. 옵션 (a)는 최소 39-label backfill의 coverage·권리·비용과 delisting/corporate-action 처리가 입증될 때만 재개한다.

중요하게, **survivorship와 model training-cutoff는 독립 장벽**이다. 옵션 (a)가 universe 문제를 완전히 해결해도 charter §4와 prereg §8의 cutoff 조건을 만족하지 않는 현대 모델의 2016–2025 결과는 confirmatory T3가 될 수 없다.

## 2. 판정 기준

정상 PIT membership ledger는 최소 다음 필드를 가져야 한다.

`issuer_id, security_id, action, announcement_timestamp_et, effective_after_close_date, first_in_index_session, source_url, source_sha256`

`announcement_timestamp_et`와 `effective_after_close_date`는 합치지 않는다. 합병·분할·spin-off로 trading line이 잠시 늘거나 바뀌는 경우에는 company membership과 security-line membership을 별도로 보존한다. acceptance 기준은 다음과 같다.

- 2016-01-01 직전 anchor와 2025-12-31까지 모든 add/drop을 설명한다.
- 40개 분기말 OEF 상태를 모두 reconcile한다. 현금·선물·temporary line은 사전 규칙으로 제외한다.
- 각 add/drop에는 S&P 공식 근거가 하나 이상 있거나, licensed official history와 일치해야 한다.
- unmatched constituent와 설명되지 않는 interval gap은 0이다.
- ticker/name/share-class 변경은 permanent security/issuer ID로 연결한다.
- source URL, retrieval time, raw-source hash와 canonical ledger hash를 보존한다.

## 3. PIT constituent 소스 후보

| 후보 | 2016–2025 coverage | 발표일 vs 발효일 PIT | 라이선스·비용 | 검증 가능성 및 판정 |
|---|---|---|---|---|
| **S&P DJI 공식** | S&P 100 현행 page·methodology·공개 change notices는 확인. historical event product의 전체 기간·필드는 계약 전 sample 필요 | 사건별 공지는 게시일과 별도 effective date를 담는다. 가장 권위 있는 원천. S&P 100 전용 notice SLA는 공개 methodology에서 확인하지 못했으므로 실제 게시시각을 사건별 저장 | constituent/weights/corporate-events data는 proprietary product. 공개 정가 없음. **quote, research-use, derived-output, redistribution 권리 확인 필요** | conditional best source. 공식 event history를 primary로 하고 EDGAR·permanent IDs로 reconcile |
| **OEF + SEC EDGAR** | 2016Q1–2025Q4 **40/40 quarter ends 발견**. 2016–2018 N-Q/주주보고서, 2019 transition forms, 2020–2025 NPORT-P/주주보고서 | holdings as-of와 filing date는 정확하지만 index announcement/effective date가 아니다. 분기 중 변경은 interval-censored | SEC/EDGAR 공개 접근 $0. SEC fair-access, declared user agent, 10 requests/s 이하 준수. 이번 조사는 두 sample과 filing metadata만 열람 | 강한 독립 quarter-end anchor. OEF는 representative sampling이며 cash·futures·잔여 line 가능. **단독 primary source 불가** |
| **Compustat / WRDS** | 공개 catalog에 historical index-constituent table `idxcst_his`가 있으나 login 필요. S&P 100 code·from/thru·전체 기간은 sample query 전 미확인 | from/thru가 있으면 effective interval 후보. announcement field는 확인되지 않음 | institution/vendor entitlement. 공개 정가 없음. S&P DJI constituent names/add-drop 사용에 별도 direct license가 필요할 수 있음. **quote/contract 필요** | entitlement가 있으면 공식 공지 + EDGAR와 3-way check. 현재는 conditional |
| **CRSP** | US Stock DB는 active/inactive securities와 long history를 제공하지만 공개 catalog에서 S&P 100 membership product는 확인하지 못함 | membership 원천보다는 PERMNO/PERMCO, historical CUSIP/ticker, delisting·merger continuity에 적합 | academic/institutional license. 공개 정가 없음 | 단독 membership 근거 아님. Compustat/S&P ledger의 identity·return validator로 유용 |
| **Wikipedia revision history** | 2016–2025 각 연도 revision 존재. 현재 로컬 universe도 고정 oldid에 provenance를 둠 | revision timestamp는 편집시각이지 발표일/발효일이 아니다. 지연편집·오류·vandalism·누락 가능 | $0. text 재사용은 CC BY-SA 4.0/GFDL의 attribution/share-alike 준수 | candidate discovery와 anomaly check 전용. primary 금지 |
| **Wayback Machine** | OEF product page에 2016–2025 전 연도 capture metadata가 존재 | capture time은 crawl time. 동적 holdings/API/XLS가 capture에 포함되지 않을 수 있고 발표/발효시점이 아님 | 조회 $0. archive 접근은 underlying S&P/BlackRock content의 재사용 license를 부여하지 않음 | 사라진 공지나 당시 page state 보조. primary 금지 |

추천 교차검증 순서는 다음과 같다.

1. **최상:** S&P official event history/change notices → daily membership intervals → OEF 40 quarter ends reconcile → CRSP/Compustat permanent-ID mapping.
2. **학술 라이선스 경로:** Compustat `idxcst_his` schema/coverage 확인 → S&P 공개 공지 spot/checksum audit → EDGAR 40/40 reconciliation.
3. **완전 무료 경로:** EDGAR quarterly anchors + 모든 S&P 공개 공지의 완전성 감사 + Wikipedia/Wayback anomaly search. 하나라도 설명되지 않는 분기 중 변화가 있으면 exact PIT acceptance 실패다.

OEF 40/40은 **filing discovery completeness**이지 holdings 40개 전수 parse 완료를 뜻하지 않는다. 대표 sample은 [2016-12-31 N-Q](https://www.sec.gov/Archives/edgar/data/1100663/000119312517065125/d346678dnq.htm)와 [2024-06-30 NPORT holdings](https://www.sec.gov/Archives/edgar/data/1100663/000175272424191829/251704BR063024.htm)이다. SEC의 [N-PORT reporting 설명](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/investment-company-reporting-modernization-rules)은 public quarter-end 정보와 60일 제출 구조를 설명한다. OEF 자체 보고서는 representative sampling 때문에 모든 index security를 보유하지 않을 수 있다고 명시한다.

## 4. 데이터 공백 정량화

### 4.1 로컬 기준선

검증된 FinGPT 자산은 2016–2025, 100 ticker × 10 years의 1,000/1,000 complete manifests다. declared captures는 436,916건이고, R03 canonical eligibility를 만족하는 것은 247,976 unique articles와 301,541 ticker-article events다. eligible text coverage는 headline 100%, summary 29.33%, body 50.90%, headline-only 49.10%다.

이 census의 eligibility는 `at least one symbol in frozen 100-name universe`를 포함한다. 따라서 이 수치는 PIT 전체 universe의 completeness 증거가 아니며, 2026 panel 밖 종목의 missingness를 측정하지도 않는다. price bars도 같은 survivor panel/window에 한정된다.

### 4.2 turnover와 distinct-member 추정

공식 공지 검색 결과만으로 turnover를 세면 누락 위험이 컸다. 따라서 운영 규모는 [Wikipedia S&P 100 revision history](https://en.wikipedia.org/w/index.php?title=S%26P_100&action=history)의 매년 1월 1일 직전 고정 revision 11개를 코드로 비교해 추정했다. 이는 공개 archive 관측치이며 official PIT ledger가 아니다.

| annual transition | 2016→17 | 2017→18 | 2018→19 | 2019→20 | 2020→21 | 2021→22 | 2022→23 | 2023→24 | 2024→25 | 2025→26 | 합계 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gross added ticker labels | 11 | 2 | 3 | 4 | 4 | 3 | 3 | 1 | 1 | 4 | **36** |

- 각 snapshot의 security-line count: `100, 102, 102, 102, 101, 101, 101, 101, 101, 101, 101`.
- 11개 snapshot union: **134 distinct ticker labels**. 이 값은 파싱된 표에 대해서는 exact이고, 실제 2016–2025 window에 대해서는 **lower bound**다.
- gross additions 36, removals 35, 연평균 gross additions **3.6 labels/year**.
- baseline과 gross turnover를 이용한 planning envelope는 **134–136 labels**지만 hard upper bound가 아니다. annual boundary 사이에서 편입·이탈한 round trip은 두 snapshot 모두에서 빠질 수 있어 실제 수는 136을 넘을 수 있다.
- ticker labels에는 `FB/META`, `PCLN/BKNG`, `BK/BNY` 같은 rename과 `GOOG/GOOGL`, `FOX/FOXA` 같은 share classes가 섞인다. exact issuer count와 security-line count는 permanent-ID crosswalk 후 별도로 확정해야 한다.

### 4.3 2026 survivor panel과의 차집합

2026-06-30 로컬 100-symbol panel과 annual-snapshot ticker-label union을 비교하면 다음이 나온다.

- historical union ∩ local panel: **95 ticker labels**.
- historical union에 있으나 local panel에 없는 label: **39 observed**.
- local panel에만 있는 label: `AMAT, BNY, GEV, LRCX, MU` 5개. `BNY`는 과거 `BK`의 rename이므로 issuer gap과 query-label gap이 다름을 보여준다.
- annual-boundary 누락을 감안한 운영 gap 계획치는 **39–41+ labels**다.

39개 observed historical-only labels는 다음과 같다.

`AGN, AIG, ALL, APA, APC, BAX, BIIB, BK, CELG, CHTR, DD, DOW, DVN, DWDP, EBAY, EMC, EXC, F, FB, FCX, FOX, FOXA, HAL, HON, KHC, KMI, MET, MON, NOV, NSC, OXY, PCLN, PYPL, RTN, SLB, TGT, TWX, UTX, WBA`

이 수치는 **재수집해야 할 article 수나 issuer 수가 아니라, 전용 manifest와 bars가 없는 old/query-label 규모**다. successor/current-symbol page에 cross-symbol article이 일부 들어 있을 수 있으므로 실제 missing article count는 합법적 backfill 전 metadata-only preflight로 다시 측정해야 한다.

annual snapshot exposure를 합치면 historical-only 39 labels가 약 **199 ticker-years**를 차지한다. 기존 corpus 평균을 단순 비례하면 raw captures 약 **86,946**, eligible ticker-events 약 **60,007**, 저장량 약 **0.531 GB**다. 이는 news intensity, multi-symbol duplicates, alias와 partial-year membership을 무시한 planning proxy일 뿐 coverage 예측이나 구매 견적이 아니다.

### 4.4 Alpaca 뉴스·bars backfill 가능성

[Alpaca Historical News](https://docs.alpaca.markets/us/docs/historical-news-data)는 2015년부터의 데이터를 문서화하고 현재 공급원을 Benzinga로 밝힌다. 따라서 시간 범위상 2016–2025 former members를 질의할 가능성은 있다. 그러나 다음 이유로 coverage는 아직 **미입증**이다.

- delisted/acquired predecessor symbol의 검색과 historical symbol alias 동작을 공개 문서만으로 보장할 수 없다.
- 평균 130+ articles/day라는 전체 feed 설명은 특정 former ticker의 completeness 보장이 아니다.
- 기존 local manifests와 동일한 article schema, pagination, corrections, `created_at/updated_at`, source-symbol behavior를 preflight해야 한다.
- 별도 news backfill 정가는 검토한 공개 페이지에서 찾지 못했다. [market-data plan](https://docs.alpaca.markets/us/docs/about-market-data-api)은 Basic $0/month, Algo Trader Plus $99/month와 2016 이후 stock history를 표시하지만, 이는 news entitlement와 complete all-exchange bars 권리를 자동 보장하지 않는다.
- [Alpaca public support](https://alpaca.markets/support/redistribute-alpaca-api)는 API data redistribution을 허용하지 않는다고 명시한다. 내부 research retention, model-input, derived-output, publication 권리는 실제 계약과 Benzinga third-party terms를 별도 검토해야 한다.

따라서 옵션 (a)의 비용은 단순히 `39 × 10 ticker-years`가 아니다. 관측 exposure proxy는 199 ticker-years이고, 최소 39 old-symbol queries, alias/predecessor queries, delisting-inclusive adjusted bars, corporate-action mapping, completeness audit, storage/compute와 계약 검토를 포함한다. 구매나 API probe를 하지 않았으므로 정확한 기사 수·요청 수·총비용은 이 보고서에서 산정하지 않는다.

### 4.5 ticker·합병·share-class mapping

raw ticker equality는 허용할 수 없다. 예시는 다음과 같다.

- 동일 issuer rename: `FB → META`.
- merger/spin lineage: `UTX → RTX`와 `OTIS/CARR`, `DWDP → DOW/DD/CTVA`.
- acquired predecessors: `AGN → ABBV`, `CELG → BMY`, `APC → OXY`, `RTN`과 UTX/RTX 결합.
- multiple share classes/vendor notation: `GOOG/GOOGL`, `FOXA/FOX`, `BRK.B/BRK-B`.

필수 crosswalk는 effective-dated `issuer_id ↔ security_id ↔ CUSIP/PERMNO ↔ vendor symbol` 구조여야 한다. membership은 issuer와 security line을 분리하고, news는 source-symbol과 intersecting issuer를 모두 기록한다. bars는 split·special distribution·merger consideration·delisting return을 포함해야 한다. ticker string을 현재 이름으로 소급 치환하면 look-ahead와 가짜 missingness가 동시에 생긴다.

## 5. endpoint 승격 옵션

| 옵션 | 성립 조건 | 얻는 것 | 잔여 한계 | 판정 |
|---|---|---|---|---|
| **(a) 완전 PIT: membership + news + bars** | every decision-date membership, 최소 39 old-label/alias news coverage, predecessor/delisted bars, sector history, permanent-ID crosswalk, full-frame census와 negative tests | survivorship로 인한 endpoint 강등을 해제할 수 있음 | model-cutoff 장벽은 별도. archive/provider missingness, delisting return, mapping error와 라이선스 비용 잔존 | **조건부 가능, 현재 미성립** |
| **(b) PIT membership, data는 survivor 교집합** | validated membership ledger 후 `U_PIT(t) ∩ U_available`로 frame 재산출 | 미래 편입 전 노출 제거, membership timing 일부 개선 | exit·M&A·delisting survivor conditioning, sector/universe median·clip·z-score·rank 왜곡, opportunity set 축소, coverage missingness가 exit와 상관 | **secondary sensitivity만; 승격 불가** |
| **(c) 현행 survivor panel** | sealed design과 기존 census 유지 | 비용·권리 변화 없이 재현 가능 | estimand는 “2026 survivor panel에 소급한 capability test”. historical S&P 100 일반화·confirmatory 주장 불가 | **historical baseline 유지** |
| **(d) prospective PIT** | model/schema/universe rule을 첫 평가 뉴스 전에 pin; decision-time snapshot, entrants/exits, alias와 same-contract news/bars를 지속 수집 | cutoff와 survivorship 두 장벽을 함께 피하는 가장 깨끗한 future primary/confirmatory 경로 | 기다림, future data rights·운영·label maturation 필요. 2016–2025 historical 질문은 정상화하지 않음 | **권고** |

옵션 (b)에서 특히 남는 bias는 단순 “표본 수 감소”가 아니다. charter §12.3의 sector-relative outcome, sector/universe median imputation, cross-sectional clipping/demeaning/z-score, top/bottom selection과 `<20 valid names => no trade`가 모두 선택된 survivor 교집합에서 다시 계산된다. 이 결과는 actual PIT S&P 100의 factor, benchmark, portfolio 또는 turnover가 아니다.

## 6. 권고안

**공식 권고: 옵션 (d)를 승격 경로로 채택한다.** 이유는 다음과 같다.

- 옵션 (a)는 membership ledger보다 최소 39 old-label 뉴스·bars, delisting/corporate actions와 이용권이 병목이며 현재 완전성·가격·권리가 미확인이다.
- 옵션 (b)는 cheap robustness check지만 survivor conditioning을 제거하지 못하므로 primary 정상화라는 목표에 맞지 않는다.
- 옵션 (c)는 sealed historical evidence를 정직하게 보존한다.
- 옵션 (d)는 prereg §8-2가 이미 예정한 경로이며, model pin 이후 들어오는 data에 decision-time universe를 저장해 cutoff와 survivorship를 동시에 통제할 수 있다.

운영 순서는 `historical (c) 유지 → validated membership이 생기면 (b) secondary 추가 → prospective (d)를 별도 primary로 preregister`다. 이것은 여러 옵션을 공동 primary로 추천하는 것이 아니다. **승격 recommendation은 (d) 하나**이며, (b)/(c)는 historical evidence의 보존·감도분석 역할이다.

옵션 (a)는 다음 stop/go gate를 모두 통과할 때만 다시 평가한다.

1. official/Compustat membership sample이 2016–2025와 announcement/effective 요구를 충족한다.
2. 39 observed historical-only labels와 추가 intrayear candidates의 metadata-only coverage preflight가 기존 contract와 비교 가능하다.
3. predecessor/delisted bars에 delisting·merger returns가 포함된다.
4. Alpaca/Benzinga 및 price-data 계약이 local research retention과 intended model use를 서면 허용한다.
5. full-frame census, source hashes와 independent review가 완료된다.

## 7. 채택 시 문서 수정 범위

이번 작업은 봉인 문서를 수정하지 않는다. 옵션 (d)를 별도 승인 후 채택하면 다음 범위가 필요하다.

### Charter

- **§4:** 2016–2025 survivor exploratory와 future prospective primary를 명시적으로 분리한다. PIT universe만으로 historical model-cutoff가 해결되지 않음을 유지한다.
- **§9-4:** prospective universe provenance, announcement/effective separation, model/schema pin과 fail-closed rule을 결정 항목으로 추가한다.
- **§12.1:** 기존 2016–2025 survivor decision frame을 덮어쓰지 않고 별도 prospective frame을 둔다. 각 decision time의 membership snapshot과 effective-date source를 고정한다.
- **§12.2:** entrant news eligibility, source-symbol/issuer intersection, alias handling과 identical T2/T3 payload를 prospective universe에 맞춘다.
- **§12.3:** sector/universe transforms, valid-name gate, ranks, phase books와 turnover를 당시 PIT cross-section으로 정의한다.

### Preregistration

- **§3:** prospective start, model/schema pin time, label maturation, one-shot evaluation topology를 추가한다.
- **§8-2:** “pin 후 prospective”를 membership snapshot cadence, effective-session rule, entrant/departure ingestion SLA와 연결한다.
- **§10:** future data collection의 provider/license/retention 권한을 별도 승인 gate로 둔다.
- **§14.1:** PIT membership, announcement/effective provenance, alias와 eligibility contract를 추가한다.
- **§14.3:** dynamic PIT cross-section의 imputation·standardization·portfolio 규칙을 고정한다.

새 schema/source hashes, coverage census, failure fixtures와 독립 기술 검토로 P5 seal을 다시 만들어야 한다. 이 보고서는 그 수정을 승인하지 않는다.

## 8. 공개 근거와 한계

주요 공개 근거는 [S&P 100 page](https://www.spglobal.com/spdji/en/indices/equity/sp-100/), [S&P U.S. Indices Methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf), [S&P Index Data capabilities](https://www.spglobal.com/spdji/en/documents/index-policies/index-data-capabilities-brochure.pdf), [OEF product page](https://www.ishares.com/us/products/239723/ishares-sp-100-etf), [SEC EDGAR access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data), [WRDS historical identifiers](https://wrds-www.wharton.upenn.edu/pages/wrds-research/database-linking-matrix/using-compustat-historical-identifier-notebook/), [CRSP US Stock Databases](https://www.crsp.org/products/research-products/crsp-us-stock-databases/), [Wikipedia revision history](https://en.wikipedia.org/w/index.php?title=S%26P_100&action=history), [Wikimedia Terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), [Wayback API](https://archive.org/help/wayback_api.php), Alpaca news/plan/redistribution 문서다.

상세 URL 목록, local-input hashes, revision oldids, counts와 zero-action record는 companion evidence JSON에 있다. 공개 search 결과의 부재를 계약상 부재로 해석하지 않았고, 공개 가격이 없는 상품은 모두 `quote required`로 표시했다. 수치 134·39·199는 annual snapshot 기반 관측/계획 수치이며 licensed constituent file을 대체하지 않는다.

## 9. 독립 검토 체크리스트

- 11개 annual revision의 table parsing을 재현하고, 17개 현재 발견된 official announcement URL을 seed로 전체 event ledger의 완전성을 감사한다.
- OEF 40 quarter ends 각각에서 cleaned equity holdings를 계산하고 event ledger와 대조한다.
- company count, stock-line count, dual-class count를 별도로 보고한다.
- 39-label list를 permanent IDs로 재구축하고 FB/META, PCLN/BKNG, BK/BNY 등 alias를 issuer gap과 분리한다.
- Compustat `idxcst_his` 또는 S&P official sample의 S&P 100 index code, from/thru semantics, announcement field와 라이선스를 확인한다.
- option (b)의 intersection frame에서 sector/rank/no-trade 변화량을 raw text 없이 count-only로 산출한다.
- option (d) 수정안이 historical P5 seal을 덮어쓰지 않고 새 prospective seal을 만드는지 확인한다.

## 10. SHA-256 pins와 zero-call 선언

- `report_prefix_sha256` (UTF-8 bytes; 본문 끝의 단일 `\n`은 포함하고 `## 10` 헤더 앞 공백행은 제외): `60f8757e1b2a94633828a2cd067811fb8ab28d1ddd357370341b1d8d0b701ecb`
- `docs/r03-pit-universe-feasibility-evidence.json` full-file SHA-256: `4797ab56e451432ed82aa0f9155dbb8ceee426451736490a17aa9f8b062c24bf`
- local input hashes: companion evidence JSON `local_inputs`에 고정.

Zero-action declaration:

- external provider/LLM calls: **0**
- data purchases/subscriptions: **0**
- bulk downloads or collection jobs: **0**
- news original text copied/quoted into repo: **0**
- FinGPT writes: **0**
- universe or implementation changes: **0**
- commits/pushes: **0 / 0**

공개 웹 문서·metadata·두 sample SEC filing의 열람은 위 provider/LLM call 수에 포함되지 않는다. 이 보고서는 조사 산출물이며 universe 변경, backfill, provider probe, 구현 또는 실행을 승인하지 않는다.

## 11. 독립 기술 검토 기록 (2026-07-19)

- 검토자: Claude (Fable 5), same-session lineage — 기술 검증이며 조직적 독립 검토 아님.
- **로컬 검증 전부 통과:**
  - evidence full-file SHA (`4797ab56…`) 일치; `report_prefix_sha256` (`60f8757e…`)
    는 "본문 끝 단일 `\n` 포함, `## 10` 헤더 앞 공백행 제외" 경계로 정확 일치;
    `local_inputs` 7건(봉인된 R03 P5 문서 5건 + feasibility handoff + FinGPT
    `universe.json`) 전부 재계산 일치; **P5 seal 무결(5/5) 재확인**.
  - 산술 10건 전부 일치: 134 = 95 + 39; 100 = 95 + 5; gross additions
    합 36; net +1 = 36 − 35 = 마지막(101) − 처음(100); 비례 proxy 3종은
    코퍼스 평균 × 199 ticker-years와 자릿수까지 정확(86,946 / 60,007 /
    0.531 GB); 11 snapshots / 10 transitions; 공지 URL 17건; 39-label
    목록 길이 39.
  - zero-action 선언 전 항목 0; 신규 산출물 2건 외 워크트리 변화 없음.
- **검토 범위 한계 (검증 불가 항목의 명시):** Wikipedia 11개 revision의
  parsing(134/39의 원천)과 EDGAR 40/40 filing discovery는 웹 원천 재조회
  없이는 독립 재현 불가 — 본 검토에서는 재현하지 않았다. 단, oldid 11건과
  filing URL이 pin되어 있고 §9 체크리스트가 이를 후속 감사 항목으로 이미
  포함하므로 record는 재현 가능하다.
- **내용 판단:** 소스 비교표의 라이선스 판정(공개 부재 ≠ 계약상 부재,
  `quote required` 표기)은 보수적으로 정확. label ≠ issuer 구분(FB/META,
  BK/BNY, GOOG/GOOGL)과 crosswalk 요구는 타당. 옵션 (b)의 잔여 bias 열거
  (sector transform·rank·no-trade gate가 교집합에서 재계산되는 문제)는
  정확하며 "secondary sensitivity만" 판정을 지지한다. **권고 (d)는 prereg
  §8-2와 정합하는 유일한 cutoff+survivorship 동시 통제 경로로 타당**;
  (a)의 5-gate 재개 조건과 §7의 문서 수정 범위(봉인 미접촉, 신규
  prospective seal)도 적절하다.
- 비차단 발견: **1건 (LOW)** — `report_prefix_sha256`의 경계 서술("`## 10`
  header 직전까지")이 공백행 처리에 모호함; 실제 규약(본문 + 단일 개행)을
  §10에 명시할 것. 차단 발견: **0**.
- 판정: **`ACCEPTED_WITH_NONBLOCKING_FINDINGS`**. 이 수락은 universe 변경,
  backfill, provider probe, 데이터 구매, 구현, commit, push를 승인하지
  않는다. 옵션 (d)의 채택 및 §7 수정 범위 착수는 별도 사용자 승인 사항이다.
