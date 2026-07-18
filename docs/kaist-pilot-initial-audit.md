# KAIST pilot parquet 초기 감사

작성일: 2026-07-17

데이터 경로: `data/kaist_pilot/`

## 1. Critical Evaluation

### 1.1 반입 및 Git 격리

- 원본 `kwam-report-automation/experiments/outputs/kaist_pilot` 디렉터리를
  `data/kaist_pilot/`로 이동했다.
- 이동 전후 10개 parquet의 SHA-256을 비교한 결과 missing, changed, extra가
  모두 0이었다.
- 원본 경로는 이동 후 존재하지 않는다.
- 저장소 `.gitignore`의 `data/` 규칙이 적용되며 `git check-ignore`로 확인했다.
- 기존 작업 중이던 `docs/key-paper-selection.md`,
  `docs/candidate-paper-data-inventory.md`,
  `docs/company-data-extraction-request.md`에는 손대지 않았다.

### 1.2 물리 파일과 논리 데이터셋

물리 parquet는 10개지만 논리 데이터셋은 8개다.

- ZI master/reference 6개
  - 펀드기본정보: 167,588행
  - 클래스펀드: 50,121행
  - 펀드별속성코드: 966,365행
  - 속성코드: 385행
  - 유형코드: 300행
  - 코드정보: 708행
- KOSPI200 구성종목: 146,253행
- KOSPI200 지수산출: 731행

중복 저장은 다음과 같다.

- 최상위 `kaist_kospi200_constituents.parquet`와
  `lake/incremental/kaist_kospi200_constituents.parquet`는 SHA-256까지 같은
  완전 중복 파일이다.
- 최상위 `kaist_kospi200_index_levels.parquet` 731행은
  `lake/incremental/krx_index_levels.parquet` 4,386행 중 KOSPI200 731행과
  데이터가 같다. 후자는 KOSPI, KOSDAQ, KOSPI200, KOSPI200 TR, KRX100,
  KRX300의 6개 지수를 포함한다.

중복은 분석상 오류는 아니지만, 어느 경로를 canonical source로 사용할지
고정하지 않으면 이중 집계와 불필요한 I/O가 생긴다. 본 분석에서는 최상위
KAIST deliverable 파일을 canonical source로 본다.

### 1.3 추출 형식과 metadata

- 추출 스크립트 097~099를 확인한 결과, SQL*Plus wrapper가 반환한 값을
  그대로 보존하기 위해 날짜 외 컬럼은 문자열로 저장하도록 의도되어 있다.
- 따라서 fund master의 금액·비율과 constituents의 수량·비중이 Parquet에서
  문자열인 것은 현재 추출 설계와 일치한다.
- KOSPI200 constituents의 주요 수치 문자열은 모두 숫자로 파싱 가능했다.
  단, `WEIGHT_TR`은 146,253행 전부 빈 문자열이다.
- 분석 단계에서는 raw 문자열 컬럼을 덮어쓰지 말고 별도 numeric 컬럼을
  만들어야 한다. 빈 문자열은 missing으로 처리하되 원본과 구분해 보존한다.
- 원 추출 코드는 SQL, 실행시각, 행 수, 키 중복, 기간을 담은
  `097/098/099_manifest_*.json`을 만들도록 되어 있으나 이번 반입분에는
  parquet만 있고 manifest는 없다. 재현성 metadata가 데이터와 함께 전달되지
  않은 상태다.

### 1.4 Kaniel: fund-skill ML replication

#### 확인된 강점

- `협회펀드코드`는 fund master 167,588행에서 NULL과 중복이 모두 0이다.
- 설정일은 1970-05-20~2026-07-14, 해지일이 있는 레코드는 126,528개다.
  장기 표본과 해지펀드를 식별할 기반은 있다.
- 펀드별속성코드의 `(협회펀드코드, 속성코드)` 중복은 0이며 fund master 및
  속성 codebook 조인율은 모두 100%다.
- 국내 공모 주식형의 1차 식별자로 `대유형코드=20`을 사용할 수 있다.
  사모주식형은 별도 `대유형코드=40`으로 구분된다.
- 운용전략 codebook에는 인덱스 `S104`, 정통인덱스 `S105`,
  인핸스드인덱스 `S106`, ETF `M113`이 존재한다.

#### 예비 universe

다음 보수적 규칙으로 1차 후보를 계산했다.

1. `대유형코드=20`
2. active 후보 유형은 일반주식 `2001`, 중소형주식 `20020`,
   배당주식 `20030`, 테마주식 `20040`
3. 인덱스·정통인덱스·인핸스드인덱스·ETF 속성
   `S104/S105/S106/M113` 제외
4. 설정일이 2025-12-31 이전이고, 해지일이 없거나 2023-01-01 이후여서
   2023~2025 pilot 기간과 생존기간이 겹치는 코드만 유지

결과는 5,304개 class-level fund code다.

- `해지구분=1`: 3,417개
- `해지구분=2`: 196개
- `해지구분=X`: 1,691개
- 일반주식: 3,677개
- 중소형주식: 574개
- 테마주식: 568개
- 배당주식: 485개

