"""Exact documented Kimchi-factor construction on the available Korean data.

The accounting source is a latest-revision snapshot without announcement
timestamps.  The fixed three-month lag is therefore implemented exactly, but
the accounting result remains a labelled non-PIT sensitivity.  Stock returns
are the local price-return series and exclude cash dividends.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from .kimchi_methodology import (
    annual_yield_percent_to_period_return,
    assign_kospi_2x3_buckets,
    assign_kospi_quintiles,
    filter_rebalance_universe,
)


ACCOUNT_CODES = {
    "total_assets": ("4001110000",),
    "total_liabilities": ("4001140000",),
    "total_equity": ("4001160000", "4001570000"),
    "controlling_equity": ("4001160050",),
    "noncontrolling_interest": ("4001167500", "4001550000"),
    "operating_income": ("4001230000",),
    "interest_expense": ("4001250100",),
    "depreciation": ("4001410500",),
    "amortization": ("4001410600",),
}
ANNUAL_SIGNALS = {
    "HML": "book_to_market",
    "RMW": "profitability",
    "CMA": "investment",
}
FACTOR_ORDER = ("RM", "RMRF", "SMB", "HML", "RMW", "CMA", "MOM", "RF")


@dataclass(frozen=True)
class ExactKimchiResult:
    """All reproducible artifacts emitted by the strict builder."""

    daily_returns: pd.DataFrame
    monthly_returns: pd.DataFrame
    daily_2x3_buckets: pd.DataFrame
    monthly_2x3_buckets: pd.DataFrame
    daily_quintile_buckets: pd.DataFrame
    monthly_quintile_buckets: pd.DataFrame
    annual_memberships: pd.DataFrame
    momentum_memberships: pd.DataFrame
    accounting_signals: pd.DataFrame
    audit: dict[str, object]


def _require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def load_market_snapshots(path: str | Path) -> pd.DataFrame:
    """Load the bounded FGSC extract, normalizing SQLPlus-truncated headers."""

    names = ["ticker", "date", "isin", "fgsc_code", "market_code", "spac_yn"]
    frame = pd.read_csv(
        path,
        header=0,
        names=names,
        dtype=str,
        encoding="utf-8-sig",
    )
    if frame.shape[1] != len(names):
        raise ValueError("FGSC snapshot must have exactly six positional columns")
    frame["date"] = pd.to_datetime(frame["date"], format="%Y%m%d", errors="raise")
    frame["ticker"] = frame["ticker"].str.upper()
    if frame.duplicated(["date", "ticker"]).any():
        raise ValueError("FGSC snapshot has duplicate date-ticker keys")
    if not set(frame["market_code"].dropna().unique()).issubset({"1", "2"}):
        raise ValueError("FGSC market code must be 1 (KOSPI) or 2 (KOSDAQ)")
    if not set(frame["spac_yn"].dropna().unique()).issubset({"0", "1"}):
        raise ValueError("FGSC SPAC flag must be 0 or 1")
    frame["market"] = frame["market_code"].map({"1": "KOSPI", "2": "KOSDAQ"})
    frame["is_common_stock"] = True
    frame["is_listed"] = True
    frame["is_spac"] = frame["spac_yn"].eq("1")
    frame["is_pre_merger_spac"] = frame["is_spac"]
    frame["is_financial"] = frame["fgsc_code"].str.startswith("FGSC.40")
    return frame.sort_values(["date", "ticker"]).reset_index(drop=True)


def load_price_panel(
    path: str | Path,
    *,
    start: str | pd.Timestamp = "2017-01-01",
) -> pd.DataFrame:
    """Read raw close returns and recompute ME as close times common shares."""

    dataset = ds.dataset(path, format="parquet")
    table = dataset.to_table(
        columns=[
            "date",
            "ticker",
            "종가",
            "return",
            "유통주식수",
            "market_cap",
            "is_trading_halt",
        ],
        filter=ds.field("date") >= pd.Timestamp(start),
    )
    frame = table.to_pandas()
    frame = frame.rename(
        columns={"종가": "raw_close", "유통주식수": "listed_common_shares"}
    )
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    numeric = ["raw_close", "return", "listed_common_shares", "market_cap"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    if frame.duplicated(["date", "ticker"]).any():
        raise ValueError("price panel has duplicate date-ticker keys")
    frame["calculated_market_cap"] = frame["raw_close"].mul(
        frame["listed_common_shares"]
    )
    comparable = frame[["market_cap", "calculated_market_cap"]].dropna()
    if not comparable["market_cap"].eq(comparable["calculated_market_cap"]).all():
        raise ValueError("stored market cap differs from raw close times share count")
    frame["market_cap"] = frame["calculated_market_cap"]
    frame["is_trading_halt"] = frame["is_trading_halt"].fillna(False).astype(bool)
    frame = frame.sort_values(["ticker", "date"]).reset_index(drop=True)
    grouped = frame.groupby("ticker", sort=False)
    frame["lag_market_cap"] = grouped["market_cap"].shift(1)
    lag_date = grouped["date"].shift(1)
    frame.loc[frame["date"].sub(lag_date).dt.days.gt(10), "lag_market_cap"] = np.nan
    frame["formation_year"] = np.where(
        frame["date"].dt.month.ge(7),
        frame["date"].dt.year,
        frame["date"].dt.year - 1,
    )
    frame["holding_month"] = frame["date"].dt.to_period("M")
    return frame


def load_statement_facts(
    path: str | Path,
    *,
    first_fiscal_year: int = 2016,
) -> pd.DataFrame:
    """Read only verified annual consolidated accounts needed by the method."""

    dataset = ds.dataset(path, format="parquet", partitioning="hive")
    codes = sorted({code for candidates in ACCOUNT_CODES.values() for code in candidates})
    predicate = (
        (ds.field("statement_scope") == "consolidated")
        & (ds.field("settlement_type") == "D")
        & (ds.field("fiscal_year") >= first_fiscal_year)
        & ds.field("account_code").isin(codes)
    )
    columns = [
        "ticker",
        "fiscal_period",
        "fiscal_year",
        "settlement_type",
        "statement_scope",
        "account_code",
        "numeric_value",
        "dump_last_modified",
    ]
    return dataset.to_table(columns=columns, filter=predicate).to_pandas()


def derive_accounting_signals(
    statement_facts: pd.DataFrame,
    *,
    reporting_lag_months: int = 3,
) -> pd.DataFrame:
    """Create annual BE, BM inputs, OPE/BE, and asset growth in KRW."""

    if reporting_lag_months != 3:
        raise ValueError("the documented Kimchi methodology requires a 3-month lag")
    required = {
        "ticker",
        "fiscal_period",
        "fiscal_year",
        "settlement_type",
        "statement_scope",
        "account_code",
        "numeric_value",
        "dump_last_modified",
    }
    _require(statement_facts, required, "statement facts")
    codes = {code for candidates in ACCOUNT_CODES.values() for code in candidates}
    frame = statement_facts.loc[
        statement_facts["statement_scope"].eq("consolidated")
        & statement_facts["settlement_type"].eq("D")
        & statement_facts["account_code"].isin(codes)
    ].copy()
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame["fiscal_period"] = pd.to_datetime(frame["fiscal_period"], errors="raise")
    frame["dump_last_modified"] = pd.to_datetime(
        frame["dump_last_modified"], errors="coerce"
    )
    frame["numeric_value"] = pd.to_numeric(frame["numeric_value"], errors="coerce")
    logical_key = ["ticker", "fiscal_period", "account_code"]
    frame = frame.sort_values([*logical_key, "dump_last_modified"])
    frame = frame.drop_duplicates(logical_key, keep="last")

    code_to_item = {
        code: item for item, candidates in ACCOUNT_CODES.items() for code in candidates
    }
    code_priority = {
        code: priority
        for candidates in ACCOUNT_CODES.values()
        for priority, code in enumerate(candidates)
    }
    frame["item"] = frame["account_code"].map(code_to_item)
    frame["code_priority"] = frame["account_code"].map(code_priority)
    item_key = ["ticker", "fiscal_period", "item"]
    frame = frame.sort_values([*item_key, "code_priority"])
    frame = frame.drop_duplicates(item_key, keep="first")
    wide = frame.pivot(
        index=["ticker", "fiscal_period"], columns="item", values="numeric_value"
    ).reset_index()
    for item in ACCOUNT_CODES:
        if item not in wide:
            wide[item] = np.nan
    wide["fiscal_year"] = wide["fiscal_period"].dt.year
    wide = wide.sort_values(["ticker", "fiscal_period"]).reset_index(drop=True)
    # Nineteen observed issuer-years contain two annual D rows because the
    # issuer changed its fiscal year-end.  The June Y formation rule calls for
    # the last annual statement ending in calendar year Y-1.
    wide = wide.drop_duplicates(["ticker", "fiscal_year"], keep="last")
    wide = wide.sort_values(["ticker", "fiscal_period"]).reset_index(drop=True)

    nci = wide["noncontrolling_interest"].fillna(0.0)
    component_be = wide["total_equity"].sub(nci)
    balance_sheet_be = wide["total_assets"].sub(wide["total_liabilities"]).sub(nci)
    wide["book_equity_thousand"] = (
        component_be.combine_first(wide["controlling_equity"])
        .combine_first(balance_sheet_be)
    )
    wide["book_equity_source"] = np.select(
        [
            component_be.notna(),
            wide["controlling_equity"].notna(),
            balance_sheet_be.notna(),
        ],
        [
            "total_equity_minus_nci",
            "controlling_equity_fallback",
            "assets_minus_liabilities_minus_nci_fallback",
        ],
        default="missing",
    )
    wide["ebitda_thousand"] = (
        wide["operating_income"] + wide["depreciation"] + wide["amortization"]
    )
    previous_assets = wide.groupby("ticker", sort=False)["total_assets"].shift(1)
    previous_period = wide.groupby("ticker", sort=False)["fiscal_period"].shift(1)
    annual_gap = wide["fiscal_period"].sub(previous_period).dt.days.between(300, 450)
    wide["prior_total_assets_thousand"] = previous_assets.where(annual_gap)
    wide["available_date"] = (
        wide["fiscal_period"]
        + pd.offsets.MonthEnd(0)
        + pd.DateOffset(months=reporting_lag_months)
    )
    monetary = [
        "book_equity_thousand",
        "ebitda_thousand",
        "interest_expense",
        "total_assets",
        "prior_total_assets_thousand",
    ]
    for column in monetary:
        wide[column.removesuffix("_thousand") + "_krw"] = wide[column].mul(1_000.0)
    keep = [
        "ticker",
        "fiscal_period",
        "fiscal_year",
        "available_date",
        "book_equity_source",
        "book_equity_krw",
        "ebitda_krw",
        "interest_expense_krw",
        "total_assets_krw",
        "prior_total_assets_krw",
    ]
    return wide[keep].replace([np.inf, -np.inf], np.nan).reset_index(drop=True)


def _formation_cross_sections(
    snapshots: pd.DataFrame,
    prices: pd.DataFrame,
) -> pd.DataFrame:
    price_columns = [
        "date",
        "ticker",
        "raw_close",
        "listed_common_shares",
        "market_cap",
        "is_trading_halt",
    ]
    cross = snapshots.merge(
        prices[price_columns],
        on=["date", "ticker"],
        how="left",
        validate="one_to_one",
    )
    cross["is_trading_halt"] = cross["is_trading_halt"].fillna(True).astype(bool)
    cross["formation_year"] = cross["date"].dt.year
    cross["formation_month"] = cross["date"].dt.to_period("M")
    return cross


def build_annual_memberships(
    snapshots: pd.DataFrame,
    prices: pd.DataFrame,
    accounting: pd.DataFrame,
) -> pd.DataFrame:
    """Form June KOSPI-breakpoint portfolios for HML, RMW, CMA, and SMB."""

    june = _formation_cross_sections(
        snapshots.loc[snapshots["date"].dt.month.eq(6)].copy(), prices
    )
    accounting = accounting.copy()
    accounting["formation_year"] = accounting["fiscal_year"].add(1)
    merged = june.merge(
        accounting,
        on=["ticker", "formation_year"],
        how="left",
        validate="one_to_one",
    )
    valid_timing = merged["available_date"].le(merged["date"])
    merged.loc[~valid_timing.fillna(False), "book_equity_krw"] = np.nan
    merged.loc[~valid_timing.fillna(False), "ebitda_krw"] = np.nan
    merged.loc[~valid_timing.fillna(False), "interest_expense_krw"] = np.nan
    merged.loc[~valid_timing.fillna(False), "total_assets_krw"] = np.nan
    merged.loc[~valid_timing.fillna(False), "prior_total_assets_krw"] = np.nan
    positive_be = merged["book_equity_krw"].where(merged["book_equity_krw"].gt(0))
    merged["book_to_market"] = positive_be.div(merged["market_cap"])
    merged["profitability"] = merged["ebitda_krw"].sub(
        merged["interest_expense_krw"]
    ).div(positive_be)
    valid_prior_assets = merged["prior_total_assets_krw"].gt(0)
    merged["investment"] = np.nan
    merged.loc[valid_prior_assets, "investment"] = (
        merged.loc[valid_prior_assets, "total_assets_krw"]
        .sub(merged.loc[valid_prior_assets, "prior_total_assets_krw"])
        .div(merged.loc[valid_prior_assets, "prior_total_assets_krw"])
    )
    merged[list(ANNUAL_SIGNALS.values())] = merged[
        list(ANNUAL_SIGNALS.values())
    ].replace([np.inf, -np.inf], np.nan)

    results: list[pd.DataFrame] = []
    for factor, signal in ANNUAL_SIGNALS.items():
        rows: list[pd.DataFrame] = []
        for formation_date, cross_section in merged.groupby("date", sort=True):
            eligible = filter_rebalance_universe(cross_section, factor=factor)
            reference_available = eligible["market"].eq("KOSPI") & eligible[
                signal
            ].notna()
            if not reference_available.any():
                continue
            assigned = assign_kospi_2x3_buckets(eligible, signal_column=signal)
            quintiles = assign_kospi_quintiles(
                eligible[["ticker", "market", signal]], signal_column=signal
            )[["ticker", "quantile"]]
            assigned = assigned.merge(
                quintiles, on="ticker", how="left", validate="one_to_one"
            )
            assigned["formation_date"] = formation_date
            assigned["formation_year"] = pd.Timestamp(formation_date).year
            assigned["factor"] = factor
            assigned["characteristic"] = assigned[signal]
            assigned["formation_market_cap"] = assigned["market_cap"]
            rows.append(assigned)
        factor_membership = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
        results.append(factor_membership)
        if factor == "HML" and not factor_membership.empty:
            results.append(factor_membership.assign(factor="SMB"))
    membership = pd.concat(results, ignore_index=True)
    columns = [
        "formation_date",
        "formation_year",
        "ticker",
        "factor",
        "market",
        "bucket",
        "quantile",
        "formation_market_cap",
        "characteristic",
        "size_breakpoint",
        "signal_30_breakpoint",
        "signal_70_breakpoint",
    ]
    return membership[columns].sort_values(
        ["formation_date", "factor", "ticker"]
    ).reset_index(drop=True)


def _monthly_stock_panel(prices: pd.DataFrame) -> pd.DataFrame:
    source = prices.copy()
    source["holding_month"] = source["date"].dt.to_period("M")
    valid = source.loc[
        source["return"].notna(), ["date", "ticker", "holding_month", "return"]
    ].copy()
    valid["holding_month"] = valid["date"].dt.to_period("M")
    valid["gross"] = valid["return"].add(1.0)
    returns = valid.groupby(["ticker", "holding_month"], sort=True).agg(
        gross=("gross", "prod"),
        date=("date", "max"),
        n_days=("return", "size"),
    )
    returns["return"] = returns["gross"].sub(1.0)
    caps = (
        source.loc[source["market_cap"].gt(0)]
        .sort_values(["ticker", "date"])
        .groupby(["ticker", "holding_month"], sort=True)["market_cap"]
        .last()
        .rename("formation_market_cap")
        .reset_index()
    )
    caps["holding_month"] = caps["holding_month"].add(1)
    return returns.reset_index()[
        ["ticker", "holding_month", "date", "return", "n_days"]
    ].merge(caps, on=["ticker", "holding_month"], how="left", validate="one_to_one")


def build_momentum_memberships(
    snapshots: pd.DataFrame,
    prices: pd.DataFrame,
) -> pd.DataFrame:
    """Form monthly MOM portfolios using exactly holding t-12 through t-2."""

    monthly = _monthly_stock_panel(prices)
    wide = monthly.pivot(index="holding_month", columns="ticker", values="return")
    gross_signal = pd.DataFrame(1.0, index=wide.index, columns=wide.columns)
    complete = pd.DataFrame(True, index=wide.index, columns=wide.columns)
    for lag in range(1, 12):
        lagged = wide.shift(lag)
        gross_signal = gross_signal.mul(lagged.add(1.0))
        complete &= lagged.notna()
    signal_wide = gross_signal.where(complete).sub(1.0)
    signals = signal_wide.rename_axis(index="formation_month").reset_index().melt(
        id_vars="formation_month", var_name="ticker", value_name="momentum"
    )
    signals = signals.dropna(subset=["momentum"])

    cross = _formation_cross_sections(snapshots, prices).merge(
        signals,
        on=["formation_month", "ticker"],
        how="left",
        validate="one_to_one",
    )
    results: list[pd.DataFrame] = []
    for formation_date, cross_section in cross.groupby("date", sort=True):
        eligible = filter_rebalance_universe(cross_section, factor="MOM")
        reference_available = eligible["market"].eq("KOSPI") & eligible[
            "momentum"
        ].notna()
        if not reference_available.any():
            continue
        assigned = assign_kospi_2x3_buckets(eligible, signal_column="momentum")
        quintiles = assign_kospi_quintiles(
            eligible[["ticker", "market", "momentum"]], signal_column="momentum"
        )[["ticker", "quantile"]]
        assigned = assigned.merge(
            quintiles, on="ticker", how="left", validate="one_to_one"
        )
        assigned["formation_date"] = formation_date
        assigned["formation_month"] = pd.Timestamp(formation_date).to_period("M")
        assigned["holding_month"] = assigned["formation_month"].add(1)
        assigned["factor"] = "MOM"
        assigned["characteristic"] = assigned["momentum"]
        assigned["formation_market_cap"] = assigned["market_cap"]
        results.append(assigned)
    membership = pd.concat(results, ignore_index=True)
    columns = [
        "formation_date",
        "formation_month",
        "holding_month",
        "ticker",
        "factor",
        "market",
        "bucket",
        "quantile",
        "formation_market_cap",
        "characteristic",
        "size_breakpoint",
        "signal_30_breakpoint",
        "signal_70_breakpoint",
    ]
    return membership[columns].sort_values(
        ["formation_date", "ticker"]
    ).reset_index(drop=True)


def _bucket_returns(
    panel: pd.DataFrame,
    *,
    factor: str,
    bucket_column: str,
    frequency: str,
) -> pd.DataFrame:
    results: list[pd.DataFrame] = []
    base = panel.loc[
        panel["return"].notna() & panel[bucket_column].notna(),
        ["date", "return", "weight_cap", bucket_column],
    ].copy()
    for weight in ("vw", "ew"):
        valid = base.copy()
        if weight == "vw":
            valid = valid.loc[valid["weight_cap"].gt(0)].copy()
            valid["weighted_return"] = valid["return"].mul(valid["weight_cap"])
            grouped = valid.groupby(["date", bucket_column], sort=True).agg(
                numerator=("weighted_return", "sum"),
                denominator=("weight_cap", "sum"),
                n_stocks=("return", "size"),
            )
            grouped["ret"] = grouped["numerator"].div(grouped["denominator"])
        else:
            grouped = valid.groupby(["date", bucket_column], sort=True).agg(
                ret=("return", "mean"), n_stocks=("return", "size")
            )
        result = grouped.reset_index().rename(columns={bucket_column: "bucket"})
        result["frequency"] = frequency
        result["factor"] = factor
        result["weight"] = weight
        results.append(
            result[["date", "frequency", "factor", "bucket", "weight", "ret", "n_stocks"]]
        )
    return pd.concat(results, ignore_index=True)


def _portfolio_panels(
    prices: pd.DataFrame,
    annual_memberships: pd.DataFrame,
    momentum_memberships: pd.DataFrame,
    *,
    start: pd.Timestamp,
    latest_complete_month: pd.Period,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    daily = prices.loc[prices["date"].ge(start)].copy()
    daily_annual = daily.merge(
        annual_memberships[["formation_year", "ticker", "factor", "bucket", "quantile"]],
        on=["formation_year", "ticker"],
        how="inner",
        validate="many_to_many",
    ).rename(columns={"lag_market_cap": "weight_cap"})
    daily_momentum = daily.merge(
        momentum_memberships[["holding_month", "ticker", "factor", "bucket", "quantile"]],
        on=["holding_month", "ticker"],
        how="inner",
        validate="many_to_one",
    ).rename(columns={"lag_market_cap": "weight_cap"})
    daily_panel = pd.concat([daily_annual, daily_momentum], ignore_index=True)

    monthly = _monthly_stock_panel(prices)
    monthly = monthly.loc[
        monthly["holding_month"].ge(start.to_period("M"))
        & monthly["holding_month"].le(latest_complete_month)
    ].copy()
    monthly["formation_year"] = np.where(
        monthly["holding_month"].dt.month.ge(7),
        monthly["holding_month"].dt.year,
        monthly["holding_month"].dt.year - 1,
    )
    monthly_annual = monthly.merge(
        annual_memberships[["formation_year", "ticker", "factor", "bucket", "quantile"]],
        on=["formation_year", "ticker"],
        how="inner",
        validate="many_to_many",
    ).rename(columns={"formation_market_cap": "weight_cap"})
    monthly_momentum = monthly.merge(
        momentum_memberships[["holding_month", "ticker", "factor", "bucket", "quantile"]],
        on=["holding_month", "ticker"],
        how="inner",
        validate="many_to_one",
    ).rename(columns={"formation_market_cap": "weight_cap"})
    monthly_panel = pd.concat([monthly_annual, monthly_momentum], ignore_index=True)
    return daily_panel, monthly_panel


def _all_bucket_returns(
    panel: pd.DataFrame,
    *,
    frequency: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    construction: list[pd.DataFrame] = []
    quintiles: list[pd.DataFrame] = []
    for factor, factor_panel in panel.groupby("factor", sort=False):
        construction.append(
            _bucket_returns(
                factor_panel,
                factor=str(factor),
                bucket_column="bucket",
                frequency=frequency,
            )
        )
        quintiles.append(
            _bucket_returns(
                factor_panel,
                factor=str(factor),
                bucket_column="quantile",
                frequency=frequency,
            )
        )
    return pd.concat(construction, ignore_index=True), pd.concat(
        quintiles, ignore_index=True
    )


def _factor_from_six_buckets(buckets: pd.DataFrame, *, factor: str) -> pd.Series:
    wide = buckets.pivot(index="date", columns="bucket", values="ret")
    required = ["S1", "S2", "S3", "B1", "B2", "B3"]
    wide = wide.reindex(columns=required)
    if factor == "SMB":
        result = wide[["S1", "S2", "S3"]].mean(axis=1, skipna=False).sub(
            wide[["B1", "B2", "B3"]].mean(axis=1, skipna=False)
        )
    elif factor in {"HML", "RMW", "MOM"}:
        result = wide[["S3", "B3"]].mean(axis=1, skipna=False).sub(
            wide[["S1", "B1"]].mean(axis=1, skipna=False)
        )
    elif factor == "CMA":
        result = wide[["S1", "B1"]].mean(axis=1, skipna=False).sub(
            wide[["S3", "B3"]].mean(axis=1, skipna=False)
        )
    else:
        raise ValueError(f"unsupported factor: {factor}")
    return result.rename(factor)


def load_ecos_market_and_rf(
    kospi_path: str | Path,
    rf_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load official ECOS KOSPI levels and annual-percent CD yields."""

    def read_rows(path: str | Path, value_name: str) -> pd.DataFrame:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = pd.DataFrame(payload["rows"])[["TIME", "DATA_VALUE"]]
        rows = rows.rename(columns={"TIME": "date", "DATA_VALUE": value_name})
        rows["date"] = pd.to_datetime(rows["date"], format="%Y%m%d", errors="raise")
        rows[value_name] = pd.to_numeric(rows[value_name], errors="raise")
        if rows["date"].duplicated().any():
            raise ValueError(f"ECOS {value_name} has duplicate dates")
        return rows.sort_values("date").reset_index(drop=True)

    return read_rows(kospi_path, "kospi_level"), read_rows(rf_path, "annual_rf_percent")


