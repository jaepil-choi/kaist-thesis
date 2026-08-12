# Guijarro-Ordonez 한국 replication: 남은 GPU 실행 handoff

기준일은 2026-08-12, 기준 tracked commit은 `7bdd38f`다. 이 문서의 목적은
이미 완료된 실험을 반복하지 않고, 현재 한국 price-return variant에서 실행 가능한
미완료 실험만 원격 GPU에서 수행하는 것이다.

## 1. 핵심 판정

현재 `45/45`는 원 논문 번호에 대응하는 Figure/Table 파일이 존재한다는 뜻이지,
표 안의 모든 실험 조합이 계산됐다는 뜻이 아니다. `run.py status`도 YAML registry의
상태 문자열만 세므로 GPU 실험 coverage를 판정하는 명령으로 사용하면 안 된다.

현재 실행 가능한데 아직 돌리지 않은 장시간 학습은 **74개 실행 단위**다.

| 구분 | 남은 실행 수 | 직접 채우는 산출물 |
|---|---:|---|
| 기본 CNN Sharpe | 9 | Main Tables 1–2, Figure 5, Appendix Table A.VIII |
| Mean-variance CNN/Fourier | 18 | Main Tables 3–4 |
| CNN 60일 lookback | 9 | Main Tables 5–6 |
| CNN 4년 constant | 9 | Main Tables 7–8 |
| Direct FFN / OU-feature FFN | 18 | Appendix Table A.IX |
| Friction-aware CNN | 11 | Appendix Table A.X |
| **합계** | **74** | 파생 alpha·상관·그림은 builder 재실행으로 생성 |

이 수는 동일한 K=0 주식수익률을 factor family별로 중복 실행하지 않고 PCA0 한 번으로
공유한 값이다. 각 rolling 실행은 1,000일 학습창과 125일 stride의 OOS subperiod
5개를 각각 100 epochs로 학습한다. constant 실행은 최초 subperiod 하나만 학습한다.

## 2. 절대 재실행하지 않을 완료 작업

아래 작업은 tracked 실행상태와 2026-08-12 `paper-assets/` snapshot에 반영됐다.
원격지에 원천 audit가 없다는 이유만으로 다시 학습하지 않는다. 먼저 기존 GPU 또는
보관본에서 `outputs/`를 복원한다.

- PCA K=1/3/5/8/10/15 residual 및 loading 생성과 PCA5 universe를 재사용하는
  K=0 identity-return 입력 branch
- Korean FF1/FF3/FF5 residual 및 factor leg 생성
- PCA·FF의 OU+Threshold 전체 실행
- PCA K=0/1/3/5/8/10/15 Fourier+FFN Sharpe 전체 실행
- FF1/FF3/FF5 Fourier+FFN Sharpe 전체 실행
- PCA5 CNN+Transformer rolling Sharpe
- PCA5 CNN+Transformer mean-variance
- PCA5 friction-aware CNN Sharpe
- PCA5 CNN+Transformer 60일 lookback
- PCA5 CNN+Transformer 4년 constant
- PCA5 CNN+Transformer 5일 holding
- PCA5 Direct FFN 및 OU-feature FFN
- PCA5 Fourier+FFN mean-variance
- PCA5 16-candidate validation grid
- PCA5·FF5의 5개 alternative network, 총 10개 실행
- K=1, 60개월 short-history IPCA sensitivity
- 기존 robustness, interpretability, appendix, risk-premium 및 report builder 실행

특히 `scripts/run_remaining_replication.py`는 이름과 달리 아래 74개 grid를 실행하지
않는다. 기존 5일 holding, alternative networks, K=1 short-history IPCA와 builder를
다시 확인하는 runner이므로 이번 GPU batch의 진입점으로 사용하지 않는다.

## 3. Git 밖에서 반드시 전달할 파일

`guijarro-ordonez-2025-replication/outputs/` 전체는 gitignore된다. Git clone/pull만
받은 원격지는 residual, loading, checkpoint, audit가 없으므로 중복 실행 방지와
report 재생성을 모두 할 수 없다.

원격 GPU로 다음 디렉터리를 경로 구조 그대로 전달한다.

- `guijarro-ordonez-2025-replication/outputs/`
- `data/kaist_pilot/canonical/common/korean_equity/`
- `data/kaist_pilot/canonical/guijarro_2025/`
- `data/kimchi-factor/`

현재 이 PC의 ignored output tree는 완전한 원본이 아니다. tracked manifest가 가리키는
`outputs/orchestration/run-20260811T021314Z/manifest.json`과 일부 완료 실행의 최종
`simulation_audit.json`이 현재 PC에는 없다. 가장 완전한 원본은 해당 무인 실행을
수행한 GPU PC 또는 별도 archive여야 한다. 다음 파일들이 복원되기 전에는 새 결과와
기존 결과를 합친 최종 report를 만들지 않는다.

- `outputs/orchestration/run-20260811T021314Z/`
- 완료된 PCA5 rolling/mean-variance/friction-aware CNN의 `simulation_audit.json`,
  `daily_performance.csv`, `daily_asset_weights.parquet`
- 완료된 PCA8/10/15 Fourier+FFN의 같은 최종 파일
- validation grid와 alternative-network의 전체 audit 및 결과

checkpoint 일부만 있는 디렉터리를 완료로 간주하지 않는다. 반대로 tracked 문서상
완료된 위 작업은 원천 파일이 누락됐더라도 이번 pending 목록에 추가하지 않는다.

## 4. 원격 GPU preflight

저장소 루트에서 다음 순서로 확인한다.

```powershell
git pull --ff-only origin master
uv pip install --python .venv\Scripts\python.exe -r guijarro-ordonez-2025-replication\config\rocm-windows-7.2.1-requirements.txt
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/verify_rocm_environment.py
```

NVIDIA 또는 Linux 환경이면 해당 플랫폼용 PyTorch가 설치돼 있어야 하며, 최종 gate는
`torch.cuda.is_available() == True`와 실제 tensor smoke test 성공이다. `DLSA_DEVICE`
를 설정한다면 `cuda`만 사용한다. GPU preflight가 실패하면 CPU fallback으로 장시간
학습을 시작하지 않는다.

전달된 입력도 확인한다. K=0은 별도 PCA0 residual 파일이 아니라 PCA5 panel의
universe와 observed-return mask를 재사용한다.

```powershell
$required = @('guijarro-ordonez-2025-replication/outputs/kimchi-exact/daily_factor_returns.csv')
foreach ($k in 1, 3, 5, 8, 10, 15) {
  $required += "guijarro-ordonez-2025-replication/outputs/pca/daily_residuals_k${k}_20200102_c252_l60.parquet"
  $required += "guijarro-ordonez-2025-replication/outputs/pca/daily_low_rank_loadings_k${k}_20200102_c252_l60.parquet"
}
foreach ($k in 1, 3, 5) {
  $required += "guijarro-ordonez-2025-replication/outputs/fama-french/daily_residuals_ff${k}_20200102_l60.parquet"
  $required += "guijarro-ordonez-2025-replication/outputs/fama-french/daily_factor_legs_ff${k}_20200102_l60.parquet"
}
$missing = $required | Where-Object { -not (Test-Path -LiteralPath $_) }
if ($missing) { throw "Missing transferred inputs: $($missing -join ', ')" }
```

여러 학습을 병렬로 돌리지 않는다. PyTorch GPU 연산 외의 panel 전처리도 CPU와 RAM을
크게 사용하므로 아래 job family를 **한 번에 하나씩, 표의 우선순위 순서대로** 실행한다.

## 5. 공통 실행 규칙

모든 명령은 저장소 루트에서 실행한다.

- `uv run --no-sync python ...`만 사용한다.
- 기본 계약은 seed 0, 100 epochs, 1,000일 training, 125일 retraining, 1일 holding이다.
- 실행 디렉터리가 있어도 `simulation_audit.json`이 없으면 완료가 아니다. checkpoint에서
  재개한다.
- `simulation_audit.json`이 있으면 `epochs=100`, factor model, objective, lookback,
  rolling/constant, 비용, holding과 OOS 날짜를 검사한 후에만 skip한다.
- 한 명령이 nonzero exit로 끝나면 다음 job family로 넘어가지 않는다.
- 실행 로그와 환경·source hash·artifact hash를 `outputs/orchestration/` 아래 새 run ID로
  보존한다.

GPU batch를 시작하기 전에 기존 `orchestration.py`를 확장하거나 별도 pending runner를
추가해 아래 74개 matrix를 machine-readable task로 등록한다. runner는 유효한 완료
audit만 skip하고, job을 순차 실행하며, 각 종료 상태와 source/environment/artifact
hash를 새 orchestration manifest에 기록해야 한다. 아래 PowerShell block은 정확한
실험 조합을 명시한 reference이며, manifest 없이 ad-hoc 실행한 상태를 최종 완료로
간주하지 않는다.

아래 표의 공통 factor grid는 다음과 같다.

- PCA: `0, 1, 3, 8, 10, 15` — PCA5는 해당 기본 사양이 이미 완료됐으므로 제외
- FF: `1, 3, 5` — FF8은 data-blocked이므로 제외

## 6. P0 — 기본 CNN Sharpe 9개

가장 먼저 실행한다. Main Tables 1–2의 중심 결과와 Appendix Table A.VIII의 전략
상관행렬을 직접 해소한다.

```powershell
$pca = 0, 1, 3, 8, 10, 15
foreach ($k in $pca) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors $k --simulation-model cnn_transformer --simulation-objective sharpe --simulation-lookback-days 30 --simulation-epochs 100
  if ($LASTEXITCODE -ne 0) { throw "P0 PCA$k failed" }
}

$ff = 1, 3, 5
foreach ($k in $ff) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-fama-french --ff-factors $k --simulation-model cnn_transformer --simulation-objective sharpe --simulation-lookback-days 30 --simulation-epochs 100
  if ($LASTEXITCODE -ne 0) { throw "P0 FF$k failed" }
}
```

완료 후 benchmark CNN은 PCA0/1/3/5/8/10/15 및 FF1/3/5에 모두 존재해야 한다.

## 7. P1 — Mean-variance 18개

PCA5의 CNN과 Fourier는 이미 완료됐다. 나머지 grid에서 두 정책을 실행한다.

```powershell
$models = 'cnn_transformer', 'fourier_ffn'
$pca = 0, 1, 3, 8, 10, 15
foreach ($model in $models) {
  foreach ($k in $pca) {
    uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors $k --simulation-model $model --simulation-objective meanvar --simulation-lookback-days 30 --simulation-epochs 100
    if ($LASTEXITCODE -ne 0) { throw "P1 $model PCA$k failed" }
  }
}

$ff = 1, 3, 5
foreach ($model in $models) {
  foreach ($k in $ff) {
    uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-fama-french --ff-factors $k --simulation-model $model --simulation-objective meanvar --simulation-lookback-days 30 --simulation-epochs 100
    if ($LASTEXITCODE -ne 0) { throw "P1 $model FF$k failed" }
  }
}
```

## 8. P2 — CNN 60일 lookback 9개

PCA5 60일 실행은 완료됐다. 나머지 grid만 실행한다.

```powershell
$pca = 0, 1, 3, 8, 10, 15
foreach ($k in $pca) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors $k --simulation-model cnn_transformer --simulation-objective sharpe --simulation-lookback-days 60 --simulation-epochs 100
  if ($LASTEXITCODE -ne 0) { throw "P2 PCA$k failed" }
}

$ff = 1, 3, 5
foreach ($k in $ff) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-fama-french --ff-factors $k --simulation-model cnn_transformer --simulation-objective sharpe --simulation-lookback-days 60 --simulation-epochs 100
  if ($LASTEXITCODE -ne 0) { throw "P2 FF$k failed" }
}
```

## 9. P3 — CNN 4년 constant 9개

`--simulation-constant-model`은 최초 1,000일 학습 후 재학습하지 않는 4년 사양이다.
PCA5는 완료됐으므로 제외한다.

```powershell
$pca = 0, 1, 3, 8, 10, 15
foreach ($k in $pca) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors $k --simulation-model cnn_transformer --simulation-objective sharpe --simulation-lookback-days 30 --simulation-epochs 100 --simulation-constant-model
  if ($LASTEXITCODE -ne 0) { throw "P3 PCA$k failed" }
}

$ff = 1, 3, 5
foreach ($k in $ff) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-fama-french --ff-factors $k --simulation-model cnn_transformer --simulation-objective sharpe --simulation-lookback-days 30 --simulation-epochs 100 --simulation-constant-model
  if ($LASTEXITCODE -ne 0) { throw "P3 FF$k failed" }
}
```

원 논문의 8년 constant 사양은 현재 2020–2026 residual 표본으로 실행하지 않는다.

## 10. P4 — 시계열 신호 ablation 18개

PCA5 Direct FFN과 OU-feature FFN은 완료됐다. 나머지 grid에서 두 모델을 실행한다.
CLI의 `ou_ffn`이 문서 Table A.IX의 OU+FFN에 대응한다.

```powershell
$models = 'direct_ffn', 'ou_ffn'
$pca = 0, 1, 3, 8, 10, 15
foreach ($model in $models) {
  foreach ($k in $pca) {
    uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors $k --simulation-model $model --simulation-objective sharpe --simulation-lookback-days 30 --simulation-epochs 100
    if ($LASTEXITCODE -ne 0) { throw "P4 $model PCA$k failed" }
  }
}

$ff = 1, 3, 5
foreach ($model in $models) {
  foreach ($k in $ff) {
    uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-fama-french --ff-factors $k --simulation-model $model --simulation-objective sharpe --simulation-lookback-days 30 --simulation-epochs 100
    if ($LASTEXITCODE -ne 0) { throw "P4 $model FF$k failed" }
  }
}
```

## 11. P5 — PCA friction-aware CNN 11개

원문 Appendix Table A.X의 PCA row는 K=0/1/3/5/10/15이며 K=8은 없다. PCA5
Sharpe 사양은 완료됐으므로 Sharpe 5개와 mean-variance 6개만 실행한다.

```powershell
$pcaSharpe = 0, 1, 3, 10, 15
foreach ($k in $pcaSharpe) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors $k --simulation-model cnn_transformer_frictions --simulation-objective sharpe --simulation-lookback-days 30 --simulation-epochs 100 --simulation-transaction-cost 0.0005 --simulation-short-holding-cost 0.0001
  if ($LASTEXITCODE -ne 0) { throw "P5 Sharpe PCA$k failed" }
}

$pcaMeanVariance = 0, 1, 3, 5, 10, 15
foreach ($k in $pcaMeanVariance) {
  uv run --no-sync python guijarro-ordonez-2025-replication/run.py simulate-pca --pca-factors $k --simulation-model cnn_transformer_frictions --simulation-objective meanvar --simulation-lookback-days 30 --simulation-epochs 100 --simulation-transaction-cost 0.0005 --simulation-short-holding-cost 0.0001
  if ($LASTEXITCODE -ne 0) { throw "P5 Mean-variance PCA$k failed" }
}
```

이 비용은 원문의 고정 5 bp transaction cost와 일별 1 bp short holding cost
sensitivity다. 실제 한국 bid-ask, borrow fee 또는 market impact 검증으로 표현하지 않는다.

## 12. GPU 실행 후 필요한 코드·builder 작업

74개 학습이 끝나도 Markdown 표가 자동으로 완성되는 것은 아니다. 다음 순서로
코드와 산출물을 정리한다.

1. **실험 matrix 추가**
   - factor family, K, model, objective, lookback, rolling/constant, holding, cost를
     식별자로 갖는 machine-readable matrix를 추가한다.
   - 상태는 `complete`, `unrun`, `data_blocked`, `not_applicable`로 분리한다.
   - `complete`는 audit 경로와 SHA-256을 가져야 한다.
2. **`run.py status` 강화**
   - 45개 번호 파일 개수와 실험 matrix coverage를 별도로 출력한다.
   - YAML 상태 문자열만 세어 scientific completion처럼 보이지 않게 한다.
3. **기존 report builder 재실행**
   - `report-strategies`는 복원된 기존 audit와 신규 audit를 모두 읽어 Main Tables
     1–8, Figure 5–8을 다시 만든다.
   - `build-appendix`는 신규 benchmark CNN, ablation, friction audit를 읽어
     Tables A.VIII–A.X를 다시 만든다.
   - generic friction CSV에 PCA 결과가 생성되더라도 원문 Main Table 9의 IPCA 칸을
     PCA 결과로 대체하지 않는다. PCA friction 결과는 Appendix Table A.X에만 배치한다.
4. **Appendix Tables A.VI–A.VII builder 확장**
   - 현재 구현은 PCA5 unconditional residual만 계산하도록 hard-coded되어 있다.
   - 기존 FF1/3/5와 PCA0/1/3/8/10/15 residual에도 같은 unit-gross unconditional
     계산과 alpha regression을 적용한다.
   - 이 단계는 추가 neural training이 아니라 CPU 분석 작업이다.
5. **snapshot과 논문 초안 동기화**
   - 새 CSV/PNG를 `paper-assets/`로 export하고 manifest를 새로 만든다.
   - `guijarro-korea-replication.md`의 `—ᵁ`만 실제 audit가 있는 cell에 한해 숫자로
     교체한다. `—ᴰ`와 `—ᴺ`는 유지한다.

Builder 명령은 다음과 같다.

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/run.py report-strategies
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-robustness
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-interpretability
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-appendix
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-appendix-signals
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-risk-premium
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/export_thesis_assets.py
```

## 13. 현재 데이터로 실행 금지인 항목

다음 항목은 GPU가 빨라도 해결되지 않는다. 입력 gate가 해소되기 전에는 proxy로
채우거나 실패할 것을 알면서 batch에 넣지 않는다.

- 미국 CRSP/Compustat exact replication 전체
- 240개월 rolling history가 필요한 exact IPCA K=1/3/5/8/10/15
- 비수렴한 K=5 60개월 short-history IPCA 반복 실행
- exact STREV·LTREV가 없는 FF8
- FF10·FF15 — 원 사양상 비해당
- 2020–2026 residual로 수행하는 8년 constant training
- 종목·시점별 bid-ask, shortability, borrow fee가 필요한 실제 비용 검증
- 현금배당 포함 total return, 상장폐지수익률, filing-vintage PIT 재무가 필요한 exact
  한국 replication 주장
- 원문 Table 9의 IPCA friction 결과

K=1 60개월 short-history IPCA는 이미 실행됐지만 exact IPCA가 아니므로 다시 돌리지
않고 sensitivity로만 보존한다.

## 14. 최종 완료 gate

다음 조건을 모두 충족해야 이번 원격 GPU 작업을 완료로 판정한다.

- pending 74개 각각에 최종 `simulation_audit.json`, `daily_performance.csv`,
  `daily_asset_weights.parquet`가 존재한다.
- 각 audit가 100 epochs 및 요청한 factor/model/objective/lookback/cost 계약과 일치한다.
- 기존 완료 audit와 신규 audit가 하나의 `outputs/` tree에 함께 보존된다.
- Main Tables 1–8과 Appendix Tables A.VI–A.X의 실행 가능한 `—ᵁ`가 모두 제거된다.
- IPCA·FF8·8년 constant 등 `—ᴰ`, FF10/15의 `—ᴺ`는 근거와 함께 유지된다.
- 새 experiment matrix는 numbered artifact coverage와 scientific grid coverage를
  별도로 보고한다.
- tracked `paper-assets/manifest.json`의 모든 exported file hash가 일치한다.
- 테스트와 lint가 통과한다.

```powershell
uv run --no-sync pytest guijarro-ordonez-2025-replication/tests -p no:cacheprovider
uv run --no-sync ruff check guijarro-ordonez-2025-replication
git status --short
```

Windows에서 pytest temp cleanup이 실패하면 저장소 밖의 고유한 ASCII basetemp를
사용한다. 기존 `.pytest_cache`나 lock을 임의로 삭제하지 않는다.

최종 handoff에는 다음을 함께 남긴다.

- 실행 commit SHA와 GPU/PyTorch 환경
- 성공·실패·skip된 정확한 job matrix
- 각 audit 및 artifact의 SHA-256
- 표본 날짜, 종목 수, OOS 날짜와 subperiod 수
- 변경된 tracked 문서·CSV·PNG 목록
- 여전히 남은 data blocker

모든 결과의 분류는 **한국 현금배당 제외 price-return variant**다. 위 74개를 모두
실행해도 미국 exact replication 또는 240개월 IPCA replication이 되는 것은 아니다.
