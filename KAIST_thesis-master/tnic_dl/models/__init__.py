"""
Models module for TNIC-DL.

Contains:
- Deep autoencoder architecture (Kim et al. 2020)
- Training utilities
"""

from tnic_dl.models.autoencoder import DeepAutoencoder
from tnic_dl.models.trainer import AutoencoderTrainer

__all__ = [
    "DeepAutoencoder",
    "AutoencoderTrainer",
]
