# Key Paper 후보 정리

`paper-search` skill(OpenAlex, `config/key-paper.yaml`의 tier 1~4 저널)로
찾은 thesis key paper 후보들을 기록한다. 학교 best practice: prestigious
journal의 key paper를 골라 한국 데이터로 replicate/extend.

## 상태: 유력 후보 (아직 최종 확정 아님)

### 1. Estimating Stock Market Betas via Machine Learning

- **저자**: Wolfgang Drobetz, Fabian Hollstein, Tizian Otto, Marcel Prokopczuk
- **저널**: Journal of Financial and Quantitative Analysis (tier 2), 2024
- **피인용**: 20
- **DOI**: https://doi.org/10.1017/s0022109024000036
- **OpenAlex ID**: W4391648532

**Abstract 요약**: ML 기반(random forest가 최고 성능) 주식시장 beta
추정치가 기존 벤치마크 모델보다 forecast error·hedging error 모두 낮음.
Time-varying beta의 model complexity는 시간에 따라 크게 변함. 가장 중요한
예측 변수는 과거 beta·turnover·size. 개선된 beta 추정치로 만든
market-neutral anomaly 전략과 minimum-variance 포트폴리오가 선형회귀 기반
beta보다 성과가 좋음.

**왜 후보인가**: 실증논문이고 tier-2 prestigious journal이며, 방법론이
명확함(ML beta 추정 → anomaly/min-variance 포트폴리오 구성 → 성과 검증) —
한국 주식 데이터로 replicate 가능. 앞서 논의했던 covariance
matrix/tracking-error 추정 문제(beta도 결국 covariance의 함수)와 연결되며,
이는 enhanced index/benchmark-relative 포트폴리오 구성의 실무적
추정 레이어에 해당함.

### 2. Cross-sectional expected returns: new Fama–MacBeth regressions in the era of machine learning

- **저자**: Yufeng Han, Ai He, David E. Rapach, Guofu Zhou
- **저널**: European Finance Review (tier 2), 2024
- **피인용**: 43
- **DOI**: https://doi.org/10.1093/rof/rfae027
- **OpenAlex ID**: W4402028449

**Abstract 요약**: 고전적인 Fama-MacBeth regression 프레임워크를 빅데이터·ML
시대에 맞게 확장 — regularization + predictor selection, forecast
combination, encompassing의 3단계 절차. 200개 이상의 firm characteristics에
적용해서 out-of-sample 예측정확도와 economic value를 표준 Fama-MacBeth
대비 유의미하게 개선. 횡단면 예측력 평가를 위한 새로운 성과지표(시계열
out-of-sample R²의 횡단면 버전 등)도 제안.

**왜 후보인가**: Tier-2 저널이고, 한국 실증 자산가격결정 연구에서도 이미
표준적으로 쓰이는 도구(Fama-MacBeth)를 확장한 것이며, 저자들이 구현·해석이
쉽다는 점을 직접 강조함. 이 ML 확장판 Fama-MacBeth 절차를 한국
firm characteristics에 적용하는 건 방법론적으로 자연스럽고 선례가 많은
replication 설계.

### 문헌 추적 결과 (references / citing papers)

두 논문의 references(이론적 계보)와 citing papers(그 이후 누가 뭘 했는지)를
OpenAlex로 추적해서 gap이 아직 열려있는지 확인.

**References**: 둘 다 견고하고 정통적인 계보로 이어짐 — 특별한 이슈 없음.
Beta 논문: Sharpe(1964), Lintner(1966), Fama-MacBeth(1973),
Fama-French(1993), Bollerslev-Engle-Wooldridge의 time-varying-beta
CAPM(1988), Newey-West(1987). Fama-MacBeth ML 논문: Lasso(Tibshirani
1996), Elastic Net(Zou & Hastie 2005), Adaptive Lasso(Zou 2006),
forecast combination/encompassing 문헌, Jegadeesh-Titman 모멘텀(1993).

**Citing papers — 위험 신호**: "Machine Learning Forecasts of Asymmetric
Betas Using Firm-Specific Information" (2026, OpenAlex에 아직 abstract
없음, working paper로 추정)가 **우리 후보 두 논문을 모두 인용**함. 제목상
firm characteristics 기반 예측(Fama-MacBeth ML 논문의 접근)과 asymmetric
beta 예측(beta 논문의 확장)을 이미 결합했을 가능성이 있음 — 우리가 생각하던
결합 방향과 거의 같은 방향으로 보임. **본격적으로 결합 방법론 설계에
들어가기 전에 SSRN/구글 스콜라에서 직접 확인 필요** (OpenAlex엔 아직
abstract가 없음).

**Citing papers — 안심 신호**: "Time-Varying Betas and Effects of Data
Frequency and Estimation Window Preferences: Case of Istanbul Stock
Exchange" (2025)가 beta 논문의 "단일 국가 replication" 사례처럼 보였으나,
확인해보니 Drobetz et al.의 ML 방법론이 아니라 단순 rolling/recursive
regression을 쓴 논문 — 그냥 literature review에서 beta 논문을 인용만 함.
따라서 미국 외 단일 시장(예: 한국)에 ML 기반 beta(또는 ML 기반
Fama-MacBeth)를 적용하는 연구는 아직 열려 있는 gap으로 보임.

