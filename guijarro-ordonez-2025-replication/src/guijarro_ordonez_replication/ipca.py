"""Instrumented PCA estimation with explicit exact and short-history modes."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.decomposition import PCA

from .characteristics import CHARACTERISTIC_COLUMNS


FloatArray = NDArray[np.float64]
PAPER_WINDOW_MONTHS = 240
PAPER_GAMMA_RIDGE = 0.0


class ShortHistoryIPCAWarning(UserWarning):
    """The IPCA estimation window is shorter than the paper's 240 months."""


class ReducedCharacteristicIPCAWarning(UserWarning):
    """The IPCA estimation uses fewer than the paper's 46 characteristics."""


class RidgeIPCAWarning(UserWarning):
    """Gamma is penalized; the paper's estimator has no ridge term."""


@dataclass(frozen=True)
class IPCAFit:
    """One IPCA alternating-least-squares estimate."""

    gamma: FloatArray
    factors: tuple[FloatArray, ...]
    iterations: int
    converged: bool
    final_delta: float
    gamma_ridge: float = PAPER_GAMMA_RIDGE


@dataclass(frozen=True)
class DailyIPCAResult:
    """Long-form daily IPCA residuals and an estimation audit."""

    residuals: pd.DataFrame
    loadings: pd.DataFrame
    audit: dict[str, object]


def ipca_run_tag(
    *,
    factors: int,
    initial_months: int,
    window_months: int,
    n_characteristics: int | None = None,
    gamma_ridge: float = PAPER_GAMMA_RIDGE,
) -> str:
    """Build the artifact tag for one IPCA specification.

    The paper's specification keeps the historical
    ``k{K}_i{initial}_w{window}`` tag unchanged so that existing outputs stay
    addressable.  Deviating runs append the instrument count and the ridge
    intensity.
    """

    tag = f"k{factors}_i{initial_months}_w{window_months}"
    if (
        n_characteristics is not None
        and n_characteristics != len(CHARACTERISTIC_COLUMNS)
    ):
        tag += f"_c{n_characteristics}"
    if gamma_ridge != PAPER_GAMMA_RIDGE:
        tag += "_r" + f"{gamma_ridge:g}".replace(".", "p").replace("-", "m")
    return tag


def select_characteristics_by_coverage(
    coverage: Mapping[str, float],
    *,
    threshold: float,
) -> tuple[str, ...]:
    """Return the characteristics observed at least ``threshold`` of the time.

    ``coverage`` is the raw non-missing proportion recorded in
    ``characteristic_audit.json``.  The result keeps the canonical
    ``CHARACTERISTIC_COLUMNS`` order so that Gamma rows stay comparable across
    runs.  A threshold of 0 reproduces the paper's full 46-column instrument
    set.
    """

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    missing = sorted(set(CHARACTERISTIC_COLUMNS).difference(coverage))
    if missing:
        raise ValueError(f"coverage is missing characteristics: {missing}")
    selected = tuple(
        column
        for column in CHARACTERISTIC_COLUMNS
        if float(coverage[column]) >= threshold
    )
    if not selected:
        raise ValueError(f"no characteristic reaches coverage {threshold}")
    return selected


def validate_characteristic_columns(
    columns: Sequence[str] | None,
) -> tuple[str, ...]:
    """Validate an instrument subset and warn when it is not the paper's 46."""

    if columns is None:
        return tuple(CHARACTERISTIC_COLUMNS)
    selected = tuple(columns)
    if not selected:
        raise ValueError("characteristic_columns must not be empty")
    unknown = sorted(set(selected).difference(CHARACTERISTIC_COLUMNS))
    if unknown:
        raise ValueError(f"unknown characteristics: {unknown}")
    if len(set(selected)) != len(selected):
        raise ValueError("characteristic_columns contains duplicates")
    if len(selected) != len(CHARACTERISTIC_COLUMNS):
        warnings.warn(
            f"REDUCED_CHARACTERISTICS: estimating Gamma on {len(selected)} of "
            f"{len(CHARACTERISTIC_COLUMNS)} paper characteristics.",
            ReducedCharacteristicIPCAWarning,
            stacklevel=2,
        )
    return selected


