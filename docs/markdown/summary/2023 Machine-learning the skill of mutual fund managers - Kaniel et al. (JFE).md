# Machine-Learning the Skill of Mutual Fund Managers

이 논문은 신경망으로 액티브 뮤추얼펀드의 다음 달 위험조정 성과를 표본 외 예측한다. 펀드 flow와 펀드 자체의 momentum, 그리고 투자심리와의 비선형 상호작용이 핵심 예측정보이며, 보유종목 특성은 총수익의 체계적 부분은 설명하지만 abnormal return은 거의 예측하지 못한다.

## Abstract

머신러닝은 수수료 전·후 모두 고성과와 저성과 펀드를 구분하며 예측력은 3년 이상 지속된다. fund momentum과 flow가 가장 중요하고 보유주식 특성은 유의하지 않다. 예측 long-short 수익은 고심리 상태 뒤에 더 크며, 신경망은 선형모형이 놓치는 sentiment×flow 및 sentiment×momentum 상호작용을 포착한다.

## 1. Introduction

1980~2019년 미국 액티브 주식형 펀드의 Carhart 4요인 abnormal return을 46개 보유종목 특성, 13개 펀드·family 특성, sentiment 또는 CFNAI로 예측한다. 한 은닉층 feedforward neural network를 training·validation·test로 나누어 평가하며 모든 성과는 표본 외다.

전체 정보를 쓴 prediction-weighted 포트폴리오에서 상위 10%의 누적 gross abnormal return은 72%, 하위 10%는 -119%로 총 격차가 191%다. 월별로 상위는 +15bp, 하위는 -25bp이며 수수료 차이로 설명되지 않는다. flow·fund momentum·sentiment 세 변수만으로도 상·하위 월 격차 48bp, 월 Sharpe 0.24를 얻는다. 예측은 36개월 뒤에도 long-short 월 Sharpe 0.20으로 지속된다.

기여는 total return보다 factor exposure를 제거한 abnormal return이 상대성과 예측에 적합함을 보이고, 정보집합의 경제적 가치를 동일한 유연모형 안에서 비교하며, macro state가 여러 fold에 고르게 포함되는 cross-out-of-sample 평가를 제안한다는 데 있다. 또한 prediction-weighting과 신경망 interaction의 전역적 gradient 측정·유의성 검정을 제시한다.

## 2. Data

CRSP 펀드 자료와 Thomson holdings를 연결하고, 종목·펀드·family·거시 특성을 결합한다. 핵심 종속변수는 과거 자료로 추정한 동적 요인노출을 제거한 다음 달 abnormal return이다.

### 2.1. Mutual funds

미국 국내주식 중심 액티브 펀드 3,275개, 1980년 1월~2019년 1월 407,158 fund-month를 사용한다. 수익률·보수·TNA·투자목적은 CRSP Survivor Bias-Free Database, 분기 보유내역은 Thomson에서 얻는다. 각 관측치는 전월 holdings와 TNA가 있고, 최근 36개월 중 최소 30개월 수익률이 있어야 한다.

### 2.2. Abnormal fund returns

최근 36개월 rolling regression으로 각 펀드의 Carhart 시장·규모·가치·momentum beta를 추정하고, 당월 초과수익에서 해당 요인수익 보상을 빼 abnormal return을 만든다. 표본 평균·중앙값은 월 -0.03%, 표준편차는 2.00%다. 주 결과는 gross 기준이지만 net-of-fee와 확장 요인모형에도 강건하다.

### 2.3. Holdings-based characteristics

기존 주식수익 예측문헌의 46개 특성을 여섯 범주로 나누고, 각 펀드의 직전 보유비중으로 가중한다. 특성은 횡단면 순위를 -0.5~0.5로 정규화하고, 결측치는 특성공간 latent-factor 모형으로 대체한다. 완전관측 표본에서도 결론은 같다.

### 2.4. Fund and family characteristics

13개 변수에는 단기반전과 2~12개월 등 fund abnormal-return momentum, flow, 규모, 연령, turnover, expense 및 family momentum·flow·규모·연령·펀드 수가 포함된다. fund momentum은 분기 holdings 기반 stock momentum과 달리 분기 중 거래와 펀드의 요인조정 잔차 성과를 반영한다. 평균 펀드는 13.7년, TNA 11.53억 달러, 월 expense 약 0.1%, 월 flow 1.6%다.

### 2.5. Macro-economic information

경제상태는 Baker–Wurgler investor sentiment와 85개 실물지표의 첫 주성분인 Chicago Fed National Activity Index(CFNAI)로 측정한다. sentiment는 IPO, turnover, closed-end discount 등 시장심리를, CFNAI는 생산·고용·소비·주택·판매 등 실물활동을 대표한다.

