"""Risk-premium and residual decompositions for the Korean Figure 13 variant."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


def decompose_fama_french_stock_returns(
    stock_returns: pd.DataFrame,
    factor_returns: pd.DataFrame,
    factor_legs: pd.DataFrame,
    *,
    factor_columns: tuple[str, ...] = ("RMRF", "SMB", "HML", "RMW", "CMA"),
) -> pd.DataFrame:
    """Decompose stock excess returns into fitted FF and residual components."""

    required_stock = {"date", "ticker", "return"}
    required_factor = {"date", *factor_columns}
    leg_columns = [f"factor_asset_weight_{column}" for column in factor_columns]
    required_legs = {"date", "ticker", *leg_columns}
    for name, frame, required in (
        ("stock_returns", stock_returns, required_stock),
        ("factor_returns", factor_returns, required_factor),
        ("factor_legs", factor_legs, required_legs),
    ):
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{name} is missing columns: {sorted(missing)}")
    stocks = stock_returns[["date", "ticker", "return"]].copy()
    factors = factor_returns[["date", *factor_columns]].copy()
    legs = factor_legs[["date", "ticker", *leg_columns]].copy()
    for frame in (stocks, factors, legs):
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    stocks["ticker"] = stocks["ticker"].astype(str).str.upper()
    legs["ticker"] = legs["ticker"].astype(str).str.upper()
    aligned = stocks.merge(factors, on="date", how="inner", validate="many_to_one")
    aligned = aligned.merge(
        legs, on=["date", "ticker"], how="inner", validate="one_to_one"
    )
    factor_values = aligned[list(factor_columns)].to_numpy(float)
    # The saved synthetic factor-leg coefficient is -beta.
    negative_beta = aligned[leg_columns].to_numpy(float)
    aligned["systematic_return"] = np.sum(-negative_beta * factor_values, axis=1)
    aligned["residual_return"] = aligned["return"] - aligned["systematic_return"]
    return aligned[["date", "ticker", "return", "systematic_return", "residual_return"]]


def fitted_factor_portfolio(
    strategy: pd.DataFrame,
    factors: pd.DataFrame,
    *,
    factor_columns: tuple[str, ...] = ("RMRF", "SMB", "HML", "RMW", "CMA"),
    leverage: float = 1.65,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Fit the public notebook's no-intercept factor-mimicking portfolio."""

    if leverage <= 0:
        raise ValueError("leverage must be positive")
    if missing := {"date", "return"}.difference(strategy.columns):
        raise ValueError(f"strategy is missing columns: {sorted(missing)}")
    if missing := {"date", *factor_columns}.difference(factors.columns):
        raise ValueError(f"factors are missing columns: {sorted(missing)}")
    left = strategy[["date", "return"]].copy()
    right = factors[["date", *factor_columns]].copy()
    left["date"] = pd.to_datetime(left["date"], errors="raise")
    right["date"] = pd.to_datetime(right["date"], errors="raise")
    aligned = left.merge(right, on="date", how="inner").dropna()
    fitted = sm.OLS(aligned["return"], aligned[list(factor_columns)]).fit()
    coefficients = fitted.params.to_numpy(float)
    gross = np.abs(coefficients).sum()
    if gross <= 0:
        raise ValueError("fitted factor coefficients have zero gross exposure")
    normalized = leverage * coefficients / gross
    aligned["factor_portfolio_return"] = (
        aligned[list(factor_columns)].to_numpy(float) @ normalized
    )
    output = aligned[["date", "return", "factor_portfolio_return"]].rename(
        columns={"return": "statistical_arbitrage_return"}
    )
    audit = {
        **{f"coefficient_{name}": float(value) for name, value in zip(factor_columns, normalized, strict=True)},
        "factor_portfolio_gross_leverage": float(np.abs(normalized).sum()),
        "no_intercept_r_squared": float(fitted.rsquared),
    }
    return output, audit


def build_risk_premium_figure(
    stock_returns: pd.DataFrame,
    factor_returns: pd.DataFrame,
    factor_legs: pd.DataFrame,
    strategy: pd.DataFrame,
    output_directory: Path,
) -> dict[str, object]:
    """Build a Korean FF5 analogue of the paper's IPCA Figure 13."""

    output_directory.mkdir(parents=True, exist_ok=True)
    decomposition = decompose_fama_french_stock_returns(
        stock_returns, factor_returns, factor_legs
    )
    comparison, fit_audit = fitted_factor_portfolio(strategy, factor_returns)
    last_dates = decomposition["date"].drop_duplicates().sort_values().tail(22)
    recent = decomposition.loc[decomposition["date"].isin(last_dates)].copy()
    coverage = recent.groupby("ticker").size()
    complete_tickers = coverage.loc[coverage.eq(len(last_dates))].index
    recent = recent.loc[recent["ticker"].isin(complete_tickers)]
    ranking = (
        recent.groupby("ticker")["systematic_return"].apply(lambda values: values.abs().sum()).nlargest(7)
    )
    tickers = ranking.index.tolist()
    if not tickers:
        raise ValueError("no complete stock histories for Figure 13")
    decomposition.to_csv(output_directory / "figure_13_stock_decomposition.csv", index=False)
    comparison.to_csv(output_directory / "figure_13_factor_portfolio.csv", index=False)

    figure, axes = plt.subplots(2, 4, figsize=(14, 7), sharex=True)
    for axis, ticker in zip(axes.ravel(), tickers, strict=False):
        sample = recent.loc[recent["ticker"].eq(ticker)].sort_values("date")
        stock_growth = (1 + sample["return"]).cumprod()
        systematic_growth = (1 + sample["systematic_return"]).cumprod()
        axis.plot(sample["date"], systematic_growth, label="FF5 systematic", linewidth=2)
        axis.plot(sample["date"], stock_growth, label="Stock excess return", alpha=0.65)
        axis.set_title(ticker)
        axis.xaxis.set_major_locator(plt.MaxNLocator(4))
        axis.tick_params(axis="x", rotation=25)
    for axis in axes.ravel()[len(tickers) :]:
        axis.set_visible(False)
    axes.ravel()[0].legend(fontsize=8)
    figure.suptitle("Stock return and Korean FF5 systematic component (last 22 days)")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_13a_stock_factor_components.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 5))
    statarb = (1 + comparison["statistical_arbitrage_return"]).cumprod()
    factor = (1 + comparison["factor_portfolio_return"]).cumprod()
    axis.plot(comparison["date"], statarb, label="Statistical arbitrage portfolio")
    axis.plot(comparison["date"], factor, label="Fitted Korean FF5 portfolio")
    axis.set(title="Statistical arbitrage versus fitted factor portfolio", ylabel="Growth of 1")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_directory / "fig_13b_statarb_factor_portfolio.png", dpi=180)
    plt.close(figure)

    audit: dict[str, object] = {
        "classification": "Korean FF5 analogue; exact paper IPCA Figure 13 blocked",
        "stock_examples": tickers,
        "stock_example_days": len(last_dates),
        "strategy_observations": len(comparison),
        "factor_model": "Korean FF5 price-return non-PIT accounting sensitivity",
        "paper_leverage_constant": 1.65,
        **fit_audit,
    }
    (output_directory / "figure_13_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit
