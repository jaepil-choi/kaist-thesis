"""Tests for paper-compatible empirical statistics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from guijarro_ordonez_replication.results import (
    _strategy_group,
    factor_alpha,
    performance_statistics,
)


def test_performance_statistics_match_public_ddof_zero_contract() -> None:
    returns = np.array([0.01, -0.005, 0.007, 0.002])
    result = performance_statistics(returns)
    assert result["annual_return"] == pytest.approx(returns.mean() * 252)
    assert result["annual_volatility"] == pytest.approx(
        returns.std(ddof=0) * np.sqrt(252)
    )


def test_factor_alpha_recovers_known_intercept() -> None:
    dates = pd.date_range("2020-01-01", periods=40, freq="B")
    factor = np.linspace(-0.01, 0.01, len(dates))
    strategy = pd.DataFrame({"date": dates, "return": 0.001 + 0.5 * factor})
    factors = pd.DataFrame({"date": dates, "RMRF": factor})
    result = factor_alpha(strategy, factors, ["RMRF"])
    assert result["annual_alpha"] == pytest.approx(0.252)
    assert result["observations"] == 40


def test_numbered_table_grouping_keeps_friction_runs_separate() -> None:
    base = {
        "epochs": 100,
        "holding_days": 1,
        "model": "cnn_transformer",
        "objective": "sharpe",
        "lookback_days": 30,
        "rolling_retrain": True,
        "transaction_cost": 0.0,
        "short_holding_cost": 0.0,
    }
    assert _strategy_group(base) == "sharpe"
    friction = {
        **base,
        "model": "cnn_transformer_frictions",
        "transaction_cost": 0.0005,
        "short_holding_cost": 0.0001,
    }
    assert _strategy_group(friction) == "frictions"
    assert _strategy_group({**base, "lookback_days": 60}) == "lookback60"
    assert _strategy_group({**base, "rolling_retrain": False}) == "constant"