## 3. Main analysis

59개 펀드·보유종목 특성과 macro 변수를 입력해 다음 달 abnormal return의 비선형 조건부 평균을 학습한다. 정보집합을 바꾸되 같은 신경망을 사용해 어떤 데이터가 실제 예측성과를 만드는지 비교한다.

### 3.1. Sampling scheme

전체 시점을 세 fold로 나누고 두 fold에서 추정·튜닝, 나머지에서 평가하는 과정을 세 번 반복해 모든 관측치의 표본 외 예측을 얻는다. 기본은 날짜를 무작위 배정해 각 fold에 고·저 sentiment 상태가 고르게 들어가게 한다. 시간순서를 모형 입력으로 사용하지 않고 미래 오차를 예측에 넣지 않으므로 저자들은 look-ahead bias가 아니라고 설명하지만, 실시간 투자 가능성은 expanding-window 검정에서 별도로 확인한다.

### 3.2. Neural network

최적 구조는 ReLU를 쓰는 한 은닉층 feedforward network다. L1 regularization, early stopping, hidden units 등 hyperparameter는 validation에서 선택하고 서로 다른 초기값 8개 적합을 ensemble해 분산과 국소최적 문제를 줄인다. 복잡한 상호작용을 허용하면서도 표본 규모에 맞는 얕은 구조가 더 안정적이다.

### 3.3. Optimal prediction

매월 예측 abnormal return으로 펀드를 10분위로 나누고, 분위 내에서 동일가중 또는 예측치가 극단적일수록 큰 비중을 주는 prediction-weighting을 적용한다. prediction-weighting이 ranking과 signal strength를 모두 써 더 큰 spread를 만든다. 전체정보 기준 상위 10%는 누적 +72%, 하위는 -119%이며, 상·하위 보수가 비슷하므로 gross 격차는 fee가 아니다. net return을 직접 예측하면 상위 누적 net alpha 37%, 하위 약 -170%이고 약 20%의 펀드가 수수료 후 양의 abnormal return을 보인다.

### 3.4. Which information most useful when predicting fund abnormal returns?

fund-specific variables+sentiment가 가장 유용하고 stock characteristics는 abnormal return 예측을 거의 개선하지 않는다. 이 정보집합의 월 long-short 평균은 약 40bp, 월 Sharpe 0.25(연환산 약 0.87)다. sentiment를 추가하면 순위뿐 아니라 spread 크기 예측이 좋아지고 factor R²가 상승한다. flow와 fund momentum을 제거하면 성과가 크게 떨어진다.

### 3.5. Longer holding periods

1개월 예측으로 구성한 포트폴리오의 성과차는 보유기간을 늘려도 천천히 감소한다. 3개월 long-short 월 Sharpe가 약 0.30이고, 36개월에도 0.20으로 통계적·경제적으로 유의하다. 이는 알려진 단기 펀드성과 지속성보다 훨씬 길며, flow가 skill에 즉시 완전히 반응하지 않고 gradual하게 이동한다는 해석과 맞는다.

### 3.6. Sampling scheme

무작위 fold 결과를 chronological cross-validation과 실시간 가능한 expanding-window로 재검증한다. 평균 예측 spread와 fund variables의 우위는 유지되지만, chronological split에서는 특정 fold에 고심리 시기가 없어 sentiment의 중요도와 interaction이 약하게 추정된다. 즉 핵심 성과예측은 표본분할에 강건하나 macro-state 상호작용 측정은 상태의 표본 대표성에 민감하다.

## 4. Understanding the results

예측력의 원천을 변수 중요도, macro interaction, parsimonious specification, 수익률 분해, 예측대상 비교로 해석한다.

### 4.1. Variable importance and interaction effects

표본 외 예측함수의 평균 제곱 gradient로 변수 중요도를 측정하면 fund flow와 2~12개월 fund momentum이 최상위이고 sentiment가 이를 조건화한다. 고심리 상태에서 flow·momentum·단기반전에 따른 상·하 성과차가 훨씬 커지며, 최상위 outperform과 최하위 underperform이 대체로 대칭적으로 확대된다. 이는 단순 additive sentiment 또는 사후 sentiment 회귀로 포착하기 어려운 비선형 interaction이다.

### 4.2. Which macro-economic variable?

CFNAI를 추가하면 예측 수준은 다소 개선되지만 fund characteristics와의 interaction은 거의 없다. CFNAI 상태별 관계는 주로 평행 이동하는 반면, sentiment는 flow·momentum의 기울기 자체를 바꾼다. 따라서 결과는 일반적인 경기순환보다 투자자 심리와 자금배분 마찰에 더 직접적으로 연결된다.

### 4.3. A parsimonious model

