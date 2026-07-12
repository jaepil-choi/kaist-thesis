"""
Cosine Similarity Computation for TNIC-DL.

Computes pairwise cosine similarity between embeddings.
"""

from typing import Optional
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
from sklearn.preprocessing import normalize
from tnic_dl.config import get_dl_config
from tnic_dl.utils import setup_logger

logger = setup_logger(__name__)


def compute_cosine_similarity(
    embeddings: np.ndarray,
    normalize_first: bool = True,
    batch_size: Optional[int] = None,
    min_similarity: Optional[float] = None,
    return_sparse: Optional[bool] = None,
) -> np.ndarray:
    """
    Compute pairwise cosine similarity matrix.

    Args:
        embeddings: Embeddings array (N x D)
        normalize_first: Whether to L2 normalize embeddings first (default True)
        batch_size: Batch size for computation (default from config)
        min_similarity: Minimum similarity to keep (for sparsity) (default from config)
        return_sparse: Whether to return sparse matrix (default from config)

    Returns:
        Similarity matrix (N x N), dense or sparse
    """
    batch_size = batch_size or get_dl_config("tnic_dl.similarity.batch_size", 1000)
    min_similarity = min_similarity if min_similarity is not None else get_dl_config("tnic_dl.similarity.min_similarity", 0.0)
    return_sparse = return_sparse if return_sparse is not None else get_dl_config("tnic_dl.similarity.save_sparse", True)

    n_samples = embeddings.shape[0]
    logger.info(f"Computing cosine similarity for {n_samples} samples")

    # Normalize embeddings if requested
    if normalize_first:
        embeddings = normalize(embeddings, norm='l2', axis=1)
        logger.info("Embeddings L2 normalized")

    # Compute similarity
    if n_samples <= batch_size:
        # Small enough to compute in one go
        similarity = sklearn_cosine_similarity(embeddings)
        logger.info(f"Computed similarity matrix: {similarity.shape}")
    else:
        # Compute in batches
        logger.info(f"Computing in batches of {batch_size}")
        similarity = _compute_similarity_batched(embeddings, batch_size)

    # Apply minimum similarity threshold
    if min_similarity > 0:
        similarity[similarity < min_similarity] = 0
        logger.info(f"Applied min similarity threshold: {min_similarity}")

    # Convert to sparse if requested
    if return_sparse:
        # Set diagonal to 0 before converting to sparse (self-similarity not needed)
        np.fill_diagonal(similarity, 0)

        # Convert to sparse
        similarity_sparse = csr_matrix(similarity)
        sparsity = 1 - (similarity_sparse.nnz / (n_samples * n_samples))
        logger.info(f"Converted to sparse matrix. Sparsity: {sparsity:.2%}, NNZ: {similarity_sparse.nnz:,}")
        return similarity_sparse
    else:
        return similarity


def _compute_similarity_batched(embeddings: np.ndarray, batch_size: int) -> np.ndarray:
    """
    Compute cosine similarity in batches.

    Args:
        embeddings: Embeddings array (N x D), already normalized
        batch_size: Batch size for computation

    Returns:
        Similarity matrix (N x N)
    """
    n_samples = embeddings.shape[0]
    similarity = np.zeros((n_samples, n_samples), dtype=np.float32)

    n_batches = int(np.ceil(n_samples / batch_size))

    for i in range(n_batches):
        start_i = i * batch_size
        end_i = min((i + 1) * batch_size, n_samples)
        batch_i = embeddings[start_i:end_i]

        # Compute similarity for this batch against all samples
        similarity[start_i:end_i, :] = sklearn_cosine_similarity(batch_i, embeddings)

        if (i + 1) % 10 == 0 or (i + 1) == n_batches:
            logger.info(f"  Batch {i+1}/{n_batches} completed")

    return similarity


