"""Data-backed Korean variants of selected paper appendix outputs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .results import factor_alpha, performance_statistics
from .trading import ResidualPanel


def unconditional_average_residual_returns(
    panel: ResidualPanel,
    *,
    start_index: int = 1000,
) -> pd.DataFrame:
    """Return a unit-gross equal-weight average of available PCA residuals."""

    if panel.extra_asset_loadings is not None:
        raise ValueError("unconditional average is implemented for PCA composition")
    values = np.zeros(len(panel.dates) - start_index, dtype=float)
    for day_index in range(start_index, len(panel.dates)):
        available = panel.observed[day_index] & (panel.residuals[day_index] != 0)
        count = int(available.sum())
        if count == 0:
            continue
        weight = np.zeros(len(panel.tickers), dtype=float)
        weight[available] = 1 / count
        asset_weight = weight - (
            weight @ panel.left[day_index]
        ) @ panel.right[day_index].T
        gross = np.abs(asset_weight).sum()
        if gross > 0:
            weight /= gross
        values[day_index - start_index] = weight @ panel.residuals[day_index]
    return pd.DataFrame({"date": panel.dates[start_index:], "return": values})


def build_appendix_outputs(
    panel: ResidualPanel,
    strategy_directories: list[Path],
    factors: pd.DataFrame,
    industry: pd.DataFrame,
    output_directory: Path,
) -> dict[str, object]:
    """Build Korean variants of Appendix Figure A.5-A.7 and Table A.VI-A.VIII/A.X."""

    output_directory.mkdir(parents=True, exist_ok=True)
    unconditional = unconditional_average_residual_returns(panel)
    unconditional.to_csv(
        output_directory / "unconditional_average_residual_returns.csv", index=False
    )
    table_a06 = pd.DataFrame(
        [{"strategy": "PCA5 average residual", **performance_statistics(unconditional["return"].to_numpy())}]
    )
    table_a06.to_csv(output_directory / "table_a06_unconditional_performance.csv", index=False)
    factor_sets = {
        "CAPM": ["RMRF"],
        "Korean FF3": ["RMRF", "SMB", "HML"],
        "Korean FF5": ["RMRF", "SMB", "HML", "RMW", "CMA"],
        "Korean 6-factor": ["RMRF", "SMB", "HML", "RMW", "CMA", "MOM"],
    }
    alpha_rows = [
        {
            "strategy": "PCA5 average residual",
            "factor_model": name,
            **factor_alpha(unconditional, factors, columns),
        }
        for name, columns in factor_sets.items()
    ]
    pd.DataFrame(alpha_rows).to_csv(
        output_directory / "table_a07_unconditional_alpha.csv", index=False
    )

    returns: dict[str, pd.Series] = {}
    cost_rows = []
    benchmark_weights: pd.DataFrame | None = None
    benchmark_label = ""
    for directory in strategy_directories:
        daily = pd.read_csv(directory / "daily_performance.csv", parse_dates=["date"])
        audit = json.loads((directory / "simulation_audit.json").read_text("utf-8"))
        label = f"{audit.get('factor_model', 'PCA')} / {audit['model']}"
        returns[label] = daily.set_index("date")["return"]
        post_cost = (
            daily["gross_return"]
            - 0.0005 * daily["turnover"]
            - 0.0001 * daily["short_proportion"]
        )
        cost_rows.append(
            {
                "strategy": label,
                **performance_statistics(post_cost.to_numpy()),
                "transaction_cost": 0.0005,
                "short_holding_cost": 0.0001,
            }
        )
        if audit.get("factor_model") == "PCA" and audit["model"] == "cnn_transformer":
            benchmark_weights = pd.read_parquet(directory / "daily_asset_weights.parquet")
            benchmark_label = label
    return_frame = pd.concat(returns, axis=1).dropna()
    return_frame.corr().to_csv(output_directory / "table_a08_strategy_correlations.csv")
    pd.DataFrame(cost_rows).to_csv(
        output_directory / "table_a10_pca_and_benchmark_costs.csv", index=False
    )

    volatility = pd.Series(
        [
            panel.residuals[day, panel.observed[day]].std(ddof=0)
            if panel.observed[day].any()
            else np.nan
            for day in range(len(panel.dates))
        ],
        index=panel.dates,
    )
    figure, axis = plt.subplots(figsize=(9, 4))
    axis.plot(volatility.index, volatility.rolling(20).mean())
    axis.set(title="20-day mean cross-sectional PCA residual volatility", ylabel="Daily volatility")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_a06_residual_volatility.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 5))
    for directory in strategy_directories:
        daily = pd.read_csv(directory / "daily_performance.csv", parse_dates=["date"])
        audit = json.loads((directory / "simulation_audit.json").read_text("utf-8"))
        label = f"{audit.get('factor_model', 'PCA')} / {audit['model']}"
        post_cost = (
            daily["gross_return"]
            - 0.0005 * daily["turnover"]
            - 0.0001 * daily["short_proportion"]
        )
        axis.plot(daily["date"], (1 + post_cost).cumprod() - 1, label=label)
    axis.set(title="Cumulative returns after paper trading-cost constants", ylabel="Cumulative return")
    axis.legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(output_directory / "fig_a07_returns_after_costs.png", dpi=180)
    plt.close(figure)

    industry_status = "blocked_no_completed_pca_cnn_weights"
    if benchmark_weights is not None:
        benchmark_weights.index = pd.to_datetime(benchmark_weights.index)
        long_weights = benchmark_weights.stack().rename("weight").reset_index()
        long_weights.columns = ["date", "ticker", "weight"]
        classifications = industry.copy()
        classifications["date"] = pd.to_datetime(classifications["date"])
        classifications["ticker"] = classifications["ticker"].astype(str).str.upper()
        merged = long_weights.merge(
            classifications[["date", "ticker", "industry_code"]],
            on=["date", "ticker"],
            how="left",
        )
        merged["industry"] = merged["industry_code"].astype("Int64").astype(str).str[:2]
        concentration = (
            merged.dropna(subset=["industry_code"])
            .assign(abs_weight=lambda frame: frame["weight"].abs())
            .groupby(["date", "industry"], as_index=False)["abs_weight"]
            .sum()
        )
        average = concentration.groupby("industry")["abs_weight"].mean().nlargest(12)
        figure, axis = plt.subplots(figsize=(9, 4))
        axis.bar(average.index, average.values)
        axis.set(
            title=f"Average absolute industry allocation: {benchmark_label}",
            xlabel="Two-digit Korean industry code",
            ylabel="Gross allocation share",
        )
        figure.tight_layout()
        figure.savefig(output_directory / "fig_a05_industry_concentration.png", dpi=180)
        plt.close(figure)
        industry_status = "generated_korean_industry_taxonomy"

    audit = {
        "classification": "Korean PCA5 appendix variants",
        "strategy_count": len(strategy_directories),
        "industry_figure_status": industry_status,
        "trading_cost_interpretation": (
            "paper constants applied mechanically; not realized Korean cost validation"
        ),
        "exact_ipca_outputs": "blocked by 240-month history and convergence",
    }
    (output_directory / "appendix_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit
