# vqapr-scenario-testbed run 2 — spec corrections against the canonical implementation

- **Date:** 2026-09-03
- **Audience:** evaluator. Not for the agent under evaluation — it references
  `Deep_Learning_Statistical_Arbitrage_Code/` and `guijarro-ordonez-2025-replication/`,
  both out of bounds inside the testbed.
- **Subject:** where run 2's FF-residual arm departs from the authors' published
  implementation, and what has to be pinned so a run 3 is comparable to
  `guijarro-ordonez-2025-replication/`.

Run 2 produced `vqapr-scenario-testbed/out/` (phase 1: FF5+MOM K=6 OU+Thresh; phase 2:
K=0 and FF5 × {OU+Thresh, Fourier+FFN}). Its scenario had asked for the PCA arm and was
replaced live with the FF arm after the 252-day rolling PCA exhausted memory.

The canonical reference for every item below is the authors' code in
`Deep_Learning_Statistical_Arbitrage_Code/`, the official implementation published with
the paper. Where paper text and that code disagree, the disagreement is named explicitly.

---

## C-1 The loading regression must have no intercept — run 2 is wrong

Paper, equation (1)
(`docs/markdown/2025 Deep Learning Statistical Arbitrage - Guijarro-Ordonez et al. (MS).md:671-677`):

```
ε_t = R_t − β_{t−1}ᵀ F_t = (I_N − β_{t−1} wF_{t−1}ᵀ) R_t = Φ_{t−1} R_t
```

No alpha. This is structural, not notational: the sentence immediately above it says the
factors are traded assets and therefore "the arbitrage portfolios are themselves traded
portfolios". The residual has to be a linear function of `R_t` for `Φ_{t−1} R_t` to be a
portfolio return. An intercept adds a constant that no portfolio pays.

Official code, `Deep_Learning_Statistical_Arbitrage_Code/factor_models/famafrench.py:183`:

```python
regr = LinearRegression(fit_intercept=False, n_jobs=1).fit(X, Y)
...
residuals = oos_returns - factors.dot(loadings)
```

`factor_models/pca.py:198` is the same.

The paper's "This is the same procedure as in Carhart (1997)" (line 2028) refers to the
rolling 60-day loading estimation, not to carrying an alpha.

Run 2 estimated with an intercept and dropped it from the coefficient vector
(`vqapr-scenario-testbed/work/decl/ff5_resid.py:65-67`), leaving the estimated alpha
inside the residual. `out/DEVIATIONS.md` D-9 calls this "a choice the paper does not spell
out". The paper does spell it out. D-9 is an error, not a deviation.

`guijarro-ordonez-2025-replication` is correct here
(`src/guijarro_ordonez_replication/fama_french_residuals.py`, `fit_intercept=False`).

## C-2 The universe is a three-part monthly mask, not a cap filter — run 2 is wrong

Official code, `factor_models/utils.py:88-97`, called identically by `famafrench.py:121`,
`pca.py:120` and `ipca.py:360`:

```python
market_cap_mask   = monthly_caps / np.nansum(monthly_caps, axis=1, keepdims=True) >= cap_pct * 0.01
non_nan_ret_mask  = ~np.isnan(monthly_returns)
non_nan_char_mask = ~np.isnan(unnormalized_monthly_chars.sum(axis=2))   # all 46 characteristics
mask = non_nan_ret_mask & non_nan_char_mask & market_cap_mask
```

applied at the previous month (`famafrench.py:162`,
`monthly_idx = first_oos_monthly_idx - 2  # ensures monthly mask is always backward-looking`),
and ANDed each day with a daily no-missing-return test over the 60-session loading window
(`famafrench.py:169-170`).

The paper's body text (lines 1959-1961) names only the 0.01% cap cut. The characteristic
requirement is implicit in "For each stock we have its cross-sectionally centered and
rank-transformed characteristics of the previous month" and explicit in the code.

Run 2 applied the cap cut alone (`vqapr-scenario-testbed/prep/prepare.py:97`,
`me["member"] = me.market_cap > 1e-4 * me.tot`) — no monthly-return test, no characteristic
test. Result: ~825 names a month against the replication's 228 over the sample and a
median 176 a day in the FF5 panel.

`guijarro-ordonez-2025-replication` reproduces the canonical mask
(`src/guijarro_ordonez_replication/pca.py:141`, `fama_french_residuals.py:64`).

### Caveat that belongs in both projects' notes

Faithful to the code is not the same as faithful to the paper's intent here. In the US
panel the paper says the missing-data filters remove at most 2% of stocks. On this Korean
characteristic build they are the binding constraint: estimation-universe coverage in
`guijarro-ordonez-2025-replication/outputs/ipca/characteristic_audit_sepscope_common.json`
runs from 0.196 (D2P) through a median of 0.581. Requiring all 46 non-null is what takes
the universe to 228 names, not the cap cut. So 228 is a Korean data limitation, not "the
paper's ~550 largest names, roughly the S&P 500". `docs/execution-status.md` says only
"a smaller KOSPI/KOSDAQ universe", which does not distinguish the two causes and should.

## C-3 Halted and zero-volume days — run 2 diverges knowingly

Run 2 treats a day as unobserved unless the name actually traded (`out/DEVIATIONS.md` D-5):
halts and zero-volume days become NULL and non-tradable. The canonical code has no such
concept (CRSP has no halt column) and the replication reads the vendor `return` column as
given (`src/guijarro_ordonez_replication/characteristics.py:199-224`), so the vendor's
filled zeros enter as observed returns.

D-5's reasoning is sound on its own terms — a halted name's flat line looks like perfect
mean reversion to the OU rule. But it is a different specification, and it has to be
switched off for a like-for-like comparison. Keep it as a named sensitivity, not as the
headline.

## C-4 Fourier+FFN specification — run 2 guessed, and guessed differently

Run 2 could not read the architecture: `paper/` lost Figure A.1 in text extraction
(`out/DEVIATIONS.md` D-14), so it used 2 hidden layers × 32 ReLU units, no dropout, and
FFT coefficients divided by L.

Canonical, `Deep_Learning_Statistical_Arbitrage_Code/models/FourierFFN.py:34-57`:
`hidden_units = [30, 16, 8, 4]`, i.e. 30 → 16 → 8 → 4 → 1, each hidden block
Linear + ReLU + `Dropout(0.25)`, linear output.

Canonical features, `preprocessing.py:86-95`: cumulative residual over the 30-day window,
rebased so each window starts at that day's residual, then `np.fft.rfft`, packed as real
parts of coefficients 0..15 (16 values) followed by imaginary parts of coefficients 1..14
(14 values) = 30 floats. **No division by L.**

## C-5 OU+Thresh estimator details — run 2 diverges in two places

Canonical, `models/OUThreshold.py:82-141`, on the 29 AR(1) pairs of the 30-day cumulative
residual:

- `vars_x`, `vars_y`: `torch.var` (n−1). `covs`: `torch.mean` of the cross-product (n).
  R² = cov² / (var_x · var_y).
- β = cov / var_x, α = mean_y − β·mean_x, μ = α / (1 − β).
- σ = sqrt(var(residuals, n−1) / |1 − β²|).
- trade only if `0 < β < 1` and σ > 1e-16.
- signal = (μ − Y_last) / σ; w = 1{signal > 1.25} − 1{signal < −1.25}, times 1{R² > 0.25}.

There is **no κ = −log β** anywhere in the signal. Run 2's D-10 describes the Appendix B.2
parameterisation with κ and a `σ_e²` with two degrees of freedom removed; the canonical
code uses neither.

## C-6 Comparison mechanics — run 2 already matches

- L1 normalisation is over **asset** weights, stocks and factor legs together
  (`simulation.py:79-84`).
- Alignment: features from `ε_{t−30..t−1}`, position earns `ε_t` (`simulation.py:764`,
  `rets_test = torch.sum(weights * data_test[lookback:T,:], axis=1)`). The two projects'
  output series correlate highest at lag 0, so both label days the same way.
- Annualisation: `mean × 252` over `std(ddof=1) × sqrt(252)` (`simulation.py:492-501`).
- Run 2 books through a 10bn KRW venue with whole-share rounding; the replication computes
  weight × return directly. Run 2's own cross-check put the gap at ≤ 1.8e-3 on a few days.
  For a controlled comparison the weight-based series should be the headline and the NAV
  series the cross-check.

---

## What a run 3 needs staged into `vqapr-scenario-testbed/data/`

The testbed cannot reach either reference project, so the two derived inputs have to be
staged as ordinary data files, under neutral names that do not point outside:

