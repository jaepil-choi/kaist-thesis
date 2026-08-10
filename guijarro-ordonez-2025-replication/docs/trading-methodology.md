# Trading-policy methodology and Korean execution contract

## Classification

This implementation follows the equations and public source code of
Guijarro-Ordonez, Pelger, and Zanotti (2025). It is **not an exact U.S. result
replication**. The executable branches use Korean K=5 rolling PCA and Korean
FF1/FF3/FF5 residuals and are **Korean price-return replication variants**.

The distinction is material:

- the local adjusted return excludes cash dividends and is not total return;
- the Korean residual sample is 2020-01-02 through 2026-07-20;
- the first policy OOS date is 2024-01-19 because the first 1,000 residual days
  are reserved for training;
- exact 240-month IPCA is unavailable in the 139-month characteristic history;
- bid-ask, historical shortability, and observed borrow-cost panels are absent.

Every simulation audit preserves these differences. They must also remain in
table and figure captions.

## Signal timing

For residual return $\epsilon_{n,t}$, the day-$t$ model input contains only
days $t-L$ through $t-1$:

$$
x_{n,t-1}=\left(\epsilon_{n,t-L},
\sum_{j=0}^{1}\epsilon_{n,t-L+j},\ldots,
\sum_{j=0}^{L-1}\epsilon_{n,t-L+j}\right).
$$

The benchmark uses $L=30$. A residual is eligible only if all 30 historical
observations are present and nonzero, matching the public
`compute_nonmissing_indices` convention. The return on day $t$ is never part of
the signal for day $t$.

The Fourier benchmark applies an RFFT to the same cumulative path. It packs
the 16 real coefficients followed by the 14 interior imaginary coefficients,
preserving a 30-dimensional input.

## Trading policies

### CNN + Transformer

The published architecture uses:

- two causal one-dimensional convolutions in one residual block;
- one to eight channels, kernel size two, and a three-day receptive field;
- instance normalization, ReLU, and a normalized-input residual connection;
- an eight-dimensional Transformer encoder with four attention heads, a
  16-unit feedforward layer, and 0.25 dropout;
- a final linear map from the last time position to one residual weight.

The local class has 769 trainable parameters. Injecting identical parameters
into the public and local classes produced maximum absolute output difference
`0.0` in the implementation check.

### Fourier + FFN

The network maps 30 packed Fourier features through widths 30, 16, 8, and 4
with ReLU and 0.25 dropout, then returns one linear allocation weight.

### OU + threshold

The nontrainable benchmark fits an AR(1) representation to each 30-day
cumulative path. It trades only when $0<\beta<1$, innovation volatility is
positive, $R^2>0.25$, and the normalized mean-reversion signal exceeds
$\lvert1.25\rvert$. Output is in $\{-1,0,1\}$.

## Residual-to-asset mapping

For PCA, the saved low-rank representation reconstructs

$$\Phi_t=I-A_tB_t^\top.$$

For raw residual allocations $w_{\epsilon,t}$, underlying asset weights are
computed without materializing the dense matrix:

$$
\widetilde w_{R,t}=w_{\epsilon,t}-(w_{\epsilon,t}A_t)B_t^\top.
$$

Both residual and asset weights are divided by
$\lVert\widetilde w_{R,t}\rVert_1$. The executable underlying portfolio has
unit gross exposure and $r_{p,t}=w_{\epsilon,t}^{\top}\epsilon_t$. Turnover is
the L1 change in underlying asset weights. Short allocation is the absolute
sum of negative underlying weights.

For Korean Fama-French residuals, the 60-day no-intercept regression produces
$\epsilon_t=r_t-\beta_t f_t$ and the composition is $[I\mid-\beta_t]$.
The added factor legs are synthetic factor portfolios, not observed ETFs; this
is explicitly recorded in the residual audit.

## Optimization and rolling evaluation

The main-paper contract is:

- random seed 0;
- Adam with learning rate 0.001;
- 100 epochs and no early stopping;
- batches of 125 trading days;
- 1,000-day rolling training window;
- 125-day OOS stride and rolling retraining;
- one-day holding period.

The multi-holding branch reproduces the public `get_holding_days_returns`
contract: a day-$t$ portfolio is evaluated over $B$ days, compounded, divided
by $B$, and the $B$-lag turnover charge is divided by $B$. The public code's
leading $B$ zeros are preserved. Figure 12 Panel B still requires a separately
trained multi-day policy rather than relabeling the one-day policy.

The Sharpe objective minimizes negative annualized Sharpe. The mean-variance
objective minimizes the negative of annualized mean minus annualized
volatility. Like the public code, optimization proceeds sequentially on each
125-day batch, not on one loss over all 1,000 days.

The public `*-replication.yaml` files use `rolling_retrain: false` to replay
supplied pretrained checkpoints. The full configurations and paper use rolling
retraining, so the Korean implementation defaults to `true`.

Each completed epoch is checkpointed by subperiod. Re-running an interrupted
command resumes with the saved model and optimizer state.

## Costs and inference limits

The friction objective subtracts

$$
c_{\mathrm{trade}}\lVert w_{R,t}-w_{R,t-1}\rVert_1
+c_{\mathrm{short}}\sum_i\lvert\min(w_{R,t,i},0)\rvert.
$$

The paper uses 5 bps per transaction side and 1 bp per short position per day.
Applying these constants is a sensitivity, not validation against Korean
realized costs. Exact Korean friction claims remain blocked until bid-ask,
shortability, and borrow-cost histories are supplied.

The friction-aware CNN consumes the previous residual allocation through the
published weight-conditioned attention block. Training preserves the public
epoch/batch update convention for lagged weights; inference propagates the
previous raw allocation sequentially. A mechanically post-costed no-friction
strategy is kept separate from a policy retrained with costs in its objective.

Appendix C.5 additionally uses a direct 30-input FFN and an OU-feature FFN. The
latter uses $(\beta,\mu_{OU},\sigma_{OU},R^2)$ as the four-dimensional signal and
three 4-unit sigmoid layers, following the paper text. The authors did not
release this ablation class, so the exact private preprocessing helper cannot
be code-compared and this limitation is recorded in the appendix audit.

## Commands

From the repository root:

```powershell
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model ou_threshold
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model fourier_ffn
uv run python guijarro-ordonez-2025-replication/run.py simulate-pca --simulation-model cnn_transformer
uv run python guijarro-ordonez-2025-replication/run.py estimate-fama-french --ff-factors 5
uv run python guijarro-ordonez-2025-replication/run.py simulate-fama-french --ff-factors 5 --simulation-model ou_threshold
uv run python guijarro-ordonez-2025-replication/run.py report-pca
uv run python guijarro-ordonez-2025-replication/run.py build-spec-outputs
uv run python guijarro-ordonez-2025-replication/run.py build-robustness
uv run python guijarro-ordonez-2025-replication/run.py build-risk-premium
uv run python guijarro-ordonez-2025-replication/run.py build-appendix
uv run python guijarro-ordonez-2025-replication/run.py build-appendix-signals
uv run python guijarro-ordonez-2025-replication/run.py run-model-selection
```

`--simulation-objective meanvar`, `--simulation-lookback-days 60`, and
`--simulation-constant-model` select the corresponding variations. Any run
with fewer than 100 epochs is a pilot and must not enter paper tables.
