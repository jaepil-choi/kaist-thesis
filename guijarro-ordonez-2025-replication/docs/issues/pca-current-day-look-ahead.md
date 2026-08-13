# PCA current-day look-ahead in the public-code replication

- **Status:** Open
- **Severity:** Critical for research validity
- **Affected scope:** PCA branches with `K > 0` and every downstream strategy,
  table, figure, checkpoint, and robustness result trained from those residuals
- **Not the cause:** The trading-policy lookback window itself
- **Identified:** 2026-08-13

## Summary

The local PCA implementation faithfully reproduces the timing used in the
authors' public code, but that timing conflicts with the point-in-time contract
stated in the paper. Both implementations include the return on residual date
`t` when estimating the PCA correlation matrix and the loading regression used
to construct the same-day residual composition matrix.

The policy signal is backward-looking: the day-`t` allocation model consumes
only residual observations from `t-L` through `t-1`. Nevertheless, the raw
residual allocation is converted to same-day asset weights with a composition
matrix that depends on `R_t`. The resulting backtest therefore has a separate
look-ahead path:

```text
R_t -> same-day PCA/loading estimates -> Phi_t -> day-t asset weights -> day-t return
```

This is not evidence that the local implementation mistranscribed the public
code. It is evidence that the public code and the paper's stated methodology
are inconsistent. The existing local PCA `K > 0` results are **public-code
faithful but non-point-in-time** and cannot be treated as executable or
paper-method-faithful out-of-sample performance.

## Expected paper contract

Section 3.2 of the paper says that the residual composition matrix
`Phi_{t-1}` depends only on information available through `t-1`, so there is no
look-ahead bias. For PCA, it further says that at `t-1` the previous 252 days
are used for the correlation matrix, the previous 60 days are used for the
loading regression, and the residual for day `t` is then computed out of
sample.

The required timing is therefore:

```text
estimate Phi_{t-1} from R_{<=t-1}
observe R_t
compute epsilon_t = Phi_{t-1} R_t
form the day-t policy signal from epsilon_{t-L}, ..., epsilon_{t-1}
```

Paper evidence:

- `../../../docs/markdown/2025 Deep Learning Statistical Arbitrage - Guijarro-Ordonez et al. (MS).md:2001-2004`
- `../../../docs/markdown/2025 Deep Learning Statistical Arbitrage - Guijarro-Ordonez et al. (MS).md:2050-2058`

## Observed behavior in the authors' public code

The public PCA implementation correctly checks eligibility using returns prior
to `t`, but its estimation slice ends at `t + 1` and therefore includes `R_t`:

```python
rets_cov_window = rets_daily[
    first_oos_daily_idx + t - size_covariance_window + 1:
    first_oos_daily_idx + t + 1,
    idxs_selected,
]
```

It then:

1. estimates the correlation eigenvectors from that current-day-inclusive
   window;
2. estimates the return loadings from the last 60 rows of the same window,
   also including `R_t`;
3. computes the same-day residual from `R_t`;
4. saves the resulting composition matrix for the same date.

Relevant source:

- `../../../Deep_Learning_Statistical_Arbitrage_Code/factor_models/pca.py:173-180`
- `../../../Deep_Learning_Statistical_Arbitrage_Code/factor_models/pca.py:187-207`
- `../../../Deep_Learning_Statistical_Arbitrage_Code/simulation.py:738-764`

The public simulation constructs the signal from `[t-L, t)`, but passes the
same-date composition matrix into the asset-weight transform and evaluates it
against the same-date residual return. A backward-looking neural-network input
does not remove the composition-matrix look-ahead.

## Observed behavior in this replication

The local implementation explicitly preserved the public-code behavior:

- `src/guijarro_ordonez_replication/pca.py:44-48` states that both estimation
  windows include the current return to match the authors' implementation.
- `src/guijarro_ordonez_replication/pca.py:201-207` slices through
  `day_idx + 1`.
- `src/guijarro_ordonez_replication/pca.py:75-82` estimates loadings and the
  current residual from the current-day-inclusive window.
- `src/guijarro_ordonez_replication/pca.py:276` records
  `current_day_in_covariance_and_loading_windows: true` in the audit.
- `tests/test_pca.py:66-67` fixes that behavior as the expected test result.

The trading implementation separately confirms that the policy signal is
properly lagged:

- `src/guijarro_ordonez_replication/trading.py:250-278` constructs the day-`t`
  feature from `[t-L, t)`.
- `tests/test_trading.py:32-38` tests the backward-looking window.

The leak enters after signal generation:

- `src/guijarro_ordonez_replication/trading.py:297-314` maps residual weights
  to asset weights using `Phi = I - left @ right.T`.
- `src/guijarro_ordonez_replication/trading.py:456-467` applies same-date
  loadings and same-date residual returns in one portfolio path.
- `src/guijarro_ordonez_replication/trading.py:561-570` aligns residuals and
  both low-rank loading arrays to the same batch dates during training.

The existing `docs/pca-methodology.md` discloses the current-day inclusion and
classifies a strictly lagged estimator as an extension. That classification is
too weak: the lagged estimator is required to reproduce the point-in-time
method described by the paper. Conversely, the current implementation should
be retained only as an explicitly named public-code behavior replication.

