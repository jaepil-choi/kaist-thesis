"""
Binary Matrix Builder for TNIC Analysis

Builds sparse binary matrices Q_t following Hoberg & Phillips (2016) methodology.

Key Methodology (H&P 2016, Section II.A, p. 1429-1430):
    "A given firm i's vocabulary can be represented by a W-vector P_i, with each
     element being populated by the number 1 if firm i uses the given word and 0
     if it does not."

    "Q_t is an N_t × W matrix, where N_t is the number of firms in year t."

Matrix Format:
    - Q_t[i, j] = 1 if firm i uses word j, else 0
    - Binary representation (NOT frequency or TF-IDF)
    - Sparse CSR format for memory efficiency (typically 99%+ sparse)
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, lil_matrix, save_npz

from tnic.config import get_config
from tnic.data_loader import ParquetLoader
from tnic.utils import ensure_dir, format_bytes, setup_logger


class BinaryMatrixBuilder:
    """
    Build sparse binary matrices Q_t for TNIC analysis.

    Following H&P (2016), this class constructs binary firm-word matrices
    where Q_t[i,j] = 1 if firm i uses word j, else 0.

    Attributes:
        config: TNIC configuration
        loader: Parquet data loader
        logger: Logger instance
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize binary matrix builder.

        Args:
            config_path: Path to config directory (default: uses default config)

        Examples:
            >>> builder = BinaryMatrixBuilder()
            >>> Q_t, metadata = builder.build_matrix(2010)
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Initialize components
        self.loader = ParquetLoader(config_path=config_path)
        self.logger = setup_logger(__name__)

        self.logger.info("Binary matrix builder initialized")

    def build_matrix(
        self,
        year: int,
        save_output: bool = True
    ) -> Tuple[csr_matrix, Dict]:
        """
        Build binary matrix Q_t for a specific year.

        Args:
            year: Year to process
            save_output: Whether to save matrix to disk

        Returns:
            Tuple of (Q_t, metadata):
                - Q_t: Sparse binary matrix (N_t × W_t) in CSR format
                - metadata: Dictionary with matrix statistics

        Raises:
            FileNotFoundError: If corpus data not found for year

        Examples:
            >>> builder = BinaryMatrixBuilder()
            >>> Q_t, meta = builder.build_matrix(2010)
            >>> print(f"Matrix shape: {Q_t.shape}")
            Matrix shape: (964, 42804)
        """
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"BUILDING BINARY MATRIX Q_{year}")
        self.logger.info(f"{'=' * 80}")

        # Load firm word sets
        self.logger.info(f"Loading corpus data for {year}...")
        firm_df = self.loader.load_firm_word_sets(year)

        # Load vocabulary
        base_dir = self.config.get("paths.outputs.corpus.base_dir")
        year_dir = Path(str(base_dir).format(year=year))
        vocab_path = year_dir / f"corpus_vocabulary_{year}.csv"

        if not vocab_path.exists():
            raise FileNotFoundError(
                f"Vocabulary file not found: {vocab_path}\n"
                f"Please run corpus building for year {year} first."
            )

        vocab_df = pd.read_csv(vocab_path)

        # Get dimensions
        N_t = len(firm_df)  # Number of firms
        W_t = len(vocab_df)  # Number of words

        self.logger.info(f"Matrix dimensions:")
        self.logger.info(f"  N_{year} = {N_t:,} firms")
        self.logger.info(f"  W_{year} = {W_t:,} words")
        self.logger.info(f"  Total cells: {N_t * W_t:,}")

        # Build word to column index mapping
        self.logger.info("Building word-to-index mapping...")
        word_to_idx = {word: idx for idx, word in enumerate(vocab_df['word'])}

        # Construct sparse binary matrix
        self.logger.info(f"Constructing binary matrix (using sparse lil_matrix)...")

        # Use lil_matrix for efficient row-by-row construction
        Q_t = lil_matrix((N_t, W_t), dtype=np.int8)

        # Fill matrix
        for i, row in enumerate(firm_df.itertuples()):
            firm_words = row.unique_nouns  # numpy array of words

            # Set Q_t[i, j] = 1 for each word j used by firm i
            for word in firm_words:
                if word in word_to_idx:
                    j = word_to_idx[word]
                    Q_t[i, j] = 1

            # Progress indicator
            if (i + 1) % 200 == 0:
                pct = 100 * (i + 1) / N_t
                self.logger.info(f"  Processed {i + 1:,}/{N_t:,} firms ({pct:.1f}%)")

        self.logger.info("Matrix construction complete")

        # Convert to CSR format (efficient for operations and storage)
        self.logger.info("Converting to CSR format...")
        Q_t = Q_t.tocsr()

        # Validate matrix
        metadata = self._validate_matrix(Q_t, firm_df, vocab_df, year)

        # Save matrix
        if save_output:
            self._save_matrix(Q_t, firm_df, year, metadata)

        return Q_t, metadata

    def _validate_matrix(
        self,
        Q_t: csr_matrix,
        firm_df: pd.DataFrame,
        vocab_df: pd.DataFrame,
        year: int
    ) -> Dict:
        """
        Validate binary matrix and compute statistics.

        Args:
            Q_t: Binary matrix to validate
            firm_df: Firm dataframe (for row validation)
            vocab_df: Vocabulary dataframe (for column validation)
            year: Year

        Returns:
            Dictionary with validation results and statistics
        """
        self.logger.info("Validating matrix...")

        N_t, W_t = Q_t.shape

        # Check 1: Row sums should equal word counts
        row_sums = np.array(Q_t.sum(axis=1)).flatten()
        expected_counts = firm_df['word_count'].values

        row_validation_passed = np.allclose(row_sums, expected_counts)

        if row_validation_passed:
            self.logger.info("  ✓ Row sum validation passed")
        else:
            max_diff = np.abs(row_sums - expected_counts).max()
            self.logger.warning(f"  ✗ Row sum validation failed (max diff: {max_diff})")

        # Check 2: Column sums should match document frequency
        col_sums = np.array(Q_t.sum(axis=0)).flatten()
        expected_doc_freq = vocab_df['document_frequency'].values

        col_validation_passed = np.allclose(col_sums, expected_doc_freq)

        if col_validation_passed:
            self.logger.info("  ✓ Column sum validation passed")
        else:
            max_diff = np.abs(col_sums - expected_doc_freq).max()
            self.logger.warning(f"  ✗ Column sum validation failed (max diff: {max_diff})")

        # Check 3: Values should be binary (0 or 1)
        unique_values = np.unique(Q_t.data)
        binary_validation_passed = np.array_equal(unique_values, np.array([1], dtype=np.int8))

        if binary_validation_passed:
            self.logger.info("  ✓ Binary values validation passed")
        else:
            self.logger.warning(f"  ✗ Non-binary values found: {unique_values}")

        # Calculate sparsity
        nnz = Q_t.nnz  # Number of non-zero elements
        total_elements = N_t * W_t
        sparsity = 1 - (nnz / total_elements)

        # Memory usage
        dense_memory = N_t * W_t * 1  # 1 byte per element
        sparse_memory = nnz * 9  # CSR: 1 byte data + 8 bytes indices (approx)

        # Log statistics
        self.logger.info(f"Matrix statistics:")
        self.logger.info(f"  Non-zero elements: {nnz:,}")
        self.logger.info(f"  Sparsity: {sparsity * 100:.2f}%")
        self.logger.info(f"  Avg words per firm: {row_sums.mean():.1f}")
        self.logger.info(f"  Words range: [{row_sums.min()}, {row_sums.max()}]")

        self.logger.info(f"Memory usage:")
        self.logger.info(f"  Dense format: {format_bytes(dense_memory)}")
        self.logger.info(f"  Sparse format: {format_bytes(sparse_memory)}")
        self.logger.info(f"  Space savings: {100 * (1 - sparse_memory / dense_memory):.1f}%")

        # Build metadata
        metadata = {
            'year': year,
            'N_t': int(N_t),
            'W_t': int(W_t),
            'nnz': int(nnz),
            'sparsity': float(sparsity),
            'avg_words_per_firm': float(row_sums.mean()),
            'min_words': int(row_sums.min()),
            'max_words': int(row_sums.max()),
            'dense_memory_bytes': int(dense_memory),
            'sparse_memory_bytes': int(sparse_memory),
            'validation': {
                'row_sums': row_validation_passed,
                'col_sums': col_validation_passed,
                'binary_values': binary_validation_passed
            }
        }

        return metadata

    def _save_matrix(
        self,
        Q_t: csr_matrix,
        firm_df: pd.DataFrame,
        year: int,
        metadata: Dict
    ):
        """
        Save binary matrix and metadata to disk.

        Args:
            Q_t: Binary matrix
            firm_df: Firm dataframe (for firm mapping)
            year: Year
            metadata: Metadata dictionary
        """
        self.logger.info(f"Saving binary matrix for {year}...")

        # Get output directory
        base_dir = self.config.get("paths.outputs.binary_matrix.base_dir")
        if base_dir is None:
            raise ValueError("Output directory not configured")

        output_dir = Path(base_dir)
        ensure_dir(output_dir)

        # Save matrix
        matrix_path = output_dir / f"binary_matrix_{year}.npz"
        save_npz(matrix_path, Q_t)

        file_size = matrix_path.stat().st_size
        self.logger.info(f"  Saved matrix: {matrix_path}")
        self.logger.info(f"  File size: {format_bytes(file_size)}")

        # Save firm mapping (stock_code to row index)
        firms_path = output_dir / f"binary_firms_{year}.csv"
        firm_mapping = firm_df[['stock_code', 'firm_year']].copy()
        firm_mapping['row_index'] = range(len(firm_mapping))
        firm_mapping.to_csv(firms_path, index=False)
        self.logger.info(f"  Saved firm mapping: {firms_path}")

        # Update metadata file
        metadata_path = output_dir / "binary_matrices_metadata.json"

        # Load existing metadata if it exists
        import json
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                all_metadata = json.load(f)
        else:
            all_metadata = {}

        # Add this year's metadata
        all_metadata[str(year)] = metadata

        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(all_metadata, f, indent=2)

        self.logger.info(f"  Updated metadata: {metadata_path}")

    def build_all_matrices(
        self,
        years: Optional[list] = None,
        mode: str = "full"
    ) -> Dict[int, Dict]:
        """
        Build binary matrices for multiple years.

        Args:
            years: List of years to process (if None, uses config)
            mode: "full" (all years) or "pilot" (pilot years only)

        Returns:
            Dictionary mapping year to metadata

        Examples:
            >>> builder = BinaryMatrixBuilder()
            >>> results = builder.build_all_matrices(mode="pilot")
        """
        # Get years to process
        if years is None:
            years = list(self.config.get_year_range(mode))

        self.logger.info(f"Building binary matrices for {len(years)} years")

        all_metadata = {}

        for year in years:
            try:
                _, metadata = self.build_matrix(year, save_output=True)
                all_metadata[year] = metadata
            except Exception as e:
                self.logger.error(f"Error processing year {year}: {e}")
                all_metadata[year] = {'status': 'failed', 'error': str(e)}

        # Summary
        successful = [y for y, m in all_metadata.items() if m.get('status') != 'failed']
        failed = [y for y, m in all_metadata.items() if m.get('status') == 'failed']

        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"BINARY MATRIX CONSTRUCTION COMPLETE")
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"  Successful: {len(successful)} years")
        if failed:
            self.logger.warning(f"  Failed: {len(failed)} years: {failed}")

        return all_metadata

    def __repr__(self) -> str:
        """String representation."""
        return "BinaryMatrixBuilder()"
