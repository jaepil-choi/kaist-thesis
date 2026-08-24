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

The public replication code initializes monthly factors with `PCA(X.T)`,
allows up to 1,500 ALS iterations, and stops when the maximum absolute Gamma
change is below `1e-3`. Daily factor regressions use returns after subtracting
the daily risk-free return. Missing daily stock returns in a selected monthly
universe are represented as zero during the cross-sectional regression and
remain zero residuals, matching the public array implementation.

`initial_months` and the rolling `window_months` are distinct. The paper's
public configuration uses 420 pre-OOS months but estimates Gamma on only the
last 240 months. The estimator now rejects any ALS window that fails the
published convergence rule instead of writing unstable residuals.

## Commands

```powershell
uv run python guijarro-ordonez-2025-replication/run.py build-ipca-characteristics --allow-non-pit-statements --impute-missing-characteristics
uv run python guijarro-ordonez-2025-replication/run.py estimate-ipca --ipca-factors 5 --ipca-initial-months 60 --ipca-window-months 60 --allow-short-history-ipca
```

Omitting the short-history switch keeps the paper's 240-month gate and fails on
the current Korean history by design.

## Reduced-instrument and ridge-Gamma sensitivity

This is a deliberate extension, not a replication detail.  It exists because
the paper-specified Korean fit (46 instruments, K=5, 60-month window, no
penalty) diverges.  Two orthogonal deviations are now available and both
default to the paper's specification:

- `--ipca-characteristic-coverage T` keeps only characteristics whose measured
  raw coverage in `characteristic_audit.json` reaches `T`.  `0` keeps all 46.
  Selecting a subset emits `REDUCED_CHARACTERISTICS`.
- `--ipca-gamma-ridge L` adds `L * mean(diag(A)) * I` to the Gamma normal
  equations `A vec(Gamma) = b`.  The penalty is scaled by the mean diagonal so
  that `L` is a dimensionless shrinkage intensity comparable across windows and
  instrument counts.  `0` reproduces the paper.  Any positive value emits
  `RIDGE_GAMMA`.

The public reference implementation has no penalty term at all: its Gamma step
is `np.linalg.solve(A, b)` with a `np.linalg.pinv` fallback.  A ridge run must
therefore always be labeled as a deviation from the published estimator.

### Which characteristics survive the coverage filter

Only eight characteristics reach 90% raw coverage, and all eight are
price/trading variables:

```text
r2_1  ST_Rev  LME  LTurnover  Rel2High  Spread  SUV  Variance
```

No accounting characteristic qualifies; the best is `NI` at 86.5%.  Lowering
the threshold to 80% adds only `r12_2`, `r12_7` and `NI`.  A coverage-selected
Korean IPCA is consequently a factor model instrumented on past returns and
liquidity, not on the paper's value, profitability and investment variables.
It must not be described as a reduced-form version of the paper's IPCA.

`Spread` is itself the high-low proxy and correlates 0.875 with `Variance`, so
the surviving set is narrower in economic content than eight columns suggest.

### The instrument set is rank-deficient by construction

`r2_1` and `ST_Rev` are numerically identical columns in this panel.  That is
not a builder defect: under Chen, Pelger and Zhu's definitions both are the
prior-month return, and `characteristics.py` assigns them the same series.  The
pooled instrument Gram therefore has an exactly zero eigenvalue and a condition
number of 1.09e17 on the eight-column set, 2.7e19 on the full 46.  This is why
the reference implementation needs its `pinv` fallback, and it means Gamma is
not uniquely identified without a penalty.

### Convergence grid

`scripts/ipca_reduced_grid.py` fits the same ALS system and annual windows as
`estimate-ipca` but writes no residuals.  Results at the paper's 1e-3
tolerance, 1500-iteration ceiling, 60-month initial and rolling windows:

