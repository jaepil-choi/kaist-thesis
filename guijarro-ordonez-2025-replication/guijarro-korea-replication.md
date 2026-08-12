# 딥러닝 통계적 차익거래의 한국 주식시장 재현

## Guijarro-Ordonez, Pelger, and Zanotti (2025)의 한국시장 replication

**학위논문 초안 — 2026년 8월 12일**

> **연구 분류.** 본 연구는 원 논문의 미국 CRSP/Compustat 결과에 대한 exact
> replication이 아니다. 현금배당을 제외한 수정주가수익률, 축소된
> KOSPI·KOSDAQ 표본, 3개월 고정 공시시차를 사용한 **한국 price-return
> variant**다. 원 논문의 240개월 IPCA, 미국 표본, 현금배당 포함 total return,
> 상장폐지수익률 및 실현 공매도·거래비용 자료는 아직 확보되지 않았다.

> **산출물 동기화 주의.** 원 논문과 동일한 번호의 본문 Figure 1–19·Table
> 1–9, 부록 Figure A.1–A.7·Table A.I–A.X를 모두 본문에 배치했다. 다만 이
> PC에는 최신 GPU 실행의 Figure 9–12, Table A.III, Table A.V 파일이 복사되지
> 않았다. 해당 위치는 registry의 최종 상대경로를 그대로 사용했으며, 표에는
> tracked execution status로 확인되는 값만 기록했다. 이 여섯 산출물을 포함한
> 최신 `outputs/` 전체를 복사한 뒤 최종본으로 판정해야 한다. 또한 파일 존재와
> scientific replication completeness는 다르다. 특히 Table 1의 CNN+Transformer
> 전체 FF/PCA grid는 실행되지 않았고 IPCA는 data-blocked이므로, 번호가 붙은
> artifact가 있다는 사실만으로 원 논문 Table 1을 재현했다고 판정하지 않는다.

## 초록

Guijarro-Ordonez, Pelger, and Zanotti(2025)는 통계적 차익거래를 (i) 요인모형을
이용한 차익거래 포트폴리오 구성, (ii) 잔차수익률 경로에서의 시계열 신호 추출,
(iii) 제약된 포트폴리오 목적함수의 직접 최적화라는 세 단계로 통합한다. 본
연구는 이 설계를 한국 주식시장에 적용한다. 전월 말 시가총액 기준으로 선택한
KOSPI·KOSDAQ 보통주에 대해 Fama–French 및 rolling PCA 잔차를 구축하고,
OU+Threshold, Fourier+FFN, CNN+Transformer 정책을 동일한 1,000거래일 학습창과
125거래일 재학습 주기로 비교한다. 잔차 표본은 2020년 1월 2일부터 2026년 7월
20일까지 1,606거래일이며, 정책의 표본외 평가는 2024년 1월 19일부터 606거래일이다.

한국 PCA5 잔차에 대한 rolling CNN+Transformer는 연수익률 16.8%, 연변동성
4.0%, Sharpe ratio 4.148을 기록했다. 동일 표본에서 Fourier+FFN은 Sharpe
3.266, OU+Threshold는 1.471이었다. 5bp 거래비용과 일별 1bp 공매도 보유비용을
목적함수에 포함하면 평균 일별 turnover는 1.214에서 0.464로 감소하지만 Sharpe
ratio도 1.371로 하락한다. 이 결과는 요인 제거와 비선형 시계열 정책이 한국
가격자료에서도 유효할 가능성을 보여주지만, 높은 Sharpe ratio를 투자 가능한
성과로 해석해서는 안 된다. 현금배당, 상장폐지수익률, point-in-time universe,
종목별 shortability, borrow fee 및 market impact가 빠져 있기 때문이다. 따라서
본 연구의 결론은 **방법론적 재현 가능성과 한국 price-return 표본에서의 실증적
패턴**에 한정된다.

**핵심어:** 통계적 차익거래, 잔차수익률, PCA, IPCA, convolutional transformer,
한국 주식시장, 거래비용

## 1. 서론

전통적인 pairs trading은 두 자산 가격의 공적분 관계나 평균회귀를 가정한다.
그러나 대규모 주식 패널에서는 어느 두 종목을 pair로 선택해야 하는지, 공통
위험요인을 어떻게 제거해야 하는지, 여러 잔차 신호를 하나의 포트폴리오로 어떻게
결합해야 하는지가 별개의 문제로 남는다. 원 논문은 이 세 문제를 하나의 학습
문제로 결합한다. 먼저 관측 또는 잠재요인으로 설명되는 공통수익률을 제거하고,
그 잔차를 실제 거래 가능한 long-short 포트폴리오로 표현한다. 다음으로 최근
잔차 경로에서 CNN과 Transformer가 국소 및 장기 패턴을 추출한다. 마지막으로
개별 종목수익률 예측오차가 아니라 전체 포트폴리오의 Sharpe ratio 또는
mean-variance utility를 직접 최적화한다.

본 연구의 질문은 다음과 같다.

1. 한국 주식수익률에서 공통요인을 제거하면 원 논문과 유사하게 통계적
   차익거래 성과가 개선되는가?
2. CNN+Transformer가 OU와 Fourier 기반 정책보다 우월한가?
3. 높은 성과는 전통적 위험요인, 단순 반전, 소수 종목 집중으로 설명되는가?
4. 거래비용과 보유기간을 반영해도 결과가 유지되는가?

