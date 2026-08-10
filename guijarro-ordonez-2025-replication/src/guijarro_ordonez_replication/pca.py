"""Rolling PCA residuals following the paper's public replication code."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.linalg
from numpy.typing import NDArray

from .characteristics import CHARACTERISTIC_COLUMNS


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class PCAResidualStep:
    """One day's residual and low-rank composition representation."""

    residual: FloatArray
    standardized_eigenvectors: FloatArray
    return_loadings: FloatArray
    eigenvalues: FloatArray


@dataclass(frozen=True)
class DailyPCAResult:
    """Long-form PCA residuals, daily low-rank loadings, and audit data."""

    residuals: pd.DataFrame
    loadings: pd.DataFrame
    audit: dict[str, object]


def pca_residual_step(
    covariance_returns: FloatArray,
    *,
    n_factors: int,
    loading_window_days: int,
) -> PCAResidualStep:
    """Apply the public code's PCA and no-intercept loading regression.

    ``covariance_returns`` ends on the residual date. Consequently both the
    covariance window and the trailing loading-regression window include the
    current return, matching the authors' implementation.
    """

    returns = np.asarray(covariance_returns, dtype=float)
    if returns.ndim != 2 or not np.isfinite(returns).all():
        raise ValueError("covariance_returns must be a finite T-by-N matrix")
    if loading_window_days <= 0 or loading_window_days > returns.shape[0]:
        raise ValueError("loading_window_days must be in [1, covariance rows]")
    n_assets = returns.shape[1]
    if n_factors <= 0 or n_factors >= n_assets:
        raise ValueError("n_factors must be positive and less than asset count")

    mean = returns.mean(axis=0, keepdims=True)
    volatility = np.sqrt(np.mean((returns - mean) ** 2, axis=0))
    if not np.isfinite(volatility).all() or np.any(volatility <= 0):
        raise ValueError("all selected assets need positive finite covariance volatility")
    normalized = (returns - mean) / volatility
    correlation = normalized.T @ normalized
    eigenvalues, eigenvectors = scipy.linalg.eigh(
        correlation,
        subset_by_index=(n_assets - n_factors, n_assets - 1),
        check_finite=False,
    )
    order = np.argsort(-eigenvalues)
    eigenvalues = eigenvalues[order].real
    eigenvectors = eigenvectors[:, order].real

    trailing_returns = returns[-loading_window_days:]
    factors = (trailing_returns / volatility) @ eigenvectors
    coefficients = np.linalg.lstsq(factors, trailing_returns, rcond=None)[0]
    return_loadings = coefficients.T
    standardized_eigenvectors = eigenvectors / volatility[:, None]
    current = returns[-1]
    day_factors = (current / volatility) @ eigenvectors
    residual = current - day_factors @ return_loadings.T
    return PCAResidualStep(
        residual=residual,
        standardized_eigenvectors=standardized_eigenvectors,
        return_loadings=return_loadings,
        eigenvalues=eigenvalues,
    )


