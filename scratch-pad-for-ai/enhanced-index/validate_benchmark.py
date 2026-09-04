"""Validate the KOSPI 200 benchmark used by enhanced_index.py.

Rebuilds the daily KOSPI 200 return from the float-adjusted index weights in
kwam-enhanced-index/data/preprocessed/k200_members.parquet (weights at d's close x returns at d+1)
and compares it with (a) the KOSPI 200 return in the index-fund excess file, whose dates are fund
NAV dates and lag the close by one session, and (b) the KODEX 200 ETF close-to-close return.
Result on 2026-09-04: corr 1.0000 with (a) at lag -1 (0.3 bp daily std diff), 0.9956 with (b) at lag 0.
Run: uv run python scratch-pad-for-ai/enhanced-index/validate_benchmark.py
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
KW = ROOT.parent / "kwam-enhanced-index" / "data"
TB = ROOT / "vqapr-scenario-testbed"
m = pd.read_parquet(KW / "preprocessed/k200_members.parquet")
px = pd.read_parquet(TB / "data/korean_equity/adjusted_prices.parquet", columns=["date", "ticker", "return"])
px = px[px.date >= "2023-12-01"]
dates = np.sort(px.date.unique())
mm = m[m.date >= "2023-12-01"][["date", "ticker", "index_weight"]].copy()
mm["next"] = mm.date.map(dict(zip(dates[:-1], dates[1:])))
j = mm.merge(px, left_on=["next", "ticker"], right_on=["date", "ticker"], suffixes=("", "_r"))
rep = j.assign(c=j.index_weight * j["return"]).groupby("next").c.sum()
cov = j.groupby("next").index_weight.sum()
print("weight coverage of returns: min %.4f" % cov.min())
f = pd.read_csv(KW / "others/kospi200_index_fund_excess_returns.csv")
info = pd.read_csv(KW / "others/kospi200_index_fund_info.csv")
print(info.bm_code.value_counts().head(), info.type_name.value_counts().head())
fid = info[(info.bm_code == "A200")].sort_values("observations", ascending=False).fund_id.iloc[0]
ff = f[f.fund_id == fid].set_index(pd.to_datetime(f[f.fund_id == fid].date))
k = ff.bm_return_pct / 100
for lag in [-2, -1, 0, 1, 2]:
    c = pd.concat([rep.rename("rep"), k.shift(lag).rename("k")], axis=1).dropna()
    c = c[c.index >= "2024-01-19"]
    print("lag", lag, "corr %.4f  std diff bp %.1f n %d" % (c.rep.corr(c.k), (c.rep - c.k).std() * 1e4, len(c)))
etf = pd.read_parquet(KW / "preprocessed/k200_etf_prices.parquet")
e = etf[etf.ticker == "A069500"].set_index("date").sort_index()
er = e.execution_close_price.pct_change()
for lag in [-1, 0, 1]:
    c = pd.concat([rep.rename("rep"), er.shift(lag).rename("etf")], axis=1).dropna(); c = c[c.index >= "2024-01-19"]
    print("ETF lag", lag, "corr %.4f std diff bp %.1f n %d" % (c.rep.corr(c.etf), (c.rep - c.etf).std() * 1e4, len(c)))
c = pd.concat([rep.rename("rep"), k.rename("k"), er.rename("etf")], axis=1).dropna(); c = c[c.index >= "2024-01-19"]
print("ann: rep %.1f%% fundfile %.1f%% etf %.1f%%" % tuple(c[x].mean() * 252 * 100 for x in ["rep", "k", "etf"]))
print(c.tail(5))
