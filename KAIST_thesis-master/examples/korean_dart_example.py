"""
Complete example: TNIC analysis on Korean DART financial disclosures

This example demonstrates the full pipeline from MongoDB data retrieval
to TNIC network computation and fixed industry clustering.

**Prerequisites:**
1. MongoDB with DART disclosure data
2. pymongo installed (included in project dependencies)
3. KoNLPy installed: poetry install --extras korean
4. Mecab-ko installed (recommended): pip install python-mecab-ko

**Expected MongoDB Schema:**
{
    "document_id": "20240312000736_020000",
    "stock_code": "005930",
    "corp_name": "삼성전자",
    "year": "2024",
    "section_code": "020100",
    "text": "당사는 본사를 거점으로...",
    "char_count": 38037,
    "word_count": 7979
}

**Data Source:**
Korean DART (Data Analysis, Retrieval and Transfer System)
- Equivalent to US SEC EDGAR
- Contains financial disclosures from Korean listed companies
- Section "020100" (사업의 개요) ≈ US 10-K Item 1 (Business Description)
"""

from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_mongodb_direct():
    """
    Example 1: Direct MongoDB query and TNIC analysis
    
    This uses MongoDBAdapter with pymongo to directly query MongoDB.
    Settings are loaded from config.yaml (DB: FS, Collection: A001)
    """
    from tnic.integrations import MongoDBAdapter
    from tnic import TNICConfig, KoreanTextCleaner
    
    print("\n" + "="*70)
    print("EXAMPLE 1: Direct MongoDB Query → TNIC Analysis")
    print("="*70)
    
    # Step 1: Connect to MongoDB (reads from config.yaml)
    adapter = MongoDBAdapter.from_config()
    # Or explicitly: adapter = MongoDBAdapter("mongodb://localhost:27017", "FS", "A001")
    
    # Get database statistics
    stats = adapter.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total documents: {stats['total_documents']:,}")
    print(f"  Years available: {stats['years']}")
    print(f"  Number of firms: {stats['n_firms']:,}")
    print(f"  Total words: {stats['total_words']:,}")
    
    # Step 2: Query data for analysis
    # Example: Top Korean tech companies in 2024
    stock_codes = [
        "005930",  # 삼성전자 (Samsung Electronics)
        "000660",  # SK하이닉스 (SK Hynix)
        "005380",  # 현대자동차 (Hyundai Motor)
        "035420",  # NAVER
        "035720",  # 카카오 (Kakao)
    ]
    
    print(f"\nQuerying data for {len(stock_codes)} companies (2024)...")
    tnic_input = adapter.get_texts(
        stock_codes=stock_codes,
        year="2024",
        section_codes=["020100"]  # 사업의 개요 (Business Overview)
    )
    
    print(f"\nPrepared {len(tnic_input)} firm texts:")
    for firm_id, text in tnic_input.items():
        print(f"  {firm_id}: {len(text):,} characters")
    
    # Step 4: Configure TNIC for Korean text
    config = TNICConfig(
        language="korean",
        korean_tokenizer="mecab",  # Best for Korean
        use_frequency_stopwords=True,  # H-P methodology
        frequency_stopword_threshold=0.25,
        min_unique_words=20,
        apply_median_adjustment=True,
        tnic_similarity_threshold=0.2132
    )
    
    # Step 5: Run TNIC pipeline
    print("\n" + "-"*70)
    print("Running TNIC Pipeline (Korean Text)...")
    print("-"*70)
    
    # For Korean text, we need to use KoreanTextCleaner
    cleaner = KoreanTextCleaner(config)
    
    # Clean texts
    print("\nStep 1: Text Cleaning & Tokenization...")
    cleaned_tokens = cleaner.clean_multiple_texts(
        tnic_input,
        use_frequency_stopwords=config.use_frequency_stopwords
    )
    
    print(f"  Cleaned {len(cleaned_tokens)} firm texts")
    for firm_id, tokens in cleaned_tokens.items():
        print(f"  {firm_id}: {len(tokens)} tokens, {len(set(tokens))} unique")
    
    # Build corpus and similarity matrix
    from tnic import TNICProcessor, SimilarityCalculator
    
    processor = TNICProcessor(config)
    print("\nStep 2: Building Vocabulary Corpus...")
    corpus_result = processor.build_corpus(cleaned_tokens)
    
    print(f"  Total vocabulary size: {len(corpus_result['corpus']):,} words")
    print(f"  Top 10 words: {list(corpus_result['corpus'])[:10]}")
    
    print("\nStep 3: Creating Binary Word Matrix...")
    binary_result = processor.create_binary_matrix(
        cleaned_tokens,
        corpus_result['corpus']
    )
    
    print(f"  Matrix shape: {binary_result['binary_df'].shape}")
    print(f"  (firms={binary_result['binary_df'].shape[1]}, "
          f"words={binary_result['binary_df'].shape[0]})")
    
    # Compute similarities
    calculator = SimilarityCalculator(config)
    
    print("\nStep 4: Computing Raw Cosine Similarity...")
    raw_similarity = calculator.compute_similarity(
        binary_result['binary_df'].values.T,  # Transpose to firms × words
        list(binary_result['binary_df'].columns)
    )
    
    print(f"  Similarity matrix: {raw_similarity.shape}")
    print(f"  Mean similarity: {raw_similarity.mean():.4f}")
    
    # Apply H-P median adjustment
    if config.apply_median_adjustment:
        print("\nStep 5: Applying H-P Median Adjustment...")
        tnic_scores = calculator.compute_tnic_scores(
            raw_similarity,
            list(binary_result['binary_df'].columns),
            threshold=config.tnic_similarity_threshold
        )
        
        print(f"  Adjusted mean: {tnic_scores['adjusted_scores'].mean():.4f}")
        print(f"  Threshold: {config.tnic_similarity_threshold:.4f}")
        
        # Print peer relationships
        print("\n" + "-"*70)
        print("TNIC Peer Relationships (Adjusted Scores):")
        print("-"*70)
        
        firm_ids = list(binary_result['binary_df'].columns)
        for i, firm_i in enumerate(firm_ids):
            peers = []
            for j, firm_j in enumerate(firm_ids):
                if i != j and tnic_scores['tnic_peers'][i, j] == 1:
                    score = tnic_scores['adjusted_scores'][i, j]
                    peers.append(f"{firm_j} ({score:.4f})")
            
            if peers:
                print(f"\n{firm_i}:")
                for peer in peers:
                    print(f"  → {peer}")
            else:
                print(f"\n{firm_i}: No peers above threshold")
    
    adapter.close()
    print("\n" + "="*70)


