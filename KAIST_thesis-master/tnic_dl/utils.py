"""
Utility functions for TNIC-DL module.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from scipy.sparse import issparse, save_npz, load_npz


def setup_logger(name: str = "tnic_dl", level: int = logging.INFO) -> logging.Logger:
    """
    Set up logger for TNIC-DL module.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger


def save_embeddings(embeddings: np.ndarray, path: Path, metadata: Optional[Dict] = None) -> None:
    """
    Save embeddings to disk with optional metadata.

    Args:
        embeddings: Numpy array of embeddings (N x D)
        path: Path to save the embeddings
        metadata: Optional metadata dictionary
    """
    np.save(path, embeddings)

    if metadata:
        metadata_path = path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def load_embeddings(path: Path, return_metadata: bool = False):
    """
    Load embeddings from disk.

    Args:
        path: Path to the embeddings file
        return_metadata: Whether to return metadata as well

    Returns:
        Embeddings array, or (embeddings, metadata) tuple if return_metadata=True
    """
    embeddings = np.load(path)

    if return_metadata:
        metadata_path = path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        return embeddings, metadata

    return embeddings


def save_similarity_matrix(similarity: np.ndarray, path: Path, metadata: Optional[Dict] = None) -> None:
    """
    Save similarity matrix to disk (sparse format if applicable).

    Args:
        similarity: Similarity matrix (N x N)
        path: Path to save the matrix
        metadata: Optional metadata dictionary
    """
    if issparse(similarity):
        save_npz(path, similarity)
    else:
        # Convert dense to sparse if mostly zeros
        from scipy.sparse import csr_matrix
        sparse_sim = csr_matrix(similarity)
        save_npz(path, sparse_sim)

    if metadata:
        metadata_path = path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def load_similarity_matrix(path: Path, return_metadata: bool = False):
    """
    Load similarity matrix from disk.

    Args:
        path: Path to the similarity matrix file
        return_metadata: Whether to return metadata as well

    Returns:
        Similarity matrix, or (matrix, metadata) tuple if return_metadata=True
    """
    matrix = load_npz(path)

    if return_metadata:
        metadata_path = path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        return matrix, metadata

    return matrix


def save_json(data: Dict[str, Any], path: Path) -> None:
    """
    Save dictionary to JSON file.

    Args:
        data: Dictionary to save
        path: Path to save the JSON file
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: Path) -> Dict[str, Any]:
    """
    Load dictionary from JSON file.

    Args:
        path: Path to the JSON file

    Returns:
        Dictionary loaded from JSON
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