본 연구의 기여는 새로운 딥러닝 구조를 제안하는 데 있지 않다. 원 논문의
표본구성, 시점정렬, residual composition, 정책학습 및 45개 표·그림 계약을
한국 데이터에 가능한 범위에서 그대로 적용하고, 불가능한 부분을 proxy로
감추지 않고 data gate로 분리하는 데 있다.

## 2. 모형

### 2.1. 차익거래 포트폴리오

시점 $t$의 $N_t$개 주식 초과수익률을 $R_{t+1}\in\mathbb{R}^{N_t}$, $K$개
요인수익률을 $F_{t+1}$, 요인적재량을 $\beta_t$라 하면

$$
R_{t+1}=\beta_tF_{t+1}+\epsilon_{t+1}.
$$

요인수익률이 factor-mimicking portfolio $W_{F,t}$로 표현되면
$F_{t+1}=W_{F,t}^{\top}R_{t+1}$이고, 잔차는

$$
\epsilon_{t+1}=\Phi_tR_{t+1},\qquad
\Phi_t=I-\beta_tW_{F,t}^{\top}
$$

가 된다. 따라서 잔차는 통계적 오차항에 그치지 않고 원주식으로 복제 가능한
long-short portfolio의 수익률이다. 본 연구는 한국 FF1/FF3/FF5와 rolling
PCA의 $K=0,1,3,5,8,10,15$를 구축했다. FF loading은 직전 60거래일, PCA
요인은 직전 252거래일 상관행렬, PCA loading은 직전 60거래일로 추정했다.

![Figure 1. 차익거래 모형의 개념도](outputs/paper-spec/fig_01_conceptual_arbitrage_model.png)

**Figure 1. Conceptual Arbitrage Model.** 원주식 수익률에서 공통요인을 제거해
잔차 포트폴리오를 구성하고, 신호모형과 allocation function을 거쳐 다시 원주식
포지션으로 합성하는 과정을 나타낸다.

### 2.2. 차익거래 신호

각 잔차 $i$에 대해 직전 $L=30$일의 누적 잔차경로를 입력으로 사용한다. 당일
의사결정에 당일 수익률이 들어가지 않도록 모든 입력은 $t-1$까지로 정렬한다.
CNN은 짧은 구간의 상승·하락·굴곡 패턴을 추출하고 Transformer self-attention은
최근 30일 안에서 서로 떨어진 시점 간의 의존성을 결합한다.

![Figure 2. 국소 필터의 예](outputs/paper-spec/fig_02_examples_local_filters.png)

**Figure 2. Examples of Local Filters.** 작은 convolution filter가 잔차경로의
국소 변화에 반응하는 방식을 보여준다.

![Figure 3. 합성곱 네트워크 구조](outputs/paper-spec/fig_03_convolutional_architecture.png)

**Figure 3. Convolutional Network Architecture.** causal convolution과 residual
block을 이용하므로 미래 정보가 현재 신호로 누출되지 않는다.

![Figure 4. Transformer 구조](outputs/paper-spec/fig_04_transformer_architecture.png)

**Figure 4. Transformer Network Architecture.** CNN feature에 4-head attention과
feedforward block을 적용하고 마지막 시점의 representation을 allocation으로
변환한다.

### 2.3. 차익거래 정책

잔차 allocation을 $w_t^{\epsilon}$이라 하면 원주식 weight는

$$
w_t^R=\Phi_t^{\top}w_t^{\epsilon},\qquad
\widetilde w_t^R=\frac{w_t^R}{\lVert w_t^R\rVert_1}
$$

로 계산한다. $L^1$ norm을 1로 정규화해 일별 gross exposure를 통제한다.
정책은 다음의 표본 Sharpe ratio를 최대화하거나 mean-variance 목적함수를
최대화하도록 학습한다.

$$
\widehat{SR}=\frac{\overline r_p}{s(r_p)},\qquad
\widehat U=\overline r_p-\frac{\gamma}{2}s^2(r_p).
$$

거래마찰 사양에서는 turnover $\lVert w_t-w_{t-1}\rVert_1$에 5bp, short
position $\lVert\min(w_t,0)\rVert_1$에 일별 1bp를 선형 penalty로 부과한다.

### 2.4. 비교모형

- **OU+Threshold:** 잔차를 Ornstein–Uhlenbeck 과정으로 추정하고 정규화된
  deviation이 임계값을 넘을 때 반대 포지션을 취한다.
- **Fourier+FFN:** 사전 정의 Fourier basis로 잔차경로를 변환한 뒤 feedforward
  network가 allocation을 출력한다.
- **CNN+Transformer:** 필터와 attention을 데이터에서 공동 학습한다.
- **Direct FFN / OU-feature FFN:** 시계열 feature의 기여를 분리하기 위한
  ablation이다.

## 3. 실증분석

### 3.1. 데이터와 표본

원 논문은 전월 말 시가총액이 미국 전체 시가총액의 0.01%보다 큰 약 550개
주식을 사용한다. 한국 variant는 같은 0.01% 규칙을 KOSPI·KOSDAQ 보통주에
적용했다. 잔차 표본은 2020-01-02~2026-07-20의 1,606거래일, 일별 횡단면은
127~185종목, 각 PCA branch의 잔차행은 275,711개다. 무위험수익률은 ECOS
91일 CD 연율을 252일 복리 일수익률로 변환했다.

수익률은 권리락·분할을 반영한 decimal adjusted **price return**이며 현금배당은
포함하지 않는다. 기업특성은 3개월 고정 lag를 적용했지만 실제 공시일 vintage가
아니다. 전월 말 상장주식수, 상장폐지수익률, 종목코드 변경을 포함한 완전한 PIT
security master도 아직 최종 검증되지 않았다.

