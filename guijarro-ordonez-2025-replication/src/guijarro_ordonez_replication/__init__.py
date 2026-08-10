"""Core components for the Guijarro-Ordonez et al. replication."""

from .residuals import (
    map_residual_to_asset_weights,
    ols_residual_projection,
    project_residual_returns,
    residual_composition_matrix,
)

__all__ = [
    "map_residual_to_asset_weights",
    "ols_residual_projection",
    "project_residual_returns",
    "residual_composition_matrix",
]
