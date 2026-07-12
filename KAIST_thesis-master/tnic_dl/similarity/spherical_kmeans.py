"""
Spherical K-Means Clustering for TNIC-DL.

Implements spherical k-means (cosine distance) following Kim et al. (2020).
"""

from typing import Optional, Tuple
import numpy as np
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans
from tnic_dl.config import get_config
from tnic_dl.utils import setup_logger

logger = setup_logger(__name__)


class SphericalKMeans:
    """
    Spherical K-Means Clustering using cosine similarity.

    Kim et al. (2020) use spherical k-means instead of standard k-means
    because cosine similarity focuses on direction rather than magnitude,
    which is more appropriate for text embeddings.

    This implementation normalizes vectors to unit sphere and uses
    standard k-means, which is equivalent to spherical k-means.
    """

    def __init__(
        self,
        n_clusters: Optional[int] = None,
        max_iter: Optional[int] = None,
        n_init: Optional[int] = None,
        random_state: Optional[int] = None,
        tolerance: Optional[float] = None,
        verbose: bool = False,
    ):
        """
        Initialize spherical k-means.

        Args:
            n_clusters: Number of clusters (default from config)
            max_iter: Maximum iterations (default from config)
            n_init: Number of initializations (default from config)
            random_state: Random seed (default from config)
            tolerance: Convergence tolerance (default from config)
            verbose: Whether to print verbose output
        """
        config = get_config()

        self.n_clusters = n_clusters if n_clusters is not None else config.clustering.n_clusters
        self.max_iter = max_iter if max_iter is not None else config.clustering.max_iter
        self.n_init = n_init if n_init is not None else config.clustering.n_init
        self.random_state = random_state if random_state is not None else config.clustering.random_state
        self.tolerance = tolerance if tolerance is not None else config.clustering.tolerance
        self.verbose = verbose

        # Underlying k-means model
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            max_iter=self.max_iter,
            n_init=self.n_init,
            random_state=self.random_state,
            tol=self.tolerance,
            verbose=1 if self.verbose else 0,
        )

        self.cluster_centers_ = None
        self.labels_ = None
        self.inertia_ = None
        self.n_iter_ = None

        self.logger = logger

    def fit(self, embeddings: np.ndarray) -> 'SphericalKMeans':
        """
        Fit spherical k-means to embeddings.

        Args:
            embeddings: Embeddings array (N x D)

        Returns:
            Self (for chaining)
        """
        self.logger.info(f"Fitting spherical k-means with {self.n_clusters} clusters")
        self.logger.info(f"Input: {embeddings.shape[0]} samples, {embeddings.shape[1]} dimensions")

        # Normalize to unit sphere (L2 normalization)
        embeddings_normalized = normalize(embeddings, norm='l2', axis=1)
        self.logger.info("Embeddings normalized to unit sphere")

        # Fit standard k-means on normalized embeddings
        self.kmeans.fit(embeddings_normalized)

        # Store results
        self.cluster_centers_ = self.kmeans.cluster_centers_
        self.labels_ = self.kmeans.labels_
        self.inertia_ = self.kmeans.inertia_
        self.n_iter_ = self.kmeans.n_iter_

        self.logger.info(f"Clustering completed in {self.n_iter_} iterations")
        self.logger.info(f"Inertia: {self.inertia_:.4f}")

        # Compute cluster statistics
        self._log_cluster_stats()

        return self

    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Predict cluster labels for new embeddings.

        Args:
            embeddings: Embeddings array (N x D)

        Returns:
            Cluster labels (N,)
        """
        # Normalize
        embeddings_normalized = normalize(embeddings, norm='l2', axis=1)

        # Predict
        labels = self.kmeans.predict(embeddings_normalized)

        return labels

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Fit and predict in one step.

        Args:
            embeddings: Embeddings array (N x D)

        Returns:
            Cluster labels (N,)
        """
        self.fit(embeddings)
        return self.labels_

    def get_cluster_sizes(self) -> np.ndarray:
        """
        Get cluster sizes.

        Returns:
            Array of cluster sizes (n_clusters,)
        """
        if self.labels_ is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        unique, counts = np.unique(self.labels_, return_counts=True)
        return counts

    def get_cluster_statistics(self) -> dict:
        """
        Get statistics about the clustering.

        Returns:
            Dictionary of statistics
        """
        if self.labels_ is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        cluster_sizes = self.get_cluster_sizes()

        stats = {
            'n_clusters': self.n_clusters,
            'n_samples': len(self.labels_),
            'n_iterations': self.n_iter_,
            'inertia': float(self.inertia_),
            'cluster_sizes': {
                'mean': float(cluster_sizes.mean()),
                'std': float(cluster_sizes.std()),
                'min': int(cluster_sizes.min()),
                'max': int(cluster_sizes.max()),
                'median': float(np.median(cluster_sizes)),
            },
            'empty_clusters': int((cluster_sizes == 0).sum()),
        }

        return stats

    def _log_cluster_stats(self) -> None:
        """Log cluster statistics."""
        stats = self.get_cluster_statistics()

        self.logger.info(f"Cluster sizes - Mean: {stats['cluster_sizes']['mean']:.1f}, "
                        f"Median: {stats['cluster_sizes']['median']:.1f}, "
                        f"Min: {stats['cluster_sizes']['min']}, "
                        f"Max: {stats['cluster_sizes']['max']}")

        if stats['empty_clusters'] > 0:
            self.logger.warning(f"Found {stats['empty_clusters']} empty clusters")

    def compute_silhouette_score(self, embeddings: np.ndarray, sample_size: Optional[int] = None) -> float:
        """
        Compute silhouette score for the clustering.

        Note: This can be slow for large datasets. Use sample_size to subsample.

        Args:
            embeddings: Embeddings array (N x D)
            sample_size: Number of samples to use (default: all)

        Returns:
            Silhouette score (higher is better, range [-1, 1])
        """
        from sklearn.metrics import silhouette_score

        if self.labels_ is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        # Normalize embeddings
        embeddings_normalized = normalize(embeddings, norm='l2', axis=1)

        # Subsample if needed
        if sample_size is not None and sample_size < len(embeddings):
            indices = np.random.choice(len(embeddings), size=sample_size, replace=False)
            embeddings_normalized = embeddings_normalized[indices]
            labels = self.labels_[indices]
        else:
            labels = self.labels_

        self.logger.info(f"Computing silhouette score for {len(embeddings_normalized)} samples")

        # Compute silhouette score (use cosine metric)
        score = silhouette_score(embeddings_normalized, labels, metric='cosine')

        self.logger.info(f"Silhouette score: {score:.4f}")

        return score