**Citing papers — 유용한 방법론적 근거**: "Empirical Asset Pricing via
Machine Learning: The Role of Research Design Choices" (2025) —
5,376개 포트폴리오(설계 선택 8개 × ML 모델 7개)를 분석한 결과, 임의적 설계
선택에서 오는 "nonstandard error"가 일반 standard error의 최대 5배에
달함. 거래비용 반영 후에는 약 1/3의 포트폴리오만 유의미한 수익을 냄. ML
기반 설계를 신중하고 투명하게 해야 하는 이유를 뒷받침하는 인용문헌으로
유용 — 아래 Ang et al.의 "prudent practitioner" 회의론과도 통함.

## 이 리서치 흐름이 시작된 배경

원래는 regulatory constraint(예: cap-weight 규정) 하에서의 enhanced index
fund 성과와, long-short alpha 시그널을 long-only over/underweight로
최적으로 치환하는 문제에 관심이 있었음. 이 프레이밍의 key paper들(Grinold
& Kahn 2000; Clarke, de Silva & Thorley 2002; Clarke, de Silva, Sapra &
Thorley 2008)은 practitioner journal(FAJ, JPM)에 있지 tier 1~3 학술지에
있지 않고, 주제 자체도 국가 간 실증 replication 구조를 자연스럽게 갖기보다는
constrained-optimization/방법론 문제에 가까워서 — 학교의 "prestigious
journal key paper를 한국 데이터로 replicate" 기준과는 잘 안 맞음. 이후
인접 문헌(active share/closet indexing, ESG rating-performance trade-off,
ML 기반 fund manager skill, ML 기반 portfolio construction)을
`config/key-paper.yaml`에 설정된 저널들에서 2005~2026년 구간으로 폭넓게
키워드 검색해서 탐색함 — 결과는
`scratch-pad-for-ai/outputs/papers_2005_2026.csv`,
`scratch-pad-for-ai/outputs/ml_2020_2026.csv` 참고 (gitignore 처리되어
레포에는 저장되지 않음).

## Enhanced index fund / transfer coefficient 문헌 (원래 방향, 보류/아카이브)

Thesis key paper로는 채택하지 않기로 함(위 배경 참고 — practitioner
journal, "한국 데이터로 replicate" 기준과 맞지 않음). 다만 출발점이었고
motivation/framing이나 나중에 다시 이 방향으로 돌아올 경우를 위해 전체
내용을 기록해둠.

### 핵심 이론 논문

