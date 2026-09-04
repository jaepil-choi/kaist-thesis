"""Does each implementation's residual-to-asset weight map earn what that implementation reports?

Two sources are checked, against the same standard: the book you hold must earn the return that is
reported for it. Section 1 is the PCA low-rank map in this repo's replication, section 2 is the
Fama-French factor-leg map in the vqapr scenario testbed.

Section 1 -- the replication's PCA map (the defect).

The authors' code (`Deep_Learning_Statistical_Arbitrage_Code/factor_models/pca.py`,
`simulation.py`):

    factor portfolio weights  S = eigenvectors / vol        ("standardized eigenvectors")
    return loadings           B = OLS(returns ~ factors)
    residual                  eps = r - B (S' r)            so  Phi = I - B S'  and  eps = Phi r
    composition matrix        comp_mtx = (I - S B').T = Phi          (pca.py saves with `.T`)
    asset weights             aw = w' comp_mtx = Phi' w = (I - S B') w   (simulation.py:81)

The replication (`guijarro-ordonez-2025-replication`) stores left = S, right = B and computes
in `trading.py:low_rank_asset_weights`

    aw = w - right @ (left' w) = (I - B S') w = Phi w

which is Phi, not Phi' -- the transpose of the authors' map, and of that function's own docstring
("Apply Phi=I-left@right.T", i.e. I - S B', which is the authors' map).

The test needs no policy weights and no matrix inversion, because the two maps have different
ranges. Phi x = 0 exactly when x is in span(B), so col(Phi) is the orthogonal complement of
span(S), and col(Phi') is the orthogonal complement of span(B):

    aw = Phi  w   =>   S' aw = 0     (the replication's map)
    aw = Phi' w   =>   B' aw = 0     (the authors' map)

So project the saved asset weights onto both bases and see which one they annihilate. The reported
ratio is || X' aw || / (|| X ||_2 || aw ||_2), which is 0 for an exact annihilation and O(1) for a
generic vector.

Section 2 -- the testbed's Fama-French map (the control).

A Fama-French residual portfolio is +1 in the stock and -beta in each factor leg, so the testbed's
weight table already carries both, and the identity to check is direct: the book's weights against
realized excess returns must equal the reported headline, which is weights against residuals. This
is the same standard section 1 applies, on a path the defect does not touch.

Run: uv run python scratch-pad-for-ai/enhanced-index/check_composition_maps.py
Optional: GJC_RUN=<comma-separated strategy dir names> to test other PCA runs.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(os.environ.get("KAIST_THESIS_ROOT", Path(__file__).resolve().parents[2]))
GJC = ROOT / "guijarro-ordonez-2025-replication" / "outputs"
TB = ROOT / "vqapr-scenario-testbed"
OUT = ROOT / "scratch-pad-for-ai" / "outputs" / "enhanced-index"
OUT.mkdir(parents=True, exist_ok=True)
RUNS = os.environ.get("GJC_RUN", "pca5_cnn_transformer_sharpe_lb30_e100_constant_no-cost,"
                                 "pca5_ou_threshold_sharpe_lb30_e100_rolling_no-cost,"
                                 "pca5_fourier_ffn_sharpe_lb30_e100_rolling_no-cost").split(",")
K, ANN = 5, 252
S_COLS = [f"standardized_eigenvector_{k + 1}" for k in range(K)]
B_COLS = [f"return_loading_{k + 1}" for k in range(K)]

load = pd.read_parquet(GJC / f"pca/daily_low_rank_loadings_k{K}_20200102_c252_l60.parquet").set_index(["date", "ticker"]).sort_index()
resid = pd.read_parquet(GJC / f"pca/daily_residuals_k{K}_20200102_c252_l60.parquet").set_index(["date", "ticker"]).sort_index()

# the excess-return panel the PCA was fed: price return minus the daily CD91 rate
px = pd.read_parquet(TB / "data/korean_equity/adjusted_prices.parquet", columns=["date", "ticker", "return"])
R = px[px.date >= "2019-01-01"].pivot(index="date", columns="ticker", values="return").sort_index()
rows = json.load(open(TB / "data/ecos/rf_cd_91d_daily_20150101_20260720.json", encoding="utf-8"))["rows"]
cd = pd.DataFrame({"date": pd.to_datetime([r["TIME"] for r in rows], format="%Y%m%d"),
                   "cd91": [float(r["DATA_VALUE"]) for r in rows]}).sort_values("date")
cd["rf"] = (1 + cd.cd91 / 100) ** (1 / ANN) - 1
rf = pd.merge_asof(pd.DataFrame({"date": R.index}), cd[["date", "rf"]], on="date", direction="backward").set_index("date").rf
XS = R.sub(rf, axis=0)

# ================================================================ 1. the replication's PCA low-rank map
# ---------------------------------------------------------------- do the saved loadings mean what the authors' code means?
print("Sanity: does  eps == r - B (S' r)  hold on the saved loadings?  (r = price return - rf)")
for i in [1100, 1300, 1500]:
    day = resid.index.get_level_values(0).unique()[i]
    ld, rd = load.loc[day], resid.loc[day]
    n = ld.index
    S, B = ld[S_COLS].to_numpy(), ld[B_COLS].to_numpy()
    r = XS.reindex(index=[day], columns=n).to_numpy().ravel()
    eps = rd.loc[n, "residual"].to_numpy()
    print("   %s  %3d names   max |(I - B S') r - eps| = %.3e   (max |eps| = %.3e)"
          % (day.date(), len(n), np.abs((r - B @ (S.T @ r)) - eps).max(), np.abs(eps).max()))

# ---------------------------------------------------------------- which map produced the saved weights?
summary = []
for run in RUNS:
    aw = pd.read_parquet(GJC / f"strategies/{run}/daily_asset_weights.parquet")
    perf = pd.read_csv(GJC / f"strategies/{run}/daily_performance.csv", parse_dates=["date"]).set_index("date")["return"]
    rec = []
    for day in aw.index:
        ld = load.loc[day]
        names = [t for t in ld.index if t in set(aw.columns)]
        S, B = ld.loc[names, S_COLS].to_numpy(), ld.loc[names, B_COLS].to_numpy()
        a = aw.loc[day, names].to_numpy()
        na = np.linalg.norm(a)
        r = np.nan_to_num(XS.reindex(index=[day], columns=names).to_numpy().ravel())
        rec.append({
            "date": day,
            "S_test": float(np.linalg.norm(S.T @ a) / (np.linalg.norm(S, 2) * na)),
            "B_test": float(np.linalg.norm(B.T @ a) / (np.linalg.norm(B, 2) * na)),
            "aw_dot_r": float(a @ r),
            "reported": float(perf.get(day, np.nan)),
        })
    d = pd.DataFrame(rec).set_index("date")
    sr = lambda s: (s.mean() * ANN, s.mean() * ANN / (s.std(ddof=1) * np.sqrt(ANN)))
    print(f"\n=== {run}")
    print("   S' aw == 0 ?  (aw = Phi  w, the replication's map): median %.2e   max %.2e" % (d.S_test.median(), d.S_test.max()))
    print("   B' aw == 0 ?  (aw = Phi' w, the authors' map)     : median %.2e   max %.2e" % (d.B_test.median(), d.B_test.max()))
    print("   reported return          ann %7.4f  SR %6.3f" % sr(d.reported))
    print("   saved weights x returns  ann %7.4f  SR %6.3f  (corr with reported %.4f)" % (*sr(d.aw_dot_r), d.aw_dot_r.corr(d.reported)))
    d.to_csv(OUT / f"check_pca_composition_{run}.csv")
    summary.append({"run": run.replace("_no-cost", ""), "S'aw (repl. map)": d.S_test.median(),
                    "B'aw (authors' map)": d.B_test.median(), "reported SR": sr(d.reported)[1],
                    "saved-book SR": sr(d.aw_dot_r)[1]})
print("\n" + pd.DataFrame(summary).to_markdown(index=False, floatfmt=".3g"))


# ================================================================ 2. the testbed's Fama-French factor-leg map
# A Fama-French residual portfolio is +1 in the stock and -beta in each factor leg, so the testbed's
# weight table already carries both legs and the check is direct: recompute what the book earns from
# the vendor files and compare it with the testbed's reported headline (weights x residuals).
TB_ROWS = ["ou_k0", "ffn_k0", "ou_k1", "ffn_k1", "ou_k3", "ffn_k3", "ou_k5", "ffn_k5"]
FACTORS = ["RMRF", "SMB", "HML", "RMW", "CMA"]
DIAG = TB / "work/out/diagnostics"
if not DIAG.is_dir():
    print("\n(testbed diagnostics not present; skipping section 2)")
else:
    fr = pd.read_csv(TB / "data/factors/daily_factor_returns.csv")
    fr = fr[(fr.weight == "vw") & (fr.frequency == "daily")]
    FR = fr.assign(date=pd.to_datetime(fr.date)).set_index("date")[FACTORS].astype(float)
    sessions = XS.index
    nxt = dict(zip(sessions[:-1], sessions[1:]))
    print("\n=== testbed Fama-French books: does (weights x realized returns) equal the reported headline?")
    tb_rows = []
    for row in TB_ROWS:
        w = pd.read_parquet(DIAG / f"{row}_weights.parquet")
        w["date"] = pd.to_datetime(w.date)
        piv = w.pivot(index="date", columns="instrument", values="weight").fillna(0.0)
        legs = piv.reindex(columns=FACTORS, fill_value=0.0)
        stk = piv[[c for c in piv.columns if c not in FACTORS]]
        decisions = [d for d in stk.index if d in nxt]
        rd = [nxt[d] for d in decisions]
        earned = ((stk.loc[decisions].to_numpy() * XS.reindex(index=rd, columns=stk.columns).fillna(0.0).to_numpy()).sum(1)
                  + (legs.loc[decisions].to_numpy() * FR.reindex(rd).fillna(0.0).to_numpy()).sum(1))
        rep = pd.read_csv(DIAG / f"{row}_daily.csv", parse_dates=["date"]).set_index("date")
        got = pd.Series(earned, index=pd.DatetimeIndex(rd)).reindex(rep.index)
        diff = (got - rep.ret_headline).abs()
        tb_rows.append({"row": row,
                        "max |diff|": diff.max(),
                        "max |diff| where the residual is present": diff[rep.n_missing_resid == 0].max(),
                        "days with a missing residual": int((rep.n_missing_resid > 0).sum())})
    print(pd.DataFrame(tb_rows).to_markdown(index=False, floatfmt=".2e"))
    print("Rows whose residuals are all present agree to float precision, so the testbed's map is the")
    print("authors' convention. The remaining days are the documented encoding of a missing residual")
    print("as zero (testbed DEPARTURES D-09), not a mapping error.")
