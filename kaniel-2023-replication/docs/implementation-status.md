# Implementation status

기준일: 2026-08-07

## 구현 완료

- 본문·부록 Figure/Table 64개 output registry
- source schema audit와 외부입력 gate
- active type의 class-level daily-to-monthly streaming panel
- Table 1, Table 2, Figure 3, Table B.1 generator
- prior 36개월 Carhart beta와 Eq. (2) abnormal-return 산식
- `F_ST_Rev`, `F_r2_1`, `F_r12_2` 시점 정렬
- 대표수익률과 전월 TNA 가중 클래스 수익률 비교 및 그룹별 consolidation gate
- share-class TNA 일치율, 수익률 차이, consolidation 판정 진단 Figure 3종
- 일별 주식수익률의 월별 복리연결 및 lagged market-cap/momentum formation
- annual June 2×3 size/book-to-market, monthly 2×3 momentum factor construction
- 재무 announcement timestamp 부재 시 HML 생성을 막는 기본 PIT gate
- random/chronological 3-fold cross-OOS MLP ensemble과 extreme-decile portfolio
- Eq. (4)–(6) prediction weights와 equal-weight 비교
- ECOS 월별 11개 시계열 3,191건 수집·검증 및 RF·경기상태 기본 입력 연결
- ECOS 5개 구성요소의 고정-calibration PCA sentiment proxy와 1개월 lag
- non-PIT Carhart sensitivity부터 rolling alpha, 3-fold ML, decile portfolio까지 실행

## ECOS 입력 확보 현황

| 입력 | 채택 시계열 | 기간 | 판정 |
|---|---|---|---|
| RF | 통안증권 91일, 연%를 월 decimal로 변환 | 2006-09~2026-07 | 기본 입력 확보 |
| RF robustness | CD 91일 | 1991-03~2026-07 | 은행 신용위험 때문에 보조용 |
| 경기상태 | ESI 순환변동치 - 100 | 2003-01~2026-07 | CFNAI와 다른 robustness proxy |
| sentiment 구성 후보 | 회전율·개인 수급·예탁금·신용융자 | 1998-06~2026-07 | 원천 패널 |
| sentiment proxy | 5개 구성요소 고정-calibration PCA | 2015-01~2026-07 | 불완전 proxy, 실행 입력 |

ECOS에는 IPO 수·첫날 수익률, 주식발행 비중, dividend premium이 없어
Baker–Wurgler 방식의 exact-definition sentiment는 아직 완성되지 않았다.
proxy는 2005~2014에서 loading을 고정하고 관측월을 다음 달에 사용한다.

## Parsimonious proxy 실행 결과

- factor: 3개월 reporting lag, 명시적 non-PIT book-equity sensitivity
- factor 전체 기간: 2015-01~2026-07, 139개월
- MKT·SMB·HML·MOM·RF 완전관측 구간: 2019-07~2026-07, 85개월
- OOS prediction: 136,641건, 2022-10~2026-06
- top/bottom portfolio: 45개월, 결측 0
- equal-weight long-short 평균: 월 0.2227%
- prediction-weighted long-short 평균: 월 0.3364%

이 평균은 45개월의 기술통계다. 표준오차·통계적 유의성·거래비용 검정 전에는
경제적 성과 확정치로 해석하지 않는다. 결과는 `implemented_proxy`이며 exact
Table 7과 구분한다.

## 전체 class-month 중간 패널

- 원천: 19,927,019 fund-day
- 선택된 active-type 원행: 15,974,873
- 산출: 778,877 class-month, 8,482 fund codes, 367 months
- 기간: 1996-01~2026-07
- `(month, fund_code)` 중복: 0
- 설정 placeholder 제거: 7,158행
- 숫자로 변환되지 않거나 0 이하인 return factor: 0행
- 0.5 미만 또는 1.5 초과 return factor: 219행, 124개 fund code
- 오염된 fund-month: 193개; monthly return과 flow를 결측 처리

이 파일은 share-class 통합 전 중간 산출물이다. 최종 fund-month 표본으로
사용하지 않는다.

## 현재 blocker

1. 공시일 기반 PIT 한국 Carhart 4요인 완성본(non-PIT sensitivity는 실행 완료)
2. exact-definition 한국형 Baker–Wurgler sentiment(ECOS-only proxy는 실행 완료)
3. 대표 TNA는 class 합계로 검증됐지만 대표수익률은 class 가중수익률보다
   중앙값 월 10.78bp 높음; gross/net 의미 확인 필요
4. `실현수익률`의 gross/net 및 분배금 처리에 대한 vendor 정의
5. 극단 return factor가 분할·병합·청산 조정인지 데이터 오류인지 확인
6. 역사적 fee와 turnover
7. survivorship-bias-free full holdings와 46개 stock characteristics
8. 재무제표 실제 공시시각과 historical revision vintage
9. `market_cap`의 total/free-float 기준 및 수정수익률의 total-return 정의
10. sklearn backend의 dropout 0.95 미지원과 tuning-grid validation 미구현

ECOS-only proxy를 사용한 parsimonious `flow + F_r12_2 + sentiment` 전 단계는
완료했다. fee·turnover·holdings가 필수인 결과는 proxy로 채우지 않고 registry에서
blocked로 유지한다. Table 7 sensitivity는 `implemented_proxy`로 분류하며,
공시일 기반 PIT factor와 확장 sentiment가 확보되기 전에는 exact
`implemented`로 승격하지 않는다.
