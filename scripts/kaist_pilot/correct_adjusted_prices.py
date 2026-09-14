"""Correct vendor adjustment-factor defects in the KAIST pilot ``adjusted_prices.parquet``.

The canonical file is the output of ``build_adjusted_prices`` in kwam-enhanced-index
(``src/kwam_enhanced_index/data/preprocessing.py``). That code turns FnGuide daily prices into
adjusted prices, and the file reached this repository through qlibx on 2026-08-07 (manifest 112).
The builder trusts the vendor's ``수정계수`` (the adjustment factor, 수정계수 = 전일종가 / 기준가 on
an event day) and ``기준가`` (the base price). It then computes, per ticker:

    adjustment_multiplier_t = product of 수정계수 over the ticker's later rows
    adj_<price>_t           = <price>_t / adjustment_multiplier_t
    return_t                = 종가_t / 기준가_t - 1

Three vendor defects break that chain. This script repairs them:

A. A share consolidation or split whose ``기준가`` and ``수정계수`` were never adjusted. The share
   count jumps by an integer ratio, but 수정계수 stays 1. The day's return is clearly beyond the daily
   price limit, and the share-adjusted return is plausible. Example: A052670 on 2026-02-09 (1,500:1),
   which reads +29,948%. Repair: 수정계수 := the share ratio, and 기준가 := 전일종가 / 수정계수, so the
   return is recomputed.
B. ``수정계수 = 0`` with ``전일종가 = 0`` on a row that is not the ticker's first (A065180 on
   2016-06-02). This zeroes every earlier multiplier and turns earlier adjusted prices into inf.
   Repair: 전일종가 := the previous row's close; rule C then sets the factor.
C. A 기준가 that was adjusted while 수정계수 stayed inconsistent with it: 기준가 differs from
   전일종가 / 수정계수 by more than one price tick. Within one tick, the difference is the exchange's
   tick rounding and the vendor factor is kept. Repair: 수정계수 := 전일종가 / 기준가, the vendor's own
   definition, so the adjusted series agrees with the vendor return.

Returns change only for rows corrected under A. Multipliers and adjusted prices are recomputed only
for tickers with a corrected row. Every other value is carried over unchanged. Each corrected row is
written to an audit CSV, and the run is recorded in a manifest.

Run from the repository root:
    uv run python scripts/kaist_pilot/correct_adjusted_prices.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


EQUITY = Path("data/kaist_pilot/canonical/common/korean_equity")
DEFAULT_SOURCE = Path(
    "data/kaist_pilot/canonical/common/korean_equity_source/adjusted_prices.uncorrected.parquet"
)
DEFAULT_OUTPUT = EQUITY / "adjusted_prices.parquet"
DEFAULT_AUDIT = Path("data/kaist_pilot/metadata/checks/qlibx_korean_equity/adjusted_prices_corrections.csv")
DEFAULT_MANIFEST = Path(
    "data/kaist_pilot/metadata/manifests/114_adjusted_prices_corrections_20260914.json"
)

PRICE_COLUMNS = {"기준가": "adj_base", "시가": "adj_open", "고가": "adj_high", "저가": "adj_low", "종가": "adj_close"}
# KRX daily price limit since 2015-06-15 (earlier 15%). Only moves clearly beyond it are candidates:
# a limit-down day is -30% up to float error, and a merger or share issue can fall on one (A206640
# 2015-09-11, A221610 2020-05-19) without any price adjustment being due.
PRICE_LIMIT = 0.30
LIMIT_MARGIN = 0.01
# The share-adjusted gross return (1 + return) * share ratio must be plausible for a split: between a
# 90% fall and a tenfold rise. A merger that multiplies shares while the price barely moves fails it.
ADJUSTED_GROSS_BAND = (0.1, 10.0)
# A share ratio this far from 1 is treated as a candidate corporate action (not float noise).
SHARE_RATIO_BAND = (0.5, 2.0)
# How close a share ratio must be to an integer (or its reciprocal) to be read as a split ratio.
RATIO_TOLERANCE = 0.01
# The exchange rounds an event day's 기준가 to the tick, and the vendor rounds 수정계수 to six
# decimals. A 5:1 split can therefore show 기준가 368 against 전일종가 / 5 = 368.4. A disagreement
# within one tick is rounding; the vendor factor is the true ratio, so it is kept. Ticks follow the
# coarser of the pre-2023 KOSPI schedule and the 2023 unified schedule at each price level.
TICK_SCHEDULE = ((1_000, 1.0), (5_000, 5.0), (10_000, 10.0), (50_000, 50.0), (100_000, 100.0), (500_000, 500.0))


def krx_tick(price: pd.Series) -> pd.Series:
    """Tick size at each price level: the coarser of the pre-2023 and 2023 schedules."""

    tick = pd.Series(1_000.0, index=price.index)
    for upper, size in reversed(TICK_SCHEDULE):
        tick = tick.where(price >= upper, size)
    return tick


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def future_adjustment_multiplier(factor: pd.Series) -> pd.Series:
    """The builder's multiplier: product of the ticker's later factors (kwam-enhanced-index)."""

    return factor.iloc[::-1].shift(1).cumprod().iloc[::-1].fillna(1.0)


def snap_split_ratio(share_ratio: float) -> float | None:
    """Return the factor for an integer split/consolidation ratio, or None if the ratio is not one."""

    if share_ratio >= 1.0:
        whole = round(share_ratio)
        return float(whole) if whole >= 2 and abs(share_ratio / whole - 1.0) <= RATIO_TOLERANCE else None
    whole = round(1.0 / share_ratio)
    return 1.0 / whole if whole >= 2 and abs(share_ratio * whole - 1.0) <= RATIO_TOLERANCE else None


def correct(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the corrected table (same rows, order and columns) and an audit of corrected rows."""

    frame = prices.copy()
    frame["_row"] = np.arange(len(frame))
    frame = frame.sort_values(["ticker", "date"], kind="stable")
    grouped = frame.groupby("ticker", sort=False)
    first = grouped.cumcount().eq(0)
    last_close = grouped["종가"].shift(1)
    last_shares = grouped["유통주식수"].shift(1)
    original = frame[["기준가", "전일종가", "수정계수", "return"]].copy()
    rule = pd.Series("", index=frame.index, dtype=object)

    # A. unadjusted consolidation/split
    share_ratio = frame["유통주식수"] / last_shares
    vendor_return = frame["종가"] / frame["기준가"].where(frame["기준가"] > 0) - 1.0
    candidate_a = (
        ~first
        & frame["수정계수"].eq(1.0)
        & last_shares.gt(0)
        & frame["유통주식수"].gt(0)
        & ~share_ratio.between(*SHARE_RATIO_BAND)
        & vendor_return.abs().gt(PRICE_LIMIT + LIMIT_MARGIN)
        & ((1.0 + vendor_return) * share_ratio).between(*ADJUSTED_GROSS_BAND)
        & frame["전일종가"].gt(0)
    )
    for index in frame.index[candidate_a]:
        factor = snap_split_ratio(float(share_ratio[index]))
        if factor is None:
            raise ValueError(
                "share count jump without an integer split ratio; review before correcting: "
                f"{frame.at[index, 'ticker']} {frame.at[index, 'date']} ratio {share_ratio[index]:.6f}"
            )
        frame.at[index, "수정계수"] = factor
        frame.at[index, "기준가"] = frame.at[index, "전일종가"] / factor
        rule[index] = "A"

    # B. missing previous close on a non-first row
    candidate_b = ~first & (frame["수정계수"].le(0) | frame["전일종가"].le(0)) & last_close.gt(0)
    frame.loc[candidate_b, "전일종가"] = last_close[candidate_b]
    rule[candidate_b] = rule[candidate_b].where(rule[candidate_b].ne(""), "B")

    # C. factor inconsistent with the vendor's own base price
    usable = ~first & frame["전일종가"].gt(0) & frame["기준가"].gt(0)
    implied = frame["전일종가"] / frame["기준가"]
    implied_base = frame["전일종가"] / frame["수정계수"].where(frame["수정계수"] > 0)
    inconsistent = usable & (
        frame["수정계수"].le(0) | (frame["기준가"] - implied_base).abs().gt(krx_tick(frame["기준가"]))
    )
    frame.loc[inconsistent, "수정계수"] = implied[inconsistent]
    rule[inconsistent & rule.eq("")] = "C"

    corrected_rows = rule.ne("")
    tickers = frame.loc[corrected_rows, "ticker"].unique()
    affected = frame["ticker"].isin(tickers)
    if affected.any():
        subset = frame.loc[affected]
        multiplier = subset.groupby("ticker", sort=False)["수정계수"].transform(future_adjustment_multiplier)
        frame.loc[affected, "adjustment_multiplier"] = multiplier
        for column, output in PRICE_COLUMNS.items():
            frame.loc[affected, output] = frame.loc[affected, column] / multiplier
    recompute_return = rule.eq("A")
    frame.loc[recompute_return, "return"] = (
        frame.loc[recompute_return, "종가"] / frame.loc[recompute_return, "기준가"] - 1.0
    )

    audit = pd.DataFrame(
        {
            "ticker": frame.loc[corrected_rows, "ticker"],
            "date": frame.loc[corrected_rows, "date"],
            "rule": rule[corrected_rows],
            "last_close": last_close[corrected_rows],
            "share_ratio": share_ratio[corrected_rows],
            "base_before": original.loc[corrected_rows, "기준가"],
            "base_after": frame.loc[corrected_rows, "기준가"],
            "previous_close_before": original.loc[corrected_rows, "전일종가"],
            "previous_close_after": frame.loc[corrected_rows, "전일종가"],
            "factor_before": original.loc[corrected_rows, "수정계수"],
            "factor_after": frame.loc[corrected_rows, "수정계수"],
            "return_before": original.loc[corrected_rows, "return"],
            "return_after": frame.loc[corrected_rows, "return"],
        }
    ).sort_values(["rule", "ticker", "date"])
    frame = frame.sort_values("_row").drop(columns="_row")
    frame.index = prices.index
    return frame, audit.reset_index(drop=True)


