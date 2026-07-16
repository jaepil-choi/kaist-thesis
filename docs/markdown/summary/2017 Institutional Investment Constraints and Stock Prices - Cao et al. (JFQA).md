# Institutional Investment Constraints and Stock Prices

이 논문은 위임운용기관의 분산투자·tracking-error 제약이 좋은 뉴스에 대한 추가매수와 나쁜 뉴스에 대한 추가매도를 막아 가격의 뉴스 반영을 늦추는지 검증한다. 1980~2013년 미국주식 13F 보유자료에서 기관이 이미 overweight한 winner와 이미 underweight한 loser의 가격조정이 특히 느리며, 이 제약이 momentum과 post-earnings announcement drift(PEAD)를 강화한다는 증거를 제시한다.

## Abstract

기관은 이미 overweight한 종목에 좋은 뉴스가 생겨도 추가매수하지 않고, 이미 underweight한 종목에 나쁜 뉴스가 생겨도 추가매도를 꺼린다. 그 결과 좋은 뉴스가 있는 overweight 종목은 이후 outperform하고, 나쁜 뉴스가 있는 underweight 종목은 이후 underperform한다. 기관보유 자체가 아니라 보유제약과 뉴스의 방향이 결합될 때 수익률 예측력이 생긴다는 것이 핵심이다.

## I. Introduction

기관투자자는 규제·계약·대리인 문제 때문에 포트폴리오 분산, 개별종목·산업 비중, turnover, 전략, benchmark 대비 tracking error에 제약을 받는다. 특히 분산요건과 benchmark에서 혼자 벗어날 위험인 “maverick risk”는 정보가 있더라도 포지션을 더 극단적으로 만들지 못하게 한다.

좋은 신호를 받은 종목을 이미 overweight했다면 buying constraint 때문에 수요곡선이 충분히 위로 이동하지 않아 가격이 저평가된다. 반대로 나쁜 신호를 받은 종목을 이미 underweight했다면 selling constraint 때문에 수요가 충분히 줄지 않아 가격이 고평가된다. 따라서 제약의 방향과 뉴스의 부호가 일치하는 극단에서 후속수익률 차이가 나타나고, 뚜렷한 뉴스가 없는 종목에서는 차이가 없어야 한다.

논문의 차별점은 기관이 informed하다는 무조건부 설명과 달리 정보·제약의 상호작용을 검증하는 데 있다. 최근 기관 순매수·순매도만으로는 후속수익률을 예측하지 못하지만, 거래 후 binding constraint에 도달한 경우에만 정보가 지연 반영된다는 설명이다. 공매도 제약이 아니라 보유주식에도 적용되는 buy-side의 매수·매도 제약을 함께 다룬다는 점도 중요하다.

## II. Data and Methodology

### A. Data

표본은 1980년 1분기부터 2013년 4분기까지 NYSE·AMEX·NASDAQ 보통주다. CRSP와 Compustat을 결합하고, REIT·closed-end fund·ADR, 주가 5달러 미만, 직전 연말 NYSE 시가총액 하위 10분위를 제외한다.

기관보유와 거래는 Thomson Reuters 13F 자료를 사용한다. 운용자산 1억 달러 이상 기관의 분기말 보유를 관찰하며, stock split과 100% 초과 aggregate ownership 등 오류를 점검·보정한다.

### B. Identifying Constrained Stocks

첫 번째 제약지표인 overweight ratio는 각 기관이 보유한 종목의 실제 포트폴리오 비중을 동일 보유종목으로 만든 시가총액가중 포트폴리오의 비중과 비교한다. 종목별로 그 종목을 overweight한 기관 수를 보유기관 수로 나눈다. 값이 높으면 많은 기관이 이미 크게 보유해 추가매수 제약이, 낮으면 추가매도 제약이 강한 것으로 해석한다.

원시 overweight ratio는 size, S&P 500 편입, book-to-market, momentum과 관련되므로 분기별 횡단면 회귀의 잔차를 본 분석의 overweight ratio로 사용한다. 이 구성으로 size·value·momentum에 따른 기관 선호를 제거한다.

두 번째 지표인 residual institutional ownership(RES_IO)은 aggregate institutional ownership을 동일한 기업특성에 회귀한 잔차다. 양의 RES_IO는 유사종목보다 기관이 많이 보유한 aggregate overweight, 음의 값은 underweight를 뜻한다. 개인기관의 overweight 빈도를 보는 첫 지표와 aggregate 보유규모를 보는 RES_IO는 상호보완적이며 횡단면 상관의 시계열 평균은 0.6이다.

### C. Information Proxies

첫 뉴스 proxy는 직전 6개월 수익률이다. 매 분기 winner·loser 5분위를 만들어 최상위는 좋은 뉴스, 최하위는 나쁜 뉴스로 본다. 이 설계는 momentum과 제약지표를 독립적으로 정렬해 제약의 증분효과를 식별한다.

두 번째 proxy는 IBES 실제 EPS에서 직전 consensus forecast를 뺀 뒤 주당 장부가치로 표준화한 earnings surprise(SUE)다. 이익공시 전의 사적정보 이용제약뿐 아니라 공시 후 급등락이 포지션 제약을 더 binding하게 만들어 기관이 뉴스 반대방향으로 거래하는 경로까지 포착한다.

## III. Investment Constraints and Demand for Stocks