def example_2_panel_data():
    """
    Example 2: Panel data analysis (multiple years)
    
    This demonstrates querying and analyzing multiple years of data.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Panel Data Analysis (Multiple Years)")
    print("="*70)
    
    from tnic.integrations import MongoDBAdapter
    from tnic import TNICConfig, KoreanTextCleaner
    
    # Connect to MongoDB (from config.yaml)
    adapter = MongoDBAdapter.from_config()
    
    # Query multiple years
    print("\nQuerying 2022-2024 data...")
    
    stock_codes = ["005930", "000660", "005380"]
    years_list = ["2022", "2023", "2024"]
    
    # Query each year separately
    panel_data = {}
    for year in years_list:
        texts = adapter.get_texts(
            stock_codes=stock_codes,
            year=year,
            section_codes=["020100"]
        )
        panel_data[year] = texts
        print(f"  {year}: {len(texts)} firms")
    
    # Run TNIC for each year
    config = TNICConfig(language="korean", korean_tokenizer="mecab")
    cleaner = KoreanTextCleaner(config)
    
    for year, texts in panel_data.items():
        print(f"\n{'-'*70}")
        print(f"Processing Year {year}")
        print(f"{'-'*70}")
        
        cleaned = cleaner.clean_multiple_texts(texts)
        
        print(f"  Cleaned {len(cleaned)} firms")
        for firm_id, tokens in cleaned.items():
            print(f"    {firm_id}: {len(set(tokens))} unique words")
    
    adapter.close()
    print("\n" + "="*70)


def example_3_fixed_industries():
    """
    Example 3: Creating fixed industry classifications (like SIC/NAICS)
    
    This applies hierarchical clustering to create transitive industry groups.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Fixed Industry Classification (Clustering)")
    print("="*70)
    
    from tnic.integrations import MongoDBAdapter
    from tnic import TNICConfig, KoreanTextCleaner, TNICProcessor
    from tnic import SimilarityCalculator, FixedIndustryClusterer
    
    # Query larger sample for clustering (from config.yaml)
    adapter = MongoDBAdapter.from_config()
    
    print("\nQuerying broader sample (top 50 KOSPI companies)...")
    # This would need actual stock codes
    stock_codes = [f"00{i:04d}0" for i in range(50)]  # Placeholder
    
    tnic_input = adapter.get_texts(
        stock_codes=stock_codes,
        year="2024",
        section_codes=["020100"]
    )
    
    print(f"  Retrieved {len(tnic_input)} firms")
    
    # Run preprocessing
    config = TNICConfig(language="korean", korean_tokenizer="mecab")
    cleaner = KoreanTextCleaner(config)
    processor = TNICProcessor(config)
    calculator = SimilarityCalculator(config)
    
    print("\nPreprocessing...")
    cleaned = cleaner.clean_multiple_texts(tnic_input)
    corpus_result = processor.build_corpus(cleaned)
    binary_result = processor.create_binary_matrix(cleaned, corpus_result['corpus'])
    
    print("\nComputing similarities...")
    raw_similarity = calculator.compute_similarity(
        binary_result['binary_df'].values.T,
        list(binary_result['binary_df'].columns)
    )
    
    # Create fixed industries
    print("\nRunning hierarchical clustering...")
    clusterer = FixedIndustryClusterer(n_industries=10)  # 10 industries for demo
    
    industries = clusterer.fit(
        raw_similarity,
        list(binary_result['binary_df'].columns)
    )
    
    print(f"\nCreated {len(industries)} industries:")
    for industry_id, firms in industries.items():
        print(f"  Industry {industry_id}: {len(firms)} firms")
        print(f"    {', '.join(list(firms)[:5])}...")
    
    # Save results
    output_dir = Path("outputs/korean_industries")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clusterer.save_industries(output_dir / "korean_industries_10.csv")
    print(f"\nSaved industry assignments to {output_dir}")
    
    adapter.close()
    print("\n" + "="*70)


