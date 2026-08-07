import numpy as np
import pandas as pd

from kaniel_replication.model import (
    assign_month_folds,
    cross_sectional_rank_normalize,
    fit_cross_oos_mlp,
    form_prediction_portfolios,
)


def test_rank_normalization_and_fold_assignment_are_deterministic() -> None:
    values = pd.Series([10.0, 20.0, 30.0])
    assert np.allclose(cross_sectional_rank_normalize(values), [-0.5, 0.0, 0.5])
    months = pd.date_range("2020-01-31", periods=12, freq="ME")
    first = assign_month_folds(months, scheme="random", random_seed=7)
    second = assign_month_folds(months, scheme="random", random_seed=7)
    pd.testing.assert_frame_equal(first, second)
    assert set(first["fold"]) == {0, 1, 2}


def test_cross_oos_predictions_and_extreme_portfolios() -> None:
    months = pd.date_range("2020-01-31", periods=9, freq="ME")
    rows = []
    for month_number, month in enumerate(months):
        for fund_number in range(20):
            flow = (fund_number - 10) / 20
            momentum = month_number / 20
            rows.append(
                {
                    "fund_code": f"F{fund_number:02d}",
                    "month": month,
                    "rank_flow": flow,
                    "rank_F_r12_2": momentum,
                    "sentiment": (-1) ** month_number * 0.2,
                    "target_abnormal_return": 0.03 * flow + 0.02 * momentum,
                }
            )
    sample = pd.DataFrame(rows)
    predicted = fit_cross_oos_mlp(
        sample,
        feature_columns=["rank_flow", "rank_F_r12_2", "sentiment"],
        ensemble_size=1,
        hidden_units=4,
        max_iter=80,
        random_seed=11,
    )
    assert predicted["prediction"].notna().all()
    assert predicted["fold"].notna().all()
    portfolios = form_prediction_portfolios(predicted)
    assert len(portfolios) == len(months)
    assert portfolios["long_short_prediction"].notna().all()
    assert portfolios["long_short_forecast"].notna().all()
