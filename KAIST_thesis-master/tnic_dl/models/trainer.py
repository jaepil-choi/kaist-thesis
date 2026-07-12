"""
Autoencoder Trainer for TNIC-DL.

Handles training, validation, and early stopping for the deep autoencoder.
"""

import json
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from tnic_dl.models.autoencoder import DeepAutoencoder, BinaryCrossEntropyLoss
from tnic_dl.config import get_dl_config, get_model_path
from tnic_dl.utils import setup_logger

logger = setup_logger(__name__)


class AutoencoderTrainer:
    """
    Trainer for Deep Autoencoder following Kim et al. (2020) methodology.

    Features:
    - Binary cross-entropy loss
    - Adam optimizer
    - Early stopping
    - Training/validation split
    - Model checkpointing
    """

    def __init__(
        self,
        model: Optional[DeepAutoencoder] = None,
        learning_rate: Optional[float] = None,
        batch_size: Optional[int] = None,
        epochs: Optional[int] = None,
        validation_split: Optional[float] = None,
        early_stopping_patience: Optional[int] = None,
        device: Optional[str] = None,
        verbose: Optional[bool] = None,
        use_svd_init: Optional[bool] = None,
    ):
        """
        Initialize trainer.

        Args:
            model: DeepAutoencoder model (if None, creates new model)
            learning_rate: Learning rate for Adam optimizer (default from config)
            batch_size: Batch size for training (default from config)
            epochs: Maximum epochs (default from config)
            validation_split: Fraction for validation (default from config)
            early_stopping_patience: Patience for early stopping (default from config)
            device: Device to train on ('cpu' or 'cuda') (default from config)
            verbose: Whether to print training progress (default from config)
            use_svd_init: If True, initialize encoder layers with TruncatedSVD before
                          backprop training.  This replaces the missing RBM pre-training
                          from Kim et al. (2020) with a practical alternative that
                          addresses the dead-ReLU / sparse-input problem.
                          Default True (from config or falls back to True).
        """
        self.model = model or DeepAutoencoder()
        self.learning_rate = learning_rate or get_dl_config("tnic_dl.autoencoder.training.learning_rate", 0.001)
        self.batch_size = batch_size or get_dl_config("tnic_dl.autoencoder.training.batch_size", 64)
        self.epochs = epochs or get_dl_config("tnic_dl.autoencoder.training.epochs", 100)
        self.validation_split = validation_split or get_dl_config("tnic_dl.autoencoder.training.validation_split", 0.1)
        self.early_stopping_patience = early_stopping_patience or get_dl_config("tnic_dl.autoencoder.training.early_stopping_patience", 10)
        self.device = device or get_dl_config("tnic_dl.autoencoder.training.device", "cpu")
        self.verbose = verbose if verbose is not None else get_dl_config("tnic_dl.autoencoder.training.verbose", True)
        self.use_svd_init = use_svd_init if use_svd_init is not None else get_dl_config("tnic_dl.autoencoder.training.use_svd_init", True)

        # Move model to device
        self.model = self.model.to(self.device)

        # Loss function
        self.criterion = BinaryCrossEntropyLoss()

        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'epoch_times': [],
        }

        self.logger = logger
        self.logger.info(f"Initialized AutoencoderTrainer on device: {self.device}")
        self.logger.info(self.model.summary())

    def _svd_pretrain(self, X: csr_matrix) -> None:
        """
        Initialize encoder layers using greedy layer-wise TruncatedSVD.

        Kim et al. (2020) specify RBM greedy layer-wise pre-training
        (Hinton & Salakhutdinov, 2006) to handle sparse binary inputs.
        This method implements the equivalent using SVD, which:
          - Provides the same directional initialisation benefit
          - Avoids the dead-ReLU problem on ~99%-zero binary inputs
          - Is deterministic and much faster to compute

        Layer-wise approach mirrors RBM greedy training:
          Layer 0: SVD on raw input    (2000 → 500)
          Layer 1: SVD on activations  (500  → 125)
          (Layer 2 latent dim 10 is left as Xavier — too small for SVD to add value)
        """
        self.logger.info("SVD pre-training: initialising encoder layers …")

        encoder_layers = [
            layer for layer in self.model.encoder
            if isinstance(layer, nn.Linear)
        ]

        current_input = X.toarray().astype(np.float32)  # (N, 2000)

        for idx, linear_layer in enumerate(encoder_layers[:-1]):  # skip latent layer
            n_components = linear_layer.out_features
            self.logger.info(
                f"  Layer {idx}: SVD {current_input.shape[1]} → {n_components} dims "
                f"on {current_input.shape[0]} samples"
            )

            svd = TruncatedSVD(n_components=n_components, random_state=42, n_iter=5)
            svd.fit(current_input)

            # Initialise weight matrix from SVD components (shape: out × in)
            W = torch.tensor(svd.components_, dtype=torch.float32)
            with torch.no_grad():
                linear_layer.weight.data.copy_(W)
                # Leave bias at zero (consistent with RBM visible bias init)
                linear_layer.bias.data.zero_()

            # Propagate through ReLU to get input for next layer
            activated = np.maximum(0.0, current_input @ svd.components_.T)  # ReLU
            current_input = activated

        self.logger.info("SVD pre-training complete.")

    def train(
        self,
        X: csr_matrix,
        year: Optional[int] = None,
        save_best: bool = True,
    ) -> Tuple[DeepAutoencoder, Dict[str, Any]]:
        """
        Train the autoencoder.

        Args:
            X: Input data (sparse matrix, N x V)
            year: Year (for saving model)
            save_best: Whether to save the best model

        Returns:
            Tuple of (trained_model, training_history)
        """
        self.logger.info(f"Starting training with {X.shape[0]} samples, {X.shape[1]} features")

        # SVD-based layer-wise pre-initialisation (replaces RBM pre-training from Kim et al. 2020)
        if self.use_svd_init:
            self._svd_pretrain(X)

        # Convert sparse matrix to dense tensor
        X_dense = X.toarray().astype(np.float32)
        X_tensor = torch.from_numpy(X_dense)

        # Create dataset
        dataset = TensorDataset(X_tensor, X_tensor)  # Input = Target for autoencoder

        # Split into train and validation
        val_size = int(len(dataset) * self.validation_split)
        train_size = len(dataset) - val_size
        train_dataset, val_dataset = random_split(
            dataset,
            [train_size, val_size],
            generator=torch.Generator().manual_seed(42)
        )

        self.logger.info(f"Train size: {train_size}, Validation size: {val_size}")

        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)

        # Training loop
        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None

        for epoch in range(self.epochs):
            epoch_start = time.time()

            # Train one epoch
            train_loss = self._train_epoch(train_loader)

            # Validate
            val_loss = self._validate(val_loader)

            # Record history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['epoch_times'].append(time.time() - epoch_start)

            # Print progress
            if self.verbose and (epoch % 5 == 0 or epoch == self.epochs - 1):
                self.logger.info(
                    f"Epoch {epoch+1}/{self.epochs} - "
                    f"Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}, "
                    f"Time: {self.history['epoch_times'][-1]:.2f}s"
                )

            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_state = self.model.state_dict().copy()

                if self.verbose:
                    self.logger.info(f"  → New best validation loss: {best_val_loss:.6f}")
            else:
                patience_counter += 1

            if patience_counter >= self.early_stopping_patience:
                self.logger.info(f"Early stopping at epoch {epoch+1} (patience: {self.early_stopping_patience})")
                break

        # Restore best model
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)
            self.logger.info(f"Restored best model with validation loss: {best_val_loss:.6f}")

        # Save model
        if save_best and year is not None:
            self.save_model(year)
            self.save_history(year)

        return self.model, self.history

    def _train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0

        for batch_input, batch_target in train_loader:
            batch_input = batch_input.to(self.device)
            batch_target = batch_target.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            output = self.model(batch_input)
            loss = self.criterion(output, batch_target)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def _validate(self, val_loader: DataLoader) -> float:
        """Validate the model."""
        self.model.eval()
        total_loss = 0.0

        with torch.no_grad():
            for batch_input, batch_target in val_loader:
                batch_input = batch_input.to(self.device)
                batch_target = batch_target.to(self.device)

                output = self.model(batch_input)
                loss = self.criterion(output, batch_target)

                total_loss += loss.item()

        return total_loss / len(val_loader)

    def encode_data(self, X: csr_matrix) -> np.ndarray:
        """
        Encode data to latent representations.

        Args:
            X: Input data (sparse matrix, N x V)

        Returns:
            Latent embeddings (N x latent_dim)
        """
        self.model.eval()

        # Convert to tensor
        X_dense = X.toarray().astype(np.float32)
        X_tensor = torch.from_numpy(X_dense).to(self.device)

        # Create data loader
        dataset = TensorDataset(X_tensor)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        embeddings = []

        with torch.no_grad():
            for (batch_input,) in loader:
                batch_latent = self.model.encode(batch_input)
                embeddings.append(batch_latent.cpu().numpy())

        embeddings = np.vstack(embeddings)
        self.logger.info(f"Encoded {embeddings.shape[0]} samples to {embeddings.shape[1]}-dim embeddings")

        return embeddings

    def save_model(self, year: int) -> None:
        """
        Save trained model to disk.

        Args:
            year: Year of the model
        """
        model_path = get_model_path(f"autoencoder_{year}.pt")

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'architecture': {
                'input_dim': self.model.input_dim,
                'encoder_hidden': self.model.encoder_hidden,
                'latent_dim': self.model.latent_dim,
                'decoder_hidden': self.model.decoder_hidden,
                'output_dim': self.model.output_dim,
            },
            'training_config': {
                'learning_rate': self.learning_rate,
                'batch_size': self.batch_size,
                'epochs': len(self.history['train_loss']),
                'validation_split': self.validation_split,
            },
            'year': year,
        }, model_path)

        self.logger.info(f"Saved model to {model_path}")

    def save_history(self, year: int) -> None:
        """
        Save training history to JSON.

        Args:
            year: Year of the training
        """
        log_dir = Path(get_dl_config("tnic_dl.paths.training_logs_dir", "data/korean_tnic_dl/models/training_logs"))
        log_dir.mkdir(parents=True, exist_ok=True)

        log_path = log_dir / f"training_log_{year}.json"

        history_json = {
            'year': year,
            'train_loss': self.history['train_loss'],
            'val_loss': self.history['val_loss'],
            'epoch_times': self.history['epoch_times'],
            'final_train_loss': self.history['train_loss'][-1],
            'final_val_loss': self.history['val_loss'][-1],
            'best_val_loss': min(self.history['val_loss']),
            'total_epochs': len(self.history['train_loss']),
            'total_time': sum(self.history['epoch_times']),
        }

        with open(log_path, 'w') as f:
            json.dump(history_json, f, indent=2)

        self.logger.info(f"Saved training history to {log_path}")

    @staticmethod
    def load_model(year: int, device: Optional[str] = None) -> Tuple[DeepAutoencoder, dict]:
        """
        Load trained model from disk.

        Args:
            year: Year of the model
            device: Device to load model on (default from config)

        Returns:
            Tuple of (model, metadata)
        """
        device = device or get_dl_config("tnic_dl.autoencoder.training.device", "cpu")
        model_path = get_model_path(f"autoencoder_{year}.pt", create_dir=False)

        checkpoint = torch.load(model_path, map_location=device)

        # Create model with saved architecture
        model = DeepAutoencoder(
            input_dim=checkpoint['architecture']['input_dim'],
            encoder_hidden=checkpoint['architecture']['encoder_hidden'],
            latent_dim=checkpoint['architecture']['latent_dim'],
            decoder_hidden=checkpoint['architecture']['decoder_hidden'],
            output_dim=checkpoint['architecture']['output_dim'],
        )

        # Load state
        model.load_state_dict(checkpoint['model_state_dict'])
        model = model.to(device)
        model.eval()

        logger.info(f"Loaded model from {model_path}")

        return model, checkpoint
