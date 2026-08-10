import numpy as np
import pandas as pd
import pytest

from guijarro_ordonez_replication.characteristics import (
    CHARACTERISTIC_COLUMNS,
    NonPITAccountingWarning,
    ProxyCharacteristicWarning,
    build_accounting_characteristics,
    build_monthly_characteristics,
    rank_normalize_characteristics,
)


def _annual_panel() -> pd.DataFrame:
    rows = []
    for ticker, scale in [("A", 1.0), ("B", 1.5)]:
        for year in (2018, 2019, 2020):
            growth = 1.0 + 0.1 * (year - 2018)
            rows.append(
                {
                    "ticker": ticker,
                    "fiscal_period": f"{year}-12-31",
                    "available_date": f"{year + 1}-03-31",
                    "total_assets": 1_000 * scale * growth,
                    "total_liabilities": 400 * scale,
                    "book_equity": 600 * scale,
                    "cash": 100 * scale,
                    "current_assets": 500 * scale,
                    "current_liabilities": 250 * scale,
                    "current_debt": 50 * scale,
                    "long_debt": 100 * scale,
                    "tax_payable": 10 * scale,
                    "inventory": 80 * scale * growth,
                    "ppe": 300 * scale * growth,
                    "sales": 900 * scale,
                    "cogs": 500 * scale,
                    "sga": 100 * scale,
                    "rd": 20 * scale,
                    "advertising": 10 * scale,
                    "operating_income": 150 * scale,
                    "interest_expense": 10 * scale,
                    "net_income": 110 * scale,
                    "depreciation": 30 * scale,
                    "amortization": 5 * scale,
                    "deferred_tax": 8 * scale,
                    "common_shares": 100 * scale * growth,
                    "cash_dividends": 20 * scale,
                }
            )
    return pd.DataFrame(rows)


def _daily_panel() -> pd.DataFrame:
    dates = pd.bdate_range("2018-01-02", "2021-12-31")
    rows = []
    for ticker, shift in [("A", 0.0002), ("B", -0.0001)]:
        ret = 0.001 * np.sin(np.arange(len(dates)) / 13.0) + shift
        close = 100 * np.cumprod(1 + ret)
        for index, date in enumerate(dates):
            rows.append(
                {
                    "date": date,
                    "ticker": ticker,
                    "return": ret[index],
                    "adj_close": close[index],
                    "adj_high": close[index] * 1.01,
                    "adj_low": close[index] * 0.99,
                    "trade_volume": 1_000 + index,
                    "market_cap": close[index] * 1_000_000,
                }
            )
    return pd.DataFrame(rows)


def test_accounting_builder_has_all_29_accounting_characteristics() -> None:
    result = build_accounting_characteristics(_annual_panel())

    assert len(result.columns) == 33
    assert result["Investment"].notna().sum() == 4
    assert result["available_date"].min() == pd.Timestamp("2019-03-31")


def test_full_builder_emits_warnings_and_exactly_46_columns() -> None:
    with pytest.warns(NonPITAccountingWarning):
        with pytest.warns(ProxyCharacteristicWarning):
            result = build_monthly_characteristics(
                _daily_panel(), _annual_panel(), impute_missing=True
            )

    assert all(column in result.normalized for column in CHARACTERISTIC_COLUMNS)
    assert result.normalized[list(CHARACTERISTIC_COLUMNS)].notna().all().all()
    assert result.normalized[list(CHARACTERISTIC_COLUMNS)].max().max() <= 0.5
    assert result.audit["reporting_lag_months"] == 3
    assert "Spread" in result.audit["proxy_characteristics"]


def test_rank_normalization_does_not_impute_unless_requested() -> None:
    panel = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-31")] * 2,
            "ticker": ["A", "B"],
            **{
                column: [1.0, np.nan] if column == "r2_1" else [1.0, 2.0]
                for column in CHARACTERISTIC_COLUMNS
            },
        }
    )

    strict = rank_normalize_characteristics(panel, impute_missing=False)
    imputed = rank_normalize_characteristics(panel, impute_missing=True)

    assert pd.isna(strict.loc[1, "r2_1"])
    assert imputed.loc[1, "r2_1"] == 0.0
