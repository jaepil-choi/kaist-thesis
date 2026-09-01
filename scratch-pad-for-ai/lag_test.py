"""Is the vqapr testbed's sign flip on the OU strategy explained by its one-session
implementation lag? Re-runs the paper's non-trainable OU threshold rule on the
replication's own residual panels, with and without a one-session delay.

Weights are L1-normalised on the residual side (||w^R||_1 = 1), which is not exactly the
replication's asset-side normalisation, so levels differ slightly from the published table;
the baseline-vs-lag contrast is the point.
"""
import numpy as np
import pandas as pd
import pathlib

BASE = pathlib.Path("guijarro-ordonez-2025-replication/outputs")
PANELS = {
    "PCA5": BASE / "pca/daily_residuals_k5_20200102_c252_l60.parquet",
    "FF5":  BASE / "fama-french/daily_residuals_ff5_20200102_l60.parquet",
}
L, C_THRESH, C_CRIT = 30, 1.25, 0.25


def ou_weights(win):                      # win: (L, N) residuals, oldest first
    X = np.cumsum(win, axis=0)
    x0, x1 = X[:-1], X[1:]
    mx, my = x0.mean(0), x1.mean(0)
    cx = x0 - mx
    sxx = (cx * cx).sum(0)
    sxy = (cx * (x1 - my)).sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        b = np.where(sxx > 0, sxy / sxx, np.nan)
        a = my - b * mx
        res = x1 - (a + b * x0)
        sse = (res * res).sum(0)
        sst = ((x1 - my) ** 2).sum(0)
        r2 = np.where(sst > 0, 1 - sse / sst, np.nan)
        sigma = np.sqrt((sse / max(len(x0) - 2, 1)) / (1 - b * b))
        s = (X[-1] - a / (1 - b)) / sigma
    ok = np.isfinite(s) & np.isfinite(r2) & (b > 0) & (b < 1) & (sigma > 0) & (r2 > C_CRIT)
    w = np.where(ok & (s < -C_THRESH), 1.0, 0.0) - np.where(ok & (s > C_THRESH), 1.0, 0.0)
    g = np.abs(w).sum()
    return w / g if g else w


def run(name, path):
    df = pd.read_parquet(path)
    piv = df.pivot(index="date", columns="ticker", values="residual").sort_index()
    R = piv.to_numpy(dtype=float)
    obs = ~np.isnan(R)
    R0 = np.nan_to_num(R)
    dates = piv.index
    out = []
    for lag in (0, 1):
        rets, ds = [], []
        for t in range(L + lag, len(dates)):
            lo, hi = t - L - lag, t - lag          # window ends `lag` sessions early
            win = R0[lo:hi]
            valid = obs[lo:hi].all(0) & obs[t]
            w = np.zeros(R.shape[1])
            w[valid] = ou_weights(win[:, valid])
            rets.append(float(w @ R0[t]))
            ds.append(dates[t])
        s = pd.Series(rets, index=pd.DatetimeIndex(ds))
        for tag, sub in (("full-OOS(24-01-19~)", s[s.index >= "2024-01-19"]),
                         ("2024-only", s[s.index.year == 2024])):
            mu, sd = sub.mean() * 252, sub.std(ddof=1) * np.sqrt(252)
            out.append(dict(panel=name, lag=lag, window=tag, n=len(sub),
                            sharpe=mu / sd, ann_mu_pct=mu * 100, ann_sd_pct=sd * 100))
    return out


if __name__ == "__main__":
    rows = [r for k, p in PANELS.items() for r in run(k, p)]
    pd.set_option("display.width", 160, "display.float_format", lambda v: f"{v:8.3f}")
    print(pd.DataFrame(rows).to_string(index=False))
