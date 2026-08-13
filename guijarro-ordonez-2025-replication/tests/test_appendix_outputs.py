"""Tests for appendix portfolio construction."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from guijarro_ordonez_replication.appendix_outputs import (
    _is_benchmark_cnn,
    unconditional_average_residual_returns,
)
from guijarro_ordonez_replication.trading import ResidualPanel


def test_unconditional_average_residual_has_unit_identity_gross() -> None:
    panel = ResidualPanel(
        dates=pd.date_range("2020-01-01", periods=3),
        tickers=("A", "B"),
        residuals=np.array([[0.01, 0.03], [0.02, -0.01], [0.04, 0.02]]),
        left=np.zeros((3, 2, 1)),
        right=np.zeros((3, 2, 1)),
        observed=np.ones((3, 2), dtype=bool),
    )
    result = unconditional_average_residual_returns(panel, start_index=0)
    np.testing.assert_allclose(result["return"], [0.02, 0.005, 0.03])


def test_unconditional_average_ff_includes_synthetic_factor_gross() -> None:
    panel = ResidualPanel(
        dates=pd.date_range("2020-01-01", periods=1),
        tickers=("A", "B"),
        residuals=np.array([[0.01, 0.03]]),
        left=np.zeros((1, 2, 1)),
        right=np.zeros((1, 2, 1)),
        observed=np.ones((1, 2), dtype=bool),
        extra_asset_loadings=np.array([[[0.5], [-0.25]]]),
        asset_tickers=("A", "B", "FACTOR::RM"),
    )
    result = unconditional_average_residual_returns(panel, start_index=0)
    # Equal residual weights imply stock gross 1 and factor-leg gross 0.125.
    assert result.loc[0, "return"] == pytest.approx(0.02 / 1.125)


def test_benchmark_cnn_filter_excludes_robustness_variants() -> None:
    baseline = {
        "model": "cnn_transformer",
        "objective": "sharpe",
        "lookback_days": 30,
        "training_window_days": 1000,
        "rolling_retrain": True,
        "holding_days": 1,
        "transaction_cost": 0.0,
        "short_holding_cost": 0.0,
    }

    assert _is_benchmark_cnn(baseline)
    assert not _is_benchmark_cnn({**baseline, "lookback_days": 60})
    assert not _is_benchmark_cnn({**baseline, "rolling_retrain": False})
    assert not _is_benchmark_cnn({**baseline, "holding_days": 5})
    assert not _is_benchmark_cnn({**baseline, "transaction_cost": 0.0005})
