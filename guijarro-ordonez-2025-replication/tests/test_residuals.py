import numpy as np
import pytest

from guijarro_ordonez_replication.residuals import (
    map_residual_to_asset_weights,
    ols_residual_projection,
    project_residual_returns,
    residual_composition_matrix,
)


def test_four_stock_factor_mimicking_portfolios() -> None:
    loadings = np.array([[1.2], [0.8], [1.0], [1.0]])
    factor_weights = np.full((4, 1), 0.25)

    composition = residual_composition_matrix(loadings, factor_weights)

    np.testing.assert_allclose(
        composition,
        np.array(
            [
                [0.70, -0.30, -0.30, -0.30],
                [-0.20, 0.80, -0.20, -0.20],
                [-0.25, -0.25, 0.75, -0.25],
                [-0.25, -0.25, -0.25, 0.75],
            ]
        ),
    )
    np.testing.assert_allclose(composition @ loadings, 0.0, atol=1e-12)


def test_residual_returns_and_asset_weight_netting() -> None:
    composition = np.array(
        [
            [0.70, -0.30, -0.30, -0.30],
            [-0.20, 0.80, -0.20, -0.20],
            [-0.25, -0.25, 0.75, -0.25],
            [-0.25, -0.25, -0.25, 0.75],
        ]
    )
    returns = np.array([0.020, 0.008, 0.014, 0.006])
    residual_weights = np.array([0.4, -0.2, 0.0, 0.6])

    np.testing.assert_allclose(
        project_residual_returns(returns, composition),
        composition @ returns,
    )
    raw_weights = map_residual_to_asset_weights(
        residual_weights, composition, normalize_gross=False
    )
    np.testing.assert_allclose(raw_weights, [0.17, -0.43, -0.23, 0.37])
    normalized = map_residual_to_asset_weights(residual_weights, composition)
    np.testing.assert_allclose(np.abs(normalized).sum(), 1.0)
    np.testing.assert_allclose(normalized, raw_weights / 1.2)


def test_ols_projection_annihilates_factor_loadings() -> None:
    loadings = np.array(
        [
            [1.0, 0.5],
            [0.7, 0.8],
            [1.3, 0.2],
            [1.0, 0.5],
        ]
    )

    composition = ols_residual_projection(loadings)

    np.testing.assert_allclose(composition, composition.T, atol=1e-12)
    np.testing.assert_allclose(composition @ composition, composition, atol=1e-12)
    np.testing.assert_allclose(composition @ loadings, 0.0, atol=1e-12)


def test_zero_gross_weight_normalization_fails() -> None:
    with pytest.raises(ValueError, match="zero-gross"):
        map_residual_to_asset_weights(np.zeros(2), np.eye(2))
