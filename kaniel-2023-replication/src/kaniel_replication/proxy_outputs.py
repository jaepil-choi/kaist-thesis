"""Tables and empirical figures for the parsimonious Korean proxy run."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

from .model import assign_month_folds, form_prediction_portfolios, prediction_weights
from .provenance import sha256, write_manifest


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import TwoSlopeNorm  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402


US_TABLE_7 = pd.DataFrame(
    [
        {"portfolio": "Long-short", "mean_percent": 0.40, "t_stat": 5.4,
         "monthly_sharpe": 0.25, "rf2_percent": 0.70},
        {"portfolio": "Top", "mean_percent": 0.17, "t_stat": 3.4,
         "monthly_sharpe": 0.16, "rf2_percent": -0.73},
        {"portfolio": "Bottom", "mean_percent": -0.23, "t_stat": -3.6,
         "monthly_sharpe": -0.21, "rf2_percent": 0.82},
    ]
)


def _apply_style() -> None:
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.22,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.size": 10,
        }
    )


def _validate_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def compute_table_7_summary(portfolios: pd.DataFrame) -> pd.DataFrame:
    """Compute Table 7 mean, t, Sharpe, and factor prediction R-squared."""

    _validate_columns(
        portfolios,
        {
            "top_prediction", "bottom_prediction", "long_short_prediction",
            "top_forecast", "bottom_forecast", "long_short_forecast",
        },
        "Portfolio series",
    )
    pairs = [
        ("Long-short", "long_short_prediction", "long_short_forecast"),
        ("Top", "top_prediction", "top_forecast"),
        ("Bottom", "bottom_prediction", "bottom_forecast"),
    ]
    rows = []
    for label, realized_column, forecast_column in pairs:
        observed = portfolios[[realized_column, forecast_column]].dropna()
        realized = observed[realized_column].astype(float)
        forecast = observed[forecast_column].astype(float)
        standard_deviation = realized.std(ddof=1)
        sharpe = realized.mean() / standard_deviation
        denominator = np.square(realized).sum()
        rf2 = np.nan
        if not np.isclose(denominator, 0.0):
            rf2 = 1.0 - np.square(forecast - realized).sum() / denominator
        rows.append(
            {
                "portfolio": label,
                "months": len(observed),
                "mean_percent": realized.mean() * 100,
                "t_stat": sharpe * np.sqrt(len(observed)),
                "monthly_sharpe": sharpe,
                "rf2_percent": rf2 * 100,
                "cumulative_sum_percent": realized.sum() * 100,
            }
        )
    return pd.DataFrame(rows)


def build_us_korea_comparison(korea: pd.DataFrame) -> pd.DataFrame:
    """Place the published U.S. Table 7 beside the Korean proxy result."""

    us = US_TABLE_7.assign(market="United States (published)", months=np.nan)
    kr = korea.assign(market="Korea (proxy replication)")
    columns = [
        "market", "portfolio", "months", "mean_percent", "t_stat",
        "monthly_sharpe", "rf2_percent",
    ]
    return pd.concat([us, kr], ignore_index=True)[columns]


def _assign_deciles(group: pd.DataFrame) -> pd.DataFrame:
    valid = group.dropna(subset=["prediction", "target_abnormal_return"]).copy()
    order = valid["prediction"].rank(method="first") - 1
    valid["decile"] = (np.floor(order * 10 / len(valid)).astype(int) + 1).clip(1, 10)
    return valid


def _figure_01(sentiment: pd.DataFrame, activity: pd.DataFrame, output: Path) -> None:
    sentiment = sentiment.copy()
    activity = activity.copy()
    sentiment["month"] = pd.to_datetime(sentiment["month"])
    activity["month"] = pd.to_datetime(activity["month"])
    activity = activity.loc[activity["month"].ge(sentiment["month"].min())]

    figure, axes = plt.subplots(2, 1, figsize=(10.8, 6.8), sharex=True)
    axes[0].plot(sentiment["month"], sentiment["sentiment"], color="#2166ac")
    axes[0].axhline(0, color="#555555", linewidth=0.8)
    axes[0].set(title="Panel A. Korean ECOS sentiment proxy", ylabel="PCA score")
    axes[1].plot(activity["month"], activity["activity"], color="#b2182b")
    axes[1].axhline(0, color="#555555", linewidth=0.8)
    axes[1].set(
        title="Panel B. Korean coincident activity cycle",
        ylabel="Deviation from trend", xlabel="Month",
    )
    figure.suptitle("Figure 1 proxy: sentiment and economic activity", fontsize=13)
    figure.text(
        0.01, 0.01,
        "Sentiment is a five-component ECOS proxy with a one-month availability lag; it is not the Baker-Wurgler index.",
        fontsize=8.5, color="#555555",
    )
    figure.tight_layout(rect=(0, 0.04, 1, 0.95))
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _figure_02(
    predictions: pd.DataFrame, sentiment: pd.DataFrame, output: Path, random_seed: int
) -> None:
    observed = (
        predictions.dropna(subset=["prediction"])[["month", "fold"]]
        .drop_duplicates("month").sort_values("month")
    )
    observed["month"] = pd.to_datetime(observed["month"])
    macro = sentiment.copy()
    macro["month"] = pd.to_datetime(macro["month"])
    observed = observed.merge(macro, on="month", how="left", validate="one_to_one")
    chronological = assign_month_folds(
        observed["month"], scheme="chronological", random_seed=random_seed
    ).rename(columns={"fold": "chronological_fold"})
    observed = observed.merge(chronological, on="month", validate="one_to_one")
    colors = ["#2166ac", "#b2182b", "#1b7837"]

    figure, axes = plt.subplots(2, 1, figsize=(10.8, 6.5), sharex=True, sharey=True)
    for axis, column, title in [
        (axes[0], "fold", "Panel A. Random cross-out-of-sample folds"),
        (axes[1], "chronological_fold", "Panel B. Chronological folds"),
    ]:
        axis.plot(observed["month"], observed["sentiment"], color="#888888", alpha=0.45)
        for fold, color in enumerate(colors):
            rows = observed.loc[observed[column].eq(fold)]
            axis.scatter(rows["month"], rows["sentiment"], color=color, s=22,
                         label=f"Fold {fold + 1}")
        axis.axhline(0, color="#555555", linewidth=0.8)
        axis.set(title=title, ylabel="Sentiment proxy")
    axes[0].legend(ncol=3, frameon=False, loc="upper left")
    axes[1].set(xlabel="Formation month")
    figure.suptitle("Figure 2 proxy: model folds over Korean sentiment", fontsize=13)
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _figure_04(predictions: pd.DataFrame, output: Path) -> None:
    valid = predictions.dropna(subset=["prediction", "target_abnormal_return"])
    months = valid.groupby("month").size().sort_index()
    representative_month = months.index[len(months) // 2]
    sample = _assign_deciles(valid.loc[valid["month"].eq(representative_month)])

    figure, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), sharey=True)
    for axis, decile, title in [
        (axes[0], 1, "Bottom prediction decile"),
        (axes[1], 10, "Top prediction decile"),
    ]:
        group = sample.loc[sample["decile"].eq(decile)].sort_values("prediction")
        weighted = prediction_weights(group, decile).to_numpy() * 100
        equal = np.repeat(100 / len(group), len(group))
        x = np.arange(1, len(group) + 1)
        axis.plot(x, weighted, color="#2166ac", label="Prediction weighted")
        axis.plot(x, equal, color="#b2182b", linestyle="--", label="Equal weighted")
        axis.set(title=title, xlabel="Funds sorted by prediction")
    axes[0].set_ylabel("Portfolio weight (%)")
    axes[0].legend(frameon=False)
    figure.suptitle(
        f"Figure 4 proxy: extreme-decile weights ({pd.Timestamp(representative_month):%Y-%m})",
        fontsize=13,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _figure_08(portfolios: pd.DataFrame, output: Path) -> None:
    frame = portfolios.copy()
    frame["month"] = pd.to_datetime(frame["month"])
    figure, axis = plt.subplots(figsize=(10.8, 5.2))
    axis.plot(
        frame["month"], frame["long_short_prediction"].cumsum() * 100,
        color="#2166ac", linewidth=2, label="Prediction weighted",
    )
    axis.plot(
        frame["month"], frame["long_short_equal"].cumsum() * 100,
        color="#b2182b", linestyle="--", linewidth=1.8, label="Equal weighted",
    )
    axis.axhline(0, color="#555555", linewidth=0.8)
    axis.set(
        title="Figure 8 partial proxy: cumulative long-short abnormal return",
        xlabel="Formation month (return realized in the following month)",
        ylabel="Cumulative arithmetic abnormal return (%)",
    )
    axis.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    axis.legend(frameon=False)
    figure.text(
        0.01, 0.01,
        "Only the flow + F_r12_2 + sentiment information set is available; this is not the paper's all-information-set Figure 8.",
        fontsize=8.5, color="#555555",
    )
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _figure_14(predictions: pd.DataFrame, output: Path) -> None:
    frame = predictions.dropna(
        subset=["prediction", "rank_flow", "rank_F_r12_2", "sentiment"]
    ).copy()
    bins = np.linspace(-0.5, 0.5, 6)
    frame["flow_bin"] = pd.cut(
        frame["rank_flow"], bins, labels=False, include_lowest=True
    )
    frame["momentum_bin"] = pd.cut(
        frame["rank_F_r12_2"], bins, labels=False, include_lowest=True
    )
    month_sentiment = frame[["month", "sentiment"]].drop_duplicates("month")
    month_sentiment["sentiment_state"] = pd.qcut(
        month_sentiment["sentiment"], 3, labels=["Low", "Medium", "High"]
    )
    frame = frame.merge(
        month_sentiment[["month", "sentiment_state"]],
        on="month", how="left", validate="many_to_one",
    )
    surfaces = []
    for state in ["Low", "Medium", "High"]:
        surface = (
            frame.loc[frame["sentiment_state"].eq(state)]
            .pivot_table(
                values="prediction", index="momentum_bin", columns="flow_bin",
                aggfunc="mean",
            )
            .reindex(index=range(5), columns=range(5))
            * 100
        )
        surfaces.append(surface)
    bound = max(float(np.nanmax(np.abs(surface.to_numpy()))) for surface in surfaces)
    norm = TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound)

    figure, axes = plt.subplots(
        1, 3, figsize=(13.2, 4.8), sharex=True, sharey=True, layout="constrained"
    )
    image = None
    for axis, state, surface in zip(
        axes, ["Low", "Medium", "High"], surfaces, strict=True
    ):
        image = axis.imshow(
            surface.to_numpy(), origin="lower", cmap="RdBu_r", norm=norm,
            aspect="auto",
        )
        for row in range(5):
            for column in range(5):
                value = surface.iloc[row, column]
                if pd.notna(value):
                    text_color = "white" if abs(value) > bound * 0.55 else "#222222"
                    axis.text(
                        column, row, f"{value:.2f}", ha="center", va="center",
                        fontsize=8, color=text_color,
                    )
        axis.set(
            title=f"{state} sentiment", xlabel="Flow quintile",
            xticks=range(5), xticklabels=range(1, 6),
            yticks=range(5), yticklabels=range(1, 6),
        )
    axes[0].set_ylabel("F_r12_2 momentum quintile")
    if image is not None:
        colorbar = figure.colorbar(image, ax=axes, fraction=0.025, pad=0.02)
        colorbar.set_label("Mean OOS predicted abnormal return (%)")
    figure.suptitle(
        "Figure 14 proxy: flow-momentum prediction surface by sentiment state",
        fontsize=13,
    )
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def generate_proxy_outputs(
    *, predictions_path: Path, sentiment_path: Path, activity_path: Path,
    output_root: Path, random_seed: int,
) -> list[Path]:
    """Generate Table 7 comparison and all figures supported by the proxy run."""

    predictions = pd.read_parquet(predictions_path)
    portfolios = form_prediction_portfolios(predictions)
    sentiment = pd.read_csv(sentiment_path)
    activity = pd.read_csv(activity_path)
    tables = output_root / "tables"
    figures = output_root / "figures" / "parsimonious_proxy"
    manifests = output_root / "manifests"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    portfolios_path = tables / "table_07_parsimonious_proxy_portfolios.csv"
    summary_path = tables / "table_07_parsimonious_proxy_summary.csv"
    comparison_path = tables / "table_07_us_korea_comparison.csv"
    portfolios.to_csv(portfolios_path, index=False, encoding="utf-8")
    summary = compute_table_7_summary(portfolios)
    summary.to_csv(summary_path, index=False, encoding="utf-8")
    build_us_korea_comparison(summary).to_csv(
        comparison_path, index=False, encoding="utf-8"
    )
    outputs = [
        portfolios_path,
        summary_path,
        comparison_path,
        figures / "fig_01_sentiment_activity_proxy.png",
        figures / "fig_02_proxy_fold_assignment.png",
        figures / "fig_04_proxy_portfolio_weights.png",
        figures / "fig_08_parsimonious_proxy_long_short.png",
        figures / "fig_14_parsimonious_proxy_surface.png",
    ]
    _apply_style()
    _figure_01(sentiment, activity, outputs[3])
    _figure_02(predictions, sentiment, outputs[4], random_seed)
    _figure_04(predictions, outputs[5])
    _figure_08(portfolios, outputs[6])
    _figure_14(predictions, outputs[7])
    write_manifest(
        manifests / "parsimonious_proxy_outputs.json",
        {
            "kind": "parsimonious_proxy_comparison_and_figures",
            "inputs": {
                "predictions": {"path": str(predictions_path), "sha256": sha256(predictions_path)},
                "sentiment": {"path": str(sentiment_path), "sha256": sha256(sentiment_path)},
                "activity": {"path": str(activity_path), "sha256": sha256(activity_path)},
            },
            "outputs": [{"path": str(path), "sha256": sha256(path)} for path in outputs],
            "published_us_source": "Kaniel et al. (2023), JFE, Table 7",
            "limitations": [
                "Figures are proxy or partial replications unless explicitly labeled otherwise.",
                "The Korean estimation window contains only 45 realized portfolio months.",
                "Sentiment is an incomplete ECOS-only proxy and factors are non-PIT sensitivity data.",
            ],
        },
    )
    return outputs
