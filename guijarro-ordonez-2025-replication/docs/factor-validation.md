# Kimchi Factor 구현 검증

## 2018년 이후 방법론 구현 결과

`build-kimchi-factors`는 2018-01-01 이후를 대상으로 월말 FGSC 역사
스냅샷, KOSPI-only breakpoint, 팩터별 금융업 처리, VW/EW, 2×3/5분위와
일간/월간 독립 산출을 적용한다. 분류는 **price-return variant +
fixed-3-month-lag non-PIT accounting sensitivity**다.

VW 일간 수익률과 제공된 Kimchi Factor의 공통일자 비교는 다음과 같다.

| 팩터 | 공통 일수 | 시작일 | 상관계수 | 일 MAE | 변동성 비율 | 부호 일치율 | benchmark 대비 결측률 |
|---|---:|---:|---:|---:|---:|---:|---:|
| RM | 2,095 | 2018-01-03 | 1.000000 | 0.0004 bp | 1.0000 | 100.00% | 0.05% |
| RMRF | 2,095 | 2018-01-03 | 1.000000 | 0.0004 bp | 1.0000 | 100.00% | 0.05% |
| SMB | 1,975 | 2018-07-02 | 0.9940 | 7.77 bp | 1.0087 | 96.10% | 5.77% |
| HML | 1,975 | 2018-07-02 | 0.9845 | 10.74 bp | 0.9857 | 95.59% | 5.77% |
| RMW | 1,731 | 2019-07-01 | 0.9593 | 16.54 bp | 1.0525 | 89.89% | 17.41% |
| CMA | 1,975 | 2018-07-02 | 0.9416 | 15.93 bp | 1.0158 | 87.85% | 5.77% |
| MOM | 2,074 | 2018-02-01 | 0.9908 | 7.35 bp | 1.0024 | 95.42% | 1.05% |
| RF | 2,096 | 2018-01-02 | 1.000000 | 0.0000 bp | 1.0000 | 100.00% | 0.00% |

RM의 미세 오차는 ECOS에 배포된 KOSPI 지수 수준의 표시 자릿수로 일수익률을
재계산하면서 생긴 반올림 수준이다. RF는 ECOS CD(91일)에
`(1+y/100)^(1/252)-1`을 적용한 값이 Kimchi와 전 행 일치한다.

높은 상관계수만으로 동일 계열이라고 결론 내리면 안 된다. 특히 VW는 대형주의
영향이 크므로 재무 coverage가 부족해도 상관이 높을 수 있다. 2×3 버킷의 평균
종목 수는 다음과 같다.

| 팩터 | 구성 버킷 평균 종목 수 | Kimchi 평균 종목 수 | 버킷 상관 평균 | 버킷 상관 최솟값 |
|---|---:|---:|---:|---:|
| SMB/HML | 278.5 | 349.4 | 0.9928 | 0.9857 |
| RMW | 264.1 | 354.9 | 0.9903 | 0.9822 |
| CMA | 261.7 | 348.4 | 0.9899 | 0.9769 |
| MOM | 350.8 | 353.0 | 0.9954 | 0.9903 |

재무 팩터의 종목 수 차이는 최신 local statement snapshot의 역사 coverage와
계정 구성항목 결측이 핵심이다. FY2017에는 감가상각 구성항목이 없어 RMW를
만들지 않았고, 영업이익/BE proxy로 대체하지 않았다. HML의 과거 자본총계 결측은
연결 대차대조표의 `총자산-총부채-비지배주주지분` 항등식으로만 보완했다.

월간 수익률은 일간 팩터를 누적하지 않고 종목별 월 보유수익률과 전월 말 ME로
다시 계산했다. 월간 직접 산출값과 일간 복리누적값의 평균 절대차는 SMB 38.61bp,
HML 25.38bp, RMW 26.17bp, CMA 21.39bp, MOM 20.13bp로 0이 아니다. 이는 두
주기의 독립 산출이 실제로 적용됐다는 검산이다.

전체 수치와 계보는 `outputs/kimchi-exact/`의 다음 파일에 있다.

- `daily_factor_returns.csv`, `monthly_factor_returns.csv`: VW/EW 팩터
- `daily_market_rf.csv`, `monthly_market_rf.csv`: ECOS KOSPI·CD 기반 RM/RF/RMRF
- `daily_2x3_bucket_returns.csv`, `monthly_2x3_bucket_returns.csv`
- `daily_quintile_bucket_returns.csv`, `monthly_quintile_bucket_returns.csv`
- `annual_memberships.csv`, `momentum_memberships.csv`, `accounting_signals.csv`
- `kimchi_factor_comparison.csv`, `kimchi_bucket_comparison.csv`
- `factor_construction_audit.json`

## 과거 broad-universe proxy 검증

## 결론

**이 문서의 결과는 `docs/kimchi-factor-methodology.md` 확정 전에 생성한
진단용 proxy이며 exact Kimchi Factor가 아니다.** 로컬 raw 주식·재무자료에서
논문용 8개 proxy 팩터를 생성했다. Kimchi와 공통인
RM/RMRF/SMB/HML/RMW/CMA/MOM의 공통일자 비교 결과, **시장·모멘텀·규모는
높게 일치하지만 재무 팩터는 동일 시계열로 간주할 수준이 아니다.** 특히 CMA의
상관계수는 0.568이다. 따라서 Kimchi와 로컬 팩터는 서로를 대체하는 두 복사본이
아니라, 정의·유니버스 차이를 확인하는 benchmark와 candidate series다.