overweight ratio 또는 RES_IO로 3분위 포트폴리오를 만든 뒤 전후 6개월의 institutional ownership과 두 제약지표 변화를 비교한다. 기관은 현재 underweight한 종목의 ownership을 다음 6개월에 1.48% 늘리지만 overweight 종목은 0.01% 줄인다. 두 제약지표도 0을 향해 강하게 평균회귀한다.

이 패턴은 기관이 benchmark에서 계속 멀어지는 거래를 하지 못한다는 가설과 일치한다. overweight 종목의 추가매수와 underweight 종목의 추가매도가 억제된다는 직접적인 수요 증거이자 두 제약지표의 construct validity 검정이다.

## IV. Investment Constraints and Stock Returns

### A. Overweight Ratio and Future Stock Returns

직전 6개월 수익률 5분위와 overweight ratio 3분위를 독립적으로 교차해 15개 포트폴리오를 만들고 이후 3·6개월 동일가중 수익률을 비교한다. 각 cell은 평균 약 135종목이고 size 분포도 비슷해 결과가 소형주 편향으로 설명되지 않는다.

6개월 보유에서 high-OR winner는 low-OR winner보다 월 0.29%, high-OR loser는 low-OR loser보다 월 0.30% 높다. size·book-to-market 조정 후에도 winner와 loser 양극단에서 약 0.24%의 차이가 남지만 중간 2~4분위에서는 유의하지 않다. 제약지표의 예측력이 뉴스 양극단에만 나타나는 U자형 패턴이다.

제약을 반영한 momentum 전략, 즉 overweight winner 매수·underweight loser 매도는 월 0.91%를 벌지만 반대 조합은 0.32%에 그친다. 두 전략의 월 0.59% 차이는 기관제약이 기존 momentum 수익의 강도를 조건화함을 보여준다.

### B. Alternative Measures

RES_IO를 사용해도 high-RES_IO와 low-RES_IO의 6개월 후 월수익률 차이는 winner에서 0.45%, loser에서 0.39%이고 중간 수익률 분위에서는 0.1% 미만으로 유의하지 않다. high-RES_IO winner 매수·low-RES_IO loser 매도는 월 1.02%를 벌지만 반대 조합은 0.19%로 0과 다르지 않다.

이익공시에서도 같은 구조가 나타난다. 가장 긍정적인 surprise에서는 high-OR 종목이 low-OR보다 공시 후 60거래일 동안 0.94% 더 오르고, 가장 부정적인 surprise에서는 underweight 종목의 drift가 더 음(-0.86% 차이)이다. RES_IO에서도 유사하다. 즉 PEAD도 행동편향뿐 아니라 기관의 포지션 제약으로 강화될 수 있다.

효과는 long-only 기관의 매도제약이 더 직접적으로 binding해지는 부정적 뉴스 쪽에서 더 크다. factor alpha와 characteristic-adjusted return에서도 constrained loser의 효과가 constrained winner보다 대략 두 배여서 buy·sell 제약의 비대칭성과 일치한다.

### C. Further Robustness Checks and Alternative Explanations

뉴스 horizon을 3개월·12개월로 바꾸거나 정렬 수와 포트폴리오 형성빈도를 바꾸고, 제약지표를 한 분기 더 lag하거나, 대형주·소형주 및 1980~1995·1996~2013 하위기간을 나누어도 결론이 유지된다. Fama–French 3-factor alpha와 Fama–MacBeth 회귀도 같은 U자형 상호작용을 확인한다.

Fama–MacBeth 회귀에서 OR·RES_IO와 winner/loser dummy의 상호작용은 유의하지만 이를 포함하면 제약지표의 단독효과는 사라진다. OR loser 상호작용 계수는 포트폴리오 정렬에서 관찰한 크기와 가까운 다음 분기 월 0.27%의 high-low 차이를 뜻한다.

제약이 강한 quasi-indexer에서는 결과가 뚜렷하지만 benchmark가 불분명하고 적극적으로 거래하는 transient institution에서는 훨씬 약하거나 유의하지 않다. 이는 단순 기관정보보다 tracking-error 제약의 설명과 더 잘 맞는다.

최근 기관거래만 정렬하면 순매수 종목이 순매도 종목보다 이후 outperform하지 않는다. 그러나 최근 매수해 현재 overweight가 된 종목은 최근 매도해 underweight가 된 종목보다 월 약 0.28% 높다. 정보우위가 있더라도 거래가 binding constraint에 도달했을 때만 가격 반영이 지연된다는 핵심 식별 결과다.

## V. Conclusions

분산투자·tracking-error 제약은 기관의 정보수요를 둔화시켜 좋은 뉴스가 있는 overweight 종목을 저평가하고 나쁜 뉴스가 있는 underweight 종목을 고평가한다. 이 왜곡은 momentum과 PEAD를 강화하며, 기관의 보유·거래가 가격발견을 항상 개선한다는 단순한 관점을 반박한다.

실증적으로 중요한 것은 institutional ownership이나 trading의 수준 자체가 아니라 현재 포지션이 어느 방향의 제약에 가까운지와 뉴스 부호의 결합이다. 따라서 위임운용의 계약·규제·career concern은 기관이 anomaly를 제거하지 못하게 할 뿐 아니라 anomaly의 형성에도 기여할 수 있다.

## References

기관선호·13F 거래, delegated portfolio management, limits to arbitrage, momentum과 PEAD 문헌을 연결한다. 핵심 기여는 보유자료로 buy-side 제약을 측정하고 뉴스와의 조건부 상호작용을 통해 가격지연 경로를 직접 보인 것이다.
