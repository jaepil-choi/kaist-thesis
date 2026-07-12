"""
Build Year-by-Year Korean Corpora for TNIC Analysis

This script implements the Hoberg & Phillips (2016) methodology of building
separate vocabularies and word sets for each year.

Citation:
    Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and
    endogenous product differentiation. Journal of Political Economy, 124(5),
    1423-1465.

Key Methodology (H&P 2016, Section II.A, p. 1430):
    - "We define Q_t as the matrix containing the set of normalized vectors
       V_i for all firms i **in year t**. Thus Q_t is an N_t × W matrix,
       where N_t is the number of firms in year t."
    - "W is 61,146 unique nouns and proper nouns in 1996 and 55,605 in 2008."

Why Year-by-Year:
    - Vocabulary W_t changes as product markets evolve
    - Enables time-varying similarity matrices M_t
    - Correct application of 25% frequency filter (within year, not across years)

Author: Generated for KAIST Thesis
Date: 2025-10-28
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
import pandas as pd
import numpy as np

# Set console encoding for Korean text on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tnic.korean_text_processor import KoreanTextProcessor

# Directories
DATA_DIR = project_root / "data" / "korean_texts"
OUTPUT_BASE_DIR = DATA_DIR / "by_year"
REPORTS_DIR = project_root / "reports"

# Parameters (from H&P 2016)
MIN_WORDS_PER_FIRM = 20  # H&P: Exclude firms with <20 unique words
FREQUENCY_THRESHOLD = 0.25  # H&P: Exclude words in >25% of documents
# NO minimum firms per year - H&P (2016) has no such requirement

def main():
    print("=" * 80)
    print("PHASE 2.3 REDO: BUILD YEAR-BY-YEAR KOREAN CORPORA")
    print("=" * 80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "=" * 80)
    print("METHODOLOGY")
    print("=" * 80)
    print("\nFollowing Hoberg & Phillips (2016, JPE) Section II.A:")
    print("  - Build separate vocabulary W_t for each year t")
    print("  - Q_t is N_t × W_t matrix (N_t = firms in year t)")
    print("  - Apply H&P filters within each year:")
    print(f"    * Min {MIN_WORDS_PER_FIRM} words per firm")
    print(f"    * Exclude words in >{FREQUENCY_THRESHOLD*100:.0f}% of documents")

    # Load clean data
    print("\n" + "=" * 80)
    print("1. LOADING CLEAN DATA")
    print("=" * 80)

    input_file = DATA_DIR / "business_descriptions_clean.parquet"
    print(f"\nLoading: {input_file}")
    df = pd.read_parquet(input_file)

    print(f"Loaded {len(df):,} firm-years")
    print(f"\nData summary:")
    print(f"  Unique firms: {df['stock_code'].nunique():,}")
    print(f"  Year range: {df['year'].min()} - {df['year'].max()}")
    print(f"  Avg char count: {df['char_count'].mean():.0f}")

    # Check year distribution
    print("\n" + "=" * 80)
    print("2. YEAR DISTRIBUTION")
    print("=" * 80)

    year_counts = df.groupby('year').size().sort_index()
    print("\n[BASELINE] Firms per year from clean data:")
    for year, count in year_counts.items():
        print(f"  {year}: {count:>4} firms")

    # Store for sanity checking later
    year_counts_baseline = year_counts

    # Initialize processor
    print("\n" + "=" * 80)
    print("3. INITIALIZING KOREAN TEXT PROCESSOR")
    print("=" * 80)

    processor = KoreanTextProcessor(min_length=2)

    # Process each year
    print("\n" + "=" * 80)
    print("4. PROCESSING EACH YEAR SEPARATELY")
    print("=" * 80)

    # Store summary statistics
    summary_stats = {}

    years = sorted(df['year'].unique())

    for year in years:
        print(f"\n{'=' * 80}")
        print(f"YEAR {year}")
        print(f"{'=' * 80}")

        # Filter firms for this year
        df_year = df[df['year'] == year].copy()
        N_t = len(df_year)

        print(f"\n[INPUT] Firms in {year}: {N_t}")
        baseline_count = year_counts_baseline.get(year, 0)
        print(f"[SANITY CHECK] Expected {baseline_count}, got {N_t}")
        if N_t != baseline_count:
            print(f"  [WARNING] Mismatch! Difference: {abs(N_t - baseline_count)}")

        # NO SKIPPING - process all years per H&P (2016)

        # Create firm_year identifier
        df_year['firm_year'] = df_year['stock_code'] + '_' + df_year['year']

        # Process corpus for this year
        print(f"\nProcessing {N_t:,} documents...")
        texts = dict(zip(df_year['firm_year'], df_year['text']))

        # Use tqdm for progress
        firm_words = processor.process_corpus(texts, verbose=True, use_tqdm=True)

        print(f"\n[INITIAL RESULTS]")
        print(f"  Documents processed: {len(firm_words):,}")

        all_words_initial = set()
        for words in firm_words.values():
            all_words_initial.update(words)

        word_counts_initial = [len(words) for words in firm_words.values()]

        print(f"  Total unique words: {len(all_words_initial):,}")
        print(f"  Avg words per firm: {np.mean(word_counts_initial):.1f}")
        print(f"  Min words: {np.min(word_counts_initial)}")
        print(f"  Max words: {np.max(word_counts_initial)}")

        # Apply H&P filters WITHIN this year
        print(f"\n[APPLYING H&P FILTERS]")
        print(f"\nCitation: Hoberg & Phillips (2016) exclude:")
        print(f"  - Firms with <{MIN_WORDS_PER_FIRM} unique words")
        print(f"  - Words appearing in >{FREQUENCY_THRESHOLD*100:.0f}% of documents")

        # Filter 1: Minimum words per firm
        print(f"\n[FILTER 1: Minimum {MIN_WORDS_PER_FIRM} words per firm]")
        firm_words_filtered = processor.filter_by_min_words(
            firm_words,
            min_words=MIN_WORDS_PER_FIRM,
            verbose=True
        )

        # Filter 2: Frequency-based filtering
        print(f"\n[FILTER 2: Frequency-based filtering (>{FREQUENCY_THRESHOLD*100:.0f}% of documents)]")
        firm_words_filtered = processor.filter_by_frequency(
            firm_words_filtered,
            threshold=FREQUENCY_THRESHOLD,
            verbose=True
        )

        # Filter 3: Re-apply minimum words per firm
        # After removing common words in Filter 2, some firms may drop below the
        # 20-word threshold. H&P (2016) p.1430 requires >=20 unique words AFTER
        # all filtering steps, so we re-check here.
        print(f"\n[FILTER 3: Re-apply minimum {MIN_WORDS_PER_FIRM} words per firm after frequency filter]")
        firm_words_filtered = processor.filter_by_min_words(
            firm_words_filtered,
            min_words=MIN_WORDS_PER_FIRM,
            verbose=True
        )

        # Build year-specific vocabulary W_t
        print(f"\n[BUILDING YEAR-SPECIFIC VOCABULARY W_{year}]")

        all_words = []
        for words in firm_words_filtered.values():
            all_words.extend(words)

        word_freq = Counter(all_words)
        W_t = len(word_freq)

        print(f"  Vocabulary size W_{year}: {W_t:,} words")
        print(f"  Total word instances: {len(all_words):,}")

        # Get corpus statistics
        stats = processor.get_corpus_statistics(firm_words_filtered)

        # Build vocabulary dataframe
        vocab_data = []
        for word, freq in word_freq.most_common():
            # Count document frequency
            doc_freq = sum(1 for words in firm_words_filtered.values() if word in words)
            pct_docs = 100 * doc_freq / len(firm_words_filtered)

            vocab_data.append({
                'word': word,
                'frequency': freq,
                'document_frequency': doc_freq,
                'pct_documents': pct_docs
            })

        vocab_df = pd.DataFrame(vocab_data)

        # Build firm word sets dataframe
        firm_data = []
        for firm_year, words in firm_words_filtered.items():
            stock_code = firm_year.split('_')[0]
            firm_data.append({
                'firm_year': firm_year,
                'stock_code': stock_code,
                'year': year,
                'unique_nouns': np.array(sorted(words)),
                'word_count': len(words)
            })

        firm_df = pd.DataFrame(firm_data)

        # Save outputs for this year
        print(f"\n[SAVING OUTPUTS FOR {year}]")

        year_dir = OUTPUT_BASE_DIR / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        # Save firm word sets
        firm_output = year_dir / f"firm_word_sets_{year}.parquet"
        firm_df.to_parquet(firm_output, index=False)
        print(f"  [OK] {firm_output}")

        # Save vocabulary
        vocab_output = year_dir / f"corpus_vocabulary_{year}.csv"
        vocab_df.to_csv(vocab_output, index=False, encoding='utf-8-sig')
        print(f"  [OK] {vocab_output}")

        # Save statistics
        year_stats = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'year': year,
            'N_t_input': N_t,
            'N_t_output': len(firm_words_filtered),
            'W_t': W_t,
            'firms_removed': N_t - len(firm_words_filtered),
            'removal_rate': (N_t - len(firm_words_filtered)) / N_t if N_t > 0 else 0,
            'avg_words_per_firm': stats['avg_words_per_firm'],
            'min_words_per_firm': stats['min_words_per_firm'],
            'max_words_per_firm': stats['max_words_per_firm'],
            'avg_char_count': float(df_year['char_count'].mean()),
            'median_char_count': float(df_year['char_count'].median()),
            'h_and_p_filters': {
                'min_words_threshold': MIN_WORDS_PER_FIRM,
                'frequency_threshold': FREQUENCY_THRESHOLD
            },
            'anomaly_flags': {
                'very_small_sample': len(firm_words_filtered) < 10,
                'small_vocabulary': W_t < 100,
                'low_avg_words': stats['avg_words_per_firm'] < 30,
                'high_removal_rate': (N_t - len(firm_words_filtered)) / N_t > 0.5 if N_t > 0 else False
            }
        }

        stats_output = year_dir / f"corpus_statistics_{year}.json"
        with open(stats_output, 'w', encoding='utf-8') as f:
            json.dump(year_stats, f, indent=2, ensure_ascii=False)
        print(f"  [OK] {stats_output}")

        # Store summary
        summary_stats[year] = {
            'N_t_input': N_t,
            'N_t_output': len(firm_words_filtered),
            'W_t': W_t,
            'status': 'completed',
            'avg_words_per_firm': stats['avg_words_per_firm'],
            'removal_rate': (N_t - len(firm_words_filtered)) / N_t if N_t > 0 else 0
        }

        print(f"\n[YEAR {year} COMPLETE]")
        print(f"  N_{year} = {len(firm_words_filtered):,} firms")
        print(f"  W_{year} = {W_t:,} words")
        print(f"  Avg words per firm: {stats['avg_words_per_firm']:.1f}")

        print(f"\n[DETAILED STATISTICS]")
        print(f"  Input firms: {N_t:,}")
        print(f"  Firms after min-word filter: {len(firm_words_filtered):,}")
        print(f"  Firms removed: {N_t - len(firm_words_filtered):,}")
        print(f"  Avg char count: {df_year['char_count'].mean():.0f}")
        print(f"  Median char count: {df_year['char_count'].median():.0f}")
        print(f"  Words per firm: min={stats['min_words_per_firm']}, max={stats['max_words_per_firm']}")

        # Anomaly detection
        warnings = []
        if len(firm_words_filtered) < 10:
            warnings.append(f"Very small sample: {len(firm_words_filtered)} firms")
        if W_t < 100:
            warnings.append(f"Very small vocabulary: {W_t} words")
        if stats['avg_words_per_firm'] < 30:
            warnings.append(f"Low avg words/firm: {stats['avg_words_per_firm']:.1f}")
        if N_t > 0 and (N_t - len(firm_words_filtered)) > N_t * 0.5:
            warnings.append(f"High removal rate: {100*(N_t - len(firm_words_filtered))/N_t:.1f}%")

        if warnings:
            print(f"\n[ANOMALY WARNINGS]")
            for w in warnings:
                print(f"  * {w}")

    # Generate summary report
    print("\n" + "=" * 80)
    print("5. GENERATING SUMMARY REPORT")
    print("=" * 80)

    # Create summary markdown report
    report_lines = [
        "# Phase 2.3 REDO: Year-by-Year Korean Corpus Building",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Methodology",
        "",
        "### Citation",
        "",
        "**Hoberg, G., & Phillips, G. M. (2016).** Text-based network industries and endogenous product differentiation. *Journal of Political Economy*, 124(5), 1423-1465.",
        "",
        "### Key Approach (H&P 2016, Section II.A, p. 1430)",
        "",
        "> \"We define Q_t as the matrix containing the set of normalized vectors V_i for all firms i **in year t**. Thus **Q_t is an N_t × W matrix**, where **N_t is the number of firms in year t**.\"",
        "",
        "> \"W is 61,146 unique nouns and proper nouns **in 1996** and 55,605 **in 2008**.\"",
        "",
        "**Insight**: Vocabulary W changes each year as product markets evolve. Each year requires separate processing.",
        "",
        "### H&P Filters Applied (Per Year)",
        "",
        f"1. **Minimum words**: Exclude firms with <{MIN_WORDS_PER_FIRM} unique words",
        f"2. **Frequency threshold**: Exclude words appearing in >{FREQUENCY_THRESHOLD*100:.0f}% of documents",
        "",
        "## Results by Year",
        "",
        "### Summary Table",
        "",
        "| Year | N_t (Input) | N_t (Output) | W_t (Words) | Avg Words/Firm | Removal Rate |",
        "|------|-------------|--------------|-------------|----------------|--------------|"
    ]

    for year in years:
        if year in summary_stats:
            s = summary_stats[year]
            if s['status'] == 'completed':
                report_lines.append(
                    f"| {year} | {s['N_t_input']:,} | {s['N_t_output']:,} | {s['W_t']:,} | {s['avg_words_per_firm']:.1f} | {s['removal_rate']*100:.1f}% |"
                )

    report_lines.extend([
        "",
        "### Vocabulary Evolution",
        "",
        "H&P (2016) observed vocabulary changes:",
        "- 1996: 61,146 words",
        "- 2008: 55,605 words",
        "- Change: -9.1% (vocabulary consolidation)",
        "",
        "Korean market trends will be analyzed in Phase 3.2.",
        "",
        "## Output Files",
        "",
        "For each year:",
        "```",
        "data/korean_texts/by_year/YYYY/",
        "├── firm_word_sets_YYYY.parquet",
        "├── corpus_vocabulary_YYYY.csv",
        "└── corpus_statistics_YYYY.json",
        "```",
        "",
        "## Next Steps",
        "",
        "**Phase 3.1**: Build binary matrices Q_t for each year",
        "- Q_t is (N_t × W_t) binary matrix",
        "- Q_t[i,j] = 1 if firm i uses word j, else 0",
        "- Used to compute cosine similarity M_t in Phase 3.2"
    ])

    report_path = REPORTS_DIR / "2.3_corpus_building_by_year.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n[OK] Report saved to: {report_path}")

    # Final summary
    print("\n" + "=" * 80)
    print("PHASE 2.3 REDO COMPLETE")
    print("=" * 80)

    completed_years = [y for y, s in summary_stats.items() if s['status'] == 'completed']

    print(f"\n[SUMMARY]")
    print(f"  Years processed: {len(completed_years)}")
    print(f"  Year range: {min(completed_years)} - {max(completed_years)}")
    print(f"  Total firms (output): {sum(s['N_t_output'] for s in summary_stats.values() if s['status'] == 'completed'):,}")

    if completed_years:
        W_min = min(summary_stats[y]['W_t'] for y in completed_years)
        W_max = max(summary_stats[y]['W_t'] for y in completed_years)
        print(f"  Vocabulary range: {W_min:,} - {W_max:,} words")
        print(f"  Vocabulary change: {(W_max/W_min - 1)*100:+.1f}%")

    print("\n[NEXT STEP]")
    print("  Run: poetry run python scripts/build_binary_matrices_by_year.py")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
