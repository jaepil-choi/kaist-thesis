"""KOSPI 200 enhanced index from the DLSA long-short books, without derivatives.

Takes the daily strategy weights of the vqapr scenario testbed's run 3 (the Fama-French arm,
K in {0,1,3,5} x {OU+Thresh, Fourier+FFN}), puts each book on top of the KOSPI 200 benchmark as an
active overlay, and measures what an index fund would have earned over the benchmark.

The replication's PCA books were included until 2026-09-04, when the low-rank residual-to-asset
weight map was found to be transposed (guijarro-ordonez-2025-replication/docs/issues/
pca-composition-matrix-transposed.md). The code there is fixed but the stored PCA artifacts are
not, so the PCA rows are out until those runs are redone. Restore them by putting the "rep:"
entries back in ROWS -- the loader still handles them.

The fund holds (1 - SLEEVE) of the benchmark directly and SLEEVE through a KOSPI 200 ETF. It may not
short (a name's active weight is at most its direct holding), may not lever, and holds no futures --
the ETF sleeve is the only instrument that absorbs whatever net exposure the clipped book carries.
Two ways to live with that, which is the comparison this script exists for:

  F  etf-sleeve      the book as it comes. The ETF absorbs the DOLLAR net (etf = SLEEVE - sum a), so
                     the residual market exposure of the active position is sum a_i (beta_i - 1),
                     which is not zero: a residual-reversal book buys low-beta names and sells
                     high-beta ones. The fund's beta drifts below 1.
  G  etf + beta-neutral   the book is tilted, inside the names it already holds, until
                     sum a_i (beta_i - 1) = 0. Then the single ETF instrument satisfies both the
                     budget and beta neutrality at once, with no futures. The tilt is the minimum
                     L2 adjustment along (beta - 1), re-clipped and iterated.

Reference variants, kept for continuity; each needs an instrument the fund does not have:
  A  paper-book   the book as the paper defines it (stocks + factor legs), scaled by lambda.
  B  ls-futures   stocks + the RMRF leg as a KOSPI 200 futures position; shorts allowed.
  C  long-only    B, clipped, with the clipped notional offset by futures.
  D  bm-scaled    active weight proportional to BM weight x signal, dollar-neutral via futures.
  E  long-only balanced   C's clipping, longs scaled down to the retained shorts; hedge scaled too.

Costs: 3 bp per buy, 3 bp + 20 bp tax per sell on the active stock trades; 3 bp each way on the ETF.
The benchmark's own maintenance trades are common to any index fund and are ignored.

Timing: weights decided at session d's close, filled at that close, earning session d+1. Benchmark
weights are the KOSPI 200 float-adjusted index weights at d's close. Betas are 60-session no-intercept
OLS of the name's excess return on the benchmark's, estimated through d.

Inputs (override with env vars):
  KAIST_THESIS_ROOT  repo root                      (default: two levels above this file)
  KWAM_EI_DATA       kwam-enhanced-index/data       (default: <root>/../kwam-enhanced-index/data)
Outputs: <root>/scratch-pad-for-ai/outputs/enhanced-index/
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.environ.get("KAIST_THESIS_ROOT", Path(__file__).resolve().parents[2]))
KW = Path(os.environ.get("KWAM_EI_DATA", ROOT.parent / "kwam-enhanced-index" / "data"))
TB = ROOT / "vqapr-scenario-testbed"
REP = ROOT / "guijarro-ordonez-2025-replication" / "outputs" / "strategies"
OUT = ROOT / "scratch-pad-for-ai" / "outputs" / "enhanced-index"
OUT.mkdir(parents=True, exist_ok=True)

FACTORS = ["RMRF", "SMB", "HML", "RMW", "CMA"]
# (key, label, source). "tb" = testbed run 3 diagnostics, indexed by DECISION date.
# "rep:<run>" = replication daily_asset_weights, indexed by RETURN date (shifted back one session).
ROWS = [
    ("ou_k0", "OU + Thresh, FF K=0", "tb"),
    ("ffn_k0", "Fourier + FFN, FF K=0", "tb"),
    ("ou_k1", "OU + Thresh, FF K=1", "tb"),
    ("ffn_k1", "Fourier + FFN, FF K=1", "tb"),
    ("ou_k3", "OU + Thresh, FF K=3", "tb"),
    ("ffn_k3", "Fourier + FFN, FF K=3", "tb"),
    ("ou_k5", "OU + Thresh, FF K=5", "tb"),
    ("ffn_k5", "Fourier + FFN, FF K=5", "tb"),
    # PCA rows withheld -- see the module docstring:
    # ("pca5_ou", "OU + Thresh, PCA K=5", "rep:pca5_ou_threshold_sharpe_lb30_e100_rolling_no-cost"),
    # ("pca5_ffn", "Fourier + FFN, PCA K=5", "rep:pca5_fourier_ffn_sharpe_lb30_e100_rolling_no-cost"),
    # ("pca5_cnn", "CNN+Transformer, PCA K=5", "rep:pca5_cnn_transformer_sharpe_lb30_e100_constant_no-cost"),
]
FIG_ROWS = [key for key, _, _ in ROWS]
VARIANTS = ["A paper-book", "B ls-futures", "C long-only", "D bm-scaled", "E long-only balanced",
            "F etf-sleeve", "G etf + beta-neutral"]
FREE_OF_DERIVATIVES = ["F etf-sleeve", "G etf + beta-neutral"]
LAMBDAS = [0.1, 0.2, 0.3, 0.5, 1.0]
LAMBDA_MAIN = 0.3
CAP = 0.10
SLEEVE = 0.20   # share of the benchmark replication held through a KOSPI 200 ETF (variants F, G)
BUY_BP, SELL_BP, TAX_BP = 3, 3, 20
ETF_BP = 3      # ETF buy and sell, no transaction tax
BETA_WINDOW = 60
OOS_START, OOS_END = pd.Timestamp("2024-01-19"), pd.Timestamp("2026-07-20")
ANN = 252
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

# ------------------------------------------------------------------ inputs
px = pd.read_parquet(TB / "data/korean_equity/adjusted_prices.parquet", columns=["date", "ticker", "return"])
px = px[px.date >= "2023-06-01"]
R = px.pivot(index="date", columns="ticker", values="return").sort_index()  # price returns, NaN = no row
sessions = R.index
R0 = R.fillna(0.0)  # a name with no row that day earns 0 (position flat), in the BM and the overlay alike

with open(TB / "data/ecos/rf_cd_91d_daily_20150101_20260720.json", encoding="utf-8") as fh:
    rows = json.load(fh)["rows"]
cd = pd.DataFrame({"date": pd.to_datetime([r["TIME"] for r in rows], format="%Y%m%d"),
                   "cd91": [float(r["DATA_VALUE"]) for r in rows]}).sort_values("date")
cd["rf"] = (1 + cd.cd91 / 100) ** (1 / ANN) - 1
rf = pd.merge_asof(pd.DataFrame({"date": sessions}), cd[["date", "rf"]], on="date", direction="backward").set_index("date").rf

fr = pd.read_csv(TB / "data/factors/daily_factor_returns.csv")
fr = fr[(fr.weight == "vw") & (fr.frequency == "daily")]
F = fr.assign(date=pd.to_datetime(fr.date)).set_index("date")[FACTORS].astype(float)

mem = pd.read_parquet(KW / "preprocessed/k200_members.parquet")
mem = mem[mem.date >= "2023-06-01"]
WBM = mem.pivot(index="date", columns="ticker", values="index_weight").reindex(sessions).fillna(0.0)
assert (WBM.sum(axis=1).between(0.99, 1.01)).all(), "BM weights do not sum to one"

nxt = dict(zip(sessions[:-1], sessions[1:]))
bm_ret_by_decision = pd.Series({d: float((WBM.loc[d] * R0.loc[nxt[d]]).sum()) for d in sessions[:-1]})  # earned at d+1
bm_ret_on_day = pd.Series({nxt[d]: v for d, v in bm_ret_by_decision.items()})  # indexed by the return day

# ------------------------------------------------------------------ betas to the benchmark
# 60-session no-intercept OLS of each name's excess return on the benchmark's, through d.
xs_stock = R0.sub(rf, axis=0)
xs_bm = (bm_ret_on_day.reindex(sessions).fillna(0.0) - rf)
obs = R.notna().astype(float)
num = xs_stock.mul(xs_bm, axis=0).rolling(BETA_WINDOW).sum()
den = (xs_bm ** 2).rolling(BETA_WINDOW).sum()
BETA = num.div(den, axis=0)
BETA = BETA.where(obs.rolling(BETA_WINDOW).sum() >= 40, 1.0).fillna(1.0)
print("beta panel: median %.3f  5/95 pct %.2f/%.2f" % (BETA.stack().median(), BETA.stack().quantile(.05), BETA.stack().quantile(.95)))


def load_book(key: str, source: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (stock weights, factor-leg weights), both indexed by DECISION date."""
    if source == "tb":
        w = pd.read_parquet(TB / f"work/out/diagnostics/{key}_weights.parquet")
        w["date"] = pd.to_datetime(w.date)
        piv = w.pivot(index="date", columns="instrument", values="weight").fillna(0.0)
    else:
        piv = pd.read_parquet(REP / source.split(":", 1)[1] / "daily_asset_weights.parquet")
        piv.columns = [c.replace("FACTOR::", "") for c in piv.columns]
        prev = {d: sessions[i - 1] for d in piv.index if (i := sessions.get_loc(d)) > 0}
        piv = piv.loc[list(prev)].rename(index=prev)  # the replication stamps the return date
    fac = piv.reindex(columns=FACTORS, fill_value=0.0)
    stk = piv[[c for c in piv.columns if c not in FACTORS]]
    return stk, fac


