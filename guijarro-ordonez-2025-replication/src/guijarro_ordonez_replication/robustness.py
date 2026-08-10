"""Strategy robustness outputs corresponding to paper Figures 9-12."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .results import performance_statistics
from .trading import ResidualPanel, cumulative_windows


def sparse_weight_returns(
    weights: pd.DataFrame,
    asset_returns: pd.DataFrame,
    percentiles: tuple[float, ...] = (1.0, 0.2, 0.1, 0.05, 0.01),
) -> pd.DataFrame:
    """Keep the largest absolute underlying weights and restore unit gross."""

    aligned_returns = asset_returns.reindex(index=weights.index, columns=weights.columns)
    if aligned_returns.isna().any().any():
        raise ValueError("asset returns do not fully cover strategy weight coordinates")
    raw = weights.to_numpy(float)
    returns = aligned_returns.to_numpy(float)
    output: dict[str, np.ndarray] = {}
    for percentile in percentiles:
        sparse = np.zeros_like(raw)
        for time_index, row in enumerate(raw):
            available = np.flatnonzero(row != 0)
            if len(available) == 0:
                continue
            keep = max(1, int(percentile * len(available)))
            selected = available[
                np.argpartition(np.abs(row[available]), -keep)[-keep:]
            ]
            sparse[time_index, selected] = row[selected]
            gross = np.abs(sparse[time_index]).sum()
            if gross > 0:
                sparse[time_index] /= gross
        output[f"p{percentile:g}"] = (sparse * returns).sum(axis=1)
    frame = pd.DataFrame(output, index=weights.index)
    frame.index.name = "date"
    return frame


def naive_reversal_returns(
    panel: ResidualPanel,
    *,
    offset_days: int = 1000,
    lookback_days: int = 30,
    percentile: float = 0.2,
    lags: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 22, 30),
) -> pd.DataFrame:
    """Trade the opposite of top-minus-bottom cumulative-residual ranks."""

    if panel.extra_asset_loadings is not None:
        raise ValueError("naive reversal currently requires PCA low-rank composition")
    windows, selected = cumulative_windows(
        panel.residuals, panel.observed, lookback_days
    )
    output = np.zeros((len(panel.dates) - offset_days, len(lags)), dtype=float)
    for day_index in range(offset_days, len(panel.dates)):
        window_index = day_index - lookback_days
        valid = selected[window_index]
        number = int(valid.sum())
        keep = int(percentile * number)
        if keep <= 0:
            continue
        valid_indices = np.flatnonzero(valid)
        for lag_index, lag in enumerate(lags):
            signal = windows[window_index, valid, -lag]
            high = np.argpartition(signal, -keep)[-keep:]
            low = np.argpartition(signal, keep)[:keep]
            residual_weight = np.zeros(len(panel.tickers), dtype=float)
            # Reversal: long low cumulative residuals and short high residuals.
            residual_weight[valid_indices[low]] = 1 / (2 * keep)
            residual_weight[valid_indices[high]] = -1 / (2 * keep)
            raw_asset = residual_weight - (
                residual_weight @ panel.left[day_index]
            ) @ panel.right[day_index].T
            gross = np.abs(raw_asset).sum()
            if gross > 0:
                residual_weight /= gross
            output[day_index - offset_days, lag_index] = (
                residual_weight @ panel.residuals[day_index]
            )
    frame = pd.DataFrame(output, index=panel.dates[offset_days:], columns=lags)
    frame.index.name = "date"
    return frame


def holding_period_returns(
    weights: pd.DataFrame,
    asset_returns: pd.DataFrame,
    holding_days: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 22, 30),
) -> pd.DataFrame:
    """Apply a one-day-trained asset portfolio for each B-day holding horizon."""

    returns = asset_returns.reindex(index=weights.index, columns=weights.columns)
    if returns.isna().any().any():
        raise ValueError("asset returns do not fully cover strategy weight coordinates")
    weight_values = weights.to_numpy(float)
    return_values = returns.to_numpy(float)
    output = np.zeros((len(weights), len(holding_days)), dtype=float)
    for horizon_index, horizon in enumerate(holding_days):
        for time_index in range(horizon, len(weights)):
            held_weight = weight_values[time_index - horizon + 1]
            daily = return_values[
                time_index - horizon + 1 : time_index + 1
            ] @ held_weight
            output[time_index, horizon_index] = (
                np.prod(1 + daily) - 1
            ) / horizon
    frame = pd.DataFrame(output, index=weights.index, columns=holding_days)
    frame.index.name = "date"
    return frame


def _statistics_by_column(returns: pd.DataFrame, key_name: str) -> pd.DataFrame:
    rows = []
    for column in returns:
        rows.append({key_name: column, **performance_statistics(returns[column].to_numpy())})
    return pd.DataFrame(rows)


def build_robustness_figures(
    panel: ResidualPanel,
    benchmark_weights: pd.DataFrame,
    asset_returns: pd.DataFrame,
    output_directory: Path,
) -> dict[str, object]:
    """Generate Korean variants of Figures 9-12 from one benchmark strategy."""

    output_directory.mkdir(parents=True, exist_ok=True)
    sparse = sparse_weight_returns(benchmark_weights, asset_returns)
    reversal = naive_reversal_returns(panel)
    holding = holding_period_returns(benchmark_weights, asset_returns)
    sparse.to_csv(output_directory / "sparse_weight_returns.csv")
    reversal.to_csv(output_directory / "naive_reversal_returns.csv")
    holding.to_csv(output_directory / "holding_period_returns.csv")
    sparse_stats = _statistics_by_column(sparse, "percentile")
    reversal_stats = _statistics_by_column(reversal, "lag")
    holding_stats = _statistics_by_column(holding, "holding_days")
    sparse_stats.to_csv(output_directory / "sparse_weight_statistics.csv", index=False)
    reversal_stats.to_csv(output_directory / "naive_reversal_statistics.csv", index=False)
    holding_stats.to_csv(output_directory / "holding_period_statistics.csv", index=False)

    figure, axes = plt.subplots(1, 3, figsize=(13, 4))
    x_values = np.arange(len(sparse_stats))
    for axis, column, title in zip(
        axes,
        ("sharpe", "annual_return", "annual_volatility"),
        ("Sharpe ratio", "Annual return", "Annual volatility"),
        strict=True,
    ):
        axis.plot(x_values, sparse_stats[column], marker="x")
        axis.set(xticks=x_values, xticklabels=sparse_stats["percentile"], title=title)
        axis.set_xlabel("Largest absolute weight fraction")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_09_sparse_performance.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 5))
    for column in sparse:
        axis.plot(sparse.index, (1 + sparse[column]).cumprod() - 1, label=column)
    axis.set(title="Cumulative returns of sparse asset-weight portfolios", ylabel="Cumulative return")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_directory / "fig_10_sparse_cumulative_returns.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(13, 4))
    for axis, column, title in zip(
        axes,
        ("sharpe", "annual_return", "annual_volatility"),
        ("Sharpe ratio", "Annual return", "Annual volatility"),
        strict=True,
    ):
        axis.plot(reversal_stats["lag"], reversal_stats[column], marker="x")
        axis.set(title=title, xlabel="Reversal lag L (days)")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_11_naive_reversal.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(13, 4))
    for axis, column, title in zip(
        axes,
        ("sharpe", "annual_return", "annual_volatility"),
        ("Sharpe ratio", "Annual return", "Annual volatility"),
        strict=True,
    ):
        axis.plot(holding_stats["holding_days"], holding_stats[column], marker="x")
        axis.set(title=title, xlabel="Holding period B (days)")
    figure.suptitle("One-day objective applied to longer holding periods")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_12_holding_period_panel_a.png", dpi=180)
    plt.close(figure)
    return {
        "classification": "Korean PCA5 benchmark robustness variants",
        "sparse_percentiles": list(sparse.columns),
        "reversal_lags": list(reversal.columns),
        "holding_days": list(holding.columns),
        "figure_12_limit": "Panel A only; B-day-optimized policies require separate training runs",
    }
