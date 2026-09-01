"""K=0 arm of the lag test: same OU rule, residual = stock excess return.

Uses the vqapr testbed's excess-return panel restricted to the replication's own
228-ticker / 606-session out-of-sample grid, so the only thing varying is the
one-session implementation lag.
"""
import numpy as np
import pandas as pd
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path("scratch-pad-for-ai")))
from lag_test import ou_weights, L

w_ref = pd.read_parquet(
    "guijarro-ordonez-2025-replication/outputs/strategies/"
    "pca0_ou_threshold_sharpe_lb30_e100_rolling_no-cost/daily_asset_weights.parquet")
tickers = list(w_ref.columns)

panel = pd.read_parquet("vqapr-final-testbed/build/panel/krx_daily.parquet",
                        columns=["session_date", "instrument", "excess_return"])
panel = panel[panel.instrument.isin(tickers)]
piv = panel.pivot(index="session_date", columns="instrument",
                  values="excess_return").sort_index()

# Restrict to the cross-section the replication actually selected each day: the PCA
# residual panel carries one row per (date, selected ticker), median 176 of the 228.
sel = pd.read_parquet("guijarro-ordonez-2025-replication/outputs/pca/"
                      "daily_residuals_k5_20200102_c252_l60.parquet")
mask = sel.pivot(index="date", columns="ticker", values="return_observed")
piv = piv.reindex(index=mask.index, columns=mask.columns)
R = piv.to_numpy(dtype=float)
obs = (~np.isnan(R)) & mask.fillna(False).to_numpy().astype(bool)
R0 = np.nan_to_num(R)
R0[~obs] = 0.0
dates = piv.index

rows = []
for lag in (0, 1):
    rets, ds = [], []
    for t in range(L + lag, len(dates)):
        win, valid = R0[t - L - lag:t - lag], obs[t - L - lag:t - lag].all(0) & obs[t]
        w = np.zeros(R.shape[1])
        w[valid] = ou_weights(win[:, valid])
        rets.append(float(w @ R0[t]))
        ds.append(dates[t])
    s = pd.Series(rets, index=pd.DatetimeIndex(ds))
    for tag, sub in (("full-OOS(24-01-19~)", s[s.index >= "2024-01-19"]),
                     ("2024-only", s[s.index.year == 2024])):
        mu, sd = sub.mean() * 252, sub.std(ddof=1) * np.sqrt(252)
        rows.append(dict(panel="K0", lag=lag, window=tag, n=len(sub),
                         sharpe=mu / sd, ann_mu_pct=mu * 100, ann_sd_pct=sd * 100))
pd.set_option("display.width", 160, "display.float_format", lambda v: f"{v:8.3f}")
print(pd.DataFrame(rows).to_string(index=False))