| stage as | from | why |
|---|---|---|
| `data/factors/daily_factor_returns.csv` | `guijarro-ordonez-2025-replication/outputs/kimchi-exact/daily_factor_returns.csv` | the shipped `data/kimchi-factor/*_vw_all.csv` are a *different* build: `outputs/kimchi-exact/kimchi_factor_comparison.csv` puts RMW at correlation 0.959 and CMA at 0.942 against them. The same series is required for an exact match. |
| `data/characteristics/monthly_characteristics_raw.parquet` | `guijarro-ordonez-2025-replication/outputs/ipca/monthly_characteristics_raw.parquet` | the universe mask needs all 46 characteristics. Rebuilding them from `fng_statement_facts` inside the testbed will not reproduce the same panel. **Not the `_sepscope_common` variant** — `run.py:848` (FF) and `run.py:643` (PCA) both read the base panel. See the addendum. |

`data/kimchi-factor/` should be removed from the staged tree at the same time, so the agent
cannot silently pick the wrong series.

## Consequence for the experiment

Pinning C-1 through C-5 in `SCENARIO.md` turns run 3 into a controlled comparison — "can
vqapr express this exact specification and reproduce a known series" — rather than the
discovery run the testbed was built for. That is a deliberate trade: run 3's `FINDINGS.md`
measures expressiveness and friction under a fixed spec, not whether a first-time user can
work the spec out. Worth stating in the run-3 row of the provenance table.

## Unrelated defect noticed while reading

`vqapr-scenario-testbed/.gitignore` ignores `FINDINGS.md`, `SCENARIO.md`, `data/`,
`paper/`, `workspace/`, `outputs/`, `build/`, `.vqapr/` and `.venv/` — but not `out/`,
`work/`, `prep/` or `runs/`, which run 2 produced. `README.md` states that nothing a run
produces is ever committed, because "a committed FINDINGS.md, workspace or scenario would
hand the next agent the previous agent's answers". Those four directories are currently one
`git add -A` away from doing exactly that.

---

# Addendum, 2026-09-04 — run 3 (`ff-spec`) verified against the replication

Run 3 executed the corrected `SCENARIO.md` and produced `vqapr-scenario-testbed/out/spec/`.
It claims determinism (`ff-spec` vs `ff-spec-b`: byte-identical weight tables, matching
record fingerprints) and internal consistency (headline vs the package's NAV accounting
within 9.3e-5). It does **not** claim agreement with the replication, and
`REPORT_spec.md` explicitly says bit-for-bit agreement with a PyTorch reference is not
expected. Checked against `outputs/paper-korean/table_01_korean_performance.csv` and the
per-strategy `daily_performance.csv`, on the identical 606-session window:

| cell | run 3 SR | rep SR | corr | days identical (<1e-9) | max daily gap |
|---|---|---|---|---|---|
| OU K0 | 0.36 | 0.35 | 0.998 | 334/606 | 6.8e-3 |
| OU K1 | 0.24 | 0.28 | 0.998 | 340/606 | 2.7e-3 |
| OU K3 | 0.69 | 0.73 | 0.997 | 348/606 | 2.6e-3 |
| OU K5 | 0.44 | 0.47 | 0.995 | 334/606 | 2.9e-3 |
| FFN K0 | 0.47 | −1.01 | 0.776 | 0/606 | 4.3e-2 |
| FFN K1 | 0.49 | 1.45 | 0.678 | 0/606 | 2.6e-2 |
| FFN K3 | 0.83 | 1.76 | 0.594 | 0/606 | 1.4e-2 |
| FFN K5 | 0.64 | 1.45 | 0.398 | 0/606 | 1.2e-2 |

## A-1 The OU rows are reproduced; the residual pipeline is verified identical

Comparing run 3's recorded weight table
(`.vqapr/runs/ff-spec/strategies/ou-k5-v2@32ebf12b/tables/vqapr.weight.jsonl`, factor legs
renamed `F_X` → `FACTOR::X`, decision date shifted to the return session) against
`outputs/strategies/ff5_ou_threshold_.../daily_asset_weights.parquet`:

- 19,663 jointly-held (name, day) positions, **zero sign disagreements**;
- median relative weight difference 1.0e-7, i.e. the parquet's float32 storage;
- on the 338 sessions where the two held-name sets are identical, the maximum weight
  difference across every stock and factor leg is 5.8e-8.

