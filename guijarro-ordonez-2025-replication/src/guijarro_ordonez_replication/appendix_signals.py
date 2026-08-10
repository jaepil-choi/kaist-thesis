"""Appendix signal illustrations for CNN, Fourier, and OU policies."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from .interpretability import cnn_states, load_cnn_checkpoint
from .policies import FourierFFN, OUThreshold
from .trading import ResidualPanel, cumulative_windows, packed_fourier_windows


def load_fourier_checkpoint(path: Path, *, lookback: int = 30) -> FourierFFN:
    """Load a locally trained Fourier+FFN checkpoint."""

    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model = FourierFFN(
        random_seed=0,
        lookback=lookback,
        hidden_units=(lookback, 16, 8, 4),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def illustrative_policy_paths(
    panel: ResidualPanel,
    cnn_checkpoint: Path,
    fourier_checkpoint: Path,
    *,
    lookback: int = 30,
    training_days: int = 1000,
    evaluation_days: int = 30,
) -> tuple[list[dict[str, object]], list[str]]:
    """Evaluate all three paper policies on two single-residual examples."""

    cnn = load_cnn_checkpoint(cnn_checkpoint, lookback=lookback)
    fourier = load_fourier_checkpoint(fourier_checkpoint, lookback=lookback)
    ou = OUThreshold(lookback=lookback).eval()
    windows, selected = cumulative_windows(panel.residuals, panel.observed, lookback)
    start = training_days
    stop = min(start + evaluation_days, len(panel.dates))
    complete = selected[start - lookback : stop - lookback].all(axis=0)
    candidates = np.flatnonzero(complete)
    if len(candidates) < 2:
        raise ValueError("two complete residual examples are unavailable")
    residual_scale = np.nanstd(panel.residuals[start:stop], axis=0)
    ranked = candidates[np.argsort(-residual_scale[candidates])[:2]]
    models = ("CNN+Transformer", "Fourier+FFN", "OU+Threshold")
    rows: list[dict[str, object]] = []
    with torch.no_grad():
        for example, ticker_index in enumerate(ranked, start=1):
            for day in range(start, stop):
                window = windows[day - lookback, ticker_index]
                tensor = torch.as_tensor(window[None, :], dtype=torch.float32)
                fourier_tensor = torch.as_tensor(
                    packed_fourier_windows(window[None, None, :])[:, 0],
                    dtype=torch.float32,
                )
                raw_signals = (
                    float(cnn(tensor).item()),
                    float(fourier(fourier_tensor).item()),
                    float(ou(tensor).item()),
                )
                for model_name, raw_signal in zip(models, raw_signals, strict=True):
                    allocation = float(np.sign(raw_signal))
                    rows.append(
                        {
                            "example": example,
                            "date": panel.dates[day],
                            "ticker": panel.tickers[ticker_index],
                            "model": model_name,
                            "cumulative_residual_signal": float(window[-1]),
                            "raw_policy_signal": raw_signal,
                            "allocation": allocation,
                            "strategy_return": allocation
                            * panel.residuals[day, ticker_index],
                        }
                    )
    return rows, [panel.tickers[index] for index in ranked]


def _plot_example(frame, path: Path, title: str) -> None:
    models = ("CNN+Transformer", "Fourier+FFN", "OU+Threshold")
    figure, axes = plt.subplots(3, 3, figsize=(14, 10), sharex="col")
    for row, model_name in enumerate(models):
        sample = frame.loc[frame["model"].eq(model_name)].sort_values("date")
        axes[row, 0].plot(sample["date"], sample["cumulative_residual_signal"])
        twin = axes[row, 0].twinx()
        twin.step(sample["date"], sample["allocation"], color="tab:orange", alpha=0.6)
        twin.set_ylim(-1.2, 1.2)
        axes[row, 1].plot(sample["date"], sample["raw_policy_signal"])
        axes[row, 2].plot(sample["date"], (1 + sample["strategy_return"]).cumprod() - 1)
        axes[row, 0].set_ylabel(model_name)
        for axis in axes[row]:
            axis.tick_params(axis="x", rotation=25)
            axis.xaxis.set_major_locator(plt.MaxNLocator(4))
    axes[0, 0].set_title("Cumulative residual and sign allocation")
    axes[0, 1].set_title("Raw policy signal")
    axes[0, 2].set_title("Single-residual cumulative return")
    figure.suptitle(title)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def build_appendix_signal_figures(
    panel: ResidualPanel,
    cnn_checkpoint: Path,
    fourier_checkpoint: Path,
    output_directory: Path,
    *,
    lookback: int = 30,
) -> dict[str, object]:
    """Build Korean variants of Appendix Figures A.2-A.4."""

    output_directory.mkdir(parents=True, exist_ok=True)
    rows, tickers = illustrative_policy_paths(
        panel, cnn_checkpoint, fourier_checkpoint, lookback=lookback
    )
    frame = pd.DataFrame(rows)
    frame.to_csv(output_directory / "figures_a02_a03_policy_paths.csv", index=False)
    for example, figure_name in ((1, "fig_a02_policy_signals.png"), (2, "fig_a03_policy_signals.png")):
        _plot_example(
            frame.loc[frame["example"].eq(example)],
            output_directory / figure_name,
            f"Single-residual policy illustration: {tickers[example - 1]}",
        )

    cnn = load_cnn_checkpoint(cnn_checkpoint, lookback=lookback)
    grid = np.arange(lookback)
    frequencies = (2, 28, 8, 14)
    figure, axes = plt.subplots(2, 2, figsize=(12, 7))
    for axis, frequency in zip(axes.ravel(), frequencies, strict=True):
        sinusoid = np.sin(2 * np.pi * frequency * grid / lookback)
        _, attention = cnn_states(
            cnn, torch.as_tensor(sinusoid[None, :], dtype=torch.float32)
        )
        for head in range(attention.shape[1]):
            axis.plot(
                grid + 1,
                attention[0, head, -1].detach().numpy(),
                label=f"Head {head + 1}",
            )
        axis.set(title=f"ω={frequency}/30", xlabel="Lookback day", ylabel="Attention")
    axes[0, 0].legend(ncol=2, fontsize=8)
    figure.tight_layout()
    figure.savefig(output_directory / "fig_a04_additional_sinusoidal_attention.png", dpi=180)
    plt.close(figure)

    audit = {
        "classification": "Korean PCA5 appendix signal variants",
        "representative_tickers": tickers,
        "evaluation_days": 30,
        "allocation_normalization": "sign in {-1, 0, 1}, matching the single-residual illustration",
        "raw_signal_interpretation": (
            "policy pre-normalization scalar; the paper does not publish the private plotting helper"
        ),
        "exact_ipca_figures": "blocked by 240-month IPCA history",
    }
    (output_directory / "appendix_signal_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit
