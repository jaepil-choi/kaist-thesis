import numpy as np
import pandas as pd

from kaniel_replication.proxy_outputs import (
    build_us_korea_comparison,
    compute_table_7_summary,
)


def test_table_7_summary_matches_paper_metrics() -> None:
    portfolios = pd.DataFrame(
        {
            "top_prediction": [0.03, 0.01, 0.02],
            "bottom_prediction": [-0.01, -0.02, 0.00],
            "long_short_prediction": [0.04, 0.03, 0.02],
            "top_forecast": [0.025, 0.015, 0.020],
            "bottom_forecast": [-0.005, -0.015, -0.005],
            "long_short_forecast": [0.030, 0.030, 0.025],
        }
    )
    summary = compute_table_7_summary(portfolios).set_index("portfolio")
    assert np.isclose(summary.loc["Long-short", "mean_percent"], 3.0)
    assert summary.loc["Long-short", "months"] == 3
    assert np.isfinite(summary.loc["Long-short", "rf2_percent"])

    comparison = build_us_korea_comparison(summary.reset_index())
    published = comparison.loc[
        comparison["market"].eq("United States (published)")
        & comparison["portfolio"].eq("Long-short")
    ].iloc[0]
    assert published["mean_percent"] == 0.40
    assert published["t_stat"] == 5.4
