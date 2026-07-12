"""
Vocabulary Builder for TNIC-DL.

Implements Kim et al. (2020) vocabulary selection methodology:
1. Collect all nouns from firm business descriptions
2. Exclude words appearing in >20% of documents (too common)
3. Exclude words appearing in <2 documents (too rare)
4. Exclude geographic terms
5. Select top 2000 most frequent words
"""

from collections import Counter
from pathlib import Path
from typing import List, Optional, Set, Tuple
import pandas as pd
from tnic_dl.config import get_dl_config, get_output_path
from tnic_dl.utils import setup_logger, save_json, load_json

logger = setup_logger(__name__)


class VocabularyBuilder:
    """
    Build vocabulary from noun extraction data following Kim et al. (2020) methodology.
    """

    def __init__(
        self,
        top_n_words: Optional[int] = None,
        max_doc_freq: Optional[float] = None,
        min_doc_freq: Optional[int] = None,
        min_words_per_doc: Optional[int] = None,
        exclude_geographic: Optional[bool] = None,
    ):
        """
        Initialize vocabulary builder.

        Args:
            top_n_words: Number of top words to select (default from config)
            max_doc_freq: Maximum document frequency (0-1) (default from config)
            min_doc_freq: Minimum document frequency (count) (default from config)
            min_words_per_doc: Minimum words per document (default from config)
            exclude_geographic: Whether to exclude geographic terms (default from config)
        """
        self.top_n_words = top_n_words or get_dl_config("tnic_dl.vocabulary.top_n_words", 2000)
        self.max_doc_freq = max_doc_freq or get_dl_config("tnic_dl.vocabulary.max_document_frequency", 0.20)
        self.min_doc_freq = min_doc_freq or get_dl_config("tnic_dl.vocabulary.min_document_frequency", 2)
        self.min_words_per_doc = min_words_per_doc or get_dl_config("tnic_dl.vocabulary.min_words_per_document", 20)
        self.exclude_geographic = exclude_geographic if exclude_geographic is not None else get_dl_config("tnic_dl.vocabulary.exclude_geographic", True)

        self.logger = logger

        # Korean geographic terms to exclude (cities, provinces, countries, regions)
        # Rationale: export/import-heavy firms mention destination countries frequently;
        # including these would make all exporters look similar regardless of industry.
        self.geographic_terms = {
            # Metropolitan cities (8 특별/광역시)
            '서울', '부산', '인천', '대구', '대전', '광주', '울산', '세종',
            # Provinces (9 도)
            '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
            # Major Korean cities frequently mentioned in business descriptions
            '수원', '성남', '화성', '용인', '안산', '안양', '고양', '창원', '청주',
            '전주', '포항', '천안', '원주', '춘천', '강릉', '목포', '여수', '순천',
            '제천', '충주', '군산', '익산', '구미', '경주', '진주', '통영', '거제',
            # Korea (various forms)
            '한국', '대한민국', '국내', '국내외',
            # Major trading partners / commonly cited countries
            '미국', '중국', '일본', '독일', '프랑스', '영국', '캐나다', '호주',
            '싱가포르', '인도', '브라질', '멕시코', '태국', '인도네시아', '말레이시아',
            '필리핀', '대만', '홍콩', '러시아', '터키', '베트남', '사우디', '이란',
            '이스라엘', '두바이', '남아공', '폴란드', '네덜란드', '스웨덴', '스위스',
            '이탈리아', '스페인',
            # Broad continental / macro regions
            '유럽', '아시아', '동남아', '중동', '북미', '남미', '중남미',
            '동유럽', '서유럽', '오세아니아', '아프리카', '아태',
            # Directional regions (used geographically, not industry-specific)
            '해외', '글로벌', '동부', '서부', '남부', '북부',
        }

    def build(
        self,
        df: pd.DataFrame,
        year: int,
        save: bool = True
    ) -> Tuple[List[str], dict]:
        """
        Build vocabulary from noun extraction data.

        Args:
            df: DataFrame with columns: stock_code, year, unique_nouns (list)
            year: Year for the vocabulary
            save: Whether to save the vocabulary to disk

        Returns:
            Tuple of (vocabulary list, statistics dictionary)
        """
        self.logger.info(f"Building vocabulary for year {year}")
        self.logger.info(f"Input: {len(df)} firms")

        # Step 1: Filter firms by minimum words
        df_filtered = self._filter_by_min_words(df)
        self.logger.info(f"After min words filter ({self.min_words_per_doc}): {len(df_filtered)} firms")

        # Step 2: Collect all words and document frequencies
        word_doc_freq, word_total_freq = self._compute_word_frequencies(df_filtered)
        self.logger.info(f"Total unique words: {len(word_doc_freq)}")

        # Step 3: Filter by document frequency
        n_docs = len(df_filtered)
        words_filtered = self._filter_by_doc_frequency(word_doc_freq, n_docs)
        self.logger.info(f"After document frequency filter: {len(words_filtered)} words")

        # Step 4: Exclude geographic terms
        if self.exclude_geographic:
            words_filtered = self._exclude_geographic_terms(words_filtered)
            self.logger.info(f"After geographic filter: {len(words_filtered)} words")

        # Step 5: Select top N most frequent words
        vocabulary = self._select_top_words(words_filtered, word_total_freq)
        self.logger.info(f"Final vocabulary size: {len(vocabulary)} words")

        # Compute statistics
        stats = self._compute_statistics(
            vocabulary, word_doc_freq, word_total_freq, n_docs, len(df)
        )

        # Save vocabulary and statistics
        if save:
            self._save_vocabulary(year, vocabulary, stats)

        return vocabulary, stats

    def _filter_by_min_words(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter firms with fewer than min_words_per_doc unique words."""
        df = df.copy()
        df['n_words'] = df['unique_nouns'].apply(len)
        return df[df['n_words'] >= self.min_words_per_doc].copy()

    def _compute_word_frequencies(self, df: pd.DataFrame) -> Tuple[Counter, Counter]:
        """
        Compute document frequency and total frequency for each word.

        Returns:
            Tuple of (document_frequency, total_frequency) Counters
        """
        word_doc_freq = Counter()  # Number of documents containing each word
        word_total_freq = Counter()  # Total occurrences across all documents

        for nouns_list in df['unique_nouns']:
            # Document frequency: count each word once per document
            unique_words = set(nouns_list)
            word_doc_freq.update(unique_words)

            # Total frequency: count all occurrences
            word_total_freq.update(nouns_list)

        return word_doc_freq, word_total_freq

    def _filter_by_doc_frequency(self, word_doc_freq: Counter, n_docs: int) -> Set[str]:
        """
        Filter words by document frequency.

        Excludes:
        - Words in > max_doc_freq fraction of documents (too common)
        - Words in < min_doc_freq documents (too rare)
        """
        max_docs = int(n_docs * self.max_doc_freq)

        filtered_words = set()
        for word, doc_freq in word_doc_freq.items():
            if self.min_doc_freq <= doc_freq <= max_docs:
                filtered_words.add(word)

        return filtered_words

    def _exclude_geographic_terms(self, words: Set[str]) -> Set[str]:
        """Exclude geographic terms from vocabulary."""
        return words - self.geographic_terms

    def _select_top_words(self, words: Set[str], word_total_freq: Counter) -> List[str]:
        """
        Select top N most frequent words.

        Args:
            words: Set of candidate words
            word_total_freq: Total frequency counter for all words

        Returns:
            List of top N words (sorted by frequency, descending)
        """
        # Filter total_freq to only include candidate words
        candidate_freq = {word: freq for word, freq in word_total_freq.items() if word in words}

        # Select top N
        top_words = sorted(candidate_freq.items(), key=lambda x: x[1], reverse=True)[:self.top_n_words]

        # Return just the words (not frequencies)
        return [word for word, _ in top_words]

    def _compute_statistics(
        self,
        vocabulary: List[str],
        word_doc_freq: Counter,
        word_total_freq: Counter,
        n_docs_filtered: int,
        n_docs_total: int
    ) -> dict:
        """Compute vocabulary statistics."""
        vocab_set = set(vocabulary)

        stats = {
            'year': None,  # Will be set during save
            'vocabulary_size': len(vocabulary),
            'n_firms_total': n_docs_total,
            'n_firms_after_min_words_filter': n_docs_filtered,
            'top_n_words': self.top_n_words,
            'max_document_frequency': self.max_doc_freq,
            'min_document_frequency': self.min_doc_freq,
            'min_words_per_document': self.min_words_per_doc,
            'exclude_geographic': self.exclude_geographic,
            'word_frequencies': [
                {
                    'word': word,
                    'document_frequency': word_doc_freq[word],
                    'total_frequency': word_total_freq[word],
                    'doc_freq_pct': word_doc_freq[word] / n_docs_filtered * 100,
                }
                for word in vocabulary[:50]  # Top 50 words only for stats
            ],
        }

        return stats

    def _save_vocabulary(self, year: int, vocabulary: List[str], stats: dict) -> None:
        """Save vocabulary and statistics to disk."""
        # Save vocabulary as JSON
        vocab_path = get_output_path(year, f"vocab_{year}.json")
        save_json({'vocabulary': vocabulary}, vocab_path)
        self.logger.info(f"Saved vocabulary to {vocab_path}")

        # Save statistics
        stats['year'] = year
        stats_path = get_output_path(year, f"vocab_stats_{year}.json")
        save_json(stats, stats_path)
        self.logger.info(f"Saved statistics to {stats_path}")

    def load_vocabulary(self, year: int) -> List[str]:
        """
        Load saved vocabulary from disk.

        Args:
            year: Year of the vocabulary

        Returns:
            List of vocabulary words
        """
        vocab_path = get_output_path(year, f"vocab_{year}.json", create_dir=False)
        vocab_data = load_json(vocab_path)
        return vocab_data['vocabulary']
