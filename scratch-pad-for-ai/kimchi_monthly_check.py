"""Check whether Kimchi's independent monthly factors are reproduced by monthly buy-and-hold buckets.

Input 1 is the daily bucket returns written by the vqapr testbed rerun
(``outputs/rerun-corrected-prices/weighting/weighting_ff6_daily.csv``). It holds scenario 2 and 3
memberships under W1 (buy-and-hold), W2 (previous-day market cap), W3 (June weights restored daily)
and vqapr. Input 2 is Kimchi's monthly files in ``data/kimchi-factor``.

- A bucket's monthly return is its daily returns compounded within the calendar month. For
  buy-and-hold this is exactly the month's holding-period return.
- Monthly SMB/HML apply the factor formula to those monthly bucket returns, which is Kimchi's
  "independent monthly" rule.
- The daily factors compounded within the month are reported alongside, to show the
  monthly/daily gap.
- RMRF is built from month-end KOSPI levels and three CD91 monthly conventions, to find the one
  Kimchi uses.

Run from the repository root:
    uv run python scratch-pad-for-ai/kimchi_monthly_check.py [--start 2018-07] [--end 2026-06]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

WEIGHTING = Path("vqapr-scenario-testbed/outputs/rerun-corrected-prices/weighting")
KIMCHI = Path("data/kimchi-factor")
ECOS = Path("data/kaist_pilot/canonical/guijarro_2025/ecos/raw")
OUTPUT = Path("scratch-pad-for-ai/outputs/kimchi_monthly_check.csv")
BUCKETS = ["S1", "S2", "S3", "B1", "B2", "B3"]


def factors(buckets: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SMB": buckets[["S1", "S2", "S3"]].mean(axis=1) - buckets[["B1", "B2", "B3"]].mean(axis=1),
            "HML": buckets[["S3", "B3"]].mean(axis=1) - buckets[["S1", "B1"]].mean(axis=1),
        }
    )


def compound_monthly(daily: pd.DataFrame) -> pd.DataFrame:
    return (1.0 + daily).groupby(daily.index.to_period("M")).prod(min_count=1) - 1.0


def kimchi_monthly(factor: str) -> tuple[pd.Series, pd.DataFrame]:
    frame = pd.read_csv(KIMCHI / f"kimchi_monthly_{factor}_vw_all.csv", parse_dates=["date"])
    frame["month"] = frame["date"].dt.to_period("M")
    top = frame[frame["bucket"].isna() & frame["section"].eq("returns")].set_index("month")["ret"]
    construction = frame["section"].eq("construction_bucket_returns") & frame["bucket"].isin(BUCKETS)
    buckets = frame[construction].pivot_table(index="month", columns="bucket", values="ret")
    return top, buckets.reindex(columns=BUCKETS)


def stats(ours: pd.Series, theirs: pd.Series) -> dict[str, float]:
    both = pd.concat([ours, theirs], axis=1, keys=["a", "b"]).dropna()
    diff = both["a"] - both["b"]
    return {
        "months": len(both),
        "corr": both["a"].corr(both["b"]),
        "mean_diff_pct_yr": diff.mean() * 12 * 100,
        "mae_pct_mo": diff.abs().mean() * 100,
        "te_pct_yr": diff.std() * np.sqrt(12) * 100,
        "sign_agree": float((np.sign(both["a"]) == np.sign(both["b"])).mean()),
    }


def ecos(name: str, value: str) -> pd.Series:
    path = next(ECOS.glob(f"{name}_*.json"))
    rows = pd.DataFrame(json.loads(path.read_text(encoding="utf-8"))["rows"])
    series = pd.Series(pd.to_numeric(rows["DATA_VALUE"]).to_numpy(), index=pd.to_datetime(rows["TIME"], format="%Y%m%d"))
    return series.sort_index().rename(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--start", default="2018-07")
    parser.add_argument("--end", default="2026-06")
    args = parser.parse_args()
    window = pd.period_range(args.start, args.end, freq="M")

    ff6 = pd.read_csv(WEIGHTING / "weighting_ff6_daily.csv", header=[0, 1, 2], index_col=0, parse_dates=True)
    ff3 = pd.read_csv(WEIGHTING / "weighting_ff3_daily.csv", header=[0, 1, 2], index_col=0, parse_dates=True)
    kimchi = {f: kimchi_monthly(f) for f in ("SMB", "HML")}
    print("kimchi monthly sections:", pd.read_csv(KIMCHI / "kimchi_monthly_HML_vw_all.csv")["section"].unique().tolist())

    rows = []
    for scenario in ("s2", "s3"):
        for weight in ("W1", "W2", "W3", "vqapr(A)"):
            buckets = compound_monthly(ff6[scenario][weight][BUCKETS]).reindex(window)
            monthly = factors(buckets)
            compounded = compound_monthly(ff3[scenario][weight][["SMB", "HML"]]).reindex(window)
            for factor in ("SMB", "HML"):
                top, kb = kimchi[factor]
                top, kb = top.reindex(window), kb.reindex(window)
                rows.append({"scenario": scenario, "weight": weight, "series": factor,
                             "method": "monthly buckets -> factor", **stats(monthly[factor], top)})
                rows.append({"scenario": scenario, "weight": weight, "series": factor,
                             "method": "daily factor compounded", **stats(compounded[factor], top)})
            for bucket in BUCKETS:
                rows.append({"scenario": scenario, "weight": weight, "series": bucket,
                             "method": "monthly bucket", **stats(buckets[bucket], kimchi["HML"][1].reindex(window)[bucket])})

    # RMRF: month-end KOSPI levels, three CD91 monthly conventions
    kospi, cd = ecos("kospi_index_daily", "kospi"), ecos("rf_cd_91d_daily", "cd")
    month_end = kospi.groupby(kospi.index.to_period("M")).last()
    rm = month_end.pct_change()
    cd_trading = cd.reindex(kospi.index).ffill()
    rf = {
        "(1+y_end)^(1/12)-1": (1 + cd.groupby(cd.index.to_period("M")).last() / 100) ** (1 / 12) - 1,
        "(1+y_prev_end)^(1/12)-1": ((1 + cd.groupby(cd.index.to_period("M")).last() / 100) ** (1 / 12) - 1).shift(1),
        "daily (1+y)^(1/252) compounded": (1 + ((1 + cd_trading / 100) ** (1 / 252) - 1)).groupby(
            cd_trading.index.to_period("M")).prod() - 1,
        "y_end/12": cd.groupby(cd.index.to_period("M")).last() / 100 / 12,
    }
    market = pd.read_csv(KIMCHI / "kimchi_monthly_RMRF_vw_all.csv", parse_dates=["date"])
    market = market[market["section"].eq("returns")]
    market = market.pivot_table(index=market["date"].dt.to_period("M"), columns="factor", values="ret")
    rows.append({"scenario": "all", "weight": "-", "series": "RM", "method": "KOSPI month-end level ratio",
                 **stats(rm.reindex(window), market["RM"].reindex(window))})
    for name, series in rf.items():
        rows.append({"scenario": "all", "weight": "-", "series": "RF", "method": name,
                     **stats(series.reindex(window), market["RF"].reindex(window))})
        rf_gap = (series.reindex(window) - market["RF"].reindex(window)).abs().max()
        rows[-1]["max_abs_diff"] = rf_gap
        rows.append({"scenario": "all", "weight": "-", "series": "RMRF", "method": f"RM - RF {name}",
                     **stats((rm - series).reindex(window), market["RMRF"].reindex(window))})

    result = pd.DataFrame(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)
    pd.set_option("display.width", 220)
    shown = result[result["series"].isin(["SMB", "HML", "RM", "RF", "RMRF"])]
    print(shown.round(4).to_string(index=False))
    print("\nbuckets, scenario 3 (corr / mean diff %/yr):")
    b = result[(result["scenario"] == "s3") & result["series"].isin(BUCKETS)]
    print(b.pivot(index="series", columns="weight", values="corr").reindex(BUCKETS).round(4).to_string())
    print(b.pivot(index="series", columns="weight", values="mean_diff_pct_yr").reindex(BUCKETS).round(2).to_string())


if __name__ == "__main__":
    main()
