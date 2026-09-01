# notebooks

논문 본문·부록 산출물은 `run.py`가 만든다. 이 디렉터리는 그 산출물을 만들기 전후로
**모델 내부를 이해하기 위한 학습·탐색용 노트북**만 둔다.

| 노트북 | 내용 | 필요한 입력 |
|---|---|---|
| `cnn-transformer-intuition.ipynb` | CNN weight sharing, causal padding, 학습된 국소 패턴, attention, NAAG 기여도, 상승/하락 비대칭 — 논문 Figure 14–19에 대응하는 해석 분석 | `outputs/strategies/pca5_cnn_transformer_sharpe_lb30_e100_rolling_no-cost/checkpoints/subperiod_00.pt`, `outputs/pca/daily_residuals_k5_20200102_c252_l60.parquet` |

실행:

```bash
uv run jupyter lab guijarro-ordonez-2025-replication/notebooks/cnn-transformer-intuition.ipynb
```

전부 CPU에서 수 분 내에 끝난다. 저자 공식 노트북
(`Deep_Learning_Statistical_Arbitrage_Code/notebooks/`)과 달리 미국 IPCA5 잔차나
GPU가 필요 없다.

## 주의

- 여기 그림은 전부 **한국 표본** 결과다 (잔차 2020-01-02~2026-07-20, 정책 OOS 2024-01-19~).
  원 논문의 미국 1998–2016 수치와 같을 이유가 없다.
- 공식 성과 수치는 노트북이 아니라 `outputs/strategies/*/simulation_audit.json`과
  `daily_performance.csv`를 인용한다.
- 노트북에 저장된 출력은 실행 시점 기준이다. 체크포인트를 재학습하면 다시 실행해야 한다.
