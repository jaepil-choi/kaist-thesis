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

### Gate D — 한국 investability extension

1. 종목별·일별 공매도 가능 여부
2. 대차 가능수량·잔고·borrow fee
3. 거래세, 수수료, spread와 ADV 기반 market-impact 입력
4. 공매도 금지기간과 종목별 제한 이력

## 연산자원

저자 공식 README의 full-replication 최소치는 CPU 16 cores, RAM 384GB,
저장공간 2TB, GPU VRAM 36GB다. 현재 단계에서는 full deep-learning run을
시작하지 않고, CPU PCA pilot으로 schema·PIT·composition matrix 크기를 먼저
검증한다.
