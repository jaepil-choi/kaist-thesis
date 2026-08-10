import numpy as np
import pandas as pd
import pytest

from guijarro_ordonez_replication.characteristics import CHARACTERISTIC_COLUMNS
from guijarro_ordonez_replication.ipca import (
    _gamma_step,
    ShortHistoryIPCAWarning,
    estimate_daily_ipca_residuals,
    fit_ipca_als,
    validate_ipca_window,
)


def test_gamma_step_matches_explicit_design_matrix() -> None:
    returns = (np.array([0.01, -0.02, 0.03]),)
    characteristics = (
        np.array([[0.5, -0.5], [0.0, 0.5], [-0.5, 0.0]]),
    )
    factors = (np.array([0.2, -0.1]),)
    design = np.kron(characteristics[0], factors[0].reshape(1, -1))
    expected = (np.linalg.pinv(design.T @ design) @ design.T @ returns[0]).reshape(
        2, 2
    )

    actual = _gamma_step(
        returns,
        characteristics,
        factors,
        n_characteristics=2,
        n_factors=2,
    )

    np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_exact_window_rejects_insufficient_history() -> None:
    with pytest.raises(ValueError, match="240 training months"):
        validate_ipca_window(100)


def test_short_history_requires_explicit_opt_in_and_warns() -> None:
    with pytest.raises(ValueError, match="allow_short_history"):
        validate_ipca_window(60, window_months=60)

    with pytest.warns(ShortHistoryIPCAWarning):
        assert validate_ipca_window(
            60, window_months=60, allow_short_history=True
        ) == 60


def test_ipca_als_fits_finite_characteristic_factor_system() -> None:
    rng = np.random.default_rng(2025)
    true_gamma = np.array([[1.0], [0.5], [-0.25]])
    returns = []
    characteristics = []
    for month in range(12):
        z = rng.normal(size=(20, 3))
        factor = np.array([0.01 + month * 0.0005])
        ret = (z @ true_gamma @ factor).ravel()
        characteristics.append(z)
        returns.append(ret)

    fit = fit_ipca_als(
        tuple(returns),
        tuple(characteristics),
        n_factors=1,
        max_iterations=50,
        tolerance=1e-8,
    )

    assert fit.gamma.shape == (3, 1)
    assert np.isfinite(fit.gamma).all()
    fitted = [z @ fit.gamma @ factor for z, factor in zip(characteristics, fit.factors)]
    error = np.concatenate([ret - value.ravel() for ret, value in zip(returns, fitted)])
    assert np.sqrt(np.mean(error**2)) < 1e-7
    assert np.isfinite(fit.final_delta)


def test_daily_ipca_uses_prior_month_characteristics() -> None:
    rng = np.random.default_rng(7)
    tickers = [f"A{i}" for i in range(6)]
    months = pd.date_range("2020-01-31", periods=5, freq="ME")
    monthly_rows = []
    daily_rows = []
    for month_index, month in enumerate(months):
        for ticker_index, ticker in enumerate(tickers):
            chars = rng.normal(size=len(CHARACTERISTIC_COLUMNS))
            monthly_rows.append(
                {
                    "date": month,
                    "ticker": ticker,
                    "return": 0.01 * (ticker_index - 2),
                    "market_cap": 100.0 + ticker_index,
                    **dict(zip(CHARACTERISTIC_COLUMNS, chars, strict=True)),
                }
            )
        if month_index > 0:
            for day in pd.bdate_range(months[month_index - 1] + pd.Timedelta(days=1), month):
                for ticker_index, ticker in enumerate(tickers):
                    daily_rows.append(
                        {
                            "date": day,
                            "ticker": ticker,
                            "return": 0.001 * (ticker_index - 2),
                        }
                    )

    with pytest.warns(ShortHistoryIPCAWarning):
        result = estimate_daily_ipca_residuals(
            pd.DataFrame(monthly_rows),
            pd.DataFrame(daily_rows),
            n_factors=1,
            window_months=2,
            reestimate_every_months=1,
            allow_short_history=True,
            max_iterations=5,
            require_convergence=False,
        )

    assert not result.residuals.empty
    assert result.residuals.duplicated(["date", "ticker"]).sum() == 0
    assert result.audit["window_months"] == 2
    assert result.audit["classification"] == "Korean short-history IPCA sensitivity"
