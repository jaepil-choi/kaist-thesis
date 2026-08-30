# 잔차 포트폴리오를 만들지 않고, 잔차를 종목 선정 신호로만 썼다

**대상:** `build/ou_k0_v2.py`, `build/ou_pca_k5_v3.py`, `build/ou_ff5_v2.py`
**영향:** PCA K=5 / FF5 arm의 결과는 논문의 전략이 아니다. `FINDINGS.md`의 "Results" 표
세 줄 중 두 줄이 이에 해당한다.
**심각도:** replication 오류. vqapr 귀책 아님(단서는 아래 마지막 절).

## 논문이 요구하는 것

논문은 세 단계를 분리해서 정의한다(section 2.1–2.3).

1. **arbitrage portfolio 생성.** 잔차는 스칼라가 아니라 *거래 가능한 포트폴리오*다.
   `paper/deep-learning-statistical-arbitrage.md:648-660`, 식 (1):

   > `ε_t = R_t − β_{t−1} w^F_{t−1}ᵀ R_t = (I_{N_t} − β_{t−1} w^F_{t−1}ᵀ) R_t = Φ_{t−1} R_t`

   `Φ_{t−1}`가 **residual composition matrix**다. 잔차 n번 = "종목 n을 사고, 그 종목의
   factor 노출을 복제하는 mimicking portfolio를 판다"는 실제 종목 바스켓이다.
   바로 다음 줄(`paper/...:649`)에서 논문이 못박는다: *"As factors are traded assets, the arbitrage portfolios are
   themselves traded portfolios."*

2. **signal 추출.** OU가 여기 들어간다. 출력은 잔차 포트폴리오 n에 대한 배분 `w^ε_{n,t−1}`.

3. **arbitrage trading.** `paper/...:931-932` (식 (2)의 제약, 같은 식이 `:1029`와 `:1099`에 다시 나온다):

   > `w^R_{t−1} = (w^ε_{t−1}ᵀ Φ_{t−1}) / ‖w^ε_{t−1}ᵀ Φ_{t−1}‖₁`

   즉 **종목 가중치 `w^R`는 신호 가중치 `w^ε`를 `Φ`로 밀어 넣어서 만든다.** 전략 수익은
   `w^R_{t−1}ᵀ R_t`이고, `paper/...:980-982`가 정규화 대상을 명시한다: *"The stock weights
   `w^R_{t−1}` are normalized to add up to one in absolute value."* `paper/...:2874`도 같다:
   *"the sum of absolute **stock** weights is normalized to one."*

`ε_t = Φ_{t−1} R_t`이므로 `w^εᵀ ε_t = w^εᵀ Φ_{t−1} R_t`다. 논문의 수익은 잔차 포트폴리오
수익과 (정규화 스칼라를 빼면) 같고, 그래서 **팩터 노출이 구성상 상쇄된다.**

## 실제로 한 것

세 strategy 모두 OU gate를 통과한 종목에 곧바로 `±1`을 얹고 `Rebalance.of(long=..., short=...)`
로 넘겼다. `build/ou_pca_k5_v3.py`의 selection 부분이 그대로 종목 주문이 된다:

```python
longs  = {kept[i]: Decimal(1) for i in np.flatnonzero(long_m)}
shorts = {kept[i]: Decimal(1) for i in np.flatnonzero(short_m)}
...
return va.StrategyResult(decision=va.Rebalance.of(long=longs, short=shorts, invested="1"))
```

이것은 `w^R := w^ε`, 즉 **`Φ_{t−1} = I`로 두는 것**이다. mimicking portfolio leg이 없다.
잔차는 "어느 종목을 살지" 고르는 데만 쓰였고, 만들어진 book은 그 종목들의 **원래 주가 수익**을
그대로 먹는다. `β'F` 성분이 통째로 남아 있다.

## 결과가 실제로 무엇을 의미하는가

| arm | `Φ` | 논문의 전략인가 |
|---|---|---|
| K=0 | 진짜로 `I` (factor model이 없으므로) | **예** |
| PCA K=5 | `I − β w^Fᵀ`, rank 5 | 아니오 — 잔차를 신호로만 쓴 unhedged long/short |
| FF5 | `I − β w^Fᵀ`, rank 5 | 아니오 — 위와 같음 |

그래서 `FINDINGS.md`의 결론 문장 —

> *"Removing a factor structure before trading the residual helps, and helps a lot: K=0 loses
> money, both residual definitions make it. That is the paper's central qualitative claim
> (section 3.4) and it survives transplantation to Korea."*

— 은 이 세 숫자로부터 나오지 않는다. K=0만 논문대로 구현됐고, 나머지 둘은 논문의 residual
portfolio가 아니라 "잔차로 종목을 고른 미헤지 롱숏"이다. 세 숫자는 같은 전략의 세 변형이
아니라 **서로 다른 세 전략**이다. 관측된 개선분에는 factor hedge의 효과와 종목 선정 신호의
효과가 분리되지 않은 채 섞여 있고, 후자만 남아 있을 가능성이 크다.

`F-017`의 검증도 다시 봐야 한다. `‖w‖₁ = 1`을 정확히 맞춘 것은 사실이지만, 논문이 1로
묶으라는 벡터는 `Φ`를 통과시킨 뒤의 `w^R`이다. 여기서는 `Φ`를 건너뛴 탓에 두 벡터가 우연히
같아졌을 뿐이다. 제약을 만족시킨 게 아니라, 제약이 걸릴 대상이 없었다.

## 고치려면 무엇이 필요한가

핵심은 "한 줄 더 곱하면 된다"가 아니다. **DataModel의 출력 계약이 달라진다.**

현재 `residual_pca_v2` / `residual_ff5`는 `(date, instrument) → residual` 스칼라 하나를
낸다. `Φ_{t−1}`을 만들려면 `decide()`가 그날의 `β_{t−1}` (N×K)와 `w^F_{t−1}` (N×K)까지
받아야 한다. `Φ`를 N×N으로 만들지 말고 low-rank 형태 `I − β w^Fᵀ`로 유지하면
`w^εᵀΦ = w^ε − (w^εᵀβ) w^Fᵀ`로 O(NK)에 끝난다.

## vqapr 귀책인가

**아니다.** 논문을 잘못 읽은 것이고, 위 세 파일은 전부 내가 썼다.

**다만 하나는 FINDINGS 항목이 될 자격이 있고, 이번 run에서는 시도조차 되지 않았다:**
DataModel이 (date, instrument)당 **스칼라 하나가 아니라 K개짜리 벡터 두 개**를 내보낼 수
있는가, 그리고 strategy가 그것을 정렬된 행렬로 되받을 수 있는가. `F-005`가 이미 "행 하나에
무엇이 들어 있는지 public surface가 말해주지 않는다"를 기록했는데, 그 질문의 훨씬 어려운
버전이 여기 있다. 위 오류는 이 질문을 아예 회피한 결과이기도 하다. 다음 run에서는 `Φ`를
실어 나르는 것부터 시도하고, 막히는 지점을 `FINDINGS.md`에 적을 것.
