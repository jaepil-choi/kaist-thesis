"""
Deep Learning-based Text-Based Network Industry Classification (TNIC-DL)

This module implements the Kim et al. (2020) deep autoencoder methodology
for generating low-dimensional (10-dim) industry embeddings from business descriptions.

Methodology:
1. Bag-of-words representation (top 2000 words)
2. Deep autoencoder (2000 → 500 → 125 → 10 → 125 → 500 → 2000)
3. Extract 10-dimensional latent embeddings
4. Compute cosine similarity for TNIC peer groups

The module is designed to work alongside the traditional TNIC implementation
and save outputs to a separate directory (data/korean_tnic_dl/).
"""

__version__ = "0.1.0"

# Lazy imports to avoid loading heavy dependencies unnecessarily
def get_pipeline():
    """Get the main TNIC-DL pipeline."""
    from tnic_dl.pipeline import TNICDLPipeline
    return TNICDLPipeline

def get_autoencoder():
    """Get the deep autoencoder model."""
    from tnic_dl.models.autoencoder import DeepAutoencoder
    return DeepAutoencoder

__all__ = [
    "get_pipeline",
    "get_autoencoder",
]
