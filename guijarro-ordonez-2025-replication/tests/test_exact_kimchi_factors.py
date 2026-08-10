from __future__ import annotations

import pandas as pd
import pytest

from guijarro_ordonez_replication.exact_kimchi_factors import (
    _factor_from_six_buckets,
    build_momentum_memberships,
    derive_accounting_signals,
    load_market_snapshots,
)


def test_sqlplus_truncated_headers_are_normalized_positionally() -> None:
    path = (
        __file__.replace("test_exact_kimchi_factors.py", "")
        + "fixtures/fgsc_truncated_headers.csv"
    )
    result = load_market_snapshots(path).set_index("ticker")
    assert result.loc["A005930", "market"] == "KOSPI"
    assert bool(result.loc["A123456", "is_financial"])
    assert bool(result.loc["A123456", "is_spac"])


def test_account_mapping_builds_ebitda_and_controlling_equity_fallback() -> None:
    rows: list[dict[str, object]] = []
    values = {
        "4001110000": [("2019-12-31", 100.0), ("2020-12-31", 110.0)],
        "4001160050": [("2020-12-31", 45.0)],
        "4001230000": [("2020-12-31", 10.0)],
        "4001250100": [("2020-12-31", 1.0)],
        "4001410500": [("2020-12-31", 2.0)],
        "4001410600": [("2020-12-31", 1.0)],
    }
    for code, observations in values.items():
        for fiscal_period, value in observations:
            rows.append(
                {
                    "ticker": "A",
                    "fiscal_period": fiscal_period,
                    "fiscal_year": int(fiscal_period[:4]),
                    "settlement_type": "D",
                    "statement_scope": "consolidated",
                    "account_code": code,
                    "numeric_value": value,
                    "dump_last_modified": "2026-01-01",
                }
            )
    result = derive_accounting_signals(pd.DataFrame(rows)).set_index("fiscal_year")
    assert result.loc[2020, "book_equity_source"] == "controlling_equity_fallback"
    assert result.loc[2020, "book_equity_krw"] == pytest.approx(45_000.0)
    assert result.loc[2020, "ebitda_krw"] == pytest.approx(13_000.0)
    assert result.loc[2020, "interest_expense_krw"] == pytest.approx(1_000.0)
    assert result.loc[2020, "prior_total_assets_krw"] == pytest.approx(100_000.0)
    assert result.loc[2020, "available_date"] == pd.Timestamp("2021-03-31")


def test_last_annual_statement_is_selected_when_fiscal_year_end_changes() -> None:
    rows: list[dict[str, object]] = []
    for period, value in (("2020-03-01", 90.0), ("2020-12-01", 110.0)):
        rows.append(
            {
                "ticker": "A",
                "fiscal_period": period,
                "fiscal_year": 2020,
                "settlement_type": "D",
                "statement_scope": "consolidated",
                "account_code": "4001110000",
                "numeric_value": value,
                "dump_last_modified": "2026-01-01",
            }
        )
    result = derive_accounting_signals(pd.DataFrame(rows))
    assert len(result) == 1
    assert result.loc[0, "fiscal_period"] == pd.Timestamp("2020-12-01")
    assert result.loc[0, "total_assets_krw"] == pytest.approx(110_000.0)


def test_balance_sheet_identity_fills_missing_total_equity() -> None:
    rows = []
    for code, value in (("4001110000", 100.0), ("4001140000", 60.0)):
        rows.append(
            {
                "ticker": "A",
                "fiscal_period": "2017-12-01",
                "fiscal_year": 2017,
                "settlement_type": "D",
                "statement_scope": "consolidated",
                "account_code": code,
                "numeric_value": value,
                "dump_last_modified": "2026-01-01",
            }
        )
    result = derive_accounting_signals(pd.DataFrame(rows))
    assert result.loc[0, "book_equity_krw"] == pytest.approx(40_000.0)
    assert (
        result.loc[0, "book_equity_source"]
        == "assets_minus_liabilities_minus_nci_fallback"
    )


def test_momentum_excludes_formation_month_and_requires_prior_eleven_months() -> None:
    tickers = ["A", "B", "C", "D", "E", "F"]
    months = pd.period_range("2017-01", "2018-01", freq="M")
    rows: list[dict[str, object]] = []
    for ticker_number, ticker in enumerate(tickers, start=1):
        for month in months:
            formation_month_return = 9.0 if month == pd.Period("2018-01") else 0.001
            rows.append(
                {
                    "date": month.to_timestamp("M"),
                    "ticker": ticker,
                    "return": formation_month_return + ticker_number / 10_000,
                    "raw_close": 100.0,
                    "listed_common_shares": float(ticker_number * 100),
                    "market_cap": float(ticker_number * 10_000),
                    "is_trading_halt": False,
                }
            )
    prices = pd.DataFrame(rows)
    snapshots = pd.DataFrame(
        {
            "date": [pd.Timestamp("2018-01-31")] * 6,
            "ticker": tickers,
            "market": ["KOSPI"] * 5 + ["KOSDAQ"],
            "is_common_stock": [True] * 6,
            "is_listed": [True] * 6,
            "is_spac": [False] * 6,
            "is_pre_merger_spac": [False] * 6,
            "is_financial": [False] * 6,
        }
    )
    result = build_momentum_memberships(snapshots, prices)
    assert len(result) == 6
    assert result["holding_month"].eq(pd.Period("2018-02")).all()
    assert result["characteristic"].max() < 0.02


def test_six_bucket_factor_identities() -> None:
    buckets = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-02")] * 6,
            "bucket": ["S1", "S2", "S3", "B1", "B2", "B3"],
            "ret": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06],
        }
    )
    assert _factor_from_six_buckets(buckets, factor="SMB").iloc[0] == pytest.approx(
        -0.03
    )
    assert _factor_from_six_buckets(buckets, factor="HML").iloc[0] == pytest.approx(
        0.02
    )
    assert _factor_from_six_buckets(buckets, factor="CMA").iloc[0] == pytest.approx(
        -0.02
    )
