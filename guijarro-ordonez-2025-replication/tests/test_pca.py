import numpy as np
import pandas as pd

from guijarro_ordonez_replication.characteristics import CHARACTERISTIC_COLUMNS
from guijarro_ordonez_replication.pca import (
    estimate_daily_pca_residuals,
    pca_residual_step,
)


def test_pca_low_rank_composition_reconstructs_residual() -> None:
    rng = np.random.default_rng(2025)
    returns = rng.normal(scale=0.01, size=(12, 6))

    step = pca_residual_step(
        returns,
        n_factors=2,
        loading_window_days=5,
    )

    composition = (
        np.eye(returns.shape[1])
        - step.standardized_eigenvectors @ step.return_loadings.T
    )
    np.testing.assert_allclose(step.residual, returns[-1] @ composition, atol=1e-12)


def test_daily_pca_uses_prior_month_universe() -> None:
    rng = np.random.default_rng(11)
    tickers = [f"A{i}" for i in range(8)]
    monthly_rows = []
    for month in pd.to_datetime(["2020-01-31", "2020-02-29"]):
        for ticker_index, ticker in enumerate(tickers):
            monthly_rows.append(
                {
                    "date": month,
                    "ticker": ticker,
                    "return": 0.01 * (ticker_index - 3),
                    "market_cap": 100.0 + ticker_index,
                    **dict.fromkeys(CHARACTERISTIC_COLUMNS, 0.0),
                }
            )
    daily_rows = []
    dates = pd.bdate_range("2020-01-27", periods=10)
    for day_index, day in enumerate(dates):
        for ticker_index, ticker in enumerate(tickers):
            daily_rows.append(
                {
                    "date": day,
                    "ticker": ticker,
                    "return": rng.normal(scale=0.01)
                    + 0.0001 * day_index * ticker_index,
                }
            )

    result = estimate_daily_pca_residuals(
        pd.DataFrame(monthly_rows),
        pd.DataFrame(daily_rows),
        n_factors=2,
        initial_oos_date=dates[5],
        covariance_window_days=4,
        loading_window_days=2,
        max_oos_days=2,
    )

    assert result.audit["completed_days"] == 2
    assert result.audit["current_day_in_covariance_and_loading_windows"] is True
    assert result.residuals["ticker"].nunique() == len(tickers)
    assert result.loadings.duplicated(["date", "ticker"]).sum() == 0
