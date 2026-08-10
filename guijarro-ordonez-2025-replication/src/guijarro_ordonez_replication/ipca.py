"""Instrumented PCA estimation with explicit exact and short-history modes."""

from __future__ import annotations

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .characteristics import CHARACTERISTIC_COLUMNS


FloatArray = NDArray[np.float64]
PAPER_WINDOW_MONTHS = 240


class ShortHistoryIPCAWarning(UserWarning):
    """The IPCA estimation window is shorter than the paper's 240 months."""


@dataclass(frozen=True)
class IPCAFit:
    """One IPCA alternating-least-squares estimate."""

    gamma: FloatArray
    factors: tuple[FloatArray, ...]
    iterations: int
    converged: bool


@dataclass(frozen=True)
class DailyIPCAResult:
    """Long-form daily IPCA residuals and an estimation audit."""

    residuals: pd.DataFrame
    loadings: pd.DataFrame
    audit: dict[str, object]


def validate_ipca_window(
    available_months: int,
    *,
    window_months: int = PAPER_WINDOW_MONTHS,
    allow_short_history: bool = False,
) -> int:
    """Validate the rolling window and warn for a labeled Korean extension."""

    if window_months <= 0:
        raise ValueError("window_months must be positive")
    if window_months != PAPER_WINDOW_MONTHS:
        if not allow_short_history:
            raise ValueError(
                "paper-exact IPCA requires window_months=240; pass "
                "allow_short_history=True for a labeled sensitivity"
            )
        warnings.warn(
            f"SHORT_HISTORY_IPCA: using {window_months} months instead of the "
            "paper's 240-month rolling window.",
            ShortHistoryIPCAWarning,
            stacklevel=2,
        )
    if available_months < window_months:
        raise ValueError(
            f"IPCA needs {window_months} training months but only "
            f"{available_months} are available"
        )
    return window_months


def _factor_step(
    returns: tuple[FloatArray, ...],
    characteristics: tuple[FloatArray, ...],
    gamma: FloatArray,
) -> tuple[FloatArray, ...]:
    factors: list[FloatArray] = []
    for ret_t, z_t in zip(returns, characteristics, strict=True):
        beta_t = z_t @ gamma
        factors.append(np.linalg.pinv(beta_t.T @ beta_t) @ beta_t.T @ ret_t)
    return tuple(factors)


def _gamma_step(
    returns: tuple[FloatArray, ...],
    characteristics: tuple[FloatArray, ...],
    factors: tuple[FloatArray, ...],
    *,
    n_characteristics: int,
    n_factors: int,
) -> FloatArray:
    size = n_characteristics * n_factors
    left = np.zeros((size, size), dtype=float)
    right = np.zeros(size, dtype=float)
    for ret_t, z_t, factor_t in zip(
        returns, characteristics, factors, strict=True
    ):
        design = np.kron(z_t, factor_t.reshape(1, -1))
        left += design.T @ design
        right += design.T @ ret_t
    return (np.linalg.pinv(left) @ right).reshape(n_characteristics, n_factors)


