import numpy as np
import pandas as pd
import pytest

from kaniel_replication.stock_factors import (
    attach_risk_free,
    build_carhart_equity_factors,
    derive_non_pit_book_equity,
    prepare_monthly_stock_panel,
)


def test_non_pit_book_equity_requires_explicit_override() -> None:
    facts = pd.DataFrame(
        {
            "ticker": ["A"],
            "fiscal_period": ["2020-12-01"],
            "settlement_type": ["D"],
            "statement_scope": ["consolidated"],
            "account_code": ["4001160000"],
            "numeric_value": [100.0],
            "dump_last_modified": ["2026-01-01"],
        }
    )
    with pytest.raises(ValueError, match="announcement timestamps"):
        derive_non_pit_book_equity(facts, reporting_lag_months=4)
    result = derive_non_pit_book_equity(
        facts, reporting_lag_months=4, allow_non_pit=True
    )
    assert result.loc[0, "book_equity"] == 100_000.0
    assert result.loc[0, "available_date"] == pd.Timestamp("2021-04-30")


def test_monthly_carhart_builder_uses_lagged_formation_data() -> None:
    months = pd.date_range("2019-01-31", periods=36, freq="ME")
    tickers = [f"A{i:06d}" for i in range(18)]
    rows = []
    for month_number, month in enumerate(months):
        for ticker_number, ticker in enumerate(tickers):
            rows.append(
                {
                    "date": month,
                    "ticker": ticker,
                    "return": (ticker_number % 3 - 1) * 0.001
                    + month_number * 0.0001,
                    "market_cap": float((ticker_number + 1) * 1_000_000 + month_number),
                }
            )
    monthly = prepare_monthly_stock_panel(pd.DataFrame(rows))
    book = pd.DataFrame(
        {
            "ticker": tickers,
            "available_date": pd.Timestamp("2018-12-31"),
            "book_equity": [
                float((index + 1) * 1_000_000 * [0.5, 1.0, 2.0][index % 3])
                for index in range(18)
            ],
        }
    )
    monthly["month"] = monthly["month"].astype("datetime64[us]")
    book["available_date"] = book["available_date"].astype("datetime64[s]")
    factors = build_carhart_equity_factors(monthly, book)
    usable = factors.dropna(subset=["mkt", "smb", "hml", "mom"])
    assert not usable.empty
    assert usable["month"].min() > months.min()
    rf = pd.DataFrame({"month": factors["month"], "rf": 0.001})
    completed = attach_risk_free(factors, rf)
    assert np.allclose(completed["mkt_rf"], factors["mkt"] - 0.001, equal_nan=True)
