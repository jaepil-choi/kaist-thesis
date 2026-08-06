"""Effective-date event study for KOSPI200 additions and deletions."""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd


def _prepare_returns(
    prices: pd.DataFrame, index_levels: pd.DataFrame
) -> tuple[pd.DataFrame, pd.Series, pd.DatetimeIndex]:
    required_prices = {"date", "ticker", "return"}
    missing = sorted(required_prices.difference(prices.columns))
    if missing:
        raise ValueError(f"prices is missing columns: {missing}")
    required_index = {"VALUE_DATE", "VALUE"}
    missing = sorted(required_index.difference(index_levels.columns))
    if missing:
        raise ValueError(f"index_levels is missing columns: {missing}")
    stock = prices[list(required_prices)].copy()
    stock["date"] = pd.to_datetime(stock["date"], errors="raise").dt.normalize()
    stock["return"] = pd.to_numeric(stock["return"], errors="coerce")
    stock = stock.drop_duplicates(["date", "ticker"]).set_index(["date", "ticker"])
    index = index_levels[list(required_index)].copy()
    index["VALUE_DATE"] = pd.to_datetime(
        index["VALUE_DATE"], errors="raise"
    ).dt.normalize()
    index["VALUE"] = pd.to_numeric(index["VALUE"], errors="coerce")
    index = index.drop_duplicates("VALUE_DATE").sort_values("VALUE_DATE")
    index_return = index.set_index("VALUE_DATE")["VALUE"].pct_change(fill_method=None)
    calendar = pd.DatetimeIndex(index_return.index)
    return stock, index_return, calendar


def _relative_return(
    stock: pd.Series,
    market: pd.Series,
    dates: pd.DatetimeIndex,
    minimum_coverage: float,
) -> tuple[float, float]:
    stock_values = stock.reindex(dates)
    market_values = market.reindex(dates)
    valid = stock_values.notna() & market_values.notna()
    coverage = float(valid.mean()) if len(valid) else 0.0
    if coverage < minimum_coverage or not valid.any():
        return np.nan, coverage
    stock_gross = float((1.0 + stock_values[valid]).prod())
    market_gross = float((1.0 + market_values[valid]).prod())
    if market_gross == 0:
        return np.nan, coverage
    return stock_gross / market_gross - 1.0, coverage


def compute_event_window_returns(
    events: pd.DataFrame,
    prices: pd.DataFrame,
    index_levels: pd.DataFrame,
    windows: Iterable[dict[str, int | str]],
    *,
    minimum_coverage: float = 0.90,
) -> pd.DataFrame:
    """Compute compounded stock-over-index returns in trading-session windows."""

    stock, market, calendar = _prepare_returns(prices, index_levels)
    calendar_positions = {date: offset for offset, date in enumerate(calendar)}
    rows: list[dict[str, object]] = []
    for event in events.itertuples(index=False):
        effective_date = pd.Timestamp(event.effective_date).normalize()
        position = calendar_positions.get(effective_date)
        if position is None:
            continue
        try:
            ticker_returns = stock.xs(event.ticker, level="ticker")["return"]
        except KeyError:
            ticker_returns = pd.Series(dtype=float)
        for window in windows:
            start = int(window["start"])
            end = int(window["end"])
            left, right = position + start, position + end
            if left < 0 or right >= len(calendar) or left > right:
                relative, coverage = np.nan, 0.0
            else:
                dates = calendar[left : right + 1]
                relative, coverage = _relative_return(
                    ticker_returns, market, dates, minimum_coverage
                )
            rows.append(
                {
                    "event_id": event.event_id,
                    "effective_date": effective_date,
                    "action": event.action,
                    "ticker": event.ticker,
                    "window": str(window["label"]),
                    "start_offset": start,
                    "end_offset": end,
                    "market_adjusted_return": relative,
                    "coverage": coverage,
                }
            )
    return pd.DataFrame.from_records(rows)


def summarize_event_windows(event_returns: pd.DataFrame) -> pd.DataFrame:
    """Summarize addition/deletion means and their Welch difference statistic."""

    rows: list[dict[str, object]] = []
    for window, group in event_returns.groupby("window", sort=False):
        addition = group.loc[
            group["action"].eq("addition"), "market_adjusted_return"
        ].dropna()
        deletion = group.loc[
            group["action"].eq("deletion"), "market_adjusted_return"
        ].dropna()
        difference = deletion.mean() - addition.mean()
        variance = 0.0
        if len(addition) > 1:
            variance += addition.var(ddof=1) / len(addition)
        if len(deletion) > 1:
            variance += deletion.var(ddof=1) / len(deletion)
        standard_error = math.sqrt(variance) if variance > 0 else np.nan
        event_means = (
            group.groupby(["event_id", "action"])["market_adjusted_return"]
            .mean()
            .unstack()
        )
        paired = event_means.dropna(subset=["addition", "deletion"]).copy()
        paired_spread = paired["deletion"] - paired["addition"]
        clustered_standard_error = (
            paired_spread.std(ddof=1) / math.sqrt(len(paired_spread))
            if len(paired_spread) > 1
            else np.nan
        )
        rows.append(
            {
                "window": window,
                "addition_n": len(addition),
                "addition_mean": addition.mean(),
                "deletion_n": len(deletion),
                "deletion_mean": deletion.mean(),
                "deletion_minus_addition": difference,
                "welch_t_stat": difference / standard_error
                if standard_error and not np.isnan(standard_error)
                else np.nan,
                "event_group_n": len(paired_spread),
                "event_group_mean_spread": paired_spread.mean(),
                "event_clustered_t_stat": paired_spread.mean()
                / clustered_standard_error
                if clustered_standard_error
                and not np.isnan(clustered_standard_error)
                else np.nan,
            }
        )
    return pd.DataFrame.from_records(rows)


def compute_event_paths(
    events: pd.DataFrame,
    prices: pd.DataFrame,
    index_levels: pd.DataFrame,
    *,
    minimum_offset: int,
    maximum_offset: int,
    minimum_coverage: float = 0.90,
) -> pd.DataFrame:
    """Build average cumulative market-adjusted paths from a common pre-event base."""

    windows = [
        {"label": str(offset), "start": minimum_offset, "end": offset}
        for offset in range(minimum_offset, maximum_offset + 1)
    ]
    returns = compute_event_window_returns(
        events,
        prices,
        index_levels,
        windows,
        minimum_coverage=minimum_coverage,
    )
    returns["offset"] = returns["window"].astype(int)
    summary = (
        returns.groupby(["offset", "action"])["market_adjusted_return"]
        .agg(["mean", "count"])
        .reset_index()
    )
    mean = summary.pivot(index="offset", columns="action", values="mean")
    count = summary.pivot(index="offset", columns="action", values="count")
    result = pd.DataFrame(index=mean.index)
    result["addition_mean"] = mean.get("addition")
    result["deletion_mean"] = mean.get("deletion")
    result["deletion_minus_addition"] = (
        result["deletion_mean"] - result["addition_mean"]
    )
    result["addition_n"] = count.get("addition")
    result["deletion_n"] = count.get("deletion")
    return result.reset_index()
