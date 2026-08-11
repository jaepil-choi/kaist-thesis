# Deep Learning Statistical Arbitrage: home GPU handoff

이 문서는 2026-08-10의 checkpoint handoff에서 시작해 2026-08-11 집 AMD GPU
완료 기록으로 갱신했다. 무인 실행 `run-20260811T021314Z`는 정상 종료됐고,
실행 중인 replication Python 프로세스는 없다. 체크포인트와 최종 audit는 모두
보존했다.

## 1. 현재 결론

- 논문의 residual composition, rolling PCA·FF residual, 46개 characteristic,
  IPCA ALS, OU/Fourier/CNN 정책, 비용·다기간 목적함수, numbered report,
  robustness, interpretability, appendix runner는 구현됐다.
- 논문이 요구하는 PCA K=0, 1, 3, 5, 8, 10, 15 입력 패널은 모두 생성됐다.
  K=0은 PCA5 기준 유니버스의 개별주식 초과수익률이다.
- PCA·FF의 OU 전 사양, PCA K=0/1/3/5 Fourier, FF1/3/5 Fourier, PCA5
  constant CNN, direct FFN, OU-feature FFN은 full-contract 실행이 끝났다.
- 45개 번호 산출물은 모두 `generated_from_spec`, `generated_korean_analogue`,
  `generated_korean_partial`, `generated_korean_variant` 중 하나로 분류됐고
  `implemented_waiting_full_run`은 0개다.
- 이 결과는 미국 표본 exact replication이 아니다. 한국
  **현금배당 제외 price-return variant**이며 재무는 사용자가 승인한 고정
  3개월 lag non-PIT sensitivity다.

상세 성과와 표본 계약은 `docs/execution-status.md`, 45개별 상태는
`config/output-registry.yml`을 따른다.

## 2. Git만으로 옮겨지지 않는 파일

`guijarro-ordonez-2025-replication/outputs/`는 의도적으로 gitignore된다.
현재 494개 파일, 약 0.716 GiB이며 체크포인트 162개를 포함한다. 다른 PC에서
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

저장소 루트에서 최신 커밋을 받은 뒤, AMD ROCm wheel은 반드시 저장소의 기존
`.venv`에만 설치한다. 설치 URL은
`config/rocm-windows-7.2.1-requirements.txt`에 고정되어 있다.

```powershell
uv pip install --python .venv\Scripts\python.exe -r guijarro-ordonez-2025-replication\config\rocm-windows-7.2.1-requirements.txt
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/verify_rocm_environment.py
```

bare `pip`나 시스템 Python에는 설치하지 않는다. 일반 `uv sync`는 `uv.lock`의
PyPI 해석에 따라 ROCm Torch를 교체할 수 있으므로, 검증된 GPU 환경에서는
`uv run --no-sync`를 사용한다. 검증 스크립트가 실패하면 학습을 시작하지 않는다.
특정 체크포인트의 저장 epoch까지 확인하려면 상대 glob을 추가한다.

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/verify_rocm_environment.py --skip-smoke --inspect-checkpoint 'strategies/*/checkpoints/*.pt' --output-json guijarro-ordonez-2025-replication/outputs/environment-verification.json
```

현재 구현은 `DLSA_DEVICE`를 우선하고, 미설정 시 `torch.cuda`로 노출되는 GPU가
있으면 자동으로 `cuda`, 없으면 `cpu`를 선택한다. ROCm PyTorch도 이 API를
사용한다. 여러 실험을 동시에 돌리면 VRAM과 CPU preprocessing이
경합하므로 아래 명령은 **한 번에 하나씩** 실행하는 편이 안전하다.

## 4. 완료 지점과 재실행 명령

체크포인트는 매 epoch atomic replace로 저장되고 `simulation_audit.json`은 모든
OOS subperiod가 끝난 뒤에만 생성된다. 아래 항목은 모두 완료됐으며 같은 명령을
다시 실행하면 완료 audit 또는 checkpoint를 재사용한다.

| 우선순위 | 실행 | 저장된 마지막 지점 | 재개 시점 |
|---:|---|---|---|
| 1 | PCA5 rolling CNN Sharpe | 전체 5개 subperiod 완료 | 완료; audit 생성됨 |
| 2 | PCA5 friction-aware CNN | 전체 5개 subperiod 완료 | 완료; audit 생성됨 |
| 3 | PCA5 CNN mean-variance | 전체 5개 subperiod 완료 | 완료; audit 생성됨 |
| 4 | PCA8 Fourier+FFN | 전체 5개 subperiod 완료 | 완료; audit 생성됨 |
| 5 | PCA10 Fourier+FFN | 전체 5개 subperiod 완료 | 완료; audit 생성됨 |
| 6 | PCA15 Fourier+FFN | 전체 5개 subperiod 완료 | 완료; audit 생성됨 |
| 7 | 16-model validation grid | 16개 candidate 전체 완료 | 완료; Table A.3 및 audit 생성됨 |

재개 명령은 다음과 같다.

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer_frictions --simulation-transaction-cost 0.0005 --simulation-short-holding-cost 0.0001
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer --simulation-objective meanvar
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors 8 --simulation-model fourier_ffn
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors 10 --simulation-model fourier_ffn
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors 15 --simulation-model fourier_ffn
uv run --no-sync python guijarro-ordonez-2025-replication/run.py run-model-selection
```

