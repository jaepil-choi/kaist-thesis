"""Monthly firm characteristics for the Korean IPCA sensitivity.

The paper uses 46 characteristics from Chen, Pelger, and Zhu.  This module
keeps those 46 names and their timing contract, while making two Korean-data
limitations impossible to miss:

* annual statement values are latest-revision snapshots made available with a
  fixed three-month lag, not historical point-in-time vintages;
* ``Spread`` is a high-low spread proxy because daily bid and ask quotes are
  not available in the local source.

The raw builder is deliberately split from cross-sectional normalization so
that no missing value is silently imputed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import warnings

import numpy as np
import pandas as pd


CHARACTERISTIC_COLUMNS = (
    "r2_1",
    "r12_2",
    "r12_7",
    "r36_13",
    "ST_Rev",
    "LT_Rev",
    "Investment",
    "NOA",
    "DPI2A",
    "NI",
    "PROF",
    "ATO",
    "CTO",
    "FC2Y",
    "OP",
    "PM",
    "RNA",
    "ROA",
    "ROE",
    "SGA2S",
    "D2A",
    "AC",
    "OA",
    "OL",
    "PCM",
    "A2ME",
    "BEME",
    "C",
    "CF",
    "CF2P",
    "D2P",
    "E2P",
    "Q",
    "S2P",
    "Lev",
    "AT",
    "Beta",
    "IdioVol",
    "LME",
    "LTurnover",
    "MktBeta",
    "Rel2High",
    "Resid_Var",
    "Spread",
    "SUV",
    "Variance",
)

PRICE_CHARACTERISTICS = CHARACTERISTIC_COLUMNS[:6] + CHARACTERISTIC_COLUMNS[36:]
ACCOUNTING_CHARACTERISTICS = CHARACTERISTIC_COLUMNS[6:36]

# A Korean common share always carries a ticker ending in "0"; preferred and
# other share classes end in 5, 7, 9 or a letter.  Those classes have no
# financial statements of their own -- the issuer files one set of accounts for
# the whole company -- so they can never receive an accounting characteristic.
COMMON_SHARE_CLASS_SUFFIX = "0"

# Firm-year items that must be present for a statement scope to be usable.
CORE_STATEMENT_ITEMS = ("total_assets", "total_equity", "sales", "net_income")

# Canonical annual consolidated mappings verified in kwam-enhanced-index.
# Multiple codes are ordered fallbacks, never values to be summed.
IPCA_ACCOUNT_CODES = {
    "total_assets": ("4001110000",),
    "total_liabilities": ("4001140000",),
    "total_equity": ("4001160000", "4001570000"),
    "noncontrolling_interest": ("4001167500", "4001550000"),
    "cash": ("4001110300", "4001111000", "4001460200"),
    "current_assets": ("4001110100",),
    "current_liabilities": ("4001140100",),
    "current_debt": ("4001140700", "4001140900"),
    "long_debt": ("4001146900", "4001147100"),
    "tax_payable": ("4001143200",),
    "inventory": ("4001118300",),
    "ppe": ("4001126100",),
    "sales": ("4001210000", "4001211400"),
    "cogs": ("4001220000", "4001222100"),
    "sga": ("4001222400",),
    "rd": ("4001227100",),
    "advertising": ("4001225000",),
    "operating_income": ("4001230000",),
    "interest_expense": ("4001250100",),
    "net_income": ("4001290200", "4001290180", "4001410100"),
    "depreciation": ("4001410500",),
    "amortization": ("4001410600", "4001226300"),
    "deferred_tax": ("4001149300",),
}


class NonPITAccountingWarning(UserWarning):
    """Annual accounting values are not historical announcement vintages."""


class ProxyCharacteristicWarning(UserWarning):
    """A paper characteristic is represented by a documented Korean proxy."""


@dataclass(frozen=True)
class CharacteristicResult:
    """Raw and rank-normalized monthly characteristic panels plus lineage."""

    raw: pd.DataFrame
    normalized: pd.DataFrame
    audit: dict[str, object]


class MixedStatementScopeWarning(UserWarning):
    """Some firm-years use separate rather than consolidated statements."""


class ShareClassFilterWarning(UserWarning):
    """Non-common share classes were removed from the universe."""


def filter_common_share_class(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Keep only common shares and report how many tickers were removed.

    Preferred classes cannot be matched to statements and, kept in the panel,
    they both depress measured accounting coverage and duplicate their issuer's
    exposure.  Removing them is the share-class de-duplication the project
    requires, not a coverage convenience.
    """

    ticker = frame["ticker"].astype(str).str.upper()
    keep = ticker.str.endswith(COMMON_SHARE_CLASS_SUFFIX)
    dropped = int(ticker.loc[~keep].nunique())
    if dropped:
        warnings.warn(
            f"SHARE_CLASS_FILTER: removed {dropped} non-common share classes.",
            ShareClassFilterWarning,
            stacklevel=2,
        )
    return frame.loc[keep].copy(), dropped