| coverage | L | K | ridge | converged | worst delta | max abs Gamma |
|---|---:|---:|---:|---:|---:|---:|
| >=0.9 | 8 | 1 | 0 | 7/7 | 0.000706 | 1.781 |
| >=0.9 | 8 | 1 | 0.001 | 7/7 | 0.000864 | 1.405 |
| >=0.9 | 8 | 1 | 0.01 | 7/7 | 0.001 | 0.2407 |
| >=0.9 | 8 | 1 | 0.1 | 7/7 | 0.000973 | 0.0236 |
| >=0.9 | 8 | 3 | 0 | 7/7 | 0.000953 | 224.9 |
| >=0.9 | 8 | 3 | 0.001 | 7/7 | 0.000999 | 0.3139 |
| >=0.9 | 8 | 3 | 0.01 | 7/7 | 0.000995 | 0.03223 |
| >=0.9 | 8 | 3 | 0.1 | 7/7 | 0.000991 | 0.01654 |
| >=0.9 | 8 | 5 | 0 | 7/7 | 0.000947 | 9.972 |
| >=0.9 | 8 | 5 | 0.001 | 7/7 | 0.000964 | 0.02553 |
| >=0.9 | 8 | 5 | 0.01 | 7/7 | 0.000993 | 0.01883 |
| >=0.9 | 8 | 5 | 0.1 | 7/7 | 0.000978 | 0.002577 |
| >=0.8 | 11 | 1 | 0 | 7/7 | 0.00062 | 1.389 |
| >=0.8 | 11 | 1 | 0.001 | 7/7 | 0.000905 | 1.386 |
| >=0.8 | 11 | 1 | 0.01 | 7/7 | 0.001 | 0.2632 |
| >=0.8 | 11 | 1 | 0.1 | 7/7 | 0.000998 | 0.02646 |
| >=0.8 | 11 | 3 | 0 | 7/7 | 0.000973 | 2.011e+05 |
| >=0.8 | 11 | 3 | 0.001 | 7/7 | 0.001 | 1.323 |
| >=0.8 | 11 | 3 | 0.01 | 7/7 | 0.000992 | 0.04164 |
| >=0.8 | 11 | 3 | 0.1 | 7/7 | 0.000948 | 0.007017 |
| >=0.8 | 11 | 5 | 0 | 7/7 | 0.000974 | 6.376 |
| >=0.8 | 11 | 5 | 0.001 | 7/7 | 0.001 | 0.2386 |
| >=0.8 | 11 | 5 | 0.01 | 7/7 | 0.000958 | 0.008213 |
| >=0.8 | 11 | 5 | 0.1 | 7/7 | 0.000845 | 0.001649 |
| >=0 | 46 | 1 | 0 | 7/7 | 0.000811 | 1.369 |
| >=0 | 46 | 1 | 0.001 | 7/7 | 0.000971 | 1.368 |
| >=0 | 46 | 1 | 0.01 | 7/7 | 0.001 | 0.5665 |
| >=0 | 46 | 1 | 0.1 | 7/7 | 0.000992 | 0.05962 |
| >=0 | 46 | 3 | 0 | 4/7 | 0.126 | 352 |
| >=0 | 46 | 3 | 0.001 | 7/7 | 0.000995 | 0.1704 |
| >=0 | 46 | 3 | 0.01 | 7/7 | 0.000985 | 0.05158 |
| >=0 | 46 | 3 | 0.1 | 7/7 | 0.001 | 0.01369 |
| >=0 | 46 | 5 | 0 | 0/7 | 3.36e+23 | 3.364e+23 |
| >=0 | 46 | 5 | 0.001 | 7/7 | 0.000698 | 0.0005081 |
| >=0 | 46 | 5 | 0.01 | 7/7 | 0.000453 | 0.006581 |
| >=0 | 46 | 5 | 0.1 | 7/7 | 0.000889 | 0.00181 |

Two readings matter:

1. The full 46-instrument fit fails exactly as documented: K=5 without a
   penalty ends at `3.36e23` and converges in zero of seven windows, while K=3
   converges in only four.  Any positive ridge rescues both.
2. A reduced instrument set appears to fix the problem on its own, but this is
   an artifact of the loose tolerance.  See below.

### The 1e-3 gate is too loose to certify these fits

Every unpenalized reduced-set fit lands just under the tolerance
(0.00062--0.00099).  Re-running at `--tolerance 1e-6`:

| L | K | ridge | converged at 1e-6 | worst delta |
|---:|---:|---:|---:|---:|
| 8 | 5 | 0 | 0/7 | 1.22e-02 |
| 8 | 5 | 0.001 | 7/7 | 9.98e-07 |
| 8 | 5 | 0.01 | 7/7 | 9.46e-07 |
| 8 | 5 | 0.1 | 7/7 | 9.49e-07 |
| 46 | 5 | 0.001 | 7/7 | 9.32e-07 |
| 46 | 5 | 0.01 | 7/7 | 9.60e-07 |
| 46 | 5 | 0.1 | 7/7 | 8.50e-07 |

