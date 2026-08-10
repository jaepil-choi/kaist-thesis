"""Tests for paper trading-policy architectures."""

from __future__ import annotations

import pytest
import torch

from guijarro_ordonez_replication.policies import (
    CNNTransformer,
    FourierFFN,
    OUThreshold,
)


@pytest.mark.parametrize(
    "model",
    [
        CNNTransformer(random_seed=7, lookback=30),
        FourierFFN(random_seed=7, lookback=30),
        OUThreshold(lookback=30),
    ],
)
def test_policy_returns_one_weight_per_signal(model: torch.nn.Module) -> None:
    inputs = torch.linspace(-0.1, 0.1, 90).reshape(3, 30)
    assert model(inputs).shape == (3,)


def test_cnn_transformer_seed_is_reproducible() -> None:
    first = CNNTransformer(random_seed=17, lookback=30)
    second = CNNTransformer(random_seed=17, lookback=30)
    inputs = torch.linspace(-0.2, 0.3, 60).reshape(2, 30)
    first.eval()
    second.eval()
    torch.testing.assert_close(first(inputs), second(inputs))


def test_ou_trades_only_valid_mean_reversion() -> None:
    model = OUThreshold(lookback=30, signal_threshold=0.0, r2_threshold=0.0)
    constant = torch.ones((1, 30))
    assert model(constant).item() == 0.0

