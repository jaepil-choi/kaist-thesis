"""Tables and figures for Korean variants of the paper's empirical outputs."""

from __future__ import annotations

import json
import re
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
    if audit.get("factor_model") == "PCA":
        match = re.match(r"pca(\d+)_", directory.name)
        if match:
            audit["factor_count"] = int(match.group(1))
            audit["factor_model"] = f"PCA{match.group(1)}"
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


def _strategy_group(audit: dict[str, object]) -> str | None:
    """Map one full-contract run to its numbered main-paper table group."""

    if int(audit.get("epochs", 0)) != 100 or int(audit.get("holding_days", 0)) != 1:
        return None
    model = str(audit["model"])
    objective = str(audit["objective"])
    lookback = int(audit["lookback_days"])
    rolling = bool(audit["rolling_retrain"])
    has_cost = bool(audit["transaction_cost"] or audit["short_holding_cost"])
    if model == "cnn_transformer_frictions" and has_cost:
        return "frictions"
    if model == "cnn_transformer" and lookback == 60 and objective == "sharpe":
        return "lookback60"
    if model == "cnn_transformer" and not rolling and objective == "sharpe":
        return "constant"
    if lookback == 30 and rolling and not has_cost:
        if objective == "sharpe" and model in {
            "cnn_transformer",
            "fourier_ffn",
            "ou_threshold",
        }:
            return "sharpe"
        if objective == "meanvar" and model in {"cnn_transformer", "fourier_ffn"}:
            return "meanvar"
    return None


def _numbered_tables(
    loaded: list[tuple[str, pd.DataFrame, pd.DataFrame, dict]],
    factors: pd.DataFrame,
    performance_path: Path,
    alpha_path: Path | None,
) -> tuple[int, int]:
    """Write a performance table and its factor-alpha companion."""

    performance_rows: list[dict[str, object]] = []
    alpha_rows: list[dict[str, object]] = []
    factor_sets = {
        "CAPM": ["RMRF"],
        "Korean FF3": ["RMRF", "SMB", "HML"],
        "Korean FF5": ["RMRF", "SMB", "HML", "RMW", "CMA"],
        "Korean 6-factor": ["RMRF", "SMB", "HML", "RMW", "CMA", "MOM"],
    }
    for label, daily, _, audit in loaded:
        performance_rows.append(
            {
                "strategy": label,
                "factor_model": audit.get("factor_model", "PCA"),
                "model": audit["model"],
                "objective": audit["objective"],
                "lookback_days": audit["lookback_days"],
                "rolling_retrain": audit["rolling_retrain"],
                "training_window_days": audit["training_window_days"],
                "transaction_cost": audit["transaction_cost"],
                "short_holding_cost": audit["short_holding_cost"],
                **performance_statistics(daily["return"].to_numpy()),
                "mean_daily_turnover": float(daily["turnover"].mean()),
                "mean_short_proportion": float(daily["short_proportion"].mean()),
            }
        )
        if alpha_path is not None:
            for factor_model, columns in factor_sets.items():
                alpha_rows.append(
                    {
                        "strategy": label,
                        "factor_model": factor_model,
                        **factor_alpha(daily, factors, columns),
                    }
                )
    pd.DataFrame(performance_rows).to_csv(performance_path, index=False)
    if alpha_path is not None:
        pd.DataFrame(alpha_rows).to_csv(alpha_path, index=False)
    return len(performance_rows), len(alpha_rows)


