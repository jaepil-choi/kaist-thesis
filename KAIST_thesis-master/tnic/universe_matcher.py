"""
Universe Matcher and Data Filler for TNIC Pipeline

Implements Hoberg & Phillips data filling methodology:
1. Forward fill missing firm-years with most recent data
2. Backfill early years from first available filing
3. Mask to actual trading universe (from alpha-excel)

This ensures complete panel data for all firms that ever filed,
while removing spurious firm-years where firm wasn't actually trading.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import pandas as pd
import numpy as np
from alpha_excel2.core.facade import AlphaExcel

from tnic.config import get_config
from tnic.utils import ensure_dir, setup_logger


class UniverseMatcher:
    """
    Matches MongoDB text data to trading universe and fills missing firm-years.

    Attributes:
        config: TNIC configuration
        logger: Logger instance
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Universe Matcher.

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

        self.logger.info("UniverseMatcher initialized")

    def load_universe(
        self,
        start_year: int,
        end_year: int
    ) -> Dict[int, Set[str]]:
        """
        Load trading universe from alpha-excel (FnGuide).

        A firm is in the universe for year Y if it has at least one
        valid adjusted close price on any trading day in that year.

        Args:
            start_year: First year to load
            end_year: Last year to load

        Returns:
            universe_by_year: Dict mapping year → set of stock codes (6-digit, no prefix)

        Examples:
            >>> matcher = UniverseMatcher()
            >>> universe = matcher.load_universe(2010, 2025)
            >>> print(f"2010 universe: {len(universe[2010])} firms")
        """
        self.logger.info(f"Loading trading universe from alpha-excel ({start_year}-{end_year})...")

        # Initialize alpha-excel
        ae_daily = AlphaExcel(
            start_time=f'{start_year}-01-01',
            end_time=f'{end_year}-12-31',
            universe_field=None,  # No universe masking
            config_path='./config'
        )

        # Load adjusted close prices (daily)
        fd = ae_daily.field
        adj_close_alpha = fd('fnguide_adj_close')
        adj_close_df = adj_close_alpha.to_df()

        self.logger.info(f"  Loaded adj_close: {adj_close_df.shape} (dates × securities)")

        # For each year, find firms with at least 1 valid price
        universe_by_year = {}

        for year in range(start_year, end_year + 1):
            # Filter to year's data
            year_data = adj_close_df.loc[f'{year}-01-01':f'{year}-12-31']

            # Find columns with at least one non-NaN value
            firms_with_data = year_data.notna().any(axis=0)
            firm_symbols_with_prefix = firms_with_data[firms_with_data].index.tolist()

            # Normalize symbols: strip 'A' prefix
            firm_symbols = set()
            for symbol in firm_symbols_with_prefix:
                if isinstance(symbol, str) and symbol.startswith('A'):
                    firm_symbols.add(symbol[1:])  # Remove 'A' prefix
                else:
                    firm_symbols.add(symbol)

            universe_by_year[year] = firm_symbols

            self.logger.info(f"  {year}: {len(firm_symbols):,} firms in universe")

        return universe_by_year

    def fill_and_mask(
        self,
        df_mongo: pd.DataFrame,
        universe_by_year: Dict[int, Set[str]]
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply forward fill, backfill, and universe masking.

        Process (order is critical):
        1. Forward fill: Fill forward from last known value
        2. Backfill: Fill backward from first known value
        3. Universe mask: Remove firm-years not in trading universe

        Args:
            df_mongo: DataFrame from Phase 1 extraction
                     Required columns: stock_code, year, text, char_count, corp_name
            universe_by_year: Universe from load_universe()

        Returns:
            df_filled: DataFrame with filled and masked data
            stats: Dictionary with filling statistics

        Examples:
            >>> df_filled, stats = matcher.fill_and_mask(df_mongo, universe)
            >>> print(f"Filled {stats['n_forward_fill']} forward, {stats['n_backfill']} backward")
        """
        self.logger.info("Applying forward fill, backfill, and universe masking...")

        # Ensure year is int (should already be int from run() method)
        df_mongo = df_mongo.copy()
        if df_mongo['year'].dtype == 'object':
            df_mongo['year'] = df_mongo['year'].astype(int)

        # Get all years and all firms from universe
        all_years = sorted(universe_by_year.keys())
        all_firms = set()
        for firms in universe_by_year.values():
            all_firms.update(firms)

        self.logger.info(f"  Universe: {len(all_firms):,} unique firms across {len(all_years)} years")
        self.logger.info(f"  MongoDB: {len(df_mongo):,} firm-years, {df_mongo['stock_code'].nunique():,} unique firms")

        # Step 1: Create full firm-year index from universe
        self.logger.info("  Step 1: Creating full firm-year index from universe...")
        full_index = []
        for year in all_years:
            for stock_code in universe_by_year[year]:
                full_index.append((stock_code, year))

        full_df = pd.DataFrame(full_index, columns=['stock_code', 'year'])
        self.logger.info(f"    Created {len(full_df):,} firm-year combinations")

        # Step 2: Merge with MongoDB data (left join to preserve all universe firm-years)
        self.logger.info("  Step 2: Merging with MongoDB data...")
        df_filled = full_df.merge(
            df_mongo[['stock_code', 'year', 'text', 'char_count', 'corp_name']],
            on=['stock_code', 'year'],
            how='left'
        )

        n_original = df_filled['text'].notna().sum()
        self.logger.info(f"    {n_original:,} firm-years have original text")
        self.logger.info(f"    {len(full_df) - n_original:,} firm-years missing text (to be filled)")

        # Step 3: Sort by (stock_code, year) for filling
        self.logger.info("  Step 3: Sorting for filling operations...")
        df_filled = df_filled.sort_values(['stock_code', 'year']).reset_index(drop=True)

        # Track original text presence before filling
        df_filled['_has_original'] = df_filled['text'].notna()

        # Step 4: Forward fill by firm
        self.logger.info("  Step 4: Forward filling missing years...")
        for col in ['text', 'char_count', 'corp_name']:
            df_filled[col] = df_filled.groupby('stock_code')[col].ffill()

        n_after_ffill = df_filled['text'].notna().sum()
        n_ffill = n_after_ffill - n_original
        self.logger.info(f"    Forward filled {n_ffill:,} firm-years")

        # Step 5: Backfill by firm
        self.logger.info("  Step 5: Backfilling early years...")
        for col in ['text', 'char_count', 'corp_name']:
            df_filled[col] = df_filled.groupby('stock_code')[col].bfill()

        n_after_bfill = df_filled['text'].notna().sum()
        n_bfill = n_after_bfill - n_after_ffill
        self.logger.info(f"    Backfilled {n_bfill:,} firm-years")

        # Step 6: Add metadata columns
        self.logger.info("  Step 6: Adding fill metadata...")

        # is_filled: True if text was filled (not original)
        df_filled['is_filled'] = ~df_filled['_has_original']

        # Find original_year for each text (where it first appeared)
        # Create mapping: (stock_code, text) → original_year
        original_mapping = (
            df_mongo[df_mongo['text'].notna()]
            .sort_values(['stock_code', 'year'])
            .drop_duplicates(subset=['stock_code', 'text'], keep='first')
            [['stock_code', 'text', 'year']]
            .rename(columns={'year': 'original_year'})
        )

        df_filled = df_filled.merge(
            original_mapping,
            on=['stock_code', 'text'],
            how='left'
        )

        # For rows with original text, original_year = year
        df_filled.loc[df_filled['_has_original'], 'original_year'] = df_filled.loc[df_filled['_has_original'], 'year']

        # Determine fill_method
        df_filled['fill_method'] = 'original'

        # Forward fill: original_year < current year
        mask_ffill = (df_filled['is_filled']) & (df_filled['original_year'] < df_filled['year'])
        df_filled.loc[mask_ffill, 'fill_method'] = 'forward_fill'

        # Backfill: original_year > current year
        mask_bfill = (df_filled['is_filled']) & (df_filled['original_year'] > df_filled['year'])
        df_filled.loc[mask_bfill, 'fill_method'] = 'backfill'

        # Step 7: Remove rows with no text (firms that never filed)
        self.logger.info("  Step 7: Removing firms that never filed...")
        n_before_drop = len(df_filled)
        df_filled = df_filled[df_filled['text'].notna()].copy()
        n_dropped = n_before_drop - len(df_filled)
        self.logger.info(f"    Dropped {n_dropped:,} firm-years (never filed)")

        # Clean up temporary columns
        df_filled = df_filled.drop(columns=['_has_original'])

        # Step 8: Calculate statistics
        stats = {
            'n_firm_years_before': len(df_mongo),
            'n_firm_years_after': len(df_filled),
            'n_firms_before': df_mongo['stock_code'].nunique(),
            'n_firms_after': df_filled['stock_code'].nunique(),
            'n_original': n_original,
            'n_filled': (df_filled['is_filled'] == True).sum(),
            'n_forward_fill': (df_filled['fill_method'] == 'forward_fill').sum(),
            'n_backfill': (df_filled['fill_method'] == 'backfill').sum(),
            'n_dropped_never_filed': n_dropped,
        }

        self.logger.info(f"\n  Summary:")
        self.logger.info(f"    Firm-years: {stats['n_firm_years_before']:,} → {stats['n_firm_years_after']:,}")
        self.logger.info(f"    Unique firms: {stats['n_firms_before']:,} → {stats['n_firms_after']:,}")
        self.logger.info(f"    Original data: {stats['n_original']:,}")
        self.logger.info(f"    Filled data: {stats['n_filled']:,} ({stats['n_filled']/len(df_filled)*100:.1f}%)")
        self.logger.info(f"      - Forward fill: {stats['n_forward_fill']:,}")
        self.logger.info(f"      - Backfill: {stats['n_backfill']:,}")

        return df_filled, stats

    def run(
        self,
        input_path: Path,
        output_path: Path,
        start_year: int,
        end_year: int
    ) -> Dict:
        """
        Main execution method: load → fill → mask → save.

        Args:
            input_path: Path to Phase 1b output directory (contains business_descriptions_clean_YYYY.parquet files)
                       OR path to consolidated file (backward compatibility)
            output_path: Path to save filled data
            start_year: First year to process
            end_year: Last year to process

        Returns:
            Dictionary with results and statistics

        Examples:
            >>> matcher = UniverseMatcher()
            >>> result = matcher.run(
            ...     input_path="data/korean_texts/business_descriptions_clean.parquet",
            ...     output_path="data/korean_texts/business_descriptions_filled.parquet",
            ...     start_year=2010,
            ...     end_year=2025
            ... )
        """
        self.logger.info("=" * 80)
        self.logger.info("UNIVERSE MATCHING & DATA FILLING")
        self.logger.info("=" * 80)

        # Step 1: Load Phase 1b output (yearly files or consolidated file)
        self.logger.info(f"\nStep 1: Loading Phase 1b output...")

        # Check if input_path is a file or directory
        input_path = Path(input_path)

        if input_path.is_file():
            # Backward compatibility: single consolidated file
            self.logger.info(f"  Loading from consolidated file: {input_path}")
            df_mongo_all = pd.read_parquet(input_path)
            self.logger.info(f"  Loaded {len(df_mongo_all):,} firm-years")
        else:
            # New format: yearly files in directory
            self.logger.info(f"  Loading from yearly files in: {input_path.parent}")
            yearly_dfs = []

            for year in range(start_year, end_year + 1):
                year_file = input_path.parent / f"business_descriptions_clean_{year}.parquet"

                if not year_file.exists():
                    self.logger.warning(f"  Missing clean file for {year}: {year_file}")
                    continue

                df_year = pd.read_parquet(year_file)
                yearly_dfs.append(df_year)
                self.logger.info(f"  {year}: {len(df_year):,} firm-years")

            if not yearly_dfs:
                raise FileNotFoundError(
                    f"No cleaned description files found in {input_path.parent} "
                    f"for years {start_year}-{end_year}"
                )

            df_mongo_all = pd.concat(yearly_dfs, ignore_index=True)
            self.logger.info(f"  Total loaded: {len(df_mongo_all):,} firm-years")

        # Filter to requested year range
        df_mongo_all['year'] = df_mongo_all['year'].astype(int)  # Convert to int for filtering
        df_mongo = df_mongo_all[
            (df_mongo_all['year'] >= start_year) &
            (df_mongo_all['year'] <= end_year)
        ].copy()
        self.logger.info(f"  Filtered to {start_year}-{end_year}: {len(df_mongo):,} firm-years")

        # Step 2: Load trading universe
        self.logger.info(f"\nStep 2: Loading trading universe ({start_year}-{end_year})...")
        universe_by_year = self.load_universe(start_year, end_year)

        # Step 3: Apply filling and masking
        self.logger.info(f"\nStep 3: Applying forward fill, backfill, and universe masking...")
        df_filled, stats = self.fill_and_mask(df_mongo, universe_by_year)

        # Step 4: Calculate coverage by year
        self.logger.info(f"\nStep 4: Calculating coverage by year...")
        coverage_by_year = []
        for year in range(start_year, end_year + 1):
            df_year = df_filled[df_filled['year'] == year]
            n_universe = len(universe_by_year[year])
            n_matched = len(df_year)
            coverage_pct = (n_matched / n_universe * 100) if n_universe > 0 else 0

            # Count original vs filled
            n_original = (df_year['fill_method'] == 'original').sum()
            n_filled = (df_year['is_filled'] == True).sum()

            coverage_by_year.append({
                'year': year,
                'universe_size': n_universe,
                'matched_firms': n_matched,
                'coverage_pct': round(coverage_pct, 2),
                'original': n_original,
                'filled': n_filled,
                'forward_fill': (df_year['fill_method'] == 'forward_fill').sum(),
                'backfill': (df_year['fill_method'] == 'backfill').sum()
            })

            self.logger.info(
                f"  {year}: {n_matched:,}/{n_universe:,} = {coverage_pct:.1f}% "
                f"(original: {n_original:,}, filled: {n_filled:,})"
            )

        coverage_df = pd.DataFrame(coverage_by_year)

        # Step 5: Save outputs
        self.logger.info(f"\nStep 5: Saving outputs...")

        # Save filled data
        ensure_dir(output_path.parent)
        df_filled.to_parquet(output_path, index=False)
        self.logger.info(f"  [OK] Saved filled data: {output_path}")

        # Save coverage by year
        coverage_path = output_path.parent / "universe_coverage_by_year.csv"
        coverage_df.to_csv(coverage_path, index=False)
        self.logger.info(f"  [OK] Saved coverage stats: {coverage_path}")

        # Save statistics JSON (convert numpy int64 to Python int)
        stats_path = output_path.parent / "universe_matching_stats.json"
        stats_json = {k: int(v) if isinstance(v, (np.integer, np.int64)) else v
                      for k, v in stats.items()}
        with open(stats_path, 'w') as f:
            json.dump(stats_json, f, indent=2)
        self.logger.info(f"  [OK] Saved statistics: {stats_path}")

        self.logger.info("\n" + "=" * 80)
        self.logger.info("UNIVERSE MATCHING COMPLETE")
        self.logger.info("=" * 80)

        return {
            'output': str(output_path),
            'coverage_file': str(coverage_path),
            'stats_file': str(stats_path),
            **stats
        }
