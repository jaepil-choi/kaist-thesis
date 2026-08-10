"""Tests for the Figure 13 factor/residual decomposition."""

from __future__ import annotations

import numpy as np
import pandas as pd

from guijarro_ordonez_replication.risk_premium import (
    decompose_fama_french_stock_returns,
    fitted_factor_portfolio,
)


def test_decomposition_uses_negative_saved_factor_leg_as_beta() -> None:
    dates = pd.date_range("2020-01-01", periods=3)
    factors = pd.DataFrame(
        {
            "date": dates,
            "RMRF": [0.01, 0.02, -0.01],
            "SMB": 0.0,
            "HML": 0.0,
            "RMW": 0.0,
            "CMA": 0.0,
        }
    )
    stocks = pd.DataFrame({"date": dates, "ticker": "A", "return": [0.025, 0.045, -0.015]})
    legs = pd.DataFrame({"date": dates, "ticker": "A"})
    for factor in ("RMRF", "SMB", "HML", "RMW", "CMA"):
        legs[f"factor_asset_weight_{factor}"] = -2.0 if factor == "RMRF" else 0.0
    result = decompose_fama_french_stock_returns(stocks, factors, legs)
    np.testing.assert_allclose(result["systematic_return"], [0.02, 0.04, -0.02])
    np.testing.assert_allclose(result["residual_return"], [0.005, 0.005, 0.005])


def test_fitted_factor_portfolio_has_requested_gross_leverage() -> None:
    dates = pd.date_range("2020-01-01", periods=20)
    factors = pd.DataFrame({"date": dates})
    grid = np.linspace(-0.02, 0.02, len(dates))
    for index, factor in enumerate(("RMRF", "SMB", "HML", "RMW", "CMA"), start=1):
        factors[factor] = grid**index
    strategy = pd.DataFrame(
        {"date": dates, "return": factors[["RMRF", "SMB", "HML", "RMW", "CMA"]].sum(axis=1)}
    )
    _, audit = fitted_factor_portfolio(strategy, factors, leverage=1.65)
    assert np.isclose(audit["factor_portfolio_gross_leverage"], 1.65)
