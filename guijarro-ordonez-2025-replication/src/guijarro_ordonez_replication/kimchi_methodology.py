"""Strict primitives for the documented Kimchi Factor methodology.

These functions deliberately require canonical point-in-time inputs. They do not
fall back to the broader proxy universe used by the earlier diagnostic builder.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


FINANCIALS_EXCLUDED_FACTORS = frozenset({"SMB", "HML", "RMW", "CMA"})
SUPPORTED_SORT_FACTORS = FINANCIALS_EXCLUDED_FACTORS | {"MOM"}
SECURITY_MASTER_COLUMNS = {
    "ticker",
    "market",
    "is_common_stock",
    "is_listed",
    "is_spac",
    "is_pre_merger_spac",
    "is_trading_halt",
    "is_financial",
}


def _require(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def annual_yield_percent_to_period_return(
    annual_yield_percent: pd.Series | np.ndarray | float,
    *,
    periods_per_year: int,
) -> pd.Series | np.ndarray | float:
    """Convert an annual percent yield with geometric compounding."""

    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    return (1.0 + annual_yield_percent / 100.0) ** (1.0 / periods_per_year) - 1.0


def filter_rebalance_universe(
    cross_section: pd.DataFrame,
    *,
    factor: str,
) -> pd.DataFrame:
    """Apply the point-in-time Korean common-stock eligibility contract."""

    name = factor.upper()
    if name not in SUPPORTED_SORT_FACTORS:
        raise ValueError(f"Unsupported factor for universe filtering: {factor}")
    _require(cross_section, SECURITY_MASTER_COLUMNS, "rebalance cross-section")
    boolean_columns = sorted(SECURITY_MASTER_COLUMNS.difference({"ticker", "market"}))
    if cross_section[boolean_columns].isna().any().any():
        raise ValueError("security-master eligibility flags must not be missing")
    if cross_section["ticker"].duplicated().any():
        raise ValueError("rebalance cross-section has duplicate tickers")

    market = cross_section["market"].astype(str).str.upper()
    eligible = (
        market.isin({"KOSPI", "KOSDAQ"})
        & cross_section["is_common_stock"].eq(True)
        & cross_section["is_listed"].eq(True)
        & cross_section["is_spac"].eq(False)
        & cross_section["is_pre_merger_spac"].eq(False)
        & cross_section["is_trading_halt"].eq(False)
    )
    if name in FINANCIALS_EXCLUDED_FACTORS:
        eligible &= cross_section["is_financial"].eq(False)

    result = cross_section.loc[eligible].copy()
    result["market"] = market.loc[eligible]
    return result.reset_index(drop=True)


def assign_kospi_2x3_buckets(
    cross_section: pd.DataFrame,
    *,
    signal_column: str,
) -> pd.DataFrame:
    """Compute KOSPI 50/30/70 breakpoints and apply them to both markets."""

    _require(
        cross_section,
        {"ticker", "market", "market_cap", signal_column},
        "eligible sort cross-section",
    )
    if cross_section["ticker"].duplicated().any():
        raise ValueError("eligible sort cross-section has duplicate tickers")
    frame = cross_section.copy()
    frame["market_cap"] = pd.to_numeric(frame["market_cap"], errors="coerce")
    frame[signal_column] = pd.to_numeric(frame[signal_column], errors="coerce")
    size_sample = frame.loc[frame["market_cap"].gt(0)].copy()
    size_reference = size_sample.loc[
        size_sample["market"].astype(str).str.upper().eq("KOSPI")
    ]
    if size_reference.empty:
        raise ValueError("KOSPI breakpoint reference sample is empty")

    size_cut = float(size_reference["market_cap"].quantile(0.50))
    frame = size_sample.loc[size_sample[signal_column].notna()].copy()
    signal_reference = frame.loc[
        frame["market"].astype(str).str.upper().eq("KOSPI")
    ]
    if signal_reference.empty:
        raise ValueError("KOSPI signal breakpoint reference sample is empty")
    low_cut = float(signal_reference[signal_column].quantile(0.30))
    high_cut = float(signal_reference[signal_column].quantile(0.70))
    frame["size_bucket"] = np.where(frame["market_cap"].le(size_cut), "S", "B")
    frame["signal_bucket"] = np.select(
        [frame[signal_column].le(low_cut), frame[signal_column].gt(high_cut)],
        ["1", "3"],
        default="2",
    )
    frame["bucket"] = frame["size_bucket"] + frame["signal_bucket"]
    frame["size_breakpoint"] = size_cut
    frame["signal_30_breakpoint"] = low_cut
    frame["signal_70_breakpoint"] = high_cut
    return frame.reset_index(drop=True)


def assign_kospi_quintiles(
    cross_section: pd.DataFrame,
    *,
    signal_column: str,
) -> pd.DataFrame:
    """Apply KOSPI 20/40/60/80 signal breakpoints without size neutralization."""

    _require(
        cross_section,
        {"ticker", "market", signal_column},
        "eligible quintile cross-section",
    )
    if cross_section["ticker"].duplicated().any():
        raise ValueError("eligible quintile cross-section has duplicate tickers")
    frame = cross_section.copy()
    frame[signal_column] = pd.to_numeric(frame[signal_column], errors="coerce")
    frame = frame.loc[frame[signal_column].notna()].copy()
    reference = frame.loc[frame["market"].astype(str).str.upper().eq("KOSPI")]
    if reference.empty:
        raise ValueError("KOSPI quintile reference sample is empty")
    cuts = reference[signal_column].quantile([0.20, 0.40, 0.60, 0.80]).to_numpy()
    frame["quantile"] = np.select(
        [frame[signal_column].le(cut) for cut in cuts],
        ["Q1", "Q2", "Q3", "Q4"],
        default="Q5",
    )
    for percentile, cut in zip((20, 40, 60, 80), cuts, strict=True):
        frame[f"signal_{percentile}_breakpoint"] = float(cut)
    return frame.reset_index(drop=True)


def compute_accounting_signals(
    financials: pd.DataFrame,
    *,
    reporting_lag_months: int = 3,
) -> pd.DataFrame:
    """Calculate BM, OPE/BE, and asset growth under the annual timing rule.

    Monetary inputs must already use a common unit. ``total_assets`` is the
    formation year's prior-fiscal-year value and ``prior_total_assets`` is the
    preceding fiscal year's value. EBITDA is required directly; a proxy is not
    substituted here.
    """

    if reporting_lag_months < 0:
        raise ValueError("reporting_lag_months must be nonnegative")
    required = {
        "ticker",
        "formation_date",
        "fiscal_period",
        "market_cap",
        "total_equity",
        "noncontrolling_interest",
        "ebitda",
        "interest_expense",
        "total_assets",
        "prior_total_assets",
    }
    _require(financials, required, "annual financial input")
    frame = financials.copy()
    frame["formation_date"] = pd.to_datetime(frame["formation_date"], errors="raise")
    frame["fiscal_period"] = pd.to_datetime(frame["fiscal_period"], errors="raise")
    if frame.duplicated(["ticker", "formation_date"]).any():
        raise ValueError("annual financial input has duplicate ticker-formation keys")

    numeric = [
        "market_cap",
        "total_equity",
        "noncontrolling_interest",
        "ebitda",
        "interest_expense",
        "total_assets",
        "prior_total_assets",
    ]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame["noncontrolling_interest"] = frame["noncontrolling_interest"].fillna(0.0)
    frame["available_date"] = (
        frame["fiscal_period"]
        + pd.offsets.MonthEnd(0)
        + pd.DateOffset(months=reporting_lag_months)
    )
    prior_fiscal_year = frame["fiscal_period"].dt.year.eq(
        frame["formation_date"].dt.year.sub(1)
    )
    available = frame["available_date"].le(frame["formation_date"])
    june_formation = frame["formation_date"].dt.month.eq(6)
    frame = frame.loc[prior_fiscal_year & available & june_formation].copy()

    frame["book_equity"] = frame["total_equity"].sub(
        frame["noncontrolling_interest"]
    )
    frame = frame.loc[
        frame["book_equity"].gt(0) & frame["market_cap"].gt(0)
    ].copy()
    frame["book_to_market"] = frame["book_equity"].div(frame["market_cap"])
    frame["profitability"] = frame["ebitda"].sub(
        frame["interest_expense"]
    ).div(frame["book_equity"])
    valid_prior_assets = frame["prior_total_assets"].gt(0)
    frame["investment"] = np.nan
    frame.loc[valid_prior_assets, "investment"] = (
        frame.loc[valid_prior_assets, "total_assets"]
        .sub(frame.loc[valid_prior_assets, "prior_total_assets"])
        .div(frame.loc[valid_prior_assets, "prior_total_assets"])
    )
    signal_columns = ["book_to_market", "profitability", "investment"]
    frame[signal_columns] = frame[signal_columns].replace([np.inf, -np.inf], np.nan)
    return frame.reset_index(drop=True)
