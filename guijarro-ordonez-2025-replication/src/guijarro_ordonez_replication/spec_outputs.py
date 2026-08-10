"""Generate non-empirical paper figures and appendix tables from stated specs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .characteristics import CHARACTERISTIC_COLUMNS


def _flow_figure(
    path: Path,
    title: str,
    labels: list[str],
    *,
    subtitle: str | None = None,
) -> None:
    figure, axis = plt.subplots(figsize=(max(11, 1.9 * len(labels)), 3.2))
    axis.set_xlim(0, len(labels))
    axis.set_ylim(0, 1)
    axis.axis("off")
    for index, label in enumerate(labels):
        axis.text(
            index + 0.5,
            0.5,
            label,
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "black"},
        )
        if index:
            axis.annotate(
                "",
                xy=(index + 0.15, 0.5),
                xytext=(index - 0.15, 0.5),
                arrowprops={"arrowstyle": "->", "linewidth": 1.3},
            )
    axis.set_title(title + (f"\n{subtitle}" if subtitle else ""))
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _characteristic_table() -> pd.DataFrame:
    categories = (
        ["Past returns"] * 6
        + ["Investment"] * 4
        + ["Profitability"] * 11
        + ["Intangibles"] * 4
        + ["Value"] * 10
        + ["Trading frictions"] * 11
    )
    if len(categories) != len(CHARACTERISTIC_COLUMNS):
        raise AssertionError("characteristic category mapping must contain 46 rows")
    return pd.DataFrame(
        {
            "number": np.arange(1, 47),
            "characteristic": CHARACTERISTIC_COLUMNS,
            "category": categories,
        }
    )


def build_spec_outputs(output_directory: Path) -> dict[str, object]:
    """Build Figures 1-4/A.1 and Tables A.I-A.II without empirical inputs."""

    output_directory.mkdir(parents=True, exist_ok=True)
    _flow_figure(
        output_directory / "fig_01_conceptual_arbitrage_model.png",
        "Conceptual arbitrage model",
        [
            "Last L cumulative\nresidual returns",
            "Signal extraction\nθ(·)",
            "Allocation\nwε(·)",
            "Next-day residual\nportfolio weight",
        ],
    )

    figure, axes = plt.subplots(1, 4, figsize=(11, 3), sharey=True)
    patterns = {
        "Upward trend": [0, 0.5, 1],
        "Downward trend": [1, 0.5, 0],
        "Up reversal": [1, 0, 1],
        "Down reversal": [0, 1, 0],
    }
    for axis, (name, values) in zip(axes, patterns.items(), strict=True):
        axis.plot([1, 2, 3], values, marker="o")
        axis.set(title=name, xticks=[1, 2, 3], xlabel="Local day")
    axes[0].set_ylabel("Normalized cumulative residual")
    figure.suptitle("Examples of three-day local filters")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_02_examples_local_filters.png", dpi=180)
    plt.close(figure)

    _flow_figure(
        output_directory / "fig_03_convolutional_architecture.png",
        "Convolutional network architecture",
        [
            "L × 1 cumulative\nresidual path",
            "Instance\nnormalization",
            "Causal Conv1D\n1 → 8, kernel 2",
            "ReLU + instance\nnormalization",
            "Causal Conv1D\n8 → 8, kernel 2",
            "ReLU + skip-add\nnormalized input",
            "L × 8 local\npattern features",
        ],
        subtitle="Two convolutions imply a three-day receptive field",
    )
    _flow_figure(
        output_directory / "fig_04_transformer_architecture.png",
        "Transformer network architecture",
        [
            "L × 8 CNN\nfeatures",
            "4 attention\nheads",
            "Add & normalize",
            "16-unit\nfeedforward layer",
            "Linear allocation\nweight",
        ],
    )
    _flow_figure(
        output_directory / "fig_a01_feedforward_architecture.png",
        "Feedforward network architecture",
        [
            "30 Fourier\nfeatures",
            "16 units\nReLU + dropout",
            "8 units\nReLU + dropout",
            "4 units\nReLU + dropout",
            "Linear weight",
        ],
    )

    characteristics = _characteristic_table()
    characteristics.to_csv(output_directory / "table_a01_characteristics.csv", index=False)
    hyperparameters = pd.DataFrame(
        [
            ("D", "CNN filters", "8, 16", "8"),
            ("ATT", "Attention heads", "2, 4", "4"),
            ("HDN", "Transformer hidden units", "2D, 3D", "2D"),
            ("DRP", "Transformer dropout", "0.25, 0.5", "0.25"),
            ("Dsize", "Convolution filter size", "2", "2"),
            ("LKB", "Residual lookback days", "30", "30"),
            ("WDW", "Rolling training days", "1000", "1000"),
            ("RTFQ", "Retraining frequency days", "125", "125"),
            ("BTCH", "Batch size days", "125", "125"),
            ("LR", "Learning rate", "0.001", "0.001"),
            ("EPCH", "Optimization epochs", "100", "100"),
            ("OPT", "Optimizer", "Adam", "Adam"),
        ],
        columns=["notation", "hyperparameter", "candidates", "chosen"],
    )
    hyperparameters.to_csv(output_directory / "table_a02_hyperparameters.csv", index=False)
    return {
        "classification": "generated from paper specification, not empirical data",
        "figures": 5,
        "tables": 2,
        "characteristics": len(characteristics),
        "hyperparameters": len(hyperparameters),
    }