def load_ipca_price_panel(
    path: str | Path,
    *,
    start: str | pd.Timestamp = "2015-01-01",
    common_share_class_only: bool = False,
) -> pd.DataFrame:
    """Load only daily fields required by the 46-characteristic builder."""

    import pyarrow.dataset as ds

    dataset = ds.dataset(path, format="parquet")
    table = dataset.to_table(
        columns=[
            "date",
            "ticker",
            "return",
            "adj_close",
            "adj_high",
            "adj_low",
            "trade_volume",
            "market_cap",
            "유통주식수",
        ],
        filter=ds.field("date") >= pd.Timestamp(start),
    )
    frame = table.to_pandas().rename(
        columns={"유통주식수": "listed_common_shares"}
    )
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    if frame.duplicated(["date", "ticker"]).any():
        raise ValueError("IPCA price panel has duplicate date-ticker keys")
    if common_share_class_only:
        frame, _ = filter_common_share_class(frame)
    return frame.sort_values(["ticker", "date"]).reset_index(drop=True)


def load_ipca_daily_returns(
    path: str | Path,
    *,
    start: str | pd.Timestamp = "2015-01-01",
) -> pd.DataFrame:
    """Load only the three daily fields needed after characteristics exist.

    The full price loader intentionally reads high, low, volume, market cap,
    and shares for characteristic construction.  Re-reading those columns for
    daily IPCA residual estimation wastes substantial memory on the full Korean
    stock panel, so this narrow loader keeps the estimation path bounded.
    """

    import pyarrow.dataset as ds

    dataset = ds.dataset(path, format="parquet")
    table = dataset.to_table(
        columns=["date", "ticker", "return"],
        filter=ds.field("date") >= pd.Timestamp(start),
    )
    frame = table.to_pandas()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    if frame.duplicated(["date", "ticker"]).any():
        raise ValueError("IPCA daily return panel has duplicate date-ticker keys")
    return frame.sort_values(["date", "ticker"]).reset_index(drop=True)


def _separate_scope_codes() -> dict[str, tuple[str, ...]]:
    """Map each consolidated account code to its separate-statement twin.

    FnGuide publishes consolidated statements under ``4001NNNNNN`` in
    ``DW_FNG_연결재무제표`` and separate statements under ``1001NNNNNN`` in
    ``DW_FNG_재무제표``.  The trailing six digits are shared, so the twin is a
    prefix substitution.  Two items have no twin: ``noncontrolling_interest``,
    which does not exist in a separate statement and is therefore zero by
    definition, and ``deferred_tax``, which the separate chart of accounts does
    not expose at this granularity and which both consuming formulas already
    treat as zero when missing.
    """

    return {
        item: tuple("1001" + code[4:] for code in codes)
        for item, codes in IPCA_ACCOUNT_CODES.items()
        if item not in {"noncontrolling_interest", "deferred_tax"}
    }


IPCA_SEPARATE_ACCOUNT_CODES = _separate_scope_codes()