def estimate_daily_pca_residuals(
    monthly_panel: pd.DataFrame,
    daily_excess_returns: pd.DataFrame,
    *,
    n_factors: int,
    initial_oos_date: str | pd.Timestamp,
    covariance_window_days: int = 252,
    loading_window_days: int = 60,
    cap_proportion: float = 0.01,
    max_oos_days: int | None = None,
    progress: Callable[[dict[str, object]], None] | None = None,
) -> DailyPCAResult:
    """Estimate the public-code rolling PCA residual system in long form.

    The prior calendar month's characteristic/capitalization mask determines
    the daily universe. A stock also needs complete returns in the preceding
    60 trading days. Missing values in the wider 252-day covariance window and
    on the current day are encoded as zero, as in the public array code.
    """

    required_monthly = {
        "date",
        "ticker",
        "return",
        "market_cap",
        *CHARACTERISTIC_COLUMNS,
    }
    required_daily = {"date", "ticker", "return"}
    missing_monthly = sorted(required_monthly.difference(monthly_panel.columns))
    missing_daily = sorted(required_daily.difference(daily_excess_returns.columns))
    if missing_monthly:
        raise ValueError(f"monthly panel is missing columns: {missing_monthly}")
    if missing_daily:
        raise ValueError(f"daily returns are missing columns: {missing_daily}")
    if covariance_window_days < loading_window_days:
        raise ValueError("covariance window must be at least the loading window")
    if cap_proportion < 0 or cap_proportion >= 100:
        raise ValueError("cap_proportion must be in [0, 100)")
    if max_oos_days is not None and max_oos_days <= 0:
        raise ValueError("max_oos_days must be positive when supplied")

    monthly = monthly_panel.copy()
    monthly["date"] = (
        pd.to_datetime(monthly["date"], errors="raise")
        .dt.to_period("M")
        .dt.to_timestamp("M")
    )
    monthly["ticker"] = monthly["ticker"].astype(str).str.upper()
    if monthly.duplicated(["date", "ticker"]).any():
        raise ValueError("monthly panel has duplicate month-ticker keys")
    total_cap = monthly.groupby("date", sort=False)["market_cap"].transform("sum")
    complete = monthly[["return", *CHARACTERISTIC_COLUMNS]].notna().all(axis=1)
    cap_mask = monthly["market_cap"].div(total_cap).ge(cap_proportion * 0.01)
    eligible = monthly.loc[
        complete & cap_mask & monthly["market_cap"].notna(), ["date", "ticker"]
    ]
    eligible_by_month = {
        month: group["ticker"].to_numpy()
        for month, group in eligible.groupby("date", sort=False)
    }

    daily = daily_excess_returns.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="raise")
    daily["ticker"] = daily["ticker"].astype(str).str.upper()
    if daily.duplicated(["date", "ticker"]).any():
        raise ValueError("daily return panel has duplicate date-ticker keys")
    wide = daily.pivot(index="date", columns="ticker", values="return").sort_index()
    dates = pd.DatetimeIndex(wide.index)
    start = pd.Timestamp(initial_oos_date)
    start_idx = int(dates.searchsorted(start, side="left"))
    if start_idx >= len(dates):
        raise ValueError("initial_oos_date is after the daily sample")
    if start_idx < covariance_window_days - 1:
        raise ValueError(
            "insufficient pre-OOS daily history for the covariance window"
        )
    stop_idx = len(dates)
    if max_oos_days is not None:
        stop_idx = min(stop_idx, start_idx + max_oos_days)

    tickers = wide.columns.to_numpy()
    ticker_to_column = {ticker: index for index, ticker in enumerate(tickers)}
    values = wide.to_numpy(float)
    residual_parts: list[pd.DataFrame] = []
    loading_parts: list[pd.DataFrame] = []
    selected_counts: list[int] = []
    skipped_days: list[dict[str, object]] = []
    left_names = [f"standardized_eigenvector_{k + 1}" for k in range(n_factors)]
    right_names = [f"return_loading_{k + 1}" for k in range(n_factors)]

    for day_idx in range(start_idx, stop_idx):
        day = dates[day_idx]
        characteristic_month = (
            day.to_period("M") - 1
        ).to_timestamp("M")
        month_tickers = eligible_by_month.get(characteristic_month, np.array([]))
        candidate_columns = np.array(
            [ticker_to_column[ticker] for ticker in month_tickers if ticker in ticker_to_column],
            dtype=int,
        )
        if len(candidate_columns) <= n_factors:
            skipped_days.append({"date": day.date().isoformat(), "reason": "universe"})
            continue
        prior = values[day_idx - loading_window_days : day_idx, candidate_columns]
        has_loading_history = np.isfinite(prior).all(axis=0)
        selected_columns = candidate_columns[has_loading_history]
        if len(selected_columns) <= n_factors:
            skipped_days.append({"date": day.date().isoformat(), "reason": "history"})
            continue

        covariance = np.nan_to_num(
            values[
                day_idx - covariance_window_days + 1 : day_idx + 1,
                selected_columns,
            ],
            nan=0.0,
        )
        mean = covariance.mean(axis=0, keepdims=True)
        volatility = np.sqrt(np.mean((covariance - mean) ** 2, axis=0))
        valid_volatility = np.isfinite(volatility) & (volatility > 0)
        selected_columns = selected_columns[valid_volatility]
        covariance = covariance[:, valid_volatility]
        if len(selected_columns) <= n_factors:
            skipped_days.append(
                {"date": day.date().isoformat(), "reason": "volatility"}
            )
            continue

        step = pca_residual_step(
            covariance,
            n_factors=n_factors,
            loading_window_days=loading_window_days,
        )
        selected_tickers = tickers[selected_columns]
        observed = np.isfinite(values[day_idx, selected_columns])
        residual = step.residual.copy()
        residual[~observed] = 0.0
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
        load = pd.DataFrame(
            np.column_stack(
                [step.standardized_eigenvectors, step.return_loadings]
            ),
            columns=[*left_names, *right_names],
        )
        load.insert(0, "ticker", selected_tickers)
        load.insert(0, "date", day)
        loading_parts.append(load)
        selected_counts.append(len(selected_columns))
        if progress is not None and (
            day_idx == start_idx or (day_idx - start_idx + 1) % 20 == 0
        ):
            progress(
                {
                    "event": "pca_day_completed",
                    "date": day.date().isoformat(),
                    "selected_assets": len(selected_columns),
                }
            )

    if not residual_parts:
        raise ValueError("no daily PCA residuals were produced")
    residuals = pd.concat(residual_parts, ignore_index=True)
    loadings = pd.concat(loading_parts, ignore_index=True)
    audit: dict[str, object] = {
        "classification": "Korean price-return PCA replication variant",
        "n_factors": n_factors,
        "initial_oos_date": start.date().isoformat(),
        "covariance_window_days": covariance_window_days,
        "loading_window_days": loading_window_days,
        "cap_proportion_percent": cap_proportion,
        "monthly_universe_characteristic_rule": (
            "all 46 raw pre-imputation characteristics and monthly return observed"
        ),
        "daily_return_definition": (
            "cash-dividend-excluding adjusted price return minus ECOS daily RF"
        ),
        "current_day_in_covariance_and_loading_windows": True,
        "residual_start": residuals["date"].min().date().isoformat(),
        "residual_end": residuals["date"].max().date().isoformat(),
        "residual_rows": len(residuals),
        "loading_rows": len(loadings),
        "completed_days": len(selected_counts),
        "skipped_days": skipped_days,
        "selected_assets_min": min(selected_counts),
        "selected_assets_median": float(np.median(selected_counts)),
        "selected_assets_max": max(selected_counts),
        "composition_reconstruction": (
            "I - standardized_eigenvectors @ return_loadings.T"
        ),
    }
    return DailyPCAResult(residuals=residuals, loadings=loadings, audit=audit)
