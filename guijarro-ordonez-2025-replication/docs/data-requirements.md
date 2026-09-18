# 데이터 요구사항과 현재 gap

## 판정

Kimchi Factor 직접 산출의 규범은 저장소 루트
`docs/kimchi-factor-methodology.md`다. 아래의 기존 팩터 builder는 그 방법론이
확정되기 전에 만든 broad-universe proxy이므로 exact 결과로 사용하지 않는다.

현재 데이터는 **2015년 이후 PCA residual pilot에는 부분적으로 사용 가능**하지만,
원 논문의 Fama–French/PCA/IPCA 전체 replication에는 부족하다. 특히 IPCA는
240개월 rolling window가 필요하므로 FY 2016 이후 재무자료로는 구조적으로
실행할 수 없다.

| 입력 | 원 논문 계약 | 현재 보유 | 판정 |
|---|---|---|---|
| 일별 주식 total return | 1978–2016 CRSP, residual 1998–2016 | 2015–2026 `adjusted_prices.parquet`; 현금배당 제외 확인 | 기간 부족, 논문 total return은 미충족 |
| 전월 말 시가총액 | 전체 시장의 0.01% 초과 universe | `종가 × 유통주식수` 재계산·저장값 전 행 검증 | 주식수 명칭·시점 차이 audit 필요 |
| PIT security master | 상장·상폐·코드변경·corporate action | 2018-01~2026-06 월말 FGSC 시장·산업·SPAC 스냅샷 | Kimchi 리밸런싱에는 사용 가능, 논문 일별 master는 부족 |
| 일별 무위험수익률 | 1개월 T-bill | ECOS CD(91일) 일별 원자료 확보; 252일 복리 환산 검증 | 한국 Kimchi 방법론의 2015년 이후 입력 확보 |
| 일별 FF factor | 1/3/5/8 factor, MOM·STREV·LTREV | 2018년 이후 strict RM/RF/SMB/HML/RMW/CMA/MOM 및 과거 proxy LTR/STR | strict 5-factor+MOM 가능, strict FF8은 미완성 |
| PCA 입력 | 252일 covariance, 60일 loading | 일별 return 존재 | gate 통과 후 pilot 가능 |
| IPCA history | 월별 46개 특성, 240개월 window | 재무 FY 2016–2026 | 기간 부족 |
| 재무 PIT | 당시 공시된 값과 revision vintage | 실제 공시일 없음, 복수 dump revision | 사용자 지정 3개월 lag sensitivity만 허용; exact PIT는 blocked |
| 46개 characteristic | 수익률·투자·수익성·무형·가치·마찰 46개 | 46열 builder 및 427,076 종목-월 산출; 3개월 lag와 median-rank imputation | Spread·Beta 계열·CF·NI는 문서화된 proxy, exact 아님 |
| 거래비용 | turnover 5bp + short holding 1bp | 거래량·거래대금만 존재 | 논문 단순비용은 설정 가능, 실측 검증 불가 |
| investability | 종목별 shortability·borrow cost·market impact | 전용 자료 없음 | 한국 extension blocked |

## 이미 재사용 가능한 파일

