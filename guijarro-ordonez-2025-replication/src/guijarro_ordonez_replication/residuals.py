"""Residual-portfolio construction from equations (1) and (3) of the paper."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]


def _finite_matrix(values: ArrayLike, *, name: str) -> FloatArray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2:
        raise ValueError(f"{name} must be two-dimensional")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} must contain only finite values")
    return matrix


def residual_composition_matrix(
    loadings: ArrayLike,
    factor_weights: ArrayLike,
) -> FloatArray:
    """Return Phi = I - beta W_F.T for traded factor-mimicking portfolios.

    ``loadings`` and ``factor_weights`` both have shape ``(n_assets, n_factors)``.
    Row ``n`` of the returned matrix contains the asset weights of residual
    portfolio ``n``.
    """

    beta = _finite_matrix(loadings, name="loadings")
    weights = _finite_matrix(factor_weights, name="factor_weights")
    if beta.shape != weights.shape:
        raise ValueError(
            "loadings and factor_weights must have the same "
            "(n_assets, n_factors) shape"
        )
    n_assets = beta.shape[0]
    return np.eye(n_assets, dtype=float) - beta @ weights.T


def ols_residual_projection(loadings: ArrayLike) -> FloatArray:
    """Return the OLS residual-maker I - beta pinv(beta).

    This is the IPCA-style cross-sectional projection used by the authors'
    reference implementation. ``pinv`` also gives a defined result when the
    loading matrix is not full column rank.
    """

    beta = _finite_matrix(loadings, name="loadings")
    return np.eye(beta.shape[0], dtype=float) - beta @ np.linalg.pinv(beta)


def project_residual_returns(
    asset_returns: ArrayLike,
    composition: ArrayLike,
) -> FloatArray:
    """Map asset returns into residual returns.

    A one-dimensional input is treated as one date. A two-dimensional input
    must have shape ``(n_dates, n_assets)``.
    """

    phi = _finite_matrix(composition, name="composition")
    if phi.shape[0] != phi.shape[1]:
        raise ValueError("composition must be square")

    returns = np.asarray(asset_returns, dtype=float)
    if not np.isfinite(returns).all():
        raise ValueError("asset_returns must contain only finite values")
    if returns.ndim == 1:
        if returns.shape[0] != phi.shape[1]:
            raise ValueError("asset_returns length does not match composition")
        return phi @ returns
    if returns.ndim == 2:
        if returns.shape[1] != phi.shape[1]:
            raise ValueError("asset_returns width does not match composition")
        return returns @ phi.T
    raise ValueError("asset_returns must be one- or two-dimensional")


def map_residual_to_asset_weights(
    residual_weights: ArrayLike,
    composition: ArrayLike,
    *,
    normalize_gross: bool = True,
) -> FloatArray:
    """Map residual allocations to executable asset weights.

    Implements ``w_R = w_epsilon.T Phi`` and, by default, the paper's
    L1-normalization so that gross asset exposure equals one.
    """

    phi = _finite_matrix(composition, name="composition")
    if phi.shape[0] != phi.shape[1]:
        raise ValueError("composition must be square")
    weights = np.asarray(residual_weights, dtype=float)
    if weights.ndim != 1 or weights.shape[0] != phi.shape[0]:
        raise ValueError("residual_weights must match the number of residuals")
    if not np.isfinite(weights).all():
        raise ValueError("residual_weights must contain only finite values")

    asset_weights = weights @ phi
    if not normalize_gross:
        return asset_weights
    gross = np.abs(asset_weights).sum()
    if gross <= np.finfo(float).eps:
        raise ValueError("cannot normalize a zero-gross asset portfolio")
    return asset_weights / gross