def fit_ipca_als(
    returns: tuple[FloatArray, ...],
    characteristics: tuple[FloatArray, ...],
    *,
    n_factors: int,
    max_iterations: int = 100,
    tolerance: float = 1e-5,
) -> IPCAFit:
    """Fit the paper/reference-code IPCA alternating least-squares system."""

    if not returns or len(returns) != len(characteristics):
        raise ValueError("returns and characteristics must contain the same months")
    n_characteristics = characteristics[0].shape[1]
    if n_factors <= 0 or n_factors > n_characteristics:
        raise ValueError("n_factors must be in [1, n_characteristics]")
    for ret_t, z_t in zip(returns, characteristics, strict=True):
        if ret_t.ndim != 1 or z_t.ndim != 2 or z_t.shape[0] != ret_t.shape[0]:
            raise ValueError("each month must have returns (N,) and chars (N,L)")
        if z_t.shape[1] != n_characteristics:
            raise ValueError("all months must have the same characteristic width")
        if not np.isfinite(ret_t).all() or not np.isfinite(z_t).all():
            raise ValueError("IPCA inputs must be finite after explicit imputation")

    # The reference code initializes factors from the characteristic-managed
    # portfolio matrix X_t = Z_t' R_t / N_t.
    managed = np.vstack(
        [z_t.T @ ret_t / len(ret_t) for ret_t, z_t in zip(returns, characteristics, strict=True)]
    )
    _, _, right_vectors = np.linalg.svd(managed, full_matrices=False)
    initial = managed @ right_vectors[:n_factors].T
    factors = tuple(row.copy() for row in initial)
    gamma = np.zeros((n_characteristics, n_factors), dtype=float)
    converged = False
    for iteration in range(1, max_iterations + 1):
        updated = _gamma_step(
            returns,
            characteristics,
            factors,
            n_characteristics=n_characteristics,
            n_factors=n_factors,
        )
        factors = _factor_step(returns, characteristics, updated)
        delta = float(np.max(np.abs(updated - gamma)))
        gamma = updated
        if iteration > 1 and delta < tolerance:
            converged = True
            break
    return IPCAFit(
        gamma=gamma,
        factors=factors,
        iterations=iteration,
        converged=converged,
    )


def _monthly_arrays(
    panel: pd.DataFrame,
    dates: pd.DatetimeIndex,
) -> tuple[tuple[FloatArray, ...], tuple[FloatArray, ...]]:
    returns: list[FloatArray] = []
    chars: list[FloatArray] = []
    for date in dates:
        month = panel.loc[panel["date"].eq(date)].dropna(
            subset=["return", *CHARACTERISTIC_COLUMNS]
        )
        if len(month) == 0:
            raise ValueError(f"no complete IPCA observations for {date.date()}")
        returns.append(month["return"].to_numpy(float))
        chars.append(month[list(CHARACTERISTIC_COLUMNS)].to_numpy(float))
    return tuple(returns), tuple(chars)


