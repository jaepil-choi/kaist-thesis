# Korean rolling PCA methodology and audit

## Public-code contract

The PCA branch follows `Deep_Learning_Statistical_Arbitrage_Code/factor_models/pca.py`:

1. Use the prior calendar month's universe mask.
2. Require monthly return, market capitalization, and all 46 raw firm
   characteristics to be observed.
3. Exclude a stock when its market capitalization is below 0.01% of aggregate
   market capitalization.
4. Require complete daily returns in the preceding 60 trading days.
5. Estimate the daily correlation eigenvectors from 252 observations ending on
   the residual date.
6. Regress the last 60 returns, including the residual date, on the PCA factors
   without an intercept.
7. Subtract the fitted return from that day's excess return.

The inclusion of the current return in both the 252-day covariance window and
the 60-day loading regression is not an interpretation: it is the behavior of
the authors' public code. It is retained for replication and recorded in every
audit. A strictly lagged alternative belongs in a separate extension.

## Return and universe limitations

Daily inputs are adjusted price returns minus the ECOS 91-day CD daily return.
The price return excludes cash dividends, so the result is a **Korean
price-return PCA replication variant**, not a total-return exact replication.

The public code applies its all-characteristic nonmissing filter even though
PCA does not directly use the characteristics. The Korean implementation
therefore uses `monthly_characteristics_raw.parquet`, not the median-imputed
normalized panel. Because direct `D2P` and other accounting coverage is sparse,
the first prior-month universe with more than five eligible stocks is December
2019. The first valid daily OOS date is consequently January 2, 2020.

## Low-rank composition storage

For each day, let `V` be the top PCA eigenvectors, `D` the diagonal volatility
matrix, and `L` the no-intercept return-regression loadings. The residual is

```text
epsilon = r [I - D^(-1) V L'].
```

Storing the full daily N-by-N matrix is unnecessary. The output stores
`D^(-1)V` and `L` by date and ticker, which reconstruct the exact composition
matrix as

```text
I - standardized_eigenvectors @ return_loadings.T
```

## 2026-08-10 full-panel result

The K=5, covariance-252, loading-60 run completed without skipped days:

- residual dates: 2020-01-02 through 2026-07-20;
- trading days: 1,606;
- residual and loading rows: 275,711 each;
- selected stocks per day: minimum 127, median 176, maximum 185.

With the paper's 1,000-day policy-training window, the first date after 1,000
residual observations is 2024-01-19. If the 30-day signal lookback is formed
before the 1,000 training examples, the corresponding first date is 2024-03-06.
The trading-policy implementation must fix which indexing convention matches
the public simulation code before reporting an OOS strategy start.

## Command

```powershell
uv run python guijarro-ordonez-2025-replication/run.py estimate-pca --pca-factors 5 --pca-initial-oos-date 2020-01-02
```
