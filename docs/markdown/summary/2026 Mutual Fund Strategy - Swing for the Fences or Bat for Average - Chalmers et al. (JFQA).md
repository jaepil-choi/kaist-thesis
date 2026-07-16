# Mutual Fund Strategy: Swing for the Fences or Bat for Average

이 논문은 적극운용 주식형 mutual fund의 종목선택을 “Swinging for the Fences”(SF)와 “Batting for Average”(BA)라는 두 전략으로 구분한다. SF는 style-adjusted 수익률 양쪽 꼬리의 home run과 strikeout을 많이 보유하고, BA는 극단성과 없이 benchmark를 자주 소폭 이기는 종목을 추구한다. SF는 지속적이고 의도적인 전략이며 더 많은 flow와 높은 fee를 가져오지만, 변동성만 높이고 risk-adjusted return은 개선하지 못한다.

## Abstract

SF와 BA는 기존 active-management 지표나 알려진 asset-pricing factor로 설명되지 않고 시간적으로 지속된다. SF 펀드는 shareholder report에서 특정 home run·strikeout 종목을 더 자주 언급하며, 특히 경제적 기여도가 큰 종목을 강조할 때 flow 반응이 커진다. 그러나 더 높은 위험과 보수에도 gross·net risk-adjusted return은 높지 않다.

passive fund에서는 전략지표가 펀드 특성·수익률·변동성·flow·fee와 연결되지 않는다. 이 위약검정은 active fund의 결과가 극단수익 종목의 우연한 보유나 자료구성의 산물이 아니라 의도적 stock-picking과 investor-attention 경쟁의 산물이라는 해석을 지지한다.

## I. Introduction

SF는 FF25 peer 대비 분기수익률 상위 10%의 home run과 하위 10%의 strikeout을 많이 보유하는 전략이다. BA는 극단적 결과를 피하면서 benchmark를 이기는 종목의 비율을 높이려는 전략이다. 두 전략은 모두 active할 수 있으므로 active share의 크기만으로는 구별되지 않는다.

SF·BA의 전략지표는 지속되지만 성공지표인 HR-SO, BA 비율, benchmark-adjusted return은 지속되지 않는다. 즉 펀드는 반복적으로 극단수익 후보를 선택할 수 있어도 그 선택이 home run으로 귀결될지, strikeout으로 귀결될지 또는 초과성과를 낼지는 예측하지 못한다.

SF는 월별 펀드 변동성을 높이고도 우월한 성과를 주지 않지만 투자자 관심을 끈다. HR+SO 1표준편차 증가는 다음 분기 flow를 18bp, 평균 펀드 기준 약 840만 달러 늘리고 연 보수는 3.7bp 높인다. 저자들은 salient한 성공사례를 만들고 공시에서 강조할 수 있다는 운용사 측 유인을 분석한다.

젊은 펀드·경력초기 manager·retail 중심 펀드가 SF를 더 많이 택한다. 규모가 커질수록 strikeout이 늘어 두 전략 모두 규모의 불경제를 겪고, 경험이 쌓일수록 home run보다 strikeout이 더 빠르게 줄어 종목선별 효율이 개선된다.

## II. Data, Variable Construction, and Summary Statistics

### A. Data and Sample Construction

1993~2020년 CRSP Mutual Funds와 Morningstar Direct 양쪽에서 수익률·규모가 일치하는 미국 적극운용 주식형 펀드를 사용한다. share class는 AUM 가중으로 펀드 수준에 합치고 Morningstar 3×3 style box의 diversified domestic equity fund만 남긴다. 관측기간 12분기 미만 또는 AUM 1,500만 달러 미만 펀드는 제외한다.

quarterly holdings는 Thomson Reuters S12에서 얻는다. 정확한 매매시점이 아니라 분기초에 보유한 종목이 다음 분기에 극단수익을 냈는지로 전략을 측정하므로, 사후에 오른 종목을 사서 home run으로 가장하는 window dressing을 피한다.

### B. Swing for the Fences and Bat for Average Strategy Measures

