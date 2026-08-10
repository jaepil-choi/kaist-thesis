"""Trading policies used in Guijarro-Ordonez, Pelger, and Zanotti (2025).

The layer order and defaults mirror the authors' public implementation.  The
classes live in this package so the Korean replication does not depend on the
adjacent reference-code checkout at runtime.
"""

from __future__ import annotations

import torch
from torch import nn


class CNNBlock(nn.Module):
    """Two causal convolutions with a repeated-channel residual connection."""

    def __init__(
        self,
        in_filters: int = 1,
        out_filters: int = 8,
        *,
        normalization: bool = True,
        filter_size: int = 2,
    ) -> None:
        super().__init__()
        if out_filters % in_filters:
            raise ValueError("out_filters must be a multiple of in_filters")
        self.in_filters = in_filters
        self.out_filters = out_filters
        self.normalization = normalization
        self.pad = nn.ConstantPad1d((filter_size - 1, 0), 0)
        self.norm1 = nn.InstanceNorm1d(in_filters)
        self.norm2 = nn.InstanceNorm1d(out_filters)
        self.conv1 = nn.Conv1d(in_filters, out_filters, filter_size)
        self.conv2 = nn.Conv1d(out_filters, out_filters, filter_size)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        outputs = self.norm1(inputs) if self.normalization else inputs
        residual = outputs
        outputs = self.relu(self.conv1(self.pad(outputs)))
        if self.normalization:
            outputs = self.norm2(outputs)
        outputs = self.relu(self.conv2(self.pad(outputs)))
        return outputs + residual.repeat(
            1, self.out_filters // self.in_filters, 1
        )


