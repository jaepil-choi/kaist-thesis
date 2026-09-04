# SCENARIO.md — the Fama-French residual arm, on Korean data, to a fixed specification

This run is different from an open reproduction. I have a reference implementation of this
arm elsewhere and I want to know whether the same specification, expressed through the
package, lands on the same numbers. So the specification below is not a starting point to
interpret — it is the job. Where I give a number or a rule, use exactly that. Where I have
not given one, follow the paper in `paper/` and record the choice you made.

The reference implementation is outside this directory and stays out of bounds. Do not go
looking for it; ask me instead.

## What I want run

The Fama-French residual arm, `K ∈ {0, 1, 3, 5}`, each with both trading policies:
**OU + Thresh** and **Fourier + FFN**. Eight rows. Nothing else from the paper — no PCA or
IPCA residuals, no CNN+Transformer, no mean-variance objective, no transaction-cost
variants, no `K = 6` or `K = 8`.

## The data

Everything is in `data/`. There is no dictionary; work out what each file holds from the
file itself.

- `data/korean_equity/adjusted_prices.parquet` — the daily panel.
- `data/factors/daily_factor_returns.csv` — the daily factor series. Use the
  value-weighted rows. `K = 1` is `[RMRF]`, `K = 3` is `[RMRF, SMB, HML]`, `K = 5` is
  `[RMRF, SMB, HML, RMW, CMA]`. `K = 0` uses no factors.
- `data/characteristics/monthly_characteristics_raw.parquet` — the monthly firm
  characteristic panel. It is an input to the universe filter, below, and to nothing else.
- `data/ecos/rf_cd_91d_daily_*.json` — the risk-free rate.

The other files under `data/` are not part of this arm. Leave them alone.

## The specification

### S1 — Returns and the risk-free rate

Use the panel's `return` column **as it is given**. A return is missing only when the panel
has no value for it. Do **not** derive missingness from trading halts, zero volume, price
limits, or any other column: a filled zero is an observed zero for this run.

`rf_daily = (1 + CD91/100)^(1/252) − 1`, matched backward to each trading date. Excess
return is `return − rf_daily`. Everything downstream — residuals, weights, the reported
table — is in excess returns.

### S2 — Universe

Two masks, ANDed, evaluated for each trading day `t`:

1. **Monthly**, taken from the month *before* the month containing `t`, and read entirely
   from the monthly characteristic panel — not from the daily panel. A ticker is in the
   monthly mask when all three hold for it in that month:
   - its market capitalisation is non-null and is at least `1e-4` of the summed market
     capitalisation of every row in the monthly panel that month;
   - its monthly return is not missing;
   - **every** characteristic column is non-null for it. The panel's non-characteristic
     columns are its key, its return, its market capitalisation and its accounting
     provenance; everything else in it is a characteristic and all of them count.
2. **Daily**: no missing return in the 60 sessions `[t − 60, t)`.

That is the whole filter. No liquidity, sector, share-class or listing-venue rule on top,
and nothing that looks at `t` or later.

### S3 — Residuals

For `K > 0`, at each `t`: regress each eligible stock's excess returns on the `K` factor
returns over the 60 sessions `[t − 60, t)` by ordinary least squares **with no intercept**.
Freeze those loadings, then `ε_t = xret_t − βᵀ F_t`. The residual portfolio for stock `n`
is `+1` in `n` and `−β_{n,k}` in factor leg `k`; the factors are tradeable assets in the
universe.

For `K = 0`, `ε_t = xret_t` and there are no factor legs.

**No intercept anywhere.** The residual has to be a linear function of that day's returns
so that it is itself a traded portfolio; an intercept breaks that.

### S4 — Windows

The residual panel begins **2020-01-02** and runs to the end of the data.

Every one of the eight rows is evaluated on the **same** out-of-sample window: the residual
panel from its 1001st session onward. This applies to the OU rows too, even though that
rule needs no training — I want the rows comparable, not each row's longest possible
window.

