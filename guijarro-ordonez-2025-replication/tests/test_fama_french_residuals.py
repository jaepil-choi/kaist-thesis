"""Tests for rolling Korean Fama-French residual construction."""

from __future__ import annotations

import numpy as np
import pandas as pd

from guijarro_ordonez_replication.characteristics import CHARACTERISTIC_COLUMNS
from guijarro_ordonez_replication.fama_french_residuals import (
    estimate_daily_fama_french_residuals,
)


def test_ff1_residual_and_factor_leg_match_no_intercept_regression() -> None:
    dates = pd.date_range("2020-01-01", periods=90, freq="B")
    tickers = ["A", "B", "C", "D"]
    factor = np.linspace(-0.02, 0.025, len(dates))
    betas = np.array([0.5, 0.8, 1.2, -0.3])
    daily = pd.DataFrame(
        [
            {"date": day, "ticker": ticker, "return": beta * factor[index]}
            for index, day in enumerate(dates)
            for ticker, beta in zip(tickers, betas, strict=True)
        ]
    )
    factors = pd.DataFrame({"date": dates, "RMRF": factor})
    monthly_rows = []
    for month in pd.date_range("2019-12-31", "2020-05-31", freq="ME"):
        for ticker in tickers:
            row = {
                "date": month,
                "ticker": ticker,
                "return": 0.01,
                "market_cap": 100.0,
            }
            row.update(dict.fromkeys(CHARACTERISTIC_COLUMNS, 1.0))
            monthly_rows.append(row)
    monthly = pd.DataFrame(monthly_rows)
    result = estimate_daily_fama_french_residuals(
        monthly,
        daily,
        factors,
        n_factors=1,
        initial_oos_date=dates[60],
        loading_window_days=60,
    )
    first_residual = result.residuals.loc[
        result.residuals["date"].eq(dates[60]), "residual"
    ]
    np.testing.assert_allclose(first_residual, 0, atol=1e-12)
    first_legs = result.factor_legs.loc[
        result.factor_legs["date"].eq(dates[60]), "factor_asset_weight_RMRF"
    ]
    np.testing.assert_allclose(first_legs, -betas, atol=1e-12)
    assert result.audit["fit_intercept"] is False
