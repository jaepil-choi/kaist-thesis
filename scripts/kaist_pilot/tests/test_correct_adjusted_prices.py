"""Synthetic checks for scripts/kaist_pilot/correct_adjusted_prices.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "correct_adjusted_prices.py"
spec = importlib.util.spec_from_file_location("correct_adjusted_prices", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _ticker(ticker, closes, bases, previous, factors, shares):
    days = pd.bdate_range("2026-01-05", periods=len(closes))
    frame = pd.DataFrame(
        {
            "date": days,
            "ticker": ticker,
            "기준가": np.asarray(bases, dtype=float),
            "시가": np.asarray(closes, dtype=float),
            "고가": np.asarray(closes, dtype=float),
            "저가": np.asarray(closes, dtype=float),
            "종가": np.asarray(closes, dtype=float),
            "전일종가": np.asarray(previous, dtype=float),
            "수정계수": np.asarray(factors, dtype=float),
            "유통주식수": np.asarray(shares, dtype=float),
        }
    )
    multiplier = module.future_adjustment_multiplier(frame["수정계수"])
    frame["adjustment_multiplier"] = multiplier
    for column, output in module.PRICE_COLUMNS.items():
        frame[output] = frame[column] / multiplier
    frame["return"] = frame["종가"] / frame["기준가"].where(frame["기준가"] > 0) - 1.0
    return frame


@pytest.fixture()
def prices():
    consolidation = _ticker(  # 1,500:1 consolidation the vendor never adjusted
        "CONS", [2080, 2080, 625000, 503000], [2080, 2080, 2080, 625000],
        [np.nan, 2080, 2080, 625000], [0, 1, 1, 1], [29_129_064, 29_129_064, 19_419, 19_419],
    )
    gap = _ticker(  # vendor factor 0 on a resumption row, previous close missing
        "GAP", [180, 178, 234, 168], [190, 180, 760, 234], [np.nan, 180, 0, 234], [0, 1, 0, 1], [4e7] * 4,
    )
    base_only = _ticker(  # base adjusted (ex-rights) but factor left at 1
        "BASE", [16000, 15980, 13230, 13300], [16000, 16000, 10180, 13230],
        [np.nan, 16000, 15980, 13230], [0, 1, 1, 1], [1e6, 1e6, 1.12e6, 1.12e6],
    )
    normal_split = _ticker(  # a vendor-adjusted 5:1 split: must stay as it is
        "SPLIT", [500000, 510000, 101000, 102000], [500000, 500000, 102000, 101000],
        [np.nan, 500000, 510000, 101000], [0, 1, 5, 1], [1e6, 1e6, 5e6, 5e6],
    )
    tick_rounded = _ticker(  # 5:1 split whose base the exchange rounded to the tick (368.4 -> 368)
        "TICK", [1800, 1842, 370, 372], [1800, 1800, 368, 370], [np.nan, 1800, 1842, 370], [0, 1, 5, 1],
        [1e6, 1e6, 5e6, 5e6],
    )
    merger_limit_down = _ticker(  # shares x5 on a -30% limit-down day (a merger): not a split
        "MERGE", [790, 790, 553, 560], [790, 790, 790, 553], [np.nan, 790, 790, 553], [0, 1, 1, 1],
        [2.8e7, 2.8e7, 1.4e8, 1.4e8],
    )
    return pd.concat(
        [consolidation, gap, base_only, normal_split, tick_rounded, merger_limit_down], ignore_index=True
    )


def test_unadjusted_consolidation_gets_ratio_factor_and_market_consistent_return(prices):
    after, audit = module.correct(prices)
    row = after[(after["ticker"] == "CONS") & (after["종가"] == 625000)].iloc[0]
    assert row["수정계수"] == pytest.approx(1 / 1500)
    assert row["기준가"] == pytest.approx(2080 * 1500)
    assert row["return"] == pytest.approx(625000 / 3_120_000 - 1)
    assert audit.loc[audit["ticker"] == "CONS", "rule"].tolist() == ["A"]


def test_zero_factor_gap_no_longer_zeroes_earlier_multipliers(prices):
    after, audit = module.correct(prices)
    gap = after[after["ticker"] == "GAP"]
    assert (gap["adjustment_multiplier"] > 0).all() and np.isfinite(gap["adj_close"]).all()
    resumed = gap.iloc[2]
    assert resumed["전일종가"] == 178 and resumed["수정계수"] == pytest.approx(178 / 760)
    assert resumed["return"] == prices.loc[resumed.name, "return"]  # vendor return kept
    assert audit.loc[audit["ticker"] == "GAP", "rule"].tolist() == ["B"]


def test_base_adjusted_factor_is_reconciled_and_return_kept(prices):
    after, audit = module.correct(prices)
    row = after[(after["ticker"] == "BASE") & (after["종가"] == 13230)].iloc[0]
    assert row["수정계수"] == pytest.approx(15980 / 10180)
    assert row["return"] == prices.loc[row.name, "return"]
    assert audit.loc[audit["ticker"] == "BASE", "rule"].tolist() == ["C"]


def test_vendor_adjusted_split_and_untouched_rows_are_identical(prices):
    after, audit = module.correct(prices)
    assert "SPLIT" not in set(audit["ticker"])
    split = prices["ticker"] == "SPLIT"
    pd.testing.assert_frame_equal(after[split], prices[split])


def test_limit_down_merger_with_more_shares_is_not_read_as_a_split(prices):
    after, audit = module.correct(prices)
    assert "MERGE" not in set(audit["ticker"])
    merge = prices["ticker"] == "MERGE"
    pd.testing.assert_frame_equal(after[merge], prices[merge])


def test_tick_rounded_base_keeps_the_true_split_factor(prices):
    after, audit = module.correct(prices)
    assert "TICK" not in set(audit["ticker"])
    tick = prices["ticker"] == "TICK"
    pd.testing.assert_frame_equal(after[tick], prices[tick])


def test_validate_passes_and_counts_rules(prices):
    after, audit = module.correct(prices)
    summary = module.validate(prices, after, audit)
    assert summary["corrected_rows_by_rule"] == {"A": 1, "B": 1, "C": 1}
    assert summary["returns_changed"] == 1


def test_non_integer_share_jump_beyond_the_limit_fails_closed(prices):
    odd = _ticker(
        "ODD", [1000, 1000, 4270], [1000, 1000, 1000], [np.nan, 1000, 1000], [0, 1, 1], [1e6, 1e6, 2.34e5],
    )
    with pytest.raises(ValueError, match="integer split ratio"):
        module.correct(pd.concat([prices, odd], ignore_index=True))
