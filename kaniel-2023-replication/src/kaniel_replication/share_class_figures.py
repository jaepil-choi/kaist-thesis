"""Create diagnostic figures for the share-class consolidation decision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

from .provenance import sha256, write_manifest


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402


DECISION_ORDER = [
    "representative_row_preferred",
    "separate_return_basis_required",
    "class_aggregate_only",
    "insufficient_evidence",
    "manual_review",
]
DECISION_LABELS = {
    "representative_row_preferred": "Representative row",
    "separate_return_basis_required": "Separate return basis",
    "class_aggregate_only": "Class aggregate only",
    "insufficient_evidence": "Insufficient evidence",
    "manual_review": "Manual review",
}


def _apply_style() -> None:
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.25,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.size": 10,
        }
    )


def _validate_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def _tna_agreement_figure(
    comparison: pd.DataFrame,
    output: Path,
    tna_tolerance_fraction: float,
) -> None:
    errors = comparison["tna_difference_fraction"].dropna().clip(lower=0)
    thresholds = np.array([0.0, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20])
    agreement = np.array([errors.le(value).mean() for value in thresholds])
    tolerance_rate = float(errors.le(tna_tolerance_fraction).mean())

    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    axis.plot(
        thresholds * 100,
        agreement * 100,
        color="#2166ac",
        marker="o",
        linewidth=2,
    )
    axis.axvline(
        tna_tolerance_fraction * 100,
        color="#b2182b",
        linestyle="--",
        linewidth=1.5,
    )
    axis.scatter(
        [tna_tolerance_fraction * 100],
        [tolerance_rate * 100],
        color="#b2182b",
        zorder=3,
    )
    axis.annotate(
        f"{tolerance_rate:.1%} within ±{tna_tolerance_fraction:.0%}",
        xy=(tna_tolerance_fraction * 100, tolerance_rate * 100),
        xytext=(18, -28),
        textcoords="offset points",
        color="#7f0000",
    )
    axis.set(
        title="Representative TNA agrees with the sum of share classes",
        xlabel="Maximum absolute TNA difference",
        ylabel="Share of comparable group-months",
        xlim=(0, thresholds.max() * 100),
        ylim=(0, 100),
    )
    axis.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    axis.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    figure.text(
        0.01,
        0.01,
        (
            f"N = {len(errors):,} group-months. The curve is capped at "
            "20% TNA difference; observations beyond the cap remain in N."
        ),
        fontsize=8.5,
        color="#555555",
    )
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _return_gap_figure(
    comparison: pd.DataFrame,
    output: Path,
    return_tolerance_bps: float,
) -> None:
    signed = (
        comparison["representative_return"] - comparison["class_weighted_return"]
    ).dropna() * 10_000
    central_limit = 50.0
    central = signed.loc[signed.between(-central_limit, central_limit)]
    outside = len(signed) - len(central)
    median = float(signed.median())
    higher_rate = float(signed.gt(0).mean())
    match_rate = float(signed.abs().le(return_tolerance_bps).mean())

    figure, axes = plt.subplots(1, 2, figsize=(11.0, 4.7))
    histogram, _, _ = axes[0].hist(
        central,
        bins=np.linspace(-central_limit, central_limit, 81),
        color="#4393c3",
        alpha=0.85,
    )
    axes[0].axvline(0, color="#444444", linewidth=1)
    axes[0].axvline(median, color="#b2182b", linestyle="--", linewidth=1.5)
    axes[0].annotate(
        f"Median = {median:+.2f} bp",
        xy=(median, histogram.max() * 0.82),
        xytext=(12, 0),
        textcoords="offset points",
        color="#7f0000",
    )
    axes[0].set(
        title="Signed monthly return gap",
        xlabel="Representative − lag-TNA-weighted classes (bp)",
        ylabel="Group-month count",
        xlim=(-central_limit, central_limit),
    )

    absolute = np.sort(signed.abs().to_numpy())
    cumulative = np.arange(1, len(absolute) + 1) / len(absolute)
    display = absolute <= 30
    axes[1].plot(
        absolute[display],
        cumulative[display] * 100,
        color="#2166ac",
        linewidth=2,
    )
    axes[1].axvline(
        return_tolerance_bps,
        color="#b2182b",
        linestyle="--",
        linewidth=1.5,
    )
    axes[1].scatter(
        [return_tolerance_bps],
        [match_rate * 100],
        color="#b2182b",
        zorder=3,
    )
    axes[1].annotate(
        f"{match_rate:.1%} within ±{return_tolerance_bps:.0f} bp",
        xy=(return_tolerance_bps, match_rate * 100),
        xytext=(18, 10),
        textcoords="offset points",
        color="#7f0000",
    )
    axes[1].set(
        title="Absolute-gap agreement rate",
        xlabel="Maximum absolute return gap (bp)",
        ylabel="Share of comparable group-months",
        xlim=(0, 30),
        ylim=(0, 100),
    )
    axes[1].yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    figure.suptitle(
        (
            "Representative returns are systematically higher than "
            "share-class weighted returns"
        ),
        fontsize=13,
    )
    figure.text(
        0.01,
        0.01,
        (
            f"N = {len(signed):,}; representative return is higher in "
            f"{higher_rate:.1%} of months. Left panel shows ±{central_limit:.0f} bp; "
            f"{outside:,} observations lie outside that range."
        ),
        fontsize=8.5,
        color="#555555",
    )
    figure.tight_layout(rect=(0, 0.06, 1, 0.94))
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _decision_figure(diagnostics: pd.DataFrame, output: Path) -> None:
    counts = (
        diagnostics["consolidation_decision"]
        .value_counts()
        .reindex(DECISION_ORDER, fill_value=0)
    )
    labels = [DECISION_LABELS[value] for value in counts.index]
    y = np.arange(len(counts))
    colors = ["#2166ac", "#ef8a62", "#67a9cf", "#999999", "#b2182b"]

    figure, axis = plt.subplots(figsize=(8.8, 4.8))
    bars = axis.barh(y, counts.to_numpy(), color=colors, alpha=0.9)
    axis.set_yticks(y, labels)
    axis.invert_yaxis()
    axis.set(
        title="Share-class groups by consolidation decision",
        xlabel="Representative-fund groups",
    )
    axis.bar_label(
        bars,
        labels=[f"{count:,} ({count / len(diagnostics):.1%})" for count in counts],
        padding=4,
    )
    axis.set_xlim(0, max(counts.max() * 1.28, 1))
    figure.text(
        0.01,
        0.01,
        (
            f"N = {len(diagnostics):,} representative groups. Only "
            "'Representative row' and 'Class aggregate only' fix one return basis."
        ),
        fontsize=8.5,
        color="#555555",
    )
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def generate_share_class_figures(
    comparison_path: Path,
    diagnostics_path: Path,
    summary_path: Path,
    output_dir: Path,
) -> list[Path]:
    """Generate the three diagnostics used to choose a consolidation rule."""

    comparison = pd.read_parquet(comparison_path)
    diagnostics = pd.read_csv(diagnostics_path)
    with summary_path.open(encoding="utf-8") as handle:
        summary: dict[str, Any] = json.load(handle)
    _validate_columns(
        comparison,
        {
            "tna_difference_fraction",
            "representative_return",
            "class_weighted_return",
        },
        "Share-class month comparison",
    )
    _validate_columns(
        diagnostics,
        {"consolidation_decision"},
        "Share-class group diagnostics",
    )
    if comparison.empty or diagnostics.empty:
        raise ValueError("Share-class diagnostics are empty")

    thresholds = summary["thresholds"]
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        output_dir / "share_class_tna_agreement.png",
        output_dir / "share_class_return_gap.png",
        output_dir / "share_class_consolidation_decisions.png",
    ]
    _apply_style()
    _tna_agreement_figure(
        comparison,
        outputs[0],
        float(thresholds["tna_tolerance_fraction"]),
    )
    _return_gap_figure(
        comparison,
        outputs[1],
        float(thresholds["return_tolerance_bps"]),
    )
    _decision_figure(diagnostics, outputs[2])
    payload = {
        "manifest_version": 1,
        "inputs": {
            "comparison": {
                "path": str(comparison_path.resolve()),
                "sha256": sha256(comparison_path),
            },
            "diagnostics": {
                "path": str(diagnostics_path.resolve()),
                "sha256": sha256(diagnostics_path),
            },
            "summary": {
                "path": str(summary_path.resolve()),
                "sha256": sha256(summary_path),
            },
        },
        "outputs": [
            {"path": str(path.resolve()), "sha256": sha256(path)} for path in outputs
        ],
    }
    write_manifest(output_dir / "share_class_figures.manifest.json", payload)
    return outputs
