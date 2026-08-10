"""Tests for appendix portfolio construction."""

from __future__ import annotations

import numpy as np
import pandas as pd

from guijarro_ordonez_replication.appendix_outputs import (
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
