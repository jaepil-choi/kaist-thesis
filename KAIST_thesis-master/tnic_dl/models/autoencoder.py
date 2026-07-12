"""
Deep Autoencoder for TNIC.

Implements Kim et al. (2020) architecture:
- Encoder: 2000 → 500 (ReLU) → 125 (ReLU) → 10 (Linear)
- Decoder: 10 → 125 (ReLU) → 500 (ReLU) → 2000 (Sigmoid)

Symmetric "butterfly" architecture with binary cross-entropy loss.
"""

import torch
import torch.nn as nn
from typing import List, Optional
from tnic_dl.config import get_dl_config
from tnic_dl.utils import setup_logger

logger = setup_logger(__name__)


class DeepAutoencoder(nn.Module):
    """
    Deep Autoencoder following Kim et al. (2020) architecture.

    Architecture:
        Input (2000) → Encoder → Latent (10) → Decoder → Output (2000)

    Encoder:
        Dense(2000, 500, ReLU) → Dense(500, 125, ReLU) → Dense(125, 10, Linear)

    Decoder:
        Dense(10, 125, ReLU) → Dense(125, 500, ReLU) → Dense(500, 2000, Sigmoid)
    """

    def __init__(
        self,
        input_dim: Optional[int] = None,
        encoder_hidden: Optional[List[int]] = None,
        latent_dim: Optional[int] = None,
        decoder_hidden: Optional[List[int]] = None,
        output_dim: Optional[int] = None,
    ):
        """
        Initialize deep autoencoder.

        Args:
            input_dim: Input dimension (default: 2000 from config)
            encoder_hidden: Encoder hidden layer sizes (default: [500, 125] from config)
            latent_dim: Latent/coded layer dimension (default: 10 from config)
            decoder_hidden: Decoder hidden layer sizes (default: [125, 500] from config)
            output_dim: Output dimension (default: 2000 from config)
        """
        super(DeepAutoencoder, self).__init__()

        # Load from config if not provided
        self.input_dim = input_dim or get_dl_config("tnic_dl.autoencoder.architecture.input_dim", 2000)
        self.encoder_hidden = encoder_hidden or get_dl_config("tnic_dl.autoencoder.architecture.encoder_hidden", [500, 125])
        self.latent_dim = latent_dim or get_dl_config("tnic_dl.autoencoder.architecture.latent_dim", 10)
        self.decoder_hidden = decoder_hidden or get_dl_config("tnic_dl.autoencoder.architecture.decoder_hidden", [125, 500])
        self.output_dim = output_dim or get_dl_config("tnic_dl.autoencoder.architecture.output_dim", 2000)

        # Build encoder
        self.encoder = self._build_encoder()

        # Build decoder
        self.decoder = self._build_decoder()

        # Initialize weights (Xavier initialization)
        self.apply(self._init_weights)

        logger.info(f"Initialized DeepAutoencoder: {self.input_dim} → {self.encoder_hidden} → {self.latent_dim} → {self.decoder_hidden} → {self.output_dim}")

    def _build_encoder(self) -> nn.Sequential:
        """Build encoder network."""
        layers = []

        # Input → First hidden layer
        layers.append(nn.Linear(self.input_dim, self.encoder_hidden[0]))
        layers.append(nn.ReLU())

        # Hidden layers
        for i in range(len(self.encoder_hidden) - 1):
            layers.append(nn.Linear(self.encoder_hidden[i], self.encoder_hidden[i + 1]))
            layers.append(nn.ReLU())

        # Last hidden → Latent (Linear activation)
        layers.append(nn.Linear(self.encoder_hidden[-1], self.latent_dim))
        # No activation (Linear) for latent layer

        return nn.Sequential(*layers)

    def _build_decoder(self) -> nn.Sequential:
        """Build decoder network."""
        layers = []

        # Latent → First hidden layer
        layers.append(nn.Linear(self.latent_dim, self.decoder_hidden[0]))
        layers.append(nn.ReLU())

        # Hidden layers
        for i in range(len(self.decoder_hidden) - 1):
            layers.append(nn.Linear(self.decoder_hidden[i], self.decoder_hidden[i + 1]))
            layers.append(nn.ReLU())

        # Last hidden → Output (Sigmoid activation for binary reconstruction)
        layers.append(nn.Linear(self.decoder_hidden[-1], self.output_dim))
        layers.append(nn.Sigmoid())

        return nn.Sequential(*layers)

    def _init_weights(self, module):
        """Initialize weights using Xavier initialization."""
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the autoencoder.

        Args:
            x: Input tensor (batch_size, input_dim)

        Returns:
            Reconstructed output (batch_size, output_dim)
        """
        # Encode
        latent = self.encoder(x)

        # Decode
        reconstructed = self.decoder(latent)

        return reconstructed

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Encode input to latent representation.

        Args:
            x: Input tensor (batch_size, input_dim)

        Returns:
            Latent representation (batch_size, latent_dim)
        """
        return self.encoder(x)

    def decode(self, latent: torch.Tensor) -> torch.Tensor:
        """
        Decode latent representation to output.

        Args:
            latent: Latent tensor (batch_size, latent_dim)

        Returns:
            Reconstructed output (batch_size, output_dim)
        """
        return self.decoder(latent)

    def get_latent_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """
        Get latent embeddings (same as encode, for clarity).

        Args:
            x: Input tensor (batch_size, input_dim)

        Returns:
            Latent embeddings (batch_size, latent_dim)
        """
        return self.encode(x)

    def count_parameters(self) -> int:
        """Count total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def summary(self) -> str:
        """
        Get model summary string.

        Returns:
            String with model architecture and parameter count
        """
        summary_str = f"""
Deep Autoencoder Summary:
------------------------
Architecture: {self.input_dim} → {self.encoder_hidden} → {self.latent_dim} → {self.decoder_hidden} → {self.output_dim}

Encoder:
  Input: {self.input_dim}
  Hidden layers: {self.encoder_hidden}
  Latent: {self.latent_dim}

Decoder:
  Latent: {self.latent_dim}
  Hidden layers: {self.decoder_hidden}
  Output: {self.output_dim}

Total Parameters: {self.count_parameters():,}
"""
        return summary_str


class BinaryCrossEntropyLoss(nn.Module):
    """
    Binary Cross-Entropy Loss for autoencoder.

    Kim et al. (2020) use BCE loss for binary input reconstruction.
    """

    def __init__(self, reduction: str = 'mean'):
        """
        Initialize BCE loss.

        Args:
            reduction: Reduction method ('mean', 'sum', or 'none')
        """
        super(BinaryCrossEntropyLoss, self).__init__()
        self.bce = nn.BCELoss(reduction=reduction)

    def forward(self, output: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        Compute BCE loss.

        Args:
            output: Reconstructed output (batch_size, output_dim)
            target: Target input (batch_size, input_dim)

        Returns:
            Loss value
        """
        return self.bce(output, target)