집 PC에서는 ROCm 7.2.1용 `torch 2.9.1+rocm7.2.1` wheel을 저장소의 `.venv`에
직접 설치했다. 일반 `uv run`은 `pyproject.toml`의 PyPI 해석 결과에 맞춰 이를
CPU 전용 Torch로 교체할 수 있으므로, 위 GPU 재개 명령은 `--no-sync`를
사용한다. 이 옵션은 가상환경을 우회하는 것이 아니라 현재 저장소 `.venv`의
검증된 패키지 집합을 그대로 사용한다.

완료 audit 기준 rolling CNN은 annual return 0.16754, annual volatility
0.04039, Sharpe 4.14767, mean daily turnover 1.21436이다. friction-aware CNN은
각각 0.06017, 0.04388, 1.37118, 0.46355이며 거래비용 5 bp와 공매도 보유비용
1 bp를 목적함수에 반영했다. mean-variance CNN은 각각 0.15557, 0.04969,
3.13086, 1.28572이다. PCA8 Fourier+FFN은 각각 0.13898, 0.03543, 3.92328,
0.84632이다. PCA10 Fourier+FFN은 각각 0.11566, 0.03276, 3.53072,
0.89213이다. PCA15 Fourier+FFN은 각각 0.05169, 0.02847, 1.81572,
0.96613이다. 모든 실행은 한국 price-return variant이며 원문 exact replication으로
분류하지 않는다.

16개 candidate가 모두 완료됐다. validation Sharpe가 가장 높은 candidate 16은
filters 16, attention heads 4, hidden-units factor 3, dropout 0.5이며 annual return
0.17320, annual volatility 0.03725, Sharpe 4.65002다. Table A.3와 최종 audit가
생성됐지만 exact IPCA validation은 240개월 이력 부족으로 계속 차단된다.

## 5. 추가 장시간 실행 결과

60일 lookback CNN은 전체 5개 subperiod를 완료했다. annual return 0.13953,
annual volatility 0.04046, Sharpe 3.44814, mean daily turnover 1.16552이며
한국 price-return variant다. 5일 holding CNN도 전체 5개 subperiod를 완료했다.
annual return 0.05150, annual volatility 0.01656, Sharpe 3.10981, mean daily
turnover 1.00355이며 같은 한국 price-return variant다.

무인 실행은 PCA5와 Korean FF5의 5개 alternative network를 모두 100 epochs로
완료했다. PCA5에서는 Network 2의 Sharpe가 4.203으로 가장 높았고, Korean
FF5에서도 Network 2가 2.674로 가장 높았다. K=1, 60개월 short-history IPCA는
7개 rolling fit이 모두 수렴해 1,330,517개 residual row를 생성했다. 이는 원문의
240개월 IPCA가 아니라 명시적인 sensitivity다.

### 무인 일괄 실행

향후 같은 실험과 산출물 검증을 다시 실행하려면 저장소 루트에서 다음 명령을
사용한다. 완료 audit와 checkpoint는 중복 학습을 피하는 데 재사용된다.

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/run_remaining_replication.py
```

orchestrator는 같은 5일 holding 프로세스가 이미 실행 중이면 종료를 기다리고,
완료 audit를 확인한 뒤 중복 학습 없이 다음 단계로 넘어간다. 각 neural-network
학습은 기존 atomic checkpoint를 그대로 재사용한다. Alternative-network 단계는
PCA5와 Korean FF5의 2개 residual panel에 5개 network를 적용한다.

각 실행의 증거는
`outputs/orchestration/run-YYYYMMDDTHHMMSSZ/` 아래 `terminal.log`,
`events.jsonl`, `manifest.json`, `environment.json`,
`source_fingerprints.json`, `audit_index.json`, `artifact_inventory.json`,
`summary.md`로 남는다. IPCA는 `IPCA ALS did not converge`만 예상된 방법론적
실패로 분류하며, 그 밖의 오류는 manifest에 실패로 남기되 가능한 후속 빌드와
검증은 계속 실행한다. 모든 결과는 한국 price-return variant이며 이 일괄 실행도
미국 표본 exact replication 또는 240개월 IPCA 제약을 해소하지 않는다.

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer --simulation-lookback-days 60
uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer --simulation-holding-days 5
uv run --no-sync python guijarro-ordonez-2025-replication/run.py run-alternative-networks --alternative-max-models 5 --simulation-epochs 100
uv run --no-sync python guijarro-ordonez-2025-replication/run.py estimate-ipca --ipca-factors 1 --ipca-initial-months 60 --ipca-window-months 60 --allow-short-history-ipca
```

마지막 IPCA 명령은 exact replication이 아니라 short-history sensitivity다.
K=5, 60개월 실행은 공개 코드의 1,500회/1e-3 convergence gate를 통과하지
못했으며 residual 파일을 만들지 않았다. K=1은 이번 실행에서 수렴했지만 exact
IPCA는 240개월 이력이 없어 계속 차단된다.

## 6. 완료된 산출물 재생성 절차

무인 실행은 아래 명령을 모두 성공적으로 수행했다. 필요할 때 개별 산출물을
재생성하는 명령으로 보존한다.

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/run.py report-strategies
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-robustness
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-interpretability
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-appendix
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-appendix-signals
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-risk-premium
uv run --no-sync python guijarro-ordonez-2025-replication/run.py status
```

`config/output-registry.yml`과 `docs/execution-status.md`는 최종 audit에 맞춰
갱신했다. 확인한 연결은 다음과 같다.

- primary rolling CNN: Figures 5, 8–11, Appendix Figures A.5/A.7,
  Tables 1/2/A.8
- five-day holding: Figure 12의 multi-day-objective 계열; builder가 one-day 계열과
  한 그림으로 결합하며 standalone 5-day audit와 cross-horizon B=5 통계는 구분
- 60-day lookback: Tables 5/6
- friction-aware CNN: Figures 6/7, Table 9, Appendix Table A.10
- CNN mean-variance: Tables 3/4의 CNN 행
- validation grid: Appendix Table A.3
- alternative networks: Appendix Table A.5

## 7. 최종 검증과 커밋

```powershell
uv run --no-sync pytest guijarro-ordonez-2025-replication/tests -p no:cacheprovider
uv run --no-sync ruff check guijarro-ordonez-2025-replication
git status --short
```

최종 무인 실행에서 67개 테스트와 Ruff가 모두 통과했다. 전체 완료 후에도
미국 CRSP/Compustat, total return, 240개월 IPCA, 실제 공시 vintage,
상장폐지수익률, bid-ask/borrow/shortability 입력 부재를 해소된 것으로
표기해서는 안 된다. 실행 성공과 exact replication은 서로 다른 판정이다.