### 3.2. 추정과 학습 계약

- seed 0, Adam learning rate 0.001, 100 epochs
- 최근 1,000거래일 학습, 125거래일마다 재학습
- 기본 signal lookback 30일, holding period 1일
- OOS 2024-01-19~2026-07-20, 606거래일
- 성과는 $252$일 기준 연율화
- alpha regression은 공개 코드와 동일한 OLS non-robust covariance

### 3.3. 주요 결과

#### 3.3.1. Sharpe ratio 목적함수

**Table 1. OOS Annualized Performance Based on Sharpe Ratio Objective**

| Model | K | Fama–French SR | Fama–French μ | Fama–French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **CNN + Trans** | 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| **CNN + Trans** | 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| **CNN + Trans** | 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| **CNN + Trans** | 5 | —ᵁ | —ᵁ | —ᵁ | **4.148** | **16.8%** | **4.0%** | —ᴰ | —ᴰ | —ᴰ |
| **CNN + Trans** | 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| **CNN + Trans** | 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| **CNN + Trans** | 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| **Fourier + FFN** | 0 | -1.006 | -17.1% | 17.0% | -1.006 | -17.1% | 17.0% | -1.006 | -17.1% | 17.0% |
| **Fourier + FFN** | 1 | 1.452 | 11.8% | 8.1% | 2.618 | 13.4% | 5.1% | —ᴰ | —ᴰ | —ᴰ |
| **Fourier + FFN** | 3 | 1.759 | 8.4% | 4.8% | 2.960 | 12.9% | 4.3% | —ᴰ | —ᴰ | —ᴰ |
| **Fourier + FFN** | 5 | 1.454 | 6.4% | 4.4% | 3.266 | 13.4% | 4.1% | —ᴰ | —ᴰ | —ᴰ |
| **Fourier + FFN** | 8 | —ᴰ | —ᴰ | —ᴰ | 3.923 | 13.9% | 3.5% | —ᴰ | —ᴰ | —ᴰ |
| **Fourier + FFN** | 10 | —ᴺ | —ᴺ | —ᴺ | 3.531 | 11.6% | 3.3% | —ᴰ | —ᴰ | —ᴰ |
| **Fourier + FFN** | 15 | —ᴺ | —ᴺ | —ᴺ | 1.816 | 5.2% | 2.8% | —ᴰ | —ᴰ | —ᴰ |
| **OU + Thresh** | 0 | 0.352 | 6.0% | 17.0% | 0.352 | 6.0% | 17.0% | 0.352 | 6.0% | 17.0% |
| **OU + Thresh** | 1 | 0.276 | 2.8% | 10.0% | 1.435 | 11.7% | 8.1% | —ᴰ | —ᴰ | —ᴰ |
| **OU + Thresh** | 3 | 0.732 | 4.6% | 6.3% | 1.138 | 7.1% | 6.2% | —ᴰ | —ᴰ | —ᴰ |
| **OU + Thresh** | 5 | 0.472 | 2.4% | 5.0% | 1.471 | 9.1% | 6.2% | —ᴰ | —ᴰ | —ᴰ |
| **OU + Thresh** | 8 | —ᴰ | —ᴰ | —ᴰ | 1.811 | 8.9% | 4.9% | —ᴰ | —ᴰ | —ᴰ |
| **OU + Thresh** | 10 | —ᴺ | —ᴺ | —ᴺ | 1.708 | 7.5% | 4.4% | —ᴰ | —ᴰ | —ᴰ |
| **OU + Thresh** | 15 | —ᴺ | —ᴺ | —ᴺ | 1.338 | 4.6% | 3.4% | —ᴰ | —ᴰ | —ᴰ |

*주:* 원 논문과 동일하게 행은 정책과 factor 수 $K$, 열은 Fama–French·PCA·IPCA의
SR, 연평균수익률 $\mu$, 연변동성 $\sigma$로 구성했다. $K=0$은 factor family와
무관한 동일 주식수익률이므로 완료된 Fourier와 OU 값을 세 열에 반복했다.
`—ᵁ`는 필요한 residual 입력은 있으나 해당 100-epoch rolling 정책을 **실행하지
않음**, `—ᴬ`는 실행 완료 기록은 있으나 세부 artifact가 이 PC에 **미동기화**,
`—ᴰ`는 입력자료 부족으로 **data-blocked**, `—ᴺ`는 Fama–French 사양상
**비해당**을 뜻한다. FF8은 exact STREV·LTREV가 없어 차단됐고, IPCA는 240개월
이력이 없어 전부 차단됐다. CNN+Transformer의 완결된 Table 1 사양은 현재
PCA5 한 cell뿐이다. 이 표는 빈 cell을 한국 proxy나 다른 정책 결과로 채우지 않는다.

요인 제거 전 $K=0$보다 PCA 잔차에서 성과가 높다. 또한 같은 PCA5에서
CNN+Transformer의 Sharpe 4.148은 Fourier+FFN 3.266과 OU 1.471보다 높다.
PCA factor 수는 5~10 사이에서 가장 높은 성과를 보이며, 15개까지 늘리면
성과가 하락한다. 이는 무조건 요인을 많이 제거하는 것이 좋은 것이 아니라,
신호와 함께 제거되는 고유수익률 변동이 증가할 수 있음을 시사한다.

**Table 2. Significance of Arbitrage Alphas Based on Sharpe Ratio Objective**

