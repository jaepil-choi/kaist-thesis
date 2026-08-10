"""Rolling Korean Fama-French residuals following the public implementation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .characteristics import CHARACTERISTIC_COLUMNS


Progress = Callable[[dict[str, object]], None]
FACTOR_ORDER = ("RMRF", "SMB", "HML", "RMW", "CMA", "MOM", "LTR", "STR")


@dataclass(frozen=True)
class DailyFamaFrenchResult:
    """Long residuals, synthetic factor-leg weights, and execution audit."""

    residuals: pd.DataFrame
    factor_legs: pd.DataFrame
    audit: dict[str, object]


def estimate_daily_fama_french_residuals(
    monthly_panel: pd.DataFrame,
    daily_excess_returns: pd.DataFrame,
    daily_factors: pd.DataFrame,
    *,
    n_factors: int,
    initial_oos_date: str | pd.Timestamp,
    loading_window_days: int = 60,
    cap_proportion: float = 0.01,
    progress: Progress | None = None,
) -> DailyFamaFrenchResult:
    """Estimate rolling no-intercept residuals and ``[I|-beta]`` compositions."""

    if n_factors not in {1, 3, 5, 8}:
        raise ValueError("n_factors must be one of 1, 3, 5, or 8")
    factor_columns = list(FACTOR_ORDER[:n_factors])
    if missing := {"date", *factor_columns}.difference(daily_factors.columns):
        raise ValueError(f"factor panel is missing columns: {sorted(missing)}")
    monthly_required = {
        "date",
        "ticker",
        "return",
        "market_cap",
        *CHARACTERISTIC_COLUMNS,
    }
    if missing := monthly_required.difference(monthly_panel.columns):
        raise ValueError(f"monthly panel is missing columns: {sorted(missing)}")
    if missing := {"date", "ticker", "return"}.difference(daily_excess_returns.columns):
        raise ValueError(f"daily returns are missing columns: {sorted(missing)}")
    if not 0 <= cap_proportion < 100:
        raise ValueError("cap_proportion must be in [0, 100)")

    monthly = monthly_panel.copy()
    monthly["date"] = pd.to_datetime(monthly["date"]).dt.to_period("M").dt.to_timestamp("M")
    monthly["ticker"] = monthly["ticker"].astype(str).str.upper()
    total_cap = monthly.groupby("date", sort=False)["market_cap"].transform("sum")
    complete = monthly[["return", *CHARACTERISTIC_COLUMNS]].notna().all(axis=1)
    large_enough = monthly["market_cap"].div(total_cap).ge(cap_proportion * 0.01)
    eligible = monthly.loc[
        complete & large_enough & monthly["market_cap"].notna(), ["date", "ticker"]
    ]
    eligible_by_month = {
        month: group["ticker"].to_numpy()
        for month, group in eligible.groupby("date", sort=False)
    }

    daily = daily_excess_returns.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="raise")
    daily["ticker"] = daily["ticker"].astype(str).str.upper()
    if daily.duplicated(["date", "ticker"]).any():
        raise ValueError("daily returns have duplicate date-ticker keys")
    returns = daily.pivot(index="date", columns="ticker", values="return").sort_index()
    dates = pd.DatetimeIndex(returns.index)
    factor_frame = daily_factors.copy()
    factor_frame["date"] = pd.to_datetime(factor_frame["date"], errors="raise")
    if "weight" in factor_frame:
        factor_frame = factor_frame.loc[factor_frame["weight"].eq("vw")]
    if "frequency" in factor_frame:
        factor_frame = factor_frame.loc[factor_frame["frequency"].eq("daily")]
    if factor_frame.duplicated("date").any():
        raise ValueError("factor panel has duplicate dates after frequency/weight selection")
    factor_values = factor_frame.set_index("date")[factor_columns].reindex(dates)

    start = pd.Timestamp(initial_oos_date)
    start_index = int(dates.searchsorted(start, side="left"))
    if start_index < loading_window_days:
        raise ValueError("insufficient pre-OOS history for loading window")
    tickers = returns.columns.to_numpy()
    ticker_to_column = {ticker: index for index, ticker in enumerate(tickers)}
    return_values = returns.to_numpy(float)
    factors = factor_values.to_numpy(float)
    residual_parts: list[pd.DataFrame] = []
    leg_parts: list[pd.DataFrame] = []
    selected_counts: list[int] = []
    skipped: list[dict[str, str]] = []
    leg_columns = [f"factor_asset_weight_{name}" for name in factor_columns]

    for day_index in range(start_index, len(dates)):
        day = dates[day_index]
        prior_factors = factors[day_index - loading_window_days : day_index]
        current_factors = factors[day_index]
        if not np.isfinite(prior_factors).all() or not np.isfinite(current_factors).all():
            skipped.append({"date": day.date().isoformat(), "reason": "factor_missing"})
            continue
        characteristic_month = (day.to_period("M") - 1).to_timestamp("M")
        month_tickers = eligible_by_month.get(characteristic_month, np.array([]))
        candidate_columns = np.array(
            [ticker_to_column[ticker] for ticker in month_tickers if ticker in ticker_to_column],
            dtype=int,
        )
        if len(candidate_columns) <= n_factors:
            skipped.append({"date": day.date().isoformat(), "reason": "universe"})
            continue
        prior_returns = return_values[
            day_index - loading_window_days : day_index, candidate_columns
        ]
        selected_columns = candidate_columns[np.isfinite(prior_returns).all(axis=0)]
        if len(selected_columns) <= n_factors:
            skipped.append({"date": day.date().isoformat(), "reason": "history"})
            continue
        estimation_returns = return_values[
            day_index - loading_window_days : day_index, selected_columns
        ]
        beta = np.linalg.lstsq(prior_factors, estimation_returns, rcond=None)[0].T
        current_returns = return_values[day_index, selected_columns]
        observed = np.isfinite(current_returns)
        residual = np.zeros(len(selected_columns), dtype=float)
        residual[observed] = (
            current_returns[observed] - beta[observed] @ current_factors
        )
        selected_tickers = tickers[selected_columns]
        residual_parts.append(
            pd.DataFrame(
                {
                    "date": day,
                    "ticker": selected_tickers,
                    "residual": residual,
                    "return_observed": observed,
                }
            )
        )
        legs = pd.DataFrame(-beta, columns=leg_columns)
        legs.insert(0, "ticker", selected_tickers)
        legs.insert(0, "date", day)
        leg_parts.append(legs)
        selected_counts.append(len(selected_columns))
        if progress is not None and (
            day_index == start_index or (day_index - start_index + 1) % 100 == 0
        ):
            progress(
                {
                    "event": "fama_french_day_completed",
                    "date": day.date().isoformat(),
                    "selected_assets": len(selected_columns),
                }
            )

    if not residual_parts:
        raise ValueError("no Fama-French residuals were produced")
    residuals = pd.concat(residual_parts, ignore_index=True)
    factor_legs = pd.concat(leg_parts, ignore_index=True)
    audit: dict[str, object] = {
        "classification": "Korean price-return Fama-French residual variant",
        "n_factors": n_factors,
        "factor_columns": factor_columns,
        "initial_oos_date": start.date().isoformat(),
        "loading_window_days": loading_window_days,
        "fit_intercept": False,
        "composition": "[I | -beta] with synthetic factor assets",
        "residual_start": residuals["date"].min().date().isoformat(),
        "residual_end": residuals["date"].max().date().isoformat(),
        "residual_rows": len(residuals),
        "completed_days": len(selected_counts),
        "selected_assets_min": min(selected_counts),
        "selected_assets_median": float(np.median(selected_counts)),
        "selected_assets_max": max(selected_counts),
        "skipped_days": skipped,
        "factor_instrument_limit": (
            "factor legs are synthetic portfolio returns, not directly observed ETFs"
        ),
    }
    return DailyFamaFrenchResult(residuals, factor_legs, audit)