def metrics(excess: pd.Series, cost: pd.Series, cost_notax: pd.Series, trades_abs: pd.Series, extra: dict) -> dict:
    gross, net = excess, excess - cost
    cum = net.cumsum()
    monthly = net.groupby(net.index.to_period("M")).sum()
    te = float(net.std(ddof=1) * np.sqrt(ANN))
    te_g = float(gross.std(ddof=1) * np.sqrt(ANN))
    oneway = float(trades_abs.mean() * ANN / 2)
    net_notax = excess - cost_notax
    return {
        "excess_gross_pct": float(gross.mean() * ANN * 100),
        "cost_pct": float(cost.mean() * ANN * 100),
        "excess_net_pct": float(net.mean() * ANN * 100),
        "excess_net_notax_pct": float(net_notax.mean() * ANN * 100),
        "te_pct": te * 100,
        "te_gross_pct": te_g * 100,
        "ir_gross": float(gross.mean() * ANN / te_g) if te_g > 0 else np.nan,
        "ir_net": float(net.mean() * ANN / te) if te > 0 else np.nan,
        "ir_net_notax": float(net_notax.mean() * ANN / (net_notax.std(ddof=1) * np.sqrt(ANN))) if net_notax.std() > 0 else np.nan,
        "breakeven_roundtrip_bp": float(gross.mean() * ANN / oneway * 1e4) if oneway > 0 else np.nan,
        "cum_net_pct": float(cum.iloc[-1] * 100),
        "mdd_net_pct": float((cum.cummax() - cum).max()) * 100,
        "hit_month_pct": float((monthly > 0).mean() * 100),
        "turnover_oneway_ann": oneway,
        **extra,
    }


def run_variant(variant: str, lam: float, stk: pd.DataFrame, fac: pd.DataFrame):
    decisions = [d for d in stk.index if d in nxt and OOS_START <= nxt[d] <= OOS_END]
    stk, fac = stk.loc[decisions], fac.loc[decisions]
    ret_days = [nxt[d] for d in decisions]
    Rn = R0.reindex(index=ret_days, columns=stk.columns, fill_value=0.0).to_numpy()  # earned at d+1
    rf_n = rf.reindex(ret_days).to_numpy()
    bm_n = bm_ret_by_decision.reindex(decisions).to_numpy()
    wbm = WBM.reindex(index=decisions, columns=stk.columns, fill_value=0.0).to_numpy()
    bta = BETA.reindex(index=decisions, columns=stk.columns).fillna(1.0).to_numpy()
    W = stk.to_numpy()
    h = lam * fac["RMRF"].to_numpy()

    if variant.startswith("D"):
        absmean = np.where(np.abs(W).sum(1) > 0, np.abs(W).sum(1) / np.maximum((W != 0).sum(1), 1), 1.0)
        raw = wbm * (W / absmean[:, None])
        scale = np.divide(np.abs(W).sum(1), np.abs(raw).sum(1), out=np.zeros(len(W)), where=np.abs(raw).sum(1) > 0)
        a = lam * raw * scale[:, None]
        h = np.zeros(len(W))
    else:
        a = lam * W

    etf = None
    if variant[0] in "ABCDE":
        if variant.startswith("A"):
            legs = (lam * fac.to_numpy() * F.reindex(ret_days).fillna(0.0).to_numpy()).sum(1)
            a_eff, fut = a, np.zeros(len(W))
            excess = (a_eff * (Rn - rf_n[:, None])).sum(1) + legs
        else:
            if variant.startswith("B"):
                a_eff, fut = a, h
            else:
                lo, hi = -wbm, np.maximum(CAP - wbm, 0.0)
                a_eff = np.clip(a, lo, hi)
                if variant.startswith("E"):
                    longs, shorts = np.clip(a_eff, 0, None), np.clip(a_eff, None, 0)
                    ratio = np.divide(-shorts.sum(1), longs.sum(1), out=np.ones(len(W)), where=longs.sum(1) > 0)
                    a_eff = longs * np.minimum(ratio, 1.0)[:, None] + shorts
                    kept = np.divide(np.abs(a_eff).sum(1), np.abs(a).sum(1), out=np.zeros(len(W)), where=np.abs(a).sum(1) > 0)
                    fut = h * kept
                else:
                    fut = (h - (a_eff.sum(1) - a.sum(1))) if variant.startswith("C") else -a_eff.sum(1)
            excess = (a_eff * (Rn - rf_n[:, None])).sum(1) + fut * (bm_n - rf_n)
    else:
        direct = (1 - SLEEVE) * wbm
        lo, hi = -direct, np.maximum(np.maximum(CAP, wbm) - direct, 0.0)
        a_eff = np.clip(a, lo, hi)
        if variant.startswith("G"):
            # tilt inside the held names until sum a_i (beta_i - 1) = 0; then the ETF, which is one
            # unit of beta per unit of dollar, settles the budget and the beta at the same time.
            dv = bta - 1.0
            for _ in range(8):
                gap = (a_eff * dv).sum(1)
                v = dv * (a_eff != 0)
                denom = (v * v).sum(1)
                step = np.divide(gap, denom, out=np.zeros(len(W)), where=denom > 0)
                a_eff = np.clip(a_eff - step[:, None] * v, lo, hi)
        longs, shorts = np.clip(a_eff, 0, None), np.clip(a_eff, None, 0)
        room = SLEEVE - shorts.sum(1)  # the longs may not sum to more ETF than the sleeve holds
        ratio = np.divide(room, longs.sum(1), out=np.ones(len(W)), where=longs.sum(1) > 0)
        a_eff = longs * np.minimum(ratio, 1.0)[:, None] + shorts
        etf = SLEEVE - a_eff.sum(1)
        fut = np.zeros(len(W))
        excess = (a_eff * (Rn - bm_n[:, None])).sum(1)

    # trades at each decision: target minus the previous target drifted by the day's returns
    Rd = R0.reindex(index=decisions, columns=stk.columns, fill_value=0.0).to_numpy()
    bm_d = bm_ret_on_day.reindex(decisions).fillna(0.0).to_numpy()
    prev = np.vstack([np.zeros((1, a_eff.shape[1])), a_eff[:-1]])
    trades = a_eff - prev * (1 + Rd) / (1 + bm_d)[:, None]
    buys, sells = np.clip(trades, 0, None).sum(1), np.clip(-trades, 0, None).sum(1)
    cost = buys * BUY_BP / 1e4 + sells * (SELL_BP + TAX_BP) / 1e4
    cost_notax = buys * BUY_BP / 1e4 + sells * SELL_BP / 1e4
    if etf is not None:  # the ETF leg trades too; its return equals the benchmark's, so no drift term
        etf_tr = np.abs(np.diff(np.concatenate([[SLEEVE], etf])))
        cost = cost + etf_tr * ETF_BP / 1e4
        cost_notax = cost_notax + etf_tr * ETF_BP / 1e4
        buys, sells = buys + etf_tr / 2, sells + etf_tr / 2

    idx = pd.DatetimeIndex(ret_days)
    xs = Rn - (bm_n if etf is not None else rf_n)[:, None]
    ex_long, ex_short = (np.clip(a_eff, 0, None) * xs).sum(1), (np.clip(a_eff, None, 0) * xs).sum(1)
    bm_x = bm_n - rf_n
    beta_book = (a_eff * bta).sum(1) + ((etf - SLEEVE) if etf is not None else fut)
    tc = [np.corrcoef(a[i][m], a_eff[i][m])[0, 1] for i in range(len(W))
          if (m := (a[i] != 0) | (a_eff[i] != 0)).sum() > 2 and a[i][m].std() > 0 and a_eff[i][m].std() > 0]
    net_dollar = a_eff.sum(1) + (lam * fac.to_numpy().sum(1) if variant.startswith("A") else fut)
    gross_eff, gross_a = np.abs(a_eff).sum(1), np.abs(a).sum(1)
    extra = {
        "active_beta": float(np.cov(excess, bm_x, ddof=1)[0, 1] / np.var(bm_x, ddof=1)),
        "beta_book_avg": float(beta_book.mean()),
        "beta_contrib_pct": float((beta_book * bm_x).mean() * ANN * 100),
        "net_dollar_avg": float(net_dollar.mean()),
        "active_gross_avg": float(gross_eff.mean()),
        "active_notional_kept": float(gross_eff.sum() / gross_a.sum()) if gross_a.sum() > 0 else np.nan,
        "transfer_coef": float(np.mean(tc)) if tc else np.nan,
        "nonbm_share_of_active": float((np.abs(a_eff) * (wbm == 0)).sum() / gross_eff.sum()) if gross_eff.sum() > 0 else np.nan,
        "excess_long_leg_pct": float(ex_long.mean() * ANN * 100),
        "excess_short_leg_pct": float(ex_short.mean() * ANN * 100),
        "excess_futures_legs_pct": float((excess - ex_long - ex_short).mean() * ANN * 100),
        "etf_weight_avg": float(np.mean(etf)) if etf is not None else np.nan,
        "etf_weight_min": float(np.min(etf)) if etf is not None else np.nan,
        "days_longs_scaled_pct": float(np.mean(np.minimum(ratio, 1.0) < 1 - 1e-9) * 100) if etf is not None else np.nan,
        "sessions": len(idx),
    }
    daily = pd.DataFrame({"excess_gross": excess, "cost": cost, "cost_notax": cost_notax,
                          "excess_net": excess - cost, "trades_abs": buys + sells,
                          "futures": fut, "active_gross": gross_eff}, index=idx)
    return daily, metrics(daily.excess_gross, daily.cost, daily.cost_notax, daily.trades_abs, extra)