def find_optimal_k_from_config(embeddings: np.ndarray) -> Tuple[int, dict]:
    """
    Run K-search using parameters from config/tnic_dl.yaml → k_search section.

    Convenience wrapper around find_optimal_k() that reads k_min, k_max, k_step,
    method, and silhouette_sample_size from the loaded config.

    Usage:
        from tnic_dl.similarity.spherical_kmeans import find_optimal_k_from_config
        optimal_k, results = find_optimal_k_from_config(embeddings)

    Returns:
        Tuple of (optimal_k, results_dict)
    """
    config = get_config()
    k_search = getattr(config, '_raw_config', {}).get('tnic_dl', {}).get('k_search', {})

    k_min = k_search.get('k_min', 30)
    k_max = k_search.get('k_max', 150)
    k_step = k_search.get('k_step', 10)
    method = k_search.get('method', 'elbow')

    k_range = range(k_min, k_max + 1, k_step)
    return find_optimal_k(embeddings, k_range=k_range, method=method,
                          random_state=config.clustering.random_state)


def find_optimal_k(
    embeddings: np.ndarray,
    k_range: range,
    method: str = 'elbow',
    random_state: int = 42,
) -> Tuple[int, dict]:
    """
    Find optimal number of clusters.

    Args:
        embeddings: Embeddings array (N x D)
        k_range: Range of k values to try (e.g., range(50, 501, 50))
        method: Method to use ('elbow' or 'silhouette')
        random_state: Random seed

    Returns:
        Tuple of (optimal_k, results_dict)
    """
    logger.info(f"Finding optimal K using {method} method")
    logger.info(f"K range: {k_range.start} to {k_range.stop} (step {k_range.step})")

    # Normalize embeddings once
    embeddings_normalized = normalize(embeddings, norm='l2', axis=1)

    results = {
        'k_values': [],
        'inertias': [],
        'silhouettes': [],
    }

    for k in k_range:
        logger.info(f"  Trying K={k}...")

        # Fit model
        model = SphericalKMeans(n_clusters=k, random_state=random_state)
        model.fit(embeddings)

        # Store results
        results['k_values'].append(k)
        results['inertias'].append(model.inertia_)

        # Compute silhouette if needed
        if method == 'silhouette':
            # Subsample for speed
            sample_size = min(5000, len(embeddings))
            score = model.compute_silhouette_score(embeddings, sample_size=sample_size)
            results['silhouettes'].append(score)

    # Find optimal K
    if method == 'elbow':
        # Use elbow method (find knee point in inertia curve)
        # Simple heuristic: maximum second derivative
        inertias = np.array(results['inertias'])
        second_diff = np.diff(inertias, n=2)
        optimal_idx = np.argmax(second_diff) + 1
        optimal_k = results['k_values'][optimal_idx]
        logger.info(f"Optimal K (elbow): {optimal_k}")

    elif method == 'silhouette':
        # Use maximum silhouette score
        optimal_idx = np.argmax(results['silhouettes'])
        optimal_k = results['k_values'][optimal_idx]
        logger.info(f"Optimal K (silhouette): {optimal_k}, score: {results['silhouettes'][optimal_idx]:.4f}")

    else:
        raise ValueError(f"Unknown method: {method}")

    return optimal_k, results
