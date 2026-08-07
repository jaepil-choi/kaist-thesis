"""Point-in-time-aware Korean Carhart factor construction primitives."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def prepare_monthly_stock_panel(prices: pd.DataFrame) -> pd.DataFrame:
    """Compound daily returns and retain month-end market capitalization."""

    _require(prices, {"date", "ticker", "return", "market_cap"}, "prices")
    frame = prices[["date", "ticker", "return", "market_cap"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["return"] = pd.to_numeric(frame["return"], errors="coerce")
    frame["market_cap"] = pd.to_numeric(frame["market_cap"], errors="coerce")
    if frame.duplicated(["date", "ticker"]).any():
        raise ValueError("prices has duplicate date-ticker keys")
    frame = frame.sort_values(["ticker", "date"])
    frame["month"] = frame["date"].dt.to_period("M").dt.to_timestamp("M")

    def compound(values: pd.Series) -> float:
        clean = values.dropna()
        return float((1.0 + clean).prod() - 1.0) if len(clean) else np.nan

    monthly_return = (
        frame.groupby(["ticker", "month"], sort=False)["return"]
        .agg(compound)
        .rename("monthly_return")
    )
    month_end_cap = (
        frame.dropna(subset=["market_cap"])
        .groupby(["ticker", "month"], sort=False)["market_cap"]
        .last()
    )
    monthly = pd.concat([monthly_return, month_end_cap], axis=1).reset_index()
    monthly = monthly.sort_values(["ticker", "month"]).reset_index(drop=True)
    gross = 1.0 + monthly["monthly_return"]
    monthly["momentum_12_2"] = (
        gross.groupby(monthly["ticker"], sort=False)
        .shift(1)
        .groupby(monthly["ticker"], sort=False)
        .rolling(11, min_periods=8)
        .apply(np.prod, raw=True)
        .reset_index(level=0, drop=True)
        - 1.0
    )
    return monthly


def derive_non_pit_book_equity(
    statement_facts: pd.DataFrame,
    *,
    reporting_lag_months: int,
    allow_non_pit: bool = False,
) -> pd.DataFrame:
    """Derive book equity only under an explicit non-PIT research override.

    The local statement dumps were collected in 2026 and do not preserve each
    historical public-release timestamp. Selecting a dump revision is therefore
    not an exact PIT operation. The default is a hard failure.
    """

    if not allow_non_pit:
        raise ValueError(
            "Statement facts lack historical announcement timestamps. "
            "Pass allow_non_pit=True only for a labeled sensitivity analysis."
        )
    if reporting_lag_months < 0:
        raise ValueError("reporting_lag_months must be nonnegative")
    required = {
        "ticker",
        "fiscal_period",
        "settlement_type",
        "statement_scope",
        "account_code",
        "numeric_value",
        "dump_last_modified",
    }
    _require(statement_facts, required, "statement_facts")
    frame = statement_facts.loc[
        statement_facts["statement_scope"].eq("consolidated")
        & statement_facts["settlement_type"].eq("D")
        & statement_facts["account_code"].eq("4001160000")
    ].copy()
    frame["fiscal_period"] = pd.to_datetime(frame["fiscal_period"], errors="raise")
    frame["dump_last_modified"] = pd.to_datetime(
        frame["dump_last_modified"], errors="coerce"
    )
    frame["numeric_value"] = pd.to_numeric(frame["numeric_value"], errors="coerce")
    logical_key = ["ticker", "fiscal_period", "settlement_type", "account_code"]
    frame = frame.sort_values(logical_key + ["dump_last_modified"])
    frame = frame.drop_duplicates(logical_key, keep="last")
    frame["available_date"] = (
        frame["fiscal_period"]
        + pd.offsets.MonthEnd(0)
        + pd.DateOffset(months=reporting_lag_months)
    )
    frame["book_equity"] = frame["numeric_value"] * 1000.0
    return frame[["ticker", "available_date", "book_equity"]].dropna()


def _weighted_return(group: pd.DataFrame) -> float:
    valid = group[["monthly_return", "formation_market_cap"]].dropna()
    valid = valid.loc[valid["formation_market_cap"].gt(0)]
    if valid.empty:
        return np.nan
    return float(
        np.average(valid["monthly_return"], weights=valid["formation_market_cap"])
    )


def _assign_annual_value_buckets(
    monthly: pd.DataFrame, book_equity: pd.DataFrame
) -> pd.DataFrame:
    june = monthly.loc[
        monthly["month"].dt.month.eq(6),
        ["month", "ticker", "market_cap"],
    ].copy()
    june["month"] = pd.to_datetime(june["month"], errors="raise").astype(
        "datetime64[ns]"
    )
    book = book_equity.copy()
    book["available_date"] = pd.to_datetime(
        book["available_date"], errors="raise"
    ).astype("datetime64[ns]")
    records: list[pd.DataFrame] = []
    for ticker, formation in june.groupby("ticker", sort=False):
        history = book.loc[book["ticker"].eq(ticker)].sort_values("available_date")
        if history.empty:
            continue
        matched = pd.merge_asof(
            formation.sort_values("month"),
            history[["available_date", "book_equity"]],
            left_on="month",
            right_on="available_date",
            direction="backward",
        )
        records.append(matched)
    if not records:
        return pd.DataFrame(columns=["formation_year", "ticker", "size_bucket", "bm_bucket"])
    formed = pd.concat(records, ignore_index=True).dropna(subset=["market_cap", "book_equity"])
    formed = formed.loc[formed["market_cap"].gt(0) & formed["book_equity"].gt(0)].copy()
    formed["book_to_market"] = formed["book_equity"] / formed["market_cap"]

    grouped = formed.groupby("month", sort=False)
    size_cut = grouped["market_cap"].transform("median")
    low_cut = grouped["book_to_market"].transform(lambda values: values.quantile(0.30))
    high_cut = grouped["book_to_market"].transform(lambda values: values.quantile(0.70))
    formed["size_bucket"] = np.where(formed["market_cap"].le(size_cut), "S", "B")
    formed["bm_bucket"] = np.select(
        [formed["book_to_market"].le(low_cut), formed["book_to_market"].ge(high_cut)],
        ["L", "H"],
        default="M",
    )
    formed["formation_year"] = formed["month"].dt.year
    return formed[["formation_year", "ticker", "size_bucket", "bm_bucket"]]


def build_carhart_equity_factors(
    monthly_stock: pd.DataFrame, book_equity: pd.DataFrame
) -> pd.DataFrame:
    """Construct monthly MKT, SMB, HML, and MOM with lagged formation data."""

    _require(
        monthly_stock,
        {"month", "ticker", "monthly_return", "market_cap", "momentum_12_2"},
        "monthly_stock",
    )
    _require(book_equity, {"ticker", "available_date", "book_equity"}, "book_equity")
    monthly = monthly_stock.copy().sort_values(["ticker", "month"])
    monthly["month"] = pd.to_datetime(monthly["month"], errors="raise")
    monthly["formation_market_cap"] = monthly.groupby("ticker")["market_cap"].shift(1)
    monthly["formation_momentum"] = monthly.groupby("ticker")["momentum_12_2"].shift(1)

    market = monthly.groupby("month", sort=True).apply(_weighted_return).rename("mkt")
    membership = _assign_annual_value_buckets(monthly, book_equity)
    monthly["formation_year"] = np.where(
        monthly["month"].dt.month.le(6), monthly["month"].dt.year - 1, monthly["month"].dt.year
    )
    value_panel = monthly.merge(
        membership, on=["formation_year", "ticker"], how="inner", validate="many_to_one"
    )
    value_portfolios = (
        value_panel.groupby(["month", "size_bucket", "bm_bucket"], sort=True)
        .apply(_weighted_return)
        .unstack(["size_bucket", "bm_bucket"])
    )
    required_portfolios = [("S", "L"), ("S", "M"), ("S", "H"), ("B", "L"), ("B", "M"), ("B", "H")]
    for column in required_portfolios:
        if column not in value_portfolios:
            value_portfolios[column] = np.nan
    smb = value_portfolios[[('S', 'L'), ('S', 'M'), ('S', 'H')]].mean(axis=1, skipna=False) - value_portfolios[[('B', 'L'), ('B', 'M'), ('B', 'H')]].mean(axis=1, skipna=False)
    hml = value_portfolios[[('S', 'H'), ('B', 'H')]].mean(axis=1, skipna=False) - value_portfolios[[('S', 'L'), ('B', 'L')]].mean(axis=1, skipna=False)

    momentum_panel = monthly.dropna(
        subset=["formation_market_cap", "formation_momentum"]
    ).copy()
    momentum_grouped = momentum_panel.groupby("month", sort=False)
    size_cut = momentum_grouped["formation_market_cap"].transform("median")
    low_cut = momentum_grouped["formation_momentum"].transform(
        lambda values: values.quantile(0.30)
    )
    high_cut = momentum_grouped["formation_momentum"].transform(
        lambda values: values.quantile(0.70)
    )
    momentum_panel["size_bucket"] = np.where(
        momentum_panel["formation_market_cap"].le(size_cut), "S", "B"
    )
    momentum_panel["momentum_bucket"] = np.select(
        [
            momentum_panel["formation_momentum"].le(low_cut),
            momentum_panel["formation_momentum"].ge(high_cut),
        ],
        ["L", "H"],
        default="M",
    )
    momentum_portfolios = (
        momentum_panel.groupby(["month", "size_bucket", "momentum_bucket"], sort=True)
        .apply(_weighted_return)
        .unstack(["size_bucket", "momentum_bucket"])
    )
    for column in [("S", "L"), ("S", "H"), ("B", "L"), ("B", "H")]:
        if column not in momentum_portfolios:
            momentum_portfolios[column] = np.nan
    mom = momentum_portfolios[[('S', 'H'), ('B', 'H')]].mean(axis=1, skipna=False) - momentum_portfolios[[('S', 'L'), ('B', 'L')]].mean(axis=1, skipna=False)
    return (
        pd.concat([market, smb.rename("smb"), hml.rename("hml"), mom.rename("mom")], axis=1)
        .reset_index()
        .sort_values("month")
        .reset_index(drop=True)
    )


def attach_risk_free(factors: pd.DataFrame, risk_free: pd.DataFrame) -> pd.DataFrame:
    """Attach a decimal monthly risk-free return and expose the input contract."""

    _require(factors, {"month", "mkt", "smb", "hml", "mom"}, "factors")
    _require(risk_free, {"month", "rf"}, "risk_free")
    rf = risk_free.copy()
    rf["month"] = pd.to_datetime(rf["month"], errors="raise")
    rf["rf"] = pd.to_numeric(rf["rf"], errors="raise")
    if rf["month"].duplicated().any():
        raise ValueError("risk_free has duplicate months")
    result = factors.merge(rf, on="month", how="left", validate="one_to_one")
    if result["rf"].isna().any():
        raise ValueError("risk_free does not cover every factor month")
    result["mkt_rf"] = result["mkt"] - result["rf"]
    return result[["month", "mkt_rf", "smb", "hml", "mom", "rf"]]