각 panel의 열은 원문과 동일하게 세 residual family별
$\alpha,t_\alpha,R^2,\mu,t_\mu$ 순서다.

*CNN+Trans model*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | 16.8% | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

*Fourier+FFN model*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | 10.8% | 2.07 | 4.6% | 11.8% | 2.26 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | 7.8% | 2.60 | 1.6% | 8.4% | 2.73 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | 5.9% | 2.18 | 0.5% | 6.4% | 2.25 | 13.3% | 5.13 | 1.4% | 13.4% | 5.06 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

*OU+Thresh model*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 7.4% | 0.71 | 13.3% | 6.0% | 0.55 | 7.4% | 0.71 | 13.3% | 6.0% | 0.55 | 7.4% | 0.71 | 13.3% | 6.0% | 0.55 |
| 1 | 0.9% | 0.14 | 2.3% | 2.8% | 0.43 | 10.7% | 2.02 | 4.1% | 11.7% | 2.23 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | 3.7% | 0.91 | 1.3% | 4.6% | 1.13 | 7.6% | 1.82 | 1.7% | 7.1% | 1.76 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | 1.9% | 0.57 | 0.5% | 2.4% | 0.73 | 9.6% | 2.46 | 2.0% | 9.1% | 2.28 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

*주:* 원 논문은 FF8을 alpha benchmark로 사용한다. 위 수치가 있는 cell은
현재 가능한 한국 6-factor(FF5+MOM) analogue이며 exact FF8 검정은 아니다.
따라서 별표 유의수준을 옮기지 않았다. 상태기호는 Table 1과 같다.

![Figure 5. 차익거래 전략의 누적 OOS 수익률](outputs/paper-korean/fig_05_korean_cumulative_returns.png)

**Figure 5. Cumulative OOS Returns of Different Arbitrage Strategies.** 한국
잔차모형별 정책의 누적성과다. 누적곡선의 우상향만으로 거래가능성을 결론내릴 수
없으며, Figure 6–7과 Table 9의 비용 결과를 함께 봐야 한다.

#### 3.3.2. Mean-variance 목적함수

**Table 3. OOS Annualized Performance Based on Mean-Variance Objective**

*CNN+Trans strategy, mean-variance objective function*

| K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | 3.131 | 15.6% | 5.0% | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |

*Fourier+FFN strategy, mean-variance objective function*

| K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | -0.812 | -16.0% | 19.7% | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |

**Table 4. Significance of Arbitrage Alphas Based on Mean-Variance Objective**

*CNN+Trans model*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | 15.6% | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

*Fourier+FFN model*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | -18.4% | -1.43 | 0.7% | -16.0% | -1.26 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

CNN 정책은 mean-variance에서도 양의 성과를 냈지만 Fourier 정책은 실패했다.
이는 목적함수 자체보다 비선형 allocation function과 재학습의 상호작용이 중요할
수 있음을 뜻한다. 단, CNN alpha의 전체 regression artifact가 현재 PC에 없어
Table 4의 최종 비교는 보류한다.

#### 3.3.3. 시계열 신호와 시간 안정성

**Table 5. OOS Annualized Performance of CNN+Trans for 60 Days Lookback Window**

| K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | 3.448 | 14.0% | 4.0% | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |

**Table 6. Significance of Arbitrage Alphas for 60 Days Lookback Window**

*CNN+Trans model, Sharpe objective function, L = 60 days*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | 14.6% | 5.54 | —ᵁ | 14.0% | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

30일 lookback의 Sharpe 4.148이 60일의 3.448보다 높다. 더 긴 과거정보가 자동으로
성과를 높이지 않으며, 한국 표본에서는 최근 한 달 안의 패턴이 상대적으로 더
유용했다.

**Table 7. OOS Annualized Performance of CNN+Trans for Constant Model**

*Ttrain = 4 years*

| K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | 4.151 | 16.2% | 3.9% | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |

*Ttrain = 8 years*

| K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |

**Table 8. Significance of Arbitrage Alphas for Constant Model**

*CNN+Trans model, Ttrain = 4 years*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | 16.2% | 6.35 | 0.7% | 16.2% | 6.44 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

*CNN+Trans model, Ttrain = 8 years*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

고정모형과 rolling 모형의 Sharpe가 거의 같다. 다만 표본이 606일에 불과하므로
이를 구조적 안정성의 증거로 확대해석할 수 없다. 원 논문의 8년 학습 사양도 한국
표본 길이 때문에 exact하게 구현되지 않았다.

#### 3.3.4. 거래마찰

**Table 9. OOS Performance of CNN+Trans with Trading Frictions**

*IPCA factor model*

| K | Sharpe ratio SR | Sharpe ratio μ | Sharpe ratio σ | Mean-variance SR | Mean-variance μ | Mean-variance σ |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

*주:* 원문 Table 9는 **IPCA 잔차 전용**이다. 한국 friction-aware PCA5 결과는
Table 9에 넣지 않고, 원문과 동일하게 PCA 전용 Table A.X에 보고한다.

비용 penalty는 turnover를 약 62% 줄이지만 Sharpe ratio도 약 67% 낮춘다. 이
비용은 종목·시점별 실제 spread, borrow fee, market impact가 아니라 고정
sensitivity다. 따라서 비용 반영 후에도 양의 Sharpe가 남았다는 사실은 실제
투자 가능성의 충분조건이 아니다.

![Figure 6. 거래마찰 목적함수 전후 turnover](outputs/paper-korean/fig_06_korean_turnover.png)

