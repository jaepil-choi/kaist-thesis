"""CNN benchmark interpretation figures corresponding to paper Figures 14-19."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from .policies import CNNTransformer
from .trading import ResidualPanel, cumulative_windows


def load_cnn_checkpoint(path: Path, *, lookback: int = 30) -> CNNTransformer:
    """Load one locally trained benchmark checkpoint for analysis."""

    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model = CNNTransformer(random_seed=0, lookback=lookback)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def cnn_states(
    model: CNNTransformer, signal: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return CNN activations and per-head self-attention weights."""

    if signal.ndim != 2:
        raise ValueError("signal must be batch-by-lookback")
    convolution = signal.reshape(signal.shape[0], 1, signal.shape[1])
    for block in model.blocks:
        convolution = block(convolution)
    sequence = convolution.permute(2, 0, 1)
    _, attention = model.encoder.self_attn(
        sequence,
        sequence,
        sequence,
        need_weights=True,
        average_attn_weights=False,
    )
    return convolution, attention


def _normalized_weights_for_day(
    model: CNNTransformer,
    windows: np.ndarray,
    selected: np.ndarray,
    panel: ResidualPanel,
    day_index: int,
    lookback: int,
) -> np.ndarray:
    window_index = day_index - lookback
    valid = selected[window_index]
    raw = np.zeros(len(panel.tickers), dtype=float)
    with torch.no_grad():
        raw[valid] = model(
            torch.as_tensor(windows[window_index, valid], dtype=torch.float32)
        ).numpy()
    raw_asset = raw - (raw @ panel.left[day_index]) @ panel.right[day_index].T
    gross = np.abs(raw_asset).sum()
    return raw / (gross + 1e-8)


def _local_patterns(model: CNNTransformer, iterations: int = 120) -> np.ndarray:
    """Find three-day inputs that maximize each final CNN channel."""

    channels = model.filter_numbers[-1]
    patterns = np.zeros((channels, 3), dtype=float)
    for channel in range(channels):
        candidate = torch.randn(1, 3, requires_grad=True)
        optimizer = torch.optim.Adam([candidate], lr=0.05)
        for _ in range(iterations):
            output = candidate.reshape(1, 1, 3)
            for block in model.blocks:
                output = block(output)
            loss = -output[0, channel, -1] + 0.01 * candidate.square().mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        values = candidate.detach().numpy().ravel()
        scale = np.max(np.abs(values))
        patterns[channel] = values / (scale if scale else 1)
    return patterns


