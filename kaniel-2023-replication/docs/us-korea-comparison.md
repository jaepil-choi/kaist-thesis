# Kaniel et al. Table 7: 미국 원문과 한국 proxy 비교

기준일: 2026-08-07

## 비교 대상

원문의 Table 7은 `flow + F_r12_2 + sentiment` 세 변수만 사용한 신경망의
prediction-weighted top/bottom decile 성과다. 한국 결과도 같은 세 입력과
논문 식 (4)–(6)의 가중식을 사용했다. 다만 한국 sentiment는 5개 ECOS
구성요소의 불완전한 proxy이고, Carhart 요인은 3개월 reporting lag를 적용한
non-PIT sensitivity이며, dropout 0.95는 구현하지 않았다.

| Portfolio | Market | Mean per month | Monthly SR | t-stat | Factor R2 |
|---|---|---:|---:|---:|---:|
| Long-short | U.S. published | 0.400% | 0.250 | 5.40 | 0.70% |
| Long-short | Korea proxy | 0.336% | 0.186 | 1.25 | -1.44% |
| Top | U.S. published | 0.170% | 0.160 | 3.40 | -0.73% |
| Top | Korea proxy | 0.887% | 0.405 | 2.72 | -4.53% |
| Bottom | U.S. published | -0.230% | -0.210 | -3.60 | 0.82% |
| Bottom | Korea proxy | 0.551% | 0.211 | 1.42 | -9.14% |

미국 수치는 Kaniel et al. (2023), Table 7이고, 한국 수치는 45개월
(formation 2022-10~2026-06, 다음 달 수익률 실현)의 cross-out-of-sample
결과다. mean, SR, t-stat은 원문과 같이 월 수익률의 표본평균과 표본표준편차로
계산했다. Factor R2는 원문 각주 15의
`1 - sum((forecast - realized)^2) / sum(realized^2)` 정의를 사용했다.

## 해석

1. **평균 크기만 보면 부분적으로 유사하다.** 한국 long-short 월평균
   0.336%는 미국 0.400%의 약 84%다. 그러나 한국 월 Sharpe는 0.186으로
   미국 0.250보다 낮고, t값은 1.25라 0과 통계적으로 구분되지 않는다.
   미국 t값 5.4와 동일한 강도의 증거가 아니다.

2. **한국의 spread 구성은 원문과 다르다.** 미국은 top +0.17%, bottom
   -0.23%로 잘하는 펀드와 못하는 펀드를 양·음으로 분리한다. 한국은 top
   +0.887%, bottom도 +0.551%다. 현재 spread는 부진 펀드의 음의 alpha를
   찾아낸 결과가 아니라, 공통적으로 높은 추정 alpha 안에서 상대 순위를
   일부 나눈 결과다.

3. **level calibration은 실패했다.** 한국 long-short Factor R2가 -1.44%라는
   것은 OOS 예측값을 그대로 수준 예측에 쓰는 것이 0을 예측하는 것보다
   제곱오차가 크다는 뜻이다. 양의 long-short 평균은 cross-sectional ranking의
   가능성을 시사하지만, 예측 alpha의 절대 크기는 신뢰할 수 없다.

4. **성과가 기간 전체에 안정적이지 않다.** 누적 long-short는 2025년 초까지
   음수였고, 이후 특히 2026년 상반기의 급등이 45개월 누적 산술수익률
   15.14%를 만들었다. 짧은 표본과 특정 regime 의존 가능성이 크다.

5. **원문의 sentiment interaction은 재현되지 않았다.** 한국 Figure 14
   proxy에서는 high-sentiment/high-flow/high-momentum 조합이 최댓값이 아니다.
   중간 sentiment 상태의 예측 수준이 가장 높고, high sentiment에서 flow
   방향은 단조롭지 않다. 현재 ECOS proxy로 원문의 high-sentiment
   amplification을 지지할 수 없다.

## 현재 생성한 논문 번호 Figure

| Figure | 한국 산출물 | 판정 |
|---|---|---|
| Figure 1 | sentiment·경기상태 시계열 | 정의가 다른 proxy |
| Figure 2 | random·chronological fold assignment | 짧은 한국 가용기간의 proxy |
| Figure 3 | single-hidden-layer network | data-independent 정적 구현 |
| Figure 4 | equal·prediction weights | 논문 식을 한국 대표월에 적용 |
| Figure 8 | parsimonious long-short 누적성과 | 한 정보집합만 있는 partial proxy |
| Figure 14 | flow·momentum·sentiment 예측 표면 | OOS 예측의 bin 평균 proxy |

Figure 14는 원문의 연속 신경망 함수를 동일 grid에서 평가한 exact figure가
아니라, 실제 OOS 관측값을 flow·momentum quintile과 sentiment tercile로 묶은
진단 heatmap이다. 이를 exact replication으로 부르지 않는다.

## 남은 핵심 검증

- 실제 공시시점과 historical revision을 사용한 PIT HML 재구축
- 대표펀드 수익률의 gross/net 정의 확정과 share-class 중복 제거
- IPO·발행·dividend-premium을 보강한 한국형 sentiment
- chronological 및 expanding-window 결과와 2026년 상반기 제외 민감도
- full holdings·46개 stock characteristics·fee·turnover 확보 후 Figure 5–13과
  appendix의 full-information 결과 구현

비교용 CSV는 `outputs/tables/table_07_us_korea_comparison.csv`, 재생성 명령은
`uv run python kaniel-2023-replication/run.py proxy-outputs`다.
