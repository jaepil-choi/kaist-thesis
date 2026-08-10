# Deep Learning Statistical Arbitrage: home GPU handoff

작성 시점은 2026-08-10이다. 회사 PC의 GPU 부재로 장시간 학습을 의도적으로
중단했다. 목표는 완료가 아니라 **checkpointed handoff** 상태다. 실행 중이던
Python 프로세스는 모두 종료했으며, 매 epoch 저장되는 체크포인트는 보존했다.

## 1. 현재 결론

- 논문의 residual composition, rolling PCA·FF residual, 46개 characteristic,
  IPCA ALS, OU/Fourier/CNN 정책, 비용·다기간 목적함수, numbered report,
  robustness, interpretability, appendix runner는 구현됐다.
- 논문이 요구하는 PCA K=0, 1, 3, 5, 8, 10, 15 입력 패널은 모두 생성됐다.
  K=0은 PCA5 기준 유니버스의 개별주식 초과수익률이다.
- PCA·FF의 OU 전 사양, PCA K=0/1/3/5 Fourier, FF1/3/5 Fourier, PCA5
  constant CNN, direct FFN, OU-feature FFN은 full-contract 실행이 끝났다.
- 45개 번호 산출물 가운데 현재 레지스트리는 35개를
  `generated_*`, 1개를 `implemented_checkpointed_full_grid`, 9개를
  `implemented_waiting_full_run`으로 분류한다.
- 이 결과는 미국 표본 exact replication이 아니다. 한국
  **현금배당 제외 price-return variant**이며 재무는 사용자가 승인한 고정
  3개월 lag non-PIT sensitivity다.

상세 성과와 표본 계약은 `docs/execution-status.md`, 45개별 상태는
`config/output-registry.yml`을 따른다.

## 2. Git만으로 옮겨지지 않는 파일

`guijarro-ordonez-2025-replication/outputs/`는 의도적으로 gitignore된다.
현재 272개 파일, 약 0.679 GiB이며 체크포인트 72개를 포함한다. 집 PC에서
재개하려면 **이 디렉터리 전체를 경로 구조 그대로 복사**해야 한다. Git clone이나
pull만 하면 체크포인트가 없어 처음부터 다시 학습한다.

원천 데이터도 저장소 정책상 Git 전달을 가정하지 않는다. 집 PC에 없다면 최소한
아래 경로를 함께 복사한다.

- `data/kaist_pilot/canonical/common/korean_equity/`
- `data/kaist_pilot/canonical/guijarro_2025/`
- `data/kimchi-factor/`

재개 학습 자체는 이미 만들어진 `outputs/pca/`,
`outputs/fama-french/`, `outputs/ipca/`를 사용하므로 전체
`outputs/`를 복사하는 것이 가장 안전하다. 부분 체크포인트 디렉터리를 정리하거나
이름을 바꾸면 안 된다.

## 3. 집 PC GPU preflight

저장소 루트에서 최신 커밋을 받고 `uv sync`한 다음 아래를 확인한다.

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) 'scratch-pad-for-ai\uv-cache-dlsa-home'
$env:DLSA_DEVICE = 'cuda'
uv sync
uv run python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

`torch.cuda.is_available()`가 `True`가 아니면 학습을 시작하지 않는다.
현재 구현은 `DLSA_DEVICE`를 우선하고, 미설정 시 CUDA가 있으면 자동으로
`cuda`, 없으면 `cpu`를 선택한다. CUDA용 PyTorch 설치 여부는 집 PC에서
별도로 확인해야 한다. 여러 실험을 동시에 돌리면 VRAM과 CPU preprocessing이
경합하므로 아래 명령은 **한 번에 하나씩** 실행하는 편이 안전하다.

## 4. 중단 지점과 재개 명령

체크포인트는 매 epoch atomic replace로 저장되고
`simulation_audit.json`은 모든 OOS subperiod가 끝난 뒤에만 생성된다. 같은
명령을 다시 실행하면 아래 저장 epoch 다음부터 자동 재개한다.

