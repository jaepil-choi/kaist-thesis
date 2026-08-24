"""Tests for the separate-scope fallback and the share-class filter.

Both are opt-in deviations from the project's consolidated-only default, so
these tests pin the default behaviour first and the opt-in behaviour second.
"""

import numpy as np
import pandas as pd
import pytest

from guijarro_ordonez_replication.characteristics import (
    CORE_STATEMENT_ITEMS,
    IPCA_ACCOUNT_CODES,
    IPCA_SEPARATE_ACCOUNT_CODES,
    MixedStatementScopeWarning,
    ShareClassFilterWarning,
    filter_common_share_class,
    load_ipca_annual_accounting,
)


def test_separate_twin_codes_share_the_trailing_digits() -> None:
    for item, codes in IPCA_SEPARATE_ACCOUNT_CODES.items():
        consolidated = IPCA_ACCOUNT_CODES[item]
        assert len(codes) == len(consolidated)
        for separate, joint in zip(codes, consolidated, strict=True):
            assert separate.startswith("1001")
            assert joint.startswith("4001")
            assert separate[4:] == joint[4:]


def test_items_without_a_separate_twin_are_excluded() -> None:
    missing = set(IPCA_ACCOUNT_CODES).difference(IPCA_SEPARATE_ACCOUNT_CODES)
    assert missing == {"noncontrolling_interest", "deferred_tax"}


def test_share_class_filter_keeps_only_common_shares() -> None:
    frame = pd.DataFrame(
        {
            "ticker": ["A005930", "a005935", "A000660", "A00088K", "A0001P0"],
            "value": [1, 2, 3, 4, 5],
        }
    )

    with pytest.warns(ShareClassFilterWarning, match="removed 2"):
        kept, dropped = filter_common_share_class(frame)

    assert dropped == 2
    assert sorted(kept["ticker"]) == ["A0001P0", "A000660", "A005930"]


def test_share_class_filter_is_silent_when_nothing_is_dropped() -> None:
    import warnings

    frame = pd.DataFrame({"ticker": ["A005930", "A000660"], "value": [1, 2]})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        kept, dropped = filter_common_share_class(frame)
    assert dropped == 0
    assert len(kept) == 2


def _write_statement_fixture(root) -> None:
    """Three issuers: consolidated-complete, separate-only, consolidated-partial."""

    def rows(ticker, scope, items, value):
        codes = (
            IPCA_ACCOUNT_CODES if scope == "consolidated" else IPCA_SEPARATE_ACCOUNT_CODES
        )
        return [
            {
                "ticker": ticker,
                "fiscal_period": "2020-12-01",
                "account_code": codes[item][0],
                "numeric_value": float(value),
                "dump_last_modified": pd.Timestamp("2026-01-01"),
                "settlement_type": "D",
                "statement_scope": scope,
                "fiscal_year": 2020,
            }
            for item in items
            if item in codes
        ]

    full = list(IPCA_ACCOUNT_CODES)
    records = []
    records += rows("A000010", "consolidated", full, 100)
    records += rows("A000020", "separate", full, 200)
    # A000030 files a consolidated statement missing a core item.
    partial = [i for i in full if i != "sales"]
    records += rows("A000030", "consolidated", partial, 300)
    records += rows("A000030", "separate", full, 400)
    frame = pd.DataFrame.from_records(records)
    for scope, scope_group in frame.groupby("statement_scope"):
        for year, year_group in scope_group.groupby("fiscal_year"):
            directory = (
                root / f"statement_scope={scope}" / f"fiscal_year={year}"
            )
            directory.mkdir(parents=True, exist_ok=True)
            year_group.drop(columns=["statement_scope", "fiscal_year"]).to_parquet(
                directory / "data_0.parquet", index=False
            )


def _empty_side_inputs(tmp_path):
    shares = pd.DataFrame(
        {
            "ticker": ["A000010"],
            "base_date": [pd.Timestamp("2020-12-31")],
            "average_common_shares": [1_000.0],
        }
    )
    dividends = pd.DataFrame(
        {
            "ticker": ["A000010"],
            "fiscal_period": [pd.Timestamp("2020-12-01")],
            "cash_dividend_amount": [10.0],
        }
    )
    share_path = tmp_path / "shares.parquet"
    dividend_path = tmp_path / "dividends.parquet"
    shares.to_parquet(share_path, index=False)
    dividends.to_parquet(dividend_path, index=False)
    return share_path, dividend_path


def test_consolidated_only_default_drops_separate_filers(tmp_path) -> None:
    root = tmp_path / "facts"
    _write_statement_fixture(root)
    share_path, dividend_path = _empty_side_inputs(tmp_path)

    frame = load_ipca_annual_accounting(
        root, share_path, dividend_path, first_fiscal_year=2016
    )

    assert sorted(frame["ticker"]) == ["A000010", "A000030"]
    assert set(frame["statement_scope"]) == {"consolidated"}
    # The partial consolidated filer is kept, with its missing core item NaN.
    partial = frame.loc[frame["ticker"].eq("A000030")].iloc[0]
    assert np.isnan(partial["sales"])


def test_separate_fallback_adds_and_replaces_the_right_firm_years(tmp_path) -> None:
    root = tmp_path / "facts"
    _write_statement_fixture(root)
    share_path, dividend_path = _empty_side_inputs(tmp_path)

    with pytest.warns(MixedStatementScopeWarning, match="firm-years use separate"):
        frame = load_ipca_annual_accounting(
            root,
            share_path,
            dividend_path,
            first_fiscal_year=2016,
            allow_separate_fallback=True,
        )

    scope = frame.set_index("ticker")["statement_scope"].to_dict()
    # Complete consolidated wins; separate-only is added; incomplete
    # consolidated is replaced by a complete separate statement.
    assert scope == {
        "A000010": "consolidated",
        "A000020": "separate",
        "A000030": "separate",
    }
    assert frame["sales"].notna().all()


def test_separate_rows_carry_zero_minority_interest(tmp_path) -> None:
    root = tmp_path / "facts"
    _write_statement_fixture(root)
    share_path, dividend_path = _empty_side_inputs(tmp_path)

    with pytest.warns(MixedStatementScopeWarning):
        frame = load_ipca_annual_accounting(
            root,
            share_path,
            dividend_path,
            first_fiscal_year=2016,
            allow_separate_fallback=True,
        )

    by_ticker = frame.set_index("ticker")
    # A000020 is a separate filer: no minority interest, so book equity keeps
    # the full 200 (scaled to thousands).  A000010 is consolidated with every
    # item set to 100, so its minority interest nets book equity to zero.
    assert by_ticker.loc["A000020", "book_equity"] == pytest.approx(200 * 1_000.0)
    assert by_ticker.loc["A000010", "book_equity"] == pytest.approx(0.0)


def test_core_statement_items_are_the_scope_selection_gate() -> None:
    assert CORE_STATEMENT_ITEMS == (
        "total_assets",
        "total_equity",
        "sales",
        "net_income",
    )
    for item in CORE_STATEMENT_ITEMS:
        assert item in IPCA_ACCOUNT_CODES
        assert item in IPCA_SEPARATE_ACCOUNT_CODES