**Figure 6. Turnover with and without Trading-Friction Objective.** 비용을
내생적으로 학습한 정책의 turnover가 낮아지는지를 비교한다.

![Figure 7. 거래마찰 목적함수 전후 short allocation](outputs/paper-korean/fig_07_korean_short_proportion.png)

**Figure 7. Short Allocation with and without Trading-Friction Objective.** 한국
공매도 가능 종목을 point-in-time으로 제한한 결과가 아니므로 short allocation은
가상 포트폴리오 비중이다.

![Figure 8. 포트폴리오 weight 분포](outputs/paper-korean/fig_08_korean_weight_distribution.png)

**Figure 8. Distribution of Portfolio Weights.** weight 분포를 통해 소수 종목
집중 여부를 점검한다.

### 3.4. 포트폴리오 집중과 단순 반전

![Figure 9. sparse 포트폴리오 성과](outputs/paper-korean/robustness/fig_09_sparse_performance.png)

**Figure 9. Performance of Sparse Portfolios.** 절대 weight가 큰 일부 종목만
남겼을 때 Sharpe, 수익률, 변동성이 어떻게 변하는지를 보여준다. 최신 audit에서
상위 1%만 남기면 변동성이 0.504로 상승하고 Sharpe가 음수가 되었으며, 전체
weight 변환의 Sharpe는 2.158이었다. **현재 PC에 PNG가 없어 최신 outputs 동기화가
필요하다.**

![Figure 10. sparse 포트폴리오 누적수익률](outputs/paper-korean/robustness/fig_10_sparse_cumulative_returns.png)

**Figure 10. Cumulative Returns of Sparse Portfolios.** Figure 9의 각 sparsity
수준에 대한 누적수익률이다. **현재 PC에 PNG가 없어 최신 outputs 동기화가
필요하다.**

![Figure 11. 단순 반전전략 성과](outputs/paper-korean/robustness/fig_11_naive_reversal.png)

**Figure 11. Simple Reversal Trading.** 여러 lag의 단순 반전전략은 시험한 모든
lag에서 음의 성과를 냈다. 따라서 CNN 성과를 단순한 1차원 평균회귀 규칙으로
설명하기 어렵다. **현재 PC에 PNG가 없어 최신 outputs 동기화가 필요하다.**

### 3.5. 차익거래의 지속성

![Figure 12. 보유기간별 성과](outputs/paper-korean/robustness/fig_12_holding_period_panel_a.png)

**Figure 12. Performance for Longer Holding Periods.** 5일 보유목적함수로 별도
학습한 CNN은 연수익률 0.052, 연변동성 0.017, Sharpe 3.110을 기록했다. 반면
1일 전략 weight를 기계적으로 5일 horizon으로 변환한 값은 연수익률 -0.006,
연변동성 0.025, Sharpe -0.235였다. 두 결과는 정의가 다르므로 혼용하면 안 된다.
**현재 PC에 PNG가 없어 최신 outputs 동기화가 필요하다.**

### 3.6. 차익거래와 위험프리미엄

![Figure 13(a). 주식수익률의 factor component](outputs/paper-korean/risk-premium/fig_13a_stock_factor_components.png)

![Figure 13(b). 통계적 차익거래 factor portfolio](outputs/paper-korean/risk-premium/fig_13b_statarb_factor_portfolio.png)

**Figure 13. Arbitrage versus Risk-Premium Component.** 원 논문은 IPCA5로
위험프리미엄 성분과 차익거래 성분을 분해한다. 한국 exact IPCA5는 240개월
이력이 없어 구축하지 못했으며, 위 그림은 사용 가능한 한국 factor/PCA 자료를
이용한 analogue다. K=1, 60개월 short-history IPCA는 7개 연도 fit에서
수렴했지만 원 정의를 대체하지 않는다.

### 3.7. 추정된 네트워크 구조

![Figure 14. allocation과 수익률 사례](outputs/paper-korean/interpretability/fig_14_allocation_return_examples.png)

**Figure 14. Examples of Allocation and Returns of CNN+Transformer Strategy.**
대표 잔차경로와 이에 대한 allocation 및 실현수익률을 함께 나타낸다.

![Figure 15. benchmark model의 국소 패턴](outputs/paper-korean/interpretability/fig_15_local_basic_patterns.png)

**Figure 15. Local Basic Patterns of Benchmark Model.** CNN filter가 추출한 국소
패턴을 시각화한다.

![Figure 16. sinusoidal input의 attention](outputs/paper-korean/interpretability/fig_16_sinusoidal_attention.png)

**Figure 16. Example Attention Weights for Sinusoidal Residual Inputs.** 주기와
위상이 다른 합성 입력에 대한 attention 반응을 보여준다.

![Figure 17. 대표 잔차의 CNN+Transformer 구조](outputs/paper-korean/interpretability/fig_17_representative_structure.png)

**Figure 17. CNN+Transformer Model Structure for a Representative Residual.**
한 시점에서 convolution feature, attention 및 최종 weight의 연결을 나타낸다.

![Figure 18. 시간에 따른 모델 구조](outputs/paper-korean/interpretability/fig_18_structure_over_time.png)

**Figure 18. CNN+Transformer Model Structure over Time.** 한 snapshot의 설명을
여러 시점으로 확장한다.

![Figure 19. allocation weight의 변수중요도](outputs/paper-korean/interpretability/fig_19_variable_importance.png)

**Figure 19. Variable Importance for Allocation Weight.** 입력 lag별 gradient
중요도를 보여준다. gradient importance는 causal effect가 아니라 현재 학습된
모형의 국소 민감도다.

