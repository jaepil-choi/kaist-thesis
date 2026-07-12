"""
Bag-of-Words Vectorizer for TNIC-DL.

Converts noun lists to binary vectors following Kim et al. (2020):
- Each firm is represented as a 2000-dimensional binary vector
- Vector element = 1 if word appears in firm's description, 0 otherwise
"""

from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, save_npz, load_npz
from tnic_dl.config import get_output_path
from tnic_dl.utils import setup_logger, save_json

logger = setup_logger(__name__)


class BagOfWordsVectorizer:
    """
    Convert noun lists to binary bag-of-words vectors.

    Following Kim et al. (2020) methodology:
    - Binary encoding (1 if word present, 0 otherwise)
    - Fixed vocabulary of 2000 words
    - Sparse matrix representation for efficiency
    """

    def __init__(self, vocabulary: Optional[List[str]] = None):
        """
        Initialize vectorizer.

        Args:
            vocabulary: List of vocabulary words (if None, must call fit() first)
        """
        self.vocabulary = vocabulary
        self.word_to_idx = None

        if vocabulary is not None:
            self._build_word_index()

        self.logger = logger

    def _build_word_index(self):
        """Build word to index mapping."""
        self.word_to_idx = {word: idx for idx, word in enumerate(self.vocabulary)}

    def fit(self, vocabulary: List[str]) -> 'BagOfWordsVectorizer':
        """
        Fit vectorizer with vocabulary.

        Args:
            vocabulary: List of vocabulary words

        Returns:
            Self (for chaining)
        """
        self.vocabulary = vocabulary
        self._build_word_index()
        self.logger.info(f"Fitted vectorizer with vocabulary size: {len(vocabulary)}")
        return self

    def transform(
        self,
        df: pd.DataFrame,
        return_firm_info: bool = True
    ) -> Tuple[csr_matrix, Optional[pd.DataFrame]]:
        """
        Transform noun lists to binary vectors.

        Args:
            df: DataFrame with columns: stock_code, year, unique_nouns (list)
            return_firm_info: Whether to return firm information DataFrame

        Returns:
            Tuple of (binary_matrix, firm_info_df)
            - binary_matrix: Sparse CSR matrix (N x V) where N=firms, V=vocabulary size
            - firm_info_df: DataFrame with firm identifiers (stock_code, year, firm_year)
        """
        if self.word_to_idx is None:
            raise ValueError("Vectorizer not fitted. Call fit() or provide vocabulary in constructor.")

        n_firms = len(df)
        vocab_size = len(self.vocabulary)

        self.logger.info(f"Transforming {n_firms} firms to binary vectors (vocab size: {vocab_size})")

        # Build sparse matrix efficiently
        rows = []
        cols = []

        for firm_idx, nouns_list in enumerate(df['unique_nouns']):
            # Get indices of words that appear in this firm's description
            word_indices = [
                self.word_to_idx[word]
                for word in set(nouns_list)  # Use set to avoid duplicates
                if word in self.word_to_idx
            ]

            # Add entries to sparse matrix
            rows.extend([firm_idx] * len(word_indices))
            cols.extend(word_indices)

        # Create sparse matrix (values are all 1s for binary encoding)
        data = np.ones(len(rows), dtype=np.int8)
        binary_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(n_firms, vocab_size),
            dtype=np.int8
        )

        self.logger.info(f"Created binary matrix: {binary_matrix.shape}, sparsity: {self._compute_sparsity(binary_matrix):.2%}")

        if return_firm_info:
            firm_info = df[['stock_code', 'year']].copy()
            firm_info['firm_year'] = firm_info['stock_code'] + '_' + firm_info['year'].astype(str)
            return binary_matrix, firm_info
        else:
            return binary_matrix, None

    def fit_transform(
        self,
        df: pd.DataFrame,
        vocabulary: List[str],
        return_firm_info: bool = True
    ) -> Tuple[csr_matrix, Optional[pd.DataFrame]]:
        """
        Fit vocabulary and transform data in one step.

        Args:
            df: DataFrame with noun lists
            vocabulary: Vocabulary list
            return_firm_info: Whether to return firm information

        Returns:
            Tuple of (binary_matrix, firm_info_df)
        """
        self.fit(vocabulary)
        return self.transform(df, return_firm_info)

    def save(
        self,
        year: int,
        binary_matrix: csr_matrix,
        firm_info: pd.DataFrame,
        vocabulary: Optional[List[str]] = None
    ) -> None:
        """
        Save binary matrix and metadata to disk.

        Args:
            year: Year of the data
            binary_matrix: Binary matrix to save
            firm_info: Firm information DataFrame
            vocabulary: Optional vocabulary list (if not already set)
        """
        if vocabulary is not None:
            self.vocabulary = vocabulary
            self._build_word_index()

        # Save binary matrix (sparse .npz format)
        matrix_path = get_output_path(year, f"binary_matrix_{year}.npz")
        save_npz(matrix_path, binary_matrix)
        self.logger.info(f"Saved binary matrix to {matrix_path}")

        # Save firm information
        firm_info_path = get_output_path(year, f"firm_info_{year}.parquet")
        firm_info.to_parquet(firm_info_path, index=False)
        self.logger.info(f"Saved firm info to {firm_info_path}")

        # Save metadata
        metadata = {
            'year': year,
            'n_firms': binary_matrix.shape[0],
            'vocab_size': binary_matrix.shape[1],
            'sparsity': self._compute_sparsity(binary_matrix),
            'nnz': binary_matrix.nnz,
            'dtype': str(binary_matrix.dtype),
            'vocabulary': self.vocabulary[:50],  # Save first 50 words only
        }
        metadata_path = get_output_path(year, f"binary_matrix_metadata_{year}.json")
        save_json(metadata, metadata_path)
        self.logger.info(f"Saved metadata to {metadata_path}")

    def load(self, year: int) -> Tuple[csr_matrix, pd.DataFrame]:
        """
        Load binary matrix and firm information from disk.

        Args:
            year: Year of the data

        Returns:
            Tuple of (binary_matrix, firm_info_df)
        """
        # Load binary matrix
        matrix_path = get_output_path(year, f"binary_matrix_{year}.npz", create_dir=False)
        binary_matrix = load_npz(matrix_path)
        self.logger.info(f"Loaded binary matrix from {matrix_path}: shape {binary_matrix.shape}")

        # Load firm information
        firm_info_path = get_output_path(year, f"firm_info_{year}.parquet", create_dir=False)
        firm_info = pd.read_parquet(firm_info_path)
        self.logger.info(f"Loaded firm info from {firm_info_path}: {len(firm_info)} firms")

        return binary_matrix, firm_info

    def _compute_sparsity(self, matrix: csr_matrix) -> float:
        """
        Compute sparsity of matrix (fraction of zeros).

        Args:
            matrix: Sparse matrix

        Returns:
            Sparsity as a fraction (0-1)
        """
        total_elements = matrix.shape[0] * matrix.shape[1]
        non_zero_elements = matrix.nnz
        return 1 - (non_zero_elements / total_elements)

    def get_vector_stats(self, binary_matrix: csr_matrix) -> dict:
        """
        Compute statistics about the binary vectors.

        Args:
            binary_matrix: Binary matrix (N x V)

        Returns:
            Dictionary of statistics
        """
        # Words per firm (row sums)
        words_per_firm = np.array(binary_matrix.sum(axis=1)).flatten()

        # Firms per word (column sums)
        firms_per_word = np.array(binary_matrix.sum(axis=0)).flatten()

        stats = {
            'n_firms': binary_matrix.shape[0],
            'vocab_size': binary_matrix.shape[1],
            'sparsity': self._compute_sparsity(binary_matrix),
            'words_per_firm': {
                'mean': float(words_per_firm.mean()),
                'std': float(words_per_firm.std()),
                'min': int(words_per_firm.min()),
                'max': int(words_per_firm.max()),
                'median': float(np.median(words_per_firm)),
            },
            'firms_per_word': {
                'mean': float(firms_per_word.mean()),
                'std': float(firms_per_word.std()),
                'min': int(firms_per_word.min()),
                'max': int(firms_per_word.max()),
                'median': float(np.median(firms_per_word)),
            },
        }

        return stats
