"""
Korean Text Processor for TNIC Analysis

This module provides Korean text processing functionality adapted from
Hoberg & Phillips (2016) methodology for English 10-K business descriptions.

Key adaptations:
- Uses kiwipiepy for Korean morphological analysis
- Extracts nouns (NNG, NNP, NNB tags) instead of English POS filtering
- Applies Korean business stopwords
- Maintains H&P filtering parameters (min 20 words, <25% frequency)

Author: Generated for KAIST Thesis
"""

import re
from collections import Counter
from typing import Dict, List, Optional, Set

import numpy as np
from tqdm import tqdm

from tnic.config import get_config
from tnic.utils import setup_logger

# Import kiwipiepy
try:
    from kiwipiepy import Kiwi
except ImportError:
    raise ImportError(
        "kiwipiepy is required for Korean text processing. "
        "Install with: poetry add kiwipiepy"
    )


class KoreanTextProcessor:
    """
    Korean text processor for TNIC corpus building.

    Implements Hoberg & Phillips (2016) text processing methodology adapted
    for Korean business descriptions.

    Processing pipeline:
        1. Tokenize Korean text using kiwipiepy
        2. Extract nouns (NNG, NNP tags only — NNB excluded)
        3. Filter by minimum word length
        4. Remove numeric tokens
        5. Remove Korean business stopwords
        6. Return unique words per document

    Attributes:
        kiwi: Kiwipiepy tokenizer instance
        min_length: Minimum word length (characters)
        stopwords: Set of Korean business stopwords
        pos_tags: POS tags to keep (nouns)
        logger: Logger instance
    """

    def __init__(
        self,
        min_length: Optional[int] = None,
        stopwords: Optional[Set[str]] = None,
        max_text_length: Optional[int] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize Korean text processor.

        Args:
            min_length: Minimum word length in characters (default: from config)
            stopwords: Custom stopwords set (default: from config)
            max_text_length: Maximum text length to process in characters (default: 50000)
            config_path: Path to config directory (default: uses default config)

        Examples:
            >>> processor = KoreanTextProcessor()
            >>> processor = KoreanTextProcessor(min_length=3, max_text_length=50000)
        """
        # Load configuration
        if config_path is None:
            self.config = get_config()
        else:
            from tnic.config import TNICConfig
            self.config = TNICConfig(config_dir=config_path)

        # Set parameters
        if min_length is None:
            min_length = self.config.get("nlp.filters.min_word_length", 2)
        self.min_length = min_length

        if stopwords is None:
            stopwords = set(self.config.get("nlp.stopwords", []))
        self.stopwords = stopwords

        # Text truncation parameter (for performance)
        if max_text_length is None:
            max_text_length = self.config.get("nlp.filters.max_text_length", 50000)
        self.max_text_length = max_text_length

        # POS tags to keep (nouns)
        # Korean adaptation of H&P (2016) methodology:
        # - H&P: "keep only nouns and proper nouns" (p. 1429)
        # - H&P proper nouns: "first letter capitalized >=90% of time" (p. 1429)
        # - Korean has no capitalization, so we rely on Kiwi POS tagger:
        #   * NNG (일반명사): Common nouns like "제품", "시장", "개발"
        #   * NNP (고유명사): Proper nouns like "삼성", "LG", brand names
        #   * NNB (의존명사) EXCLUDED: "것", "수", "등", "개", "가지", "분" etc.
        #     These are grammatical function words with zero industry discriminability.
        #     H&P "nouns and proper nouns" does not include Korean dependent nouns.
        self.pos_tags = set(self.config.get("nlp.pos_tags", ['NNG', 'NNP']))

        # Initialize logger
        self.logger = setup_logger(__name__)

        # Initialize Kiwi tokenizer
        self.logger.info("Initializing Kiwi tokenizer...")
        self.kiwi = Kiwi()
        self.logger.info("Kiwi tokenizer initialized successfully")

        self.logger.info(f"Korean text processor initialized:")
        self.logger.info(f"  Min word length: {self.min_length}")
        self.logger.info(f"  Max text length: {self.max_text_length:,} chars")
        self.logger.info(f"  POS tags: {self.pos_tags}")
        self.logger.info(f"  Stopwords: {len(self.stopwords)} words")

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Korean text and extract filtered nouns.

        Args:
            text: Korean text to tokenize

        Returns:
            List of filtered Korean nouns

        Examples:
            >>> processor = KoreanTextProcessor()
            >>> text = "당사는 제약업과 의료기기 제조업을 영위하고 있습니다."
            >>> processor.tokenize(text)
            ['제약업', '의료기기', '제조업']
        """
        # Tokenize with Kiwi
        tokens = self.kiwi.tokenize(text, normalize_coda=True)

        # Extract nouns (NNG, NNP only — NNB excluded)
        nouns = [token.form for token in tokens if token.tag in self.pos_tags]

        # Apply filters
        filtered = self._apply_filters(nouns)

        return filtered

    def _apply_filters(self, nouns: List[str]) -> List[str]:
        """
        Apply filtering to list of nouns.

        Filters:
            1. Minimum word length
            2. Remove numeric strings
            3. Remove stopwords

        Args:
            nouns: List of Korean nouns

        Returns:
            Filtered list of nouns
        """
        filtered = []

        for word in nouns:
            # Filter 1: Minimum length
            if len(word) < self.min_length:
                continue

            # Filter 2: Remove pure numbers (including Korean number format)
            if re.match(r'^[\d,\.]+$', word):
                continue

            # Filter 3: Remove stopwords
            if word in self.stopwords:
                continue

            filtered.append(word)

        return filtered

    def process_corpus(
        self,
        texts: Dict[str, str],
        verbose: bool = False,
        use_tqdm: bool = True,
        batch_size: int = 100
    ) -> Dict[str, Set[str]]:
        """
        Process a corpus of texts and extract unique words per document.

        OPTIMIZATION: Uses batch processing for faster tokenization.
        Kiwi's tokenize() method can handle multiple texts at once, which is
        significantly faster than processing one-by-one.

        Args:
            texts: Dictionary mapping document ID to text
            verbose: Print progress information
            use_tqdm: Use tqdm progress bar
            batch_size: Number of documents to process in each batch

        Returns:
            Dictionary mapping document ID to set of unique words

        Examples:
            >>> processor = KoreanTextProcessor()
            >>> texts = {
            ...     'firm1_2010': '당사는 제약업을 영위합니다.',
            ...     'firm2_2010': '당사는 IT 서비스를 제공합니다.'
            ... }
            >>> firm_words = processor.process_corpus(texts)
            >>> len(firm_words)
            2
        """
        firm_words = {}

        # Convert to list for batch processing
        doc_ids = list(texts.keys())
        doc_texts = [texts[doc_id] for doc_id in doc_ids]
        total = len(doc_ids)

        if verbose:
            self.logger.info(f"Processing {total:,} documents in batches of {batch_size}...")

        # Process in batches
        for batch_start in tqdm(range(0, total, batch_size),
                                desc="Processing batches",
                                disable=not use_tqdm):
            batch_end = min(batch_start + batch_size, total)
            batch_texts = doc_texts[batch_start:batch_end]
            batch_ids = doc_ids[batch_start:batch_end]

            # OPTIMIZATION: Truncate very long texts before tokenization
            # This significantly speeds up Kiwi processing for lengthy documents
            # Rationale: After 50k chars, additional text rarely adds distinctive vocabulary
            # H&P methodology focuses on product descriptions (typically <10k chars)
            truncated_texts = [
                text[:self.max_text_length] if len(text) > self.max_text_length else text
                for text in batch_texts
            ]

            # Batch tokenization - Kiwi processes all texts at once
            batch_results = self.kiwi.tokenize(truncated_texts, normalize_coda=True)

            # Process each document's results
            for doc_id, tokens in zip(batch_ids, batch_results):
                # Extract nouns (NNG, NNP only — NNB excluded)
                nouns = [token.form for token in tokens if token.tag in self.pos_tags]

                # Apply filters
                filtered = self._apply_filters(nouns)
                firm_words[doc_id] = set(filtered)

        if verbose:
            self.logger.info(f"Processed {len(firm_words):,} documents")

        return firm_words

    def filter_by_min_words(
        self,
        firm_words: Dict[str, Set[str]],
        min_words: int = 20,
        verbose: bool = False
    ) -> Dict[str, Set[str]]:
        """
        Filter firms with fewer than minimum unique words.

        Following H&P (2016, p. 1430):
        "We exclude firms having fewer than 20 unique words from our
         classification algorithm."

        Args:
            firm_words: Dictionary mapping firm_year to set of words
            min_words: Minimum number of unique words (default: 20)
            verbose: Print filtering information

        Returns:
            Filtered dictionary with only firms having >= min_words

        Examples:
            >>> firm_words = {
            ...     'firm1': {'word1', 'word2', 'word3'},
            ...     'firm2': set(f'word{i}' for i in range(25))
            ... }
            >>> filtered = processor.filter_by_min_words(firm_words, min_words=20)
            >>> len(filtered)
            1
        """
        initial_count = len(firm_words)

        filtered = {
            firm_id: words
            for firm_id, words in firm_words.items()
            if len(words) >= min_words
        }

        removed = initial_count - len(filtered)

        if verbose:
            self.logger.info(f"Filter: Minimum {min_words} words per firm")
            self.logger.info(f"  Before: {initial_count:,} firms")
            self.logger.info(f"  After: {len(filtered):,} firms")
            self.logger.info(f"  Removed: {removed:,} firms ({100*removed/initial_count:.1f}%)")

        return filtered

    def filter_by_frequency(
        self,
        firm_words: Dict[str, Set[str]],
        threshold: float = 0.25,
        verbose: bool = False
    ) -> Dict[str, Set[str]]:
        """
        Remove words appearing in more than threshold fraction of documents.

        Following H&P (2016, p. 1429):
        "we limit attention to nouns...that appear in no more than 25 percent
         of all product descriptions"

        Implementation note:
        - Uses DOCUMENT FREQUENCY (not term frequency)
        - Word appearing in 26% of docs is removed (even if used 1x per doc)
        - Word appearing in 24% of docs is kept (even if used 100x per doc)
        - This matches H&P's binary weighting scheme

        Args:
            firm_words: Dictionary mapping firm_year to set of words
            threshold: Maximum document frequency (0.0 to 1.0)
            verbose: Print filtering information

        Returns:
            Filtered dictionary with common words removed

        Examples:
            >>> firm_words = {
            ...     'firm1': {'common', 'word1'},
            ...     'firm2': {'common', 'word2'},
            ...     'firm3': {'common', 'word3'},
            ...     'firm4': {'rare', 'word4'}
            ... }
            >>> # 'common' appears in 75% of docs (3/4), will be removed
            >>> filtered = processor.filter_by_frequency(firm_words, threshold=0.5)
        """
        num_docs = len(firm_words)

        # Count document frequency for each word
        # Note: Since firm_words contains sets, each word counted once per document
        doc_freq = Counter()
        for words in firm_words.values():
            for word in words:
                doc_freq[word] += 1

        # Find words exceeding threshold
        # H&P: "no more than 25%" means we use strict inequality (>)
        # If threshold=0.25 and num_docs=1000, max_docs=250
        # Words appearing in 251+ documents are removed
        max_docs = int(threshold * num_docs)
        common_words = {
            word for word, freq in doc_freq.items()
            if freq > max_docs
        }

        # Remove common words from all documents
        filtered = {}
        for firm_id, words in firm_words.items():
            filtered_words = words - common_words
            filtered[firm_id] = filtered_words

        if verbose:
            self.logger.info(f"Filter: Words in >{threshold*100:.0f}% of documents")
            self.logger.info(f"  Total documents: {num_docs:,}")
            self.logger.info(f"  Threshold: >{max_docs} documents")
            self.logger.info(f"  Common words removed: {len(common_words):,}")

            if len(common_words) > 0 and len(common_words) <= 50:
                sample_words = sorted(common_words)[:20]
                self.logger.info(f"  Sample common words: {', '.join(sample_words)}")

        return filtered

    def get_corpus_statistics(
        self,
        firm_words: Dict[str, Set[str]]
    ) -> Dict[str, float]:
        """
        Compute statistics for a corpus.

        Args:
            firm_words: Dictionary mapping firm_year to set of words

        Returns:
            Dictionary with statistics:
                - num_firms: Number of firms
                - num_unique_words: Total unique words across corpus
                - avg_words_per_firm: Average words per firm
                - min_words_per_firm: Minimum words per firm
                - max_words_per_firm: Maximum words per firm
                - median_words_per_firm: Median words per firm

        Examples:
            >>> stats = processor.get_corpus_statistics(firm_words)
            >>> stats['avg_words_per_firm']
            156.3
        """
        if len(firm_words) == 0:
            return {
                'num_firms': 0,
                'num_unique_words': 0,
                'avg_words_per_firm': 0.0,
                'min_words_per_firm': 0,
                'max_words_per_firm': 0,
                'median_words_per_firm': 0.0
            }

        # Collect all unique words
        all_words = set()
        for words in firm_words.values():
            all_words.update(words)

        # Count words per firm
        word_counts = [len(words) for words in firm_words.values()]

        return {
            'num_firms': len(firm_words),
            'num_unique_words': len(all_words),
            'avg_words_per_firm': float(np.mean(word_counts)),
            'min_words_per_firm': int(np.min(word_counts)),
            'max_words_per_firm': int(np.max(word_counts)),
            'median_words_per_firm': float(np.median(word_counts))
        }

    def get_vocabulary(
        self,
        firm_words: Dict[str, Set[str]]
    ) -> Dict[str, int]:
        """
        Get vocabulary with word frequencies.

        Note: This returns DOCUMENT FREQUENCY, not term frequency.
        Since firm_words contains sets (unique words per firm), each word
        is counted once per firm that uses it.

        This is consistent with H&P's binary representation where
        word frequency within a document is ignored.

        Args:
            firm_words: Dictionary mapping firm_year to set of words

        Returns:
            Dictionary mapping word to document frequency (number of firms using it)

        Examples:
            >>> vocab = processor.get_vocabulary(firm_words)
            >>> vocab['제품']  # number of firms that use word '제품'
            127
        """
        word_freq = Counter()

        # Count how many firms use each word (document frequency)
        for words in firm_words.values():
            word_freq.update(words)

        return dict(word_freq)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"KoreanTextProcessor("
            f"min_length={self.min_length}, "
            f"stopwords={len(self.stopwords)}, "
            f"pos_tags={self.pos_tags})"
        )