## Causal diagnostic

A synthetic diagnostic held the first 251 return rows fixed and changed only
the final/current return row. Re-running the local PCA step changed the
same-day composition matrix, with maximum absolute element change
`0.6907398027319213`.

This rules out the possibility that the issue is only a date-labeling or
documentation problem. The day-`t` return causally changes the portfolio
mapping applied on day `t`.

## Research impact

### Invalid until point-in-time rerun

Every completed PCA branch with `K > 0` is affected, including:

- PCA `K = 1, 3, 5, 8, 10, 15` residuals and low-rank loadings;
- OU threshold, Fourier+FFN, direct FFN, OU-feature FFN, and
  CNN+Transformer strategies trained on those residuals;
- rolling, constant, mean-variance, friction-aware, and multi-day variants;
- validation-grid/model-selection results and PCA alternative-network runs;
- PCA-based robustness tables, figures, alpha regressions, checkpoints, and
  report summaries.

The PCA performance rows currently reported in `docs/execution-status.md` must
be interpreted as non-PIT public-code-replication diagnostics. Labels such as
"unadjusted research backtest" or "not deployable" are not sufficient by
themselves: the outputs must explicitly disclose that the day-`t` portfolio
mapping depends on `R_t`.

### Not directly invalidated by this specific issue

- **PCA `K = 0`:** `run.py:550-582` replaces the loaded PCA5 panel with an
  identity-return panel. The PCA5 composition matrix is not used for the return
  mapping. Its universe/reference-mask lineage should still be audited
  separately.
- **Korean Fama-French branches:** their loading regressions use observations
  through `t-1` and apply the frozen beta to current returns/factors. The same
  PCA timing defect has not been found there.
- **IPCA branches:** their projection is based on previously estimated
  parameters and prior-month characteristics. The same defect has not been
  found there; exact Korean IPCA remains blocked for independent data-history
  reasons.

These exclusions are narrow. They do not establish that those branches are
free of every possible look-ahead, universe, return-definition, or execution
issue.

## Root cause and classification

The root cause is a conflict between two replication targets:

1. **Public-code fidelity:** preserve the authors' exact array slicing and
   output behavior.
2. **Paper-method fidelity:** enforce the paper's stated `Phi_{t-1}`
   information set and out-of-sample residual construction.

The current code chose public-code fidelity and documented that choice, but
the downstream results were not classified strongly enough. The two targets
must be separate, named modes or pipelines. A single output must not be
described as satisfying both.

## Required correction

Introduce a paper-method/PIT PCA path with the following date-`t` sequence:

1. Select the eligible universe using only information available by `t-1`.
2. Estimate correlation, volatility, eigenvectors, factor histories, and
   return loadings using windows ending at `t-1`:

   ```python
   covariance_returns = values[day_idx - covariance_window_days:day_idx]
   loading_returns = covariance_returns[-loading_window_days:]
   ```

3. Freeze the resulting `Phi_{t-1}`.
4. After observing `R_t`, compute the factor realization and
   `epsilon_t = Phi_{t-1} R_t` without refitting any parameter on `R_t`.
5. Store estimation cutoff, residual date, availability time, and timing mode
   in the residual/loading audit.
6. Keep the existing estimator only under an explicit classification such as
   `public_code_current_day` or `public_code_non_pit`.

Do **not** repair the issue by shifting the stored composition matrices forward
one row. The residual for each date must be recomputed with a frozen prior-day
matrix, and universe membership, missing-return handling, volatility scaling,
and matrix coordinates must remain aligned.

## Regeneration requirement

Correcting the estimator changes both the factor-residual training inputs and
the residual-to-asset normalization. Existing PCA `K > 0` model checkpoints
therefore cannot be reused as corrected results.

After implementation:

1. regenerate all PCA `K > 0` residual and loading panels;
2. retrain every PCA-dependent strategy and model-selection candidate;
3. rebuild every affected table, figure, alpha regression, audit, and report;
4. preserve the old outputs as a separately labeled
   `public-code/non-PIT` comparison rather than overwriting their provenance;
5. compare public-code and paper-method results to quantify the performance
   inflation or distortion caused by the timing difference.

## Acceptance criteria

- Mutating only `R_t` does not change the matrix labeled `Phi_{t-1}`.
- Mutating any future return `R_{t+1:}` does not change residuals, weights, or
  performance through date `t`.
- The policy feature for date `t` continues to exclude `epsilon_t`.
- The PIT audit records `current_day_in_covariance_and_loading_windows: false`
  and the exact estimation cutoff for every residual date.
- Public-code and paper-method modes have distinct output paths,
  classifications, and provenance.
- No corrected PCA result reuses a checkpoint trained on the non-PIT residual
  panel.
- `docs/pca-methodology.md`, `docs/trading-methodology.md`,
  `docs/execution-status.md`, the output registry, and generated report
  captions disclose the classification consistently.
- A full output is not promoted as paper-method-faithful OOS evidence until
  all PCA-dependent downstream artifacts have been regenerated and reviewed.