| 팩터 | 공통 일수 | 상관계수 | 일 MAE | 연율 tracking error | 부호 일치율 |
|---|---:|---:|---:|---:|---:|
| RM | 2,437 | 0.9945 | 11.15 bp | 2.37% | 95.24% |
| RMRF | 2,437 | 0.9945 | 11.15 bp | 2.37% | 94.75% |
| SMB | 2,216 | 0.9033 | 29.99 bp | 7.07% | 86.42% |
| HML | 2,216 | 0.8004 | 43.33 bp | 10.01% | 82.76% |
| RMW | 2,216 | 0.6916 | 44.88 bp | 10.13% | 75.86% |
| CMA | 2,216 | 0.5680 | 38.40 bp | 12.43% | 80.96% |
| MOM | 2,437 | 0.9391 | 22.41 bp | 4.91% | 88.18% |

RMRF는 양쪽 모두 `RM - RF`이며, 로컬 RMRF에도 Kimchi의 RF를 사용했다.
따라서 독립적인 market-data 검증치는 RMRF가 아니라 RM 상관계수 0.9945다.

## 산출 규칙

- RM: 전 거래일 시가총액으로 전체 유효 종목의 일별 수익률을 value-weight
- SMB/HML/RMW/CMA: 6월 말 size median과 characteristic 30/70 breakpoint로
  2×3 정렬한 뒤 다음 7월부터 1년 보유
- HML: positive book equity / market capitalization
- RMW: operating profit / positive book equity
- CMA: 전년 대비 total-assets growth의 conservative-minus-aggressive
- MOM: 보유월 기준 12~2개월 누적수익률의 winner-minus-loser
- LTR: 보유월 기준 60~13개월 누적수익률의 loser-minus-winner
- STR: 직전 1개월 수익률의 loser-minus-winner
- 모든 characteristic portfolio의 일별 수익률: 전 거래일 시가총액 value-weight

재무 characteristic의 사용가능일은 `fiscal period month-end + 3 months`다.
membership에서 이 날짜가 6월 formation date보다 늦은 행은 0건이다. 그러나
원천은 2026년에 수집한 최신 dump revision이므로 이 검사는 미래 날짜 결합만
막을 뿐, 과거 정정 전 재무값을 복원하지는 않는다.

## 차이의 위치

시장수익률 상관계수가 0.995이므로 일별 return과 market-cap 단위가 완전히
어긋난 것은 아니다. 차이는 characteristic sort에서 커진다.

- MOM의 2×3 bucket은 대부분 0.95 이상으로 매우 높지만 S2는 0.643이다.
- HML과 RMW는 소형주 중간 bucket의 상관이 각각 0.587, 0.586으로 낮다.
- CMA의 개별 bucket 상관은 0.829~0.938인데 long-short factor 상관은 0.568이다.
  두 다리가 각각 비슷해도 작은 구성 차이가 spread에서 확대되는 전형적인
  cancellation 현상이다.
- 평균 종목 수도 다르다. 예를 들어 HML S1은 로컬 약 157개, Kimchi 약 601개다.
  현재 로컬 재무 coverage, 보통주/우선주 등 PIT security-master 부재, book
  equity와 profitability 정의 차이가 우선 조사 대상이다.

따라서 현재 결과는 코드가 전혀 다른 시장을 계산했다는 증거도 아니고, Kimchi를
정확히 복제했다는 증거도 아니다. **가격 기반 팩터는 강한 교차검증을 통과했고,
재무 기반 팩터는 방법론·유니버스 reconciliation이 남았다**는 판정이 정확하다.

## 가용 구간과 논문 적용

| 팩터 | 로컬 시작일 | 종료일 |
|---|---:|---:|
| RM | 2015-01-05 | 2026-07-20 |
| STR | 2015-02-02 | 2026-07-20 |
| MOM | 2016-01-04 | 2026-07-20 |
| SMB/HML/RMW/CMA | 2017-07-03 | 2026-07-20 |
| LTR | 2020-01-02 | 2026-07-20 |

8개 팩터의 공통 시작일은 2020-01-02다. 따라서 한국 FF8 residual pilot은
2020년 이후에만 가능하다. 이는 원 논문의 1998~2016 residual 표본을 exact
replicate하지 않는다.

## 재현 명령과 산출물

```powershell
uv run python guijarro-ordonez-2025-replication/run.py build-factors-proxy --allow-non-pit-statements
```

`outputs/factors/` 아래에 다음 파일을 생성한다.

- `constructed_daily_factors.csv`: 논문 입력용 RM/RMRF/SMB/HML/RMW/CMA/MOM/LTR/STR/RF
- `constructed_2x3_bucket_returns.csv`: 팩터별 S1~B3 일별 수익률과 종목 수
- `kimchi_factor_comparison.csv`: 위 표의 factor-level 검증치
- `kimchi_bucket_comparison.csv`: 2×3 portfolio-level 진단
- `factor_construction_audit.json`: 입력·coverage·중복키·미래 재무 결합 검사
- factor별 annual/monthly membership: 각 종목의 실제 sort 계보
