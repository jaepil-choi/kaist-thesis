"""Tables and figures for Korean variants of the paper's empirical outputs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import ttest_1samp


def performance_statistics(returns: np.ndarray) -> dict[str, float]:
    """Compute the annualized statistics used by the authors' ``run_stats.py``."""

    values = np.asarray(returns, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("returns must be a finite vector with at least two observations")
    annual_return = float(values.mean() * 252)
    annual_volatility = float(values.std(ddof=0) * np.sqrt(252))
    t_statistic, p_value = ttest_1samp(values, 0)
    return {
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe": annual_return / annual_volatility,
        "mean_t_statistic": float(t_statistic),
        "mean_p_value": float(p_value),
    }


def factor_alpha(
    strategy: pd.DataFrame,
    factors: pd.DataFrame,
    factor_columns: list[str],
) -> dict[str, float | int]:
    """Estimate the paper's daily OLS factor regression with annualized intercept."""

    required = {"date", "return"}
    if missing := required.difference(strategy.columns):
        raise ValueError(f"strategy is missing columns: {sorted(missing)}")
    if missing := {"date", *factor_columns}.difference(factors.columns):
        raise ValueError(f"factors are missing columns: {sorted(missing)}")
    left = strategy[["date", "return"]].copy()
    right = factors[["date", *factor_columns]].copy()
    left["date"] = pd.to_datetime(left["date"], errors="raise")
    right["date"] = pd.to_datetime(right["date"], errors="raise")
    aligned = left.merge(right, on="date", how="inner").dropna()
    if len(aligned) <= len(factor_columns) + 1:
        raise ValueError("insufficient aligned observations for factor regression")
    design = sm.add_constant(aligned[factor_columns], has_constant="add")
    fitted = sm.OLS(aligned["return"], design).fit()
    return {
        "observations": len(aligned),
        "annual_alpha": float(fitted.params["const"] * 252),
        "alpha_t_statistic": float(fitted.tvalues["const"]),
        "alpha_p_value": float(fitted.pvalues["const"]),
        "r_squared": float(fitted.rsquared),
        "adjusted_r_squared": float(fitted.rsquared_adj),
    }


def _load_strategy(directory: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    daily = pd.read_csv(directory / "daily_performance.csv", parse_dates=["date"])
    weights = pd.read_parquet(directory / "daily_asset_weights.parquet")
    audit = json.loads((directory / "simulation_audit.json").read_text("utf-8"))
    return daily, weights, audit


def build_korean_main_report(
    strategy_directories: list[Path],
    factor_path: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Create Korean counterparts to the paper's core performance outputs."""

    if not strategy_directories:
        raise ValueError("at least one strategy directory is required")
    factors = pd.read_csv(factor_path, parse_dates=["date"])
    if "weight" in factors:
        factors = factors.loc[factors["weight"].eq("vw")].copy()
    if "frequency" in factors:
        factors = factors.loc[factors["frequency"].eq("daily")].copy()
    factor_sets = {
        "CAPM": ["RMRF"],
        "Korean FF3": ["RMRF", "SMB", "HML"],
        "Korean FF5": ["RMRF", "SMB", "HML", "RMW", "CMA"],
        "Korean 6-factor": ["RMRF", "SMB", "HML", "RMW", "CMA", "MOM"],
    }
    loaded: list[tuple[str, pd.DataFrame, pd.DataFrame, dict]] = []
    performance_rows: list[dict[str, object]] = []
    alpha_rows: list[dict[str, object]] = []
    for directory in strategy_directories:
        daily, weights, audit = _load_strategy(directory)
        label = (
            f"{audit.get('factor_model', 'PCA')} / "
            f"{audit['model']} / {audit['objective']}"
        )
        loaded.append((label, daily, weights, audit))
        performance_rows.append(
            {
                "strategy": label,
                **performance_statistics(daily["return"].to_numpy()),
                "mean_daily_turnover": float(daily["turnover"].mean()),
                "mean_short_proportion": float(daily["short_proportion"].mean()),
                "mean_gross_leverage": float(daily["leverage"].mean()),
                "oos_start": daily["date"].min().date().isoformat(),
                "oos_end": daily["date"].max().date().isoformat(),
                "oos_days": len(daily),
            }
        )
        for factor_model, columns in factor_sets.items():
            alpha_rows.append(
                {
                    "strategy": label,
                    "factor_model": factor_model,
                    **factor_alpha(daily, factors, columns),
                }
            )

    output_directory.mkdir(parents=True, exist_ok=True)
    performance = pd.DataFrame(performance_rows)
    alphas = pd.DataFrame(alpha_rows)
    performance.to_csv(output_directory / "table_01_korean_performance.csv", index=False)
    alphas.to_csv(output_directory / "table_02_korean_factor_alpha.csv", index=False)

    figure, axis = plt.subplots(figsize=(9, 5))
    for label, daily, _, _ in loaded:
        cumulative = (1 + daily.set_index("date")["return"]).cumprod() - 1
        axis.plot(cumulative.index, cumulative, label=label)
    axis.axhline(0, color="black", linewidth=0.7)
    axis.set(title="Korean statistical-arbitrage OOS returns", ylabel="Cumulative return")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_directory / "fig_05_korean_cumulative_returns.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    for label, daily, _, _ in loaded:
        axes[0].plot(daily["date"], daily["turnover"].rolling(20).mean(), label=label)
        axes[1].plot(
            daily["date"], daily["short_proportion"].rolling(20).mean(), label=label
        )
    axes[0].set(title="20-day average turnover", ylabel="L1 turnover")
    axes[1].set(title="20-day average short allocation", ylabel="Gross short share")
    axes[0].legend()
    figure.tight_layout()
    figure.savefig(output_directory / "fig_06_07_korean_trading.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 5))
    for label, _, weights, _ in loaded:
        nonzero = weights.to_numpy().ravel()
        nonzero = nonzero[np.abs(nonzero) > 1e-10]
        axis.hist(nonzero, bins=80, density=True, histtype="step", label=label)
    axis.set(title="Distribution of nonzero underlying asset weights", xlabel="Weight")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_directory / "fig_08_korean_weight_distribution.png", dpi=180)
    plt.close(figure)

    audit = {
        "classification": "Korean residual-model price-return replication variants",
        "strategy_directories": [str(path) for path in strategy_directories],
        "factor_source": str(factor_path),
        "factor_regression_covariance": "OLS non-robust, matching public run_stats.py",
        "paper_difference": (
            "Korean 6-factor maximum because the exact Kimchi methodology supplied "
            "here does not define the paper's LTR and STR factors"
        ),
        "performance_rows": len(performance),
        "alpha_rows": len(alphas),
    }
    (output_directory / "report_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit


# Backward-compatible name for early PCA-only callers.
build_korean_pca5_report = build_korean_main_report
