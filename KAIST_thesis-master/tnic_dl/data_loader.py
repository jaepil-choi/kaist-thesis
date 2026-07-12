"""
Data loading utilities for TNIC-DL.

Extends the existing tnic.data_loader to provide DL-specific data access.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd
from tnic_dl.config import get_input_path
from tnic_dl.utils import setup_logger

logger = setup_logger(__name__)


class DLDataLoader:
    """
    Data loader for TNIC-DL module.

    Provides access to:
    - Existing noun extraction data (from tnic/ pipeline)
    - Raw business descriptions
    - Firm metadata
    """

    def __init__(self):
        """Initialize the data loader."""
        self.logger = logger

    def load_noun_data(self, year: int) -> pd.DataFrame:
        """
        Load existing noun extraction data for a given year.

        This data is produced by the traditional TNIC pipeline (Phase 2).

        Args:
            year: Year to load

        Returns:
            DataFrame with columns: firm_year, stock_code, year, unique_nouns (list), word_count
        """
        path = get_input_path(year, data_type="noun")

        if not path.exists():
            raise FileNotFoundError(
                f"Noun data not found for year {year} at {path}. "
                f"Please run the traditional TNIC pipeline first (Phase 2: Corpus Builder)."
            )

        self.logger.info(f"Loading noun data for year {year} from {path}")
        df = pd.read_parquet(path)

        # Validate expected columns
        expected_cols = {'stock_code', 'year', 'unique_nouns'}
        if not expected_cols.issubset(df.columns):
            missing = expected_cols - set(df.columns)
            raise ValueError(f"Missing expected columns: {missing}")

        self.logger.info(f"Loaded {len(df)} firms for year {year}")
        return df

    def load_text_data(self, year: Optional[int] = None) -> pd.DataFrame:
        """
        Load raw business descriptions (filled data).

        Args:
            year: Optional year to filter. If None, loads all years.

        Returns:
            DataFrame with columns: stock_code, year, text, corp_name, is_filled, etc.
        """
        path = get_input_path(year=0, data_type="text")  # year parameter ignored for text

        if not path.exists():
            raise FileNotFoundError(
                f"Business descriptions not found at {path}. "
                f"Please run the traditional TNIC pipeline first (Phase 1.5: Universe Matching)."
            )

        self.logger.info(f"Loading business descriptions from {path}")
        df = pd.read_parquet(path)

        if year is not None:
            df = df[df['year'] == year].copy()
            self.logger.info(f"Filtered to year {year}: {len(df)} firms")
        else:
            self.logger.info(f"Loaded {len(df)} firm-year observations")

        return df

    def load_multiple_years(self, years: List[int]) -> pd.DataFrame:
        """
        Load noun data for multiple years and concatenate.

        Args:
            years: List of years to load

        Returns:
            Concatenated DataFrame with all years
        """
        dfs = []
        for year in years:
            df = self.load_noun_data(year)
            dfs.append(df)

        combined = pd.concat(dfs, ignore_index=True)
        self.logger.info(f"Loaded {len(combined)} firm-year observations across {len(years)} years")
        return combined

    def validate_data(self, df: pd.DataFrame, data_type: str = "noun") -> bool:
        """
        Validate loaded data structure.

        Args:
            df: DataFrame to validate
            data_type: Type of data ("noun" or "text")

        Returns:
            True if valid, raises ValueError otherwise
        """
        if data_type == "noun":
            required_cols = {'stock_code', 'year', 'unique_nouns'}

            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                raise ValueError(f"Missing required columns: {missing}")

            # Check that unique_nouns is a list
            if not df['unique_nouns'].apply(lambda x: isinstance(x, list)).all():
                raise ValueError("unique_nouns column must contain lists")

            # Check for empty lists
            empty_count = df['unique_nouns'].apply(len).eq(0).sum()
            if empty_count > 0:
                self.logger.warning(f"Found {empty_count} firms with no nouns")

        elif data_type == "text":
            required_cols = {'stock_code', 'year', 'text'}

            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                raise ValueError(f"Missing required columns: {missing}")

            # Check for empty text
            empty_count = df['text'].isna().sum()
            if empty_count > 0:
                self.logger.warning(f"Found {empty_count} firms with missing text")

        return True