# ------------------------------------------------------------------ run everything
records, series = [], {}
for key, label, source in ROWS:
    stk, fac = load_book(key, source)
    for variant in VARIANTS:
        for lam in LAMBDAS:
            daily, m = run_variant(variant, lam, stk, fac)
            records.append({"row": key, "label": label, "variant": variant, "lambda": lam, **m})
            series[(key, variant, lam)] = daily
    print("done", key)
res = pd.DataFrame(records)
res.to_csv(OUT / "results_all.csv", index=False)
pd.concat({f"{r}|{v}|{l}": s for (r, v, l), s in series.items()}, names=["key", "date"]).to_parquet(OUT / "daily_series.parquet")

# ------------------------------------------------------------------ sanity: A at lambda 1 vs the source's own Sharpe
SRC_SR: dict[str, float] = {}   # what each source reports for the same book, on its own accounting
for key, label, source in ROWS:
    if source != "tb":
        pf = pd.read_csv(REP / source.split(":", 1)[1] / "daily_performance.csv", parse_dates=["date"])["return"]
        SRC_SR[key] = float(pf.mean() * ANN / (pf.std(ddof=1) * np.sqrt(ANN)))
tb = pd.read_csv(TB / "work/out/table.csv")
tb["row"] = tb["row"].str.replace("FF ", "", regex=False)
chk = res[(res.variant == "A paper-book") & (res["lambda"] == 1.0)][["label", "ir_gross", "excess_gross_pct", "te_gross_pct"]].copy()
chk["src"] = chk.label.str.replace(" FF ", " ", regex=False).str.replace(", FF ", ", ", regex=False)
chk = chk.merge(tb[["row", "SR", "SR_legs"]], left_on="src", right_on="row", how="left").drop(columns=["row", "src"])
src_by_label = {l: SRC_SR[k] for k, l, sc in ROWS if sc != "tb"}
chk["SR_source_reported"] = chk.label.map(src_by_label).fillna(chk.SR_legs)
chk["ir_minus_source"] = chk.ir_gross - chk.SR_source_reported
chk.to_csv(OUT / "check_paper_book_vs_source.csv", index=False)

