"""2024-only slice of the guijarro replication's OU-threshold runs, for comparison
with the vqapr testbed's 2024 pilot. Reads daily_performance.csv, no side effects."""
import pandas as pd
import numpy as np
import pathlib

base = pathlib.Path("guijarro-ordonez-2025-replication/outputs/strategies")
runs = {
    "K0 (pca0)": "pca0_ou_threshold_sharpe_lb30_e100_rolling_no-cost",
    "PCA5":      "pca5_ou_threshold_sharpe_lb30_e100_rolling_no-cost",
    "FF5":       "ff5_ou_threshold_sharpe_lb30_e100_rolling_no-cost",
    "PCA1":      "pca1_ou_threshold_sharpe_lb30_e100_rolling_no-cost",
    "FF1":       "ff1_ou_threshold_sharpe_lb30_e100_rolling_no-cost",
    "FF3":       "ff3_ou_threshold_sharpe_lb30_e100_rolling_no-cost",
}
rows = []
for label, d in runs.items():
    df = pd.read_csv(base / d / "daily_performance.csv", parse_dates=["date"])
    for tag, sub in (("full-OOS", df), ("2024-only", df[df.date.dt.year == 2024])):
        r = sub["return"].to_numpy()
        mu, sd = r.mean() * 252, r.std(ddof=1) * np.sqrt(252)
        nav = (1 + r).cumprod()
        dd = (nav / np.maximum.accumulate(nav) - 1).min()
        rows.append(dict(strategy=label, window=tag, n=len(r), sharpe=mu / sd,
                         ann_mu_pct=mu * 100, ann_sd_pct=sd * 100,
                         total_pct=(nav[-1] - 1) * 100, maxdd_pct=dd * 100,
                         turnover=sub["turnover"].mean(),
                         short_prop=sub["short_proportion"].mean()))
out = pd.DataFrame(rows)
pd.set_option("display.width", 200, "display.float_format", lambda v: f"{v:8.3f}")
print(out.to_string(index=False))