## 4. 결론

한국 price-return 표본에서도 공통요인 제거, 비선형 시계열 신호, portfolio-level
목적함수의 결합은 높은 표본외 Sharpe ratio를 만들었다. 특히 PCA5
CNN+Transformer는 OU와 Fourier benchmark보다 높은 성과를 냈고, 한국
6-factor regression으로 설명되지 않는 alpha가 관측되었다. 단순 반전과 극단적
sparsification은 성과를 설명하지 못했으며, 5일 보유에서도 별도 학습한 정책은
양의 성과를 보였다.

그러나 현재 결과에는 세 가지 중대한 제한이 있다. 첫째, 현금배당과
상장폐지수익률을 제외한 price return이므로 원 논문의 total-return 경제성과
다르다. 둘째, IPCA의 240개월 characteristic history와 실제 공시일 vintage가
없어 원 논문의 가장 강한 결과인 IPCA5를 재현하지 못했다. 셋째, 한국의
shortability, borrow fee, 거래세와 market impact를 point-in-time으로 적용하지
않았다. 높은 gross Sharpe는 이 제약들을 통과하기 전까지 deployable alpha가
아니다.

따라서 다음 단계는 모형을 더 복잡하게 만드는 것이 아니라 데이터 계약을 닫는
것이다. 구체적으로 현금배당 포함 total return, delisting return, PIT security
master, 240개월 기업특성, 실제 공시일, 일별 shortability와 borrow fee를
확보하고 동일한 45개 output을 재생성해야 한다. 이 data gate를 통과한 결과만
exact Korean replication 또는 투자실행 가능성 검증으로 승격할 수 있다.

## 참고문헌

Guijarro-Ordonez, J., Pelger, M., & Zanotti, G. (2025). Deep Learning
Statistical Arbitrage. *Management Science*. https://doi.org/10.1287/mnsc.2022.03132

Kelly, B. T., Pruitt, S., & Su, Y. (2019). Characteristics Are Covariances: A
Unified Model of Risk and Return. *Journal of Financial Economics*, 134(3),
501–524.

Fama, E. F., & French, K. R. (1993). Common Risk Factors in the Returns on
Stocks and Bonds. *Journal of Financial Economics*, 33(1), 3–56.

Fama, E. F., & French, K. R. (2015). A Five-Factor Asset Pricing Model.
*Journal of Financial Economics*, 116(1), 1–22.

# 부록

## A. 데이터

### A.1. 기업특성

**Table A.I. Firm Characteristics by Category**

| No. | Characteristic | Definition | No. | Characteristic | Definition |
| --- | --- | --- | --- | --- | --- |
| **Past Returns** |  |  | **Value** |  |  |
| 1 | r2_1 | Short-term momentum | 26 | A2ME | Assets to market cap |
| 2 | r12_2 | Momentum | 27 | BEME | Book to Market Ratio |
| 3 | r12_7 | Intermediate momentum | 28 | C | Ratio of cash and short-term investments to total assets |
| 4 | r36_13 | Long-term momentum | 29 | CF | Free Cash Flow to Book Value |
| 5 | ST_Rev | Short-term reversal | 30 | CF2P | Cashflow to price |
| 6 | LT_Rev | Long-term reversal | 31 | D2P | Dividend Yield |
| **Investment** |  |  | 32 | E2P | Earnings to price |
| 7 | Investment | Investment | 33 | Q | Tobin's Q |
| 8 | NOA | Net operating assets | 34 | S2P | Sales to price |
| 9 | DPI2A | Change in property, plants, and equipment | 35 | Lev | Leverage |
| 10 | NI | Net Share Issues | **Trading Frictions** |  |  |
| **Profitability** |  |  | 36 | AT | Total Assets |
| 11 | PROF | Profitability | 37 | Beta | CAPM Beta |
| 12 | ATO | Net sales over lagged net operating assets | 38 | IdioVol | Idiosyncratic volatility |
| 13 | CTO | Capital turnover | 39 | LME | Size |
| 14 | FC2Y | Fixed costs to sales | 40 | LTurnover | Turnover |
| 15 | OP | Operating profitability | 41 | MktBeta | Market Beta |
| 16 | PM | Profit margin | 42 | Rel2High | Closeness to past year high |
| 17 | RNA | Return on net operating assets | 43 | Resid_Var | Residual Variance |
| 18 | ROA | Return on assets | 44 | Spread | Bid-ask spread |
| 19 | ROE | Return on equity | 45 | SUV | Standard unexplained volume |
| 20 | SGA2S | Selling, general and administrative expenses to sales | 46 | Variance | Variance |
| 21 | D2A | Capital intensity |  |  |  |
| **Intangibles** |  |  |  |  |  |
| 22 | AC | Accrual |  |  |  |
| 23 | OA | Operating accruals |  |  |  |
| 24 | OL | Operating leverage |  |  |  |
| 25 | PCM | Price to cost margin |  |  |  |

*주:* 46개 characteristic의 원 정의를 유지했지만 한국 회계자료는 실제 공시일
vintage가 아니라 3개월 lag를 사용했다. 139개월만 존재하므로 원 논문의 240개월
rolling IPCA는 실행할 수 없다.

## B. 대안 모형의 구현

![Figure A.1. Feedforward network 구조](outputs/paper-spec/fig_a01_feedforward_architecture.png)

**Figure A.1. Feedforward Network Architecture.** Fourier 또는 OU feature를
입력으로 받는 비교모형의 구조다.

## C. 추가 실증결과