def build_numbered_korean_report(
    strategy_directories: list[Path],
    factor_path: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Build all numbered Korean main tables and Figures 5-8 from available runs."""

    factors = pd.read_csv(factor_path, parse_dates=["date"])
    if "weight" in factors:
        factors = factors.loc[factors["weight"].eq("vw")].copy()
    if "frequency" in factors:
        factors = factors.loc[factors["frequency"].eq("daily")].copy()
    groups: dict[str, list[tuple[str, pd.DataFrame, pd.DataFrame, dict]]] = {
        name: []
        for name in ("sharpe", "meanvar", "lookback60", "constant", "frictions")
    }
    for directory in strategy_directories:
        daily, weights, audit = _load_strategy(directory)
        group = _strategy_group(audit)
        if group is None:
            continue
        label = (
            f"{audit.get('factor_model', 'PCA')} / {audit['model']} / "
            f"{audit['objective']}"
        )
        groups[group].append((label, daily, weights, audit))
    output_directory.mkdir(parents=True, exist_ok=True)
    table_contracts = {
        "sharpe": ("table_01_korean_performance.csv", "table_02_korean_factor_alpha.csv"),
        "meanvar": ("table_03_korean_performance.csv", "table_04_korean_factor_alpha.csv"),
        "lookback60": ("table_05_korean_performance.csv", "table_06_korean_factor_alpha.csv"),
        "constant": ("table_07_korean_performance.csv", "table_08_korean_factor_alpha.csv"),
        "frictions": ("table_09_korean_performance.csv", None),
    }
    table_counts: dict[str, dict[str, int]] = {}
    for group, (performance_name, alpha_name) in table_contracts.items():
        performance_count, alpha_count = _numbered_tables(
            groups[group],
            factors,
            output_directory / performance_name,
            None if alpha_name is None else output_directory / alpha_name,
        )
        table_counts[group] = {
            "performance_rows": performance_count,
            "alpha_rows": alpha_count,
        }

    main = groups["sharpe"]
    model_panels = (
        ("cnn_transformer", "CNN+Transformer"),
        ("fourier_ffn", "Fourier+FFN"),
        ("ou_threshold", "OU threshold"),
    )
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for axis, (model, title) in zip(axes, model_panels, strict=True):
        rows = [row for row in main if row[3]["model"] == model]
        for _, daily, _, audit in rows:
            axis.plot(
                daily["date"],
                (1 + daily["return"]).cumprod() - 1,
                label=str(audit.get("factor_model", "PCA")),
                linewidth=1.1,
            )
        axis.axhline(0, color="black", linewidth=0.7)
        axis.set(title=title)
        axis.tick_params(axis="x", labelrotation=30)
        if rows:
            axis.legend(fontsize=6, ncol=2)
    axes[0].set_ylabel("Cumulative return")
    figure.suptitle("Korean statistical-arbitrage OOS returns")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_05_korean_cumulative_returns.png", dpi=180)
    plt.close(figure)

    baseline = [row for row in main if row[3]["model"] == "cnn_transformer"]
    friction = groups["frictions"]
    for metric, figure_number, ylabel in (
        ("turnover", "06", "L1 turnover"),
        ("short_proportion", "07", "Gross short share"),
    ):
        figure, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
        for axis, rows, title in zip(
            axes,
            (baseline, friction),
            ("No-friction objective", "Friction-aware objective"),
            strict=True,
        ):
            for _, daily, _, audit in rows:
                factor_label = str(audit.get("factor_model", "PCA"))
                objective_label = "SR" if audit["objective"] == "sharpe" else "MV"
                label = factor_label if rows is baseline else f"{factor_label} ({objective_label})"
                axis.plot(daily["date"], daily[metric].rolling(20).mean(), label=label)
            axis.set(title=title, ylabel=ylabel)
            axis.tick_params(axis="x", labelrotation=30)
            if rows:
                axis.legend(fontsize=6, ncol=2)
            else:
                axis.text(0.5, 0.5, "completed run unavailable", ha="center", va="center")
        figure.tight_layout()
        figure.savefig(output_directory / f"fig_{figure_number}_korean_{metric}.png", dpi=180)
        plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharex=True, sharey=True)
    for axis, (model, title) in zip(axes, model_panels, strict=True):
        rows = [row for row in main if row[3]["model"] == model]
        for _, _, weights, audit in rows:
            nonzero = weights.to_numpy().ravel()
            nonzero = nonzero[np.abs(nonzero) > 1e-10]
            axis.hist(
                nonzero,
                bins=80,
                density=True,
                histtype="step",
                label=str(audit.get("factor_model", "PCA")),
            )
        axis.set(title=title, xlabel="Weight")
        if rows:
            axis.legend(fontsize=6, ncol=2)
    axes[0].set_ylabel("Density")
    figure.suptitle("Distribution of nonzero underlying asset weights")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_08_korean_weight_distribution.png", dpi=180)
    plt.close(figure)

    audit = {
        "classification": "Korean price-return numbered empirical variants",
        "strategy_directory_count": len(strategy_directories),
        "group_counts": {name: len(rows) for name, rows in groups.items()},
        "table_counts": table_counts,
        "blocked_exact_outputs": (
            "All U.S. CRSP/Compustat and 240-month IPCA results remain blocked; "
            "empty Korean groups remain visibly empty rather than proxy-filled"
        ),
    }
    (output_directory / "numbered_report_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit


# Backward-compatible name for early PCA-only callers.
build_korean_pca5_report = build_korean_main_report