def validate_gamma_ridge(gamma_ridge: float) -> float:
    """Validate the Gamma ridge penalty and warn for any non-paper value."""

    penalty = float(gamma_ridge)
    if not np.isfinite(penalty) or penalty < 0.0:
        raise ValueError("gamma_ridge must be a finite, non-negative number")
    if penalty != PAPER_GAMMA_RIDGE:
        warnings.warn(
            f"RIDGE_GAMMA: penalizing Gamma with relative ridge {penalty:g}; "
            "the paper's estimator solves the unpenalized normal equations.",
            RidgeIPCAWarning,
            stacklevel=2,
        )
    return penalty


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
        left = beta_t.T @ beta_t
        right = beta_t.T @ ret_t
        try:
            factors.append(np.linalg.solve(left, right))
        except np.linalg.LinAlgError:
            factors.append(np.linalg.pinv(left) @ right)
    return tuple(factors)


def _gamma_step(
    returns: tuple[FloatArray, ...],
    characteristics: tuple[FloatArray, ...],
    factors: tuple[FloatArray, ...],
    *,
    n_characteristics: int,
    n_factors: int,
    ridge: float = PAPER_GAMMA_RIDGE,
) -> FloatArray:
    size = n_characteristics * n_factors
    left = np.zeros((size, size), dtype=float)
    right = np.zeros(size, dtype=float)
    for ret_t, z_t, factor_t in zip(
        returns, characteristics, factors, strict=True
    ):
        # If row i of the conceptual design matrix is kron(z_i, f_t), then
        # X'X = kron(Z'Z, f_t f_t') and X'r = kron(Z'r, f_t).  Computing these
        # sufficient statistics directly is algebraically identical but avoids
        # materializing an N_t-by-(L*K) matrix for every month and iteration.
        left += np.kron(z_t.T @ z_t, np.outer(factor_t, factor_t))
        right += np.kron(z_t.T @ ret_t, factor_t)
    if ridge > 0.0:
        # Scale-free ridge: the raw normal-equation matrix grows with the
        # number of months and the cross-section size, so a bare lambda*I is
        # not comparable across windows or characteristic subsets.  Penalizing
        # by the mean diagonal makes `ridge` a dimensionless shrinkage
        # intensity.  This term does not exist in the paper's estimator.
        scale = float(np.trace(left)) / size
        left = left + ridge * scale * np.eye(size)
    try:
        solution = np.linalg.solve(left, right)
    except np.linalg.LinAlgError:
        solution = np.linalg.pinv(left) @ right
    return solution.reshape(n_characteristics, n_factors)


def fit_ipca_als(
    returns: tuple[FloatArray, ...],
    characteristics: tuple[FloatArray, ...],
    *,
    n_factors: int,
    max_iterations: int = 1500,
    tolerance: float = 1e-3,
    initial_gamma: FloatArray | None = None,
    gamma_ridge: float = PAPER_GAMMA_RIDGE,
) -> IPCAFit:
    """Fit the paper/reference-code IPCA alternating least-squares system.

    ``gamma_ridge`` defaults to the paper's zero penalty.  A positive value is
    a deliberate deviation and is recorded on the returned fit.
    """

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

    if initial_gamma is None:
        # Match the public replication code's sklearn PCA(X.T)
        # initialization, including sklearn's centering and sign convention.
        managed = np.vstack(
            [
                z_t.T @ ret_t / len(ret_t)
                for ret_t, z_t in zip(returns, characteristics, strict=True)
            ]
        )
        components = PCA(n_components=n_factors).fit(managed.T).components_
        factors = tuple(
            components[:, month].copy() for month in range(len(returns))
        )
        gamma = np.zeros((n_characteristics, n_factors), dtype=float)
    else:
        gamma = np.asarray(initial_gamma, dtype=float).copy()
        if gamma.shape != (n_characteristics, n_factors):
            raise ValueError("initial_gamma has an incompatible shape")
        factors = tuple()
    converged = False
    delta = float("inf")
    for iteration in range(1, max_iterations + 1):
        if initial_gamma is not None:
            factors = _factor_step(returns, characteristics, gamma)
        updated = _gamma_step(
            returns,
            characteristics,
            factors,
            n_characteristics=n_characteristics,
            n_factors=n_factors,
            ridge=gamma_ridge,
        )
        if initial_gamma is None:
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
        final_delta=delta,
        gamma_ridge=float(gamma_ridge),
    )


def _ipca_classification(deviations: Sequence[str]) -> str:
    """Label one IPCA specification by how it departs from the paper."""

    if not deviations:
        return "paper-exact 240-month IPCA"
    if list(deviations) == ["short-history"]:
        # Preserved verbatim: earlier K=1 audits on disk use this exact label.
        return "Korean short-history IPCA sensitivity"
    return "Korean IPCA sensitivity (" + ", ".join(deviations) + ")"