# ------------------------------------------------------------------ index-fund context
f = pd.read_csv(KW / "others/kospi200_index_fund_excess_returns.csv", parse_dates=["date"])
info = pd.read_csv(KW / "others/kospi200_index_fund_info.csv")
f = f[f.fund_id.isin(set(info[info.type_name == "K200인덱스"].fund_id)) & (f.date >= "2024-01-22") & (f.date <= "2026-07-16")]
cnt = f.groupby("fund_id").size()
fs = [{"fund_id": fid, "excess_pct": (g.excess_return_pctp / 100).mean() * ANN * 100,
       "te_pct": (g.excess_return_pctp / 100).std(ddof=1) * np.sqrt(ANN) * 100, "n": len(g)}
      for fid, g in f[f.fund_id.isin(cnt[cnt >= cnt.max() - 5].index)].groupby("fund_id")]
funds = pd.DataFrame(fs)
funds["ir"] = funds.excess_pct / funds.te_pct
funds.merge(info[["fund_id", "fund_name", "manager_name"]], on="fund_id").to_csv(OUT / "k200_index_funds_context.csv", index=False)

# ------------------------------------------------------------------ tables
main = res[res["lambda"] == LAMBDA_MAIN].copy()
main["vo"] = main.variant.map({v: i for i, v in enumerate(VARIANTS)})
main["ro"] = main.row.map({r: i for i, (r, _, _) in enumerate(ROWS)})
main = main.sort_values(["ro", "vo"])