### C.1. Hyperparameter 선택

**Table A.II. Hyperparameter Options for the Network**

| Notation | Hyperparameters | Candidates | Chosen |
|---|---|---|---|
| D | Number of filters in the convolutional network | 8, 16 | 8 |
| ATT | Number of attention heads | 2, 4 | 4 |
| HDN | Number of hidden units in the transformer's linear layer | 2D, 3D | 2D |
| DRP | Dropout rate in the transformer | 0.25, 0.5 | 0.25 |
| Dsize | Filter size in the convolutional network | 2 | 2 |
| LKB | Number of days in the residual lookback window | 30 | 30 |
| WDW | Number of days in the rolling training window | 1,000 | 1,000 |
| RTFQ | Number of days of the retraining frequency | 125 | 125 |
| BTCH | Batch size, in days | 125 | 125 |
| LR | Learning rate | 0.001 | 0.001 |
| EPCH | Number of optimization epochs | 100 | 100 |
| OPT | Optimization method | Adam | Adam |

**Table A.III. Performance of Candidate Models on the Last Year of the Validation Data Set**

| D | ATT | HDN | DRP | SR | μ | σ |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 2 | 2 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 8 | 2 | 2 | 0.50 | —ᴬ | —ᴬ | —ᴬ |
| 8 | 2 | 3 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 8 | 2 | 3 | 0.50 | —ᴬ | —ᴬ | —ᴬ |
| 8 | 4 | 2 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 8 | 4 | 2 | 0.50 | —ᴬ | —ᴬ | —ᴬ |
| 8 | 4 | 3 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 8 | 4 | 3 | 0.50 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 2 | 2 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 2 | 2 | 0.50 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 2 | 3 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 2 | 3 | 0.50 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 4 | 2 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 4 | 2 | 0.50 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 4 | 3 | 0.25 | —ᴬ | —ᴬ | —ᴬ |
| 16 | 4 | 3 | 0.50 | **4.650** | **17.3%** | **3.7%** |

*주:* candidate 16은 validation sample에서 가장 높았을 뿐 별도의 최종 OOS
성과가 아니다. 16개 전체 행의 최종 파일 경로는
`outputs/paper-korean/model-selection/table_a03_candidate_validation_performance.csv`다.
현재 PC에는 candidate 1의 부분 checkpoint만 있어 전체 표를 복원하지 않았다.

**Table A.IV. Alternative Best Performing Models on the Data from 2002-2016**

| Model | FLNB | FLSZ | ATT | HDN | DRP | LKB | WDW |
|---|---|---:|---:|---:|---:|---:|---:|
| Network 1 | [1, 8] | 2 | 4 | 16 | 0.25 | 30 | 1,000 |
| Network 2 | [1, 16] | 2 | 4 | 32 | 0.50 | 30 | 1,000 |
| Network 3 | [1, 8] | 2 | 2 | 16 | 0.25 | 30 | 1,000 |
| Network 4 | [1, 8] | 2 | 4 | 16 | 0.25 | 30 | 1,250 |
| Network 5 | [1, 8] | 2 | 4 | 16 | 0.25 | 30 | 750 |

**Table A.V. Performance of the Alternative Models on Our Benchmark Residual Datasets, 2002-2016**

| Model | Fama-French 5 SR | Fama-French 5 μ | Fama-French 5 σ | PCA 5 SR | PCA 5 μ | PCA 5 σ | IPCA 5 SR | IPCA 5 μ | IPCA 5 σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Network 1 | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴰ | —ᴰ | —ᴰ |
| Network 2 | 2.674 | —ᴬ | —ᴬ | 4.203 | —ᴬ | —ᴬ | —ᴰ | —ᴰ | —ᴰ |
| Network 3 | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴰ | —ᴰ | —ᴰ |
| Network 4 | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴰ | —ᴰ | —ᴰ |
| Network 5 | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴬ | —ᴰ | —ᴰ | —ᴰ |

*주:* 10개 전체 행의 최종 파일 경로는
`outputs/paper-korean/alternative-networks/table_a05_alternative_network_performance.csv`다.
현재 PC에는 해당 ignored GPU artifact가 없어 확인되지 않은 8개 수치를
추정하거나 채우지 않았다.

### C.2. 해석

![Figure A.2. 정책별 allocation과 signal](outputs/paper-korean/appendix-signals/fig_a02_policy_signals.png)

**Figure A.2. Allocation Weights and Signals for Different Methods.** 동일한
잔차경로에 대한 OU, Fourier, CNN 정책의 반응을 비교한다.

![Figure A.3. 추가 allocation과 signal 사례](outputs/paper-korean/appendix-signals/fig_a03_policy_signals.png)

**Figure A.3. Additional Allocation and Signal Examples.** Figure A.2의 추가
사례다.

![Figure A.4. 추가 sinusoidal attention](outputs/paper-korean/appendix-signals/fig_a04_additional_sinusoidal_attention.png)

**Figure A.4. Additional Attention Weights for Sinusoidal Inputs.** 합성 신호의
주기와 위상 변화에 대한 attention 반응을 추가로 보여준다.

### C.3. 무조건부 잔차평균

**Table A.VI. OOS Annualized Performance of Unconditional Average Residuals**

*Equally Weighted Residuals*

| K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | 2.287 | 10.1% | 4.4% | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |

**Table A.VII. Significance of Alphas Based on Unconditional Average Residuals**

*Equally Weighted Residuals*

| K | Fama-French α | Fama-French tα | Fama-French R² | Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 5 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | 9.2% | 3.23 | 4.6% | 10.1% | 3.54 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 8 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 10 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| 15 | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

