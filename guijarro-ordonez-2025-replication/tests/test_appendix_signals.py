"""Tests for appendix single-residual signal illustrations."""

from __future__ import annotations

import torch
from pathlib import Path

from guijarro_ordonez_replication.appendix_signals import load_fourier_checkpoint
from guijarro_ordonez_replication.policies import FourierFFN


PROJECT = Path(__file__).resolve().parents[1]


def test_fourier_checkpoint_loader_round_trip() -> None:
    model = FourierFFN(hidden_units=(30, 16, 8, 4))
    path = PROJECT / "outputs" / ".test-fourier-checkpoint.pt"
    try:
        torch.save({"model_state_dict": model.state_dict()}, path)
        loaded = load_fourier_checkpoint(path)
        inputs = torch.randn(4, 30)
        model.eval()
        with torch.no_grad():
            torch.testing.assert_close(model(inputs), loaded(inputs))
    finally:
        path.unlink(missing_ok=True)