def _market_rf_returns(
    kospi: pd.DataFrame,
    rf_yield: pd.DataFrame,
    *,
    frequency: str,
) -> pd.DataFrame:
    if frequency == "daily":
        result = kospi.copy()
        result["RM"] = result["kospi_level"].pct_change(fill_method=None)
        result = pd.merge_asof(
            result.sort_values("date"),
            rf_yield.sort_values("date"),
            on="date",
            direction="backward",
            tolerance=pd.Timedelta(days=7),
        )
        result["RF"] = annual_yield_percent_to_period_return(
            result["annual_rf_percent"], periods_per_year=252
        )
        return result[["date", "RM", "RF"]]
    if frequency != "monthly":
        raise ValueError(f"unsupported frequency: {frequency}")
    levels = kospi.assign(month=kospi["date"].dt.to_period("M"))
    levels = levels.groupby("month", sort=True).tail(1).sort_values("month")
    levels["RM"] = levels["kospi_level"].pct_change(fill_method=None)
    yields = rf_yield.assign(month=rf_yield["date"].dt.to_period("M"))
    yields = yields.groupby("month", sort=True).tail(1)[["month", "annual_rf_percent"]]
    result = levels.merge(yields, on="month", how="left", validate="one_to_one")
    result["RF"] = annual_yield_percent_to_period_return(
        result["annual_rf_percent"], periods_per_year=12
    )
    return result[["date", "RM", "RF"]]