def _statement_scope_wide(
    dataset: object,
    *,
    scope: str,
    account_codes: dict[str, tuple[str, ...]],
    first_fiscal_year: int,
) -> pd.DataFrame:
    """Pivot one statement scope into a ticker/fiscal-period item table."""

    import pyarrow.dataset as ds

    codes = sorted({code for candidates in account_codes.values() for code in candidates})
    facts = dataset.to_table(
        columns=[
            "ticker",
            "fiscal_period",
            "account_code",
            "numeric_value",
            "dump_last_modified",
        ],
        filter=(
            (ds.field("statement_scope") == scope)
            & (ds.field("settlement_type") == "D")
            & (ds.field("fiscal_year") >= first_fiscal_year)
            & ds.field("account_code").isin(codes)
        ),
    ).to_pandas()
    if facts.empty:
        return pd.DataFrame(columns=["ticker", "fiscal_period", *IPCA_ACCOUNT_CODES])
    facts["ticker"] = facts["ticker"].astype(str).str.upper()
    facts["fiscal_period"] = pd.to_datetime(facts["fiscal_period"], errors="raise")
    facts["dump_last_modified"] = pd.to_datetime(
        facts["dump_last_modified"], errors="coerce"
    )
    facts["numeric_value"] = pd.to_numeric(facts["numeric_value"], errors="coerce")
    logical = ["ticker", "fiscal_period", "account_code"]
    facts = facts.sort_values([*logical, "dump_last_modified"]).drop_duplicates(
        logical, keep="last"
    )
    code_to_item = {
        code: item for item, candidates in account_codes.items() for code in candidates
    }
    code_priority = {
        code: priority
        for candidates in account_codes.values()
        for priority, code in enumerate(candidates)
    }
    facts["item"] = facts["account_code"].map(code_to_item)
    facts["priority"] = facts["account_code"].map(code_priority)
    item_key = ["ticker", "fiscal_period", "item"]
    facts = facts.sort_values([*item_key, "priority"]).drop_duplicates(
        item_key, keep="first"
    )
    wide = facts.pivot(
        index=["ticker", "fiscal_period"], columns="item", values="numeric_value"
    ).reset_index()
    for item in IPCA_ACCOUNT_CODES:
        if item not in wide:
            wide[item] = np.nan
    wide["calendar_year"] = wide["fiscal_period"].dt.year
    wide = wide.sort_values(["ticker", "fiscal_period"]).drop_duplicates(
        ["ticker", "calendar_year"], keep="last"
    )
    wide["statement_scope"] = scope
    return wide


