"""Tests for rolling statistical-arbitrage preprocessing and accounting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch

from guijarro_ordonez_replication.trading import (
    ResidualPanel,
    SimulationConfig,
    annualized_statistics,
    cumulative_windows,
    factor_leg_asset_weights,
    identity_return_panel,
    low_rank_asset_weights,
    packed_fourier_windows,
    simulate_rolling_strategy,
)


def test_cumulative_windows_are_backward_looking() -> None:
    residuals = np.arange(1, 13, dtype=float).reshape(6, 2)
    observed = np.ones_like(residuals, dtype=bool)
    windows, selected = cumulative_windows(residuals, observed, lookback=3)
    np.testing.assert_allclose(windows[0, 0], [1, 4, 9])
    np.testing.assert_allclose(windows[1, 0], [3, 8, 15])
    assert selected.all()


def test_zero_residual_marks_window_unavailable_like_public_code() -> None:
    residuals = np.ones((5, 2))
    residuals[1, 0] = 0
    windows, selected = cumulative_windows(
        residuals, np.ones_like(residuals, dtype=bool), lookback=3
    )
    assert not selected[0, 0]
    assert selected[0, 1]
    assert np.count_nonzero(windows[0, 0]) == 0


def test_fourier_packing_matches_public_layout() -> None:
    cumulative = np.arange(30, dtype=np.float32).reshape(1, 1, 30)
    packed = packed_fourier_windows(cumulative)
    coefficients = np.fft.rfft(cumulative, axis=-1)
    np.testing.assert_allclose(packed[..., :16], coefficients.real, rtol=1e-6)
    np.testing.assert_allclose(packed[..., 16:], coefficients[..., 1:-1].imag, rtol=1e-6)


def test_identity_return_panel_uses_reference_universe_and_zero_composition() -> None:
    dates = pd.date_range("2020-01-01", periods=3)
    reference = ResidualPanel(
        dates=dates,
        tickers=("A", "B"),
        residuals=np.zeros((3, 2)),
        left=np.ones((3, 2, 1)),
        right=np.ones((3, 2, 1)),
        observed=np.array([[True, True], [True, False], [True, True]]),
    )
    daily = pd.DataFrame(
        {
            "date": [*dates, *dates],
            "ticker": ["A"] * 3 + ["B"] * 3,
            "return": [0.01, 0.02, 0.03, -0.01, -0.02, -0.03],
        }
    )
    panel = identity_return_panel(reference, daily)
    np.testing.assert_allclose(panel.residuals, [[0.01, -0.01], [0.02, 0], [0.03, -0.03]])
    assert not panel.observed[1, 1]
    assert np.count_nonzero(panel.left) == 0
    assert np.count_nonzero(panel.right) == 0


def test_low_rank_mapping_matches_dense_composition() -> None:
    residual_weights = torch.tensor([[0.7, -0.2, 0.4]])
    left = torch.tensor([[[0.2], [0.4], [-0.1]]])
    right = torch.tensor([[[0.3], [-0.2], [0.5]]])
    normalized_residual, asset = low_rank_asset_weights(
        residual_weights, left, right
    )
    dense = torch.eye(3) - left[0] @ right[0].T
    expected_raw = residual_weights @ dense
    expected_gross = expected_raw.abs().sum()
    torch.testing.assert_close(asset, expected_raw / expected_gross)
    torch.testing.assert_close(normalized_residual, residual_weights / expected_gross)
    torch.testing.assert_close(asset.abs().sum(dim=1), torch.ones(1))


def test_factor_leg_mapping_adds_synthetic_hedges() -> None:
    residual = torch.tensor([[0.6, -0.4]])
    negative_betas = torch.tensor([[[-1.0], [-0.5]]])
    normalized, assets = factor_leg_asset_weights(residual, negative_betas)
    expected = torch.tensor([[0.6, -0.4, -0.4]])
    gross = expected.abs().sum()
    torch.testing.assert_close(assets, expected / gross)
    torch.testing.assert_close(normalized, residual / gross)


def test_annualized_statistics_use_252_days() -> None:
    values = torch.tensor([0.01, -0.005, 0.007])
    mean, volatility, sharpe = annualized_statistics(values)
    torch.testing.assert_close(mean, values.mean() * 252)
    torch.testing.assert_close(volatility, values.std() * np.sqrt(252))
    torch.testing.assert_close(sharpe, mean / (volatility + 1e-8))


def test_ou_rolling_simulation_is_strictly_oos() -> None:
    dates = pd.date_range("2020-01-01", periods=14, freq="B")
    residuals = np.column_stack(
        [
            np.sin(np.arange(14)) * 0.01 + 0.001,
            np.cos(np.arange(14)) * 0.01 + 0.001,
        ]
    )
    panel = ResidualPanel(
        dates=dates,
        tickers=("A", "B"),
        residuals=residuals,
        left=np.zeros((14, 2, 1)),
        right=np.zeros((14, 2, 1)),
        observed=np.ones((14, 2), dtype=bool),
    )
    config = SimulationConfig(
        model_name="ou_threshold",
        lookback_days=3,
        training_window_days=8,
        stride_days=2,
        epochs=1,
        batch_days=2,
    )
    result = simulate_rolling_strategy(panel, config)
    assert result.daily["date"].iloc[0] == dates[8]
    assert len(result.daily) == 6
    assert result.audit["subperiods"] == 3
    assert np.isfinite(result.daily.drop(columns="date").to_numpy()).all()


def test_config_rejects_nonpositive_holding_period() -> None:
    with pytest.raises(ValueError, match="positive"):
        SimulationConfig(holding_days=0).validate()


def test_multiday_holding_path_keeps_public_leading_zeros() -> None:
    dates = pd.date_range("2020-01-01", periods=14, freq="B")
    residuals = np.column_stack(
        [np.sin(np.arange(14)) * 0.01 + 0.001, np.cos(np.arange(14)) * 0.01 + 0.001]
    )
    panel = ResidualPanel(
        dates=dates,
        tickers=("A", "B"),
        residuals=residuals,
        left=np.zeros((14, 2, 1)),
        right=np.zeros((14, 2, 1)),
        observed=np.ones((14, 2), dtype=bool),
    )
    result = simulate_rolling_strategy(
        panel,
        SimulationConfig(
            model_name="ou_threshold",
            lookback_days=3,
            training_window_days=8,
            stride_days=6,
            epochs=1,
            batch_days=2,
            holding_days=3,
        ),
    )
    np.testing.assert_allclose(result.daily["return"].iloc[:3], 0)
    identity_return_panel,