def prepare_ipca_monthly_panel(
    monthly_panel: pd.DataFrame,
    *,
    cap_proportion: float = 0.01,
) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """Normalize dates and apply the paper's small-cap exclusion.

    Returns the filtered panel and its sorted month-end index so that the
    estimator and any diagnostic share one universe definition.
    """

    if cap_proportion < 0 or cap_proportion >= 100:
        raise ValueError("cap_proportion must be in [0, 100)")
    monthly = monthly_panel.copy()
    monthly["date"] = pd.to_datetime(monthly["date"], errors="raise")
    monthly["date"] = monthly["date"].dt.to_period("M").dt.to_timestamp("M")
    monthly["ticker"] = monthly["ticker"].astype(str).str.upper()
    total_cap = monthly.groupby("date", sort=False)["market_cap"].transform("sum")
    monthly = monthly.loc[
        monthly["market_cap"].div(total_cap).ge(cap_proportion * 0.01)
    ].copy()
    dates = pd.DatetimeIndex(sorted(monthly["date"].unique()))
    return monthly, dates


def _monthly_arrays(
    panel: pd.DataFrame,
    dates: pd.DatetimeIndex,
    columns: Sequence[str] = CHARACTERISTIC_COLUMNS,
) -> tuple[tuple[FloatArray, ...], tuple[FloatArray, ...]]:
    selected = list(columns)
    returns: list[FloatArray] = []
    chars: list[FloatArray] = []
    for date in dates:
        month = panel.loc[panel["date"].eq(date)].dropna(
            subset=["return", *selected]
        )
        if len(month) == 0:
            raise ValueError(f"no complete IPCA observations for {date.date()}")
        returns.append(month["return"].to_numpy(float))
        chars.append(month[selected].to_numpy(float))
    return tuple(returns), tuple(chars)


def estimate_daily_ipca_residuals(
    monthly_panel: pd.DataFrame,
    daily_returns: pd.DataFrame,
    *,
    n_factors: int,
    initial_months: int | None = None,
    window_months: int = PAPER_WINDOW_MONTHS,
    reestimate_every_months: int = 12,
    cap_proportion: float = 0.01,
    allow_short_history: bool = False,
    max_iterations: int = 1500,
    tolerance: float = 1e-3,
    characteristic_columns: Sequence[str] | None = None,
    gamma_ridge: float = PAPER_GAMMA_RIDGE,
    progress: Callable[[dict[str, object]], None] | None = None,
    daily_return_definition: str = "caller-supplied return",
    require_convergence: bool = True,
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

    ``characteristic_columns`` restricts the instrument set and
    ``gamma_ridge`` penalizes the Gamma normal equations.  Both default to the
    paper's specification and both emit a warning when they do not.
    """

    selected_columns = validate_characteristic_columns(characteristic_columns)
    penalty = validate_gamma_ridge(gamma_ridge)
    required_monthly = {
        "date",
        "ticker",
        "return",
        "market_cap",
        *selected_columns,
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

    monthly, dates = prepare_ipca_monthly_panel(
        monthly_panel, cap_proportion=cap_proportion
    )
    if initial_months is None:
        initial_months = window_months
    if initial_months < window_months:
        raise ValueError("initial_months must be at least window_months")
    validate_ipca_window(
        len(dates),
        window_months=window_months,
        allow_short_history=allow_short_history,
    )
    if len(dates) <= initial_months:
        raise ValueError(
            f"IPCA needs more than {initial_months} pre-OOS months but only "
            f"{len(dates)} are available"
        )
    daily = daily_returns.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="raise")
    daily["ticker"] = daily["ticker"].astype(str).str.upper()

    residual_parts: list[pd.DataFrame] = []
    loading_parts: list[pd.DataFrame] = []
    fit_audit: list[dict[str, object]] = []
    previous_gamma: FloatArray | None = None
    for oos_idx in range(initial_months, len(dates), reestimate_every_months):
        train_dates = dates[oos_idx - window_months : oos_idx]
        if progress is not None:
            progress(
                {
                    "event": "fit_started",
                    "train_start": train_dates[0].date().isoformat(),
                    "train_end": train_dates[-1].date().isoformat(),
                }
            )
        train_returns, train_chars = _monthly_arrays(
            monthly, train_dates, selected_columns
        )
        fit = fit_ipca_als(
            train_returns,
            train_chars,
            n_factors=n_factors,
            max_iterations=(
                max_iterations if previous_gamma is None else max_iterations // 2
            ),
            tolerance=tolerance,
            initial_gamma=previous_gamma,
            gamma_ridge=penalty,
        )
        if require_convergence and not fit.converged:
            raise RuntimeError(
                "IPCA ALS did not converge for training window "
                f"{train_dates[0].date()} to {train_dates[-1].date()}; "
                f"iterations={fit.iterations}, final_delta={fit.final_delta:.6g}"
            )
        previous_gamma = fit.gamma
        next_idx = min(oos_idx + reestimate_every_months, len(dates))
        for char_date in dates[oos_idx - 1 : next_idx - 1]:
            next_month = char_date + pd.offsets.MonthEnd(1)
            z = monthly.loc[
                monthly["date"].eq(char_date),
                ["ticker", *selected_columns],
            ].dropna()
            if z.empty:
                continue
            beta = z[list(selected_columns)].to_numpy(float) @ fit.gamma
            load = pd.DataFrame(beta, columns=[f"beta_{k + 1}" for k in range(n_factors)])
            load.insert(0, "ticker", z["ticker"].to_numpy())
            load.insert(0, "characteristic_date", char_date)
            load.insert(0, "holding_month", next_month)
            loading_parts.append(load)

            days = daily.loc[
                daily["date"].dt.to_period("M").eq(next_month.to_period("M"))
                & daily["ticker"].isin(z["ticker"])
            ]
            if days.empty or len(z) <= n_factors:
                continue
            tickers = z["ticker"].to_numpy()
            return_matrix = days.pivot(
                index="date", columns="ticker", values="return"
            ).reindex(columns=tickers)
            factor_projection = np.linalg.pinv(beta.T @ beta) @ beta.T
            for day, row in return_matrix.sort_index().iterrows():
                observed = row.notna().to_numpy()
                ret = row.fillna(0.0).to_numpy(float)
                factor = factor_projection @ ret
                residual = ret - beta @ factor
                residual[~observed] = 0.0
                part = pd.DataFrame(
                    {
                        "date": day,
                        "ticker": tickers,
                        "residual": residual,
                        "return_observed": observed,
                    }
                )
                residual_parts.append(part)
        fit_audit.append(
            {
                "train_start": train_dates[0].date().isoformat(),
                "train_end": train_dates[-1].date().isoformat(),
                "iterations": fit.iterations,
                "converged": fit.converged,
                "final_delta": fit.final_delta,
                "gamma_max_abs": float(np.max(np.abs(fit.gamma))),
            }
        )
        if progress is not None:
            progress({"event": "fit_completed", **fit_audit[-1]})

    if not residual_parts:
        raise ValueError("no daily IPCA residuals were produced")
    residuals = pd.concat(residual_parts, ignore_index=True).drop_duplicates(
        ["date", "ticker"], keep="last"
    )
    loadings = pd.concat(loading_parts, ignore_index=True).drop_duplicates(
        ["holding_month", "ticker"], keep="last"
    )
    deviations: list[str] = []
    if window_months != PAPER_WINDOW_MONTHS:
        deviations.append("short-history")
    if len(selected_columns) != len(CHARACTERISTIC_COLUMNS):
        deviations.append("reduced-characteristics")
    if penalty != PAPER_GAMMA_RIDGE:
        deviations.append("ridge-gamma")
    audit: dict[str, object] = {
        "classification": _ipca_classification(deviations),
        "deviations": deviations,
        "characteristic_count": len(selected_columns),
        "paper_characteristic_count": len(CHARACTERISTIC_COLUMNS),
        "characteristic_columns": list(selected_columns),
        "gamma_ridge": penalty,
        "paper_gamma_ridge": PAPER_GAMMA_RIDGE,
        "n_factors": n_factors,
        "initial_months": initial_months,
        "window_months": window_months,
        "paper_window_months": PAPER_WINDOW_MONTHS,
        "reestimate_every_months": reestimate_every_months,
        "max_iterations": max_iterations,
        "tolerance": tolerance,
        "daily_return_definition": daily_return_definition,
        "cap_proportion_percent": cap_proportion,
        "residual_start": residuals["date"].min().date().isoformat(),
        "residual_end": residuals["date"].max().date().isoformat(),
        "residual_rows": len(residuals),
        "fits": fit_audit,
    }
    return DailyIPCAResult(residuals=residuals, loadings=loadings, audit=audit)
