"""PCA / IPCA 를 4종목 장난감 예제로 처음부터 보여주는 학습용 스크립트.

Guijarro-Ordonez, Pelger, Zanotti (2025) "Deep Learning Statistical Arbitrage"
의 잔차 생성 단계를 개념적으로 이해하기 위한 자료다. 논문 결과를 재현하지
않는다. 숫자는 전부 합성 데이터이며, 유일하게 실제 코드를 호출하는 곳은
IPCA 의 ALS 추정(guijarro_ordonez_replication.ipca.fit_ipca_als)이다.

실행:
    uv run python scratch-pad-for-ai/explain_pca_vs_ipca_toy.py
    uv run python scratch-pad-for-ai/explain_pca_vs_ipca_toy.py --section 3
    uv run python scratch-pad-for-ai/explain_pca_vs_ipca_toy.py --seed 7

섹션:
    1  특성 스케일 문제와 횡단면 랭크 정규화
    2  PCA: 공분산 -> 고유벡터(베타) -> 팩터 -> 잔차
    3  PCA 는 최근 데이터를 더 볼 수 있나 (동일가중 vs 지수가중 vs 롤링)
    4  IPCA: Gamma 추정. 베타가 시간에 따라 변하는 것을 확인
    5  IPCA 일별 잔차 스텝 (팩터 = 베타비례 롱숏 포트폴리오)
    6  무엇이 언제 재추정되는가 (논문 코드 기준 요약)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "guijarro-ordonez-2025-replication" / "src"))

from guijarro_ordonez_replication.ipca import fit_ipca_als  # noqa: E402

NAMES = ["대형A", "대형B", "소형C", "소형D"]
RAW_CAP = [4_800_000, 1_300_000, 8_500, 3_200]  # 억원
RAW_PBR = [1.35, 1.80, 0.42, 0.65]
RAW_TURNOVER = [6_200, 3_100, 45, 12]  # 억원

# 손으로 만든 6일치 수익률(%). 대형2개가 같이, 소형2개가 따로 같이 움직인다.
DAILY_RETURNS = np.array(
    [
        [2.0, 1.8, 0.5, 0.3],
        [-1.5, -1.2, -0.3, -0.5],
        [3.0, 2.6, 1.0, 0.8],
        [-0.5, -0.8, 1.5, 1.2],
        [1.0, 1.2, -2.0, -1.8],
        [-2.0, -1.6, 0.3, 0.5],
    ]
)
DAY_LABELS = [f"D{i + 1}" for i in range(len(DAILY_RETURNS))]

# 섹션 4 의 데이터생성과정: 베타 = 1.0*사이즈랭크 + 0.0*밸류랭크
GAMMA_TRUE = np.array([[1.0], [0.0]])
N_MONTHS = 24
CAP_GROWTH_C = 1.42  # 소형C 가 월 42% 성장해 시총 1위가 된다

# 섹션 5 의 일별 수익률(%)
MONTH_DAILY_RETURNS = np.array(
    [
        [1.50, 0.10, 0.90, -0.60],
        [-2.20, -0.30, -1.00, 1.10],
        [0.80, 0.40, 0.20, 0.05],
    ]
)


def _banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def _frame(array, index, columns, decimals=3) -> str:
    return pd.DataFrame(array, index=index, columns=columns).round(decimals).to_string()


def _rank_normalize(values) -> np.ndarray:
    """repo 의 characteristics.rank_normalize_characteristics 와 같은 변환."""
    return pd.Series(values).rank(pct=True, method="average").to_numpy() - 0.5


def _top_eigenvectors(matrix, n_components, orient_positive=True):
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    if orient_positive:
        for k in range(eigenvectors.shape[1]):
            if eigenvectors[:, k].sum() < 0:
                eigenvectors[:, k] = -eigenvectors[:, k]
    return eigenvalues[:n_components], eigenvectors[:, :n_components]


# ---------------------------------------------------------------------------
def section_1_scaling() -> None:
    _banner("[1] 특성 스케일 문제와 횡단면 랭크 정규화")
    raw = pd.DataFrame(
        {"시가총액(억)": RAW_CAP, "PBR": RAW_PBR, "거래대금(억)": RAW_TURNOVER},
        index=NAMES,
    )
    print("원본 특성. 단위도 범위도 제각각이라 그대로 회귀에 넣을 수 없다.\n")
    print(raw.to_string())

    normalized = raw.apply(lambda col: _rank_normalize(col.to_numpy()))
    print("\nrank(pct=True) - 0.5 로 정규화하면 전부 (-0.5, 0.5] 의 같은 자에 올라간다.\n")
    print(normalized.round(3).to_string())
    offset = 1 / (2 * len(NAMES))
    print(
        f"\n  각 열 평균 = {normalized.mean().round(4).tolist()}."
        f"  rank(pct=True) 는 1/N..1 을 주므로 1/(2N)={offset:.3f} 만큼 치우친다."
        "\n  종목 2000개면 0.00025 라 무시할 수 있지만 소표본에서는 눈에 띈다."
    )


# ---------------------------------------------------------------------------
def section_2_pca() -> None:
    _banner("[2] PCA: 공분산 -> 고유벡터(베타) -> 팩터 -> 잔차")
    returns = DAILY_RETURNS
    print("6일치 일별 수익률(%). 대형2개가 같이, 소형2개가 따로 같이 움직이도록 만들었다.\n")
    print(_frame(returns, DAY_LABELS, NAMES, 2))

    centered = returns - returns.mean(axis=0)
    covariance = np.cov(centered, rowvar=False)
    print("\n[2a] 공분산행렬. 대형A-대형B(3.47)와 소형C-소형D(1.31)가 크고 교차항은 0 근처다.\n")
    print(_frame(covariance, NAMES, NAMES, 2))

    eigenvalues, eigenvectors = _top_eigenvectors(covariance, 4)
    share = eigenvalues / eigenvalues.sum() * 100
    print("\n[2b] 고유값 = 각 방향이 설명하는 변동 크기\n")
    print(
        pd.DataFrame(
            {"고유값": eigenvalues.round(3), "설명비중(%)": share.round(1)},
            index=[f"PC{i + 1}" for i in range(4)],
        ).to_string()
    )
    print("\n  PC1+PC2 가 99.8% 를 설명한다. 4종목의 움직임이 사실상 2개 힘으로 환원된다.")

    print("\n[2c] 고유벡터 = PCA 베타. PC1 은 대형에만, PC2 는 소형에만 걸린다.")
    print("     시가총액을 알려준 적이 없는데 공분산 구조만으로 무리를 찾아냈다.\n")
    print(_frame(eigenvectors[:, :2], NAMES, ["PC1", "PC2"]))

    factors = centered @ eigenvectors[:, :2]
    print("\n[2d] 팩터 수익률 = 베타를 가중치로 한 포트폴리오 수익률\n")
    print(_frame(factors, DAY_LABELS, ["PC1", "PC2"]))

    residual_1 = centered - factors[:, :1] @ eigenvectors[:, :1].T
    residual_2 = centered - factors @ eigenvectors[:, :2].T
    print("\n[2e] PC1+PC2 제거 후 잔차(%) - 논문이 딥러닝에 먹이는 재료\n")
    print(_frame(residual_2, DAY_LABELS, NAMES))
    print("\n  횡단면 표준편차가 어떻게 줄어드는가:")
    print(f"    원수익률      {centered.std(0).round(2)}")
    print(f"    PC1 제거 후   {residual_1.std(0).round(2)}   <- 대형만 잡힘")
    print(f"    PC1+2 제거 후 {residual_2.std(0).round(2)}   <- 전부 잡힘")


# ---------------------------------------------------------------------------
def _weighted_pc1(sample, weights=None):
    """가중 PCA 의 1번 주성분. weights=None 이면 표준(동일가중) PCA."""
    if weights is None:
        weights = np.ones(len(sample))
    weights = weights / weights.sum()
    mean = (weights[:, None] * sample).sum(axis=0)
    centered = sample - mean
    covariance = (weights[:, None] * centered).T @ centered
    _, vectors = _top_eigenvectors(covariance, 1)
    return vectors[:, 0]


def _regime_shift_returns(rng, n_half):
    """레짐 전환 패널.

    앞 절반(과거): 대형 2종목이 강하게 동조, 소형은 개별적. -> PC1 = 대형 팩터
    뒤 절반(현재): 소형 2종목이 동조, 대형은 개별적.        -> PC1 = 소형 팩터

    과거 레짐의 진폭을 더 크게(3.0 vs 2.0) 주어, 전체 동일가중 PCA 가
    '낡았지만 변동이 컸던' 구조에 끌려가도록 만든다.
    """
    old_amp, new_amp, idio = 3.0, 2.0, 0.4
    large_factor = rng.normal(0, old_amp, n_half)
    small_factor = rng.normal(0, new_amp, n_half)
    returns = np.zeros((2 * n_half, 4))
    noise = lambda scale: rng.normal(0, scale, n_half)  # noqa: E731
    # 레짐 1 (과거): 대형만 동조
    returns[:n_half, 0] = 1.0 * large_factor + noise(idio)
    returns[:n_half, 1] = 0.9 * large_factor + noise(idio)
    returns[:n_half, 2] = noise(idio)
    returns[:n_half, 3] = noise(idio)
    # 레짐 2 (현재): 소형만 동조
    returns[n_half:, 0] = noise(idio)
    returns[n_half:, 1] = noise(idio)
    returns[n_half:, 2] = 1.0 * small_factor + noise(idio)
    returns[n_half:, 3] = 0.9 * small_factor + noise(idio)
    return returns


def section_3_recency(seed: int) -> None:
    _banner("[3] PCA 는 최근 데이터를 더 볼 수 있나")
    print(
        "질문: PCA 는 윈도우 안의 모든 날을 똑같이 세는가?\n"
        "답: 표준 PCA 는 그렇다. 최근성을 반영하는 방법이 세 가지 있고,\n"
        "    논문 코드는 (b) 지수가중은 쓰지 않고 (c) 롤링만 쓴다."
    )

    n_half = 120
    halflife = 40.0
    returns = _regime_shift_returns(np.random.default_rng(seed), n_half)

    age = np.arange(len(returns))[::-1]
    results = {
        "(a) 전체 240일 동일가중": _weighted_pc1(returns),
        f"(b) 지수가중 반감기{halflife:.0f}일": _weighted_pc1(returns, 0.5 ** (age / halflife)),
        "(c) 최근 120일 롤링": _weighted_pc1(returns[-n_half:]),
    }

    print("\n실험: 240일 표본에 레짐 전환을 심는다.")
    print("      과거 120일 = 대형 2종목만 동조 (진폭 3.0, 크게 움직였다)")
    print("      현재 120일 = 소형 2종목만 동조 (진폭 2.0)")
    print("      '지금'의 진짜 구조는 소형이다. PC1 이 소형C/소형D 에 걸려야 정답.\n")
    table = pd.DataFrame(results, index=NAMES)
    print(table.round(3).to_string())
    print("\n  각 방식이 무엇을 PC1 으로 골랐나 (절대 로딩이 큰 쪽):")
    for label, loading in results.items():
        large = np.abs(loading[:2]).sum()
        small = np.abs(loading[2:]).sum()
        verdict = "대형 팩터 (낡음)" if large > small else "소형 팩터 (현재)"
        print(f"    {label:24s} -> {verdict}   대형합={large:.3f} 소형합={small:.3f}")
    print(
        "\n  (a) 는 진폭이 컸던 과거 레짐에 끌려간다. (b),(c) 는 현재 구조를 잡아낸다.\n"
        "\n논문 코드가 실제로 쓰는 방식 (factor_models/pca.py):\n"
        "  - 지수가중은 쓰지 않는다. 윈도우 안은 전부 동일가중(np.mean)이다.\n"
        "  - 대신 롤링 윈도우를 쓰고 매 거래일 고유값분해를 다시 한다.\n"
        "      size_covariance_window = 252  (고유벡터 추정)\n"
        "  - 추가로 2단 윈도우를 쓴다. 252일로 고유벡터를 뽑은 뒤\n"
        "    최근 60일만으로 로딩을 다시 회귀한다.\n"
        "      size_window = 60              (로딩 회귀)\n"
        "    -> 계단식이지만 최근 60일에 더 큰 비중을 주는 장치다."
    )


# ---------------------------------------------------------------------------
def section_4_ipca(seed: int) -> np.ndarray:
    _banner("[4] IPCA: Gamma 추정. 베타가 시간에 따라 변하는 것을 확인")
    rng = np.random.default_rng(seed)

    size_rank = np.zeros((N_MONTHS, 4))
    value_rank = np.zeros((N_MONTHS, 4))
    for t in range(N_MONTHS):
        caps = [RAW_CAP[0], RAW_CAP[1], RAW_CAP[2] * (CAP_GROWTH_C**t), RAW_CAP[3]]
        size_rank[t] = _rank_normalize(caps)
        value_rank[t] = _rank_normalize(RAW_PBR)

    print("소형C 의 시총을 매달 42% 키워 시총 1위로 만든다. 사이즈 랭크의 변화:\n")
    print(_frame(size_rank[[0, 8, 16, 23]], ["M1", "M9", "M17", "M24"], NAMES))

    chars = np.stack([size_rank, value_rank], axis=2)  # T x N x L
    beta_true = chars @ GAMMA_TRUE  # T x N x 1
    factors_true = rng.normal(0, 3.0, size=N_MONTHS)
    returns = beta_true[:, :, 0] * factors_true[:, None] + rng.normal(0, 0.5, (N_MONTHS, 4))

    print("\n정답을 심어둔다:  베타 = 1.0*사이즈랭크 + 0.0*밸류랭크")
    print("이 24개월 패널을 replication repo 의 실제 함수 fit_ipca_als 에 그대로 넣는다.")

    fit = fit_ipca_als(
        tuple(returns[t] for t in range(N_MONTHS)),
        tuple(chars[t] for t in range(N_MONTHS)),
        n_factors=1,
        max_iterations=1500,
        tolerance=1e-3,
    )
    print(
        f"\n  iterations={fit.iterations}  converged={fit.converged}  "
        f"final_delta={fit.final_delta:.2e}\n"
    )
    scale = fit.gamma[0, 0] / GAMMA_TRUE[0, 0]
    print(
        pd.DataFrame(
            {
                "추정 Gamma": fit.gamma[:, 0],
                "스케일 정규화": fit.gamma[:, 0] / scale,
                "진짜 Gamma": GAMMA_TRUE[:, 0],
            },
            index=["사이즈랭크", "밸류랭크"],
        )
        .round(4)
        .to_string()
    )
    factors_hat = np.array([fit.factors[t][0] for t in range(N_MONTHS)])
    print(f"\n  추정팩터 vs 진짜팩터 상관 = {np.corrcoef(factors_hat, factors_true)[0, 1]:.4f}")
    print(
        f"\n  Gamma 가 진짜값의 {scale:.2f} 배로 나온 것에 주의.\n"
        "  (베타 x c) x (팩터 / c) = 같은 수익률 이므로 눈금이 식별되지 않는다.\n"
        "  Kelly-Pruitt-Su 원논문은 Gamma'Gamma = I 로 눈금을 고정하지만\n"
        "  이 논문의 공개 코드도 replication 코드도 그 정규화를 하지 않는다.\n"
        "  -> 한국 패널에서 Gamma 가 3.36e23 까지 발산한 문제의 근본 원인."
    )

    beta_path = (chars @ fit.gamma)[:, :, 0] / scale
    print("\n[4a] Gamma 는 24개월 내내 하나인데 베타는 저절로 변한다\n")
    print(_frame(beta_path[[0, 8, 16, 23]], ["M1", "M9", "M17", "M24"], NAMES))
    print("\n  소형C: -0.01 -> 0.49.  대형A: 0.51 -> 0.26.  PCA 로는 불가능한 일이다.")
    return beta_path[16]


# ---------------------------------------------------------------------------
def section_5_daily_residuals(beta_vector) -> None:
    _banner("[5] IPCA 일별 잔차 스텝")
    beta = np.round(beta_vector, 3).reshape(-1, 1)
    print("월초에 전월말 특성으로 베타를 확정하고 한 달간 고정한다.")
    print("  (오늘 잔차에 오늘 시총을 쓰면 look-ahead 가 된다)\n")
    print(_frame(beta, NAMES, ["beta"]))

    daily = MONTH_DAILY_RETURNS
    labels = [f"D{i + 1}" for i in range(len(daily))]
    print("\n이번 달 일별 수익률(%)\n")
    print(_frame(daily, labels, NAMES, 2))

    projection = np.linalg.pinv(beta.T @ beta) @ beta.T
    print("\n[5a] 팩터 추출 가중치 pinv(b'b) b'\n")
    print(_frame(projection, ["가중치"], NAMES, 4))
    print(
        f"\n  베타에 정확히 비례한다 (베타 / b'b, b'b={float((beta.T @ beta)[0, 0]):.4f}).\n"
        "  즉 팩터 = 베타 큰 종목 롱 / 베타 음수인 종목 숏 하는 실제 포트폴리오.\n"
        f"  {NAMES[3]} 는 베타가 음수라 가중치도 음수 = 공매도."
    )

    rows = []
    for day_idx, day_returns in enumerate(daily):
        factor = float((projection @ day_returns)[0])
        residual = day_returns - beta[:, 0] * factor
        rows.append([factor, *residual])
        if day_idx == 0:
            terms = " + ".join(f"{w:.4f}*({r})" for w, r in zip(projection[0], day_returns))
            print(f"\n  [D1 손계산] f = {terms} = {factor:.4f}")
            print(
                f"  [D1] {NAMES[0]} 잔차 = {day_returns[0]} - "
                f"{beta[0, 0]}*{factor:.4f} = {residual[0]:.4f}"
            )

    table = pd.DataFrame(rows, index=labels, columns=["팩터 f(%)"] + [f"{n} 잔차" for n in NAMES])
    print("\n[5b] 팩터와 잔차\n")
    print(table.round(4).to_string())

    residuals = table.iloc[:, 1:].to_numpy()
    print("\n[5c] 검증: 잔차는 베타와 직교하는가 (0 이어야 함)")
    print(f"    잔차 @ 베타 = {(residuals @ beta[:, 0]).round(12)}")
    print("    팩터 노출이 정확히 0. 이것이 '리스크 중립화'의 수학적 정의다.\n")
    print(f"    횡단면 변동성: 원수익률 {daily.std(1).round(3)} -> 잔차 {residuals.std(1).round(3)}")


# ---------------------------------------------------------------------------
def section_6_schedule() -> None:
    _banner("[6] 무엇이 언제 재추정되는가 (논문 코드 기준)")
    print(
        "질문: IPCA 는 매일 PCA 를 하는 것인가?\n"
        "답: 아니다. IPCA 에서 PCA 는 ALS 의 '초기값'으로 Gamma 추정 때만 한 번 쓰인다.\n"
        "    일별 스텝에는 고유값분해가 전혀 없다. 베타가 이미 주어져 있으므로\n"
        "    그냥 횡단면 OLS 사영일 뿐이다.\n"
    )
    schedule = pd.DataFrame(
        [
            ["PCA", "고유값분해", "매 거래일", "직전 252 거래일", "eigh 를 매일 다시 푼다"],
            ["PCA", "로딩 회귀", "매 거래일", "직전 60 거래일", "고유벡터를 짧은 창에 재회귀"],
            ["PCA", "팩터/잔차", "매 거래일", "당일", "-"],
            ["IPCA", "PCA (ALS 초기값)", "Gamma 추정시 1회", "월간 240개월", "sklearn PCA(X.T)"],
            ["IPCA", "Gamma (ALS)", "12개월마다", "월간 240개월", "이전 Gamma 에서 워밍스타트"],
            ["IPCA", "베타 = Z @ Gamma", "매월 1회", "전월말 특성", "한 달간 고정"],
            ["IPCA", "팩터/잔차", "매 거래일", "당일", "고유값분해 없음. 단순 OLS"],
        ],
        columns=["브랜치", "무엇을", "언제", "무슨 데이터로", "비고"],
    )
    print(schedule.to_string(index=False))
    print(
        "\n핵심 대비:\n"
        "  PCA  - 베타를 '수익률 공분산'에서 매일 새로 뽑는다. 종목당 숫자 하나, 상수.\n"
        "  IPCA - 베타를 '특성 x Gamma' 로 만든다. Gamma 는 1년에 한 번 갱신되지만\n"
        "         특성이 매달 갱신되므로 베타는 매달 변한다.\n"
        "\n따라서 최근성 반영 방식도 다르다:\n"
        "  PCA  - 252일 롤링 창을 매일 갱신. 시장 구조 변화에 빠르게 반응.\n"
        "  IPCA - Gamma 는 20년 창으로 느리게, 베타는 특성을 통해 매달 빠르게.\n"
        "         '무엇이 리스크인가'는 천천히, '이 종목이 얼마나 노출됐나'는 빠르게."
    )


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--section", type=int, choices=range(1, 7), default=None, help="특정 섹션만 실행 (기본: 전부)"
    )
    parser.add_argument("--seed", type=int, default=7, help="난수 시드 (기본 7)")
    args = parser.parse_args()

    pd.set_option("display.width", 200)
    np.set_printoptions(precision=4, suppress=True)

    wanted = args.section

    def run(n: int) -> bool:
        return wanted is None or wanted == n

    if run(1):
        section_1_scaling()
    if run(2):
        section_2_pca()
    if run(3):
        section_3_recency(args.seed)
    if run(4) or run(5):
        beta_vector = section_4_ipca(args.seed)
        if run(5):
            section_5_daily_residuals(beta_vector)
    if run(6):
        section_6_schedule()
    print()


if __name__ == "__main__":
    main()