def load_ipca_annual_accounting(
    statement_path: str | Path,
    annual_share_path: str | Path,
    dividend_path: str | Path,
    *,
    first_fiscal_year: int = 2016,
    reporting_lag_months: int = 3,
    allow_separate_fallback: bool = False,
) -> pd.DataFrame:
    """Load standardized annual inputs from the current Korean raw sources.

    The same fixed three-month availability lag is applied to every accounting
    item, as explicitly requested for this sensitivity.  Latest dump revisions
    are selected by logical key.

    With ``allow_separate_fallback`` a firm-year that has no usable
    consolidated statement falls back to its separate statement.  The choice is
    made per firm-year and is all-or-nothing: mixing consolidated assets with
    separate sales inside one firm-year would produce an internally
    inconsistent statement.  Issuers without subsidiaries file separate
    accounts only, so without the fallback they are dropped entirely.
    """

    if reporting_lag_months != 3:
        raise ValueError("the Korean IPCA sensitivity requires a fixed 3-month lag")
    import pyarrow.dataset as ds

    dataset = ds.dataset(statement_path, format="parquet", partitioning="hive")
    wide = _statement_scope_wide(
        dataset,
        scope="consolidated",
        account_codes=IPCA_ACCOUNT_CODES,
        first_fiscal_year=first_fiscal_year,
    )
    if allow_separate_fallback:
        separate = _statement_scope_wide(
            dataset,
            scope="separate",
            account_codes=IPCA_SEPARATE_ACCOUNT_CODES,
            first_fiscal_year=first_fiscal_year,
        )
        # A separate statement has no minority interest by construction.
        separate["noncontrolling_interest"] = 0.0
        core = list(CORE_STATEMENT_ITEMS)

        def _keys(frame: pd.DataFrame, complete_only: bool) -> set[tuple]:
            subset = (
                frame.loc[frame[core].notna().all(axis=1)] if complete_only else frame
            )
            return set(map(tuple, subset[["ticker", "calendar_year"]].to_numpy()))

        # Prefer a core-complete consolidated statement.  Fall back to separate
        # only where consolidated is absent or incomplete, and keep a partial
        # consolidated statement when no complete separate one exists either:
        # characteristics that need just a few items stay computable.
        consolidated_complete = _keys(wide, True)
        separate_complete = _keys(separate, True)
        consolidated_any = _keys(wide, False)
        take_separate = (separate_complete - consolidated_complete) | (
            _keys(separate, False) - consolidated_any
        )
        drop_consolidated = separate_complete - consolidated_complete
        wide = wide.loc[
            [
                key not in drop_consolidated
                for key in map(tuple, wide[["ticker", "calendar_year"]].to_numpy())
            ]
        ]
        separate = separate.loc[
            [
                key in take_separate
                for key in map(tuple, separate[["ticker", "calendar_year"]].to_numpy())
            ]
        ]
        if not separate.empty:
            warnings.warn(
                f"MIXED_STATEMENT_SCOPE: {len(separate)} firm-years use separate "
                "statements because no usable consolidated statement exists.",
                MixedStatementScopeWarning,
                stacklevel=2,
            )
            wide = pd.concat([wide, separate], ignore_index=True)
        wide = wide.sort_values(["ticker", "fiscal_period"]).reset_index(drop=True)

    shares = pd.read_parquet(
        annual_share_path,
        columns=["ticker", "base_date", "average_common_shares"],
    )
    shares["ticker"] = shares["ticker"].astype(str).str.upper()
    shares["calendar_year"] = pd.to_datetime(shares["base_date"]).dt.year
    shares = shares.sort_values(["ticker", "base_date"]).drop_duplicates(
        ["ticker", "calendar_year"], keep="last"
    )
    dividends = pd.read_parquet(
        dividend_path,
        columns=["ticker", "fiscal_period", "cash_dividend_amount"],
    )
    dividends["ticker"] = dividends["ticker"].astype(str).str.upper()
    dividends["calendar_year"] = pd.to_datetime(dividends["fiscal_period"]).dt.year
    dividends = (
        dividends.groupby(["ticker", "calendar_year"], as_index=False)[
            "cash_dividend_amount"
        ]
        .max()
        .rename(columns={"cash_dividend_amount": "cash_dividends"})
    )
    wide = wide.merge(
        shares[["ticker", "calendar_year", "average_common_shares"]],
        on=["ticker", "calendar_year"],
        how="left",
    ).merge(dividends, on=["ticker", "calendar_year"], how="left")

    nci = wide["noncontrolling_interest"].fillna(0.0)
    wide["book_equity"] = wide["total_equity"].sub(nci).combine_first(
        wide["total_assets"] - wide["total_liabilities"] - nci
    )
    wide["common_shares"] = wide["average_common_shares"]
    wide["available_date"] = (
        wide["fiscal_period"]
        + pd.offsets.MonthEnd(0)
        + pd.DateOffset(months=reporting_lag_months)
    )
    monetary = [
        *IPCA_ACCOUNT_CODES,
        "book_equity",
        "cash_dividends",
    ]
    for column in monetary:
        if column in wide:
            wide[column] = pd.to_numeric(wide[column], errors="coerce").mul(1_000.0)
    keep = [
        "ticker",
        "fiscal_period",
        "available_date",
        "statement_scope",
        "total_assets",
        "total_liabilities",
        "book_equity",
        "cash",
        "current_assets",
        "current_liabilities",
        "current_debt",
        "long_debt",
        "tax_payable",
        "inventory",
        "ppe",
        "sales",
        "cogs",
        "sga",
        "rd",
        "advertising",
        "operating_income",
        "interest_expense",
        "net_income",
        "depreciation",
        "amortization",
        "deferred_tax",
        "common_shares",
        "cash_dividends",
    ]
    return wide[keep].replace([np.inf, -np.inf], np.nan).reset_index(drop=True)


def _require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator.astype(float).div(denominator.astype(float))
    return result.where(denominator.ne(0)).replace([np.inf, -np.inf], np.nan)


def _compound_lags(wide: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """Compound monthly returns at inclusive lags ``start`` through ``end``."""

    gross = pd.DataFrame(1.0, index=wide.index, columns=wide.columns)
    complete = pd.DataFrame(True, index=wide.index, columns=wide.columns)
    for lag in range(start, end + 1):
        shifted = wide.shift(lag)
        gross = gross.mul(shifted.add(1.0))
        complete &= shifted.notna()
    return gross.where(complete).sub(1.0)


def _rolling_market_statistics(
    monthly: pd.DataFrame,
    *,
    beta_window: int = 60,
    beta_min_periods: int = 24,
) -> pd.DataFrame:
    """Estimate monthly market beta and residual variance without look-ahead."""

    market = monthly.groupby("date", sort=True)["return"].mean().rename("market")
    work = monthly.merge(market, on="date", how="left")

    def calculate(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values("date").copy()
        cov = group["return"].rolling(beta_window, beta_min_periods).cov(group["market"])
        var = group["market"].rolling(beta_window, beta_min_periods).var()
        group["MktBeta"] = cov.div(var).replace([np.inf, -np.inf], np.nan)
        residual = group["return"] - group["MktBeta"] * group["market"]
        group["Resid_Var"] = residual.rolling(2, 2).var()
        group["IdioVol"] = np.sqrt(group["Resid_Var"])
        return group

    parts: list[pd.DataFrame] = []
    for ticker, group in work.groupby("ticker", sort=False):
        calculated = calculate(group)
        calculated["ticker"] = ticker
        parts.append(calculated)
    return pd.concat(parts, ignore_index=True)


def build_monthly_price_characteristics(daily_prices: pd.DataFrame) -> pd.DataFrame:
    """Build the 17 price/trading characteristics available from local data.

    ``Beta`` uses daily market-model returns rather than the paper's five-year
    overlapping three-day estimator, and ``IdioVol``/``Resid_Var`` use the
    market model rather than FF3 before strict FF3 data begin.  These are
    explicitly classified as proxies in the returned audit of the top-level
    builder.
    """

    required = {
        "date",
        "ticker",
        "return",
        "adj_close",
        "adj_high",
        "adj_low",
        "trade_volume",
        "market_cap",
    }
    _require(daily_prices, required, "daily prices")
    columns = list(required)
    if "listed_common_shares" in daily_prices:
        columns.append("listed_common_shares")
    frame = daily_prices[columns].copy()
    if "listed_common_shares" not in frame:
        frame["listed_common_shares"] = _safe_divide(
            frame["market_cap"], frame["adj_close"]
        )
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame = frame.sort_values(["ticker", "date"])
    frame["month"] = frame["date"].dt.to_period("M")
    frame["hl_spread"] = _safe_divide(
        frame["adj_high"] - frame["adj_low"],
        (frame["adj_high"] + frame["adj_low"]) / 2.0,
    )

    market_daily = frame.groupby("date", sort=True)["return"].mean().rename("market")
    frame = frame.merge(market_daily, on="date", how="left")

    def daily_stats(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values("date").copy()
        cov = group["return"].rolling(1260, 750).cov(group["market"])
        var = group["market"].rolling(1260, 750).var()
        group["Beta"] = cov.div(var).replace([np.inf, -np.inf], np.nan)
        group["Variance"] = group["return"].rolling(42, 30).var()
        group["past_year_high"] = group["adj_high"].rolling(252, 120).max()
        return group

    parts: list[pd.DataFrame] = []
    for ticker, group in frame.groupby("ticker", sort=False):
        calculated = daily_stats(group)
        calculated["ticker"] = ticker
        parts.append(calculated)
    frame = pd.concat(parts, ignore_index=True)
    grouped = frame.groupby(["ticker", "month"], sort=False)
    monthly = grouped.agg(
        **{
            "date": ("date", "max"),
            "return": (
                "return",
                lambda value: (1.0 + value.dropna()).prod() - 1.0,
            ),
            "adj_close": ("adj_close", "last"),
            "market_cap": ("market_cap", "last"),
            "trade_volume": ("trade_volume", "sum"),
            "shares": ("listed_common_shares", "last"),
            "Beta": ("Beta", "last"),
            "Variance": ("Variance", "last"),
            "past_year_high": ("past_year_high", "last"),
            "Spread": ("hl_spread", "mean"),
        }
    ).reset_index()
    monthly["NI_proxy"] = np.log(
        _safe_divide(
            monthly["shares"],
            monthly.groupby("ticker", sort=False)["shares"].shift(12),
        )
    )
    monthly["LME"] = np.log(monthly["market_cap"].where(monthly["market_cap"].gt(0)))
    monthly["LTurnover"] = _safe_divide(monthly["trade_volume"], monthly["shares"])
    monthly["Rel2High"] = _safe_divide(
        monthly["adj_close"], monthly["past_year_high"]
    )

    # A signed last-day standardized unexplained-volume proxy.  Averaging OLS
    # residuals would be identically zero because the regression has an intercept.
    def suv(group: pd.DataFrame) -> float:
        clean = group[["trade_volume", "return"]].dropna()
        if len(clean) < 10:
            return np.nan
        y = np.log1p(clean["trade_volume"].to_numpy(float))
        ret = clean["return"].to_numpy(float)
        x = np.column_stack([np.ones(len(clean)), np.maximum(ret, 0), np.maximum(-ret, 0)])
        residual = y - x @ np.linalg.lstsq(x, y, rcond=None)[0]
        scale = residual.std(ddof=1)
        return float(residual[-1] / scale) if scale > 0 else np.nan

    suv_values = grouped.apply(suv).rename("SUV").reset_index()
    monthly = monthly.merge(suv_values, on=["ticker", "month"], how="left")
    monthly = _rolling_market_statistics(monthly)

    returns = monthly.pivot(index="month", columns="ticker", values="return").sort_index()
    signals = {
        "r2_1": returns,
        "ST_Rev": returns,
        "r12_2": _compound_lags(returns, 1, 11),
        "r12_7": _compound_lags(returns, 6, 11),
        "r36_13": _compound_lags(returns, 12, 35),
        "LT_Rev": _compound_lags(returns, 12, 59),
    }
    keys = monthly[["ticker", "month", "date"]].copy()
    for name, wide in signals.items():
        long = (
            wide.rename_axis(index="month", columns="ticker")
            .reset_index()
            .melt(id_vars="month", var_name="ticker", value_name=name)
        )
        keys = keys.merge(long, on=["month", "ticker"], how="left")
    keep = [
        "ticker",
        "month",
        "date",
        "return",
        "market_cap",
        "NI_proxy",
        *PRICE_CHARACTERISTICS,
    ]
    base = monthly.drop(columns=["date"]).merge(keys, on=["ticker", "month"], how="left")
    return base[keep].sort_values(["date", "ticker"]).reset_index(drop=True)


def build_accounting_characteristics(annual: pd.DataFrame) -> pd.DataFrame:
    """Build 29 accounting characteristics from standardized annual inputs.

    Monetary inputs must use one common unit.  ``available_date`` must already
    equal fiscal period end plus three months.
    """

    required = {
        "ticker",
        "fiscal_period",
        "available_date",
        "total_assets",
        "total_liabilities",
        "book_equity",
        "cash",
        "current_assets",
        "current_liabilities",
        "current_debt",
        "long_debt",
        "tax_payable",
        "inventory",
        "ppe",
        "sales",
        "cogs",
        "sga",
        "rd",
        "advertising",
        "operating_income",
        "interest_expense",
        "net_income",
        "depreciation",
        "amortization",
        "deferred_tax",
        "common_shares",
        "cash_dividends",
    }
    _require(annual, required, "annual accounting panel")
    frame = annual.copy()
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame["fiscal_period"] = pd.to_datetime(frame["fiscal_period"], errors="raise")
    frame["available_date"] = pd.to_datetime(frame["available_date"], errors="raise")
    frame = frame.sort_values(["ticker", "fiscal_period"]).reset_index(drop=True)
    group = frame.groupby("ticker", sort=False)
    lag = {column: group[column].shift(1) for column in required if column in frame and column not in {"ticker", "fiscal_period", "available_date"}}
    da = frame["depreciation"].fillna(0) + frame["amortization"].fillna(0)
    debt = frame["current_debt"].fillna(0) + frame["long_debt"].fillna(0)
    operating_assets = frame["total_assets"] - frame["cash"].fillna(0)
    operating_liabilities = frame["total_liabilities"] - debt
    noa_amount = operating_assets - operating_liabilities
    lag_noa = noa_amount.groupby(frame["ticker"], sort=False).shift(1)
    working_capital = (
        frame["current_assets"]
        - frame["cash"].fillna(0)
        - frame["current_liabilities"]
        - frame["current_debt"].fillna(0)
        - frame["tax_payable"].fillna(0)
    )
    delta_wc = working_capital - working_capital.groupby(frame["ticker"], sort=False).shift(1)
    lag_assets = lag["total_assets"]
    lag_be = lag["book_equity"]
    delta_ppe_inventory = (
        frame["ppe"].fillna(0)
        + frame["inventory"].fillna(0)
        - lag["ppe"].fillna(0)
        - lag["inventory"].fillna(0)
    )
    capex_proxy = (frame["ppe"] - lag["ppe"]).clip(lower=0).fillna(0) + da
    gross_profit = frame["sales"] - frame["cogs"]

    carry = ["ticker", "fiscal_period", "available_date"]
    if "statement_scope" in frame:
        carry.append("statement_scope")
    output = frame[carry].copy()
    output["Investment"] = _safe_divide(frame["total_assets"] - lag_assets, lag_assets)
    output["NOA"] = _safe_divide(noa_amount, lag_assets)
    output["DPI2A"] = _safe_divide(delta_ppe_inventory, lag_assets)
    output["NI"] = np.log(_safe_divide(frame["common_shares"], lag["common_shares"]))
    output["PROF"] = _safe_divide(gross_profit, frame["book_equity"])
    output["ATO"] = _safe_divide(frame["sales"], lag_noa)
    output["CTO"] = _safe_divide(frame["sales"], lag_assets)
    output["FC2Y"] = _safe_divide(
        frame["sga"].fillna(0) + frame["rd"].fillna(0) + frame["advertising"].fillna(0),
        frame["sales"],
    )
    output["OP"] = _safe_divide(
        frame["sales"] - frame["cogs"] - frame["interest_expense"].fillna(0) - frame["sga"].fillna(0),
        frame["book_equity"],
    )
    output["PM"] = _safe_divide(frame["operating_income"], frame["sales"])
    output["RNA"] = _safe_divide(frame["operating_income"], lag_noa)
    output["ROA"] = _safe_divide(frame["net_income"], lag_assets)
    output["ROE"] = _safe_divide(frame["net_income"], lag_be)
    output["SGA2S"] = _safe_divide(frame["sga"], frame["sales"])
    output["D2A"] = _safe_divide(da, frame["total_assets"])
    output["AC"] = _safe_divide(delta_wc, frame["book_equity"])
    output["OA"] = _safe_divide(delta_wc - da, lag_assets)
    output["OL"] = _safe_divide(frame["cogs"] + frame["sga"].fillna(0), frame["total_assets"])
    output["PCM"] = _safe_divide(gross_profit, frame["sales"])
    # Market-scaled variables are completed after the as-of merge with month-end ME.
    output["A2ME"] = frame["total_assets"]
    output["BEME"] = frame["book_equity"]
    output["C"] = _safe_divide(frame["cash"], frame["total_assets"])
    output["CF"] = _safe_divide(frame["net_income"] + da - delta_wc - capex_proxy, frame["book_equity"])
    output["CF2P"] = frame["net_income"] + da + frame["deferred_tax"].fillna(0)
    output["D2P"] = frame["cash_dividends"]
    output["E2P"] = frame["net_income"]
    output["Q"] = frame["total_assets"] - frame["book_equity"] - frame["deferred_tax"].fillna(0)
    output["S2P"] = frame["sales"]
    output["Lev"] = _safe_divide(debt, debt + frame["book_equity"])
    output["AT"] = frame["total_assets"]
    return output[[*carry, *ACCOUNTING_CHARACTERISTICS]]


def _asof_accounting(price: pd.DataFrame, accounting: pd.DataFrame) -> pd.DataFrame:
    price = price.copy()
    accounting = accounting.copy()
    price["date"] = pd.to_datetime(price["date"]).astype("datetime64[ns]")
    accounting["available_date"] = pd.to_datetime(
        accounting["available_date"]
    ).astype("datetime64[ns]")
    pieces: list[pd.DataFrame] = []
    by_ticker = {ticker: part for ticker, part in accounting.groupby("ticker", sort=False)}
    for ticker, left in price.groupby("ticker", sort=False):
        right = by_ticker.get(ticker)
        left = left.sort_values("date")
        if right is None:
            merged = left.copy()
            for column in ["fiscal_period", "available_date", *ACCOUNTING_CHARACTERISTICS]:
                merged[column] = pd.NaT if column in {"fiscal_period", "available_date"} else np.nan
            if "statement_scope" in accounting:
                merged["statement_scope"] = None
        else:
            merged = pd.merge_asof(
                left,
                right.sort_values("available_date"),
                left_on="date",
                right_on="available_date",
                by="ticker",
                direction="backward",
                allow_exact_matches=True,
            )
        pieces.append(merged)
    return pd.concat(pieces, ignore_index=True)


def _estimation_universe(raw: pd.DataFrame, cap_proportion: float = 0.01) -> pd.DataFrame:
    """Apply the IPCA market-cap filter used by the estimator."""

    frame = raw.copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.to_period("M").dt.to_timestamp("M")
    total = frame.groupby("date", sort=False)["market_cap"].transform("sum")
    return frame.loc[frame["market_cap"].div(total).ge(cap_proportion * 0.01)]


def rank_normalize_characteristics(
    panel: pd.DataFrame,
    *,
    impute_missing: bool,
) -> pd.DataFrame:
    """Cross-sectionally rank characteristics to [-0.5, 0.5]."""

    _require(panel, {"date", "ticker", *CHARACTERISTIC_COLUMNS}, "characteristic panel")
    pass_through = [
        column for column in ("date", "ticker", "return", "market_cap") if column in panel
    ]
    normalized = panel[pass_through].copy()
    for column in CHARACTERISTIC_COLUMNS:
        values = panel.groupby("date", sort=False)[column].rank(pct=True, method="average") - 0.5
        if impute_missing:
            values = values.fillna(0.0)
        normalized[column] = values
    return normalized


def build_monthly_characteristics(
    daily_prices: pd.DataFrame,
    annual_accounting: pd.DataFrame,
    *,
    impute_missing: bool = False,
) -> CharacteristicResult:
    """Build and normalize all 46 characteristics with mandatory warnings."""

    warnings.warn(
        "NON_PIT_3M_LAG: annual statements are latest revisions made available "
        "at fiscal-period end plus three months.",
        NonPITAccountingWarning,
        stacklevel=2,
    )
    warnings.warn(
        "PROXY_CHARACTERISTICS: Spread uses daily high-low ranges; Beta, "
        "IdioVol and Resid_Var use local market-model approximations.",
        ProxyCharacteristicWarning,
        stacklevel=2,
    )
    price = build_monthly_price_characteristics(daily_prices)
    accounting = build_accounting_characteristics(annual_accounting)
    raw = _asof_accounting(price, accounting)
    raw["NI"] = raw["NI"].combine_first(raw["NI_proxy"])
    me = raw["LME"].pipe(np.exp)
    for column in ("A2ME", "BEME", "CF2P", "D2P", "E2P", "S2P"):
        raw[column] = _safe_divide(raw[column], me)
    raw["Q"] = _safe_divide(raw["Q"] + me, raw["AT"])
    scope_columns = ["statement_scope"] if "statement_scope" in raw else []
    raw = raw[
        [
            "date",
            "ticker",
            "return",
            "market_cap",
            "fiscal_period",
            "available_date",
            *scope_columns,
            *CHARACTERISTIC_COLUMNS,
        ]
    ]
    normalized = rank_normalize_characteristics(raw, impute_missing=impute_missing)
    coverage = {
        column: float(raw[column].notna().mean()) for column in CHARACTERISTIC_COLUMNS
    }
    # `coverage` spans every ticker and month in the raw panel, including the
    # years before any statement is available.  IPCA never estimates on that
    # panel: it drops stocks below 0.01% of aggregate market capitalization.
    # Instrument selection has to be judged on the universe actually fitted.
    universe = _estimation_universe(raw)
    coverage_universe = {
        column: float(universe[column].notna().mean())
        for column in CHARACTERISTIC_COLUMNS
    }
    if scope_columns:
        scope_counts = (
            raw["statement_scope"].value_counts(dropna=True).astype(int).to_dict()
        )
    else:
        scope_counts = {}
    audit: dict[str, object] = {
        "classification": "Korean IPCA non-PIT 3-month-lag sensitivity",
        "characteristic_count": len(CHARACTERISTIC_COLUMNS),
        "statement_scope_rows": scope_counts,
        "coverage_basis": {
            "coverage": "all tickers and months in the raw panel",
            "coverage_estimation_universe": (
                "months and tickers that survive the 0.01% market-cap filter"
            ),
        },
        "reporting_lag_months": 3,
        "statement_vintage": "latest local dump revision",
        "imputation": "cross-sectional median rank (0.0)" if impute_missing else "none",
        "proxy_characteristics": {
            "Spread": "monthly mean daily high-low relative range; no bid/ask quotes",
            "Beta": "daily local equal-weight market model; 1260-day window, 750 minimum",
            "MktBeta": "monthly local equal-weight market model; 60 months, 24 minimum",
            "IdioVol": "monthly market-model residual volatility",
            "Resid_Var": "two-month market-model residual variance",
            "CF": "capital expenditure proxied by positive PPE change plus D&A",
            "NI": "12-month listed-common-share change fills the bounded annual-share extract",
        },
        "coverage": coverage,
        "coverage_estimation_universe": coverage_universe,
        "rows": len(raw),
        "start": raw["date"].min().date().isoformat(),
        "end": raw["date"].max().date().isoformat(),
    }
    return CharacteristicResult(raw=raw, normalized=normalized, audit=audit)