- `data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet`
  - 8,651,872행, 4,962종목, 2015-01-02~2026-07-20
  - `return`, `market_cap`, 거래량, 거래대금 및 수정가격 필드
  - 원본 `date`는 세션 날짜이지 관측 가능 시각이 아니다. 일별 종가의 `available_at`은
    `Asia/Seoul` 현지시각 기준으로 **2016-08-01 전에는 15:00, 그날부터는 15:30**을
    사용한다. KRX는 2016-08-01에 증권시장 정규장을 30분 연장했다
    ([KRX 2016 brochure](https://global.krx.co.kr/contents/GLB/01/0107/0107010000/20170630_eng_brochure.pdf),
    [현재 KRX 규정의 09:00~15:30](https://regulation.krx.co.kr/contents/RGL/03/03020401/RGL03020401.jsp)).
    전 기간에 15:30을 적용하면 2015~2016-07 관측치를 실제보다 30분 늦게 공개된 것으로
    기록한다.
  - timezone을 붙일 때 UTC epoch를 재표시하는 cast를 쓰지 않는다. 예를 들어
    `2015-01-02 15:00` 현지 wall time은 `2015-01-02 15:00+09:00`이어야 하며,
    `2015-01-03 00:00+09:00`이 아니다. 전체 변환 전에 이 알려진 한 행을
    `Asia/Seoul -> UTC -> Asia/Seoul`로 round-trip하여 날짜, 시각, offset을 검증한다.
- `fng_statement_facts/`
  - 22개 partition, 39,307,271행, FY 2016~2026
  - 실제 공시시각이 없어 exact PIT characteristic에는 바로 사용할 수 없음
- 일·연간 주식수, 배당 항목, 시점별 산업분류
- `data/kimchi-factor/`
  - 2016-08-08~2026-08-07 일별 RM·RF·RMRF·SMB·HML·RMW·CMA·MOM
  - characteristic factor별 2×3 구성 포트폴리오와 quintile 수익률 포함
- `data/kaist_pilot/canonical/guijarro_2025/fng/raw/fgsc_market_rebalance_snapshots_201801_202606.csv`
  - 월말 102개 날짜, 224,779행, `(date,ticker)` 중복 0
  - KOSPI/KOSDAQ, FGSC 금융업 및 DB 내부 SPAC 판정

## ECOS 무위험수익률 검증

- 공식 통계표: `817Y002` 시장금리(일별)
- 항목: `010502000` CD(91일)
- 단위·주기: 연 %, 일별
- 저장 원자료: `data/kaist_pilot/canonical/guijarro_2025/ecos/raw/rf_cd_91d_daily_20150101_20260720.json`
- 실제 수록 구간: 2015-01-02~2026-07-20, 2,844건, 중복일 0건, 숫자 결측 0건

Kimchi RF와 겹치는 2,438일을 비교하면
`(1 + annual_percent / 100)^(1/252) - 1`의 평균절대오차는
`2.15e-17`, 최대 절대오차는 `9.91e-17`이다. 부동소수점 반올림 수준에서
일치하므로 일간 RF 변환 규칙은 확정했다. `annual_percent / 100 / 252`의 단순
나눗셈은 같은 자료와 일치하지 않으므로 사용하지 않는다.

## 3개월 lag proxy 팩터 sensitivity

`run.py build-factors-proxy --allow-non-pit-statements`는 연차 연결재무제표의
주주자본, 영업이익, 총자산을 사용한다. 회계연도 말에 3개월을 더한 날짜 이후에만
해당 값을 허용하고, 6월 말 size/characteristic 2×3 포트폴리오를 만든다.
HML은 book-to-market, RMW는 operating profit/book equity, CMA는 총자산 성장률,
MOM은 직전 2~12개월 누적수익률을 사용한다.

이 규칙은 사용 가능 시점을 보수적으로 이동시키지만, 2026년에 수집된 최신
재무 dump가 과거 정정 전 값을 복원하지는 못한다. 따라서 이 결과로
`historical_statement_announcement_times_available` gate를 통과시켜서는 안 된다.

또한 이 proxy는 KOSPI/KOSDAQ 보통주 PIT universe, SPAC 구간, 금융업 필터,
KOSPI-only breakpoint, KOSPI RM, EBITDA-이자비용 수익성 및 VW/EW·일간/월간
동시 산출 계약을 충족하지 않는다.

## 사용자에게 필요한 데이터 확인 순서

### Gate A — PCA pilot 시작 전 필수

1. 사건별 배당락일·DPS가 있는 total-return 원천 확보 (`return`은 현금배당 제외로 확인)
2. `market_cap` 계산에 사용된 주식수가 총발행주식수인지 유동주식수인지
3. 상장폐지 종목의 마지막 수익률 및 상장폐지수익률 포함 여부
4. 역사적 보통주/우선주·SPAC·REIT 구분과 종목코드 변경 mapping
5. 일별 한국 무위험수익률 또는 월별 91일물 proxy의 사전 고정 변환 규칙

이 다섯 항목이 확인되면 2016년 이후 PCA residual pilot을 먼저 실행할 수 있다.

### Gate B — Fama–French branch

1. 월말 FGSC 밖의 상장폐지·코드변경까지 포함하는 완전한 PIT security master
2. ECOS KOSPI price index보다 높은 정밀도의 공식 원지수 계열
3. 현금배당을 포함하는 사건별 total-return 원천
4. 실제 공시·정정일이 있는 연결 재무 vintage
5. 1980~1994년 정기예금금리의 ECOS 통계표·항목·만기 정의

### Gate C — IPCA exact branch

1. 최소 20년 이상의 survivorship-free 월별 주식 panel
2. 실제 공시일·정정일이 있는 재무제표 vintage
3. 논문 Table A.I의 46개 characteristic builder는 구현됨. 다만 exact 원천이 없는 proxy와 raw 결측 coverage를 해소해야 함
4. 일별 bid-ask spread와 turnover 정의
5. 금융업 재무제표 테이블 (아래 회계 coverage 진단 참조)
6. FY 2011~2015 연결·별도 재무제표 (아래 회계 coverage 진단 참조)
7. 위 1~6을 DataGuide Excel로 직접 받을 때의 계정명·아이템코드 목록은 아래
   `DataGuide 추출 목록 — IPCA 46 characteristics` 참조

## 회계 characteristic coverage 진단

2026-08-24 측정. 기준을 명확히 한다. `characteristic_audit.json`의 `coverage`는
raw 패널 전체(4,962종목·139개월) 기준이고, IPCA가 실제로 추정하는 것은 시가총액
0.01% 필터를 통과한 유니버스다. 아래 숫자는 후자 기준이다.

2023년 추정 유니버스 1,102종목에서 `BEME` 결측 원인 분해:

| 원인 | 종목 | 조치 |
|---|---:|---|
| 커버됨 (연결 전용 파이프라인) | 785 (71.2%) | — |
| 별도 재무제표만 제출 | +101 → 886 (80.4%) | **코드로 해결 완료** |
| 금융업: 추출본에 부재 | 48 | **추가 추출 필요** |
| 우선주 등 비보통주 | 18 | **코드로 해결 완료** |
| SPAC·신규상장·희소 공시 | 150 | 대부분 불가피 |

시가총액 밴드를 좁혀도 개선되지 않는다. 2020~2025년 `BEME` coverage는 상위
100종목에서 0.777, 상위 300종목 0.762, 상위 500종목 0.747, 전체 0.744다. 즉
소형주 문제가 아니라 원천의 구조적 문제다.

### 해결된 부분: 연결/별도 account code 체계

FnGuide는 연결을 `DW_FNG_연결재무제표`의 `4001NNNNNN`, 별도를
`DW_FNG_재무제표`의 `1001NNNNNN`으로 발행한다. 뒤 6자리가 공유되므로 23개 항목
중 21개에 쌍둥이 코드가 존재한다. 예외는 별도 재무제표에 정의상 존재하지 않는
`noncontrolling_interest`(0으로 처리)와 별도 계정과목에 없는
`deferred_tax`(소비하는 두 산식 모두 결측을 0으로 처리)다.

`--allow-separate-scope`와 `--common-share-class-only`를 적용하면 2019년 이후
추정 유니버스 coverage가 다음과 같이 개선된다.

| characteristic 군 | 개선 전 | 개선 후 |
|---|---:|---:|
| `BEME`·`A2ME`·`Q`·`Lev`·`AT`·`D2A` | 0.741 | 0.829 |
| `Investment`·`NOA`·`DPI2A`·`RNA`·`AC`·`OA` | 0.701 | 0.801 |
| `C`·`CF2P`·`E2P` | 0.711 | 0.799 |
| `ROA`·`ROE`·`CF` | 0.675 | 0.772 |
| `PROF`·`OP`·`OL`·`PCM` | 0.655 | 0.734 |

가격 characteristic은 최대 0.002 감소하며, 이는 우선주 제거로 횡단면이 바뀐
결과다. 회귀는 없다.

### 남은 추출 요청 1 — 금융업 재무제표

`fng_statement_facts`에는 은행·보험·증권의 재무제표가 아예 없다. 확인된 예:
`A000400` 롯데손해보험, `A000540` 흥국화재, `A323410` 카카오뱅크. FnGuide는
금융업 재무제표를 별도 테이블로 관리하므로 해당 원천이 필요하다. 필요 항목은
현재 `IPCA_ACCOUNT_CODES`와 동일한 23개 표준 항목이며, 금융업 계정과목 체계의
대응 코드표가 함께 필요하다.

대안으로 금융업을 명시적으로 제외할 수 있다. book-to-market 기반 연구에서
금융업 제외는 확립된 관행이므로 논문에서 방어 가능하다. 다만 조용히 결측으로
두는 현재 상태는 두 선택지 중 어느 것도 아니므로 반드시 하나를 택해야 한다.

### 남은 추출 요청 2 — FY 2011~2015 재무제표

현재 statement 원천은 FY 2016에서 시작한다. 여기에 3개월 lag와 특성 산식의
`shift(1)` 연쇄가 겹쳐 사용 가능 시점이 단계적으로 밀린다.

| characteristic | 필요한 과거 연도 | 최초 사용 가능 |
|---|---:|---|
| `BEME`·`AT`·`Lev` | 당해만 | 2017년 |
| `Investment`·`OA`·`NOA` | 1년 lag | 2018년 |
| `ROA`·`PROF`·`E2P` | 2년 lag | 2019년 |

11.5년 패널 중 4년이 구조적으로 비어 있다. FY 2011~2015를 확보하면 이 4년이
살아나고, 240개월 exact IPCA blocker도 함께 완화된다. K-IFRS가 2011년에
도입되었으므로 2011년 이후는 계정 정의 일관성을 확보할 수 있다. 그 이전
K-GAAP 구간은 계정 정의가 달라 별도 검토가 필요하다.

요청 형식은 현재 `fng_statement_facts`와 동일한 partition 구조
(`statement_scope`, `fiscal_year`)와 컬럼 스키마를 유지하면 코드 변경 없이
연결된다.

### 남은 gap 3 — 배당

`D2P`는 개선 후에도 0.242에 머문다. `fng_dividend_items.parquet`에 280종목만
수록되어 있기 때문이다. 전체 상장종목의 연간 현금배당총액 계열이 필요하다.

### Gate D — 한국 investability extension

1. 종목별·일별 공매도 가능 여부
2. 대차 가능수량·잔고·borrow fee
3. 거래세, 수수료, spread와 ADV 기반 market-impact 입력
4. 공매도 금지기간과 종목별 제한 이력

## DataGuide 추출 목록 — IPCA 46 characteristics

2026-09-17 정리. 원 저자 공개 코드
`Deep_Learning_Statistical_Arbitrage_Code/factor_models/ipca.py`는 characteristic을
직접 계산하지 않는다. `characteristics-replication.csv`에 `yy, mm, date, permno,
ret` 뒤로 46개 열이 미리 계산되어 들어오고, `factor_models/utils.py`의
`preprocess_monthly_chars_dlap`가 월별 횡단면 rank를 `[-0.5, 0.5]`로 바꾸며,
시가총액은 열 index 19(`LME`)로 0.01% universe filter에만 쓴다. 코드가 요구하는
입력은 결국 두 파일이다.

1. 월별 panel: 월 수익률 `ret` + 46개 characteristic (Gamma 추정과 beta 계산)
2. 일별 panel: 일 수익률 − 일 무위험수익률 (OOS residual 계산)

46개 변수의 원천 계정은 Chen-Pelger-Zhu Appendix 정의를 따라 우리가 만들어야
하고, 그 산식은 `src/guijarro_ordonez_replication/characteristics.py`에 이미
구현되어 있다. 아래 목록은 그 builder의 입력 항목(`IPCA_ACCOUNT_CODES` 23개 +
주식수·배당 + 일별 주가)을 DataGuide 계정명으로 옮긴 것이다.

DataGuide 계정명과 아이템코드는 회사 mapping
`data/kaist_pilot/metadata/mappings/korean_equity/dataguide_statement_mapping.parquet`
(IFRS 연결·연간 기준, `(천원)` 접미사까지 DataGuide 표기 그대로)에서 가져왔다.
주가·주식수·배당·호가 항목은 이 mapping에 없으므로 DataGuide 아이템 검색에서
확인해야 하는 후보명으로 적고 `확인` 표시를 붙였다.

### 추출 조건

- 유니버스: KOSPI·KOSDAQ 전체 보통주. **상장폐지 종목을 반드시 포함**한다.
  현재 상장 종목만 받으면 survivorship bias가 생긴다. 우선주는 재무제표가 없으므로
  받아도 쓰지 않는다.
- 기간: 주가는 2000-01부터, 재무는 **FY1998부터**. `Investment`·`OA`·`NOA`는 1년,
  `ROA`·`PROF`·`E2P`는 2년 lag 연쇄가 있어 재무 시작연도보다 2년 뒤부터
  characteristic이 생긴다. 원문 240개월 window와 1998년 OOS 시작을 그대로 두면
  한국은 2000-01 시작 시 첫 OOS가 2020-01이므로, window 길이는 별도로 정해야 한다.
- 재무 기준: **IFRS 연결 연간**을 주로 쓰고, 연결이 없는 기업은 IFRS 별도 연간으로
  대체한다. 2010년 이전은 K-IFRS 연결이 없으므로 **GAAP 개별 연간**을 같은 계정명으로
  한 벌 더 받는다. DataGuide는 세 체계를 다른 아이템으로 제공하므로 같은 계정명을
  IFRS연결·IFRS별도·GAAP개별 세 벌로 받아야 한다. 현재 loader의 연결→별도 fallback에
  GAAP scope를 하나 더 붙이면 된다.
- 주기: 재무는 연간(결산월 기준, 결산기 변경 기업은 달력연도 내 마지막 결산),
  주가·거래·호가는 일간, 주식수·배당은 연간과 월말.
- 시점: DataGuide 재무 시계열은 결산월 기준으로 나오므로 builder의 `결산월 말 + 3개월`
  lag 규칙을 그대로 적용한다. 감사보고서 제출일이나 실적 공시일 아이템이 있으면 함께
  받아 PIT 검증에 쓴다(`확인`).

### 재무제표 항목 (연간, 세 체계 각각)

| builder 항목 | DataGuide 계정명 (아이템코드) | 쓰이는 characteristic | 비고 |
|---|---|---|---|
| `total_assets` | 자산총계(천원) `M000901001` | Investment, NOA, DPI2A, CTO, ROA, D2A, OA, OL, A2ME, C, Q, AT | |
| `total_liabilities` | 부채총계(천원) `M000902001` | NOA, book equity 항등식 | |
| `total_equity` | 자본총계(천원) `M000903001` | BEME, PROF, OP, ROE, AC, CF, Q, Lev | |
| (지배주주지분) | 자본총계(지배)(천원) `M000903003` | book equity 교차검증 | 비지배 차감 전에 직접 값과 대조 |
| `noncontrolling_interest` | 비지배주주지분(천원) `M000903004` | book equity = 자본총계 − 비지배 | 별도·GAAP개별에는 없음 → 0 |
| `cash` | 현금및현금성자산(천원) `M000901030` | C, NOA, AC, OA | Compustat CHE는 단기투자 포함. 단기금융상품(천원) `M000901034`, 단기유가증권(천원) `M000901009`를 같이 받아 합산 여부를 정한다 |
| `current_assets` | 유동자산(천원) `M000901002` | AC, OA (working capital) | |
| `current_liabilities` | 유동부채(천원) `M000902003` | AC, OA | |
| `current_debt` | 단기차입금(천원) `M000902009` + 유동성장기부채(천원) `M000902044` | NOA, AC, OA, Lev | Compustat DLC = 단기차입 + 유동성장기부채. 단기사채(천원) `M000901066`도 받아 둔다 |
| `long_debt` | 장기차입금(천원) `M000902013` + 사채(천원) `M000901070` | NOA, Lev | Compustat DLTT는 사채 포함. 금융리스부채(천원) `M000901075`는 선택 |
| `tax_payable` | 당기법인세부채(천원) `M000991033` | AC, OA | |
| `inventory` | 재고자산(천원) `M000901012` | DPI2A | |
| `ppe` | 유형자산(천원) `M000901017` | DPI2A, CF(capex proxy) | 원문 DPI2A는 gross PPE(PPEGT). DataGuide 유형자산은 순액이므로 proxy로 기록 |
| `sales` | 매출액(천원) `M000904001` | ATO, CTO, FC2Y, OP, PM, SGA2S, PCM, PROF, S2P | |
| `cogs` | 매출원가(천원) `M000905001` | PROF, OP, OL, PCM | 매출총이익(천원) `M000904007`을 같이 받아 `매출액−매출원가` 검산 |
| `sga` | 판매비와관리비(천원) `M000904017` | FC2Y, OP, SGA2S, OL | |
| `rd` | 연구개발비(천원) `M000904027` | FC2Y | 판관비 내 세부항목. 이중계산 여부는 아래 참조 |
| `advertising` | 광고선전비(천원) `M000904030` | FC2Y | 판관비 내 세부항목 |
| `operating_income` | 영업이익(천원) `M000906001` | PM, RNA | 영업이익(발표기준)(천원) `M000906002`도 받아 두면 2012년 이후 정의 변경 검산 가능 |
| `interest_expense` | 이자비용(천원) `M000906020` | OP | |
| `net_income` | 당기순이익(천원) `M000908001` | ROA, ROE, CF, CF2P, E2P | 당기순이익(지배)(천원) `M000908004`도 함께. Compustat IB는 지배주주 기준이므로 지배 값을 우선 후보로 검토 |
| `depreciation` | 유형자산감가상각비(천원) `M000911043` | D2A, OA, CF, CF2P | 현금흐름표 기준. 손익계산서 기준 `M000904025`는 판관비 내 감가상각비만이므로 쓰지 않는다 |
| `amortization` | 무형자산상각비(천원) `M000901044` | D2A, OA, CF, CF2P | 현금흐름표 기준 |
| `deferred_tax` | 이연법인세부채(천원) `M000911019` | Q, CF2P | 이연법인세자산(천원) `M000991023`도 받아 순액 여부를 정한다 |
| (capex) | *유형자산순취득액(C/F)(천원) `M000993004` 또는 유형자산처분(취득)(천원) `M000909036` | CF | 현재 builder는 `ΔPPE(양수) + D&A` proxy를 쓴다. 이 항목을 받으면 원문 정의(NI + D&A − ΔWC − CAPX)에 가까워진다 |
| (배당총액) | 배당금지급(영업,투자,재무)(천원) `M000909041` | D2P 후보 | 우선주 배당 포함 총액. 아래 배당 항목과 비교 |

### 주식수·배당 (연간·월말)

| builder 항목 | DataGuide 후보 계정명 | 쓰이는 characteristic | 비고 |
|---|---|---|---|
| `common_shares` | 상장주식수(보통주), 발행주식수(보통주) `확인` | NI, LTurnover, ME 검산 | 분할·병합 조정이 필요하므로 수정계수와 같이 받는다. 월말 값이면 `NI`를 12개월 log 변화로 계산 |
| `cash_dividends` | 현금배당금총액(보통주) 또는 주당현금배당금(보통주) × 보통주식수 `확인` | D2P | 원문 D2P는 보통주 현금배당 총액 / ME. 배당금지급(C/F)은 우선주 포함이라 차선 |

### 주가·거래 항목 (일간)

오늘 받은 `data/dataguide/데이터가이드_주가시계열.csv`(2000-01-04~2026-09-16,
4,071종목)에는 기준가·시가·고가·저가·종가·수정계수·수정계수(현금배당포함)만 있다.
아래 항목은 별도로 받아야 한다.

| 항목 | DataGuide 후보 계정명 | 쓰이는 characteristic | 비고 |
|---|---|---|---|
| 수정 고가·저가·종가 | 이미 수령 (고가·저가·종가 × 수정계수) | Rel2High, Spread proxy, Variance | |
| 일·월 총수익률 | 수정계수(현금배당포함)로 계산 | r2_1, r12_2, r12_7, r36_13, ST_Rev, LT_Rev, Beta, MktBeta, IdioVol, Resid_Var, Variance, `ret` | 배당 포함 수익률이 원문 CRSP `ret`에 대응 |
| 거래량 | 거래량(주) `확인` | LTurnover, SUV | |
| 거래대금 | 거래대금(원) `확인` | 검산·turnover 대안 | |
| 시가총액 | 시가총액(원) 또는 종가 × 상장주식수 `확인` | LME, A2ME, BEME, CF2P, D2P, E2P, Q, S2P, 0.01% universe filter | 보통주 시가총액 기준. 우선주 합산 여부 확인 |
| 매도호가·매수호가 (종가 시점) | 매도호가, 매수호가 또는 최우선호가 `확인` | Spread | 없으면 현재의 high-low proxy를 유지하고 문서화 |
| 상장·상폐일, 시장구분 | 상장일, 상장폐지일, 시장구분 `확인` | PIT universe | 상장폐지 종목 포함 조건과 함께 요청 |

### 시장·무위험

| 항목 | 원천 | 쓰이는 characteristic |
|---|---|---|
| 시장수익률 (일·월) | KOSPI 지수(ECOS `802Y001`) 또는 DataGuide 지수 시계열; 원문은 CRSP VW 시장 | Beta, MktBeta, IdioVol, Resid_Var |
| FF3 일별 factor | 2016-08 이후 Kimchi 파일. 그 이전은 같은 DataGuide 자료로 SMB·HML을 직접 구성 | IdioVol, Resid_Var (원문은 FF3 residual) |
| 무위험수익률 (일) | ECOS `817Y002` CD(91일). 현재 2015~2026 원자료를 2000년까지 연장 | 일별 residual 입력, `ret − rf` |

### characteristic별 산식과 입력

산식은 `characteristics.py`의 구현 그대로다. `lag`는 직전 회계연도, `ME`는 월말
시가총액, `D&A`는 유형자산감가상각비 + 무형자산상각비, `debt`는 단기차입금 +
유동성장기부채 + 장기차입금 + 사채, `WC`는 유동자산 − 현금 − 유동부채 −
유동성차입 − 당기법인세부채다.

과거수익률 (6개, 월 총수익률만 필요)

| 이름 | 산식 |
|---|---|
| r2_1 | 직전 1개월 수익률 |
| r12_2 | t−12 ~ t−2 누적수익률 |
| r12_7 | t−12 ~ t−7 누적수익률 |
| r36_13 | t−36 ~ t−13 누적수익률 |
| ST_Rev | 직전 1개월 수익률 (r2_1과 동일 열) |
| LT_Rev | t−60 ~ t−13 누적수익률 |

투자 (4개)

| 이름 | 산식 | 입력 |
|---|---|---|
| Investment | (자산총계 − lag 자산총계) / lag 자산총계 | 자산총계 |
| NOA | [(자산총계 − 현금) − (부채총계 − debt)] / lag 자산총계 | 자산총계, 현금, 부채총계, debt |
| DPI2A | (Δ유형자산 + Δ재고자산) / lag 자산총계 | 유형자산, 재고자산, 자산총계 |
| NI | log(보통주식수 / lag 보통주식수) | 수정 보통주식수 |

수익성 (11개)

| 이름 | 산식 | 입력 |
|---|---|---|
| PROF | (매출액 − 매출원가) / 자본 | 매출액, 매출원가, book equity |
| ATO | 매출액 / lag NOA금액 | 매출액, NOA 구성항목 |
| CTO | 매출액 / lag 자산총계 | 매출액, 자산총계 |
| FC2Y | (판관비 + 연구개발비 + 광고선전비) / 매출액 | 판관비, 연구개발비, 광고선전비, 매출액 |
| OP | (매출액 − 매출원가 − 이자비용 − 판관비) / 자본 | + 이자비용 |
| PM | 영업이익 / 매출액 | 영업이익, 매출액 |
| RNA | 영업이익 / lag NOA금액 | 영업이익 |
| ROA | 당기순이익 / lag 자산총계 | 당기순이익, 자산총계 |
| ROE | 당기순이익 / lag 자본 | 당기순이익, book equity |
| SGA2S | 판관비 / 매출액 | 판관비, 매출액 |
| D2A | D&A / 자산총계 | 유형자산감가상각비, 무형자산상각비, 자산총계 |

무형 (4개)

| 이름 | 산식 | 입력 |
|---|---|---|
| AC | ΔWC / 자본 | 유동자산, 현금, 유동부채, 유동성차입, 당기법인세부채, book equity |
| OA | (ΔWC − D&A) / lag 자산총계 | + D&A, 자산총계 |
| OL | (매출원가 + 판관비) / 자산총계 | 매출원가, 판관비, 자산총계 |
| PCM | (매출액 − 매출원가) / 매출액 | 매출액, 매출원가 |

가치 (10개)

| 이름 | 산식 | 입력 |
|---|---|---|
| A2ME | 자산총계 / ME | 자산총계, 시가총액 |
| BEME | 자본 / ME | book equity, 시가총액 |
| C | 현금(및 단기투자) / 자산총계 | 현금, 단기금융상품, 자산총계 |
| CF | (당기순이익 + D&A − ΔWC − capex) / 자본 | + capex 또는 ΔPPE proxy |
| CF2P | (당기순이익 + D&A + 이연법인세) / ME | 당기순이익, D&A, 이연법인세부채, 시가총액 |
| D2P | 현금배당총액 / ME | 배당총액, 시가총액 |
| E2P | 당기순이익 / ME | 당기순이익, 시가총액 |
| Q | (자산총계 + ME − 자본 − 이연법인세) / 자산총계 | 자산총계, book equity, 이연법인세부채, 시가총액 |
| S2P | 매출액 / ME | 매출액, 시가총액 |
| Lev | debt / (debt + 자본) | debt 구성항목, book equity |

거래마찰 (11개)

| 이름 | 산식 | 입력 |
|---|---|---|
| AT | 자산총계 (수준) | 자산총계 |
| Beta | 일별 시장모형 beta, 최대 1,260일 창 (원문은 Frazzini-Pedersen 3일 중첩수익률 beta) | 일 수익률, 시장수익률 |
| IdioVol | 시장모형 잔차 표준편차 (원문은 FF3 잔차) | 일 수익률, 시장(FF3) |
| LME | log ME | 시가총액 |
| LTurnover | 월 거래량 / 상장주식수 | 거래량, 상장주식수 |
| MktBeta | 월별 시장모형 beta, 60개월 창 (최소 24) | 월 수익률, 시장수익률 |
| Rel2High | 월말 종가 / 직전 252일 최고가 | 수정 종가·고가 |
| Resid_Var | 시장모형 잔차 분산 | 위와 동일 |
| Spread | 전월 일별 bid-ask spread 평균 (현재는 high-low proxy) | 호가 또는 고가·저가 |
| SUV | 거래량을 ± 수익률에 회귀한 잔차의 표준화값 | 거래량, 일 수익률 |
| Variance | 직전 42거래일 수익률 분산 | 일 수익률 |

### 원문과 달라지거나 확인이 필요한 점

- **판관비 이중계산**: K-IFRS 판관비는 연구개발비·광고선전비를 이미 포함한다.
  Compustat XSGA도 XRD·XAD를 포함하므로 원문 FC2Y 정의 자체가 중복 합산이다.
  원문 그대로 더할지, 한국에서는 판관비만 쓸지 문서에 고정한다.
- **유형자산 gross vs net**: 원문 DPI2A는 취득원가(PPEGT) 변화다. DataGuide
  유형자산은 감가상각누계액 차감 후 순액이다. 취득원가 아이템이 있으면 받고,
  없으면 proxy로 기록한다.
- **capex**: `*유형자산순취득액(C/F)`를 받으면 현재 `ΔPPE(양수) + D&A` proxy를 원문
  정의로 되돌릴 수 있다.
- **당기순이익 기준**: Compustat IB는 지배주주 귀속 기준이다. 당기순이익(지배)와
  당기순이익 둘 다 받아 어느 쪽을 쓸지 정한다.
- **book equity**: 자본총계 − 비지배주주지분과 자본총계(지배)가 같은지 검산한다.
  우선주자본금(천원) `M000903008`을 빼는 Compustat CEQ 방식과의 차이도 기록한다.
- **Spread**: 종가 시점 최우선 호가가 DataGuide에 없으면 high-low proxy를 유지하고
  `PROXY_CHARACTERISTICS` 경고를 그대로 둔다.
- **금융업**: DataGuide는 금융업 재무를 별도 계정체계(은행·보험·증권)로 제공한다.
  같은 계정명이 없으므로 회계 characteristic 없이 가격 characteristic만 갖거나
  제외한다. 어느 쪽이든 명시한다.
- **GAAP 구간 계정 정의**: 2010년 이전 GAAP 개별과 2011년 이후 IFRS 연결의 계정
  정의 차이(영업이익 정의, 무형자산상각비 위치)는 연결 시점의 값 점프로 검산한다.
- **DataGuide 시계열 layout**: 오늘 받은 CSV처럼 `코드, 코드명, 유형, 아이템코드,
  아이템명, 집계주기` 뒤에 날짜 열이 오는 wide format이다.
  `KAIST_thesis-master/load_dataguide.py`가 영문 header(`Symbol`, `Item Name`)를
  기준으로 melt·pivot하므로 한글 header용으로 고쳐서 재사용한다.

## 연산자원

저자 공식 README의 full-replication 최소치는 CPU 16 cores, RAM 384GB,
저장공간 2TB, GPU VRAM 36GB다. 현재 단계에서는 full deep-learning run을
시작하지 않고, CPU PCA pilot으로 schema·PIT·composition matrix 크기를 먼저
검증한다.