flow, 2~12개월 fund momentum(F_r12_2), sentiment 세 변수만 쓴 한 은닉층 모형도 대부분의 성과를 재현한다. prediction-weighted long-short 평균은 월 약 40bp, Sharpe 0.25이고 상위 +17bp, 하위 -23bp 정도다. 단순화된 함수에서도 고 sentiment일수록 flow와 momentum의 효과가 크게 증폭된다.

### 4.4. Decomposing abnormal returns

abnormal return을 직전 분기말 holdings를 고정한 between-disclosure 성과와 분기 중 거래를 반영한 within-disclosure 성과로 나눈다. 전체 예측 spread의 약 절반은 기존 보유종목의 이후 성과, 나머지 절반은 분기 중 거래에서 나온다. within 부분은 return gap과 factor-risk exposure 변화로 다시 분해된다. flow와 fund momentum은 두 성분을 모두 예측하지만, 많은 stock characteristics의 return-gap 예측은 더 큰 체계적 위험을 취한 결과여서 순수 within alpha로 남지 않는다.

### 4.5. Abnormal versus total return prediction

동일 신경망으로 total return을 예측하면 stock characteristics의 예측력이 커진다. 그러나 이는 주로 시장·요인 노출의 공통성분을 맞히는 것이며, factor component를 제거하면 거의 사라진다. total-return 기반 long-short의 Sharpe는 abnormal-return 직접예측보다 낮다. 먼저 total return을 예측한 뒤 사후 무조건부 factor regression으로 alpha를 계산하는 것은 시점별 beta를 먼저 제거한 조건부 abnormal-return 예측과 같지 않다.

### 4.6. Time-variation in performance

성과 예측력은 시장심리에 따라 변한다. 고 sentiment 이후에는 상위와 하위 펀드의 realized spread가 크고, long-only 투자자도 상위 펀드에서 월 약 0.27% abnormal return을 얻는다. 반면 CFNAI별 차이는 약하다. 이 결과는 skill이 고정적으로 관측되는 것이 아니라 investor attention·flow와 시장심리의 결합에 따라 더 잘 드러남을 뜻한다.

## 5. Conclusion

신경망은 액티브 펀드의 장기적이고 경제적으로 큰 표본 외 abnormal-return 예측력을 발견한다. 이익의 상당 부분은 최악의 펀드를 피하는 데서 오지만, 10~20%의 펀드는 수수료 후에도 양의 alpha를 낸다. 핵심 신호는 flow와 fund momentum이며 고 sentiment가 그 효과를 증폭한다. 보유주식 특성은 순수 skill보다 systematic return을 예측한다.

방법론적으로 factor-model의 국소 잔차인 abnormal return을 직접 예측하고, 동일한 유연모형으로 정보집합을 비교하며, macro state를 고려한 교차 표본 외 평가와 prediction-weighting을 사용할 것을 제안한다. 결과는 펀드 위임·자금이동의 마찰과 투자자 sophistication 이론에 제약을 준다.

## Declaration of Competing Interest

저자들은 연구 결과에 영향을 줄 수 있는 경쟁적 재무 이해관계나 개인적 관계가 없다고 선언한다.

## Data availability

자료는 CRSP, Thomson Reuters, Compustat 등 라이선스 데이터와 공개 macro series로 구성되어 원자료의 공개 재배포에는 제약이 있다.

## Appendix A. Additional empirical results

기본 무작위 split의 추가 결과와 chronological·expanding-window 대안, 수수료 후 성과, 동일가중, 장기보유, interaction, 규모·예측대상 강건성을 제시한다.

### A.1. Random sampling method: Additional results

기본 random cross-out-of-sample 설계에서 본문의 결론을 다양한 포트폴리오 구성과 정보집합으로 반복한다.

#### A.1.1. Predicted top and bottom decile returns

상위의 양의 alpha와 하위의 더 큰 음의 alpha가 각각 유의하며, 전체 long-short 성과가 한쪽 극단에만 의존하지 않음을 확인한다.

#### A.1.2. After-fee abnormal returns

수수료 후 abnormal return을 직접 예측해도 상위 약 10~20%는 양의 성과, 하위는 큰 음의 성과를 보인다. 상·하위의 fee 수준이 비슷해 순위 spread의 원인은 보수 차이가 아니다.

#### A.1.3. Equally-weighted prediction portfolios

분위 내 동일가중도 유의한 예측 spread를 만들지만 prediction-weighting보다 작다. 예측치의 상대 강도까지 비중에 반영하는 것이 경제적 가치를 높인다.

#### A1.4. One-year holding period

목표변수를 다음 12개월 평균 abnormal return으로 바꾸어 직접 학습하면, 1개월 예측을 12개월 보유하는 방식보다 장기성과가 개선된다. 장기 horizon에서는 더 지속적인 펀드 특성의 중요도가 높아진다.

