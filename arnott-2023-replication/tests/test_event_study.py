import numpy as np
import pandas as pd

from arnott_replication.event_study import (
    compute_event_paths,
    compute_event_window_returns,
    summarize_event_windows,
)


def _fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2024-01-02", periods=12, freq="B")
    levels = pd.DataFrame(
        {"VALUE_DATE": dates, "VALUE": 100 * np.cumprod(np.repeat(1.01, len(dates)))}
    )
    prices = pd.concat(
        [
            pd.DataFrame({"date": dates, "ticker": "ADD", "return": 0.02}),
            pd.DataFrame({"date": dates, "ticker": "DEL", "return": 0.00}),
        ],
        ignore_index=True,
    )
    events = pd.DataFrame(
        {
            "event_id": ["E", "E"],
            "effective_date": [dates[5], dates[5]],
            "action": ["addition", "deletion"],
            "ticker": ["ADD", "DEL"],
        }
    )
    return events, prices, levels


def test_event_window_returns_compound_relative_to_index() -> None:
    events, prices, levels = _fixture()
    result = compute_event_window_returns(
        events,
        prices,
        levels,
        [{"label": "post", "start": 1, "end": 2}],
        minimum_coverage=1.0,
    )
    addition = result.loc[result["action"].eq("addition"), "market_adjusted_return"].iloc[0]
    deletion = result.loc[result["action"].eq("deletion"), "market_adjusted_return"].iloc[0]
    assert np.isclose(addition, (1.02**2) / (1.01**2) - 1)
    assert np.isclose(deletion, 1 / (1.01**2) - 1)
    summary = summarize_event_windows(result)
    assert np.isclose(
        summary.loc[0, "deletion_minus_addition"], deletion - addition
    )
    assert summary.loc[0, "event_group_n"] == 1
    assert np.isnan(summary.loc[0, "event_clustered_t_stat"])


def test_event_paths_preserve_both_actions() -> None:
    events, prices, levels = _fixture()
    paths = compute_event_paths(
        events,
        prices,
        levels,
        minimum_offset=-2,
        maximum_offset=2,
        minimum_coverage=1.0,
    )
    assert list(paths["offset"]) == [-2, -1, 0, 1, 2]
    assert paths[["addition_mean", "deletion_mean"]].notna().all().all()