각 종목의 분기수익률을 size와 book-to-market로 정한 FF25 peer portfolio 수익률로 조정한다. peer 대비 상위 10%면 home run(HR), 하위 10%면 strikeout(SO), 0보다 크면 hit로 정의한다. 펀드의 HR·SO·BA는 분기초 보유종목 중 각 범주에 해당하는 종목의 동일가중 비율이다.

HR+SO는 SF의 강도, HR-SO는 SF의 성공도, 1(HR+SO=0)은 극단종목이 전혀 없는 BA 전략 선택, BA는 보유종목 중 peer benchmark를 이긴 비율이다. t-2 분기말 보유로 t-1의 HR·SO를 만들고 t의 수익률·flow·fee를 설명해 시간순서를 명확히 한다.

20/80·15/85·5/95 percentile, market-adjustment·FF6, value weight·return weight·상위 20개 보유종목만 사용하는 대안에서도 결과가 유지된다. 기본 동일가중치는 작은 보유종목까지 투자자의 눈에 띄는 종목명으로 작동할 수 있다는 salience 관점을 반영한다.

### C. Disclosure Data and Measures

2003~2020년 SEC N-CSR의 Management Discussion of Fund Performance를 fund별로 분리하고, 보유종목명·ticker와 대조해 manager가 home run을 기여종목으로 또는 strikeout을 손실기여종목으로 언급했는지 기계적으로 판별한다. MENTIONED_HR과 MENTIONED_SO는 연간 보고서에서 해당 종목을 하나 이상 명시했는지를 나타낸다.

### D. Summary Statistics

active 표본은 2,312개 펀드, 114,935 fund-quarter다. 평균 분기 gross return은 2.65%, net return은 2.34%, Morningstar benchmark-adjusted net return은 -0.19%, Carhart 4-factor alpha는 -0.07%다.

평균 HR은 5.16%, SO는 4.30%, HR+SO는 9.47%, HR-SO는 0.85%, BA는 49.15%다. fund-quarter의 약 8~9%는 HR과 SO가 전혀 없다. 연간 보고서에서 home run을 언급한 펀드는 46.5%, strikeout을 언급한 펀드는 39.3%다.

평균 펀드 AUM은 46억 달러지만 중앙값은 4.35억 달러이고, 평균 expense ratio는 1.23%, turnover는 82%, fund age는 15년, 보유종목 수는 127개다. 표본의 67%가 retail 중심이고 manager 평균경력은 약 10년이다.

### E. Home Runs Versus Other Forms of Extreme Returns

home run은 단일일 최고수익(MAX) 기반 lottery stock, 과거 250일 high-volatility·high-skewness 종목과 구별된다. home run이면서 lottery인 확률은 1.41%, high-volatility와 겹칠 확률은 1.91%, high-skewness와 겹칠 확률은 1.37%에 불과하다.

전체 home run 중 lottery stock은 14%, high-volatility는 19%, high-skewness는 14% 정도다. 따라서 SF는 단일일 복권형 수익이나 단순 변동성·왜도 노출이 아니라 분기 전체의 peer-adjusted 극단성과를 겨냥하는 별도 종목선택 특성이다.

## III. Swing for the Fences Versus Bat for Average

### A. Persistence

Morningstar category fixed effect를 포함해 4개 분기 lag를 동시에 회귀하면 HR, SO, HR+SO, 1(HR+SO=0)의 모든 lag가 양(+)이고 유의하다. 반면 HR-SO, BA, benchmark-adjusted return은 지속되지 않는다. 전략 선택은 반복되지만 성과는 반복되지 않는다는 구분이다.

전이행렬에서도 같은 결과가 나온다. low-HR 펀드의 32%가 다음 분기에도 low-HR에 남지만 high-HR로 이동하는 비율은 6%뿐이며, 이 대각선 집중은 4분기 뒤에도 HR·SO·HR+SO에서 유지된다.

### B. Marketing Swinging for the Fences

SF가 강할수록 N-CSR에서 특정 극단종목을 언급할 확률이 단조롭게 높다. 최상위 HR 5분위는 home run을 언급할 확률이 57%, 최상위 SO 5분위는 strikeout을 언급할 확률이 44%다. 모든 분위에서 성공종목을 실패종목보다 더 자주 언급한다.