So no-intercept residuals, the OU estimator, the residual-to-asset mapping and the L1
normalisation all agree. Every remaining difference enters through universe membership.

## A-2 The universe gap is my staging error, not the run's

I staged `monthly_characteristics_raw_sepscope_common.parquet`. The replication's FF and
PCA residual builders read the **base** panel, `outputs/ipca/monthly_characteristics_raw.parquet`
(`run.py:848` and `run.py:643`). The sepscope panel is the separate-scope / common-share-class
rebuild with better accounting coverage, so it admits strictly more names:

- applying the S2 mask to both, the base panel's eligible month-ticker set is a **strict
  subset** of the sepscope panel's: 13,689 pairs in both, 0 base-only, 478 sepscope-only;
- 229 eligible tickers (base) against 235 (sepscope); the base figure matches the
  replication's `residual_assets = 228`;
- mean eligible names a month over 2024-2026: 173.5 (base) against 176.8 (sepscope);
- four tickers — `A002960`, `A006390`, `A104700`, `A178920` — are eligible under sepscope
  and never under base. They account for 281 of the 352 (name, day) positions run 3 holds
  and the replication does not.

Because the book is L1-normalised, one extra name changes every weight that day, which is
why 45% of sessions differ while the machinery is identical.

**Action:** restage `outputs/ipca/monthly_characteristics_raw.parquet` and re-run. Note that
overwriting the staged file breaks run 3's provenance (issue `023`: nothing compares a run
record's source digests to what is registered now), so archive `out/spec/` and the `ff-spec`
run records first.

A second, smaller discrepancy survives that fix and should be re-checked afterwards: 29
(name, day) positions held by the replication and not by run 3, ~0.15% of the joint book.
The likely cause is run 3's rule that a name needs 30 *consecutive* eligible sessions
(`DEVIATIONS_spec.md`, S5) against the public-code convention where a missing residual is
stored as zero and the window is filled rather than dropped
(`Deep_Learning_Statistical_Arbitrage_Code/factor_models/utils.py`, `compute_residual_filter`
and `compute_nonmissing_indices`). Worth pinning in S5 before the re-run.

## A-3 The Fourier+FFN rows are not reproduced, and probably cannot be at one seed

The FFN cells disagree far beyond anything the universe can explain — K = 0 has no factor
model at all and differs by ~3 names in 176, yet the Sharpe ratios are +0.47 and −1.01. The
disagreement is unstable rather than biased:

| | 2024 | 2025 | 2026 |
|---|---|---|---|
| FFN K0 run 3 | −0.78 | 1.99 | 0.53 |
| FFN K0 rep | −1.81 | −0.52 | −1.25 |
| FFN K5 run 3 | 1.62 | 1.19 | −0.46 |
| FFN K5 rep | 0.74 | 1.86 | 1.94 |

Run 3's network follows the specification (30 → 16 → 8 → 4 → 1, ReLU, dropout 0.25,
unscaled `rfft` features, Adam 1e-3, 100 epochs, 125-day batches, 1,000-session rolling
window, 5 retrainings) but is numpy with hand-written gradients — no ML library is
installed in the testbed and `AGENTS.md` forbids adding one. Different RNG streams for
initialisation and dropout, and a different reduction order, are enough to put two faithful
implementations this far apart after 100 epochs.

The honest reading is that a single-seed Fourier+FFN number is not a reproducibility target
on this sample: the spread between two correct implementations exceeds the effect being
measured. If that cell matters, both sides need a seed ensemble (10-20 seeds, report the
distribution), and the comparison should be between distributions, not between two draws.
Until then, only the OU rows carry a claim.

## A-4 What the run itself got right

Worth recording separately from the numbers: the specification was carried out as written,
and the cross-check the spec asked for (headline weights × residual returns against the
package's own accounting) caught two real bugs in the run before the final table — factor
legs built from the previous session's loadings, and `PanelWindow.latest()` handing stale
loadings to names with no row on the decision day (`FINDINGS.md` F-019, F-020). The
determinism claim holds. The run's own `DEVIATIONS_spec.md` lists every fill-in the
specification left open, including the ones that matter most: what counts as a
"characteristic column", per-batch versus per-window Sharpe, and the 30-consecutive-session
rule in A-2.