**Grinold, R. C., & Kahn, R. N. (2000). The Efficiency Gains of Long-Short Investing.**
*Financial Analysts Journal*, 피인용 93. DOI: [10.2469/faj.v56.n6.2402](https://doi.org/10.2469/faj.v56.n6.2402). OpenAlex: W2118540747.
Efficiency를 "구현된(최적) 포트폴리오의 IR / alpha의 intrinsic IR"로 정의;
long-only 제약의 efficiency 비용을 보이고, enhanced(저위험) long-only
전략을 명시적으로 다룸.

**Clarke, R., de Silva, H., & Thorley, S. (2002). Portfolio Constraints and the Fundamental Law of Active Management.**
*Financial Analysts Journal*, 피인용 253. DOI: [10.2469/faj.v58.n5.2468](https://doi.org/10.2469/faj.v58.n5.2468). OpenAlex: W1863029622.
Transfer coefficient 개념의 원조 논문 — Grinold의 fundamental law of
active management를 제약(short-sale, turnover, market-cap/style
neutrality, sector 제약) 하의 포트폴리오로 일반화, 성과분석을 위한 ex
ante/ex post correlation 관계 제시.

### 방법론 보완 논문

**Clarke, R., de Silva, H., Sapra, S. G., & Thorley, S. (2008). Long–Short Extensions: How Much Is Enough?**
*Financial Analysts Journal*, 피인용 15. DOI: [10.2469/faj.v64.n1.4](https://doi.org/10.2469/faj.v64.n1.4). OpenAlex: W2124644747.
Benchmark 구성, security covariance matrix, 최적화 파라미터의 함수로서
long-short extension(예: 130/30)의 최적 규모를 구하는 analytical model.

**Clarke, R., de Silva, H., & Thorley, S. (2005). Performance Attribution and the Fundamental Law.**
*Financial Analysts Journal*, 피인용 17. DOI: [10.2469/faj.v61.n5.2758](https://doi.org/10.2469/faj.v61.n5.2758). OpenAlex: W2072630071.
같은 저자 팀이 2002년 fundamental-law 프레임워크를 ex post 성과 attribution과
연결한 후속작. 2002년 논문의 citation을 추적하다가 새로 발견함 — 아직 깊게
읽지 않음.

**Tol, R., & Wanningen, C. (2011). 130/30: By How Much Will the Information Ratio Improve?**
*The Journal of Portfolio Management*, 피인용 6. DOI: [10.3905/jpm.2011.37.3.062](https://doi.org/10.3905/jpm.2011.37.3.062). OpenAlex: W2098738581.
실증연구: 미국 대형주 130/30 vs long-only 상품 42개 매칭 쌍. Transfer
coefficient가 long-only tracking error에 따라 약 40~50% 개선되며,
"sweet spot"은 tracking error 2~3% 구간.

### Citation 추적으로 찾은 2020~2026년 확장 논문

**Lo, A. W., & Zhang, R. (2024). Performance Attribution for Portfolio Constraints.**
*Management Science*, 피인용 2. DOI: [10.1287/mnsc.2024.05365](https://doi.org/10.1287/mnsc.2024.05365). OpenAlex: W4405724285.
Clarke et al.(2002) 계열의 현대적 후속작: constrained portfolio의 성과를
(1) unconstrained mean-variance 최적해, (2) 개별 static constraint,
(3) constraint 자체에 담긴 정보로 분해; Bayesian estimation risk
분석으로 확장. 지금까지 찾은 것 중 가장 직접적인 이론적 후속작 — enhanced
index 방향을 다시 검토한다면 가장 유력한 후보.

**Ang, A., Chen, L., Gates, M. D., & Henderson, P. (2021). Index + Factors + Alpha.**
*Financial Analysts Journal*, 피인용 5. DOI: [10.1080/0015198x.2021.1960782](https://doi.org/10.1080/0015198x.2021.1960782). OpenAlex: W3200035552.
Index 노출·factor 노출·순수 alpha 간 최적 배분을 위한 Bayesian
방법론, 각 수익원의 information ratio에 대한 prior 사용.

**Joenväärä, J., & Kosowski, R. (2020). The Effect of Regulatory Constraints on Fund Performance: New Evidence from UCITS Hedge Funds.**
*European Finance Review*, 피인용 0. DOI: [10.1093/rof/rfaa017](https://doi.org/10.1093/rof/rfaa017). OpenAlex: W3124856464.
UCITS 규제 제약(적격자산, 분산투자, 공매도 제한)의 실증적 비용: matching
estimator로 UCITS vs 일반 헤지펀드를 비교해 연 1.06~4.05%의
위험조정수익률 손실을 추정. 원래 관심사였던 "regulatory cap-weight
constraint" 프레이밍과 직접 관련 있으나, enhanced index fund가 아니라
헤지펀드를 다룸.

**Chen, Y., & Israelov, R. (2023). Exclude with Impunity: Personalized Indexing and Stock Restrictions.**
*Financial Analysts Journal*, 피인용 3. DOI: [10.1080/0015198x.2023.2258061](https://doi.org/10.1080/0015198x.2023.2258061). OpenAlex: W4387781519.
Cap-weight가 아닌 종목 제외(stock-exclusion) 제약에 대한 시뮬레이션
백테스트; 소규모~중간 규모 제외는 passive/active 성과에 영향이 작다는 결과.
다른 종류의 제약이라 대조 사례로 유용.

### 제외 (키워드만 겹치는 false positive — 제목은 비슷하나 주제 다름)

- Pedersen, L. H. (2018). Sharpening the Arithmetic of Active Management.
  *FAJ*, 피인용 65. OpenAlex: W2784101727. Sharpe의 "비용 전 active =
  passive" 명제에 대한 논문으로, 포트폴리오 제약과는 무관 — 저자가 같을
  것으로 기대했으나 무관한 논문.
- Kao, D.-L. (2002). Battle for Alphas: Hedge Funds versus Long-Only
  Portfolios. *FAJ*, 피인용 86. OpenAlex: W1937416399. Alpha 분포를
  비교하는 실증논문으로, constraint 최적화 논문이 아님.

### 설정된 저널 목록에서 찾지 못함

"Enhanced indexation: can volatility timing improve portfolio
performance?" (2025) — Clarke et al.(2008)을 인용하는 논문으로 발견됐으나
`config/key-paper.yaml`의 tier 1~4 저널에서는 찾을 수 없었음; 아직
config에 없는 저널(예: Journal of Asset Management, Quantitative
Finance)에 실렸을 가능성이 높음.

## 그 외 발견했으나 아직 정식 후보로 올리지 않은 논문들

- Cremers & Petajisto (2009), "How Active Is Your Fund Manager?" — RFS,
  피인용 1577. Active Share 개념의 원조 논문.
- Cremers, Ferreira, Matos & Starks (2016), "Indexing and active fund
  management: International evidence" — JFE, 피인용 356.
- "Sustainability or performance? Ratings and fund managers' incentives"
  (2024, JFE, 피인용 74) — ESG rating과 fund 성과의 trade-off,
  natural-experiment 설계.
- ML 기반 fund skill 판별 짝 논문 (2023, JFE): "Machine-learning the
  skill of mutual fund managers" (피인용 106), "Machine learning and
  fund characteristics help to select mutual funds with positive alpha"
  (피인용 99).
- "Model Comparison with Transaction Costs" (2023, JF, 피인용 87) —
  거래비용을 반영하면 어떤 factor model이 우월한지 결론이 뒤집힘.