무조건부 평균잔차도 양의 성과를 내므로 모든 수익성이 복잡한 시계열 신호에서만
나오는 것은 아니다. 그러나 CNN의 Sharpe 4.148보다 낮아 allocation timing이
추가 정보를 제공한다.

### C.4. 전략 간 의존성

**Table A.VIII. Correlations Between CNN+Transformer Strategy Returns**

|  | Fama-French 3 | PCA 3 | IPCA 3 | Fama-French 5 | PCA 5 | IPCA 5 | PCA 10 | IPCA 10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fama-French 3 | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᴰ |
| PCA 3 | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᴰ |
| IPCA 3 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| Fama-French 5 | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᴰ |
| PCA 5 | —ᵁ | —ᵁ | —ᴰ | —ᵁ | **1.00** | —ᴰ | —ᵁ | —ᴰ |
| IPCA 5 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |
| PCA 10 | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᵁ | —ᴰ | —ᵁ | —ᴰ |
| IPCA 10 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |

*주:* 현재 PC에는 rolling CNN 전략 하나만 동기화되어 상관행렬이 1×1이다.
원 논문과 같은 factor-model 간 dependency 결론을 내리려면 최신 전체 전략
artifact가 필요하다.

### C.5. 시계열 신호 ablation

**Table A.IX. OOS Annualized Performance Based on Sharpe Ratio Objective**

| Model | K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OU+FFN | 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| OU+FFN | 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| OU+FFN | 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| OU+FFN | 5 | —ᵁ | —ᵁ | —ᵁ | 1.878 | 8.3% | 4.4% | —ᴰ | —ᴰ | —ᴰ |
| OU+FFN | 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| OU+FFN | 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| OU+FFN | 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| FFN | 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| FFN | 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| FFN | 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| FFN | 5 | —ᵁ | —ᵁ | —ᵁ | 2.188 | 8.1% | 3.7% | —ᴰ | —ᴰ | —ᴰ |
| FFN | 8 | —ᴰ | —ᴰ | —ᴰ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| FFN | 10 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |
| FFN | 15 | —ᴺ | —ᴺ | —ᴺ | —ᵁ | —ᵁ | —ᵁ | —ᴰ | —ᴰ | —ᴰ |

CNN+Transformer의 높은 성과는 횡단면 allocation만이 아니라 잔차경로에서
학습한 시계열 representation과 관련된다.

### C.6. PCA 잔차의 거래마찰

**Table A.X. OOS Performance of CNN+Trans with Trading Frictions**

*PCA factor model*

| K | Sharpe ratio SR | Sharpe ratio μ | Sharpe ratio σ | Mean-variance SR | Mean-variance μ | Mean-variance σ |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 1 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 3 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 5 | 1.371 | 6.0% | 4.4% | —ᵁ | —ᵁ | —ᵁ |
| 10 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |
| 15 | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ | —ᵁ |

### C.7. 산업집중도

![Figure A.5. 포트폴리오 산업집중도](outputs/paper-korean/appendix/fig_a05_industry_concentration.png)

**Figure A.5. Industry Concentration of Portfolio Weights.** 한국 산업분류에
따른 weight 집중도를 보여준다. 원 논문의 SIC 분류와 완전히 동일하지 않은
한국 analogue다.

### C.8. 시간에 따른 시장효율성과 비용후 성과

![Figure A.6. 시간에 따른 잔차 변동성](outputs/paper-korean/appendix/fig_a06_residual_volatility.png)

**Figure A.6. Volatility of Residuals over Time.** 일별 횡단면 잔차변동성의 평균과
분위를 통해 차익거래 기회의 시간변화를 점검한다.

![Figure A.7. 거래비용 차감 후 누적수익률](outputs/paper-korean/appendix/fig_a07_returns_after_costs.png)

**Figure A.7. Cumulative Returns after Trading Costs.** 고정 거래비용을 차감한
누적수익률이다. 실제 한국 종목별 비용이 아니라 sensitivity라는 점에 유의한다.

## D. 45개 산출물 완전성 점검

| 구분 | 원 논문 번호 | 이 초안 배치 | 현재 파일 상태 |
|---|---|---:|---|
| 본문 Figure | 1–19 | 19/19 | 15개 확인, Figure 9–12 동기화 필요 |
| 본문 Table | 1–9 | 9/9 | Table 1 CNN grid 미실행·IPCA/FF8 차단; 일부 GPU 세부행 동기화 필요 |
| 부록 Figure | A.1–A.7 | 7/7 | 7개 확인 |
| 부록 Table | A.I–A.X | 10/10 | 번호·구조 배치, A.III·A.V 전체행 동기화 필요 |
| **합계** | **45개** | **45/45** | **번호 배치는 완료했으나 full scientific replication은 미완료** |

최종 제출 전 검증 순서는 다음과 같다.

1. 최신 GPU PC의 `guijarro-ordonez-2025-replication/outputs/` 전체를 이 PC의
   같은 경로로 복사한다.
2. `config/output-registry.yml`의 45개 `path`가 모두 실제 파일인지 검사한다.
3. Table 3–6, 9, A.III, A.V, A.VIII, A.X를 최신 CSV에서 다시 렌더링한다.
4. 수치·그림 설명과 `docs/execution-status.md`의 audit metric을 대조한다.
5. Typst 학위논문 source로 옮긴 뒤 PDF를 compile하고 표·그림 넘침과 인용을
   시각적으로 검수한다.
