# Identifying the Effect of Stock Indexing: Impetus or Impediment to Arbitrage and Price Discovery

이 논문은 지수투자가 가격발견을 저해하는지 촉진하는지 Russell 지수 정기변경을 이용해 인과적으로 검증한다. 결과는 대형·중형주에서는 유의한 효과가 없지만, 사전 차익거래 제약이 강한 micro-cap에서는 지수 편입이 대차·유동성 제약을 완화하고 뉴스 반영 속도를 높인다는 것이다.

## Abstract

Russell 재구성 경계의 준무작위 지수 편입을 fuzzy 회귀불연속설계(RDD)로 분석한다. 지수투자는 large/mid-cap의 차익거래와 가격발견에는 식별 가능한 영향을 주지 않지만, micro-cap의 뉴스 반영 속도를 높인다. 작동경로는 대차공급 확대와 거래유동성 개선을 통한 정보거래 제약 완화다.

## I. Introduction

패시브 투자의 성장으로 가격 동조화와 정보효율 저하 우려가 커졌지만, 지수소유와 가격 특성 간 단순 상관관계는 기업 특성과 투자자 선택 때문에 인과해석이 어렵다. 저자들은 2007~2016년 Russell 2000의 상·하단 경계에서 시가총액이 근소하게 달라 지수 편입·퇴출이 갈리는 종목을 비교한다.

핵심 결과는 두 경계의 비대칭성이다. #1,000 경계의 large/mid/small 종목에서는 지수소유 변화가 크더라도 대차, 유동성, 동조성, 뉴스 반영 속도에 유의한 변화가 없다. 반면 #3,000 경계의 micro-cap 편입은 대차 제약 완화, 유동성 개선, 체계적 변동성과 동조성 증가, 시장·산업·기업·부정적 뉴스 반영 지연 감소를 낳고, 퇴출은 정반대다. 따라서 동조성 증가를 곧바로 기업고유 정보 감소로 해석해서는 안 된다.

## II. Research Design

Russell의 규칙 기반 연례 재구성에서 발생하는 지수소속 불연속을 도구변수로 사용한다. 실제 Russell 순위가 비공개이므로 공개 자료로 순위를 근사하고, 실제 편입확률의 불완전한 점프를 2단계 최소제곱 fuzzy RDD로 처리한다.

### A. The Annual Russell Reconstitution

매년 5월 말 rank day의 총시가총액으로 대상 종목을 정렬하고, 6월 말 Russell 1000·2000·3000E 구성을 갱신한다. #1,000 경계에는 기존 소속을 유지시키는 banding 때문에 상·하 두 개의 실질 경계가 있고, #3,000 경계는 Russell 2000과 3000E 사이 단일 경계다. 투명한 일정과 기계적 기준 때문에 경계 근처에서 외생적 지수수요 충격이 발생한다.

### B. Sample Construction

Markit 대차자료가 포괄적으로 제공되고 post-banding 제도가 일관되게 적용되는 2007~2016년 재구성을 사용한다. FTSE Russell의 3000E 구성, CRSP·Compustat의 가격·주식수, FactSet 기관소유, Markit 대차, CRSP 유동성, 애널리스트·경영진 정보환경 자료를 연결한다. 주 분석은 각 경계의 ±200 순위 bandwidth 안에서 편입·퇴출 종목과 이전 소속이 같은 정적(counterfactual) 종목을 비교한다.

### C. Instrument for Index Assignment Variable

비공개인 5월 말 Russell 총시가총액 순위를 Compustat과 CRSP 주식수 중 큰 값에 종가를 곱해 근사한다. 이를 각 공식 breakpoint에 대해 0 중심 순위로 변환하고, 이 순위가 예측하는 지수소속을 실제 6월 말 소속의 도구변수로 쓴다. 측정오차가 있어도 경계에서 강한 1단계 점프가 존재하면 fuzzy RDD 식별이 가능하다.

### D. Fuzzy Regression Discontinuity Design

예측 편입과 실제 편입이 완전히 일치하지 않으므로 sharp RDD가 아닌 fuzzy RDD를 사용한다. 결과변수는 대부분 재구성 전 1년에서 후 1년까지의 변화로 측정해 수준 차이를 제거한다.

#### 1. Two-Equation System

1단계에서 경계 통과 여부와 중심화 순위 및 상호작용으로 실제 Russell 2000 소속을 예측하고, 2단계에서 예측된 소속이 결과변수에 미치는 국소 평균처치효과를 추정한다. 선형 순위통제, ±200 bandwidth, 균등 kernel이 기본이며 Calonico et al.의 이분산 강건 근접이웃 분산을 사용한다.