def build_interpretability_figures(
    panel: ResidualPanel,
    checkpoint_path: Path,
    output_directory: Path,
    *,
    lookback: int = 30,
    training_days: int = 1000,
    test_days: int = 125,
) -> dict[str, object]:
    """Build Korean-data versions of Figures 14-19 using one rolling model."""

    model = load_cnn_checkpoint(checkpoint_path, lookback=lookback)
    windows, selected = cumulative_windows(panel.residuals, panel.observed, lookback)
    start = training_days
    stop = min(start + test_days, len(panel.dates))
    valid_counts = selected[start - lookback : stop - lookback].sum(axis=0)
    ticker_index = int(np.argmax(valid_counts))
    valid_days = [
        day
        for day in range(start, stop)
        if selected[day - lookback, ticker_index]
    ]
    if len(valid_days) < 4:
        raise ValueError("no representative residual has four valid OOS windows")
    output_directory.mkdir(parents=True, exist_ok=True)

    sample_days = np.linspace(0, len(valid_days) - 1, 4, dtype=int)
    figure, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for axis, position in zip(axes.ravel(), sample_days, strict=True):
        day = valid_days[position]
        signal = windows[day - lookback, ticker_index]
        normalized = _normalized_weights_for_day(
            model, windows, selected, panel, day, lookback
        )[ticker_index]
        axis.plot(np.arange(1, lookback + 1), signal)
        axis.set_title(
            f"{panel.dates[day].date()}  w={normalized:.4f}, "
            f"ε={panel.residuals[day, ticker_index]:.4f}"
        )
        axis.set(xlabel="Lookback day", ylabel="Cumulative residual")
    figure.suptitle(f"Allocation and return examples: {panel.tickers[ticker_index]}")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_14_allocation_return_examples.png", dpi=180)
    plt.close(figure)

    patterns = _local_patterns(model)
    figure, axes = plt.subplots(2, 4, figsize=(12, 6), sharey=True)
    for channel, axis in enumerate(axes.ravel()):
        axis.plot([1, 2, 3], patterns[channel], marker="o")
        axis.set(title=f"Pattern {channel + 1}", xticks=[1, 2, 3])
    figure.suptitle("Local three-day patterns maximizing CNN channels")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_15_local_basic_patterns.png", dpi=180)
    plt.close(figure)

    time_grid = np.arange(lookback)
    frequencies = (1, 2, 3, 8, 14)
    figure, axes = plt.subplots(len(frequencies), 2, figsize=(11, 12))
    for row, frequency in enumerate(frequencies):
        sinusoid = np.sin(2 * np.pi * frequency * time_grid / lookback)
        _, attention = cnn_states(
            model, torch.as_tensor(sinusoid[None, :], dtype=torch.float32)
        )
        axes[row, 0].plot(time_grid + 1, sinusoid)
        for head in range(attention.shape[1]):
            axes[row, 1].plot(
                time_grid + 1,
                attention[0, head, -1].detach().numpy(),
                label=f"Head {head + 1}",
            )
        axes[row, 0].set_ylabel(f"ω={frequency}/30")
    axes[0, 0].set_title("Sinusoidal input")
    axes[0, 1].set_title("Last-query attention weights")
    axes[0, 1].legend(ncol=2)
    figure.tight_layout()
    figure.savefig(output_directory / "fig_16_sinusoidal_attention.png", dpi=180)
    plt.close(figure)

    representative_day = valid_days[len(valid_days) // 2]
    signal = torch.as_tensor(
        windows[representative_day - lookback, ticker_index][None, :],
        dtype=torch.float32,
    )
    convolution, attention = cnn_states(model, signal)
    figure, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    axes[0].plot(time_grid + 1, signal.numpy().ravel())
    axes[0].set_ylabel("Cumulative residual")
    for channel in range(convolution.shape[1]):
        axes[1].plot(
            time_grid + 1,
            convolution[0, channel].detach().numpy(),
            label=str(channel + 1),
        )
    for head in range(attention.shape[1]):
        axes[2].plot(
            time_grid + 1,
            attention[0, head, -1].detach().numpy(),
            label=f"Head {head + 1}",
        )
    axes[1].set_ylabel("CNN activation")
    axes[2].set(xlabel="Lookback day", ylabel="Attention weight")
    axes[1].legend(ncol=4)
    axes[2].legend(ncol=4)
    figure.suptitle(
        f"CNN+Transformer structure: {panel.tickers[ticker_index]}, "
        f"{panel.dates[representative_day].date()}"
    )
    figure.tight_layout()
    figure.savefig(output_directory / "fig_17_representative_structure.png", dpi=180)
    plt.close(figure)

    timeline_rows = []
    for day in valid_days:
        day_signal = torch.as_tensor(
            windows[day - lookback, ticker_index][None, :], dtype=torch.float32
        )
        convolution, attention = cnn_states(model, day_signal)
        normalized = _normalized_weights_for_day(
            model, windows, selected, panel, day, lookback
        )[ticker_index]
        lag = np.arange(lookback, dtype=float)
        average_attention = attention[0, :, -1].mean(dim=0).detach().numpy()
        timeline_rows.append(
            {
                "date": panel.dates[day],
                "allocation": normalized,
                "attention_recency": float(average_attention @ lag),
                "mean_abs_cnn_activation": float(
                    convolution.abs().mean().detach()
                ),
            }
        )
    timeline = pd.DataFrame(timeline_rows)
    timeline.to_csv(output_directory / "fig_18_structure_timeline.csv", index=False)
    figure, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(timeline["date"], timeline["allocation"])
    axes[1].plot(timeline["date"], timeline["attention_recency"])
    axes[2].plot(timeline["date"], timeline["mean_abs_cnn_activation"])
    axes[0].set_ylabel("Residual allocation")
    axes[1].set_ylabel("Attention day index")
    axes[2].set_ylabel("Mean |CNN activation|")
    figure.suptitle(f"Model structure over time: {panel.tickers[ticker_index]}")
    figure.tight_layout()
    figure.savefig(output_directory / "fig_18_structure_over_time.png", dpi=180)
    plt.close(figure)

    available = np.argwhere(selected[start - lookback : stop - lookback])
    available = available[: min(512, len(available))]
    gradient_inputs = torch.as_tensor(
        np.stack([windows[time, asset] for time, asset in available]),
        dtype=torch.float32,
    ).requires_grad_(True)
    model(gradient_inputs).sum().backward()
    importance = gradient_inputs.grad.abs().mean(dim=0).detach().numpy()
    importance /= importance.sum()
    pd.DataFrame(
        {"lookback_day": np.arange(1, lookback + 1), "importance": importance}
    ).to_csv(output_directory / "fig_19_input_gradient_importance.csv", index=False)
    figure, axis = plt.subplots(figsize=(9, 4))
    axis.bar(np.arange(1, lookback + 1), importance)
    axis.set(
        title="Normalized average absolute gradient for allocation weight",
        xlabel="Lookback day",
        ylabel="Importance share",
    )
    figure.tight_layout()
    figure.savefig(output_directory / "fig_19_variable_importance.png", dpi=180)
    plt.close(figure)

    audit = {
        "classification": "Korean PCA5 CNN interpretability variant",
        "checkpoint": str(checkpoint_path),
        "checkpoint_epoch": int(
            torch.load(checkpoint_path, map_location="cpu", weights_only=False)["epoch"]
        )
        + 1,
        "model_subperiod": 0,
        "analysis_start": panel.dates[start].date().isoformat(),
        "analysis_end": panel.dates[stop - 1].date().isoformat(),
        "representative_ticker": panel.tickers[ticker_index],
        "gradient_observations": len(available),
        "method_difference": (
            "Korean data and locally retrained checkpoint replace the paper's U.S. IPCA5 model"
        ),
    }
    (output_directory / "interpretability_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit
