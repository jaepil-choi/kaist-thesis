# Korean IPCA methodology and warning contract

## Scope

The paper's IPCA branch uses 46 monthly firm characteristics, a 240-month
rolling estimation window, and annual re-estimation.  The implementation keeps
the same 46 column names and alternating-least-squares equations, but separates
two modes:

1. `paper-exact`: requires 240 complete training months and refuses to run when
   the history is shorter.
2. `korea-short-history`: runs only with `--allow-short-history-ipca` and emits
   `SHORT_HISTORY_IPCA`.

The Korean mode is an extension/sensitivity, not an exact replication result.

## Accounting timing

All annual consolidated accounting values are assigned

```text
available_date = fiscal_period_month_end + 3 calendar months
```

The local facts are latest-revision snapshots without historical announcement
timestamps.  Every build therefore emits `NON_PIT_3M_LAG`.  The lag prevents an
obvious same-period look-ahead, but does not recreate the statement vintage
that an investor actually observed.

## The 46 characteristics

The columns follow Table A.I of Guijarro-Ordonez, Pelger, and Zanotti and
Appendix B of Chen, Pelger, and Zhu:

- past returns: `r2_1`, `r12_2`, `r12_7`, `r36_13`, `ST_Rev`, `LT_Rev`
- investment: `Investment`, `NOA`, `DPI2A`, `NI`
- profitability: `PROF`, `ATO`, `CTO`, `FC2Y`, `OP`, `PM`, `RNA`, `ROA`,
  `ROE`, `SGA2S`, `D2A`
- intangibles: `AC`, `OA`, `OL`, `PCM`
- value: `A2ME`, `BEME`, `C`, `CF`, `CF2P`, `D2P`, `E2P`, `Q`, `S2P`, `Lev`
- trading frictions: `AT`, `Beta`, `IdioVol`, `LME`, `LTurnover`, `MktBeta`,
  `Rel2High`, `Resid_Var`, `Spread`, `SUV`, `Variance`

Raw characteristics are cross-sectionally ranked each month to `[-0.5, 0.5]`.
Missing values remain missing unless
`--impute-missing-characteristics` is explicitly supplied.  That option fills
the missing normalized rank with `0`, the cross-sectional median rank, and the
audit records the imputation.

## Korean proxies

The following substitutions always emit `PROXY_CHARACTERISTICS` and are saved
in `characteristic_audit.json`:

- `Spread`: monthly mean of the daily high-low relative range because bid and
  ask quotes are unavailable.
- `Beta`: local equal-weight market-model beta over at most 1,260 daily
  observations, requiring at least 750.
- `MktBeta`: local equal-weight market-model beta over 60 monthly observations,
  requiring at least 24.
- `IdioVol` and `Resid_Var`: local market-model residual measures.  These are
  not the paper's FF3 residual measures before strict FF3 data become available.
- `CF`: capital expenditure is proxied by positive PPE growth plus depreciation
  and amortization.
- `NI`: when the bounded annual-share extract is absent, the 12-month log change
  in listed common shares from the daily price panel is used.

These substitutions permit estimation but must not be described as exact
Chen-Pelger-Zhu characteristics.

## Universe and estimation

For each month, stocks below 0.01% of aggregate market capitalization are
excluded.  Gamma is estimated from monthly returns and prior-month normalized
characteristics.  For each subsequent daily cross-section:

```text
beta_t = Z_(t-1) Gamma
f_t = pinv(beta_t' beta_t) beta_t' R_t
epsilon_t = R_t - beta_t f_t
```

Gamma is re-estimated every 12 months.  Daily composition matrices are not
materialized because their `T x N x N` size can reach hundreds of GB.  The
saved loadings reproduce a day's matrix as `I - beta pinv(beta)`.

## Commands

```powershell
uv run python guijarro-ordonez-2025-replication/run.py build-ipca-characteristics --allow-non-pit-statements --impute-missing-characteristics
uv run python guijarro-ordonez-2025-replication/run.py estimate-ipca --ipca-factors 5 --ipca-window-months 60 --allow-short-history-ipca
```

Omitting the short-history switch keeps the paper's 240-month gate and fails on
the current Korean history by design.

## Current full-panel audit

The 2026-08-10 full run produced 427,076 security-month rows from January 2015
through July 2026. The raw panel is intentionally sparse before normalization:

- price/trading variables are generally 74% to 100% observed after their own
  lookbacks;
- accounting variables are generally 38% to 50% observed over the full panel;
- `NI` reaches 86.5% after the listed-share proxy;
- direct `D2P` coverage is only 5.4% because the bounded dividend extract has
  280 tickers.

The normalized output is complete only when explicit median-rank imputation is
enabled. Consequently, the short-history IPCA result is a feasibility and
sensitivity result; it is not evidence that the 46 original U.S. variables were
observed without substitution.
