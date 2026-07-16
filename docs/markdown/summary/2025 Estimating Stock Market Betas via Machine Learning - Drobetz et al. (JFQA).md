# Estimating Stock Market Betas via Machine Learning

이 논문은 미국 개별주식의 향후 1년 시장 beta를 81개 변수와 여러 머신러닝 모형으로 예측하고 전통적 추정량과 비교한다. random forest(RF), gradient-boosted regression trees(GBRT), 1층 neural network가 통계적 예측오차와 포트폴리오의 경제적 성과에서 우세하며, RF가 전반적으로 가장 좋다.

## Abstract

머신러닝 beta 추정량은 forecast·hedging error를 낮추고 시장중립 anomaly 전략과 minimum variance portfolio(MVP)를 개선한다. 과거 beta, turnover, size가 가장 중요한 예측변수이고, 필요한 모형 복잡도와 변수 중요도는 시간에 따라 크게 변한다. 동일 변수를 쓰는 선형회귀보다 비선형성과 상호작용을 허용한 모형이 유의하게 좋다.

## I. Introduction

beta는 자본비용, 성과평가, 위험관리, 헤징, 포트폴리오 구성에 널리 쓰이지만 관측되지 않고 시간가변적이어서 미래값 예측이 필요하다. 저자들은 rolling, shrinkage, portfolio, long-memory benchmark와 선형·tree·neural-network 모형을 미국 전체 상장주식의 장기 표본에서 비교한다.

RF의 시가총액가중 MSE는 1년 일별 rolling beta보다 평균 20% 낮고, 약 70%의 표본 월에서 유의하게 우세하며 model confidence set에 두 배 이상 자주 포함된다. GBRT와 NN도 비슷하게 좋다. 우위는 경기침체 전후, small·illiquid·value·loser 주식처럼 beta 예측이 어려운 곳에서 더 크다. 머신러닝은 낮은 beta를 과소추정하고 높은 beta를 과대추정하는 전통 모형의 극단오차를 줄인다.

경제적으로도 anomaly의 ex post beta를 0에 가깝게 만들고 momentum·idiosyncratic volatility·betting-against-beta alpha와 MVP 위험·수익 특성을 개선한다. RF의 복잡도는 어려운 시기에 높아지고, 과거 beta·기술지표·회계정보의 중요도가 크다. 단순히 많은 변수를 쓰는 선형모형은 충분하지 않으며 비선형·상호작용 포착이 핵심이다.

## II. Literature Review

전통적 beta 추정은 5년 월별 또는 1년 일별 rolling OLS에서 출발하지만 window 선택의 bias–variance trade-off와 이상치 때문에 변동적이고 극단적인 값을 낸다. EWMA, slope winsorization, Vasicek·Karolyi shrinkage, 기업특성 기반 hybrid shrinkage, portfolio beta, long-memory 모형이 이를 개선해 왔다.

기존 머신러닝 자산가격 연구는 주로 기대수익·총변동성 예측에 집중했다. beta 예측의 선행연구는 소수 대형주와 제한된 tree 모형만 비교했다. 이 논문은 광범위한 benchmark, neural network, 전체 미국주식·장기표본·81개 predictor, anomaly와 MVP 응용, 시간가변 복잡도와 변수중요도까지 함께 분석한다.

## III. Data

CRSP 일·월별 수익률과 Compustat 회계자료를 사용하며, 1970년 3월~2020년 12월 NYSE·AMEX·NASDAQ 상장 이력이 있는 모든 기업을 포함한다. 생존편향이 없고 월평균 1,806종목이며 최초 표본 외 beta는 1979년 12월에 산출한다.

81개 predictor는 여러 horizon의 과거 beta, 회계특성, 기술지표, default spread, Fama–French 47개 산업 dummy로 구성된다. 장부가치 비음수, 매출·거래대금 양수, 현재와 과거 36개월 수익률, 모든 beta·predictor 관측 조건을 적용한다. 기업특성은 월별 0.5·99.5 percentile winsorization 후 횡단면 순위를 [-1,1]로 변환하고 결측을 횡단면 회귀로 보정한다. 시장자료는 즉시, 회계자료는 결산 4개월 후 이용 가능하다고 가정한다.

## IV. Forecast Models

매월 t까지의 정보로 t+1부터 t+12까지 1년 realized beta를 예측하고, 다음 달로 이동하는 중첩 표본 외 예측을 만든다. realized beta는 향후 1년 일별 개별주식·시장수익률의 공분산/시장분산으로 측정하며, 평가손실은 월별 시가총액가중 MSE다.

### A. Benchmark Estimators

네 계열을 비교한다. rolling-window는 5년 월별·1년 일별 OLS와 단·장기 EWMA를, shrinkage는 slope-winsorized·Vasicek·Karolyi·기업특성 hybrid beta를 포함한다. 추가로 Fama–French 방식 portfolio beta와 beta 시계열 지속성을 활용한 long-memory 추정량을 사용한다. 단순 rolling보다 정교한 최신 benchmark까지 포함해 머신러닝의 증분가치를 보수적으로 평가한다.

### B. Machine Learning Estimators

과거 beta와 기업·시장 특성에서 향후 realized beta의 조건부 기대값을 직접 학습한다. 모든 모형은 validation MSE 최소화를 목표로 하며, 선형·비선형·parametric·nonparametric 함수족의 차이만 있다.

#### 1. Sample Splitting

시간순서를 보존해 9년 training, 1년 validation, 1년 test로 나눈다. validation에서 hyperparameter를 선택하고 test는 추정·튜닝에 전혀 사용하지 않는다. 매년 window를 1년씩 이동해 모형을 재적합하며 1979년 12월부터 2019년 12월까지 총 40년 1개월의 표본 외 평가를 얻는다. 이 설계는 model·backtest overfitting을 줄인다.

#### 2. Machine Learning Techniques

선형계열은 pooled OLS(LM)와 고차원 과적합을 줄이는 elastic net(ELANET)이다. tree 계열은 RF와 GBRT로 비선형 threshold와 변수 상호작용을 자동 포착한다. neural network는 ReLU 기반 구조를 비교하며 가장 단순한 1층 NN_1이 깊은 구조보다 안정적이다. 모형 복잡도 관련 hyperparameter는 매년 validation에서 적응적으로 선택한다.

## V. Statistical Analysis of Market Beta Forecasts

평균 forecast error, model confidence set, Diebold–Mariano 검정, 시계열·횡단면 분해와 hedging error로 통계적 성능을 평가한다. RF·GBRT·NN_1이 일관되게 상위다.

### A. Forecast Errors

rolling beta의 평균 MSE는 9.44~19.17%로 크다. 개선된 benchmark 중 slope-winsorized 8.77%, hybrid 8.53%, long-memory 8.29%가 가장 좋다. RF·GBRT·NN_1은 7.77~8.04%로 이를 더 낮추지만, LM 9.15%와 ELANET 8.89%는 열위다. 따라서 predictor 수 증가만으로는 부족하고 비선형·interaction이 필요하다.

RF는 1년 일별 rolling 대비 평균 MSE가 20% 낮고, 침체기·침체 직후처럼 beta가 불안정한 때 상대적 개선이 더 크다. 머신러닝 추정치는 분산과 극단값이 작고 model confidence set 포함비율과 ex post hedging error에서도 우세하다. 다른 forecast horizon, 동일가중 MSE, MAE, 추가 macro 변수, 다른 factor beta에서도 결론이 유지된다.

### B. Forecast Errors of Cross-Sectional Portfolio Sorts

예측 beta 10분위에서 전통 모형은 low-beta의 실제 beta를 과소추정하고 high-beta를 과대추정하는 평균회귀형 오류가 뚜렷하다. 머신러닝은 모든 분위의 MSE를 줄이고 오류분포를 더 균일하게 만들며 양 극단의 방향성 bias를 거의 제거한다.

firm characteristics별로도 RF는 거의 모든 그룹에서 rolling·linear 모형보다 좋다. 개선폭은 small, illiquid, high book-to-market(value), 과거 loser 주식에서 특히 크다. 이 종목들은 회계·거래 특성의 추가정보가 중요하고 전통적 역사수익률 추정이 가장 불안정한 집단이다.

## VI. Economic Value of Market Beta Forecasts

통계적 정확도가 실제 포트폴리오 의사결정을 개선하는지 anomaly hedging, 시장중립 anomaly 성과, 단일요인 공분산 기반 MVP로 검증한다. 기대수익 예측이 필요한 일반 최적화는 범위에서 제외해 beta 정보의 직접가치에 집중한다.

### A. Anomaly Portfolio Hedging

size, book-to-market, illiquidity extreme decile long·short 포트폴리오가 사전 beta 1, long-short beta 0이 되도록 추정 beta로 비중을 조정한다. benchmark 기반 포트폴리오는 ex post beta가 0에서 유의하게 벗어나는 경우가 많지만 RF·GBRT·NN_1은 실제 시장중립에 더 가깝다. 이는 낮은 평균 MSE가 hedge 대상의 방향성 beta 오류 감소로 이어짐을 보여준다.

### B. Anomaly Portfolio Performance

