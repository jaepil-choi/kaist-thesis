"""
Corpus Builder for TNIC Analysis

Builds year-specific vocabularies following Hoberg & Phillips (2016) methodology.

Key Methodology (H&P 2016, Section II.A, p. 1430):
    "We define Q_t as the matrix containing the set of normalized vectors V_i for
     all firms i in year t. Thus Q_t is an N_t × W matrix, where N_t is the number
     of firms in year t."

This module implements year-by-year corpus building with:
- Separate vocabularies W_t for each year
- H&P filtering (min 20 words, <25% frequency)
- Firm-level word sets for matrix construction
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import numpy as np
import pandas as pd

from tnic.config import get_config
from tnic.data_loader import ParquetLoader
from tnic.korean_text_processor import KoreanTextProcessor
from tnic.utils import ensure_dir, setup_logger


class CorpusBuilder:
    """
    Build year-specific corpora for TNIC analysis.

    Following H&P (2016), this class builds separate vocabularies for each year,
    applying filters within each year independently.

    Attributes:
        config: TNIC configuration
        processor: Korean text processor
        loader: Parquet data loader
        logger: Logger instance
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize corpus builder.

        Args:
            config_path: Path to config directory (default: uses default config)

        Examples:
            >>> builder = CorpusBuilder()
            >>> builder.build_year_corpus(2010)
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Initialize components
        self.processor = KoreanTextProcessor(config_path=config_path)
        self.loader = ParquetLoader(config_path=config_path)
        self.logger = setup_logger(__name__)

        # Get H&P parameters
        self.min_words_per_firm = self.config.get("hp.filtering.min_words_per_firm", 20)
        self.frequency_threshold = self.config.get("hp.filtering.frequency_threshold", 0.25)

        self.logger.info("Corpus builder initialized")
        self.logger.info(f"  H&P parameters:")
        self.logger.info(f"    Min words per firm: {self.min_words_per_firm}")
        self.logger.info(f"    Frequency threshold: {self.frequency_threshold}")

    def build_year_corpus(
        self,
        year: int,
        df: Optional[pd.DataFrame] = None,
        save_outputs: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Build corpus for a single year.

        Args:
            year: Year to process
            df: DataFrame with business descriptions (if None, loads from file)
            save_outputs: Whether to save outputs to disk

        Returns:
            Tuple of (firm_df, vocab_df, statistics):
                - firm_df: Firm-level word sets
                - vocab_df: Vocabulary with frequencies
                - statistics: Corpus statistics dictionary

        Examples:
            >>> builder = CorpusBuilder()
            >>> firm_df, vocab_df, stats = builder.build_year_corpus(2010)
            >>> print(f"Processed {stats['N_t_output']} firms with {stats['W_t']} words")
        """
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"BUILDING CORPUS FOR YEAR {year}")
        self.logger.info(f"{'=' * 80}")

        # Load data if not provided
        if df is None:
            self.logger.info("Loading filled business descriptions...")
            df = self.loader.load_filled_descriptions()

        # Filter to year
        df_year = df[df['year'] == year].copy()
        initial_firm_count = len(df_year)

        # Apply minimum character count filter (H&P 2016, p. 1434)
        # H&P: "fewer than 1,000 characters" were excluded
        #
        # Implementation choice: Apply per-year rather than globally
        # Rationale:
        # - Same firm may have different description lengths across years
        # - A firm with short description in one year may have detailed one in another
        # - Excluding at year-level preserves more data for years with good descriptions
        # - This is more lenient than H&P but captures annual variation in filing quality
        min_char_count = self.config.get("hp.filtering.min_char_count", 1000)

        if 'char_count' in df_year.columns:
            before_char_filter = len(df_year)
            df_year = df_year[df_year['char_count'] >= min_char_count].copy()
            after_char_filter = len(df_year)

            if after_char_filter < before_char_filter:
                removed = before_char_filter - after_char_filter
                self.logger.info(
                    f"Character count filter (>={min_char_count} chars): "
                    f"Removed {removed:,} firms ({100*removed/before_char_filter:.1f}%)"
                )
        else:
            self.logger.warning(
                f"'char_count' column not found - skipping character count filter"
            )

        N_t_input = len(df_year)

        self.logger.info(f"Input firms for {year}: {N_t_input:,}")

        if N_t_input == 0:
            raise ValueError(f"No data found for year {year}")

        # Create firm_year identifier (ensure year is string)
        df_year['firm_year'] = df_year['stock_code'] + '_' + df_year['year'].astype(str)

        # Process corpus
        self.logger.info(f"Processing {N_t_input:,} documents...")
        texts = dict(zip(df_year['firm_year'], df_year['text']))

        firm_words = self.processor.process_corpus(
            texts,
            verbose=True,
            use_tqdm=True
        )

        self.logger.info(f"Initial processing complete:")
        self.logger.info(f"  Documents processed: {len(firm_words):,}")

        # Get initial statistics
        initial_stats = self.processor.get_corpus_statistics(firm_words)
        self.logger.info(f"  Total unique words: {initial_stats['num_unique_words']:,}")
        self.logger.info(f"  Avg words per firm: {initial_stats['avg_words_per_firm']:.1f}")

        # Apply H&P filters in correct order (H&P 2016, p. 1430)
        # CRITICAL: Word-level filters BEFORE firm-level filters
        #
        # Filter order rationale:
        # 1. First remove common words (>25% frequency) from vocabulary
        # 2. Then count remaining distinctive words per firm
        # 3. Then remove firms with <20 distinctive words
        #
        # Why this order matters:
        # - If reversed, firm with 25 words (kept) might have 20 common words
        # - After removing common words, only 5 distinctive words remain
        # - Such firm should be excluded but wouldn't be if order reversed
        self.logger.info(f"Applying H&P filters:")
        self.logger.info(f"  1. Words in <{self.frequency_threshold*100:.0f}% of documents (word-level)")
        self.logger.info(f"  2. Min {self.min_words_per_firm} words per firm (firm-level)")

        # Filter 1: Frequency-based filtering (word-level)
        # H&P 2016, p. 1429: "limit attention to nouns...that appear in no more than 25 percent"
        firm_words_filtered = self.processor.filter_by_frequency(
            firm_words,
            threshold=self.frequency_threshold,
            verbose=True
        )

        # Filter 2: Minimum words per firm (firm-level)
        # H&P 2016, p. 1430: "exclude firms having fewer than 20 unique words"
        # CRITICAL: This must be applied AFTER frequency filtering to count distinctive words only
        firm_words_filtered = self.processor.filter_by_min_words(
            firm_words_filtered,
            min_words=self.min_words_per_firm,
            verbose=True
        )

        # Build year-specific vocabulary W_t
        # IMPORTANT: W_t contains only words AFTER filtering for computational efficiency
        #
        # H&P 2016, p. 1430: "W: unique words used in the union of the document
        # used by all firms in year t"
        #
        # Implementation rationale:
        # - W_t includes only words that passed frequency filter (<25% of docs)
        # - Words filtered out would create zero-valued dimensions for all firms
        # - Including them would increase matrix sparsity without adding information
        # - This is computationally efficient and doesn't affect similarity calculations
        #
        # Example:
        # - Word "company" appears in 80% of docs → filtered out
        # - If included in W_t: P_i[company] = 1 for 80% of firms
        # - After normalization, contributes noise rather than distinctive information
        # - By excluding, we focus on words that distinguish firm products
        self.logger.info(f"Building year-specific vocabulary W_{year}...")

        all_words = []
        for words in firm_words_filtered.values():
            all_words.extend(words)

        word_freq = Counter(all_words)
        W_t = len(word_freq)

        self.logger.info(f"  Vocabulary size W_{year}: {W_t:,} words")
        self.logger.info(f"  Total word instances: {len(all_words):,}")

        # Get final statistics
        final_stats = self.processor.get_corpus_statistics(firm_words_filtered)

        # Build vocabulary dataframe
        # Note: 'frequency' here is total word instances across all firms
        # This differs from document frequency (number of firms using the word)
        #
        # OPTIMIZATION: Pre-compute document frequency in one pass
        # Old approach: O(W × N) - for each word, iterate through all firms
        # New approach: O(N × avg_words) - iterate through firms once, count each word
        # For W=60,000, N=5,000, avg_words=100: 60k*5k=300M vs 5k*100=500k checks
        doc_freq_counter = Counter()
        for words in firm_words_filtered.values():
            for word in words:
                doc_freq_counter[word] += 1

        vocab_data = []
        for word, freq in word_freq.most_common():
            # Lookup pre-computed document frequency
            doc_freq = doc_freq_counter[word]
            pct_docs = 100 * doc_freq / len(firm_words_filtered)

            vocab_data.append({
                'word': word,
                'frequency': freq,  # Total instances across corpus
                'document_frequency': doc_freq,  # Number of firms using this word
                'pct_documents': pct_docs  # Percentage of firms (should be <25% by construction)
            })

        vocab_df = pd.DataFrame(vocab_data)

        # Build firm word sets dataframe
        # Stores unique words per firm for later binary matrix construction
        #
        # H&P 2016, Equation 1 (p. 1430): Binary vector P_i
        # - P_i[w] = 1 if firm i uses word w, 0 otherwise
        # - We store as set of words (equivalent to sparse representation)
        # - Later: Binary matrix builder converts this to P_i vectors
        #
        # Storage format:
        # - 'unique_nouns': numpy array of sorted words (for reproducibility)
        # - Sorted order ensures consistent binary matrix column ordering
        firm_data = []
        for firm_year, words in firm_words_filtered.items():
            stock_code = firm_year.split('_')[0]
            firm_data.append({
                'firm_year': firm_year,
                'stock_code': stock_code,
                'year': year,
                'unique_nouns': np.array(sorted(words)),  # Sorted for reproducibility
                'word_count': len(words)
            })

        firm_df = pd.DataFrame(firm_data)

        # Build statistics dictionary
        statistics = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'year': year,
            'N_t_input': N_t_input,
            'N_t_output': len(firm_words_filtered),
            'W_t': W_t,
            'firms_removed': N_t_input - len(firm_words_filtered),
            'removal_rate': (N_t_input - len(firm_words_filtered)) / N_t_input if N_t_input > 0 else 0,
            'avg_words_per_firm': final_stats['avg_words_per_firm'],
            'min_words_per_firm': final_stats['min_words_per_firm'],
            'max_words_per_firm': final_stats['max_words_per_firm'],
            'median_words_per_firm': final_stats['median_words_per_firm'],
            'avg_char_count': float(df_year['char_count'].mean()),
            'median_char_count': float(df_year['char_count'].median()),
            'h_and_p_filters': {
                'min_words_threshold': self.min_words_per_firm,
                'frequency_threshold': self.frequency_threshold
            }
        }

        # Log summary
        self.logger.info(f"Year {year} complete:")
        self.logger.info(f"  N_{year} = {len(firm_words_filtered):,} firms")
        self.logger.info(f"  W_{year} = {W_t:,} words")
        self.logger.info(f"  Avg words per firm: {final_stats['avg_words_per_firm']:.1f}")
        self.logger.info(f"  Firms removed: {statistics['firms_removed']:,} ({statistics['removal_rate']*100:.1f}%)")

        # Save outputs
        if save_outputs:
            self._save_outputs(year, firm_df, vocab_df, statistics)

        return firm_df, vocab_df, statistics

    def _save_outputs(
        self,
        year: int,
        firm_df: pd.DataFrame,
        vocab_df: pd.DataFrame,
        statistics: Dict
    ):
        """
        Save corpus outputs for a year.

        Args:
            year: Year
            firm_df: Firm word sets dataframe
            vocab_df: Vocabulary dataframe
            statistics: Statistics dictionary
        """
        self.logger.info(f"Saving outputs for {year}...")

        # Get output directory
        base_dir = self.config.get("paths.outputs.corpus.base_dir")
        if base_dir is None:
            raise ValueError("Output directory not configured")

        year_dir = Path(str(base_dir).format(year=year))
        ensure_dir(year_dir)

        # Save firm word sets
        firm_output = year_dir / f"firm_word_sets_{year}.parquet"
        firm_df.to_parquet(firm_output, index=False)
        self.logger.info(f"  Saved: {firm_output}")

        # Save vocabulary
        vocab_output = year_dir / f"corpus_vocabulary_{year}.csv"
        vocab_df.to_csv(vocab_output, index=False, encoding='utf-8-sig')
        self.logger.info(f"  Saved: {vocab_output}")

        # Save statistics
        stats_output = year_dir / f"corpus_statistics_{year}.json"
        with open(stats_output, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {stats_output}")

    def build_all_years(
        self,
        years: Optional[list] = None,
        mode: str = "full"
    ) -> Dict[int, Dict]:
        """
        Build corpora for multiple years.

        Args:
            years: List of years to process (if None, uses config)
            mode: "full" (all years) or "pilot" (pilot years only)

        Returns:
            Dictionary mapping year to statistics

        Examples:
            >>> builder = CorpusBuilder()
            >>> results = builder.build_all_years(mode="pilot")
            >>> results = builder.build_all_years(years=[2010, 2011, 2012])
        """
        # Get years to process
        if years is None:
            years = list(self.config.get_year_range(mode))

        self.logger.info(f"Building corpora for {len(years)} years: {min(years)}-{max(years)}")

        # Load data once (filled data from Phase 1.5)
        df = self.loader.load_filled_descriptions()

        # Process each year
        all_stats = {}

        for year in years:
            try:
                _, _, stats = self.build_year_corpus(year, df=df, save_outputs=True)
                all_stats[year] = stats
            except Exception as e:
                self.logger.error(f"Error processing year {year}: {e}")
                all_stats[year] = {'status': 'failed', 'error': str(e)}

        # Summary
        successful = [y for y, s in all_stats.items() if s.get('status') != 'failed']
        failed = [y for y, s in all_stats.items() if s.get('status') == 'failed']

        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"CORPUS BUILDING COMPLETE")
        self.logger.info(f"{'=' * 80}")
        self.logger.info(f"  Successful: {len(successful)} years")
        if failed:
            self.logger.warning(f"  Failed: {len(failed)} years: {failed}")

        return all_stats

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CorpusBuilder("
            f"min_words={self.min_words_per_firm}, "
            f"freq_threshold={self.frequency_threshold})"
        )
