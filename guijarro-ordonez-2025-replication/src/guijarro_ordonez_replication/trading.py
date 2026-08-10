"""Paper-faithful signal preprocessing and rolling residual trading simulation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray
from torch import nn

from .policies import CNNTransformer, FourierFFN, OUThreshold


FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]
Progress = Callable[[dict[str, object]], None]


@dataclass(frozen=True)
class ResidualPanel:
    """Dense residual panel and the two low-rank composition-matrix terms."""

    dates: pd.DatetimeIndex
    tickers: tuple[str, ...]
    residuals: FloatArray
    left: FloatArray
    right: FloatArray
    observed: BoolArray
    extra_asset_loadings: FloatArray | None = None
    asset_tickers: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SimulationConfig:
    """Published simulation defaults; execution device is a local adaptation."""

    model_name: str = "cnn_transformer"
    objective: str = "sharpe"
    random_seed: int = 0
    lookback_days: int = 30
    training_window_days: int = 1000
    stride_days: int = 125
    epochs: int = 100
    batch_days: int = 125
    learning_rate: float = 0.001
    holding_days: int = 1
    transaction_cost: float = 0.0
    short_holding_cost: float = 0.0
    rolling_retrain: bool = True
    device: str = "cpu"
    checkpoint_directory: Path | None = None
    resume_checkpoints: bool = True

    def validate(self) -> None:
        if self.model_name not in {"cnn_transformer", "fourier_ffn", "ou_threshold"}:
            raise ValueError(f"unsupported model_name: {self.model_name}")
        if self.objective.lower() not in {"sharpe", "meanvar"}:
            raise ValueError(f"unsupported objective: {self.objective}")
        if self.lookback_days < 2:
            raise ValueError("lookback_days must be at least two")
        if self.training_window_days <= self.lookback_days:
            raise ValueError("training window must exceed lookback")
        if min(self.stride_days, self.epochs, self.batch_days) <= 0:
            raise ValueError("stride, epochs, and batch_days must be positive")
        if self.holding_days != 1:
            raise ValueError("the current exact path supports one-day holding only")
        if min(self.transaction_cost, self.short_holding_cost) < 0:
            raise ValueError("trading costs cannot be negative")


@dataclass(frozen=True)
class SimulationResult:
    """Daily out-of-sample strategy observations and an execution audit."""

    daily: pd.DataFrame
    weights: pd.DataFrame
    audit: dict[str, object]


def load_pca_residual_panel(
    residual_path: Path,
    loading_path: Path,
) -> ResidualPanel:
    """Load long-form PCA outputs into a common dense ticker coordinate system."""

    residual_frame = pd.read_parquet(residual_path)
    loading_frame = pd.read_parquet(loading_path)
    residual_required = {"date", "ticker", "residual", "return_observed"}
    if missing := residual_required.difference(residual_frame.columns):
        raise ValueError(f"residual input is missing columns: {sorted(missing)}")
    left_columns = sorted(
        column
        for column in loading_frame
        if column.startswith("standardized_eigenvector_")
    )
    right_columns = sorted(
        column for column in loading_frame if column.startswith("return_loading_")
    )
    if not left_columns or len(left_columns) != len(right_columns):
        raise ValueError("loading input needs matching low-rank factor columns")
    for frame in (residual_frame, loading_frame):
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
        frame["ticker"] = frame["ticker"].astype(str).str.upper()
        if frame.duplicated(["date", "ticker"]).any():
            raise ValueError("PCA inputs contain duplicate date-ticker keys")
    dates = pd.DatetimeIndex(sorted(residual_frame["date"].unique()))
    tickers = tuple(sorted(residual_frame["ticker"].unique()))
    date_codes = pd.Categorical(residual_frame["date"], categories=dates).codes
    ticker_codes = pd.Categorical(residual_frame["ticker"], categories=tickers).codes
    shape = (len(dates), len(tickers))
    residuals = np.zeros(shape, dtype=np.float64)
    observed = np.zeros(shape, dtype=bool)
    residuals[date_codes, ticker_codes] = residual_frame["residual"].to_numpy(float)
    observed[date_codes, ticker_codes] = residual_frame["return_observed"].to_numpy(bool)

    loading_dates = pd.Categorical(loading_frame["date"], categories=dates).codes
    loading_tickers = pd.Categorical(loading_frame["ticker"], categories=tickers).codes
    if np.any(loading_dates < 0) or np.any(loading_tickers < 0):
        raise ValueError("loading keys are not a subset of residual keys")
    rank = len(left_columns)
    low_rank_shape = (*shape, rank)
    left = np.zeros(low_rank_shape, dtype=np.float64)
    right = np.zeros(low_rank_shape, dtype=np.float64)
    left[loading_dates, loading_tickers] = loading_frame[left_columns].to_numpy(float)
    right[loading_dates, loading_tickers] = loading_frame[right_columns].to_numpy(float)
    if not all(np.isfinite(array).all() for array in (residuals, left, right)):
        raise ValueError("PCA arrays must be finite")
    return ResidualPanel(dates, tickers, residuals, left, right, observed)


def load_fama_french_residual_panel(
    residual_path: Path,
    factor_leg_path: Path,
) -> ResidualPanel:
    """Load rolling FF residuals with synthetic factor assets."""

    residual_frame = pd.read_parquet(residual_path)
    leg_frame = pd.read_parquet(factor_leg_path)
    for frame in (residual_frame, leg_frame):
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
        frame["ticker"] = frame["ticker"].astype(str).str.upper()
        if frame.duplicated(["date", "ticker"]).any():
            raise ValueError("Fama-French inputs contain duplicate date-ticker keys")
    leg_columns = [
        column for column in leg_frame if column.startswith("factor_asset_weight_")
    ]
    if not leg_columns:
        raise ValueError("factor-leg input has no factor asset columns")
    dates = pd.DatetimeIndex(sorted(residual_frame["date"].unique()))
    tickers = tuple(sorted(residual_frame["ticker"].unique()))
    date_codes = pd.Categorical(residual_frame["date"], categories=dates).codes
    ticker_codes = pd.Categorical(residual_frame["ticker"], categories=tickers).codes
    shape = (len(dates), len(tickers))
    residuals = np.zeros(shape, dtype=float)
    observed = np.zeros(shape, dtype=bool)
    residuals[date_codes, ticker_codes] = residual_frame["residual"].to_numpy(float)
    observed[date_codes, ticker_codes] = residual_frame["return_observed"].to_numpy(bool)
    leg_dates = pd.Categorical(leg_frame["date"], categories=dates).codes
    leg_tickers = pd.Categorical(leg_frame["ticker"], categories=tickers).codes
    if np.any(leg_dates < 0) or np.any(leg_tickers < 0):
        raise ValueError("factor-leg keys are not a subset of residual keys")
    extra = np.zeros((*shape, len(leg_columns)), dtype=float)
    extra[leg_dates, leg_tickers] = leg_frame[leg_columns].to_numpy(float)
    zeros = np.zeros((*shape, 1), dtype=float)
    factor_names = tuple(
        f"FACTOR::{column.removeprefix('factor_asset_weight_')}"
        for column in leg_columns
    )
    return ResidualPanel(
        dates=dates,
        tickers=tickers,
        residuals=residuals,
        left=zeros,
        right=zeros.copy(),
        observed=observed,
        extra_asset_loadings=extra,
        asset_tickers=(*tickers, *factor_names),
    )


def cumulative_windows(
    residuals: FloatArray,
    observed: BoolArray,
    lookback: int,
) -> tuple[FloatArray, BoolArray]:
    """Return cumulative-sum windows and backward-looking availability masks.

    Row zero uses residual observations ``[0, lookback)`` to trade on date
    ``lookback``. This matches the public code and excludes the traded return.
    """

    values = np.asarray(residuals, dtype=float)
    mask = np.asarray(observed, dtype=bool) & (values != 0)
    if values.ndim != 2 or mask.shape != values.shape:
        raise ValueError("residuals and observed must be matching T-by-N arrays")
    if not 1 < lookback < values.shape[0]:
        raise ValueError("lookback must be between one and sample length")
    windows = np.zeros(
        (values.shape[0] - lookback, values.shape[1], lookback),
        dtype=np.float32,
    )
    selected = np.zeros(windows.shape[:2], dtype=bool)
    for output_index, day_index in enumerate(range(lookback, values.shape[0])):
        valid = mask[day_index - lookback : day_index].all(axis=0)
        selected[output_index] = valid
        if valid.any():
            windows[output_index, valid] = np.cumsum(
                values[day_index - lookback : day_index, valid], axis=0
            ).T
    return windows, selected


def packed_fourier_windows(cumulative: FloatArray) -> FloatArray:
    """Pack rFFT real and interior imaginary terms into ``lookback`` features."""

    windows = np.asarray(cumulative, dtype=np.float32)
    if windows.ndim != 3:
        raise ValueError("cumulative windows must be T-by-N-by-lookback")
    lookback = windows.shape[-1]
    coefficients = np.fft.rfft(windows, axis=-1)
    packed = np.empty_like(windows)
    split = lookback // 2 + 1
    packed[..., :split] = coefficients.real
    packed[..., split:] = coefficients[..., 1:-1].imag
    return packed


def low_rank_asset_weights(
    residual_weights: torch.Tensor,
    left: torch.Tensor,
    right: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Apply ``Phi=I-left@right.T`` and normalize underlying gross exposure."""

    if residual_weights.ndim != 2 or left.ndim != 3 or right.shape != left.shape:
        raise ValueError("invalid residual-weight or low-rank loading shapes")
    if residual_weights.shape != left.shape[:2]:
        raise ValueError("weight and loading coordinates do not match")
    factor_exposure = torch.einsum("tn,tnk->tk", residual_weights, left)
    asset_weights = residual_weights - torch.einsum(
        "tk,tnk->tn", factor_exposure, right
    )
    gross = asset_weights.abs().sum(dim=1, keepdim=True)
    denominator = gross + 1e-8
    return residual_weights / denominator, asset_weights / denominator


