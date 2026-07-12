"""
Text Data Cleaner for TNIC Pipeline

Implements Phase 1b: Data cleaning for raw MongoDB business descriptions.

Cleaning Steps:
1. Remove zero-length documents
2. Truncate to 95th percentile (per year) - NEW METHOD (not exclusion)
3. Level-based deduplication (prefer level=2)
4. Firm-year deduplication (keep latest report)

This replaces the temporary cleaning logic in scripts/extract_korean_texts.py
with a permanent, reusable component in the tnic module.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import numpy as np

from tnic.config import get_config
from tnic.utils import ensure_dir, setup_logger


class TextCleaner:
    """
    Text data cleaner for TNIC pipeline Phase 1b.

    Applies validated cleaning steps to raw MongoDB business descriptions,
    using the truncation method (not exclusion) for outlier handling.

    Attributes:
        config: TNIC configuration
        logger: Logger instance
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Text Cleaner.

        Args:
            config_path: Path to config directory (default: uses default config)
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Initialize logger
        self.logger = setup_logger(__name__)

        self.logger.info("TextCleaner initialized")

    def _remove_zero_length(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Step 1: Remove documents with zero or negative character counts.

        Args:
            df: Input DataFrame with 'char_count' column

        Returns:
            Cleaned DataFrame, number of rows removed
        """
        n_before = len(df)
        df_clean = df[df['char_count'] > 0].copy()
        n_removed = n_before - len(df_clean)

        return df_clean, n_removed

    def _truncate_to_percentile(
        self,
        df: pd.DataFrame,
        percentile: int = 95
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Step 2: Truncate text to per-year percentile threshold.

        NEW METHOD: Instead of EXCLUDING documents > threshold,
        TRUNCATE them to the threshold length.

        This preserves all firms (0% loss) while removing outlier noise.

        Args:
            df: Input DataFrame with 'text', 'char_count', 'year' columns
            percentile: Percentile to use as cutoff (default: 95)

        Returns:
            Cleaned DataFrame with truncated text, statistics dict
        """
        df_clean = df.copy()

        # Ensure year is int for grouping
        if df_clean['year'].dtype == 'object':
            df_clean['year'] = df_clean['year'].astype(int)

        # Track statistics per year
        year_stats = {}
        total_truncated = 0

        # Process each year separately
        for year in sorted(df_clean['year'].unique()):
            year_mask = df_clean['year'] == year

            # Calculate year-specific percentile
            cutoff = np.percentile(df_clean.loc[year_mask, 'char_count'], percentile)

            # Count documents to truncate
            to_truncate_mask = year_mask & (df_clean['char_count'] > cutoff)
            n_to_truncate = to_truncate_mask.sum()

            # Truncate text to cutoff
            if n_to_truncate > 0:
                df_clean.loc[to_truncate_mask, 'text'] = \
                    df_clean.loc[to_truncate_mask, 'text'].str[:int(cutoff)]

                # Update char_count to reflect truncation
                df_clean.loc[to_truncate_mask, 'char_count'] = \
                    df_clean.loc[to_truncate_mask, 'text'].str.len()

            # Store stats
            year_stats[year] = {
                'cutoff': int(cutoff),
                'n_truncated': int(n_to_truncate),
                'pct_truncated': float(n_to_truncate / year_mask.sum() * 100) if year_mask.sum() > 0 else 0.0
            }

            total_truncated += n_to_truncate

        stats = {
            'total_truncated': total_truncated,
            'by_year': year_stats
        }

        return df_clean, stats

    def _deduplicate_by_level(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Step 3: Level-based deduplication.

        Prefer level=2 (granular subsection) over level=1 (merged section)
        for duplicate rcept_no (receipt numbers).

        Args:
            df: Input DataFrame with 'rcept_no', 'level' columns

        Returns:
            Cleaned DataFrame, number of rows removed
        """
        n_before = len(df)

        # Handle missing level field
        df_clean = df.copy()
        if 'level' not in df_clean.columns:
            df_clean['level'] = 1
            self.logger.warning("  'level' field missing, assuming level=1 for all documents")

        # Sort: prefer level=2 over level=1 for same rcept_no
        df_clean = df_clean.sort_values(['rcept_no', 'level'], ascending=[True, False])
        df_clean = df_clean.drop_duplicates(subset=['rcept_no'], keep='first')

        n_removed = n_before - len(df_clean)

        return df_clean, n_removed

    def _deduplicate_firm_year(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Step 4: Firm-year deduplication.

        Keep only the latest report per (stock_code, year) combination.
        Some firms file multiple reports per year (amendments, corrections).

        Args:
            df: Input DataFrame with 'stock_code', 'year', 'rcept_dt' columns

        Returns:
            Cleaned DataFrame, number of rows removed
        """
        n_before = len(df)

        # Sort by rcept_dt descending (latest first)
        df_clean = df.sort_values('rcept_dt', ascending=False)

        # Drop duplicates, keeping first (latest)
        df_clean = df_clean.drop_duplicates(subset=['stock_code', 'year'], keep='first')

        n_removed = n_before - len(df_clean)

        # Sort by stock_code and year for consistent output
        df_clean = df_clean.sort_values(['stock_code', 'year']).reset_index(drop=True)

        return df_clean, n_removed

    def clean(
        self,
        df: pd.DataFrame,
        year_range: Optional[Tuple[int, int]] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply all cleaning steps to raw MongoDB data.

        Steps (in order):
        1. Remove zero-length documents
        2. Truncate to 95th percentile (per year)
        3. Level-based deduplication
        4. Firm-year deduplication

        Args:
            df: Raw DataFrame from MongoDB extraction
            year_range: (start_year, end_year) for filtering (optional)

        Returns:
            df_clean: Cleaned DataFrame
            stats: Cleaning statistics dictionary
        """
        self.logger.info("Applying cleaning steps...")

        # Track initial state
        n_initial = len(df)

        # Handle empty DataFrames (years with no data)
        if n_initial == 0:
            self.logger.warning("  No documents to clean (empty DataFrame)")
            return df, {
                'n_initial': 0,
                'n_final': 0,
                'n_firms_initial': 0,
                'n_firms_final': 0,
                'n_removed_zero_length': 0,
                'n_removed_level_dedup': 0,
                'n_removed_firmyear_dedup': 0,
                'truncation_stats': {'total_truncated': 0, 'by_year': {}},
                'retention_rate_pct': 0.0,
                'firm_retention_rate_pct': 0.0
            }

        n_firms_initial = df['stock_code'].nunique()

        self.logger.info(f"  Initial: {n_initial:,} documents, {n_firms_initial:,} unique firms")

        # Step 1: Remove zero-length documents
        self.logger.info("  Step 1: Removing zero-length documents...")
        df_clean, n_removed_zero = self._remove_zero_length(df)
        self.logger.info(f"    Removed: {n_removed_zero:,} documents")

        # Step 2: Truncate to 95th percentile (NEW METHOD)
        self.logger.info("  Step 2: Truncating to 95th percentile (per year)...")
        df_clean, truncate_stats = self._truncate_to_percentile(df_clean, percentile=95)
        self.logger.info(f"    Truncated: {truncate_stats['total_truncated']:,} documents")

        # Show per-year truncation stats
        for year, ystats in sorted(truncate_stats['by_year'].items()):
            self.logger.info(
                f"      {year}: cutoff={ystats['cutoff']:,} chars, "
                f"truncated={ystats['n_truncated']:,} ({ystats['pct_truncated']:.1f}%)"
            )

        # Step 3: Level-based deduplication
        self.logger.info("  Step 3: Level-based deduplication...")
        df_clean, n_removed_level = self._deduplicate_by_level(df_clean)
        self.logger.info(f"    Removed: {n_removed_level:,} duplicate rcept_no")

        # Step 4: Firm-year deduplication
        self.logger.info("  Step 4: Firm-year deduplication...")
        df_clean, n_removed_firmyear = self._deduplicate_firm_year(df_clean)
        self.logger.info(f"    Removed: {n_removed_firmyear:,} duplicate firm-years")

        # Final stats
        n_final = len(df_clean)
        n_firms_final = df_clean['stock_code'].nunique()

        self.logger.info(f"  Final: {n_final:,} documents, {n_firms_final:,} unique firms")

        retention_rate = 100 * n_final / n_initial if n_initial > 0 else 0
        firm_retention_rate = 100 * n_firms_final / n_firms_initial if n_firms_initial > 0 else 0

        self.logger.info(f"  Document retention: {retention_rate:.1f}%")
        self.logger.info(f"  Firm retention: {firm_retention_rate:.1f}%")

        # Compile statistics
        stats = {
            'n_initial': n_initial,
            'n_final': n_final,
            'n_firms_initial': n_firms_initial,
            'n_firms_final': n_firms_final,
            'n_removed_zero_length': n_removed_zero,
            'n_removed_level_dedup': n_removed_level,
            'n_removed_firmyear_dedup': n_removed_firmyear,
            'truncation_stats': truncate_stats,
            'retention_rate_pct': retention_rate,
            'firm_retention_rate_pct': firm_retention_rate
        }

        return df_clean, stats

    def run(
        self,
        input_path: Path,
        output_path: Path,
        year_range: Tuple[int, int]
    ) -> Dict:
        """
        Main execution method: load → clean → save.

        Args:
            input_path: Path to raw extraction (business_descriptions_raw.parquet)
            output_path: Path to save cleaned data (business_descriptions_clean.parquet)
            year_range: (start_year, end_year)

        Returns:
            Dictionary with results and statistics

        Examples:
            >>> cleaner = TextCleaner()
            >>> result = cleaner.run(
            ...     input_path="data/korean_texts/business_descriptions_raw.parquet",
            ...     output_path="data/korean_texts/business_descriptions_clean.parquet",
            ...     year_range=(2010, 2025)
            ... )
        """
        self.logger.info("=" * 80)
        self.logger.info("TEXT DATA CLEANING")
        self.logger.info("=" * 80)

        # Step 1: Load raw data
        self.logger.info(f"\nStep 1: Loading raw data from {input_path}...")
        df_raw = pd.read_parquet(input_path)
        self.logger.info(f"  Loaded {len(df_raw):,} documents")

        # Step 2: Apply cleaning
        self.logger.info(f"\nStep 2: Applying cleaning steps...")
        df_clean, stats = self.clean(df_raw, year_range=year_range)

        # Step 3: Save cleaned data
        self.logger.info(f"\nStep 3: Saving cleaned data...")
        ensure_dir(output_path.parent)
        df_clean.to_parquet(output_path, index=False)
        self.logger.info(f"  [OK] Saved: {output_path}")

        # Step 4: Save statistics
        stats_path = output_path.parent / "cleaning_stats.json"
        # Convert numpy types to Python types for JSON serialization
        stats_json = self._prepare_stats_for_json(stats)
        with open(stats_path, 'w') as f:
            json.dump(stats_json, f, indent=2)
        self.logger.info(f"  [OK] Saved stats: {stats_path}")

        self.logger.info("\n" + "=" * 80)
        self.logger.info("TEXT DATA CLEANING COMPLETE")
        self.logger.info("=" * 80)

        return {
            'output': str(output_path),
            'stats_file': str(stats_path),
            **stats
        }

    def _prepare_stats_for_json(self, stats: Dict) -> Dict:
        """Convert numpy/pandas types to Python types for JSON serialization."""
        stats_json = {}
        for key, value in stats.items():
            # Convert key to string if it's an integer (for year keys)
            json_key = str(key) if isinstance(key, (int, np.integer)) else key

            if isinstance(value, (np.integer, np.int64)):
                stats_json[json_key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                stats_json[json_key] = float(value)
            elif isinstance(value, dict):
                stats_json[json_key] = self._prepare_stats_for_json(value)
            else:
                stats_json[json_key] = value
        return stats_json