### S5 — OU + Thresh

On the cumulative residual over the local lookback `L = 30`, rebased so each window starts
at that day's residual. Fit an AR(1) `Y_s = α + β Y_{s−1}` on the 29 pairs, with:

- `var(X)`, `var(Y)` on `n − 1` degrees of freedom;
- `cov(X, Y)` as the plain mean of the centred cross-product, on `n`;
- `R² = cov² / (var_X · var_Y)`;
- `β = cov / var_X`, `α = mean_Y − β · mean_X`, `μ = α / (1 − β)`;
- `σ = sqrt( var(residuals, n − 1) / |1 − β²| )`.

Trade the name only when `0 < β < 1` and `σ > 1e-16`. Signal `s = (μ − Y_last) / σ`.
Weight `w = 1{s > 1.25} − 1{s < −1.25}`, multiplied by `1{R² > 0.25}`.

The signal is that ratio directly. Do not introduce a mean-reversion speed, a time-scaling,
or an equilibrium-variance term beyond the `σ` defined above.

### S6 — Fourier + FFN

Features, per name per day: the cumulative residual over the same 30-day rebased window,
real FFT (`rfft`), packed as the real parts of coefficients `0..15` (16 values) followed by
the imaginary parts of coefficients `1..14` (14 values) — 30 floats. **Unscaled**: do not
divide by `L`, do not standardise, do not normalise.

Network: `30 → 16 → 8 → 4 → 1`. Each hidden block is Linear, then ReLU, then dropout at
`0.25`. The output layer is linear, one value per name.

Training: Adam at learning rate `0.001`, 100 epochs, batches of 125 days, a rolling
training window of the previous 1,000 sessions, re-estimated every 125 sessions. The
objective is the Sharpe ratio of the normalised book's daily return.

### S7 — Book construction and timing

Positions in residual portfolios map back to positions in stocks and factor legs. Normalise
so that absolute weights over stocks **and** factor legs sum to one.

The features for day `t` use residuals `ε_{t−30} … ε_{t−1}`; the position formed on `t`
earns `ε_t`. Daily frequency, one-day holding, trading at the close.

Report the weight-based return series — the book's normalised weights against the residual
returns they earn — as the headline. If the package's own accounting produces a second
series (share rounding, a cash book, valuation marks), report that as a cross-check
alongside, and say how far apart they are.

### S8 — Evaluation

Annualised `μ = 252 × mean`, `σ = sqrt(252) × std` with `n − 1` degrees of freedom,
`SR = μ / σ`, on daily excess returns over the common window.

## What I want back

- A table, one row per `K × policy` — eight rows — with SR, `μ` (%), `σ` (%), plus the
  out-of-sample window and the session count. Sharpe to two decimals, `μ` and `σ` to one.
- A cumulative out-of-sample return figure, one line per row.
- The run itself, reproducible: registered inputs, strategies, and whatever the package
  records about the run, so I can re-run it and get the same table.
- A short note, separate from `FINDINGS.md`, of **every place you departed from the
  specification above or had to fill in something it does not fix** — what the spec says or
  omits, what the data let you do, what you did, and how it could move the numbers. I want
  these listed, not silently absorbed. If a piece of the specification cannot be done at all
  with these files or through this package, say so and stop that piece rather than
  substituting something that looks similar.
- Determinism matters this time: fix and record every seed, and say whether a second run of
  the same configuration reproduces the table exactly.

## Conventions I will accept without asking

- A single risk-free series for the whole sample, converted as in S1.
- Whatever the package needs in order to express "decide on the close, fill on that close" —
  if it requires the fill instant to be strictly after the decision instant, invent the
  smallest gap that satisfies it and write it down.

If the specification itself is unclear — which file is which, whether a convention is
acceptable, what I meant by a rule — ask me. Questions about the package are not mine to
answer.
