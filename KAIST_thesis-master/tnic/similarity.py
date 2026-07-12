"""
Similarity Matrix Computation for TNIC Analysis

Computes pairwise cosine similarity matrices M_t following Hoberg & Phillips (2016).

Key Methodology (H&P 2016, Section II.A, p. 1430):
    "Product Cosine Similarity_{i,j} = (V_i * V_j)"

    Where V_i is the normalized unit-length vector for firm i.

Matrix Properties:
    - M_t[i,j] = cosine similarity between firm i and j
    - Symmetric: M_t[i,j] = M_t[j,i]
    - Diagonal = 1.0 (firms perfectly similar to themselves)
    - Range: [0, 1] where 1 = identical vocabularies

Median Adjustment (H&P 2016, p. 1436):
    "We compute its median score as the median similarity between firm i and all
     other firms... We achieve this by subtracting these median scores from the raw
     scores to obtain our final scores."
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, load_npz
from sklearn.metrics.pairwise import cosine_similarity

from tnic.config import get_config
from tnic.utils import ensure_dir, format_bytes, setup_logger


class SimilarityComputer:
    """
    Compute cosine similarity matrices M_t for TNIC analysis.

    Following H&P (2016), this class computes pairwise cosine similarities
    from binary matrices and optionally applies median adjustment.

    Attributes:
        config: TNIC configuration
        logger: Logger instance
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize similarity computer.

        Args:
            config_path: Path to config directory (default: uses default config)

        Examples:
            >>> computer = SimilarityComputer()
            >>> M_t, meta = computer.compute_similarity(2010)
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Initialize logger
        self.logger = setup_logger(__name__)

        # Get parameters
        self.apply_median_adjustment = self.config.get(
            "hp.similarity.median_adjustment",
            True
        )

        self.logger.info("Similarity computer initialized")
        self.logger.info(f"  Median adjustment: {self.apply_median_adjustment}")

    def compute_similarity(
        self,
        year: int,
        Q_t: Optional[csr_matrix] = None,
        save_output: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        Compute cosine similarity matrix M_t for a specific year.

        Args:
            year: Year to process
            Q_t: Binary matrix (if None, loads from file)
            save_output: Whether to save matrix to disk

        Returns:
            Tuple of (M_t, metadata):
                - M_t: Similarity matrix (N_t × N_t)
                - metadata: Dictionary with matrix statistics

        Examples:
            >>> computer = SimilarityComputer()
            >>> M_t, meta = computer.compute_similarity(2010)
            >>> print(f"Mean similarity: {meta['off_diagonal']['mean']:.4f}")
        """
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"COMPUTING SIMILARITY MATRIX M_{year}")
        self.logger.info(f"{'=' * 80}")

        # Load binary matrix if not provided
        if Q_t is None:
            self.logger.info(f"Loading binary matrix Q_{year}...")
            Q_t = self._load_binary_matrix(year)

        N_t, W_t = Q_t.shape

        self.logger.info(f"Binary matrix Q_{year}:")
        self.logger.info(f"  Shape: {N_t:,} firms × {W_t:,} words")
        self.logger.info(f"  Non-zeros: {Q_t.nnz:,}")

        # Load firm identifiers
        firms_df = self._load_firm_mapping(year)

        if len(firms_df) != N_t:
            self.logger.warning(
                f"Firm count mismatch: {len(firms_df)} in mapping vs {N_t} in matrix"
            )

        # Compute similarity matrix
        self.logger.info(f"Computing cosine similarity matrix...")
        self.logger.info(f"  Formula: M_t = Q_t × Q_t^T / (||Q_t|| × ||Q_t||^T)")
        self.logger.info(f"  Output shape: {N_t:,} × {N_t:,}")

        # Memory estimate
        memory_mb = (N_t * N_t * 8) / (1024 ** 2)  # 8 bytes per float64
        self.logger.info(f"  Memory estimate: {format_bytes(int(memory_mb * 1024 ** 2))}")

        # Compute raw similarity (sklearn handles sparse input efficiently)
        M_t_raw = cosine_similarity(Q_t)

        self.logger.info(f"Raw similarity matrix computed:")
        self.logger.info(f"  Shape: {M_t_raw.shape}")
        self.logger.info(f"  Dtype: {M_t_raw.dtype}")

        # Apply median adjustment if enabled (H&P 2016, p. 1436)
        if self.apply_median_adjustment:
            self.logger.info(f"Applying median adjustment (H&P 2016, p. 1436)...")
            M_t, median_stats = self._apply_median_adjustment(M_t_raw)
        else:
            self.logger.info(f"Median adjustment: disabled")
            M_t = M_t_raw
            median_stats = None

        # Validate and compute statistics
        metadata = self._validate_and_analyze(M_t, year, median_adjusted=self.apply_median_adjustment)

        # Add median adjustment statistics to metadata (H&P 2016, p. 1436)
        if median_stats is not None:
            metadata['median_adjustment'] = median_stats
            self.logger.info(f"Added median adjustment statistics to metadata")

        # Save output
        if save_output:
            self._save_similarity_matrix(M_t, firms_df, year, metadata)

        return M_t, metadata

    def _apply_median_adjustment(
        self,
        M_t: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply median adjustment to similarity matrix.

        Following H&P (2016, p. 1436):
        "For a firm i we compute its median score as the median similarity between
         firm i and all other firms... We achieve this by subtracting these median
         scores from the raw scores to obtain our final scores."

        Args:
            M_t: Raw similarity matrix (N_t × N_t)

        Returns:
            Tuple of (adjusted_matrix, statistics):
                - adjusted_matrix: Median-adjusted similarity matrix
                - statistics: Dictionary with median adjustment statistics

        Examples:
            >>> M_raw = np.array([[1.0, 0.3, 0.2], [0.3, 1.0, 0.15], [0.2, 0.15, 1.0]])
            >>> M_adj, stats = self._apply_median_adjustment(M_raw)
        """
        N_t = M_t.shape[0]

        self.logger.info(f"Computing per-firm median scores...")

        # Step 1: Compute median score for each firm
        # Median similarity between firm i and all OTHER firms (exclude diagonal)
        median_scores = np.zeros(N_t)

        for i in range(N_t):
            # Get all similarities for firm i
            similarities = M_t[i, :].copy()

            # Exclude self-similarity (diagonal)
            similarities = np.delete(similarities, i)

            # Compute median
            median_scores[i] = np.median(similarities)

        # Step 2: Adjust similarity matrix
        # Symmetric adjustment: use average of both firms' medians
        self.logger.info(f"Adjusting similarity matrix (symmetric method)...")

        M_adjusted = M_t.copy()

        for i in range(N_t):
            for j in range(N_t):
                if i != j:  # Don't adjust diagonal
                    # Symmetric adjustment: average both medians
                    avg_median = (median_scores[i] + median_scores[j]) / 2.0
                    M_adjusted[i, j] = M_t[i, j] - avg_median

        # Diagonal remains 1.0 (self-similarity not adjusted)
        np.fill_diagonal(M_adjusted, 1.0)

        # Step 3: Compute statistics
        median_stats = {
            'mean_median': float(median_scores.mean()),
            'std_median': float(median_scores.std()),
            'min_median': float(median_scores.min()),
            'max_median': float(median_scores.max())
        }

        self.logger.info(f"Median score statistics:")
        self.logger.info(f"  Mean: {median_stats['mean_median']:.6f}")
        self.logger.info(f"  Std: {median_stats['std_median']:.6f}")
        self.logger.info(f"  Range: [{median_stats['min_median']:.6f}, {median_stats['max_median']:.6f}]")

        # Note: Adjusted matrix may have negative values
        # This is expected and correct per H&P methodology
        min_adjusted = M_adjusted.min()
        if min_adjusted < 0:
            neg_count = (M_adjusted < 0).sum()
            total_count = N_t * N_t
            neg_pct = 100.0 * neg_count / total_count
            self.logger.info(f"  Negative values: {neg_count:,}/{total_count:,} ({neg_pct:.2f}%)")
            self.logger.info(f"  Min adjusted value: {min_adjusted:.6f}")
            self.logger.info(f"  (Negative values are expected after median adjustment)")

        return M_adjusted, median_stats

    def _load_binary_matrix(self, year: int) -> csr_matrix:
        """
        Load binary matrix Q_t from disk.

        Args:
            year: Year

        Returns:
            Binary matrix Q_t

        Raises:
            FileNotFoundError: If matrix not found
        """
        base_dir = self.config.get("paths.outputs.binary_matrix.base_dir")
        if base_dir is None:
            raise ValueError("Binary matrix directory not configured")

        matrix_path = Path(base_dir) / f"binary_matrix_{year}.npz"

        if not matrix_path.exists():
            raise FileNotFoundError(
                f"Binary matrix not found: {matrix_path}\n"
                f"Please run binary matrix building for year {year} first."
            )

        Q_t = load_npz(matrix_path)
        return Q_t

    def _load_firm_mapping(self, year: int) -> pd.DataFrame:
        """
        Load firm identifier mapping.

        Args:
            year: Year

        Returns:
            DataFrame with firm identifiers

        Raises:
            FileNotFoundError: If mapping not found
        """
        base_dir = self.config.get("paths.outputs.corpus.base_dir")
        if base_dir is None:
            raise ValueError("Corpus directory not configured")

        year_dir = Path(str(base_dir).format(year=year))
        firms_path = year_dir / f"firm_word_sets_{year}.parquet"

        if not firms_path.exists():
            raise FileNotFoundError(
                f"Firm mapping not found: {firms_path}\n"
                f"Please run corpus building for year {year} first."
            )

        firms_df = pd.read_parquet(firms_path)
        return firms_df

    def _validate_and_analyze(self, M_t: np.ndarray, year: int, median_adjusted: bool = False) -> Dict:
        """
        Validate similarity matrix and compute statistics.

        Args:
            M_t: Similarity matrix
            year: Year
            median_adjusted: Whether matrix has been median-adjusted

        Returns:
            Dictionary with validation results and statistics
        """
        self.logger.info("Validating similarity matrix...")

        N_t = M_t.shape[0]

        # Validation checks
        validation = {}

        # Check 1: Diagonal should be 1.0
        diagonal = np.diag(M_t)
        diagonal_check = np.allclose(diagonal, 1.0)
        max_diag_diff = np.abs(diagonal - 1.0).max()

        validation['diagonal'] = bool(diagonal_check)  # Convert numpy bool to Python bool

        if diagonal_check:
            self.logger.info("  ✓ Diagonal validation passed (all ≈ 1.0)")
        else:
            self.logger.warning(f"  ✗ Diagonal not all 1.0, max diff: {max_diag_diff:.6f}")

        # Check 2: Symmetry
        is_symmetric = np.allclose(M_t, M_t.T)
        validation['symmetric'] = bool(is_symmetric)  # Convert numpy bool to Python bool

        if is_symmetric:
            self.logger.info("  ✓ Symmetry validation passed")
        else:
            max_sym_diff = np.abs(M_t - M_t.T).max()
            self.logger.warning(f"  ✗ Not symmetric, max diff: {max_sym_diff:.6f}")

        # Check 3: Value range
        min_val = float(M_t.min())
        max_val = float(M_t.max())

        # After median adjustment, values can be negative (H&P 2016, p. 1436)
        # Only diagonal must remain 1.0
        if median_adjusted:
            # Adjusted matrix: no specific range constraint, but diagonal should be 1.0
            range_check = True  # Diagonal check done separately
            validation['range'] = bool(range_check)
            self.logger.info(f"  ✓ Value range (median-adjusted): [{min_val:.6f}, {max_val:.6f}]")
            if min_val < 0:
                neg_count = (M_t < 0).sum()
                total_count = M_t.size
                neg_pct = 100.0 * neg_count / total_count
                self.logger.info(f"    (Negative values: {neg_count:,}/{total_count:,} = {neg_pct:.2f}% - expected)")
        else:
            # Raw matrix: should be [0, 1]
            range_check = (min_val >= 0) and (max_val <= 1)
            validation['range'] = bool(range_check)

            if range_check:
                self.logger.info(f"  ✓ Value range check passed: [{min_val:.6f}, {max_val:.6f}]")
            else:
                self.logger.warning(f"  ✗ Values outside [0, 1]: [{min_val:.6f}, {max_val:.6f}]")

        # Check 4: NaN or inf
        has_nan = bool(np.isnan(M_t).any())
        has_inf = bool(np.isinf(M_t).any())
        no_invalid = not has_nan and not has_inf

        validation['no_invalid'] = bool(no_invalid)  # Convert to Python bool

        if no_invalid:
            self.logger.info("  ✓ No NaN or inf values")
        else:
            self.logger.warning(f"  ✗ Found NaN={has_nan}, inf={has_inf}")

        # Compute off-diagonal statistics
        self.logger.info("Computing statistics...")

        off_diag_mask = ~np.eye(N_t, dtype=bool)
        off_diag_vals = M_t[off_diag_mask]

        off_diag_stats = {
            'mean': float(off_diag_vals.mean()),
            'median': float(np.median(off_diag_vals)),
            'std': float(off_diag_vals.std()),
            'min': float(off_diag_vals.min()),
            'max': float(off_diag_vals.max()),
            'p50': float(np.percentile(off_diag_vals, 50)),
            'p75': float(np.percentile(off_diag_vals, 75)),
            'p90': float(np.percentile(off_diag_vals, 90)),
            'p95': float(np.percentile(off_diag_vals, 95)),
            'p99': float(np.percentile(off_diag_vals, 99))
        }

        self.logger.info(f"Off-diagonal statistics:")
        self.logger.info(f"  Mean: {off_diag_stats['mean']:.4f}")
        self.logger.info(f"  Median: {off_diag_stats['median']:.4f}")
        self.logger.info(f"  Std: {off_diag_stats['std']:.4f}")
        self.logger.info(f"  Range: [{off_diag_stats['min']:.4f}, {off_diag_stats['max']:.4f}]")
        self.logger.info(f"  Percentiles: p75={off_diag_stats['p75']:.4f}, p95={off_diag_stats['p95']:.4f}")

        # Network density at thresholds
        thresholds = [0.1, 0.15, 0.2, 0.25, 0.3]
        threshold_stats = {}

        self.logger.info(f"Network density at thresholds:")

        for thresh in thresholds:
            above_thresh = (M_t >= thresh) & off_diag_mask
            n_pairs = above_thresh.sum() // 2  # Symmetric matrix
            pct_pairs = 100 * n_pairs / (N_t * (N_t - 1) / 2)

            # Average peers per firm
            peers_per_firm = above_thresh.sum(axis=1)
            avg_peers = peers_per_firm.mean()

            threshold_stats[str(thresh)] = {
                'n_pairs': int(n_pairs),
                'pct_pairs': float(pct_pairs),
                'avg_peers': float(avg_peers)
            }

            self.logger.info(
                f"  Threshold {thresh:.2f}: {pct_pairs:.2f}% pairs, "
                f"avg {avg_peers:.1f} peers/firm"
            )

        # Build metadata
        metadata = {
            'year': year,
            'N_t': int(N_t),
            'validation': validation,
            'off_diagonal': off_diag_stats,
            'threshold_stats': threshold_stats
        }

        return metadata

    def _save_similarity_matrix(
        self,
        M_t: np.ndarray,
        firms_df: pd.DataFrame,
        year: int,
        metadata: Dict
    ):
        """
        Save similarity matrix and metadata to disk.

        Args:
            M_t: Similarity matrix
            firms_df: Firm dataframe
            year: Year
            metadata: Metadata dictionary
        """
        self.logger.info(f"Saving similarity matrix for {year}...")

        # Get output directory
        base_dir = self.config.get("paths.outputs.similarity.base_dir")
        if base_dir is None:
            raise ValueError("Output directory not configured")

        output_dir = Path(base_dir)
        ensure_dir(output_dir)

        # Save matrix as NPZ (compressed)
        matrix_path = output_dir / f"similarity_matrix_{year}.npz"
        np.savez_compressed(matrix_path, similarity_matrix=M_t)

        file_size = matrix_path.stat().st_size
        self.logger.info(f"  Saved matrix: {matrix_path}")
        self.logger.info(f"  File size: {format_bytes(file_size)}")

        # Save firm mapping (for row/column indices)
        firms_path = output_dir / f"similarity_firms_{year}.csv"
        firm_mapping = firms_df[['stock_code', 'firm_year']].copy()
        firm_mapping['index'] = range(len(firm_mapping))
        firm_mapping.to_csv(firms_path, index=False)
        self.logger.info(f"  Saved firm mapping: {firms_path}")

        # Update metadata file
        metadata_path = output_dir / "similarity_matrices_metadata.json"

        # Load existing metadata if exists
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    all_metadata = json.load(f)
            except json.JSONDecodeError as e:
                self.logger.warning(f"  Corrupted metadata file, recreating: {e}")
                all_metadata = {}
        else:
            all_metadata = {}

        # Add this year's metadata
        all_metadata[str(year)] = metadata

        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(all_metadata, f, indent=2)

        self.logger.info(f"  Updated metadata: {metadata_path}")

    def compute_all_similarities(
        self,
        years: Optional[list] = None,
        mode: str = "full"
    ) -> Dict[int, Dict]:
        """
        Compute similarity matrices for multiple years.

        Args:
            years: List of years to process (if None, uses config)
            mode: "full" (all years) or "pilot" (pilot years only)

        Returns:
            Dictionary mapping year to metadata

        Examples:
            >>> computer = SimilarityComputer()
            >>> results = computer.compute_all_similarities(mode="pilot")
        """
        # Get years to process
        if years is None:
            years = list(self.config.get_year_range(mode))

        self.logger.info(f"Computing similarity matrices for {len(years)} years")

        all_metadata = {}

        for year in years:
            try:
                _, metadata = self.compute_similarity(year, save_output=True)
                all_metadata[year] = metadata
            except Exception as e:
                self.logger.error(f"Error processing year {year}: {e}")
                all_metadata[year] = {'status': 'failed', 'error': str(e)}

        # Summary
        successful = [y for y, m in all_metadata.items() if m.get('status') != 'failed']
        failed = [y for y, m in all_metadata.items() if m.get('status') == 'failed']

        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"SIMILARITY COMPUTATION COMPLETE")
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"  Successful: {len(successful)} years")
        if failed:
            self.logger.warning(f"  Failed: {len(failed)} years: {failed}")

        return all_metadata

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SimilarityComputer("
            f"median_adjustment={self.apply_median_adjustment})"
        )