Reducing the instrument set does not make the system identified; it only slows
the drift enough to pass the published gate.  The ridge is what restores
identification, and it does so for the full 46 instruments as well.  The
unpenalized Gamma also grows across windows -- `max abs Gamma` rises 1.39, 2.45,
9.97 over the seven annual fits -- while the penalized Gamma declines smoothly
from 0.0188 to 0.0119.  A loading map of order 10 applied to ranks in
`[-0.5, 0.5]` is not an economically plausible beta.

### Residuals are nearly invariant to the penalty

The two eight-instrument residual panels correlate 0.9990 overall and at least
0.9962 in every calendar year, with annualized residual volatility 0.4568
versus 0.4565.  This is expected: the residual is the projection
`R - B pinv(B'B) B' R` onto the column space of `B = Z Gamma`, and shrinking
Gamma changes its scale far more than its span.  The ridge should therefore be
justified as restoring a well-posed, reproducible estimate of Gamma, not as a
device that improves residual quality.

Against the PCA5 reference the coverage-selected IPCA residuals retain more
market exposure (mean absolute market beta 0.25 versus 0.04) and higher
dispersion (0.457 versus 0.336 annualized).  These two panels are not directly
comparable: the IPCA universe is the monthly characteristic universe with 1,820
tickers, while the PCA branch trades a 127--185 stock daily cross-section.

### Commands

```powershell
uv run python guijarro-ordonez-2025-replication/scripts/ipca_reduced_grid.py
uv run python guijarro-ordonez-2025-replication/run.py estimate-ipca `
    --ipca-factors 5 --ipca-initial-months 60 --ipca-window-months 60 `
    --allow-short-history-ipca --ipca-characteristic-coverage 0.90 `
    --ipca-gamma-ridge 0
uv run python guijarro-ordonez-2025-replication/run.py estimate-ipca `
    --ipca-factors 5 --ipca-initial-months 60 --ipca-window-months 60 `
    --allow-short-history-ipca --ipca-characteristic-coverage 0.90 `
    --ipca-gamma-ridge 0.01
uv run python guijarro-ordonez-2025-replication/scripts/compare_ipca_residuals.py
```

Artifacts are tagged `k5_i60_w60_c8` and `k5_i60_w60_c8_r0p01`; the paper's
own specification keeps its existing untagged `k{K}_i{I}_w{W}` name.  Each
run produced 1,330,517 daily residual rows over 2020-01-02--2026-07-20.

### Classification

Both arms carry the deviations `short-history` and `reduced-characteristics`,
and the penalized arm adds `ridge-gamma`.  Neither is an exact replication of
any result in the paper, and neither removes the 240-month blocker.

## Recovering the accounting characteristics

The first reduced-instrument run admitted eight price/trading columns and no
accounting column at all.  That was a data-plumbing artifact, not a property of
the Korean market.  Two opt-in fixes now exist on
`build-ipca-characteristics`; both are recorded in the panel audit and both
write to tagged artifacts so the paper-default panel consumed by `estimate-pca`
and every numbered output is never overwritten.

- `--allow-separate-scope`.  FnGuide publishes consolidated statements as
  `4001NNNNNN` in `DW_FNG_연결재무제표` and separate statements as
  `1001NNNNNN` in `DW_FNG_재무제표`.  The pipeline only carried the `4001`
  codes, so an issuer without subsidiaries, which files separate accounts only,
  matched no code at all and was dropped.  Twenty-one of the 23 mapped items
  have a twin code; `noncontrolling_interest` does not exist in a separate
  statement and is set to zero, and `deferred_tax` has no twin and stays
  missing, which both consuming formulas already treat as zero.
- `--common-share-class-only`.  Korean common shares end in `0`; preferred and
  other classes end in 5, 7, 9 or a letter and have no statements of their own.
  Carrying them depressed measured coverage and duplicated their issuer's
  exposure.  153 classes are removed.

Scope selection is per firm-year and all-or-nothing.  A complete consolidated
statement always wins; a separate statement is used when consolidated is
absent or missing a core item; an incomplete consolidated statement is still
kept when no complete separate one exists, so characteristics needing only a
few items stay computable.  Mixing consolidated assets with separate sales
inside one firm-year would produce an internally inconsistent statement.

### Coverage effect

Measured on the 0.01% market-cap estimation universe from 2019 onward:

| characteristic group | before | after |
|---|---:|---:|
| `BEME` `A2ME` `Q` `Lev` `AT` `D2A` | 0.741 | 0.829 |
| `Investment` `NOA` `DPI2A` `RNA` `AC` `OA` | 0.701 | 0.801 |
| `C` `CF2P` `E2P` | 0.711 | 0.799 |
| `ROA` `ROE` `CF` | 0.675 | 0.772 |
| `PROF` `OP` `OL` `PCM` | 0.655 | 0.734 |

No characteristic regresses; price columns move by at most 0.002 because
removing preferred classes changes the cross-section slightly.  5,269
firm-years use separate statements.  `D2P` stays at 0.242 because the dividend
extract covers only 280 tickers.

Remaining blockers are documented in `docs/data-requirements.md`: financial
sector issuers are absent from the statement extract entirely, and the FY2016
start plus the `shift(1)` lag chains leave four of the eleven panel years
structurally empty.

### Three coverage bases

Coverage depends on which rows you count, and the three bases disagree enough
to change the selected instrument set:

- `coverage` in the audit: every ticker and month in the raw panel.
- `coverage_estimation_universe`: the 0.01% market-cap universe, all months.
- `--ipca-coverage-from 2019-01-01`: that universe restricted to the months in
  which accounting data can exist at all.

The first two average in 2015--2018, where accounting characteristics are zero
by construction, so no accounting column can clear a 0.80 threshold under
either.  Selecting on the third basis is a deliberate, documented choice; the
selected columns are always written into the run audit.  At threshold 0.80 it
admits 28 instruments of which 13 are accounting, and at 0.75 it admits 40 of
which 25 are accounting.

### Convergence with accounting instruments

The ridge conclusion holds and sharpens.  K=5, 60-month windows, paper
tolerance:

| instruments | ridge | converged | max abs Gamma |
|---|---:|---:|---:|
| 8 price only | 0 | 7/7 | 9.97 |
| 8 price only | 0.01 | 7/7 | 0.019 |
| 28 with accounting | 0 | fails at window 2020-01--2024-12 | -- |
| 28 with accounting | 0.01 | 7/7 | 0.0046 |
| 40 with accounting | 0 | 7/7 | 0.013 |
| 40 with accounting | 0.01 | 7/7 | 0.0014 |
| 46 full set | 0 | 1/7 | 1.6e16 |
| 46 full set | 0.01 | 7/7 | -- |

The 28-instrument fit refuses to converge without a penalty
(`final_delta=0.00278` after 750 iterations) even though the 40-instrument fit
converges: ALS convergence is not monotone in the number of instruments.  Any
specification that includes accounting characteristics should carry the ridge.

### Residual comparison

All four IPCA panels cover 2020-01-02--2026-07-20 with 1,330,517 to 1,334,017
rows.

| panel | stocks | annualized residual std | mean abs market beta |
|---|---:|---:|---:|
| 8 price, ridge 0.01 | 1,820 | 0.4565 | 0.253 |
| 28 with accounting, ridge 0.01 | 1,817 | 0.4632 | 0.324 |
| 40 with accounting, ridge 0 | 1,817 | 0.4646 | 0.337 |
| 40 with accounting, ridge 0.01 | 1,817 | 0.4625 | 0.312 |
| PCA5 reference | 228 | 0.3358 | 0.036 |

Adding accounting instruments slightly raises both residual dispersion and
leftover market exposure.  That is worth stating plainly rather than assuming
richer instruments must produce cleaner residuals, but it should not be
over-read: the panels differ in which price instruments they also contain, and
the PCA5 column trades a 127--185 stock cross-section rather than 1,817.

### Commands

```powershell
uv run python guijarro-ordonez-2025-replication/run.py build-ipca-characteristics `
    --allow-non-pit-statements --impute-missing-characteristics `
    --allow-separate-scope --common-share-class-only
uv run python guijarro-ordonez-2025-replication/run.py estimate-ipca `
    --ipca-factors 5 --ipca-initial-months 60 --ipca-window-months 60 `
    --allow-short-history-ipca --ipca-panel-tag _sepscope_common `
    --ipca-characteristic-coverage 0.80 --ipca-coverage-from 2019-01-01 `
    --ipca-gamma-ridge 0.01
```

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

The K=5, 60-month Korean sensitivity is currently **blocked by numerical
non-convergence**. With the public `PCA(X.T)` initialization, `solve`-first
normal equations, 1,500-iteration ceiling, and `1e-3` tolerance, the January
2015--December 2019 window ended at `final_delta=3.71009`; shifting the window
to January 2016--December 2020 produced `final_delta=2.42492e23`. These windows
must not be used as residual inputs. The likely mechanism is weak numerical
identification from a window only 60 months long combined with extensive
median-rank imputation, especially direct `D2P` coverage of only 5.4%.