COLS = {"label": "Row", "variant": "Variant", "excess_gross_pct": "Excess gross %", "ir_gross": "IR gross",
        "cost_pct": "Cost %", "excess_net_pct": "Excess net %", "te_pct": "TE %", "ir_net": "IR net",
        "excess_net_notax_pct": "Excess net, no tax %", "turnover_oneway_ann": "Turnover 1-way/yr",
        "breakeven_roundtrip_bp": "Break-even bp", "active_notional_kept": "Notional kept",
        "nonbm_share_of_active": "Non-BM share", "mdd_net_pct": "MDD net %"}
(OUT / "table_main_lambda0.3.md").write_text(
    main[list(COLS)].rename(columns=COLS).to_markdown(index=False, floatfmt=".2f"), encoding="utf-8")

FG = {"label": "Row", "variant": "Variant", "excess_gross_pct": "Excess gross %", "ir_gross": "IR gross",
      "beta_book_avg": "Book beta", "active_beta": "Realized active beta", "beta_contrib_pct": "Beta x BM excess %",
      "cost_pct": "Cost %", "excess_net_pct": "Excess net %", "te_pct": "TE %", "ir_net": "IR net",
      "transfer_coef": "TC vs raw book", "active_notional_kept": "Notional kept",
      "etf_weight_avg": "ETF avg", "etf_weight_min": "ETF min", "days_longs_scaled_pct": "Days longs scaled %"}
fg = main[main.variant.isin(FREE_OF_DERIVATIVES)][list(FG)].rename(columns=FG)
(OUT / "table_FG_no_derivatives_lambda0.3.md").write_text(fg.to_markdown(index=False, floatfmt=".3f"), encoding="utf-8")

legs = main[main.variant.isin(["B ls-futures", "C long-only", "E long-only balanced", "F etf-sleeve", "G etf + beta-neutral"])][
    ["label", "variant", "excess_gross_pct", "excess_long_leg_pct", "excess_short_leg_pct",
     "excess_futures_legs_pct", "active_notional_kept"]]
legs.columns = ["Row", "Variant", "Excess gross %", "Long leg %", "Short leg %", "Futures/legs %", "Notional kept"]
(OUT / "table_leg_attribution_lambda0.3.md").write_text(legs.to_markdown(index=False, floatfmt=".2f"), encoding="utf-8")

with open(OUT / "table_lambda_grid.md", "w", encoding="utf-8") as fh:
    for metric, title in [("ir_net", "Net IR"), ("excess_net_pct", "Net excess return (% p.a.)"), ("te_pct", "Tracking error (% p.a.)")]:
        g = res[res.variant.isin(FREE_OF_DERIVATIVES)].pivot_table(index=["label", "variant"], columns="lambda", values=metric)
        fh.write(f"## {title} by lambda, derivative-free variants\n\n" + g.to_markdown(floatfmt=".2f") + "\n\n")
res.pivot_table(index=["label", "variant"], columns="lambda", values=["excess_net_pct", "te_pct", "ir_net"]).to_csv(OUT / "table_lambda_grid.csv")
with open(OUT / "table_index_funds.md", "w", encoding="utf-8") as fh:
    fh.write(f"KOSPI 200 index funds (type K200인덱스, {len(funds)} with full coverage), NAV dates 2024-01-22..2026-07-16\n\n")
    fh.write(funds[["excess_pct", "te_pct", "ir"]].describe().loc[["mean", "25%", "50%", "75%", "min", "max"]].to_markdown(floatfmt=".2f") + "\n")

# ------------------------------------------------------------------ figures
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e6e3", "grid.linewidth": 0.6,
                     "axes.edgecolor": "#8a8a85", "figure.facecolor": "white", "axes.facecolor": "white"})
LBL = {k: l for k, l, _ in ROWS}

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)
for ax, variant in zip(axes, FREE_OF_DERIVATIVES):
    for i, key in enumerate(FIG_ROWS):
        s = series[(key, variant, LAMBDA_MAIN)].excess_net.cumsum() * 100
        ax.plot(s.index, s.values, color=PALETTE[i], linewidth=1.6, label=LBL[key])
    ax.axhline(0, color="#8a8a85", linewidth=0.8)
    ax.set_title(f"{variant}, lambda = {LAMBDA_MAIN}", loc="left")
axes[0].set_ylabel("cumulative net excess over KOSPI 200 (%, sum of daily)")
axes[0].legend(frameon=False, fontsize=7, loc="lower left")
fig.tight_layout()
fig.savefig(OUT / "fig1_cumulative_net_excess.png", dpi=150)

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), sharey=True)
for ax, variant in zip(axes, FREE_OF_DERIVATIVES):
    for i, key in enumerate(FIG_ROWS):
        d = res[(res.row == key) & (res.variant == variant)].sort_values("lambda")
        ax.plot(d["lambda"], d.ir_net, color=PALETTE[i], marker="o", markersize=4, linewidth=1.6, label=LBL[key])
    ax.axhline(0, color="#8a8a85", linewidth=0.8)
    ax.set_title(f"{variant}: net IR vs lambda", loc="left")
    ax.set_xlabel("lambda (overlay scale)")
axes[0].set_ylabel("IR (net of costs)")
axes[0].legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(OUT / "fig2_ir_vs_lambda.png", dpi=150)

fig, axes = plt.subplots(2, 1, figsize=(11.5, 7.6), sharex=True)
x = np.arange(len(ROWS))
wd = 0.36
for ax, col, ttl in zip(axes, ["ir_gross", "ir_net"], ["before costs", "after costs"]):
    for j, variant in enumerate(FREE_OF_DERIVATIVES):
        d = main[main.variant == variant].set_index("row").reindex([r for r, _, _ in ROWS])
        ax.bar(x + (j - 0.5) * wd, d[col], width=wd - 0.04, color=PALETTE[j], label=variant)
    ax.axhline(0, color="#8a8a85", linewidth=0.8)
    ax.set_ylabel(f"IR at lambda = {LAMBDA_MAIN}")
    ax.set_title(f"Derivative-free implementations, {ttl}", loc="left")
axes[1].set_xticks(x, [l for _, l, _ in ROWS], rotation=20, ha="right")
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "fig3_ir_by_variant.png", dpi=150)

print(fg.to_markdown(index=False, floatfmt=".3f"))
print("\ncheck A@1 vs source:\n", chk.to_string())
print("\nwritten to", OUT)
