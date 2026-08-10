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
    factors = factors.copy()
    if "weight" in factors:
        factors = factors.loc[factors["weight"].eq("vw")].copy()
    if "frequency" in factors:
        factors = factors.loc[factors["frequency"].eq("daily")].copy()
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

    cnn_returns: dict[str, pd.Series] = {}
    friction_rows = []
    ablation_rows = []
    benchmark_weights: pd.DataFrame | None = None
    benchmark_label = ""
    benchmark_daily: pd.DataFrame | None = None
    for directory in strategy_directories:
        daily = pd.read_csv(directory / "daily_performance.csv", parse_dates=["date"])
        audit = json.loads((directory / "simulation_audit.json").read_text("utf-8"))
        label = f"{audit.get('factor_model', 'PCA')} / {audit['model']}"
        if audit["model"] == "cnn_transformer":
            cnn_returns[label] = daily.set_index("date")["return"]
        if audit["model"] == "cnn_transformer_frictions":
            friction_rows.append(
                {
                    "strategy": label,
                    "objective": audit["objective"],
                    **performance_statistics(daily["return"].to_numpy()),
                    "transaction_cost": audit["transaction_cost"],
                    "short_holding_cost": audit["short_holding_cost"],
                }
            )
        if (
            audit["model"] in {"direct_ffn", "ou_ffn"}
            and audit["objective"] == "sharpe"
            and audit["lookback_days"] == 30
            and audit["rolling_retrain"] is True
        ):
            ablation_rows.append(
                {
                    "factor_model": audit.get("factor_model", "PCA"),
                    "model": audit["model"],
                    **performance_statistics(daily["return"].to_numpy()),
                }
            )
        if audit.get("factor_model") == "PCA" and audit["model"] == "cnn_transformer":
            benchmark_weights = pd.read_parquet(directory / "daily_asset_weights.parquet")
            benchmark_label = label
            benchmark_daily = daily
    if cnn_returns:
        return_frame = pd.concat(cnn_returns, axis=1).dropna()
        return_frame.corr().to_csv(output_directory / "table_a08_strategy_correlations.csv")
    else:
        pd.DataFrame().to_csv(output_directory / "table_a08_strategy_correlations.csv")
    pd.DataFrame(friction_rows).to_csv(
        output_directory / "table_a10_pca_cnn_friction_trained.csv", index=False
    )
    pd.DataFrame(ablation_rows).to_csv(
        output_directory / "table_a09_time_series_ablation.csv", index=False
    )

    residual_frame = pd.DataFrame(panel.residuals, index=panel.dates, columns=panel.tickers)
    residual_frame = residual_frame.where(panel.observed)
    # The paper specifies one-calendar-month smoothing but does not publish the
    # pre-smoothing volatility estimator. We use a trailing 22-trading-day
    # standard deviation and disclose this operational choice in the audit.
    rolling_volatility = residual_frame.rolling(22, min_periods=15).std(ddof=0)
    volatility_summary = pd.DataFrame(
        {
            "cross_sectional_mean": rolling_volatility.mean(axis=1),
            "quantile_2_5": rolling_volatility.quantile(0.025, axis=1),
            "quantile_97_5": rolling_volatility.quantile(0.975, axis=1),
        }
    ).rolling(22, min_periods=10).mean()
    volatility_summary.index.name = "date"
    volatility_summary.to_csv(output_directory / "figure_a06_residual_volatility.csv")
    figure, axis = plt.subplots(figsize=(9, 4))
    axis.plot(
        volatility_summary.index,
        volatility_summary["cross_sectional_mean"],
        label="Cross-sectional mean",
    )
    axis.fill_between(
        volatility_summary.index,
        volatility_summary["quantile_2_5"],
        volatility_summary["quantile_97_5"],
        alpha=0.2,
        label="Cross-sectional 95% interval",
    )
    axis.set(title="PCA5 residual volatility over time", ylabel="Daily volatility")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_directory / "fig_a06_residual_volatility.png", dpi=180)
    plt.close(figure)

    cost_figure_status = "blocked_no_completed_pca_cnn_weights"
    if benchmark_daily is not None:
        post_cost = (
            benchmark_daily["gross_return"]
            - 0.0005 * benchmark_daily["turnover"]
            - 0.0001 * benchmark_daily["short_proportion"]
        )
        pd.DataFrame(
            {
                "date": benchmark_daily["date"],
                "post_cost_return": post_cost,
            }
        ).to_csv(output_directory / "figure_a07_returns_after_costs.csv", index=False)
        figure, axis = plt.subplots(figsize=(9, 5))
        axis.plot(
            benchmark_daily["date"],
            (1 + post_cost).cumprod() - 1,
            label=benchmark_label,
        )
        axis.set(
            title="PCA5 CNN cumulative returns after paper cost constants",
            ylabel="Cumulative return",
        )
        axis.legend()
        figure.tight_layout()
        figure.savefig(output_directory / "fig_a07_returns_after_costs.png", dpi=180)
        plt.close(figure)
        cost_figure_status = "generated_mechanical_paper_cost_constants"

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
        portfolio_concentration = (
            merged.dropna(subset=["industry_code"])
            .assign(abs_weight=lambda frame: frame["weight"].abs())
            .groupby(["date", "industry"], as_index=False)["abs_weight"]
            .sum()
        )
        population = classifications.copy()
        population["industry"] = (
            population["industry_code"].astype("Int64").astype(str).str[:2]
        )
        population = (
            population.dropna(subset=["industry_code"])
            .groupby(["date", "industry"], as_index=False)["ticker"]
            .nunique()
            .rename(columns={"ticker": "population_count"})
        )
        population["population_share"] = population["population_count"].div(
            population.groupby("date")["population_count"].transform("sum")
        )
        concentration = portfolio_concentration.merge(
            population[["date", "industry", "population_share"]],
            on=["date", "industry"],
            how="left",
        )
        concentration["standardized_concentration"] = concentration["abs_weight"].div(
            concentration["population_share"]
        )
        concentration = concentration.sort_values(["industry", "date"])
        concentration["rolling_132_day_concentration"] = (
            concentration.groupby("industry")["standardized_concentration"]
            .transform(lambda values: values.rolling(132, min_periods=66).mean())
        )
        concentration.to_csv(
            output_directory / "figure_a05_industry_concentration.csv", index=False
        )
        leading = (
            portfolio_concentration.groupby("industry")["abs_weight"]
            .mean()
            .nlargest(10)
            .index
        )
        figure, axis = plt.subplots(figsize=(9, 4))
        for industry_code in leading:
            sample = concentration.loc[concentration["industry"].eq(industry_code)]
            axis.plot(
                sample["date"],
                sample["rolling_132_day_concentration"],
                label=industry_code,
            )
        axis.set(
            title=f"132-day standardized industry concentration: {benchmark_label}",
            ylabel="Portfolio share / population share",
        )
        axis.legend(title="Industry", ncol=2, fontsize=7)
        figure.tight_layout()
        figure.savefig(output_directory / "fig_a05_industry_concentration.png", dpi=180)
        plt.close(figure)
        industry_status = "generated_korean_industry_taxonomy"

    audit = {
        "classification": "Korean PCA5 appendix variants",
        "strategy_count": len(strategy_directories),
        "industry_figure_status": industry_status,
        "cost_figure_status": cost_figure_status,
        "cnn_correlation_strategy_count": len(cnn_returns),
        "friction_trained_strategy_count": len(friction_rows),
        "ablation_strategy_count": len(ablation_rows),
        "residual_volatility_estimator": (
            "22-day trailing stock-level residual standard deviation; cross-sectional "
            "mean and 2.5/97.5 percentiles; 22-day smoothing"
        ),
        "trading_cost_interpretation": (
            "Figure A.7 mechanically applies paper constants; Table A.X requires "
            "friction-aware retraining; neither validates realized Korean costs"
        ),
        "exact_ipca_outputs": "blocked by 240-month history and convergence",
    }
    (output_directory / "appendix_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit
