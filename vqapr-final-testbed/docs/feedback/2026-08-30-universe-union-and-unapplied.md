# 유니버스를 연 단위 union으로 고정했고, K=0 arm에는 아예 적용하지 않았다

**대상:** `build/prepare_venue.py`, `build/ou_k0_v2.py`, `build/run_ou_*_v2.yaml`
**영향:** 세 arm이 같은 cross-section을 보고 있다는 `FINDINGS.md`의 전제가 성립하지 않는다.
K=0 arm에는 미래 정보가 들어가 있다.
**심각도:** replication 오류 + look-ahead. vqapr 귀책 아님.

## 세 가지 오류가 겹쳐 있다

### 1. roster가 한 해의 union이다 — look-ahead

`build/prepare_venue.py:32-36`:

```sql
-- roster: every name in the universe at any point in the window
select distinct instrument from pan
where in_universe and session_date between '2024-01-01' and '2024-12-31'
```

이 리스트가 그대로 `build/run_ou_k0_v2.yaml`의 `instruments:` 854개가 된다. 그런데 논문의
필터는 **월 단위**다(`paper/deep-learning-statistical-arbitrage.md:1959-1963`): *"stocks whose
market capitalization at the previous month was larger than 0.01% of the total market
capitalization at that previous month"*. `build/prepare_panel.py`가 그 규칙을 제대로
구현해서 `in_universe`를 월별로 붙여 놨는데, venue를 만들 때 그것을 연 단위로 뭉갰다.

2024년 월별 유니버스 크기와 union:

```
2024-01  712    2024-05  695    2024-09  642
2024-02  729    2024-06  703    2024-10  657
2024-03  718    2024-07  675    2024-11  648
2024-04  709    2024-08  656    2024-12  646
union(2024) = 854
```

어느 달을 기준으로 봐도 roster가 17~25% 부풀어 있다. 더 나쁜 것은 **2024-01-02 시점의
venue에 그 해 12월에야 유니버스에 들어온 종목이 이미 들어 있다**는 점이다. 연말이 되어야
알 수 있는 집합을 연초부터 거래 가능 대상으로 쥐고 시작했다. 전형적인 look-ahead다.

논문은 이 데이터셋이 unbalanced임을 명시하고(`paper/...:1965-1967`) 월별로 구성이 바뀌는 것을
전제한다. union으로 고정하는 것은 그 설계를 정확히 반대로 뒤집는 것이다.

### 2. K=0 arm은 `in_universe`를 한 번도 보지 않는다

| 파일 | 요청 필드 | 유니버스 적용 |
|---|---|---|
| `build/residual_pca_v2.py:50` | `("excess_return", "in_universe")` | 적용 (`:101`) |
| `build/residual_ff5.py:45` | `("excess_return", "in_universe")` | 적용 (`:92`) |
| `build/ou_k0_v2.py:53` | `("excess_return",)` | **없음** |

K=0은 residual materialization을 거치지 않고 `krx-daily`를 직접 읽는데, 그 경로에서
`in_universe`를 요청하지 않았다. 그래서 K=0 arm은 854개 union 전체를 대상으로 거래했고,
PCA/FF5 arm은 그날 유니버스(642~729개)만 봤다.

`FINDINGS.md`가 재실행 이유로 적어 둔 문장 —

> *"so the three factor families are compared on the same screened cross-section, which is
> the only way the comparison means anything"*

— 은 변동성 스크린에 대해서만 참이고, 유니버스에 대해서는 거짓이다. **가장 이상한 숫자가
나온 arm(K=0, Sharpe −1.079)이 정확히 유니버스가 적용되지 않은 arm이다.** 그 −1.079에는
실행 지연뿐 아니라 "그날 유니버스에 없는 종목 100~200개를 추가로 거래한 효과"가 섞여 있고,
현재 산출물로는 둘이 분리되지 않는다.

### 3. 필터의 *의도*를 옮기지 않고 문구만 옮겼다

논문이 시총 규칙을 도입하는 문장은 `paper/...:1957`이다:

> *"Our analysis uses only the most liquid stocks in order to avoid trading and market
> friction issues."*

시총은 **CRSP에서 유동성의 proxy로** 쓰인 것이지 그 자체가 목적이 아니다. 그리고 논문은
그 필터가 잘 작동한다는 근거를 두 개 제시한다:

- `paper/...:1963` — 평균 약 **550종목**, S&P 500과 대략 일치.
- `paper/...:2060` — rolling window 안에서 결측으로 탈락하는 종목은 **최대 2%**,
  `paper/...:2043-2044` — 다음날 결측은 **0.1%**.

이 두 수치가 sanity anchor다. 한국에 옮겼더니 **854종목**이 나왔다. 미국보다 훨씬 작은
시장에서 논문보다 55% 많은 종목이 나온 시점에서 "필터가 옮겨지지 않았다"고 판단했어야 했다.
`F-020`이 뒤늦게 발견한 것 — 2024년 수익률 sd가 0.002 미만인 종목 5개, 244세션 동안 서로
다른 수익률이 30개 미만인 종목 51개 — 은 논문의 2% / 0.1% 기준을 한참 벗어난다. KRX에는
CRSP의 대형주에 없는 거래정지·관리종목·사실상 정지 종목이 시총 필터를 통과한 채 남는다.

그 상황에서 취한 조치가 `SD_FLOOR_FRACTION = 0.1`, 즉 **패널 median sd의 10%라는 근거 없는
컷오프를 사후에 발명한 것**이었다. 논문에 없는 숫자고, 왜 0.1인지 어디에도 없다. 옳은 순서는
반대다: 논문이 시총으로 달성하려던 *유동성* 기준을 한국 데이터에 맞는 관측 가능한 형태로
다시 정의하고(거래대금 / 거래량 / 무거래일 비율), 그것을 **월별 유니버스 규칙 안에** 넣은
다음, 논문의 550종목·2%·0.1% anchor와 대조해 통과 여부를 판정하는 것이다. 논문 자신이 PCA
branch에 대해 이미 규칙을 하나 주고 있다(`paper/...:2056-2058`): *"At each day we only consider
the stocks with no missing observations in the daily returns during the rolling window."*
이것은 구현됐지만, 결측이 아니라 **움직이지 않는** 종목은 이 규칙을 통과한다.

`build/prepare_panel.py`가 이미 `tradable`(거래정지 아님 + 관리종목 아님)을 계산해 두었는데,
유니버스 규칙에도 strategy의 `decide()`에도 쓰이지 않았다. 가장 값싼 첫 수정은 이것이다.

## 정리하면

- roster는 월별로 바뀌어야 하고, 그 달 이전 정보만으로 결정되어야 한다.
- 세 arm 모두 같은 유니버스 규칙을 통과한 cross-section 위에서 결정해야 한다. K=0도 예외가
  아니다.
- 시총 필터 하나를 그대로 옮기는 것으로는 부족하다. 논문이 명시한 550/2%/0.1% anchor에
  맞춰 한국용 유동성 기준을 세우고, 통과하지 못하면 그 사실을 결과와 함께 적어야 한다.
- 사후에 발명한 `SD_FLOOR_FRACTION`은 유니버스 규칙이 제대로 서면 필요 없어진다. 남긴다면
  왜 그 값인지 근거가 있어야 한다.

## vqapr 귀책인가

**아니다.** 세 파일 모두 내가 썼고, `in_universe`는 요청하기만 하면 나오는 필드였다.

다만 `F-019`/`F-020`에서 이미 적은 관찰이 여기서 한 번 더 강해진다. 그날 유니버스에 없는
종목 200개를 1년 내내 들고 있는 시뮬레이션 세 개가 전부 `ok: true`로 끝났고, run record의
어떤 artifact도 그것을 드러내지 않는다. roster가 어떤 규칙으로 정해졌는지, 그 규칙이 기간
내내 고정이었는지는 `vqapr show run` 어디에도 남지 않는다 — `F-009`/`F-016`이 실행 시점
convention에 대해 지적한 것과 같은 종류의 공백이다.
