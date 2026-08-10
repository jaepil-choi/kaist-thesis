from __future__ import annotations

import pandas as pd
import pytest

from guijarro_ordonez_replication.kimchi_methodology import (
    annual_yield_percent_to_period_return,
    assign_kospi_2x3_buckets,
    assign_kospi_quintiles,
    compute_accounting_signals,
    filter_rebalance_universe,
)


def _security_cross_section() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": ["A", "B", "C", "D", "E", "F"],
            "market": ["KOSPI", "KOSPI", "KOSDAQ", "KOSPI", "KOSPI", "KONEX"],
            "is_common_stock": [True, True, True, True, True, True],
            "is_listed": [True] * 6,
            "is_spac": [False, False, False, True, False, False],
            "is_pre_merger_spac": [False] * 6,
            "is_trading_halt": [False, False, False, False, True, False],
            "is_financial": [False, True, True, False, False, False],
        }
    )


def test_universe_excludes_ineligible_names_and_financials_by_factor() -> None:
    frame = _security_cross_section()
    hml = filter_rebalance_universe(frame, factor="HML")
    momentum = filter_rebalance_universe(frame, factor="MOM")
    assert hml["ticker"].tolist() == ["A"]
    assert momentum["ticker"].tolist() == ["A", "B", "C"]


def test_breakpoints_come_only_from_kospi_and_apply_to_kosdaq() -> None:
    frame = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "market": ["KOSPI", "KOSPI", "KOSDAQ"],
            "market_cap": [100.0, 200.0, 10_000.0],
            "signal": [1.0, 3.0, 100.0],
        }
    )
    result = assign_kospi_2x3_buckets(frame, signal_column="signal").set_index(
        "ticker"
    )
    assert result.loc["C", "bucket"] == "B3"
    assert result.loc["C", "size_breakpoint"] == pytest.approx(150.0)
    assert result.loc["C", "signal_30_breakpoint"] == pytest.approx(1.6)
    assert result.loc["C", "signal_70_breakpoint"] == pytest.approx(2.4)


def test_size_breakpoint_does_not_depend_on_signal_coverage() -> None:
    frame = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "market": ["KOSPI", "KOSPI", "KOSPI"],
            "market_cap": [100.0, 200.0, 1_000.0],
            "signal": [1.0, 2.0, None],
        }
    )
    result = assign_kospi_2x3_buckets(frame, signal_column="signal")
    assert result["size_breakpoint"].iloc[0] == pytest.approx(200.0)


def test_quintiles_are_not_size_neutralized() -> None:
    frame = pd.DataFrame(
        {
            "ticker": ["A", "B", "C", "D", "E", "F"],
            "market": ["KOSPI"] * 5 + ["KOSDAQ"],
            "signal": [1.0, 2.0, 3.0, 4.0, 5.0, 10.0],
        }
    )
    result = assign_kospi_quintiles(frame, signal_column="signal").set_index("ticker")
    assert result.loc["F", "quantile"] == "Q5"
    assert "size_bucket" not in result.columns


def test_accounting_signals_require_prior_fiscal_year_and_three_month_lag() -> None:
    frame = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "formation_date": ["2021-06-30", "2021-06-30", "2021-06-30"],
            "fiscal_period": ["2020-12-01", "2021-03-01", "2020-12-01"],
            "market_cap": [200.0, 200.0, 200.0],
            "total_equity": [120.0, 120.0, 120.0],
            "noncontrolling_interest": [None, 0.0, 130.0],
            "ebitda": [30.0, 30.0, 30.0],
            "interest_expense": [6.0, 6.0, 6.0],
            "total_assets": [550.0, 550.0, 550.0],
            "prior_total_assets": [500.0, 500.0, 500.0],
        }
    )
    result = compute_accounting_signals(frame, reporting_lag_months=3)
    assert result["ticker"].tolist() == ["A"]
    assert result.loc[0, "available_date"] == pd.Timestamp("2021-03-31")
    assert result.loc[0, "book_equity"] == pytest.approx(120.0)
    assert result.loc[0, "book_to_market"] == pytest.approx(0.60)
    assert result.loc[0, "profitability"] == pytest.approx(0.20)
    assert result.loc[0, "investment"] == pytest.approx(0.10)


def test_cd_yield_uses_geometric_252_day_conversion() -> None:
    actual = annual_yield_percent_to_period_return(1.36, periods_per_year=252)
    expected = (1.0 + 0.0136) ** (1.0 / 252.0) - 1.0
    assert actual == pytest.approx(expected)
