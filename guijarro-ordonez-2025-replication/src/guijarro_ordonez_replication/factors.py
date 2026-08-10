"""Korean daily Fama-French factor construction and benchmark diagnostics.

The local statement snapshots do not contain historical announcement timestamps.
Annual accounting values are therefore exposed only after a fixed reporting lag,
but the resulting characteristics remain a non-PIT sensitivity analysis.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds


ACCOUNT_CODES = {
    "book_equity": ("4001160000", "4001160050"),
    "operating_profit": ("4001230000",),
    "total_assets": ("4001110000",),
}
FACTOR_NAMES = ("RM", "RMRF", "SMB", "HML", "RMW", "CMA", "MOM", "LTR", "STR")
ANNUAL_FACTORS = ("HML", "RMW", "CMA")


def _require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def load_statement_facts(path: str | Path) -> pd.DataFrame:
    """Read only the annual consolidated facts required by the factor builder."""

    dataset = ds.dataset(path, format="parquet", partitioning="hive")
    codes = sorted({code for values in ACCOUNT_CODES.values() for code in values})
    predicate = (
        (ds.field("statement_scope") == "consolidated")
        & (ds.field("settlement_type") == "D")
        & ds.field("account_code").isin(codes)
    )
    columns = [
        "ticker",
        "fiscal_period",
        "settlement_type",
        "statement_scope",
        "account_code",
        "numeric_value",
        "dump_last_modified",
    ]
    return dataset.to_table(columns=columns, filter=predicate).to_pandas()


def prepare_daily_stock_panel(prices: pd.DataFrame) -> pd.DataFrame:
    """Normalize daily returns and create strictly lagged value weights."""

    _require(prices, {"date", "ticker", "return", "market_cap"}, "prices")
    frame = prices[["date", "ticker", "return", "market_cap"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["ticker"] = frame["ticker"].astype(str)
    frame["return"] = pd.to_numeric(frame["return"], errors="coerce")
    frame["market_cap"] = pd.to_numeric(frame["market_cap"], errors="coerce")
    if frame.duplicated(["date", "ticker"]).any():
        raise ValueError("prices has duplicate date-ticker keys")
    frame = frame.sort_values(["ticker", "date"]).reset_index(drop=True)
    grouped = frame.groupby("ticker", sort=False)
    frame["lag_market_cap"] = grouped["market_cap"].shift(1)
    lag_date = grouped["date"].shift(1)
    stale = frame["date"].sub(lag_date).dt.days.gt(10)
    frame.loc[stale, "lag_market_cap"] = np.nan
    frame["formation_year"] = np.where(
        frame["date"].dt.month.ge(7),
        frame["date"].dt.year,
        frame["date"].dt.year - 1,
    )
    frame["holding_month"] = frame["date"].dt.to_period("M")
    return frame


def derive_lagged_annual_characteristics(
    statement_facts: pd.DataFrame,
    *,
    reporting_lag_months: int = 3,
    allow_non_pit: bool = False,
) -> pd.DataFrame:
    """Build book-to-market inputs, profitability, and investment.

    Profitability is operating profit divided by positive book equity. Investment
    is annual total-asset growth. Monetary statement values are in KRW thousands;
    book equity is converted to KRW for comparison with market capitalization.
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
        & statement_facts["account_code"].isin(
            {code for values in ACCOUNT_CODES.values() for code in values}
        )
    ].copy()
    frame["fiscal_period"] = pd.to_datetime(frame["fiscal_period"], errors="raise")
    frame["dump_last_modified"] = pd.to_datetime(
        frame["dump_last_modified"], errors="coerce"
    )
    frame["numeric_value"] = pd.to_numeric(frame["numeric_value"], errors="coerce")
    logical_key = ["ticker", "fiscal_period", "account_code"]
    frame = frame.sort_values(logical_key + ["dump_last_modified"])
    frame = frame.drop_duplicates(logical_key, keep="last")

    code_to_item = {
        code: item for item, codes in ACCOUNT_CODES.items() for code in codes
    }
    code_priority = {
        code: priority
        for codes in ACCOUNT_CODES.values()
        for priority, code in enumerate(codes)
    }
    frame["item"] = frame["account_code"].map(code_to_item)
    frame["code_priority"] = frame["account_code"].map(code_priority)
    item_key = ["ticker", "fiscal_period", "item"]
    frame = frame.sort_values(item_key + ["code_priority"])
    frame = frame.drop_duplicates(item_key, keep="first")
    wide = frame.pivot(
        index=["ticker", "fiscal_period"],
        columns="item",
        values="numeric_value",
    ).reset_index()
    for column in ACCOUNT_CODES:
        if column not in wide:
            wide[column] = np.nan
    wide = wide.sort_values(["ticker", "fiscal_period"]).reset_index(drop=True)
    previous_assets = wide.groupby("ticker", sort=False)["total_assets"].shift(1)
    previous_period = wide.groupby("ticker", sort=False)["fiscal_period"].shift(1)
    period_gap = wide["fiscal_period"].sub(previous_period).dt.days
    wide["investment"] = wide["total_assets"].div(previous_assets).sub(1.0)
    wide.loc[~period_gap.between(300, 450), "investment"] = np.nan
    positive_equity = wide["book_equity"].where(wide["book_equity"].gt(0))
    wide["profitability"] = wide["operating_profit"].div(positive_equity)
    wide["book_equity"] = positive_equity.mul(1_000.0)
    wide["available_date"] = (
        wide["fiscal_period"]
        + pd.offsets.MonthEnd(0)
        + pd.DateOffset(months=reporting_lag_months)
    )
    numeric = ["book_equity", "profitability", "investment"]
    wide[numeric] = wide[numeric].replace([np.inf, -np.inf], np.nan)
    return wide[
        ["ticker", "fiscal_period", "available_date", *numeric]
    ].reset_index(drop=True)