#### 2. First-Stage Fuzzy RDD Results

도구변수는 매우 강하다. #3,000 하단에서 편입확률은 97%, 퇴출확률은 96% 점프한다. #1,000의 band 경계에서는 편입 88%, 퇴출 84%의 점프가 나타난다. 완전 순응은 아니지만 실제 지수배정을 강하게 예측한다.

#### 3. Local Randomization at the Reconstitution Cutoff

경계 양쪽에서 5월 말 시가총액과 이전 11개월 시가총액·순위 변화가 매끄럽고, McCrary 밀도검정도 불연속을 발견하지 못한다. 재구성 전 index/non-index/total 기관소유에도 체계적 점프가 없다. 기업이 순위를 정밀 조작했다는 증거가 없으므로 경계 근처의 국소 무작위성 가정을 지지한다.

## III. Identifying the Effect of Stock Indexing

먼저 추종기관의 강제 매매로 index ownership이 실제 불연속적으로 변하는지 확인한 뒤, 대차시장·유동성·가격동조성·변동성·뉴스 반영 지연의 변화를 추정한다. 영향은 사전 제약이 강한 #3,000 경계에 집중된다.

### A. Pre-Reconstitution Characteristics

#3,000 근처 micro/small-cap은 #1,000 근처 mid/large-cap보다 index ownership과 대여가능 주식이 적고, 대차재고 집중도·대차수수료·공매도위험·bid-ask spread·비유동성이 높다. 즉 하단 경계 종목은 사전 차익거래 제약이 훨씬 강해 동일한 지수수요 충격의 한계효과가 클 조건을 갖는다.

### B. The Effect of Stock Indexing on Index and Non-Index Ownership

#3,000에서 편입되면 index IO가 3.87%p 증가해 정적 3000E 종목의 사전 평균 대비 132% 늘고, 퇴출되면 4.31%p 감소해 정적 Russell 2000 평균 대비 50% 줄어든다. non-index IO 변화는 0과 구별되지 않아 처치가 추종기관의 기계적 매매임을 확인한다. #1,000에서도 편입 +3.35%p(25%), 퇴출 -2.91%p(19%)의 index IO 변화가 발생한다.

### C. The Effect of Stock Indexing on Securities Lending Conditions

#3,000 편입은 대여가능 물량을 3.22%p, 사전 평균 대비 38% 늘리고 대여자 재고집중도를 낮추며 실제 대차물량을 늘린다. 대차수수료는 0.87%p, 그 변동성으로 측정한 공매도위험은 0.62%p 하락한다. 퇴출은 대여가능 물량을 4.18%p(27%) 줄이고 집중도와 대차수수료(1.54%p)를 높인다. #1,000에서는 일부 대여물량 변화가 있어도 비용·위험까지 이어지는 일관된 완화효과가 약하다.

### D. The Effect of Stock Indexing on Liquidity

#3,000 편입 후 bid-ask spread가 0.47%p, 사전 평균 대비 39% 줄고 Amihud 비유동성과 가격비탄력성도 개선된다. 퇴출 후 spread는 0.26%p, 사전 평균 대비 57% 늘고 비유동성 지표도 악화된다. 반면 #1,000의 유동성 효과는 0과 구별되지 않는다. 이는 지수수요가 본래 유동적인 대형주보다 제약이 큰 micro-cap에서 거래조건을 실질적으로 바꾼다는 증거다.

### E. The Effect of Stock Indexing on Price-Synchronicity and Volatility

#3,000 편입은 시장·산업 수익률에 대한 가격동조성을 높이고 퇴출은 낮춘다. 편입의 동조성 증가는 기업고유 변동성 감소가 아니라 체계적 변동성 증가가 주도한다. 퇴출은 체계적 변동성이 크게, 고유 변동성이 작게 감소한다. #1,000에서는 동조성·변동성 변화가 유의하지 않다. 따라서 높은 동조성을 정보환경 악화의 증거로 단정할 수 없으며 뉴스 반영 속도를 직접 볼 필요가 있다.

### F. The Effect of Stock Indexing on the Speed of Price Adjustment to News

Hou–Moskowitz 방식의 시장·산업·기업 news delay와 실적발표일 고빈도 delay, 부정적 뉴스 delay를 사용한다. #3,000 편입은 모든 지연지표를 불연속적으로 낮춰 가격이 정보를 더 빨리 반영하게 하고, 퇴출은 지연을 늘린다. #1,000에서는 효과가 없다. 하단 경계에서 동조성 증가와 delay 감소가 함께 나타나므로, 이는 noise 증가보다 체계적·기업 정보의 더 신속한 반영으로 해석된다.