def factor_leg_asset_weights(
    residual_weights: torch.Tensor,
    extra_asset_loadings: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Map FF residuals into stock identities plus synthetic factor legs."""

    if residual_weights.ndim != 2 or extra_asset_loadings.ndim != 3:
        raise ValueError("invalid residual-weight or factor-loading shapes")
    if residual_weights.shape != extra_asset_loadings.shape[:2]:
        raise ValueError("weight and factor-loading coordinates do not match")
    factor_weights = torch.einsum(
        "tn,tnk->tk", residual_weights, extra_asset_loadings
    )
    unnormalized = torch.cat((residual_weights, factor_weights), dim=1)
    gross = unnormalized.abs().sum(dim=1, keepdim=True)
    denominator = gross + 1e-8
    return residual_weights / denominator, unnormalized / denominator


def annualized_statistics(returns: torch.Tensor) -> tuple[torch.Tensor, ...]:
    """Return paper-compatible annual mean, volatility, and Sharpe ratio."""

    annual_mean = returns.mean() * 252
    annual_volatility = returns.std() * torch.sqrt(
        torch.tensor(252.0, device=returns.device)
    )
    return annual_mean, annual_volatility, annual_mean / (annual_volatility + 1e-8)


def objective_loss(returns: torch.Tensor, objective: str) -> torch.Tensor:
    """Published Sharpe or mean-minus-volatility training objective."""

    mean, volatility, sharpe = annualized_statistics(returns)
    if objective.lower() == "sharpe":
        return -sharpe
    if objective.lower() == "meanvar":
        return -(mean - volatility)
    raise ValueError(f"unsupported objective: {objective}")


def _model(config: SimulationConfig) -> nn.Module:
    if config.model_name == "cnn_transformer":
        return CNNTransformer(
            random_seed=config.random_seed,
            lookback=config.lookback_days,
        )
    if config.model_name == "fourier_ffn":
        return FourierFFN(
            random_seed=config.random_seed,
            lookback=config.lookback_days,
            hidden_units=(config.lookback_days, 16, 8, 4),
        )
    return OUThreshold(lookback=config.lookback_days)


def _features(config: SimulationConfig, cumulative: FloatArray) -> FloatArray:
    return (
        packed_fourier_windows(cumulative)
        if config.model_name == "fourier_ffn"
        else cumulative
    )


def _predict_weights(
    model: nn.Module,
    features: torch.Tensor,
    selected: torch.Tensor,
) -> torch.Tensor:
    weights = torch.zeros(selected.shape, device=features.device)
    if selected.any():
        weights[selected] = model(features[selected])
    return weights


def _portfolio_path(
    model: nn.Module,
    features: torch.Tensor,
    selected: torch.Tensor,
    residuals: torch.Tensor,
    left: torch.Tensor,
    right: torch.Tensor,
    extra_asset_loadings: torch.Tensor | None = None,
    *,
    transaction_cost: float,
    short_holding_cost: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    raw_weights = _predict_weights(model, features, selected)
    if extra_asset_loadings is None:
        residual_weights, asset_weights = low_rank_asset_weights(
            raw_weights, left, right
        )
    else:
        residual_weights, asset_weights = factor_leg_asset_weights(
            raw_weights, extra_asset_loadings
        )
    strategy_returns = (residual_weights * residuals).sum(dim=1)
    turnover = torch.cat(
        (
            torch.zeros(1, device=residuals.device),
            (asset_weights[1:] - asset_weights[:-1]).abs().sum(dim=1),
        )
    )
    short_proportion = torch.clamp(asset_weights, max=0).abs().sum(dim=1)
    net_returns = (
        strategy_returns
        - transaction_cost * turnover
        - short_holding_cost * short_proportion
    )
    return net_returns, strategy_returns, turnover, short_proportion, asset_weights


def _train_subperiod(
    model: nn.Module,
    config: SimulationConfig,
    features: FloatArray,
    selected: BoolArray,
    panel: ResidualPanel,
    start: int,
    stop: int,
    progress: Progress | None,
    subperiod: int,
) -> None:
    device = torch.device(config.device)
    model.to(device).train()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    checkpoint_path = (
        None
        if config.checkpoint_directory is None
        else config.checkpoint_directory / f"subperiod_{subperiod:02d}.pt"
    )
    initial_epoch = 0
    if checkpoint_path is not None and config.resume_checkpoints and checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        initial_epoch = int(checkpoint["epoch"]) + 1
        if progress is not None:
            progress(
                {
                    "event": "checkpoint_resumed",
                    "subperiod": subperiod,
                    "next_epoch": initial_epoch + 1,
                }
            )
    signal_start = start + config.lookback_days
    signal_stop = stop
    for epoch in range(initial_epoch, config.epochs):
        for batch_start in range(signal_start, signal_stop, config.batch_days):
            batch_stop = min(batch_start + config.batch_days, signal_stop)
            feature_slice = slice(
                batch_start - config.lookback_days,
                batch_stop - config.lookback_days,
            )
            inputs = torch.as_tensor(features[feature_slice], device=device)
            valid = torch.as_tensor(selected[feature_slice], device=device)
            returns = torch.as_tensor(
                panel.residuals[batch_start:batch_stop],
                dtype=torch.float32,
                device=device,
            )
            left = torch.as_tensor(
                panel.left[batch_start:batch_stop], dtype=torch.float32, device=device
            )
            right = torch.as_tensor(
                panel.right[batch_start:batch_stop], dtype=torch.float32, device=device
            )
            net_returns, _, _, _, _ = _portfolio_path(
                model,
                inputs,
                valid,
                returns,
                left,
                right,
                (
                    None
                    if panel.extra_asset_loadings is None
                    else torch.as_tensor(
                        panel.extra_asset_loadings[batch_start:batch_stop],
                        dtype=torch.float32,
                        device=device,
                    )
                ),
                transaction_cost=config.transaction_cost,
                short_holding_cost=config.short_holding_cost,
            )
            loss = objective_loss(net_returns, config.objective)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if checkpoint_path is not None:
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = checkpoint_path.with_suffix(".tmp")
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                },
                temporary,
            )
            temporary.replace(checkpoint_path)
        if progress is not None and (epoch == 0 or (epoch + 1) % 10 == 0):
            progress(
                {
                    "event": "training_epoch",
                    "subperiod": subperiod,
                    "epoch": epoch + 1,
                    "epochs": config.epochs,
                    "loss": float(loss.detach().cpu()),
                }
            )


def simulate_rolling_strategy(
    panel: ResidualPanel,
    config: SimulationConfig,
    *,
    progress: Progress | None = None,
) -> SimulationResult:
    """Train and evaluate the policy over rolling out-of-sample subperiods."""

    config.validate()
    if len(panel.dates) <= config.training_window_days:
        raise ValueError("residual sample does not exceed the training window")
    if config.device.startswith("cuda") and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is unavailable")
    cumulative, selected = cumulative_windows(
        panel.residuals, panel.observed, config.lookback_days
    )
    features = _features(config, cumulative)
    output_size = len(panel.dates) - config.training_window_days
    strategy = np.zeros(output_size, dtype=float)
    gross_strategy = np.zeros(output_size, dtype=float)
    turnover = np.zeros(output_size, dtype=float)
    short_proportion = np.zeros(output_size, dtype=float)
    asset_names = panel.asset_tickers or panel.tickers
    asset_weights = np.zeros((output_size, len(asset_names)), dtype=np.float32)
    model: nn.Module | None = None
    subperiods = int(np.ceil(output_size / config.stride_days))

    for subperiod in range(subperiods):
        train_start = subperiod * config.stride_days
        train_stop = train_start + config.training_window_days
        test_start = train_stop
        test_stop = min(test_start + config.stride_days, len(panel.dates))
        if config.model_name != "ou_threshold" and (
            config.rolling_retrain or model is None
        ):
            model = _model(config)
            _train_subperiod(
                model,
                config,
                features,
                selected,
                panel,
                train_start,
                train_stop,
                progress,
                subperiod,
            )
        elif model is None:
            model = _model(config)

        device = torch.device(config.device)
        model.to(device).eval()
        feature_slice = slice(
            test_start - config.lookback_days,
            test_stop - config.lookback_days,
        )
        with torch.no_grad():
            values = _portfolio_path(
                model,
                torch.as_tensor(features[feature_slice], device=device),
                torch.as_tensor(selected[feature_slice], device=device),
                torch.as_tensor(
                    panel.residuals[test_start:test_stop],
                    dtype=torch.float32,
                    device=device,
                ),
                torch.as_tensor(
                    panel.left[test_start:test_stop],
                    dtype=torch.float32,
                    device=device,
                ),
                torch.as_tensor(
                    panel.right[test_start:test_stop],
                    dtype=torch.float32,
                    device=device,
                ),
                (
                    None
                    if panel.extra_asset_loadings is None
                    else torch.as_tensor(
                        panel.extra_asset_loadings[test_start:test_stop],
                        dtype=torch.float32,
                        device=device,
                    )
                ),
                transaction_cost=config.transaction_cost,
                short_holding_cost=config.short_holding_cost,
            )
        reported_turnover = values[2].clone()
        if len(reported_turnover) > 1:
            reported_turnover[0] = reported_turnover[1:].mean()
        destination = slice(
            test_start - config.training_window_days,
            test_stop - config.training_window_days,
        )
        strategy[destination] = values[0].cpu().numpy()
        gross_strategy[destination] = values[1].cpu().numpy()
        turnover[destination] = reported_turnover.cpu().numpy()
        short_proportion[destination] = values[3].cpu().numpy()
        asset_weights[destination] = values[4].cpu().numpy()
        if progress is not None:
            progress(
                {
                    "event": "subperiod_completed",
                    "subperiod": subperiod,
                    "subperiods": subperiods,
                    "test_start": panel.dates[test_start].date().isoformat(),
                    "test_end": panel.dates[test_stop - 1].date().isoformat(),
                }
            )

    dates = panel.dates[config.training_window_days :]
    daily = pd.DataFrame(
        {
            "date": dates,
            "return": strategy,
            "gross_return": gross_strategy,
            "turnover": turnover,
            "short_proportion": short_proportion,
            "leverage": np.abs(asset_weights).sum(axis=1),
        }
    )
    weights = pd.DataFrame(asset_weights, index=dates, columns=asset_names)
    weights.index.name = "date"
    torch_returns = torch.as_tensor(strategy)
    mean, volatility, sharpe = annualized_statistics(torch_returns)
    factor_model = "Fama-French" if panel.extra_asset_loadings is not None else "PCA"
    audit: dict[str, object] = {
        "classification": f"Korean {factor_model} price-return replication variant",
        "factor_model": factor_model,
        "model": config.model_name,
        "objective": config.objective,
        "random_seed": config.random_seed,
        "lookback_days": config.lookback_days,
        "training_window_days": config.training_window_days,
        "stride_days": config.stride_days,
        "rolling_retrain": config.rolling_retrain,
        "epochs": config.epochs,
        "batch_days": config.batch_days,
        "learning_rate": config.learning_rate,
        "holding_days": config.holding_days,
        "transaction_cost": config.transaction_cost,
        "short_holding_cost": config.short_holding_cost,
        "device": config.device,
        "checkpoint_directory": (
            str(config.checkpoint_directory)
            if config.checkpoint_directory is not None
            else None
        ),
        "residual_days": len(panel.dates),
        "residual_assets": len(panel.tickers),
        "oos_days": len(daily),
        "oos_start": dates.min().date().isoformat(),
        "oos_end": dates.max().date().isoformat(),
        "subperiods": subperiods,
        "annual_return": float(mean),
        "annual_volatility": float(volatility),
        "sharpe": float(sharpe),
        "mean_daily_turnover": float(turnover.mean()),
        "mean_short_proportion": float(short_proportion.mean()),
        "data_limitations": [
            "cash-dividend-excluding adjusted price returns, not total returns",
            "exact 240-month IPCA branch is history-blocked",
            "Korean universe is smaller than the U.S. CRSP universe",
        ],
    }
    return SimulationResult(daily=daily, weights=weights, audit=audit)
