# Full-paper execution status

This document records the full-contract Korean run of Guijarro-Ordonez,
Pelger, and Zanotti (2025). The machine-readable source of truth for the 45
numbered outputs is `config/output-registry.yml`; every numerical result below
is recoverable from an ignored `outputs/**/simulation_audit.json` file.

## Classification boundary

No output in this project is an exact replication of the paper's U.S. result.
The executable Korean branch uses cash-dividend-excluding adjusted price
returns, a smaller KOSPI/KOSDAQ universe, and a 2020-01-02--2026-07-20
residual sample. Accounting characteristics use the explicitly authorized
fixed three-month lag but not filing-vintage point-in-time data. These runs are
therefore Korean price-return variants.

The exact U.S. branch remains data-blocked by CRSP/Compustat inputs. The exact
Korean IPCA branch remains history-blocked because the paper requires a
240-month rolling window while the local monthly panel has only 139 months.
The attempted K=5, 60-month short-history sensitivity did not meet the public
code's 1,500-iteration, 1e-3 convergence gate and consequently produced no
residual file.

## Executed sample contract

- Residual dates: 2020-01-02--2026-07-20, 1,606 trading days.
- Residual rows: 275,711 for every PCA K branch.
- Daily cross-section: 127--185 selected stocks.
- Policy training: first 1,000 days; 125-day rolling retraining and test
  subperiods; seed 0; 100 epochs for neural policies.
- Policy OOS dates: 2024-01-19--2026-07-20, 606 trading days.
- PCA factor counts: K=0, 1, 3, 5, 8, 10, and 15. K=0 is the observed
  stock-excess-return panel on the PCA5 reference universe.

## Completed benchmark results

Annual return and volatility are decimal annualized values. These are
unadjusted research backtests and not deployable performance estimates.

| Factor model | Policy | Annual return | Annual volatility | Sharpe |
|---|---:|---:|---:|---:|
| Stock returns, K=0 | OU threshold | 0.060 | 0.170 | 0.352 |
| Stock returns, K=0 | Fourier+FFN | -0.171 | 0.170 | -1.006 |
| PCA1 | OU threshold | 0.117 | 0.081 | 1.435 |
| PCA1 | Fourier+FFN | 0.134 | 0.051 | 2.618 |
| PCA3 | OU threshold | 0.071 | 0.062 | 1.138 |
| PCA3 | Fourier+FFN | 0.129 | 0.043 | 2.960 |
| PCA5 | OU threshold | 0.091 | 0.062 | 1.471 |
| PCA5 | Fourier+FFN | 0.134 | 0.041 | 3.266 |
| PCA5 | direct FFN | 0.084 | 0.038 | 2.187 |
| PCA5 | OU-feature FFN | 0.079 | 0.042 | 1.877 |
| PCA5 | Fourier+FFN, mean-variance | -0.160 | 0.197 | -0.812 |
| PCA5 | CNN+Transformer, constant | 0.162 | 0.039 | 4.151 |
| PCA5 | CNN+Transformer, rolling Sharpe | 0.168 | 0.040 | 4.148 |
| PCA5 | CNN+Transformer, rolling mean-variance | 0.156 | 0.050 | 3.131 |
| PCA5 | CNN+Transformer, friction-aware | 0.060 | 0.044 | 1.371 |
| PCA8 | OU threshold | 0.089 | 0.049 | 1.811 |
| PCA8 | Fourier+FFN | 0.139 | 0.035 | 3.923 |
| PCA10 | OU threshold | 0.075 | 0.044 | 1.708 |
| PCA10 | Fourier+FFN | 0.116 | 0.033 | 3.531 |
| PCA15 | OU threshold | 0.046 | 0.034 | 1.338 |
| Korean FF1 | OU threshold | 0.028 | 0.100 | 0.276 |
| Korean FF3 | OU threshold | 0.046 | 0.063 | 0.732 |
| Korean FF5 | OU threshold | 0.024 | 0.050 | 0.472 |
| Korean FF1 | Fourier+FFN | 0.118 | 0.081 | 1.452 |
| Korean FF3 | Fourier+FFN | 0.084 | 0.048 | 1.759 |
| Korean FF5 | Fourier+FFN | 0.064 | 0.044 | 1.454 |

## Checkpointed and outstanding executable runs

Company-PC execution was intentionally stopped on 2026-08-10 because the
machine has no GPU. The completed part of each active run is checkpointed and
resumable; exact epochs and home-GPU commands are in
`docs/home-gpu-handoff.md`.

- Completed on the home AMD GPU: rolling PCA5 CNN+Transformer Sharpe,
  mean-variance, and friction-aware objectives. Mean-variance produced annual
  return 0.156, volatility 0.050, Sharpe 3.131, and mean daily turnover 1.286.
  The friction-aware objective uses 5 bp transaction cost and 1 bp
  short-holding cost; mean daily turnover fell from 1.214 to 0.464 while the
  Sharpe ratio fell from 4.148 to 1.371.
- Completed on the home AMD GPU after the PCA5 objectives: PCA8 Fourier+FFN,
  with annual return 0.139, volatility 0.035, Sharpe 3.923, and mean daily
  turnover 0.846; and PCA10 Fourier+FFN, with annual return 0.116, volatility
  0.033, Sharpe 3.531, and mean daily turnover 0.892.
- Checkpointed: PCA15 Fourier+FFN and candidate 2 of the 16-candidate validation
  grid.
- Not started: 60-day lookback, five-day holding, five alternative CNN
  specifications, and K=1 short-history IPCA convergence sensitivity.

After each run completes, `report-strategies`, `build-robustness`, and
`build-appendix` regenerate the numbered CSV/PNG outputs. Empty exact groups
are retained as explicit blockers rather than filled with a proxy.