### G. Variation with Pre-Reconstitution Characteristics

사전 대차와 거래가 모두 어려운 micro-cap 편입종목에서 동조성 증가는 덜 제약된 종목의 약 2배, price delay 감소는 2~3배다. 애널리스트 커버리지와 경영진 가이던스가 부족한 정보환경에서도 효과가 더 강하다. 이는 지수 편입이 정보 자체를 대체한다기보다, 정보거래를 막던 차익거래 제약을 완화한다는 메커니즘과 부합한다.

### H. Sensitivity Checks

±100 bandwidth, Imbens–Kalyanaraman 최적 bandwidth, 삼각 kernel, 3차 순위통제, 연도 고정효과에서도 결론이 유지된다. 이전 지수소속으로 조건화하지 않고 경계 근처 전체 표본을 쓰는 대안적 RDD도 같은 방향의 결과를 낸다. 따라서 bandwidth·함수형태·표본조건화 선택에 대한 민감도가 낮다.

## IV. Conclusion

지수투자의 효과는 종목의 사전 차익거래 제약에 달려 있다. large/mid/small-cap 상단 경계에서는 유의한 변화가 없지만, micro-cap 하단 경계에서 편입은 대차공급과 유동성을 늘리고 시장·산업·기업 뉴스 반영을 빠르게 하며, 퇴출은 반대 효과를 낸다. 지수화가 언제나 가격발견을 해친다는 견해와 달리, 제약이 강한 종목에서는 정보거래를 촉진한다. 다만 Big 3의 소유·의결권 집중이라는 별도의 기업지배구조 문제는 남는다.

## Appendix A. Variable Definitions

주요 결과변수를 기관소유, 대차조건, 유동성, 가격동조성·변동성, 가격지연의 다섯 묶음으로 정의한다. 대부분 재구성 전후 1년의 변화로 사용한다.

### Institutional Ownership

INDEX_IO는 FactSet이 index 기관으로 분류한 보유자의 지분율, NON_INDEX_IO는 전체 기관지분에서 이를 뺀 값, TOTAL_IO는 13F·N-30D 보고기관의 총 지분율이다.

### Securities Lending Conditions

Markit 자료로 대여가능 물량, 실제 대차물량, 대여자 재고집중도, 주가 대비 대차수수료, 일별 대차수수료 변동성으로 측정한 공매도위험을 구성한다.

### Stock Liquidity Conditions

CRSP 종가 bid-ask spread, Amihud의 절대수익률/달러거래량 비율, Gao–Ritter의 절대수익률/주식회전율 비율을 사용한다. 값이 클수록 거래가 어렵다.

### Price Synchronicity and Volatility

주별 기업수익률을 동시점 시장·산업수익률에 회귀한 R²의 logit이 동조성이다. 회귀 적합성분과 잔차의 변동성으로 체계적·고유 변동성을 분해한다.

### Price Delay

시장·산업·기업수익률의 현재값만 쓴 모형과 과거값을 추가한 모형의 R² 차이로 delay를 계산한다. 실적발표일 주변 분별·일별 반응 및 부정적 뉴스만의 지연도 별도로 측정하며, 값이 클수록 가격반영이 느리다.

## Appendix B. FactSet Institutional Ownership Database

FactSet은 투자설명서·factsheet·감사보고서와 운용사 정보를 바탕으로 기관 단위에서 index/non-index 유형을 수작업 분류한다. 2020년 12월 기준 전 세계 84개 index 기관을 식별한다. 다만 Vanguard처럼 패시브와 액티브 펀드를 모두 가진 운용사를 기관 전체로 분류하므로 INDEX_IO에 측정오차가 있고, 이는 처치효과를 약화시키는 방향일 가능성이 크다.

## Appendix C. Sensitivity Checks

기본 ±200, 선형 순위통제, 균등 kernel, 이전 소속 조건화 결과를 다양한 bandwidth·kernel·다항식·고정효과와 비교한다. ±100은 전체 지수변경의 36%, ±200은 60%를 포착하며, 자료주도 MSE bandwidth에서도 주요 처치효과가 유지된다. 이전 소속으로 조건화하지 않은 전체 표본 결과도 일관적이다.

## References

연구는 Russell RDD 식별 문헌, 패시브 소유와 지배구조·정보생산 문헌, ETF·지수편입과 동조성 문헌, 공매도·대차·유동성 제약 문헌을 결합한다. 핵심 차별점은 index ownership만 보지 않고 대차→유동성→뉴스 반영 속도의 인과경로를 함께 검증한 것이다.
