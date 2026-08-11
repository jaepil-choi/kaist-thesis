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
residual file. A separate K=1, 60-month sensitivity converged in all seven
annual fits and generated 1,330,517 daily residual rows, but it does not remove
the 240-month exact-replication blocker.

## Final unattended run

Run `run-20260811T021314Z` completed on the AMD GPU on 2026-08-11. Eleven
tasks succeeded and the five-day-holding task was skipped only because its
completed audit already existed; there were no failed tasks. The run completed
all ten 100-epoch alternative-network specifications, the K=1 short-history
IPCA sensitivity, every downstream output builder, project status, 67 tests,
and Ruff. The captured execution commit is `0ee7b84`; the subsequent
`a34aa72` commit changed only the five-day run documentation. Timestamped logs,
environment, source hashes, parsed audits, and artifact hashes are preserved
under `outputs/orchestration/run-20260811T021314Z/`.

The output registry now has zero `implemented_waiting_full_run` entries. All
45 numbered outputs exist as spec-derived, Korean analogue, Korean partial, or
Korean variant artifacts. This is an executable-output completion statement,
not an exact U.S. replication claim.

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
| PCA15 | Fourier+FFN | 0.052 | 0.028 | 1.816 |
| Korean FF1 | OU threshold | 0.028 | 0.100 | 0.276 |
| Korean FF3 | OU threshold | 0.046 | 0.063 | 0.732 |
| Korean FF5 | OU threshold | 0.024 | 0.050 | 0.472 |
| Korean FF1 | Fourier+FFN | 0.118 | 0.081 | 1.452 |
| Korean FF3 | Fourier+FFN | 0.084 | 0.048 | 1.759 |
| Korean FF5 | Fourier+FFN | 0.064 | 0.044 | 1.454 |

## Completed GPU runs and reviewed results

- Completed on the home AMD GPU: rolling PCA5 CNN+Transformer Sharpe,
  mean-variance, and friction-aware objectives. Mean-variance produced annual
  return 0.156, volatility 0.050, Sharpe 3.131, and mean daily turnover 1.286.
  The friction-aware objective uses 5 bp transaction cost and 1 bp
  short-holding cost; mean daily turnover fell from 1.214 to 0.464 while the
  Sharpe ratio fell from 4.148 to 1.371.
- Completed on the home AMD GPU after the PCA5 objectives: PCA8 Fourier+FFN,
  with annual return 0.139, volatility 0.035, Sharpe 3.923, and mean daily
  turnover 0.846; and PCA10 Fourier+FFN, with annual return 0.116, volatility
  0.033, Sharpe 3.531, and mean daily turnover 0.892. PCA15 Fourier+FFN then
  produced annual return 0.052, volatility 0.028, Sharpe 1.816, and mean daily
  turnover 0.966.
- Completed on the home AMD GPU: all 16 candidates in the PCA5 validation grid.
  Candidate 16 (`filters=16`, `attention_heads=4`, `hidden_units_factor=3`,
  `dropout=0.5`) had the highest validation Sharpe, 4.650, with annual return
  0.173 and annual volatility 0.037. Appendix Table A.3 and the grid audit were
  generated. Exact IPCA validation remains blocked by the 240-month history
  requirement.
- Completed on the home AMD GPU: the PCA5 CNN+Transformer 60-day-lookback
  robustness run, with annual return 0.140, volatility 0.040, Sharpe 3.448,
  mean daily turnover 1.166, and mean short proportion 0.501. Its Korean FF5
  annual alpha is 0.146 with t-statistic 5.540. The matching 30-day run had
  Sharpe 4.148; Tables 5/6 were regenerated and reviewed.
- Completed on the home AMD GPU: the five-day-holding robustness run, with
  annual return 0.052, volatility 0.017, Sharpe 3.110, mean daily turnover
  1.004, and mean short proportion 0.507. Figure 12 was regenerated from the
  supplied multi-day-trained weights. Its separate cross-horizon transform at
  B=5 has annual return -0.006, volatility 0.025, and Sharpe -0.235; that
  mechanical Figure 12 statistic is not the standalone five-day simulation
  audit and the two definitions must not be interchanged.
- Figures 9/10 show that retaining only the largest 1% of asset weights raises
  volatility to 0.504 and produces a negative Sharpe, while the full-weight
  portfolio has Sharpe 2.158 in the robustness transformation. Figure 11's
  simple reversal benchmarks are negative at every tested lag. These results
  do not support a claim that greater sparsity or naive reversal improves the
  Korean strategy.
- All five alternative networks completed on both PCA5 and Korean FF5
  residuals. PCA5 Network 2 has the highest Sharpe, 4.203; Korean FF5 Network
  2 has the highest Sharpe, 2.674. Appendix Table A.5 contains all ten rows and
  satisfies the 100-epoch network execution contract.
- K=1 short-history IPCA converged in four or five ALS iterations in each of
  seven annual fits. It uses 60 months rather than the paper's 240 months and
  is classified only as a Korean short-history sensitivity.

Empty exact groups remain explicit blockers rather than being filled with a
proxy. The remaining work is data acquisition for total returns, filing-vintage
accounting data, delisting returns, and realized trading/shorting costs, not an
unexecuted local model run.
