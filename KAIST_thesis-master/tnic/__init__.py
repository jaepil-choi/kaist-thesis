"""
TNIC: Text-based Network Industry Classification

A Python implementation of the Hoberg & Phillips (2016) Text-based Network Industry
Classification methodology, adapted for Korean financial market data.

Citation:
    Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and
    endogenous product differentiation. Journal of Political Economy, 124(5), 1423-1465.

    Hoberg, G., & Phillips, G. M. (2018). Text-based industry momentum.
    Journal of Financial and Quantitative Analysis, 53(6), 2355-2388.

Modules:
    - config: Configuration management (YAML-based)
    - korean_text_processor: Korean text processing (kiwipiepy)
    - corpus_builder: Year-specific vocabulary construction
    - binary_matrix: Sparse binary matrix Q_t construction
    - similarity: Cosine similarity matrix M_t computation
    - data_loader: MongoDB and Parquet data loading
    - utils: Shared utilities

Quick Start:
    >>> from tnic import CorpusBuilder, BinaryMatrixBuilder, SimilarityComputer
    >>> from tnic.config import get_config
    >>>
    >>> # Build corpus for 2010
    >>> builder = CorpusBuilder()
    >>> firm_df, vocab_df, stats = builder.build_year_corpus(2010)
    >>>
    >>> # Build binary matrix
    >>> matrix_builder = BinaryMatrixBuilder()
    >>> Q_t, metadata = matrix_builder.build_matrix(2010)
    >>>
    >>> # Compute similarities
    >>> computer = SimilarityComputer()
    >>> M_t, metadata = computer.compute_similarity(2010)

Author: KAIST Thesis Project
Date: 2025-01-05
"""

__version__ = "0.1.0"
__author__ = "KAIST Thesis Project"

# Configuration (always available, lightweight)
from tnic.config import TNICConfig, get_config

# Lazy imports for heavy dependencies
# Only import when actually used to avoid loading pandas, pymongo, etc. during tests
def _lazy_import():
    """Lazy import of heavy dependencies."""
    global MongoDBLoader, ParquetLoader
    global KoreanTextProcessor
    global CorpusBuilder, BinaryMatrixBuilder, SimilarityComputer, PeerGroupBuilder
    global TNICPipeline
    global utils

    from tnic.data_loader import MongoDBLoader, ParquetLoader
    from tnic.korean_text_processor import KoreanTextProcessor
    from tnic.corpus_builder import CorpusBuilder
    from tnic.binary_matrix import BinaryMatrixBuilder
    from tnic.similarity import SimilarityComputer
    from tnic.peer_groups import PeerGroupBuilder
    from tnic.pipeline import TNICPipeline
    from tnic import utils

# Define __getattr__ for lazy loading
def __getattr__(name):
    """Lazy load modules on first access."""
    if name in [
        'MongoDBLoader', 'ParquetLoader',
        'KoreanTextProcessor',
        'CorpusBuilder', 'BinaryMatrixBuilder', 'SimilarityComputer', 'PeerGroupBuilder',
        'TNICPipeline',
        'utils'
    ]:
        _lazy_import()
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Configuration
    "TNICConfig",
    "get_config",

    # Data Loading
    "MongoDBLoader",
    "ParquetLoader",

    # Text Processing
    "KoreanTextProcessor",

    # Core Pipeline
    "CorpusBuilder",
    "BinaryMatrixBuilder",
    "SimilarityComputer",
    "PeerGroupBuilder",

    # Orchestration
    "TNICPipeline",

    # Utilities
    "utils",
]