class CNNTransformer(nn.Module):
    """Paper benchmark: causal CNN followed by a Transformer encoder."""

    is_trainable = True

    def __init__(
        self,
        *,
        random_seed: int = 0,
        lookback: int = 30,
        normalization_conv: bool = True,
        filter_numbers: tuple[int, ...] = (1, 8),
        attention_heads: int = 4,
        use_convolution: bool = True,
        hidden_units_factor: int = 2,
        dropout: float = 0.25,
        filter_size: int = 2,
        use_transformer: bool = True,
    ) -> None:
        super().__init__()
        if lookback <= 1:
            raise ValueError("lookback must exceed one day")
        if not filter_numbers or filter_numbers[0] != 1:
            raise ValueError("filter_numbers must start with one input channel")
        torch.manual_seed(random_seed)
        self.random_seed = random_seed
        self.lookback = lookback
        self.filter_numbers = filter_numbers
        self.use_convolution = use_convolution and len(filter_numbers) > 1
        self.use_transformer = use_transformer
        self.blocks = nn.ModuleList(
            CNNBlock(
                filter_numbers[index],
                filter_numbers[index + 1],
                normalization=normalization_conv,
                filter_size=filter_size,
            )
            for index in range(len(filter_numbers) - 1)
        )
        width = filter_numbers[-1]
        self.encoder = nn.TransformerEncoderLayer(
            d_model=width,
            nhead=attention_heads,
            dim_feedforward=hidden_units_factor * width,
            dropout=dropout,
        )
        self.linear = nn.Linear(width, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != self.lookback:
            raise ValueError(f"inputs must have shape (batch, {self.lookback})")
        outputs = inputs.reshape(inputs.shape[0], 1, self.lookback)
        if self.use_convolution:
            for block in self.blocks:
                outputs = block(outputs)
        outputs = outputs.permute(2, 0, 1)
        if self.use_transformer:
            outputs = self.encoder(outputs)
        return self.linear(outputs[-1]).squeeze(-1)


class WeightsTransformer(nn.Module):
    """Public friction model's attention block with lagged weight input."""

    def __init__(
        self,
        *,
        width: int = 8,
        attention_heads: int = 4,
        hidden_units: int = 16,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()
        self.attention = nn.MultiheadAttention(width, attention_heads)
        self.linear1 = nn.Linear(width + 1, hidden_units)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(hidden_units, width + 1)
        self.norm1 = nn.LayerNorm(width + 1)
        self.norm2 = nn.LayerNorm(width + 1)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.activation = nn.ReLU(inplace=True)

    def forward(
        self, inputs: torch.Tensor, old_weights: torch.Tensor
    ) -> torch.Tensor:
        attended = self.attention(inputs, inputs, inputs)[0][-1]
        outputs = inputs[-1] + self.dropout1(attended)
        outputs = torch.cat((outputs, old_weights.reshape(-1, 1)), dim=1)
        outputs = self.norm1(outputs)
        transformed = self.linear2(
            self.dropout(self.activation(self.linear1(outputs)))
        )
        return self.norm2(outputs + self.dropout2(transformed))


class CNNTransformerFrictions(nn.Module):
    """CNN+Transformer policy conditioned on the previous residual weight."""

    is_trainable = True
    uses_previous_weight = True

    def __init__(
        self,
        *,
        random_seed: int = 0,
        lookback: int = 30,
        normalization_conv: bool = True,
        filter_numbers: tuple[int, ...] = (1, 8),
        attention_heads: int = 4,
        hidden_units_factor: int = 2,
        dropout: float = 0.25,
        filter_size: int = 2,
    ) -> None:
        super().__init__()
        torch.manual_seed(random_seed)
        self.random_seed = random_seed
        self.lookback = lookback
        self.filter_numbers = filter_numbers
        self.blocks = nn.ModuleList(
            CNNBlock(
                filter_numbers[index],
                filter_numbers[index + 1],
                normalization=normalization_conv,
                filter_size=filter_size,
            )
            for index in range(len(filter_numbers) - 1)
        )
        width = filter_numbers[-1]
        self.encoder = WeightsTransformer(
            width=width,
            attention_heads=attention_heads,
            hidden_units=hidden_units_factor * width,
            dropout=dropout,
        )
        self.linear = nn.Linear(width + 1, 1)

    def forward(
        self, inputs: torch.Tensor, old_weights: torch.Tensor
    ) -> torch.Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != self.lookback:
            raise ValueError(f"inputs must have shape (batch, {self.lookback})")
        outputs = inputs.reshape(inputs.shape[0], 1, self.lookback)
        for block in self.blocks:
            outputs = block(outputs)
        outputs = outputs.permute(2, 0, 1)
        outputs = self.encoder(outputs, old_weights)
        return self.linear(outputs).squeeze(-1)


class FourierFFN(nn.Module):
    """Paper benchmark feedforward network for packed Fourier coefficients."""

    is_trainable = True

    def __init__(
        self,
        *,
        random_seed: int = 0,
        lookback: int = 30,
        hidden_units: tuple[int, ...] = (30, 16, 8, 4),
        dropout: float = 0.25,
    ) -> None:
        super().__init__()
        if not hidden_units or hidden_units[0] != lookback:
            raise ValueError("hidden_units must start with lookback")
        torch.manual_seed(random_seed)
        self.random_seed = random_seed
        self.lookback = lookback
        self.layers = nn.ModuleList(
            nn.Sequential(
                nn.Linear(hidden_units[index], hidden_units[index + 1]),
                nn.ReLU(inplace=True),
                nn.Dropout(dropout),
            )
            for index in range(len(hidden_units) - 1)
        )
        self.final = nn.Linear(hidden_units[-1], 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != self.lookback:
            raise ValueError(f"inputs must have shape (batch, {self.lookback})")
        outputs = inputs
        for layer in self.layers:
            outputs = layer(outputs)
        return self.final(outputs).squeeze(-1)


class OUFeaturesFFN(nn.Module):
    """Paper Appendix C.5 OU four-feature signal with a sigmoid FFN allocation."""

    is_trainable = True

    def __init__(
        self,
        *,
        random_seed: int = 0,
        lookback: int = 30,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()
        torch.manual_seed(random_seed)
        self.lookback = lookback
        self.layers = nn.ModuleList(
            nn.Sequential(nn.Linear(4, 4), nn.Sigmoid(), nn.Dropout(dropout))
            for _ in range(3)
        )
        self.final = nn.Linear(4, 1)

    def _ou_features(self, inputs: torch.Tensor) -> torch.Tensor:
        x_values = inputs[:, :-1].float()
        y_values = inputs[:, 1:].float()
        mean_x = x_values.mean(dim=1)
        mean_y = y_values.mean(dim=1)
        variance_x = x_values.var(dim=1) + 1e-16
        variance_y = y_values.var(dim=1) + 1e-16
        covariance = (
            (x_values - mean_x[:, None]) * (y_values - mean_y[:, None])
        ).mean(dim=1)
        beta = covariance / variance_x
        alpha = mean_y - beta * mean_x
        long_run_mean = alpha / (1.0 - beta + 1e-8)
        innovations = y_values - beta[:, None] * x_values - alpha[:, None]
        sigma = torch.sqrt(
            innovations.var(dim=1) / (torch.abs(1.0 - beta.square()) + 1e-8)
        )
        r_squared = covariance.square() / (variance_x * variance_y)
        return torch.nan_to_num(
            torch.stack((beta, long_run_mean, sigma, r_squared), dim=1)
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != self.lookback:
            raise ValueError(f"inputs must have shape (batch, {self.lookback})")
        outputs = self._ou_features(inputs)
        for layer in self.layers:
            outputs = layer(outputs)
        return self.final(outputs).squeeze(-1)


class OUThreshold(nn.Module):
    """Nontrainable Ornstein-Uhlenbeck threshold benchmark from the paper."""

    is_trainable = False

    def __init__(
        self,
        *,
        lookback: int = 30,
        signal_threshold: float = 1.25,
        r2_threshold: float = 0.25,
    ) -> None:
        super().__init__()
        self.lookback = lookback
        self.signal_threshold = signal_threshold
        self.r2_threshold = r2_threshold

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != self.lookback:
            raise ValueError(f"inputs must have shape (batch, {self.lookback})")
        x_values = inputs[:, :-1].float()
        y_values = inputs[:, 1:].float()
        mean_x = x_values.mean(dim=1)
        mean_y = y_values.mean(dim=1)
        variance_x = x_values.var(dim=1) + 1e-16
        variance_y = y_values.var(dim=1) + 1e-16
        covariance = (
            (x_values - mean_x[:, None]) * (y_values - mean_y[:, None])
        ).mean(dim=1)
        r_squared = covariance.square() / (variance_x * variance_y)
        beta = covariance / variance_x
        alpha = mean_y - beta * mean_x
        long_run_mean = alpha / (1.0 - beta)
        innovations = y_values - beta[:, None] * x_values - alpha[:, None]
        sigma = torch.sqrt(innovations.var(dim=1) / torch.abs(1.0 - beta.square()))
        valid = (beta > 0) & (beta < 1) & (sigma > 1e-16)
        signal = torch.where(valid, (long_run_mean - y_values[:, -1]) / sigma, 0.0)
        weights = (signal > self.signal_threshold).float()
        weights -= (signal < -self.signal_threshold).float()
        weights *= (r_squared > self.r2_threshold).float()
        return torch.nan_to_num(weights)