def _assemble_factor_returns(
    buckets: pd.DataFrame,
    market_rf: pd.DataFrame,
    *,
    frequency: str,
) -> pd.DataFrame:
    results: list[pd.DataFrame] = []
    for weight in ("vw", "ew"):
        subset = buckets.loc[buckets["weight"].eq(weight)]
        series = [
            _factor_from_six_buckets(
                subset.loc[subset["factor"].eq(factor)], factor=factor
            )
            for factor in ("SMB", "HML", "RMW", "CMA", "MOM")
        ]
        style = pd.concat(series, axis=1).reset_index()
        result = market_rf.merge(style, on="date", how="outer", validate="one_to_one")
        result["RMRF"] = result["RM"].sub(result["RF"])
        result["frequency"] = frequency
        result["weight"] = weight
        results.append(result[["date", "frequency", "weight", *FACTOR_ORDER]])
    return pd.concat(results, ignore_index=True).sort_values(
        ["date", "weight"]
    ).reset_index(drop=True)


def build_exact_kimchi_factors(
    *,
    prices: pd.DataFrame,
    snapshots: pd.DataFrame,
    accounting: pd.DataFrame,
    kospi: pd.DataFrame,
    rf_yield: pd.DataFrame,
    start: str | pd.Timestamp = "2018-01-01",
) -> ExactKimchiResult:
    """Build daily and independently calculated monthly factor series."""

    start_date = pd.Timestamp(start)
    annual_memberships = build_annual_memberships(snapshots, prices, accounting)
    momentum_memberships = build_momentum_memberships(snapshots, prices)
    latest_complete_month = snapshots["date"].max().to_period("M")
    daily_panel, monthly_panel = _portfolio_panels(
        prices,
        annual_memberships,
        momentum_memberships,
        start=start_date,
        latest_complete_month=latest_complete_month,
    )
    daily_buckets, daily_quintiles = _all_bucket_returns(
        daily_panel, frequency="daily"
    )
    monthly_buckets, monthly_quintiles = _all_bucket_returns(
        monthly_panel, frequency="monthly"
    )
    daily_market_rf = _market_rf_returns(kospi, rf_yield, frequency="daily")
    daily_market_rf = daily_market_rf.loc[daily_market_rf["date"].ge(start_date)]
    monthly_market_rf = _market_rf_returns(kospi, rf_yield, frequency="monthly")
    monthly_market_rf = monthly_market_rf.loc[
        monthly_market_rf["date"].ge(start_date)
        & monthly_market_rf["date"].dt.to_period("M").le(latest_complete_month)
    ]
    daily_returns = _assemble_factor_returns(
        daily_buckets, daily_market_rf, frequency="daily"
    )
    monthly_returns = _assemble_factor_returns(
        monthly_buckets, monthly_market_rf, frequency="monthly"
    )

    audit: dict[str, object] = {
        "classification": "price-return variant; fixed-3-month-lag non-PIT accounting sensitivity",
        "stock_return_includes_cash_dividends": False,
        "statement_vintage": "latest local dump revision",
        "fiscal_year_selection": "last annual D statement ending in prior calendar year",
        "reporting_lag_months": 3,
        "market_cap_formula": "raw_close * source 유통주식수",
        "breakpoint_reference": "KOSPI only",
        "snapshot_rows": len(snapshots),
        "snapshot_dates": int(snapshots["date"].nunique()),
        "snapshot_start": snapshots["date"].min().date().isoformat(),
        "snapshot_end": snapshots["date"].max().date().isoformat(),
        "price_rows": len(prices),
        "price_tickers": int(prices["ticker"].nunique()),
        "accounting_rows": len(accounting),
        "book_equity_source_counts": accounting["book_equity_source"]
        .value_counts(dropna=False)
        .to_dict(),
        "annual_membership_rows": annual_memberships.groupby("factor").size().to_dict(),
        "momentum_membership_rows": len(momentum_memberships),
        "daily_output_end": daily_returns["date"].max().date().isoformat(),
        "monthly_output_end": monthly_returns["date"].max().date().isoformat(),
        "factor_coverage": {},
    }
    for weight in ("vw", "ew"):
        frame = daily_returns.loc[daily_returns["weight"].eq(weight)]
        audit["factor_coverage"][weight] = {
            factor: {
                "observations": int(frame[factor].notna().sum()),
                "start": (
                    frame.loc[frame[factor].notna(), "date"].min().date().isoformat()
                    if frame[factor].notna().any()
                    else None
                ),
                "end": (
                    frame.loc[frame[factor].notna(), "date"].max().date().isoformat()
                    if frame[factor].notna().any()
                    else None
                ),
            }
            for factor in FACTOR_ORDER
        }
    return ExactKimchiResult(
        daily_returns=daily_returns,
        monthly_returns=monthly_returns,
        daily_2x3_buckets=daily_buckets,
        monthly_2x3_buckets=monthly_buckets,
        daily_quintile_buckets=daily_quintiles,
        monthly_quintile_buckets=monthly_quintiles,
        annual_memberships=annual_memberships,
        momentum_memberships=momentum_memberships,
        accounting_signals=accounting,
        audit=audit,
    )