시가총액이 NYSE 20 percentile 이상인 투자가능 주식으로 momentum, idiosyncratic volatility, betting-against-beta 전략을 만들고 매월 예측 beta만큼 시장포트폴리오로 hedge한다. momentum의 FF5 alpha는 1년 rolling beta 8.62%, 최상 benchmark long-memory 9.44%에 비해 RF 9.79%, GBRT 9.74%, NN_1 9.49%다. 더구나 benchmark 전략의 realized beta는 유의하게 음수인 반면 머신러닝은 0과 구별되지 않는다.

idiosyncratic volatility와 BAB에서도 머신러닝은 높은 alpha와 더 정확한 시장중립성을 보인다. 즉 일부 높은 수익은 잔존 시장노출이 아니라 더 나은 beta 추정에 기반한다.

### C. Minimum Variance Portfolios

예측 beta와 과거 1년 시장·고유분산으로 단일요인 공분산행렬을 만들고, 공매도 금지·종목당 5% 상한·완전투자 조건에서 매월 MVP를 구성한다. 머신러닝 MVP는 가장 낮은 전체·하방 변동성, 덜 나쁜 최저수익과 drawdown, 높은 평균수익·terminal value·Sharpe를 보인다.

순수 MVP의 ex post beta 차이가 결과를 설명하지는 않는다. 예상 MVP beta만큼 시장을 hedge하면 RF·GBRT·NN_1은 realized beta가 0인 시장중립 MVP를 만들지만 모든 benchmark는 0에서 유의하게 벗어난다. 전·후반기 분할에서도 성과가 안정적이다.

## VII. Properties and Operating Scheme of Machine Learning Estimators

가장 우수한 RF를 중심으로 “black box”의 작동방식을 복잡도와 변수기여도로 해석한다. GBRT와 NN에서도 질적으로 유사한 패턴이 나타난다.

### A. Model Complexity

RF에 포함되는 tree 수를 매년 선택된 모형 복잡도로 본다. 복잡도는 2000~2009년, 특히 2001년 말에 높고 2010년대에는 낮다. validation MSE와 복잡도의 상관은 0.90으로, 예측이 어려운 시장에서는 더 복잡한 함수가 필요하다.

반면 test MSE와 복잡도의 상관은 -0.06, rolling 대비 상대개선과는 0.17로 유의하지 않다. 높은 복잡도가 곧 표본 외 오류나 상대성과 악화를 뜻하지 않는 것은 validation으로 적응적 tuning이 작동했기 때문이다. 복잡도를 고정하기보다 시장상태에 맞춰 선택해야 한다.

### B. Variable Importance

각 predictor를 training 표본의 중립적 중앙값으로 바꿀 때 MSE가 얼마나 증가하는지 계산하고 합이 1이 되도록 정규화한다. 과거 beta 묶음이 전체 중요도의 60% 이상을 차지하며, 기술지표와 회계변수가 뒤따르고 macro·산업정보는 평균적으로 작다. 개별 상위 변수는 여러 horizon의 beta, turnover, size이며 상위 5개가 82.99%를 설명한다.

그러나 중요도는 시간가변적이다. 평균적으로 하위인 29개 변수도 특정 시기에는 합계 기여가 거의 30%에 이르고, 금융위기처럼 다른 시기에는 매우 작다. 따라서 평균 중요도만으로 변수를 영구 제거하면 조건부 정보를 잃을 수 있다. 종합 predictor set과 비선형 interaction이 RF 우위의 핵심이다.

## VIII. Conclusion

미국 전체주식의 장기 표본에서 RF, GBRT, NN은 전통적 beta 추정량보다 forecast·hedging error가 작고 anomaly 헤징과 MVP 구성도 개선한다. RF가 가장 우수하지만 tree와 얕은 neural network의 공통된 장점은 덜 극단적이고 더 안정적인 beta 예측이다.

성과우위는 많은 기업특성의 공동정보를 이용하는 것과, 선형모형이 놓치는 비선형·상호작용을 포착하는 데서 온다. 과거 beta가 가장 중요하지만 predictor의 기여와 필요한 복잡도가 시간에 따라 변하므로, 적응적 validation과 포괄적 정보집합이 실무 적용의 핵심이다.

## Supplementary material

보충자료에는 benchmark와 머신러닝 구현·hyperparameter, 다른 forecast horizon·손실함수·factor beta, 표본분할, macro 변수, MVP 하위기간, 비선형·interaction 사례 등 광범위한 강건성 검정이 수록되어 있다.

## References

CAPM과 시간가변 beta, rolling·shrinkage·portfolio·long-memory 추정, 기업특성 기반 beta, 금융 머신러닝, anomaly hedging과 MVP 문헌을 연결한다. 논문의 핵심 차별점은 예측 정확도뿐 아니라 경제적 활용과 black-box 해석을 하나의 장기 표본에서 함께 평가한 것이다.