포트폴리오 비중과 종목수익률을 결합한 contribution이 큰 home run·strikeout은 공시될 가능성이 두 배 이상 높다. manager는 단순히 극단종목이 많을 때뿐 아니라 펀드성과에 미친 영향이 클 때 종목명을 선택적으로 강조하며, home run 쪽 비대칭이 더 강하다.

### C. Which Funds Swing for the Fences?

turnover 1표준편차 증가는 HR+SO를 0.82%p 높이고, expense ratio가 높은 펀드도 SF가 강하다. institutional-client 중심 펀드는 HR+SO가 46bp 낮아 retail investor를 상대하는 펀드에서 SF가 더 흔하다.

규모가 커질수록 home run은 늘지 않지만 strikeout이 유의하게 늘고 HR-SO와 BA가 낮아진다. AUM이 한 log 단위 증가하면 SO는 14.7bp 증가하고 HR-SO는 9bp 하락하며, fund fixed effect에서는 성공도 하락폭이 38bp다. 더 많은 자금을 투자하기 위해 덜 선호하는 종목까지 선택하는 규모의 불경제와 일치한다.

5년 미만 펀드의 HR+SO·HR·SO는 각각 10.8%·6.1%·4.9%지만 20년 초과 펀드는 8.6%·4.5%·3.9%다. manager 경력이 늘수록 SO가 HR보다 빨리 줄어 학습효과가 나타난다. team-managed fund는 solo-managed fund보다 HR+SO가 51bp 낮고 극단종목이 전혀 없을 확률이 2.05%p 높다.

### D. Fund Strategies Versus Other Measures of Active Management

active share와 industry concentration을 통제해도 SF·BA의 구분과 다른 펀드특성 결과는 유지된다. 두 전략 모두 passive benchmark에서 벗어나는 적극적 종목선택이므로 active share가 높을 수 있고, active의 정도가 아니라 극단수익을 노리는 방식이 다르다.

momentum factor loading은 SF·BA와 유의한 관련이 없다. Open Asset Pricing Project의 광범위한 factor universe를 적용해도 home run 종목의 상위 factor가 집중되지 않고, 가장 흔한 10개 factor는 평균 6.7%의 home run에만 관련된다. fund 수준에서도 factor prevalence가 HR 분위별로 비슷해 알려진 factor exposure가 SF를 설명하지 못한다.

## IV. Fund Performance

### A. Returns

Morningstar benchmark-adjusted net return을 전략지표에 회귀하고 lagged performance, size, family size, turnover, fee, client type, flow, age, experience, holdings 수, style premium, category·date fixed effect를 통제한다. HR+SO, 1(HR+SO=0), HR, SO, HR-SO, BA 어느 것도 다음 분기 수익률을 예측하지 못한다.

Carhart 4-factor alpha, fund fixed effect, value·return weighting과 상위 20개 보유종목 기반 전략지표에서도 같고, gross return에도 우위가 없다. 높은 fee가 SF의 gross skill을 투자자에게서 이전한 결과도 아니며, SF와 BA 모두 benchmark를 넘는 stock-picking 성과를 만들지 못한다.

### B. Volatility

HR+SO 최상위와 최하위 펀드 포트폴리오의 횡단면 분기수익률 표준편차 차이는 1.05%p이고, HR과 SO 개별정렬도 각각 0.77%p·0.80%p 차이가 난다. 4-factor alpha 변동성을 사용해도 유사하다.

fund-level 회귀에서 HR+SO가 1%p 높아지면 월 benchmark-adjusted volatility가 3.09bp 증가한다. 1표준편차 증가는 22.7bp 증가에 해당하며, HR·SO가 없는 BA 펀드는 변동성이 4.1bp 낮다. HR과 SO는 모두 위험을 높이지만 HR-SO와 BA 성공도는 변동성과 견고한 관계가 없다.

## V. Management Incentives

### A. Fund Flows

과거 1분기·1년·3년 성과와 펀드특성을 통제해도 HR+SO 1표준편차 증가는 다음 분기 flow를 18bp, 평균 펀드 기준 약 839만 달러 늘린다. HR과 SO가 전혀 없으면 flow가 4bp 낮다.

HR 1표준편차 증가는 flow를 0.88%p 늘리고 SO 1표준편차 증가는 0.80%p 줄인다. 평균 펀드는 HR이 SO보다 많아 두 효과를 합친 SF의 순 flow 효과가 약 +0.20%p다. HR-SO와 BA 1표준편차 증가도 각각 flow를 0.70%p·0.66%p 높여 investor가 극단적 성공과 일관된 소폭 성공 모두에 반응함을 보여준다.

공시 salience가 반응을 증폭한다. home run 비중 1%p 증가는 언급하지 않은 펀드의 flow를 7.1bp 늘리지만 N-CSR에서 종목을 언급하면 15.3bp 늘린다. strikeout도 언급될 때 유출효과가 두 배 이상이다. contribution이 큰 HR은 1표준편차당 flow 효과가 0.43%p에서 1.22%p로 커지고, 중요한 SO의 유출효과도 거의 두 배다.

retail-focused fund에서는 같은 flow 민감도가 institutional-focused fund보다 65~86% 강하다. 투자자는 극단성과를 manager skill의 단순하고 눈에 띄는 신호로 해석하고, manager는 home run을 만들고 보고서에서 강조할 유인을 갖는다.

### B. Fund Fees

HR+SO 상위 펀드는 하위 펀드보다 expense ratio 분포가 높다. category·date fixed effect와 펀드특성을 통제하면 HR+SO 1표준편차 증가는 연 보수를 3.7bp 높이고, 극단종목이 없는 BA 펀드는 1.91bp 낮은 보수를 부과한다. HR과 SO 모두 fee와 양의 관계지만 HR-SO와 BA 성공도는 관련이 없다.

N-CSR에서 home run·strikeout을 강조하면 SF와 높은 fee의 관계가 17~38% 더 강하다. 통계적 유의성은 flow 결과보다 약하지만, 운용사가 salient한 종목 사례를 높은 보수의 정당화에 활용한다는 경제적 해석과 일치한다. 다만 관찰자료의 연관관계이므로 전략이 fee를 인과적으로 올린다고 단정하기보다 manager incentive의 일관된 증거로 해석해야 한다.

## VI. Evidence from Passive Funds

동일한 기준으로 구성한 passive 표본은 218개 펀드, 7,826 fund-quarter다. active fund와 달리 size, institutional focus, fee, turnover, fund age, manager experience가 HR+SO 또는 BA 전략지표와 체계적으로 연결되지 않는다.

passive fund에서 HR+SO와 1(HR+SO=0)은 benchmark-adjusted return, volatility, flow, expense ratio 어느 것도 설명하지 못한다. 지수를 기계적으로 추종하면서 우연히 보유한 극단성과 종목은 투자자나 운용사의 행동과 연결되지 않으므로, active 표본의 관계가 의도적 전략이라는 주장을 강화한다.

## VII. Conclusion

SF와 BA는 active의 많고 적음이 아니라 종목선택 결과분포를 어떻게 만들려는지의 차이다. 젊고 retail 중심인 펀드는 눈에 띄는 home run을 만들 가능성이 높은 SF를 선택하고, 그 결과 위험·flow·fee는 높아지지만 gross·net risk-adjusted performance는 개선되지 않는다.

투자자는 home run을 skill 신호로 보상하고 strikeout을 벌하며, fund disclosure는 이 반응을 증폭한다. 논문의 중심 메시지는 active manager가 superior alpha 없이도 성과의 salience를 설계하고 마케팅해 자산과 보수를 늘릴 수 있다는 것이다.

## Supplementary Material

보충자료에는 변수정의, 전략지표의 대안 threshold·가중방식, transition matrix, age profile, factor exposure 검정, gross·net·Carhart 성과, 변동성, flow rank, retail interaction과 passive-fund 추가결과가 수록되어 있다.

## References

mutual fund stock selection, active share·industry concentration, lottery-like returns·idiosyncratic volatility, flow-performance convexity, fee competition, fund disclosure·attention, career concern과 규모의 불경제 문헌을 결합한다. 핵심 기여는 종목별 극단성과의 양쪽 꼬리와 공시 salience를 전략·성과·운용사 유인으로 연결한 것이다.