def validate(before: pd.DataFrame, after: pd.DataFrame, audit: pd.DataFrame) -> dict[str, object]:
    """Fail closed on anything the correction must not do; return summary counts."""

    if list(before.columns) != list(after.columns) or len(before) != len(after):
        raise AssertionError("schema or row count changed")
    if not before[["ticker", "date"]].equals(after[["ticker", "date"]]):
        raise AssertionError("row keys or order changed")
    multiplier = after["adjustment_multiplier"]
    if not (np.isfinite(multiplier) & multiplier.gt(0)).all():
        raise AssertionError("a multiplier is zero, negative or not finite")
    for column in PRICE_COLUMNS.values():
        values = after[column]
        if np.isinf(values).any():
            raise AssertionError(f"{column} still has infinite values")
    untouched = ~after["ticker"].isin(audit["ticker"].unique())
    for column in before.columns:
        left, right = before.loc[untouched, column], after.loc[untouched, column]
        if not (left.equals(right) or ((left == right) | (left.isna() & right.isna())).all()):
            raise AssertionError(f"untouched ticker values changed in {column}")
    return_changed = ~(
        (before["return"] == after["return"]) | (before["return"].isna() & after["return"].isna())
    )
    rule_a = audit.loc[audit["rule"].eq("A"), ["ticker", "date"]]
    changed_keys = after.loc[return_changed, ["ticker", "date"]]
    if len(changed_keys) != len(rule_a) or not changed_keys.merge(rule_a).shape[0] == len(rule_a):
        raise AssertionError("a return changed outside rule A")

    def return_gap(frame: pd.DataFrame) -> pd.Series:
        """|adjusted-close return - return| where 전일종가 is the previous row's close; NaN elsewhere."""

        ordered = frame.sort_values(["ticker", "date"], kind="stable")
        grouped = ordered.groupby("ticker", sort=False)
        comparable = ordered["전일종가"].eq(grouped["종가"].shift(1)) & ordered["기준가"].gt(0)
        implied = ordered["adj_close"] / grouped["adj_close"].shift(1) - 1.0
        return (implied - ordered["return"]).abs().where(comparable).reindex(frame.index)

    gap_before, gap_after = return_gap(before), return_gap(after)
    keys = after[["ticker", "date"]].assign(_gap_after=gap_after, _gap_before=gap_before)
    corrected = keys.merge(audit[["ticker", "date"]], on=["ticker", "date"])
    worst_corrected = float(corrected["_gap_after"].max(skipna=True)) if len(corrected) else 0.0
    if worst_corrected > 1e-9:
        raise AssertionError(f"a corrected row's adjusted close and return disagree by {worst_corrected}")
    worse = gap_after.gt(gap_before.fillna(np.inf) + 1e-12)
    if worse.any():
        raise AssertionError(f"{int(worse.sum())} rows moved further from their return than before")
    return {
        "rows": int(len(after)),
        "corrected_rows_by_rule": audit["rule"].value_counts().sort_index().to_dict(),
        "tickers_recomputed": int(audit["ticker"].nunique()),
        "returns_changed": int(return_changed.sum()),
        "max_gap_on_corrected_rows": worst_corrected,
        "rows_with_rounding_gap_over_1e-9_kept": int(gap_after.gt(1e-9).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dry-run", action="store_true", help="validate and print the summary only")
    args = parser.parse_args()

    table = pq.read_table(args.source)
    before = table.to_pandas()
    after, audit = correct(before)
    summary = validate(before, after, audit)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    print(audit.loc[audit["rule"].isin(["A", "B"])].to_string(index=False))
    if args.dry_run:
        return

    corrected = pa.Table.from_pandas(after, schema=table.schema, preserve_index=False)
    temporary = args.output.with_suffix(".tmp.parquet")
    pq.write_table(corrected, temporary)
    os.replace(temporary, args.output)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(args.audit, index=False, encoding="utf-8")
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "purpose": "Repair vendor adjustment-factor defects in adjusted_prices.parquet",
        "command": "uv run python scripts/kaist_pilot/correct_adjusted_prices.py",
        "producer": "kwam-enhanced-index src/kwam_enhanced_index/data/preprocessing.py::build_adjusted_prices",
        "source": {"path": args.source.as_posix(), "sha256": sha256(args.source)},
        "output": {"path": args.output.as_posix(), "sha256": sha256(args.output)},
        "audit": {"path": args.audit.as_posix(), "sha256": sha256(args.audit)},
        "rules": {
            "A": "unadjusted consolidation/split: integer share ratio, 수정계수 = 1, |return| > 31%, "
            "(1 + return) * share ratio in [0.1, 10]",
            "B": "수정계수 = 0 or 전일종가 = 0 on a non-first row: 전일종가 := previous close",
            "C": "수정계수 := 전일종가 / 기준가 where the vendor factor disagrees with its base price",
        },
        "parameters": {
            "price_limit": PRICE_LIMIT,
            "share_ratio_band": SHARE_RATIO_BAND,
            "ratio_tolerance": RATIO_TOLERANCE,
            "base_tolerance": "one KRX tick at the base price (coarser of the pre-2023 and 2023 schedules)",
        },
        "summary": summary,
    }
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"wrote {args.output} ({len(audit)} corrected rows)")


if __name__ == "__main__":
    main()