def get_top_k_similar(
    similarity_matrix: np.ndarray,
    k: int,
    exclude_self: bool = True,
) -> tuple:
    """
    Get top-k most similar firms for each firm.

    Args:
        similarity_matrix: Similarity matrix (N x N)
        k: Number of top similar firms to return
        exclude_self: Whether to exclude self-similarity (default True)

    Returns:
        Tuple of (indices, scores)
        - indices: Array (N x k) of top-k firm indices
        - scores: Array (N x k) of top-k similarity scores
    """
    n_samples = similarity_matrix.shape[0]

    # If sparse, convert to dense for top-k extraction
    if isinstance(similarity_matrix, csr_matrix):
        similarity_matrix = similarity_matrix.toarray()

    # Exclude self if requested
    if exclude_self:
        similarity_matrix = similarity_matrix.copy()
        np.fill_diagonal(similarity_matrix, -np.inf)

    # Get top-k indices (argsort descending)
    top_k_indices = np.argsort(-similarity_matrix, axis=1)[:, :k]

    # Get corresponding scores
    top_k_scores = np.take_along_axis(similarity_matrix, top_k_indices, axis=1)

    logger.info(f"Extracted top-{k} similar firms for {n_samples} samples")

    return top_k_indices, top_k_scores


def get_similar_above_threshold(
    similarity_matrix: np.ndarray,
    threshold: float,
    exclude_self: bool = True,
) -> dict:
    """
    Get all firms above similarity threshold for each firm.

    Args:
        similarity_matrix: Similarity matrix (N x N)
        threshold: Similarity threshold
        exclude_self: Whether to exclude self-similarity (default True)

    Returns:
        Dictionary mapping firm_idx → list of (peer_idx, similarity) tuples
    """
    n_samples = similarity_matrix.shape[0]

    # If sparse, keep sparse for efficiency
    if isinstance(similarity_matrix, csr_matrix):
        similarity_csr = similarity_matrix
    else:
        similarity_csr = csr_matrix(similarity_matrix)

    peers_dict = {}

    for i in range(n_samples):
        # Get row (similarities for firm i)
        row = similarity_csr.getrow(i)

        # Get nonzero indices and values
        nonzero_indices = row.nonzero()[1]
        nonzero_values = row.data

        # Filter by threshold
        mask = nonzero_values >= threshold
        peer_indices = nonzero_indices[mask]
        peer_similarities = nonzero_values[mask]

        # Exclude self
        if exclude_self:
            self_mask = peer_indices != i
            peer_indices = peer_indices[self_mask]
            peer_similarities = peer_similarities[self_mask]

        # Store as list of tuples
        peers_dict[i] = list(zip(peer_indices, peer_similarities))

    logger.info(f"Found peers above threshold {threshold} for {n_samples} firms")

    # Compute statistics
    n_peers = [len(peers) for peers in peers_dict.values()]
    logger.info(f"  Peers per firm - Mean: {np.mean(n_peers):.1f}, Median: {np.median(n_peers):.1f}, "
                f"Min: {np.min(n_peers)}, Max: {np.max(n_peers)}")

    return peers_dict


def compute_similarity_statistics(similarity_matrix: np.ndarray, exclude_diagonal: bool = True) -> dict:
    """
    Compute statistics about the similarity matrix.

    Args:
        similarity_matrix: Similarity matrix (N x N)
        exclude_diagonal: Whether to exclude diagonal (self-similarity) from stats

    Returns:
        Dictionary of statistics
    """
    # Convert to dense if sparse
    if isinstance(similarity_matrix, csr_matrix):
        sim_dense = similarity_matrix.toarray()
    else:
        sim_dense = similarity_matrix.copy()

    # Exclude diagonal
    if exclude_diagonal:
        mask = ~np.eye(sim_dense.shape[0], dtype=bool)
        off_diagonal = sim_dense[mask]
    else:
        off_diagonal = sim_dense.flatten()

    stats = {
        'shape': sim_dense.shape,
        'mean': float(off_diagonal.mean()),
        'std': float(off_diagonal.std()),
        'min': float(off_diagonal.min()),
        'max': float(off_diagonal.max()),
        'median': float(np.median(off_diagonal)),
        'percentiles': {
            'p25': float(np.percentile(off_diagonal, 25)),
            'p50': float(np.percentile(off_diagonal, 50)),
            'p75': float(np.percentile(off_diagonal, 75)),
            'p90': float(np.percentile(off_diagonal, 90)),
            'p95': float(np.percentile(off_diagonal, 95)),
            'p99': float(np.percentile(off_diagonal, 99)),
        },
    }

    if isinstance(similarity_matrix, csr_matrix):
        total_elements = similarity_matrix.shape[0] * similarity_matrix.shape[1]
        stats['sparsity'] = 1 - (similarity_matrix.nnz / total_elements)
        stats['nnz'] = int(similarity_matrix.nnz)

    return stats