def estimate_daily_ipca_residuals(
    monthly_panel: pd.DataFrame,
    daily_returns: pd.DataFrame,
    *,
    n_factors: int,
    window_months: int = PAPER_WINDOW_MONTHS,
    reestimate_every_months: int = 12,
    cap_proportion: float = 0.01,
    allow_short_history: bool = False,
    max_iterations: int = 100,
    tolerance: float = 1e-5,
) -> DailyIPCAResult:
    """Estimate daily OOS IPCA residuals using prior-month characteristics.

    ``monthly_panel`` must contain month-end returns plus 46 normalized
    characteristics.  Gamma is estimated only from the preceding rolling
    monthly window.  On each daily date, the factor return is estimated
    cross-sectionally and the residual is therefore out of sample with respect
    to both Gamma and the stock characteristics.

    Composition matrices are intentionally not materialized here: an N-by-N
    matrix for every day can exceed hundreds of GB.  They can be reconstructed
    from the saved daily loadings as ``I - B pinv(B)``.
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
    missing_daily = sorted(required_daily.difference(daily_returns.columns))
    if missing_monthly:
        raise ValueError(f"monthly panel is missing columns: {missing_monthly}")
    if missing_daily:
        raise ValueError(f"daily returns are missing columns: {missing_daily}")
    if reestimate_every_months <= 0:
        raise ValueError("reestimate_every_months must be positive")

    monthly = monthly_panel.copy()
    monthly["date"] = pd.to_datetime(monthly["date"], errors="raise")
    monthly["date"] = monthly["date"].dt.to_period("M").dt.to_timestamp("M")
    monthly["ticker"] = monthly["ticker"].astype(str).str.upper()
    if cap_proportion < 0 or cap_proportion >= 100:
        raise ValueError("cap_proportion must be in [0, 100)")
    total_cap = monthly.groupby("date", sort=False)["market_cap"].transform("sum")
    monthly = monthly.loc[
        monthly["market_cap"].div(total_cap).ge(cap_proportion * 0.01)
    ].copy()
    dates = pd.DatetimeIndex(sorted(monthly["date"].unique()))
    validate_ipca_window(
        len(dates),
        window_months=window_months,
        allow_short_history=allow_short_history,
    )
    daily = daily_returns.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="raise")
    daily["ticker"] = daily["ticker"].astype(str).str.upper()

    residual_parts: list[pd.DataFrame] = []
    loading_parts: list[pd.DataFrame] = []
    fit_audit: list[dict[str, object]] = []
    for oos_idx in range(window_months, len(dates), reestimate_every_months):
        train_dates = dates[oos_idx - window_months : oos_idx]
        train_returns, train_chars = _monthly_arrays(monthly, train_dates)
        fit = fit_ipca_als(
            train_returns,
            train_chars,
            n_factors=n_factors,
            max_iterations=max_iterations,
            tolerance=tolerance,
        )
        next_idx = min(oos_idx + reestimate_every_months, len(dates))
        for char_date in dates[oos_idx - 1 : next_idx - 1]:
            next_month = char_date + pd.offsets.MonthEnd(1)
            z = monthly.loc[
                monthly["date"].eq(char_date),
                ["ticker", *CHARACTERISTIC_COLUMNS],
            ].dropna()
            if z.empty:
                continue
            beta = z[list(CHARACTERISTIC_COLUMNS)].to_numpy(float) @ fit.gamma
            load = pd.DataFrame(beta, columns=[f"beta_{k + 1}" for k in range(n_factors)])
            load.insert(0, "ticker", z["ticker"].to_numpy())
            load.insert(0, "characteristic_date", char_date)
            load.insert(0, "holding_month", next_month)
            loading_parts.append(load)

            days = daily.loc[
                daily["date"].dt.to_period("M").eq(next_month.to_period("M"))
                & daily["ticker"].isin(z["ticker"])
            ]
            beta_by_ticker = dict(zip(z["ticker"], beta, strict=True))
            for day, cross in days.groupby("date", sort=True):
                cross = cross.dropna(subset=["return"])
                if len(cross) <= n_factors:
                    continue
                b = np.vstack([beta_by_ticker[ticker] for ticker in cross["ticker"]])
                ret = cross["return"].to_numpy(float)
                factor = np.linalg.pinv(b.T @ b) @ b.T @ ret
                part = cross[["date", "ticker"]].copy()
                part["residual"] = ret - b @ factor
                residual_parts.append(part)
        fit_audit.append(
            {
                "train_start": train_dates[0].date().isoformat(),
                "train_end": train_dates[-1].date().isoformat(),
                "iterations": fit.iterations,
                "converged": fit.converged,
            }
        )

    if not residual_parts:
        raise ValueError("no daily IPCA residuals were produced")
    residuals = pd.concat(residual_parts, ignore_index=True).drop_duplicates(
        ["date", "ticker"], keep="last"
    )
    loadings = pd.concat(loading_parts, ignore_index=True).drop_duplicates(
        ["holding_month", "ticker"], keep="last"
    )
    audit: dict[str, object] = {
        "classification": (
            "paper-exact 240-month IPCA"
            if window_months == PAPER_WINDOW_MONTHS
            else "Korean short-history IPCA sensitivity"
        ),
        "characteristic_count": len(CHARACTERISTIC_COLUMNS),
        "n_factors": n_factors,
        "window_months": window_months,
        "paper_window_months": PAPER_WINDOW_MONTHS,
        "reestimate_every_months": reestimate_every_months,
        "cap_proportion_percent": cap_proportion,
        "residual_start": residuals["date"].min().date().isoformat(),
        "residual_end": residuals["date"].max().date().isoformat(),
        "residual_rows": len(residuals),
        "fits": fit_audit,
    }
    return DailyIPCAResult(residuals=residuals, loadings=loadings, audit=audit)
