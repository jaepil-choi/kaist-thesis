"""Tests for CNN interpretation primitives."""

from __future__ import annotations

import torch

from guijarro_ordonez_replication.interpretability import cnn_states
from guijarro_ordonez_replication.policies import CNNTransformer


def test_cnn_states_exposes_channels_and_attention_heads() -> None:
    model = CNNTransformer(random_seed=0, lookback=30)
    model.eval()
    convolution, attention = cnn_states(model, torch.randn(2, 30))
    assert convolution.shape == (2, 8, 30)
    assert attention.shape == (2, 4, 30, 30)
