# Key Paper 후보 정리

`paper-search` skill(OpenAlex, `config/key-paper.yaml`의 tier 1~4 저널)로
찾은 thesis key paper 후보들을 기록한다. 학교 best practice: prestigious
journal의 key paper를 골라 한국 데이터로 replicate/extend.

## 상태: 유력 후보 (아직 최종 확정 아님)

**일반 참고**: 각 후보에 대해 OpenAlex 기반 유사논문·인용 추적을 넓게
수행함. 인접 문헌은 항상 어느 정도 존재하며, 이 학교는 "prestigious
journal key paper를 한국 데이터로 replicate/extend"하는 게 목표이지
새 방법론을 제안하는 게 아니므로, 인접 문헌의 존재 자체를 배제 사유로
보지 않는다. 실제 판단 기준은 (1) 한국에서 그 논문의 데이터를 구할 수
있는가, (2) 그 논문이 기존 방법론을 적용하는 설계인가(새 방법론 제안이면
master's thesis에 부적합)이다. 아래 각 후보의 "데이터·재현성" 메모 참고.

### 현재 판정 및 실행 우선순위 (2026-07-17)

후보 논문의 PDF/Markdown 원문 정독과 회사 DW Priority 1~10 중 1~6·9·10
조사를 완료했다.
아래 순서는 **주제 선호가 아니라 현재 확인된 데이터의 실행확실성 순서**다.
세부 변수·회사 DB 확인 항목은 `docs/candidate-paper-data-inventory.md`, 실제
DW 조사 로그는 `kwam-report-automation/temp/data-exploration/
findings-zi-fund-data.md`에 정리되어 있다.

1. **#5 Machine-learning the skill of mutual fund managers** — 펀드 특성으로
   미래 risk-adjusted performance를 예측하는 ML 기반 fund skill 연구.
   핵심 return·TNA·flow·survivorship 데이터가 실제 DB에서 확인되어 가장
   안전한 후보가 됐다.
2. **#8 Earning Alpha by Avoiding the Index Rebalancing Crowd** — KRX 지수
   구성종목·비중과 정기변경 효력일을 회사 DW에서 복원할 수 있어 데이터
   실행확실성이 크게 상승했다. 다만 Financial Analysts Journal(tier 4)이라
   학술지 prestige는 #3보다 약하고, 발표일·변경사유는 추가 확인이 필요하다.
3. **#3 Mutual fund performance: Using bespoke benchmarks to disentangle
   mandates, constraints and skill** — 펀드별 mandate와 constraint를 반영한
   맞춤형 benchmark로 진정한 skill을 분리하는 연구. 자산군별 약관 한도와
   장기 fund performance는 강하지만, 차입·공매도·증권대여·turnover 제약은
   구조화되지 않아 **조건부 3순위**다. 데이터보다 학술지 강도를 중시하면
   #8보다 먼저 검토할 수 있으나 constraint gate가 통과해야 한다.
- **보류 — #9 Mutual Fund Strategy: Swing for the Fences or Bat for Average** —
   holdings에서 운용전략을 식별하고 flow·수수료·위험·성과를 연결하는 연구.
   최신성과 차별성은 높지만, ZI holdings가 full portfolio가 아닌 자산구분별
   top-10으로 확인되어 **현재 데이터만으로는 보류/no-go**다. 별도의 장기
   full-holdings 원천을 확보할 때만 후보로 복귀시킨다.

Priority 1 조사에서 `DW_ZI_펀드일별분석`은 1996-01-03~2026-07-15의
영업일별 fund panel이고 `(기준일자, 협회펀드코드)` unique grain이며,
return·BM return·AUM 핵심 필드의 통계상 결측이 0임을 확인했다. 일별
`실현수익률`은 `기준가_t/기준가_(t-1)`의 decimal return factor이고,
`순자산_t/(순자산_(t-1)×실현수익률_t)-1`로 flow가 계산됨을 sample에서
실측했다. 2009년 해지펀드의 전체 이력도 보존되어 survivorship-bias-free
표본 구성이 가능하다. 반면 `DW_ZI_펀드자산내역`은 전체 246회의 월별
snapshot이지만 자산구분별 `순위`가 10에서 잘리고, 주식형 sample의 S1
top-10 비중 합도 40.43%에 불과했다. 2026-05-04 이후 적재도 멈춰 있다.
Priority 4~5에서는 보수율 단위와 총보수 합산식은 확인했지만 보수·약관·BM이
모두 현재 snapshot뿐이고, turnover 전용 자료가 없음을 확인했다. 약관의
자산군 한도는 정형화되어 있으나 차입·공매도·증권대여·회전율은 구조화된
필드가 없다. 따라서 #5의 parsimonious model은 go에 가장 가깝고, #3은
자유서술 제약 코딩과 표본 coverage가 통과해야 하는 조건부 후보다. full
holdings가 식별의 핵심인 #9는 ZI만으로 진행할 수 없다.

Priority 6·9·10에서는 `DW_ZI_운용사일별분석`이 1999년부터 존재하고,
KRX 지수 구성·산출 table에서 일별 구성종목·비중과 정기변경 효력일을 복원할
수 있음을 확인했다. 반면 개인 펀드매니저 table, 시장 전체 대차·공매도,
기관별 종목 holdings는 WRDSS에 없다. 이 결과로 #8 Arnott는 데이터 기준
2순위로 상승했고, 대차공급·borrow fee 메커니즘이 핵심인 #7 Ahn의 완전복제와
#4 Cao는 no-go로 확정된다.

### ~~1. Estimating Stock Market Betas via Machine Learning~~

**상태: 후보 제외 (already replicated)** — 고성규(MFE 24)가 한국
주식시장을 대상으로 이미 replicate했으므로 새로운 key paper 후보에서는
cross out한다. 비교·참고를 위해 아래 논문 정보와 기존 검토 내용은 남겨둔다.

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

**데이터·재현성**: 저위험. Predictor(과거 beta, turnover, size 등)가
표준적인 firm characteristic이라 한국 데이터로 구하기 쉽고, RF라는 기존
ML 방법을 적용하는 구조라 replication에 적합하다.

### ~~2. Cross-sectional expected returns: new Fama–MacBeth regressions in the era of machine learning~~

**상태: 후보 제외 (already replicated)** — 김보배(MFE 25)가 2026년
「새로운 Fama-MacBeth 회귀분석을 이용한 한국 주식 시장의 횡단면 수익률
예측」(*Cross-Sectional Return Prediction in the Korean Stock Market: A New
Fama-MacBeth Approach*)으로 한국 주식시장에 직접 적용했다. Key paper의
2024년 공개 이후 수행된 동일 방법론·동일 시장 replication이므로 후보에서
제외한다. 아래 논문 정보와 검토 내용은 비교·참고를 위해 남겨둔다.

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

**데이터·재현성**: 중위험. 원 논문은 200개 이상의 firm characteristics를
쓰는데, 한국 연구는 보통 20~90개 수준이라 characteristic 확보·구축 공수가
크다. 방법론(regularization-selection-combination)은 기존 절차를
적용하는 것이라 replication에는 적합함.

### 3. Mutual fund performance: Using bespoke benchmarks to disentangle mandates, constraints and skill

**상태: 원문 정독·Priority 4~5 확인 완료 — 조건부 3순위.**

- **저자**: Alessandro Beber, Michael W. Brandt, Jason Cen, Kenneth A. Kavajecz
- **저널**: Journal of Empirical Finance (tier 3), 2021
- **피인용**: 12
- **DOI**: https://doi.org/10.1016/j.jempfin.2020.12.001
- **OpenAlex ID**: W2970643464

**Abstract 요약**: 모든 뮤추얼펀드는 서로 다른 mandate(운용지침)와
constraint(제약)를 갖는데도, 기존 성과평가는 이를 무시하고 범용 벤치마크로
순위를 매긴다는 문제의식에서 출발. 각 펀드의 mandate·constraint를 반영한
"맞춤형(bespoke) 다요인 벤치마크"를 구성하는 방법론을 제시. 이 방식으로
재평가하면 평균 펀드의 성과기록이 크게 개선되고, 펀드 간 순위도 원래 순위와
유의미하게 달라짐 — mandate·constraint를 통제하지 않으면 실력(skill)을
잘못 측정하게 된다는 걸 정량적으로 입증.

**왜 후보인가**: Mutual fund regulatory/mandate constraint 하에서 "무엇이
최적 운용이고 무엇이 실력인가"를 방법론적으로 분리해내는 논문 — 원래 관심사였던
regulatory constraint 프레이밍(아래 "Enhanced index fund / transfer
coefficient 문헌" 참고)과 직접 연결되면서도, tier 3 학술지라 "prestigious
journal key paper를 한국 데이터로 replicate" 기준에는 부합. Bespoke
benchmark 구성 방법론을 한국 펀드 데이터에 적용하는 replication 설계가
가능해 보임.

**데이터·재현성**: **중고위험의 조건부 후보로 하향**. `DW_ZI_펀드약관한도`의
국내·해외 주식, 채권, 유동성, 수익증권 한도는 숫자로 잘 채워져 있고,
row 부재와 명시적 0%도 구분된다. `DW_ZI_펀드스타일분석`은 월별 9-box가
100%로 합산되어 size/value-growth mandate를 보완한다. 장기 fund return과
해지펀드 이력도 있어 성과측정 기반은 강하다.

그러나 원 논문의 핵심 constraint set 전체가 확보된 것은 아니다. 차입,
공매도, 증권대여, 회전율, 종목수 상한은 전용 코드·컬럼이 없고, `FB53`
레버리지 코드도 sample에서 실제 값 형태를 확인하지 못했다. turnover 전용
테이블과 매수·매도금액도 ZI 30개 안에 없다. 이 변수들을 `FF02` 자유서술이나
외부 약관 원문에서 일관되게 코딩할 수 있는지가 새로운 핵심 gate다.

약관·보수·공식 BM은 날짜 컬럼이 없는 현재 snapshot뿐이다. 원 논문도 한
시점의 prospectus를 쓰므로 단면 replication 자체에는 맞지만, 현재 살아 있는
펀드 중심으로 제약 표본이 형성되면 look-ahead와 survivorship selection이
생길 수 있다. `DW_ZI_펀드자산내역`의 top-10 한계는 core benchmark를 직접
막지는 않지만 portfolio 검증에는 쓸 수 없다. 따라서 Beber는 즉시 go가 아니라,
한 시점에서 최소 50개 펀드에 대해 핵심 제약 3개 이상을 안정적으로 코딩할 수
있을 때만 go로 전환한다.

**원문 검토 상태**: PDF/Markdown 정독 완료. 원 논문은 1974~2013년 월별
주식자료와 2009년 prospectus/SAI에서 코딩한 71개 펀드의 투자대상·현금·차입·
공매도·회전율·거래비용 제약을 결합한다. 한국 적용에서는 FnGuide의 size,
book-to-market, momentum, industry와 ZI 제약을 결합하면 된다.

### 4. Institutional Investment Constraints and Stock Prices

**상태: WRDSS 기관 holdings 부재 확인 — no-go.**

- **저자**: Jie Cao, Bing Han, Qinghai Wang
- **저널**: Journal of Financial and Quantitative Analysis (tier 2), 2017
- **피인용**: 50
- **DOI**: https://doi.org/10.1017/s0022109017000102
- **OpenAlex ID**: W3121379631

**Abstract 요약**: 위임운용(delegated portfolio management)에서의 투자제약이
종목 수요를 왜곡시킨다는 가설을 검증. 이미 overweight한 종목에 좋은 뉴스가
나와도 기관은 더 사지 않고, 이미 underweight한 종목에 나쁜 뉴스가 나와도
팔기를 꺼림(제약 때문에 추가 매수/매도가 어려움). 그 결과 "좋은 뉴스인데
overweight라 더 못 산 종목"이 "나쁜 뉴스인데 underweight라 더 못 판 종목"보다
이후 유의하게 초과성과를 내고, 이것이 모멘텀·PEAD 같은 이상현상 일부를
설명한다고 주장.

**왜 후보인가**: Tier-2 저널이고 피인용 50으로 검증된 논문. 기관투자자의
포트폴리오 제약이 가격형성(모멘텀/PEAD)에 미치는 영향을 다뤄 자산가격결정
이상현상 문헌과 직접 연결됨 — 한국 시장의 기관투자자 보유비중 데이터로
동일한 overweight/underweight 뉴스반응 비대칭을 검증하는 replication이
연구질문으로 옮길 수는 있으나, 실제 실행가능성은 기관별 전체 holdings의
존재에 전적으로 달려 있다.

**데이터·재현성**: 기존 후보군 중 가장 고위험. 이 논문은 미국 13F(모든
$100M+ 기관의 분기별 전체 보유내역 의무공시)를 쓰는데, 한국에는 이런
등가 제도가 없다 — 5% 보유·변동 공시(5%룰)는 대량 지분에만 적용되고
전체 기관의 종목별 비중을 보여주지 않는다. 종목별 overweight/underweight
판정 자체를 구성하기 어려울 수 있어, 국민연금 등 개별 대형기관 공시나
펀드 holdings로 대용 가능한지부터 확인해야 진행 여부를 판단할 수 있다.
`DW_ZI_펀드자산내역`에는 펀드별 종목코드·비중·수량·평가액이 있지만,
자산구분별 top-10만 저장되고 주식형 sample의 비중 합도 40.43%에 그쳤다.
따라서 “국내 공모주식형 펀드”로 범위를 좁혀도 종목별
overweight/underweight를 구성할 수 없다. WRDSS 1,044개 object에서도
기관별 종목 보유수량 table을 찾지 못했고 기관코드는 이름 매핑용 참조 table만
존재했다. 별도 full institutional holdings 원천이 없는 한 **no-go**다.

### 5. Machine-learning the skill of mutual fund managers

**상태: 원문 정독·관련 Priority 1~6 검증 완료 — 현재 1순위.**

- **저자**: Ron Kaniel, Zihan Lin, Markus Pelger, Stijn Van Nieuwerburgh
- **저널**: Journal of Financial Economics (tier 1), 2023
- **피인용**: 107 (OpenAlex, 2026-07-17 확인)
- **DOI**: https://doi.org/10.1016/j.jfineco.2023.07.004
- **OpenAlex ID**: W4385753172

**Abstract 요약**: 머신러닝으로 펀드 특성(fund characteristics)만 갖고도
고성과/저성과 뮤추얼펀드를 수수료 차감 전후 모두 일관되게 구분해낼 수 있고,
이 초과성과가 3년 넘게 지속됨을 보임. Fund momentum과 fund flow가 가장
중요한 예측변수이고, 펀드가 보유한 종목들의 특성 자체는 예측력이 없음.
예측 롱숏 포트폴리오의 수익률은 고(高)센티먼트 시기 직후에 더 높으며,
신경망 추정을 통해 센티먼트와 fund flow·fund momentum 간의 새로운
상호작용 효과를 발견.

**왜 후보인가**: Tier-1 저널(JFE), 피인용 107로 이미 활발히 인용되는 논문.
기존 후보 #1(ML 기반 beta 추정), #2(ML 확장 Fama-MacBeth)와 같은 "ML을
자산가격결정/성과평가 방법론에 도입" 계열이라 방법론적 일관성이 있음.
펀드 특성 기반 예측 방법론을 한국 뮤추얼펀드 데이터에 적용하는 replication이
가능해 보이며, 한국은 미국 대비 fund characteristics 기반 스킬 예측 연구가
상대적으로 적어 gap일 가능성.

**데이터·재현성**: **저위험으로 확인**. 제로인 DW 실데이터 조사로 핵심 입력이
실제로 장기간 사용 가능함을 확인했다.
`DW_ZI_펀드일별분석`에서 설정액·설정좌수·순자산·실현수익률·BM수익률을 얻어
fund return, AUM, flow, fund momentum을 구성할 수 있다.
`DW_ZI_펀드지표분석`에는 alpha·beta·R-square·Sharpe·IR과 순위가 있고,
`DW_ZI_운용사일별분석`·`DW_ZI_운용사지표분석`은 family momentum·flow·성과
변수에 대응한다. `DW_ZI_클래스펀드`, 설정일·해지일을 이용하면 share-class
통합, fund age와 생존편향을 처리할 수 있다. 원
논문에서 holdings-stock characteristics는 abnormal return 예측에 거의
기여하지 않으므로, holdings가 없어도 핵심 replication이 가능하다는 점도
장점이다.
사전 계산된 alpha·IR은 검산용으로 쓰고, 최종 논문에서는 raw fund/BM return으로
주요 성과지표를 직접 재계산하는 편이 재현성 측면에서 안전하다.

Priority 6에서 `DW_ZI_운용사일별분석`이 1999-08-23부터 존재함을 확인해
family TNA·flow·momentum의 장기 구축 가능성은 강화됐다. 개인 매니저 ID,
담당기간·경력·team-managed 정보는 WRDSS 전체에서 찾지 못했지만 parsimonious
model의 필수 입력은 아니다. retail/institutional은 `D100` 판매방식과 `E100`
대상고객 속성으로 대용 가능성이 있으나 아직 실측 검증하지 않았다.

Priority 1 실측 결과는 다음과 같다. `DW_ZI_펀드일별분석`은 1996-01-03부터
2026-07-15까지 최신 적재되고, 108M행 통계에서 핵심 수치필드 결측은 0이다.
해지된 펀드도 설정일부터 해지 다음날까지 이력이 남아 있다. `실현수익률`은
일별 decimal factor이고, `순자산`과 결합한 표준 flow 공식이 무유출입 구간에서
거의 정확히 0을 산출했다. 설정일 첫 행은 `순자산=0, 실현수익률=1` placeholder라
제외해야 한다. 보수율은 percent 단위이고 `FA10` 총보수가 5개 구성 보수의
합과 일치하지만, 날짜 컬럼이 없어 현재값만 존재한다. 따라서 현재 보수를
과거 전 기간에 가산해 gross return을 만드는 것은 허용하기 어렵다. turnover
자료도 ZI 30개 안에는 없다. 이 한계는 13개 특성·gross-return 확장에는
영향을 주지만, `flow`·fund momentum·sentiment 중심의 parsimonious model은
막지 않는다. 남은 핵심 확인은 실현수익률의 순보수·분배금 처리, share-class
합산 공식, 한국 Carhart factor와 Baker–Wurgler sentiment 대용변수다.

**원문 검토 상태**: PDF/Markdown 정독 완료. 정확한 predictor는 46개
holdings-based stock characteristics와 13개 fund/family characteristics다.
그러나 parsimonious model의 `flow`, `F_r12_2` fund momentum, sentiment 세
변수가 결과 대부분을 재현하므로, 우선 이 핵심모형을 한국 표본에서 replicate한
뒤 13개 fund/family characteristics까지 확장하는 설계가 가장 안전하다.
46개 holdings characteristics는 ZI top-10으로 만들 수 없으므로 별도 full
holdings 원천을 확보할 때만 추가한다.

### ~~6. ETF Arbitrage, Non-Fundamental Demand, and Return Predictability~~

**상태: 후보 제외 (already replicated)** — 안희찬이 2022년 「한국 ETF
시장에서 차익거래가 가지는 비본질적 수요에 대한 신호효과 및 수익률예측성에
관한 실증연구」(*An Empirical Study on Signaling Effect on Non-Fundamental
Demand of Arbitrage Trading and Return Predictability in the Korean ETF
Market*)로 한국시장에 직접 적용했다. Key paper의 2020년 공개 이후
ETF arbitrage, non-fundamental demand, return predictability라는 핵심
연구질문을 그대로 복제한 논문이므로 후보에서 제외한다. 아래 논문 정보와
검토 내용은 비교·참고를 위해 남겨둔다.

- **저자**: David Brown, Shaun Davies, Matthew C. Ringgenberg
- **저널**: Review of Finance (tier 2), 2020
- **피인용**: 132
- **DOI**: https://doi.org/10.1093/rof/rfaa027
- **OpenAlex ID**: W3121485504

**Abstract 요약**: 비기본가치적(non-fundamental) 수요충격은 자산가격에 큰
영향을 주지만 직접 관측하기 어려움. ETF 1차 시장에서 authorized
participant(AP)가 ETF와 기초자산 간 일물일가법칙 위반을 창출/환매
(creation/redemption)로 교정한다는 점을 이용해, 이 창출/환매 흐름(ETF
flow) 자체가 비기본가치 수요의 신호임을 이론+실증으로 보임. 고유입 ETF를
숏·저유입 ETF를 롱하는 포트폴리오가 월 1.1~2.0% 초과수익을 내고, 이 왜곡이
투자자에게 실질적 비용(저성과)까지 유발함.

**왜 후보인가**: Tier-2 저널, 피인용 132로 검증된 논문. ETF flow를
비기본가치 수요의 관측 가능한 대리변수로 쓰는 식별전략이 명확하고
재현가능함 — 한국 ETF 시장의 creation/redemption 데이터로 동일한
flow-기반 예측 포트폴리오를 구성하는 replication이 가능해 보임.

**데이터·재현성**: 저위험. KRX가 ETF 상장좌수(shares outstanding) 일별
변화를 공개하는데, 이게 학계에서 쓰는 creation/redemption 대용변수와
구조가 같다 — 접근성 좋음.

### 7. Identifying the Effect of Stock Indexing: Impetus or Impediment to Arbitrage and Price Discovery?

**상태: 지수 이벤트 기반 축소 replication만 가능 — exact replication no-go.**

- **저자**: Byung Hyun Ahn, Panos N. Patatoukas
- **저널**: Journal of Financial and Quantitative Analysis (tier 2), 2021
- **피인용**: 9
- **DOI**: https://doi.org/10.1017/s0022109021000235
- **OpenAlex ID**: W3155965432

**Abstract 요약**: "인덱스 투자 증가가 차익거래를 방해하고 가격발견을
저해한다"는 우려를 Russell 지수 재구성(reconstitution)을 자연실험으로
이용해 인과적으로 검증. 대형주·중형주에서는 인덱스 투자가 차익거래자의
뉴스 반영 능력에 뚜렷한 영향이 없지만, 초소형주(micro-cap)에서는 오히려
뉴스에 대한 가격조정 속도를 높임 — 메커니즘은 인덱싱이 차익거래 제약을
완화시켜 원래 거래하기 힘들었던 초소형주의 정보거래를 촉진한다는 것.

**왜 후보인가**: Tier-2 저널. Russell 재구성 같은 규칙 기반 지수 재조정을
자연실험으로 쓰는 식별전략이 깨끗하고, "인덱싱이 가격발견을 해친다"는
통념에 반대되는 결과라 흥미로움. 코스피/코스닥 지수 정기변경(예: KOSPI200
편입·편출)을 유사한 자연실험으로 활용하는 한국 replication이 가능해 보임.

**데이터·재현성**: **축소 설계는 중저위험, 완전복제는 불가**. 회사 DW의
`DW_KRX지수구성*`과 `DW_KRX지수산출*`에서 과거 구성종목·비중과 정기변경
효력일을 복원할 수 있어 편입·편출 전후 가격·거래량·동조성 분석은 가능하다.
그러나 원 논문의 메커니즘 식별에 필요한 시장 전체 lendable quantity,
on-loan quantity, lender concentration, stock-loan fee와 index ownership은
WRDSS에 없다. 발견된 `FA_대차자산`·`DW_FA_대차담보명세`는 자사 펀드의
채권 차입·담보 자료일 뿐 시장 대차자료가 아니다. 따라서 “지수편입이
차익거래 제약을 완화한다”는 핵심 경로까지 replicate할 수 없고, 가격발견
결과만 분석하는 축소 thesis로 재정의해야 한다.

### 8. Earning Alpha by Avoiding the Index Rebalancing Crowd

**상태: Priority 9 실측 완료 — 데이터 기준 현재 2순위.**

- **저자**: Robert D. Arnott, Christopher Brightman, Vitali Kalesnik, Lillian Wu
- **저널**: Financial Analysts Journal (tier 4), 2023
- **피인용**: 8
- **DOI**: https://doi.org/10.1080/0015198x.2023.2173506
- **OpenAlex ID**: W4362607100

**Abstract 요약**: 시가총액가중지수는 밸류에이션이 오른 종목을 편입하고
내린 종목을 편출하는 기계적 룰을 갖는데, 편입/편출 발표 시 가격충격 이후
리버설이 일어남을 보임 — S&P 500 편출종목이 편입종목보다 그 다음 해 평균
22% 초과성과. 인덱스펀드보다 먼저 거래하거나 리밸런싱을 3~12개월 지연하는
단순 룰만으로 연 23bp를 추가로 벌 수 있고, 기본가치 기준(fundamental
size) 또는 다년 평균 시총으로 cap-weight하면 이 효과가 두 배가 됨.

**왜 후보인가**: Practitioner journal(FAJ, tier 4)이지만 인덱스 편입효과의
리버설이라는 명확하고 재현가능한 실증 패턴을 다룸. 한국은 KOSPI200/MSCI
Korea 등 규칙기반 리밸런싱이 활발해 동일한 "리밸런싱 군중 회피" 전략의
초과수익을 검증하는 replication이 자연스러움.

**데이터·재현성**: **중저위험으로 확인**. 회사 DW에
`DW_KRX지수구성`·`CLS`·`NP`가 일별 종목단위 구성과 여러 비중을 보유하고,
`DW_KRX지수산출`·`NP`에는 `변경여부`, 변경 전후 종목 수,
`다음정기변경일`이 존재한다. KOSPI200 실측에서 `다음정기변경일`이 실제
2025-06-13 효력일에 다음 일정으로 전환돼 정기변경 시점을 deterministic하게
식별할 수 있음을 확인했다. 따라서 과거 구성·가중치 복원과 리밸런싱 전후
수익률 분석은 현실적이다.

남은 gate는 `DW_KRX지수구성`에서 실제 편입·편출 종목을 전후 diff로 검증하고,
announcement date와 변경사유를 별도 필드·공시에서 연결하는 것이다.
`변경여부`는 단독 신호로는 불규칙하므로 쓰지 않는다. 데이터 측면에서는
Beber보다 안전하지만, Financial Analysts Journal(tier 4)이라는 학술지
적합성은 별도로 지도교수와 확인해야 한다.

### 9. Mutual Fund Strategy: Swing for the Fences or Bat for Average

**상태: 원문 정독·holdings audit 완료 — ZI 기준 보류/no-go.**

- **저자**: John Chalmers, Arash Dayani
- **저널**: Journal of Financial and Quantitative Analysis (tier 2), 2026
- **온라인 공개일**: 2026-04-23
- **피인용**: 0 (OpenAlex, 2026-07-17 확인; 최신 논문)
- **DOI**: https://doi.org/10.1017/s0022109026102865
- **OpenAlex ID**: W4403186570

**Abstract 요약**: 뮤추얼펀드의 stock-picking을 두 가지 의도적이고 지속적인
운용전략으로 구분한다. "Swinging for the Fences"(SF)는 style-adjusted
수익률 분포의 양쪽 극단에 위치한 종목, 즉 큰 성공 또는 큰 실패가 될 수 있는
종목을 보유하는 전략이고, "Batting for Average"(BA)는 지속적으로 중간 정도의
성과를 내는 종목을 고르는 전략이다. 이 구분은 기존 active-management 지표나
알려진 asset-pricing factor로 설명되지 않는다. SF 펀드는 더 많은 flow를
유치하고 높은 보수를 받으며 위험한 portfolio를 보유하지만, 더 높은
risk-adjusted return을 제공하지는 못한다. 특히 주주보고서에서 특정 보유종목을
언급할 때 SF와 flow의 관계가 강하고, passive fund에서는 SF 패턴이 나타나지
않아 두 전략이 우연한 결과가 아니라 의도적 운용선택이라는 해석을 뒷받침한다.

**왜 후보인가**: 펀드매니저의 skill을 단순 alpha가 아니라 실제 holdings에서
드러나는 stock-selection 방식으로 측정한다는 점이 매력적이다. #5가 펀드
특성으로 미래 성과를 예측하는 접근이라면, 이 논문은 운용자가 어떤 형태의
종목 성과를 추구하는지를 holdings에서 직접 식별하고 그 전략이 investor flow,
fee, risk, performance에 미치는 영향을 연결한다. 2026년 최신 tier-2 논문이고,
과거 KAIST 논문 757편 및 현재 주제 현황에서 핵심 질문을 직접 replicate한
사례는 확인되지 않았다.

**한국 replication 아이디어**: 별도 full holdings를 확보한다는 전제에서,
월별 펀드 holdings와 국내주식 가격·스타일
자료를 결합해 각 보유종목의 style-adjusted return을 계산하고, 펀드별 SF/BA
지표의 지속성을 측정한다. 이후 SF/BA가 미래 fund flow, 보수, 변동성,
BM-adjusted return 및 alpha와 어떤 관계를 갖는지 검증한다. 한국 투자자는
"대박 종목"이 포함된 펀드에 더 강하게 반응하는지, 높은 SF가 skill이 아니라
risk-taking 또는 marketing incentive를 반영하는지도 자연스러운 확장 질문이다.

**데이터·재현성**: **ZI만으로는 재현 불가**. `DW_ZI_펀드자산내역`은 월별
snapshot이지만 full holdings가 아니라 자산구분별 top-10만 저장한다.
확인한 주식형 펀드에서 S1 종목은 정확히 10개였고 `펀드내비중` 합은
40.43%에 불과했다. 전체 246개 snapshot과 KRX 6자리 종목코드가 있어 기간과
FnGuide join은 유망하지만, 누락 종목이 절반 이상인 표본으로는 모든 보유종목을
동일가중하는 원 논문의 SF/BA를 구성할 수 없다. top-10은 큰 포지션을
선택한 표본이므로 이를 이용한 SF/BA는 원 지표의 근사가 아니라 체계적으로
편향된 다른 지표가 된다.

`DW_ZI_펀드일별분석`의 설정액·순자산·수익률·BM수익률,
`DW_ZI_펀드스타일분석`의 size/value-growth와 beta,
`DW_ZI_펀드약관보수`의 fee를 결합하면 outcome과 control은 만들 수 있다.
fund flow도 1996~2026년 일별 panel에서 실측 검증되었고 해지펀드가 보존된다.
그러나 핵심 explanatory variable인 SF/BA를 만들 수 없으므로 이 장점만으로
연구설계는 성립하지 않는다. holdings가 2026-05-04 이후 멈춘 운영상 공백도
있다. 원 논문의 shareholder-report 종목 언급 메커니즘을 제외하는 것은
가능하지만, full holdings를 제외하는 것은 불가능하다.

**원문 검토 상태**: PDF/Markdown 정독 완료. 분기 `t-2` 말 holdings에 대해
다음 분기 종목수익률을 size×book-to-market FF25 peer로 조정하고, 횡단면
상·하위 10%를 HR/SO, 0 초과를 hit로 정의한다. `t-1` 전략변수로 `t`의
flow·return·fee·volatility를 설명한다. ZI top-10은 이 정의를 충족하지
못하므로, 금융투자협회·운용사·별도 vendor에서 최소 8~10년의 full holdings를
확보하기 전에는 실제 go로 전환하지 않는다.

### 과거 학생 논문과의 직접 중복 점검

`docs/other-students-works/MFE 25학번 논문 주제 현황 파악 -
과거논문작성현황.csv`의 757편을 후보들과 대조했다. 여기서 제외 기준은
주제나 데이터가 넓게 유사한지가 아니라, **key paper가 공개된 이후에 해당
key paper의 핵심 연구질문과 방법론을 한국시장에 직접 replicate했는지**이다.
따라서 학생 논문 출판년이 key paper 공개연도보다 이르면 시간상 그 key
paper의 replication일 수 없으므로 제외 사유로 보지 않는다.

이 기준에서 직접 중복으로 확인된 후보는 다음 3편이다.

- **#1 Drobetz et al. (2024 online / 2025 issue)** → 고성규(2026),
  「머신러닝을 활용한 주식시장 베타 추정: 한국 주식시장 실증 분석」.
- **#2 Han et al. (2024)** → 김보배(2026), 「새로운 Fama-MacBeth
  회귀분석을 이용한 한국 주식 시장의 횡단면 수익률 예측」.
- **#6 Brown et al. (2020)** → 안희찬(2022), 「한국 ETF 시장에서
  차익거래가 가지는 비본질적 수요에 대한 신호효과 및 수익률예측성에 관한
  실증연구」.

따라서 **#1, #2, #6은 already replicated로 제외**한다. #3, #4, #5, #7,
#8, #9는 펀드 성과평가, 기관투자자, ETF, KOSPI200 편입·편출 등 상위 주제가
유사한 과거 논문은 있으나, 해당 key paper의 직접 replication으로 확인된
학생 논문은 없으므로 이 점을 이유로 제외하지 않는다.

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
당시에는 미국 외 단일 시장, 특히 한국에 ML 기반 beta를 적용하는 연구가
열려 있는 gap으로 판단했으나, 이후 고성규(MFE 24)의 한국시장 replication을
확인했으므로 이 판단은 더 이상 유효하지 않다. 이에 따라 후보 #1은 제외한다.
ML 기반 Fama-MacBeth의 한국 적용 가능성은 후보 #2에서 별도로 검토한다.

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

**Abstract 요약**: Efficiency를 “실제로 구현된 최적 포트폴리오의
information ratio / alpha 신호 자체의 intrinsic information ratio”로 정의하고,
long-only 제약을 풀 때 얻는 효율성 개선을 분석한다. Long-short의 상대적 이점은
투자대상 종목 수가 많고, 개별자산 변동성이 낮으며, 목표 active risk가 높을수록
커진다. Long-only 제약은 특히 소형주 쪽으로 포트폴리오를 편향시키고, short
position으로 재원을 마련해 강한 양(+)의 신호에 더 크게 투자하는 것을 막는다.
그 결과 전통적인 고위험 active long-only 전략의 효율성 손실이 저위험 enhanced
index 전략보다 더 크다.

**현재 검토 메모**: “같은 alpha 예측력이라도 제약 때문에 얼마만큼 실제
portfolio IR로 이전되는가”라는 원래 연구질문의 출발점이다. 다만 일반 이론과
수치적 최적화가 중심이고 국가별 자연실험이나 한국시장 replication 단위가
명확하지 않아, thesis key paper보다는 transfer coefficient와 enhanced index
설계의 motivation 문헌으로 적합하다.

**Clarke, R., de Silva, H., & Thorley, S. (2002). Portfolio Constraints and the Fundamental Law of Active Management.**
*Financial Analysts Journal*, 피인용 254. DOI: [10.2469/faj.v58.n5.2468](https://doi.org/10.2469/faj.v58.n5.2468). OpenAlex: W1863029622.

**Abstract 요약**: Short-sale와 turnover뿐 아니라 benchmark 대비
market-cap·value-growth 중립, sector exposure 같은 현실적 제약 때문에
manager의 return forecast가 포트폴리오에 그대로 반영되지 못한다는 문제를
다룬다. 이를 측정하는 transfer coefficient를 도입해 Grinold의 fundamental
law를 constrained portfolio로 일반화한다. Ex ante 관계는 주어진 예측력과
제약 아래 active management가 낼 수 있는 잠재적 부가가치를 보여주고, ex post
관계는 실현성과를 return-prediction의 성공과 constraint가 만든 noise로
분해한다. Monte Carlo simulation으로 관계식의 정확성을 검증하고 S&P 500
benchmark 주식 포트폴리오 예제로 적용한다.

**현재 검토 메모**: 원래 관심사인 “long-short alpha 신호를 long-only
over/underweight로 옮길 때의 손실”을 가장 직접적으로 수식화한다. 한국
적용에는 종목별 expected-return signal, covariance matrix, benchmark weight,
실제 운용제약을 함께 구축해야 한다. 새로운 방법론 제안에 가까워 학교의
replicate/extend형 thesis보다는 이론적 프레임과 성과분해 기준으로 쓰는 편이
안전하다.

### 방법론 보완 논문

**Clarke, R., de Silva, H., Sapra, S. G., & Thorley, S. (2008). Long–Short Extensions: How Much Is Enough?**
*Financial Analysts Journal*, 피인용 15. DOI: [10.2469/faj.v64.n1.4](https://doi.org/10.2469/faj.v64.n1.4). OpenAlex: W2124644747.

**Abstract 요약**: 130/30 같은 long-short extension의 규모를 관행적으로
고정하지 않고, benchmark 구성·security covariance matrix·portfolio
optimization의 기초 가정에서 도출하는 analytical model을 제시한다. 단순한
security-ranking process, covariance structure, benchmark concentration
지표와 unconstrained optimization을 이용해 extension 규모를 결정하는
parameter를 식별한다. Extension은 목표 active risk, 종목 간 correlation,
benchmark 집중도, 구성종목 수, return forecast 정확도가 높을수록 커지고,
shorting cost와 개별종목 위험이 높을수록 작아진다. 변동성·상관관계·benchmark
집중도가 시간에 따라 변하므로 동일한 active risk를 유지하려면 130/30 비율도
고정하기보다 동적으로 달라져야 한다는 함의를 제시한다.

**현재 검토 메모**: “한국시장에서 적정 extension이 정말 130/30인가”를 묻는
설계에는 직접적이지만, 성과패턴의 국가별 replication보다 analytical
calibration 성격이 강하다. KOSPI 200 구성·비중과 종목 covariance는 회사
데이터로 만들 수 있으나 shorting cost와 실제 공매도 가능집합이 필요하다.

**Clarke, R., de Silva, H., & Thorley, S. (2005). Performance Attribution and the Fundamental Law.**
*Financial Analysts Journal*, 피인용 17. DOI: [10.2469/faj.v61.n5.2758](https://doi.org/10.2469/faj.v61.n5.2758). OpenAlex: W2072630071.

**Abstract 요약**: Fundamental law의 parameter를 실무에서 널리 쓰는
factor-based performance attribution과 연결한다. 시장에서 어떤 factor가
보상받았는지를 선형회귀의 factor payoff로 추정하고, fundamental law의
구성요소로 회귀기반 attribution 결과를 근사·해석하는 절차를 제시한다.
1995년 4월~2004년 3월 S&P 500을 benchmark로 하는 두 포트폴리오의 holdings,
return, factor exposure에 적용해 이론적 ex ante skill/implementation
프레임을 ex post 실현성과 분석으로 옮긴다.

**현재 검토 메모**: 2002년 논문의 transfer coefficient를 실제 성과평가 표로
연결하는 방법론적 다리다. 별도 key paper라기보다 constrained portfolio
replication에서 “signal이 나빴는지, 제약 때문에 구현이 나빴는지”를 사후
분리하는 보조방법으로 유용하다.

**Tol, R., & Wanningen, C. (2011). 130/30: By How Much Will the Information Ratio Improve?**
*The Journal of Portfolio Management*, 피인용 6. DOI: [10.3905/jpm.2011.37.3.062](https://doi.org/10.3905/jpm.2011.37.3.062). OpenAlex: W2098738581.

**Abstract 요약**: 미국 대형주 benchmark를 따르는 130/30 상품과 대응
long-only 상품에서 얻은 transfer coefficient 추정치 42개를 비교해, extension이
information ratio를 실제로 얼마나 높이는지 측정한다. 평균 transfer
coefficient 개선은 long-only tracking error에 따라 약 40~50%이며,
tracking error 0~2%에서는 42%, 2~3%에서는 48%, 3% 초과에서는 29%로
나타난다. 따라서 개선폭의 sweet spot은 2~3% 구간이다. 상품쌍의 40% 이상에서는
이론이 예측한 IR 개선폭이 실제보다 과대평가되어, 제약 완화의 이득을 그대로
성과로 간주하면 안 된다는 증거도 제시한다.

**현재 검토 메모**: 핵심 이론을 실제 상품 자료로 검증한다는 점에서 위
논문들보다 replication 구조가 분명하다. 다만 한국에 비교 가능한 long-only와
130/30 상품의 장기 표본이 충분한지가 첫 gate이며, 표본이 작으면 논문과 동일한
상품쌍 분석보다 시뮬레이션 연구로 바뀔 가능성이 크다.

### Citation 추적으로 찾은 2020~2026년 확장 논문

**Lo, A. W., & Zhang, R. (2024). Performance Attribution for Portfolio Constraints.**
*Management Science*, 피인용 2. DOI: [10.1287/mnsc.2024.05365](https://doi.org/10.1287/mnsc.2024.05365). OpenAlex: W4405724285.

**Abstract 요약**: Constrained portfolio의 holdings, expected return,
variance, expected utility, realized return을 각각 (1) unconstrained
mean-variance 최적해, (2) 개별 static constraint의 영향, (3) constraint
자체에 담긴 정보의 영향으로 분해하는 새로운 attribution framework를 제시한다.
핵심 확장은 제약을 단순한 성과비용으로만 보지 않고, 제약이 미래수익률과
상관된 정보를 담으면 오히려 성과를 개선할 수 있다고 보는 것이다. Bayesian
portfolio analysis로 estimation risk를 반영해 미래성과를 개선하거나 가장
적게 훼손하는 제약을 선택하며, simulation과 ESG constraint 사례에서는
일부 제약 포트폴리오가 그 정보를 무시한 passive benchmark보다 나을 수 있음을
보인다.

**현재 검토 메모**: Clarke et al.(2002)의 “constraint가 만든 implementation
loss”를 “constraint가 보유한 정보”까지 포함하도록 확장한 가장 직접적인 현대적
후속작이다. Enhanced index 방향을 되살린다면 이론적 key paper로 가장
유력하지만, 한국 데이터로 단순 replicate하기보다는 Bayesian portfolio
construction과 constraint attribution을 구현해야 하므로 master's thesis
범위와 방법론 제안 금지 기준을 먼저 확인해야 한다.

**Ang, A., Chen, L., Gates, M. D., & Henderson, P. (2021). Index + Factors + Alpha.**
*Financial Analysts Journal*, 피인용 5. DOI: [10.1080/0015198x.2021.1960782](https://doi.org/10.1080/0015198x.2021.1960782). OpenAlex: W3200035552.

**Abstract 요약**: 투자수익의 원천을 (1) index fund를 통한 market
asset-class exposure, (2) value·momentum·quality 같은 style factor exposure,
(3) index와 factor로 설명되지 않는 pure alpha로 분리하고, 세 원천 사이의
최적 배분 방법을 제시한다. 각 factor 및 alpha strategy의 information ratio에
prior를 부여하는 Bayesian 방식이며, 일반적으로 factor fund의 prior
불확실성은 alpha strategy보다 작게, alpha의 prior 평균은 factor보다 크게
설정할 수 있다는 경제적 판단을 모형에 명시적으로 넣는다.

**현재 검토 메모**: “index + systematic factor + manager alpha”를 한
portfolio 안에서 구분하므로 enhanced index의 실무적 자산배분 논리에는
유용하다. 그러나 abstract는 특정 시장에서의 강한 실증결과보다 allocation
방법론을 강조한다. 한국 replication을 하려면 factor/alpha IR prior 선택이
결과를 얼마나 바꾸는지 sensitivity analysis가 핵심이 된다.

**Joenväärä, J., & Kosowski, R. (2020). The Effect of Regulatory Constraints on Fund Performance: New Evidence from UCITS Hedge Funds.**
*European Finance Review*, 피인용 0. DOI: [10.1093/rof/rfaa017](https://doi.org/10.1093/rof/rfaa017). OpenAlex: W3124856464.

**Abstract 요약**: UCITS 규제를 받는 헤지펀드와 일반 헤지펀드의 성과·위험을
matching estimator로 비교해 규제의 간접비용을 추정한다. 적격자산,
분산투자, 공매도 관련 UCITS 제약으로 인한 위험조정수익률 손실은 연
1.06~4.05%로 추정된다. 이 차이는 환매조건이나 leverage 차이로 설명되지
않으며, 운용사 특성·매니저 특성과 관측되지 않은 confounder bias를 고려한
검증에서도 유지된다.

**현재 검토 메모**: “regulatory constraint가 실제 fund performance에
얼마의 비용을 만드는가”를 직접 추정해 원래 문제의식과 매우 가깝다. 다만
대상은 cap-weight enhanced index가 아니라 UCITS hedge fund이고, 한국에는
동일 전략이면서 규제 적용만 다른 충분한 treatment/control 표본이 있는지가
불분명하다. 적절한 제도 변화나 역외/국내 펀드 매칭표본을 찾을 때만 실증
후보가 된다.

**Chen, Y., & Israelov, R. (2023). Exclude with Impunity: Personalized Indexing and Stock Restrictions.**
*Financial Analysts Journal*, 피인용 3. DOI: [10.1080/0015198x.2023.2258061](https://doi.org/10.1080/0015198x.2023.2258061). OpenAlex: W4387781519.

**Abstract 요약**: Historical simulation backtest로 특정 종목을 투자집합에서
제외하는 personalized-indexing 제약이 passive 및 active portfolio 성과에
미치는 영향을 분석한다. 적은 수에서 중간 수준의 종목 제외는 passive
portfolio에 거의 영향을 주지 않는다. Active portfolio의 영향은 선택한
factor와 portfolio-construction 방식에 따라 달라지지만, 성과훼손 규모는
제외 종목 비율만 보고 예상하는 것보다 훨씬 작다. 특정 산업에 집중된 제외에서도
유사한 패턴이 나타나며, 상당히 많은 종목을 제외하기 전까지 투자성과가 크게
나빠지지 않는다는 결론이다.

**현재 검토 메모**: 제약이 항상 큰 efficiency cost를 만든다는 이론에 대한
유용한 대조사례다. ESG·고객선호에 따른 exclusion을 KOSPI universe에
적용하는 것은 가능하지만, 규제 충격을 식별하는 실증논문이 아니라
simulation/portfolio construction 연구라는 점에서 정식 후보 우선순위는
낮다.

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

아래 6편은 모두 abstract까지 읽고 연구질문·설계·핵심 결과와 현재 데이터 기준
후보 판단을 정리했다. 피인용 수는 OpenAlex에서 2026-07-18에 다시 확인했다.
Abstract가 OpenAlex에 없던 Cremers et al.(2016)은 출판사(ScienceDirect)
abstract를 확인했다.

### Active Share / indexing

**Cremers, M., & Petajisto, A. (2009). How Active Is Your Fund Manager? A New Measure That Predicts Performance.**
*Review of Financial Studies* (tier 1), 피인용 1,583.
DOI: [10.1093/rfs/hhp057](https://doi.org/10.1093/rfs/hhp057).
OpenAlex: W3123700708.

**Abstract 요약**: 펀드 보유종목이 benchmark index 보유종목과 다른 비율을
Active Share로 정의하고, 1980~2003년 미국 국내주식형 뮤추얼펀드에서
계산한다. Active Share와 fund size·expense·turnover의 횡단면 관계 및 시간에
따른 변화를 분석한 결과, Active Share가 가장 높은 펀드는 비용 전후 모두
benchmark를 유의하게 초과하고 성과 지속성도 강하다. 반대로 index fund는
아니지만 Active Share가 가장 낮은 펀드, 즉 closet indexer는 benchmark보다
낮은 성과를 낸다.

**정식 후보로 올리지 않은 이유**: Active Share의 원조 논문이고 prestige와
연구질문의 명료성은 충분하다. 그러나 replication에는 펀드별 full holdings와
동일 시점 benchmark constituents/weights가 모두 필요하다.
`DW_ZI_펀드자산내역`의 자산구분별 top-10으로는 Active Share를 계산하면
체계적인 측정오차가 생기므로, 별도 full-holdings 원천이 생기기 전에는 #9와
같은 이유로 no-go다.

**Cremers, M., Ferreira, M. A., Matos, P., & Starks, L. T. (2016). Indexing and Active Fund Management: International Evidence.**
*Journal of Financial Economics* (tier 1), 피인용 357.
DOI: [10.1016/j.jfineco.2016.02.008](https://doi.org/10.1016/j.jfineco.2016.02.008).
OpenAlex: W3123039400.

**Abstract 요약**: 전 세계 뮤추얼펀드 산업에서 explicit indexing,
closet indexing, active management의 관계를 비교한다. 저비용 index fund와
ETF의 경쟁압력이 강한 국가에서는 active fund가 benchmark에서 더 적극적으로
벗어나고 수수료를 낮춘다. Pension law 도입이 만든 indexed-fund 비중의 외생적
변화를 quasi-natural experiment로 이용해 이 관계의 인과해석을 보강한다.
Explicit indexing이 많은 국가에서는 active management의 평균 alpha가 높고,
closet indexing이 많은 국가에서는 낮아, passive 상품의 성장이 active
industry의 경쟁과 상품차별화를 개선한다는 결론이다.

**정식 후보로 올리지 않은 이유**: 32개국의 2002~2010년 open-end equity
fund·ETF와 full holdings를 이용한 국가 간 설계라 한국 단일시장 replication은
원 논문의 핵심 식별을 그대로 재현하지 못한다. 한국에서 하려면 장기
full holdings뿐 아니라 passive-fund 보급 또는 연금제도 변화라는 외생적
충격이 필요하다. Active Share를 계산할 수 없는 현재 ZI 데이터 한계도 동일하다.

### ESG rating과 fund manager incentive

**Gantchev, N., Giannetti, M., & Li, R. (2024). Sustainability or Performance? Ratings and Fund Managers' Incentives.**
*Journal of Financial Economics* (tier 1), 피인용 77.
DOI: [10.1016/j.jfineco.2024.103831](https://doi.org/10.1016/j.jfineco.2024.103831).
OpenAlex: W3159039665.

**Abstract 요약**: Morningstar sustainability “globe” rating 도입으로
fund sustainability와 performance의 trade-off가 투자자와 매니저에게
두드러진 사건을 이용한다. Rating 도입 직후 펀드들은 자금유입을 끌어내기 위해
지속가능성이 높은 종목의 보유를 늘렸지만, 이 sustainability-driven trade는
저성과를 내 펀드 전체 성과를 훼손했다. 그 결과 새로운 균형에서는 globe
rating이 더 이상 investor flow를 움직이지 않고, 펀드도 rating을 높이기 위한
거래를 중단한다. 즉 rating incentive에 대한 운용자 반응이 내생적으로
성과비용과 투자자 학습을 낳는 동학을 보인다.

**정식 후보로 올리지 않은 이유**: 최신 tier-1 논문이고 rating 도입이라는
식별사건이 명확하지만, 한국 replication에는 시점별 ESG rating, fund flow,
fund full holdings와 개별종목 sustainability score가 모두 필요하다. 현재
ZI top-10 holdings만으로는 rating 개선 목적의 portfolio reallocation을
측정할 수 없고, 한국에서 Morningstar globe rating 도입과 대응되는 외생적
사건을 별도로 찾아야 한다.

### ML 기반 fund skill 판별의 두 접근

**Kaniel, R., Lin, Z., Pelger, M., & Van Nieuwerburgh, S. (2023). Machine-Learning the Skill of Mutual Fund Managers.**
*Journal of Financial Economics* (tier 1), 피인용 107.
DOI: [10.1016/j.jfineco.2023.07.004](https://doi.org/10.1016/j.jfineco.2023.07.004).
OpenAlex: W4385753172.

**Abstract 요약**: ML이 fund characteristics만으로 비용 전후의
고성과·저성과 펀드를 지속적으로 구분하며, 예측된 초과성과가 3년 이상
지속됨을 보인다. 가장 중요한 predictor는 fund momentum과 fund flow이고,
펀드가 보유한 종목의 characteristics는 미래 risk-adjusted fund performance를
예측하지 못한다. 예측 long-short portfolio 수익률은 high-sentiment 시기
이후 더 높고, neural network는 sentiment와 fund flow·fund momentum 사이의
새롭고 큰 interaction effect를 찾아낸다.

**현재 판단**: 이 논문은 이미 본문 후보 #5로 승격되어 현재 1순위다. Full
holdings가 없어도 핵심 parsimonious model을 재현할 수 있고, 회사 DW에서
return·AUM·flow·fund momentum의 장기 panel을 확인했다는 점이 아래 DeMiguel
et al.보다 데이터 측면에서 안전하다.

**DeMiguel, V., Gil-Bazo, J., Nogales, F. J., & Santos, A. A. P. (2023). Machine Learning and Fund Characteristics Help to Select Mutual Funds with Positive Alpha.**
*Journal of Financial Economics* (tier 1), 피인용 100.
DOI: [10.1016/j.jfineco.2023.103737](https://doi.org/10.1016/j.jfineco.2023.103737).
OpenAlex: W4387951571.

**Abstract 요약**: Fund characteristics를 입력한 ML로 실제 투자 가능한
long-only mutual-fund portfolio를 구성하고, 모든 비용 차감 후 표본외 연
2.4%의 유의한 alpha를 얻는다. ML은 fund characteristic와 미래성과의
비선형 상호작용을 드러내며, 예를 들어 과거성과는 더 active한 펀드에서 특히
강한 predictor다. 규모의 불경제가 skill을 완전히 상쇄하지 않는 manager를
식별할 수 있다는 결과는, 투자자가 outperforming fund를 알아보지 못하는
정보마찰이 존재한다는 해석과 일치한다.

**현재 판단**: #5와 같은 2023년 JFE “fund characteristics + ML” 계열이지만,
이 논문은 high-minus-low 성과분류보다 투자자가 살 수 있는 long-only fund
selection과 net alpha에 초점을 둔다. 한국 적용의 실무적 결과변수는 더
직관적이나, activeness와 비용을 정확히 만들려면 holdings·시점별 fee가
필요하다. 현재 fee가 snapshot이고 holdings가 top-10인 한 #5의
flow/momentum 중심 parsimonious replication보다 우선순위가 낮다.

### 거래비용을 반영한 factor-model 비교

**Detzel, A., Novy-Marx, R., & Velikov, M. (2023). Model Comparison with Transaction Costs.**
*The Journal of Finance* (tier 1), 피인용 89.
DOI: [10.1111/jofi.13225](https://doi.org/10.1111/jofi.13225).
OpenAlex: W4327933245.

**Abstract 요약**: 거래비용을 무시하면 고비용 factor를 쓰는 asset-pricing
model에 유리하도록 모형비교가 편향된다는 점을 보인다. 비용을 무시할 때는
Hou–Xue–Zhang q-factor model과 Barillas–Shanken six-factor model이 높은
maximum squared Sharpe ratio와 205개 anomaly에 대한 작은 alpha를 보이지만,
실제 달성 가능한 mean-variance efficient frontier를 거의 포괄하지 못한다.
거래비용을 반영하면 Fama–French five-factor model의 squared Sharpe ratio가
두 대안보다 유의하게 높고, cash profitability를 사용한 변형은 그보다 더
좋다. 즉 statistical spanning과 investable efficiency의 모형 순위가 다를
수 있다.

**정식 후보로 올리지 않은 이유**: Tier-1이고 한국 factor model 비교로
옮기기 쉽지만, 205개 anomaly portfolio와 factor별 turnover·market-impact를
일관되게 구축해야 해 데이터·구현 범위가 크다. 현재 fund-skill 후보의 alpha가
거래비용 후에도 남는지 검증하는 보완문헌으로는 매우 중요하지만, 펀드 매매
내역과 turnover가 없는 ZI 데이터에서는 원 논문 수준의 비용 추정이 어렵다.
