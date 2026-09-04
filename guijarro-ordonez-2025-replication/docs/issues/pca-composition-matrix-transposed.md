# PCA residual-to-asset weight map is transposed

- **Status:** Code fixed 2026-09-04 (`trading.py`, regression test in
  `tests/test_trading.py`); stored PCA `K > 0` outputs are still from the
  defective code and remain invalid until re-run
- **Severity:** Critical for research validity
- **Affected scope:** PCA branches with `K > 0` — every saved
  `daily_asset_weights.parquet`, the reported `daily_performance.csv` returns,
  turnover, short proportion and leverage, and every table, figure and trained
  checkpoint downstream of them
- **Not affected:** Fama-French branches (a different code path), IPCA (its
  composition matrix is symmetric), PCA `K = 0` (identity)
- **Identified:** 2026-09-04

## Summary

`low_rank_asset_weights` maps residual-portfolio weights to asset weights with
`Phi` where the authors' code uses `Phi'`. The function's own docstring states
the correct map; the two `einsum` calls under it apply the transpose.

The consequence is not a rescaling. The saved PCA asset weights are a different
portfolio from the one whose return is reported, and the reported return is
itself divided by the gross of the wrong portfolio, so the headline Sharpe of
every PCA `K > 0` run is affected too.

## The authors' convention

`Deep_Learning_Statistical_Arbitrage_Code/factor_models/pca.py:190-207`, with
`S` the standardized eigenvectors (`eigenvectors / vol`, the factor-portfolio
weights) and `B` the return loadings (`pca.py:199`, `regr.coef_`):

```text
factors    F = S' r                                      (pca.py:196)
residual   eps = r - B F = (I - B S') r                   (pca.py:200)
so         Phi = I - B S'          and  eps = Phi r
```

`pca.py:204-207` builds `matrix_reduced = I - S B'` and saves
`comp_mtx = matrix_reduced.T = I - B S' = Phi`. The saved matrix is transposed
on purpose, and `simulation.py:25-26` documents the resulting orientation: "the
first row of comp_mtx_t gives the weights of the assets comprising the first
residual".

Asset weights are then formed by multiplying on the **left**
(`simulation.py:81`):

```python
asset_weights = torch.bmm(weights.reshape(T1, 1, N1), comp_mtx_t).squeeze()
```

which is `aw = w' Phi`, i.e.

```text
aw = Phi' w = (I - S B') w = w - S (B' w)
```

This is the only orientation that is self-consistent: the portfolio return
`w' eps` equals `w' Phi r = (Phi' w)' r = aw' r`. What the strategy reports and
what the book holds are then the same thing.

## What this repository does

`src/guijarro_ordonez_replication/pca.py:76-79` stores exactly the authors'
two matrices, and `pca.py:178-179` names them:

```python
left_names  = [f"standardized_eigenvector_{k + 1}" ...]   # S
right_names = [f"return_loading_{k + 1}" ...]             # B
```

`trading.py:129-137` loads them into `left = S`, `right = B`. Then
`trading.py:377-394`:

```python
"""Apply ``Phi=I-left@right.T`` and normalize underlying gross exposure."""
factor_exposure = torch.einsum("tn,tnk->tk", residual_weights, left)    # S' w
asset_weights = residual_weights - torch.einsum(
    "tk,tnk->tn", factor_exposure, right                                # B (S' w)
)
```

The code computes `aw = (I - B S') w = Phi w`. The docstring says
`I - left @ right.T = I - S B' = Phi'`, which is the authors' map. The
docstring is right and the code is transposed.

## Evidence in the saved artifacts

`Phi x = 0` exactly when `x` is in `span(B)`, so `col(Phi)` is the orthogonal
complement of `span(S)` and `col(Phi')` is the orthogonal complement of
`span(B)`. Which map produced a saved weight vector is therefore decidable
without knowing the policy weights and without inverting anything (`Phi` is
singular by construction, so inverting it is not an option):

```text
aw = Phi  w   =>   S' aw = 0        (this repository's map)
aw = Phi' w   =>   B' aw = 0        (the authors' map)
```

`../../scratch-pad-for-ai/enhanced-index/check_composition_maps.py` runs both
projections on every saved day, reporting `|| X' aw || / (|| X ||_2 || aw ||_2)`.
It first confirms the reading of the saved loadings: `eps == r - B (S' r)` holds
to `1.4e-17` on the residual panel.

| run (PCA K=5) | `S' aw` | `B' aw` | reported SR | saved book's own SR |
|---|---:|---:|---:|---:|
| `cnn_transformer_sharpe_lb30_e100_constant` | 2.7e-08 | 0.137 | 4.15 | 2.71 |
| `ou_threshold_sharpe_lb30_e100_rolling` | 1.2e-08 | 0.127 | 1.47 | 0.93 |
| `fourier_ffn_sharpe_lb30_e100_rolling` | 7.2e-08 | 0.235 | 3.27 | 0.15 |

`S' aw` is zero to float32 precision and `B' aw` is not close to zero, so the
saved weights are `Phi w`. The last column is what the saved book earns against
realized excess returns; it does not match the reported return because the saved
book is not the portfolio that earns it.

## Impact

1. **`daily_asset_weights.parquet` for every PCA `K > 0` run is not the tradable
   book of the reported strategy.** Anything that consumes those weights —
   holdings analysis, portfolio-level extensions, cost studies — is reading the
   wrong portfolio.
2. **The reported returns are affected.** `trading.py:546` reports
   `residual_weights * residuals`, but both `residual_weights` and
   `asset_weights` are divided by `gross = |asset_weights|_1` at
   `trading.py:392-394`. With the transposed map that denominator is
   `|Phi w|_1` instead of `|Phi' w|_1`, a different number every day, so the
   reported daily return is misscaled day by day and the annual mean, volatility
   and Sharpe all move. The corrected values cannot be recovered from the saved
   artifacts: `w` is not identifiable from `aw` because `Phi` is singular.
3. **Turnover, short proportion and leverage** are computed from the asset
   weights (`trading.py:549-554`), so the friction-aware and transaction-cost
   PCA runs are affected through their objective as well.
4. **Trained checkpoints must be retrained.** The training objective is the
   Sharpe of `strategy_returns`, which carries the wrong denominator, so the
   learned weights for `fourier_ffn`, `cnn_transformer` and the other trained
   policies are not the weights the corrected objective would produce.
   `ou_threshold` is deterministic and only needs the simulation re-run.

## Fix

Swap the two operands in `trading.py:388-391` so the code matches its docstring
and `simulation.py:81`:

```python
factor_exposure = torch.einsum("tn,tnk->tk", residual_weights, right)   # B' w
asset_weights = residual_weights - torch.einsum(
    "tk,tnk->tn", factor_exposure, left                                 # S (B' w)
)
```

A regression test that does not depend on a policy: for any `w`, the mapped
weights must satisfy `asset_weights @ returns == w @ residuals` on the same day,
since `eps = Phi r`. That identity holds only for the correct orientation and
fails for the transposed one, so it pins the convention directly.

The same script's section 2 applies the identity to the vqapr scenario testbed's independent
Fama-French implementation as a control. There the mapped book and the reported headline agree to
`1e-12` on every day whose residuals are all present, so that implementation already follows the
authors' convention and needs no change.

IPCA needs no change: `trading.py:207-208` builds `left = B`,
`right = B pinv(B'B)`, so `left @ right.T = B pinv(B'B) B'` is symmetric and the
two orientations coincide. Fama-French uses `factor_leg_asset_weights`, a
separate path that packs stock legs and factor legs and is unaffected — its
results agree with an independent implementation of the same specification.

## Re-run order once fixed

1. `ou_threshold` for PCA `K = 1, 3, 5, 8, 10, 15` (deterministic, CPU).
2. Re-train the PCA `fourier_ffn` and `cnn_transformer` grids.
3. Rebuild every table and figure that reads a PCA `K > 0` run.