def example_4_cross_sectional_analysis():
    """
    Example 4: Cross-sectional analysis (compare firms in same year)
    
    Use case: Identify product market competitors within an industry
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Cross-Sectional Competitor Analysis")
    print("="*70)
    
    from tnic.integrations import MongoDBAdapter
    from tnic import TNICConfig, KoreanTextCleaner, TNICProcessor, SimilarityCalculator
    import numpy as np
    
    # Focus on a specific industry (e.g., semiconductors)
    semiconductor_firms = {
        "005930": "삼성전자",
        "000660": "SK하이닉스",
        "042700": "한미반도체",
        "058470": "리노공업",
    }
    
    print(f"\nAnalyzing {len(semiconductor_firms)} semiconductor companies...")
    
    # Connect from config.yaml
    adapter = MongoDBAdapter.from_config()
    
    tnic_input = adapter.get_texts(
        stock_codes=list(semiconductor_firms.keys()),
        year="2024",
        section_codes=["020100"]
    )
    
    # Run TNIC
    config = TNICConfig(
        language="korean",
        korean_tokenizer="mecab",
        apply_median_adjustment=False  # For direct similarity comparison
    )
    
    cleaner = KoreanTextCleaner(config)
    processor = TNICProcessor(config)
    calculator = SimilarityCalculator(config)
    
    cleaned = cleaner.clean_multiple_texts(tnic_input)
    corpus_result = processor.build_corpus(cleaned)
    binary_result = processor.create_binary_matrix(cleaned, corpus_result['corpus'])
    
    raw_similarity = calculator.compute_similarity(
        binary_result['binary_df'].values.T,
        list(binary_result['binary_df'].columns)
    )
    
    # Print similarity matrix
    print("\n" + "-"*70)
    print("Pairwise Product Similarity Matrix:")
    print("-"*70)
    
    firm_ids = list(binary_result['binary_df'].columns)
    
    # Header
    print(f"\n{'':15s}", end="")
    for fid in firm_ids:
        stock_code = fid.split('_')[1]  # Extract stock code
        print(f"{stock_code:>12s}", end="")
    print()
    
    # Matrix rows
    for i, fid_i in enumerate(firm_ids):
        stock_code_i = fid_i.split('_')[1]
        corp_name = semiconductor_firms.get(stock_code_i, "Unknown")
        print(f"{corp_name[:12]:15s}", end="")
        
        for j, fid_j in enumerate(firm_ids):
            if i == j:
                print(f"{'—':>12s}", end="")
            else:
                sim = raw_similarity[i, j]
                print(f"{sim:>12.4f}", end="")
        print()
    
    # Find most similar pair
    max_sim = -1
    max_pair = (None, None)
    
    for i in range(len(firm_ids)):
        for j in range(i+1, len(firm_ids)):
            if raw_similarity[i, j] > max_sim:
                max_sim = raw_similarity[i, j]
                max_pair = (firm_ids[i], firm_ids[j])
    
    print(f"\nMost similar pair:")
    stock_1 = max_pair[0].split('_')[1]
    stock_2 = max_pair[1].split('_')[1]
    print(f"  {semiconductor_firms[stock_1]} ↔ {semiconductor_firms[stock_2]}")
    print(f"  Similarity: {max_sim:.4f}")
    
    adapter.close()
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n")
    print("="*70)
    print("  TNIC Analysis on Korean DART Financial Disclosures")
    print("  Hoberg-Phillips (2016) Methodology Adapted for Korean Text")
    print("="*70)
    
    # Note: These examples require MongoDB to be running with dart-fss-text data
    # Uncomment the example you want to run:
    
    # example_1_mongodb_direct()
    # example_2_panel_data()
    # example_3_fixed_industries()
    # example_4_cross_sectional_analysis()
    
    print("\nTo run examples, uncomment the desired function in __main__")
    print("Make sure MongoDB is running with DART disclosure data")
    print("\nPrerequisites:")
    print("  1. Configure tnic/config.yaml with your MongoDB settings")
    print("  2. Korean support: poetry install --extras korean")
    print("  3. Mecab-ko: pip install python-mecab-ko")
    print("  4. DART data in MongoDB")
    print("\nCurrent config: Database 'FS', Collection 'A001' (from config.yaml)")