이 숫자는 최종 whitelist가 아니다. 특히 `해지구분=X`가 31.9%로 크므로
코드 의미를 확인하지 않고 active 또는 dead로 임의 분류하면 표본선택 편향이
생긴다. 또한 일별 국내주식 exposure가 아직 없으므로 유형코드 오분류를
검증하지 못했다.

#### share class와 모자펀드 관계

`DW_ZI_클래스펀드`는 서로 다른 두 관계를 한 테이블에 담고 있다.

- `펀드구분=1`: share-class 관계다. 특히 `설정구분=0`의 42,680개
  서브펀드는 각각 대표펀드 하나에만 연결된다.
- `펀드구분=2`: 모펀드-자펀드 관계다. `설정구분=A/B`에서는 같은
  서브펀드가 최대 23개 대표펀드에 연결되는 many-to-many 구조가 나타난다.

전체 테이블을 단순히 `서브펀드코드 → 대표펀드코드`로 축약하면 1,430개
서브코드가 복수 대표코드에 매핑되어 중복 집계된다. share-class 합산에는
`펀드구분=1` 관계만 사용하고, 모자펀드는 별도 look-through 또는 중복방지
규칙을 적용해야 한다.

예비 5,304개 코드에 `펀드구분=1, 설정구분=0`만 적용하면 4,210개 코드가
대표펀드에 매핑되고, 미매핑 코드를 자기 자신으로 두었을 때 최대 1,305개
fund group이 된다. 실제 group 수는 fund-day TNA와 관계 코드 의미를 검증한
뒤 확정해야 한다.

#### 현재 blocker

이번 반입분에는 아래 핵심 파일이 없다.

- `DW_ZI_펀드일별분석` 기반 fund-day panel
- `DW_ZI_운용사일별분석` 기반 manager/family validation panel
- 한국 Carhart factor와 sentiment series

따라서 return, TNA, flow, fund momentum, abnormal return, ML target을 아직
구축할 수 없다. 현재 데이터만으로 Kaniel 논문의 실증 구현은 불가능하고,
universe 설계까지만 가능하다.

예비 5,304개 코드를 모두 받으면 최대치는 약 388만 fund-day 행이고,
운용사-유형 pair는 148개다. 데이터 용량 자체는 문제가 아니다. 다만 회사
스크립트 100은 수천 개 코드를 `SELECT ... FROM dual UNION ALL`로 SQL에
직접 삽입한다. 5,304개 대상에서는 SQL parse 비용과 statement size가
불필요하게 커진다. DB master에 직접 join해 같은 필터를 적용하거나,
승인된 staging/GTT 방식으로 whitelist를 join하도록 바꾸는 편이 안전하다.

### 1.5 Arnott: index-rebalancing replication

#### 확인된 강점

- 기간: 2023-01-02~2025-12-30, 731거래일
- ISIN: 전부 KOSPI200 `KRD020020016`
- 예상 키 `(일자, 지수ISIN, 종목코드1)` 중복: 0
- 종목 수: 일별 200~201개
- `지수내비중` 숫자 변환 실패: 0
- 일별 비중합: 최소 99.87, 평균 99.9981, 최대 100.14

비중합의 작은 편차는 표시 정밀도 반올림 범위로 보이며 구조적 결손 증거는
없다.

2024년 membership set change는 네 번이다.

- 2024-03-15 적용: 1개 편입, 1개 편출
- 2024-06-14 적용: 6개 편입, 6개 편출
- 2024-09-30 적용: 1개 편입, 편출 없음
- 2024-12-13 적용: 4개 편입, 5개 편출

6월 14일과 12월 13일은 index-level의 `다음정기변경일` 전환과 일치하는
정기변경이다. 3월과 9월은 수시변경으로 분리해야 한다. 9월 수시편입으로
종목 수가 201개가 됐기 때문에 12월 정기변경의 편입·편출 수가 4대 5인 것은
데이터 오류가 아니다.

중요한 시점 규칙은 다음과 같다.

- constituents의 membership이 달라지는 `일자`는 효력일 전 거래일이다.
- 실제 event effective date는 같은 행의 `적용일`이다.
- 예: row date 2024-06-13의 새 membership은 2024-06-14 적용이다.

`변경여부`는 731행 중 318행에서 1이므로 단일 event flag로 쓸 수 없다.
membership set difference, `적용일`, `다음정기변경일`을 함께 사용해야 한다.

#### 현재 blocker

이번 반입분에는 다음이 없다.

- KRX announcement date/time, 정기/수시 구분, 변경사유, 공시문서
- 편입·편출 종목의 daily total return, 거래량·거래대금, 시가총액,
  bid/ask, 거래정지·상장폐지 자료

따라서 event list와 effective date는 복원할 수 있지만 announcement-to-
effective event window, abnormal return, 거래비용, index crowding 성과는
검정할 수 없다. effective date를 announcement date로 대체하면
look-ahead bias가 생기므로 허용하면 안 된다.

### 1.6 Beber: bespoke benchmark replication