def _merge_asof_by_ticker(
    formation: pd.DataFrame, characteristics: pd.DataFrame
) -> pd.DataFrame:
    formation = formation.copy()
    characteristics = characteristics.copy()
    formation["formation_date"] = pd.to_datetime(
        formation["formation_date"], errors="raise"
    ).astype("datetime64[ns]")
    characteristics["available_date"] = pd.to_datetime(
        characteristics["available_date"], errors="raise"
    ).astype("datetime64[ns]")
    records: list[pd.DataFrame] = []
    histories = {
        ticker: group.sort_values("available_date")
        for ticker, group in characteristics.groupby("ticker", sort=False)
    }
    for ticker, left in formation.groupby("ticker", sort=False):
        history = histories.get(ticker)
        if history is None:
            continue
        matched = pd.merge_asof(
            left.sort_values("formation_date"),
            history.drop(columns="ticker"),
            left_on="formation_date",
            right_on="available_date",
            direction="backward",
        )
        records.append(matched)
    if not records:
        return pd.DataFrame()
    return pd.concat(records, ignore_index=True)


def build_annual_memberships(
    daily: pd.DataFrame, characteristics: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Create June 2x3 memberships for value, profitability, and investment."""

    _require(
        daily,
        {"date", "ticker", "market_cap"},
        "daily",
    )
    _require(
        characteristics,
        {"ticker", "available_date", "book_equity", "profitability", "investment"},
        "characteristics",
    )
    june = daily.loc[
        daily["date"].dt.month.eq(6) & daily["market_cap"].gt(0),
        ["date", "ticker", "market_cap"],
    ].copy()
    june["formation_year"] = june["date"].dt.year
    june = (
        june.sort_values(["ticker", "date"])
        .groupby(["ticker", "formation_year"], as_index=False, sort=False)
        .tail(1)
        .rename(columns={"date": "formation_date"})
    )
    matched = _merge_asof_by_ticker(june, characteristics)
    if matched.empty:
        return {factor: pd.DataFrame() for factor in ANNUAL_FACTORS}
    matched["book_to_market"] = matched["book_equity"].div(matched["market_cap"])
    source_columns = {
        "HML": "book_to_market",
        "RMW": "profitability",
        "CMA": "investment",
    }
    memberships: dict[str, pd.DataFrame] = {}
    for factor, characteristic in source_columns.items():
        formed = matched.dropna(subset=["market_cap", characteristic]).copy()
        formed = formed.loc[formed["market_cap"].gt(0)]
        grouped = formed.groupby("formation_year", sort=False)
        size_cut = grouped["market_cap"].transform("median")
        low_cut = grouped[characteristic].transform(lambda values: values.quantile(0.30))
        high_cut = grouped[characteristic].transform(
            lambda values: values.quantile(0.70)
        )
        formed["size_bucket"] = np.where(
            formed["market_cap"].le(size_cut), "S", "B"
        )
        formed["characteristic_bucket"] = np.select(
            [formed[characteristic].le(low_cut), formed[characteristic].ge(high_cut)],
            ["1", "3"],
            default="2",
        )
        memberships[factor] = formed[
            [
                "formation_year",
                "ticker",
                "formation_date",
                "available_date",
                "size_bucket",
                "characteristic_bucket",
                "market_cap",
                characteristic,
            ]
        ].rename(
            columns={
                "market_cap": "formation_market_cap",
                characteristic: "characteristic",
            }
        )
    return memberships


def _compound(values: pd.Series) -> float:
    clean = values.dropna()
    return float((1.0 + clean).prod() - 1.0) if len(clean) else np.nan


def build_momentum_membership(daily: pd.DataFrame) -> pd.DataFrame:
    """Create monthly 2x3 membership using prior months 12 through 2."""

    monthly_return = (
        daily.groupby(["ticker", "holding_month"], sort=False)["return"]
        .agg(_compound)
        .rename("monthly_return")
    )
    month_end_cap = (
        daily.dropna(subset=["market_cap"])
        .groupby(["ticker", "holding_month"], sort=False)["market_cap"]
        .last()
        .rename("formation_market_cap")
    )
    monthly = pd.concat([monthly_return, month_end_cap], axis=1).reset_index()
    monthly = monthly.sort_values(["ticker", "holding_month"]).reset_index(drop=True)
    gross = monthly["monthly_return"].add(1.0)
    monthly["characteristic"] = (
        gross.groupby(monthly["ticker"], sort=False)
        .shift(1)
        .groupby(monthly["ticker"], sort=False)
        .rolling(11, min_periods=8)
        .apply(np.prod, raw=True)
        .reset_index(level=0, drop=True)
        .sub(1.0)
    )
    monthly["formation_month"] = monthly["holding_month"]
    monthly["holding_month"] = monthly["formation_month"].add(1)
    formed = monthly.dropna(subset=["formation_market_cap", "characteristic"]).copy()
    formed = formed.loc[formed["formation_market_cap"].gt(0)]
    grouped = formed.groupby("formation_month", sort=False)
    size_cut = grouped["formation_market_cap"].transform("median")
    low_cut = grouped["characteristic"].transform(lambda values: values.quantile(0.30))
    high_cut = grouped["characteristic"].transform(
        lambda values: values.quantile(0.70)
    )
    formed["size_bucket"] = np.where(
        formed["formation_market_cap"].le(size_cut), "S", "B"
    )
    formed["characteristic_bucket"] = np.select(
        [formed["characteristic"].le(low_cut), formed["characteristic"].ge(high_cut)],
        ["1", "3"],
        default="2",
    )
    return formed[
        [
            "holding_month",
            "formation_month",
            "ticker",
            "size_bucket",
            "characteristic_bucket",
            "formation_market_cap",
            "characteristic",
        ]
    ].reset_index(drop=True)


def build_reversal_memberships(daily: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create long- and short-term reversal memberships.

    STR sorts on the immediately preceding monthly return. LTR sorts on the
    compounded return from months 60 through 13 before the holding month.
    Both factors buy prior losers and sell prior winners.
    """

    monthly_return = (
        daily.groupby(["ticker", "holding_month"], sort=False)["return"]
        .agg(_compound)
        .rename("monthly_return")
    )
    month_end_cap = (
        daily.dropna(subset=["market_cap"])
        .groupby(["ticker", "holding_month"], sort=False)["market_cap"]
        .last()
        .rename("formation_market_cap")
    )
    monthly = pd.concat([monthly_return, month_end_cap], axis=1).reset_index()
    monthly = monthly.sort_values(["ticker", "holding_month"]).reset_index(drop=True)
    gross = monthly["monthly_return"].add(1.0)
    monthly["STR"] = monthly["monthly_return"]
    monthly["LTR"] = (
        gross.groupby(monthly["ticker"], sort=False)
        .shift(12)
        .groupby(monthly["ticker"], sort=False)
        .rolling(48, min_periods=48)
        .apply(np.prod, raw=True)
        .reset_index(level=0, drop=True)
        .sub(1.0)
    )
    monthly["formation_month"] = monthly["holding_month"]
    monthly["holding_month"] = monthly["formation_month"].add(1)
    memberships: dict[str, pd.DataFrame] = {}
    for factor in ("LTR", "STR"):
        formed = monthly.dropna(
            subset=["formation_market_cap", factor]
        ).copy()
        formed = formed.loc[formed["formation_market_cap"].gt(0)]
        grouped = formed.groupby("formation_month", sort=False)
        size_cut = grouped["formation_market_cap"].transform("median")
        low_cut = grouped[factor].transform(lambda values: values.quantile(0.30))
        high_cut = grouped[factor].transform(lambda values: values.quantile(0.70))
        formed["size_bucket"] = np.where(
            formed["formation_market_cap"].le(size_cut), "S", "B"
        )
        formed["characteristic_bucket"] = np.select(
            [formed[factor].le(low_cut), formed[factor].ge(high_cut)],
            ["1", "3"],
            default="2",
        )
        memberships[factor] = formed[
            [
                "holding_month",
                "formation_month",
                "ticker",
                "size_bucket",
                "characteristic_bucket",
                "formation_market_cap",
                factor,
            ]
        ].rename(columns={factor: "characteristic"})
    return memberships


def _weighted_bucket_returns(
    panel: pd.DataFrame, *, factor: str
) -> pd.DataFrame:
    valid = panel.loc[
        panel["return"].notna() & panel["lag_market_cap"].gt(0),
        ["date", "size_bucket", "characteristic_bucket", "return", "lag_market_cap"],
    ].copy()
    valid["weighted_return"] = valid["return"].mul(valid["lag_market_cap"])
    grouped = valid.groupby(
        ["date", "size_bucket", "characteristic_bucket"], sort=True
    ).agg(
        weighted_return=("weighted_return", "sum"),
        total_weight=("lag_market_cap", "sum"),
        n_stocks=("return", "size"),
    )
    grouped["ret"] = grouped["weighted_return"].div(grouped["total_weight"])
    result = grouped.reset_index()
    result["factor"] = factor
    result["bucket"] = result["size_bucket"] + result["characteristic_bucket"]
    return result[["date", "factor", "bucket", "ret", "n_stocks"]]


def factor_return_from_buckets(
    buckets: pd.DataFrame, *, factor: str
) -> pd.Series:
    """Combine six 2x3 value-weighted portfolio returns into one factor."""

    _require(buckets, {"date", "bucket", "ret"}, "buckets")
    wide = buckets.pivot(index="date", columns="bucket", values="ret")
    required = ["S1", "S2", "S3", "B1", "B2", "B3"]
    for column in required:
        if column not in wide:
            wide[column] = np.nan
    if factor == "SMB":
        result = wide[["S1", "S2", "S3"]].mean(axis=1, skipna=False).sub(
            wide[["B1", "B2", "B3"]].mean(axis=1, skipna=False)
        )
    elif factor in {"HML", "RMW", "MOM"}:
        result = wide[["S3", "B3"]].mean(axis=1, skipna=False).sub(
            wide[["S1", "B1"]].mean(axis=1, skipna=False)
        )
    elif factor in {"CMA", "LTR", "STR"}:
        result = wide[["S1", "B1"]].mean(axis=1, skipna=False).sub(
            wide[["S3", "B3"]].mean(axis=1, skipna=False)
        )
    else:
        raise ValueError(f"Unsupported factor: {factor}")
    return result.rename(factor)


def _market_return(daily: pd.DataFrame) -> pd.Series:
    valid = daily.loc[
        daily["return"].notna() & daily["lag_market_cap"].gt(0),
        ["date", "return", "lag_market_cap"],
    ].copy()
    valid["weighted_return"] = valid["return"].mul(valid["lag_market_cap"])
    grouped = valid.groupby("date", sort=True).agg(
        weighted_return=("weighted_return", "sum"),
        total_weight=("lag_market_cap", "sum"),
    )
    return grouped["weighted_return"].div(grouped["total_weight"]).rename("RM")


def build_daily_factors(
    daily: pd.DataFrame,
    annual_memberships: dict[str, pd.DataFrame],
    momentum_membership: pd.DataFrame,
    *,
    risk_free: pd.Series | None = None,
    reversal_memberships: dict[str, pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construct daily market, style, momentum, and reversal factors."""

    factor_series: list[pd.Series] = [_market_return(daily)]
    bucket_frames: list[pd.DataFrame] = []
    for factor in ANNUAL_FACTORS:
        membership = annual_memberships[factor]
        panel = daily.merge(
            membership[
                [
                    "formation_year",
                    "ticker",
                    "size_bucket",
                    "characteristic_bucket",
                ]
            ],
            on=["formation_year", "ticker"],
            how="inner",
            validate="many_to_one",
        )
        buckets = _weighted_bucket_returns(panel, factor=factor)
        bucket_frames.append(buckets)
        factor_series.append(factor_return_from_buckets(buckets, factor=factor))
        if factor == "HML":
            factor_series.append(factor_return_from_buckets(buckets, factor="SMB"))
            bucket_frames.append(buckets.assign(factor="SMB"))

    momentum_panel = daily.merge(
        momentum_membership[
            ["holding_month", "ticker", "size_bucket", "characteristic_bucket"]
        ],
        on=["holding_month", "ticker"],
        how="inner",
        validate="many_to_one",
    )
    momentum_buckets = _weighted_bucket_returns(momentum_panel, factor="MOM")
    bucket_frames.append(momentum_buckets)
    factor_series.append(factor_return_from_buckets(momentum_buckets, factor="MOM"))
    for factor, membership in (reversal_memberships or {}).items():
        reversal_panel = daily.merge(
            membership[
                ["holding_month", "ticker", "size_bucket", "characteristic_bucket"]
            ],
            on=["holding_month", "ticker"],
            how="inner",
            validate="many_to_one",
        )
        reversal_buckets = _weighted_bucket_returns(reversal_panel, factor=factor)
        bucket_frames.append(reversal_buckets)
        factor_series.append(
            factor_return_from_buckets(reversal_buckets, factor=factor)
        )
    factors = pd.concat(factor_series, axis=1).reset_index()
    if risk_free is not None:
        named_rf = risk_free.rename("RF")
        named_rf.index = pd.to_datetime(named_rf.index, errors="raise")
        factors = factors.merge(
            named_rf.rename_axis("date").reset_index(),
            on="date",
            how="left",
            validate="one_to_one",
        )
        factors["RMRF"] = factors["RM"].sub(factors["RF"])
    else:
        factors["RF"] = np.nan
        factors["RMRF"] = np.nan
    ordered = ["date", "RM", "RMRF", "SMB", "HML", "RMW", "CMA", "MOM"]
    ordered.extend(factor for factor in ("LTR", "STR") if factor in factors)
    ordered.append("RF")
    return factors[ordered], pd.concat(bucket_frames, ignore_index=True)


def load_kimchi_factor_data(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load final and construction-bucket returns from Kimchi Factor CSVs."""

    root = Path(path)
    returns: list[pd.DataFrame] = []
    buckets: list[pd.DataFrame] = []
    for csv_path in sorted(root.glob("kimchi_daily_*_vw_all.csv")):
        frame = pd.read_csv(csv_path)
        _require(
            frame,
            {"section", "date", "factor", "bucket", "weight", "ret", "n_stocks"},
            csv_path.name,
        )
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["ret"] = pd.to_numeric(frame["ret"], errors="coerce")
        returns.append(
            frame.loc[frame["section"].eq("returns"), ["date", "factor", "ret"]]
        )
        buckets.append(
            frame.loc[
                frame["section"].eq("construction_bucket_returns"),
                ["date", "factor", "bucket", "ret", "n_stocks"],
            ]
        )
    if not returns:
        raise ValueError(f"No Kimchi Factor CSVs found under {root}")
    returns_long = pd.concat(returns, ignore_index=True)
    if returns_long.duplicated(["date", "factor"]).any():
        raise ValueError("Kimchi final returns have duplicate date-factor keys")
    returns_wide = (
        returns_long.pivot(index="date", columns="factor", values="ret")
        .sort_index()
        .reset_index()
    )
    return returns_wide, pd.concat(buckets, ignore_index=True)


def compare_return_columns(
    constructed: pd.DataFrame,
    benchmark: pd.DataFrame,
    columns: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return aligned daily observations and factor-level comparison metrics."""

    names = list(columns)
    _require(constructed, {"date", *names}, "constructed")
    _require(benchmark, {"date", *names}, "benchmark")
    aligned = constructed[["date", *names]].merge(
        benchmark[["date", *names]],
        on="date",
        how="inner",
        suffixes=("_constructed", "_kimchi"),
        validate="one_to_one",
    )
    summaries: list[dict[str, object]] = []
    for factor in names:
        pair = aligned[[f"{factor}_constructed", f"{factor}_kimchi"]].dropna()
        pair.columns = ["constructed", "kimchi"]
        difference = pair["constructed"].sub(pair["kimchi"])
        benchmark_observations = int(aligned[f"{factor}_kimchi"].notna().sum())
        constructed_std = pair["constructed"].std(ddof=1)
        kimchi_std = pair["kimchi"].std(ddof=1)
        summaries.append(
            {
                "factor": factor,
                "start": aligned.loc[pair.index, "date"].min(),
                "end": aligned.loc[pair.index, "date"].max(),
                "n_days": len(pair),
                "correlation": pair["constructed"].corr(pair["kimchi"]),
                "mean_constructed": pair["constructed"].mean(),
                "mean_kimchi": pair["kimchi"].mean(),
                "mean_difference": difference.mean(),
                "mae": difference.abs().mean(),
                "rmse": np.sqrt(difference.pow(2).mean()),
                "std_constructed": constructed_std,
                "std_kimchi": kimchi_std,
                "volatility_ratio": constructed_std / kimchi_std,
                "annualized_tracking_error": difference.std(ddof=1) * np.sqrt(252),
                "sign_agreement": pair["constructed"].mul(pair["kimchi"]).ge(0).mean(),
                "constructed_missing_rate_vs_benchmark": (
                    1.0 - len(pair) / benchmark_observations
                    if benchmark_observations
                    else np.nan
                ),
            }
        )
    return aligned, pd.DataFrame(summaries)


def compare_bucket_returns(
    constructed: pd.DataFrame, benchmark: pd.DataFrame
) -> pd.DataFrame:
    """Compare each 2x3 construction portfolio with its Kimchi counterpart."""

    keys = ["date", "factor", "bucket"]
    _require(constructed, {*keys, "ret", "n_stocks"}, "constructed buckets")
    _require(benchmark, {*keys, "ret", "n_stocks"}, "benchmark buckets")
    aligned = constructed.merge(
        benchmark,
        on=keys,
        how="inner",
        suffixes=("_constructed", "_kimchi"),
        validate="one_to_one",
    )
    summaries: list[dict[str, object]] = []
    for (factor, bucket), group in aligned.groupby(["factor", "bucket"], sort=True):
        group = group.dropna(subset=["ret_constructed", "ret_kimchi"])
        difference = group["ret_constructed"].sub(group["ret_kimchi"])
        summaries.append(
            {
                "factor": factor,
                "bucket": bucket,
                "start": group["date"].min(),
                "end": group["date"].max(),
                "n_days": len(group),
                "correlation": group["ret_constructed"].corr(group["ret_kimchi"]),
                "mae": difference.abs().mean(),
                "mean_n_constructed": group["n_stocks_constructed"].mean(),
                "mean_n_kimchi": group["n_stocks_kimchi"].mean(),
            }
        )
    return pd.DataFrame(summaries)
