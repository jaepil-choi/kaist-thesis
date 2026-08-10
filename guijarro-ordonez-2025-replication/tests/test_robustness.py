"""Tests for sparse and holding-period robustness calculations."""

from __future__ import annotations

import pandas as pd

from guijarro_ordonez_replication.robustness import (
    holding_period_returns,
    sparse_weight_returns,
)


def test_sparse_weights_are_renormalized_before_returns() -> None:
    dates = pd.date_range("2020-01-01", periods=2)
    weights = pd.DataFrame([[0.6, -0.3, 0.1], [0.2, -0.7, 0.1]], index=dates)
    returns = pd.DataFrame([[0.01, 0.02, 0.03], [0.04, 0.01, -0.02]], index=dates)
    result = sparse_weight_returns(weights, returns, percentiles=(0.2,))
    assert result.iloc[0, 0] == 0.01
    assert result.iloc[1, 0] == -0.01


def test_holding_period_return_uses_original_weight_for_b_days() -> None:
    dates = pd.date_range("2020-01-01", periods=4)
    weights = pd.DataFrame([[1.0], [1.0], [1.0], [1.0]], index=dates, columns=["A"])
    returns = pd.DataFrame([[0.01], [0.02], [0.03], [0.04]], index=dates, columns=["A"])
    result = holding_period_returns(weights, returns, holding_days=(2,))
    assert result.iloc[0, 0] == 0
    assert result.iloc[1, 0] == 0
    assert result.iloc[2, 0] == ((1.02 * 1.03) - 1) / 2