**2026-07-18 갱신: Beber 30-fund pilot 실측 완료, constraint-coding gate 실패.**

`docs/company-data-extraction-request.md` §6에서 요청한 Beber 30개
whitelist에 대해 `WRDSS.DW_ZI_펀드약관한도`(270행), `DW_ZI_펀드약관투자`
(96행), `DW_ZI_펀드스타일분석`(1,030행, 2023-01~2025-12 36개월)을 실제로
받았다.

#### 통과한 부분

- 스타일 9-box 비중합이 1,030행 전부 99.9998~100.0002%로 안정적으로 100%다.
- 다만 배당형 2개 펀드(`K55303BU4033`, `KR5226496549`)는 2023년 초와 2025년
  말에만 관측되고 중간 기간 스타일분석 커버리지가 빠진다. 결격 사유는 아니나
  원인 미확인.

#### 실패한 부분 — constraint-coding gate

`약관한도` 270행을 확인한 결과, 30개 펀드 전부 예외 없이 동일한 9개
`투자대상구분코드`만 채워져 있다: `FB10/11/12`(국내주식 계열),
`FB20/21/22`(채권 계열), `FB31/32/33`(유동성자산 계열). 이전에 존재
가능성만 언급됐던 `FB41~43`(파생상품 한도), `FB53`(차입·레버리지 한도)
코드는 30개 펀드 중 단 하나에서도 나타나지 않는다.

`약관투자`(자유서술 원문) 96행을 키워드로 스캔한 결과:

| 제약 | 검색어 | 결과 |
|---|---|---|
| 차입/레버리지 | 차입금, 레버리지 | 0/30 |
| 공매도 | 공매도 | 0/30 |
| 증권대여 | 대여, 대차 | 1/30 (유동성 관리 기법 나열 중 한 줄, 수치 한도 아님) |
| 파생상품 | 파생상품, 선물, 옵션, 스왑 | 6/30 (한도가 있다는 서술뿐, 실제 %는 텍스트에 없음) |
| 회전율 | 회전율 | 0/30 |

`docs/candidate-paper-data-inventory.md` §7이 정의한 Beber 진행 조건 —
"차입·공매도·대여·회전율 중 최소 세 가지를 수치화할 수 있어야 함" — 을
이 30개 실데이터가 충족하지 못한다. 투자대상(투자유니버스) 제약과
스타일-mandate 정합성만 확인 가능하고, 원 논문의 나머지 4개 제약
(공매도·차입·증권대여·회전율)은 구조화 필드에도 자유서술 텍스트에도
사실상 존재하지 않는다.

## 2. Conclusion/Recommendation

### 2.1 판정

현재 반입분만으로 **논문 전체 구현은 불가능**하다. 다만 데이터가 잘못된
것이 아니라, 계획된 2단계 추출 중 1차분만 받은 상태다.

- **Kaniel: partial-go.** Universe와 survivorship/share-class 설계는 시작할
  수 있지만 fund-day panel 없이는 핵심 가설을 구현할 수 없다.
- **Arnott: event-definition gate 통과.** KOSPI200 정기변경 복원은 가능하다.
  announcement와 event-stock 시장자료가 없어서 성과 검정은 아직 불가능하다.
- **Beber: constraint-coding gate 실패 (2026-07-18 확정) — no-go.** 30-fund
  pilot 실측 결과 투자대상 제약만 코딩 가능하고 공매도·차입·증권대여·회전율은
  구조화 필드에도 자유서술에도 없다. `docs/candidate-paper-data-inventory.md`
  §7의 자체 진행조건("최소 세 가지 제약 수치화")을 충족하지 못했으므로, 같은
  문서 §8의 규칙에 따라 Beber용 추가 추출과 장기 표본 구축은 중단한다.

데이터 실행확실성 순위는 `Kaniel > Arnott`로 좁혀진다. Beber는 조건부 3순위
후보에서 제외됐다. 이번 반입분 자체의 즉시 구현 진척도만 보면 Arnott event
list가 Kaniel ML panel보다 더 앞서 있다.

### 2.2 다음 작업 순서

1. `해지구분=X`, `설정구분=1/2/blank`의 vendor 정의를 확인한다.
2. 5,304개 예비 후보를 review 가능한 whitelist와 exclusion-reason 파일로
   생성한다. 최종 확정 전에는 이를 논문 표본으로 부르지 않는다.
3. 회사 스크립트 100의 수천 개 `UNION ALL` target CTE를 DB master join 또는
   staging-table join으로 바꾼 뒤 fund-day와 manager-day panel을 추출한다.
4. fund-day 수령 즉시 월말 복리수익률, flow, 설정일 placeholder,
   해지펀드 보존, share-class TNA 합산을 gate test한다.
5. Arnott용 KRX announcement와 event-stock daily market data를 별도로
   확보한다.
6. manifest JSON도 parquet와 함께 다시 가져온다.
7. 위 gate 결과 뒤에 Kaniel 본 구현과 Arnott event study 중 주제를 최종
   확정한다. Beber는 constraint-coding gate 실패로 이 확정 대상에서 제외한다.
