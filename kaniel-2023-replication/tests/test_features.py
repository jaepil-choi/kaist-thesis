import numpy as np
import pandas as pd

from kaniel_replication.features import (
    add_fund_momentum_features,
    compute_carhart_abnormal_returns,
)


def test_carhart_abnormal_return_uses_prior_window_betas() -> None:
    months = pd.date_range("2010-01-31", periods=40, freq="ME")
    mkt = np.linspace(-0.03, 0.04, len(months))
    factors = pd.DataFrame(
        {
            "month": months,
            "mkt_rf": mkt,
            "smb": 0.0,
            "hml": 0.0,
            "mom": 0.0,
            "rf": 0.001,
        }
    )
    panel = pd.DataFrame(
        {
            "fund_code": "A",
            "month": months,
            "monthly_return": 0.001 + 1.5 * mkt,
        }
    )
    result = compute_carhart_abnormal_returns(
        panel, factors, window=36, minimum_history=30
    )
    assert result["abnormal_return"].iloc[:30].isna().all()
    assert np.nanmax(np.abs(result["abnormal_return"].to_numpy())) < 1e-10


def test_fund_momentum_lags_do_not_use_future_returns() -> None:
    panel = pd.DataFrame(
        {
            "fund_code": ["A"] * 14,
            "month": pd.date_range("2020-01-31", periods=14, freq="ME"),
            "abnormal_return": np.arange(14, dtype=float),
        }
    )
    result = add_fund_momentum_features(panel, minimum_momentum_observations=8)
    assert result.loc[5, "F_ST_Rev"] == 5
    assert result.loc[5, "F_r2_1"] == 4
    assert pd.isna(result.loc[8, "F_r12_2"])
    assert result.loc[9, "F_r12_2"] == np.mean(np.arange(0, 8, dtype=float))