#### A1.5. Persistence of signals and classiﬁcation

예측 signal과 상·하위 분류가 여러 달 지속되고, 장기보유 성과가 단순한 월별 재분류 노이즈만으로 생긴 것이 아님을 보인다.

#### A1.6. Macroeconomic conditioning variables

sentiment와 CFNAI를 함께 또는 직교화해 넣어도 sentiment가 spread 크기와 fund-variable 효과를 조건화하는 핵심 변수다. CFNAI의 추가 설명력은 주로 수준효과다.

#### A1.7. Interaction effects

sentiment는 momentum·turnover·flow·reversal과 강하게 상호작용하지만 CFNAI는 거의 상호작용하지 않는다. fund variables끼리의 상호작용도 계산하며, 전역적 slope 차이로 비선형 효과를 정량화한다.

#### A1.8. Robustness to size of funds

TNA 1,500만 달러 미만 펀드를 제외하거나 value/prediction-value weighting을 적용해도 예측력이 유지된다. 결과가 소형·비투자가능 펀드에 의해 주도되지 않는다.

#### A1.9. Abnormal versus total return prediction

stock characteristics는 total return에는 유용하지만 사후 factor exposure를 보면 주로 systematic component를 예측한다. fund characteristics+sentiment가 abnormal-return 직접예측에서 우세하다.

#### A1.10. Turnover and expense ratios over time

상·하위 예측 포트폴리오 사이 expense와 turnover의 시간추세가 체계적으로 다르지 않다. 성과격차가 보수·거래활동 추세의 기계적 차이로 설명되지 않는다.

### A2. Chronological sampling method

시점을 시간순 세 fold로 나눈 교차 표본 외 평가에서도 fund skill 예측과 fund-information 우위는 유지된다. 다만 상태가 각 fold에 불균등해 sentiment 효과는 약해진다.

#### A2.1. Long-short portfolio results

상·하위 평균 skill spread는 random split과 비슷하다. stock information의 예측력이 다소 커지지만 2000년 이후 약해지고, fund momentum·flow·sentiment가 여전히 핵심이다.

#### A2.2. Holding period

1~36개월 보유기간에서도 long-short persistence가 유지되어 장기성과 결과가 무작위 시점배정에 의존하지 않는다.

#### A2.3. Interaction effects

chronological split에서는 sentiment interaction이 약하지만 momentum·단기반전·flow와의 효과는 여전히 유의하다. 고 sentiment가 없는 fold는 구조적으로 interaction을 식별하지 못한다.

#### A2.4. Predicting total returns

시간순 split에서도 total-return 예측 포트폴리오의 사후 alpha는 일부 유의하지만 factor R²가 있고, abnormal-return 직접예측의 상대적 장점이 남는다.

### A3. Expanding-window sampling method

1990년부터 매년 과거 자료만으로 모형을 갱신하는 실시간 가능 설계에서도 fund characteristics의 강한 예측력과 sentiment interaction이 재현된다. 평균 성과는 일부 감소하더라도 핵심 결론은 미래정보 사용의 산물이 아니다.

## Appendix B. Implementation: Tuning parameters

은닉층 1~여러 개, 노드 수, L1 패널티, learning rate, batch size, early stopping 후보를 validation으로 선택한다. 각 모형은 서로 다른 초기값 8회 적합을 평균한다. 펀드 abnormal-return 표본에서는 깊은 신경망보다 한 층 구조가 더 parsimonious하고 안정적이며, 복잡도가 증가하면 성능이 악화된다.

## Appendix C. Variable Importance and Interaction Effects: Statistical Significance Test

Horel and Giesecke의 한 층 신경망 대규모 표본이론을 확장해 gradient 기반 sensitivity와 macro interaction의 유의성을 검정한다. 부분미분 제곱 통계량의 점근분포를 Gaussian process와 함수 delta method로 유도하고 혼합 chi-square로 근사한다. 무작위 신경망으로 함수공간을 이산화하므로 bootstrap 재적합보다 계산이 저렴하며, 신경망 파라미터 비식별성에도 덜 민감하다.

## Supplementary material

온라인 보충자료에는 추가 자료정제, 변수정의, 표·그림, 모형 튜닝과 강건성 분석이 수록되어 있다.

## References

Carhart·Berk–Green의 펀드성과·자금흐름 문헌, holdings·return gap·active share 연구, Baker–Wurgler sentiment, 그리고 Gu et al. 계열의 금융 머신러닝 문헌을 결합한다. 핵심 차별점은 펀드 abnormal return을 직접 예측하고 정보집합과 macro interaction의 경제적 의미를 분리한 것이다.
