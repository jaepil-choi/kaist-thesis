from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from guijarro_ordonez_replication.factors import (
    build_annual_memberships,
    compare_return_columns,
    derive_lagged_annual_characteristics,
    factor_return_from_buckets,
    prepare_daily_stock_panel,
)


def test_statement_characteristics_require_override_and_use_three_month_lag() -> None:
    facts = pd.DataFrame(
        {
            "ticker": ["A", "A", "A", "A", "A", "A"],
            "fiscal_period": [
                "2019-12-01",
                "2019-12-01",
                "2019-12-01",
                "2020-12-01",
                "2020-12-01",
                "2020-12-01",
            ],
            "settlement_type": ["D"] * 6,
            "statement_scope": ["consolidated"] * 6,
            "account_code": [
                "4001160000",
                "4001230000",
                "4001110000",
                "4001160000",
                "4001230000",
                "4001110000",
            ],
            "numeric_value": [100.0, 20.0, 500.0, 120.0, 30.0, 550.0],
            "dump_last_modified": ["2026-01-01"] * 6,
        }
    )
    with pytest.raises(ValueError, match="announcement timestamps"):
        derive_lagged_annual_characteristics(facts, reporting_lag_months=3)
    result = derive_lagged_annual_characteristics(
        facts,
        reporting_lag_months=3,
        allow_non_pit=True,
    )
    row = result.loc[result["fiscal_period"].eq(pd.Timestamp("2020-12-01"))].iloc[0]
    assert row["available_date"] == pd.Timestamp("2021-03-31")
    assert row["book_equity"] == 120_000.0
    assert row["profitability"] == pytest.approx(0.25)
    assert row["investment"] == pytest.approx(0.10)


def test_daily_panel_never_uses_same_day_market_cap() -> None:
    prices = pd.DataFrame(
        {
            "date": ["2020-01-02", "2020-01-03"],
            "ticker": ["A", "A"],
            "return": [0.01, 0.02],
            "market_cap": [100.0, 102.0],
        }
    )
    result = prepare_daily_stock_panel(prices)
    assert np.isnan(result.loc[0, "lag_market_cap"])
    assert result.loc[1, "lag_market_cap"] == 100.0


def test_annual_membership_normalizes_datetime_precision() -> None:
    daily = pd.DataFrame(
        {
            "date": pd.Series(["2021-06-30"], dtype="datetime64[us]"),
            "ticker": ["A"],
            "market_cap": [200_000.0],
        }
    )
    characteristics = pd.DataFrame(
        {
            "ticker": ["A"],
            "available_date": pd.Series(["2021-03-31"], dtype="datetime64[s]"),
            "book_equity": [100_000.0],
            "profitability": [0.20],
            "investment": [0.10],
        }
    )
    memberships = build_annual_memberships(daily, characteristics)
    assert memberships["HML"].loc[0, "formation_year"] == 2021


def test_factor_bucket_identities_match_kimchi_convention() -> None:
    buckets = pd.DataFrame(
        {
            "date": pd.Timestamp("2020-01-02"),
            "bucket": ["S1", "S2", "S3", "B1", "B2", "B3"],
            "ret": [0.01, 0.02, 0.05, 0.00, 0.01, 0.03],
        }
    )
    assert factor_return_from_buckets(buckets, factor="SMB").iloc[0] == pytest.approx(
        (0.01 + 0.02 + 0.05) / 3 - (0.00 + 0.01 + 0.03) / 3
    )
    assert factor_return_from_buckets(buckets, factor="HML").iloc[0] == pytest.approx(
        (0.05 + 0.03) / 2 - (0.01 + 0.00) / 2
    )
    assert factor_return_from_buckets(buckets, factor="CMA").iloc[0] == pytest.approx(
        (0.01 + 0.00) / 2 - (0.05 + 0.03) / 2
    )
    assert factor_return_from_buckets(buckets, factor="STR").iloc[0] == pytest.approx(
        (0.01 + 0.00) / 2 - (0.05 + 0.03) / 2
    )


def test_comparison_reports_perfect_match() -> None:
    frame = pd.DataFrame(
        {"date": pd.date_range("2020-01-01", periods=3), "RM": [0.1, -0.1, 0.2]}
    )
    aligned, summary = compare_return_columns(frame, frame, ["RM"])
    assert len(aligned) == 3
    assert summary.loc[0, "correlation"] == pytest.approx(1.0)
    assert summary.loc[0, "mae"] == pytest.approx(0.0)