| 우선순위 | 실행 | 저장된 마지막 지점 | 재개 시점 |
|---:|---|---|---|
| 1 | PCA5 rolling CNN Sharpe | subperiod 0–2 완료, subperiod 3 epoch 79 | subperiod 3 epoch 80 |
| 2 | PCA5 friction-aware CNN | subperiod 0–1 완료 | subperiod 2 epoch 1 |
| 3 | PCA5 CNN mean-variance | subperiod 0 epoch 32 | subperiod 0 epoch 33 |
| 4 | PCA8 Fourier+FFN | subperiod 0 완료, subperiod 1 epoch 98 | subperiod 1 epoch 99 |
| 5 | PCA10 Fourier+FFN | subperiod 0–1 완료, subperiod 2 epoch 13 | subperiod 2 epoch 14 |
| 6 | PCA15 Fourier+FFN | subperiod 0 완료, subperiod 1 epoch 76 | subperiod 1 epoch 77 |
| 7 | 16-model validation grid | candidate 1 완료, candidate 2 epoch 93 | candidate 2 epoch 94 |

재개 명령은 다음과 같다.

```powershell
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer_frictions --simulation-transaction-cost 0.0005 --simulation-short-holding-cost 0.0001
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer --simulation-objective meanvar
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors 8 --simulation-model fourier_ffn
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors 10 --simulation-model fourier_ffn
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors 15 --simulation-model fourier_ffn
uv run python guijarro-ordonez-2025-replication/run.py run-model-selection
```

candidate 1의 validation 결과는 annual return 0.12520, annual volatility
0.03466, Sharpe 3.61227이며 이미 audit가 있다. validation table과 최종 audit는
16개 candidate가 모두 끝난 뒤 생성된다.

## 5. 아직 시작하지 않은 장시간 실행

위의 중단 작업을 먼저 끝낸 뒤 다음 순서로 실행한다.

```powershell
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer --simulation-lookback-days 60
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer --simulation-holding-days 5
uv run python guijarro-ordonez-2025-replication/run.py run-alternative-networks --alternative-max-models 5 --simulation-epochs 100
uv run python guijarro-ordonez-2025-replication/run.py estimate-ipca --ipca-factors 1 --ipca-initial-months 60 --ipca-window-months 60 --allow-short-history-ipca
```

마지막 IPCA 명령은 exact replication이 아니라 short-history sensitivity다.
K=5, 60개월 실행은 공개 코드의 1,500회/1e-3 convergence gate를 통과하지
못했으며 residual 파일을 만들지 않았다. K=1도 수렴을 보장하지 않으며 실패하면
그 실패가 결과다. exact IPCA는 240개월 이력이 없어 계속 차단된다.

## 6. 학습 완료 후 산출물 재생성

모든 실행을 마친 뒤 아래를 순서대로 실행한다.

```powershell
uv run python guijarro-ordonez-2025-replication/run.py report-strategies
uv run python guijarro-ordonez-2025-replication/run.py build-robustness
uv run python guijarro-ordonez-2025-replication/run.py build-interpretability
uv run python guijarro-ordonez-2025-replication/run.py build-appendix
uv run python guijarro-ordonez-2025-replication/run.py build-appendix-signals
uv run python guijarro-ordonez-2025-replication/run.py build-risk-premium
uv run python guijarro-ordonez-2025-replication/run.py status
```

그 다음 `config/output-registry.yml`과 `docs/execution-status.md`를 실제
audit에 맞춰 갱신한다. 특히 다음 연결을 확인한다.

- primary rolling CNN: Figures 5, 8–11, Appendix Figures A.5/A.7,
  Tables 1/2/A.8
- five-day holding: Figure 12 Panel B
- 60-day lookback: Tables 5/6
- friction-aware CNN: Figures 6/7, Table 9, Appendix Table A.10
- CNN mean-variance: Tables 3/4의 CNN 행
- validation grid: Appendix Table A.3
- alternative networks: Appendix Table A.5

## 7. 최종 검증과 커밋

```powershell
uv run pytest guijarro-ordonez-2025-replication/tests -p no:cacheprovider
uv run ruff check guijarro-ordonez-2025-replication
git status --short
```

현재 CPU→GPU 자동선택 변경은 `test_trading.py`로 검증했다. 전체 완료 시에도
미국 CRSP/Compustat, total return, 240개월 IPCA, 실제 공시 vintage,
상장폐지수익률, bid-ask/borrow/shortability 입력 부재를 해소된 것으로
표기해서는 안 된다. 실행 성공과 exact replication은 서로 다른 판정이다.
