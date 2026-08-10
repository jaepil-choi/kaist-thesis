"""Tests for Appendix C.1 model-selection contracts."""

from __future__ import annotations

import numpy as np
import pandas as pd

from guijarro_ordonez_replication.model_selection import (
    ALTERNATIVE_NETWORKS,
    VALIDATION_GRID,
    slice_panel,
)
from guijarro_ordonez_replication.trading import ResidualPanel


def test_public_validation_grid_has_sixteen_candidates() -> None:
    assert len(VALIDATION_GRID) == 16
    assert len(ALTERNATIVE_NETWORKS) == 5
    assert {spec.filters[-1] for spec in VALIDATION_GRID} == {8, 16}
    assert {spec.attention_heads for spec in VALIDATION_GRID} == {2, 4}
    assert {spec.hidden_units_factor for spec in VALIDATION_GRID} == {2, 3}
    assert {spec.dropout for spec in VALIDATION_GRID} == {0.25, 0.5}


def test_slice_panel_preserves_coordinates() -> None:
    panel = ResidualPanel(
        dates=pd.date_range("2020-01-01", periods=5),
        tickers=("A", "B"),
        residuals=np.ones((5, 2)),
        left=np.ones((5, 2, 1)),
        right=np.ones((5, 2, 1)),
        observed=np.ones((5, 2), dtype=bool),
    )
    sliced = slice_panel(panel, 3)
    assert len(sliced.dates) == 3
    assert sliced.tickers == panel.tickers
    assert sliced.residuals.shape == (3, 2)
