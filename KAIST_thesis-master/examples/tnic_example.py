# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # TNIC Pipeline Example
#
# This notebook demonstrates the **Text-Based Network Industry Classification (TNIC)**
# pipeline following the methodology from:
#
# **Hoberg, Gerard, and Gordon Phillips. "Text-based network industries and endogenous 
# product differentiation." Journal of Political Economy 124, no. 5 (2016): 1423-1465.**
#
# ## Overview
#
# The TNIC methodology computes **product market similarity** between firms based on
# their 10-K business descriptions. Key advantages:
#
# 1. **Dynamic**: Updates annually with new 10-K filings
# 2. **Granular**: Captures product-level rather than industry-level relationships
# 3. **Data-driven**: No manual classification required
# 4. **Network-based**: Reveals competitive dynamics and peer relationships
#
# ## Pipeline Steps
#
# 1. **Text Cleaning**: Lowercase, punctuation removal, stopwords, POS tagging
# 2. **Corpus Building**: Generate universe of all unique product words
# 3. **Vectorization**: Create binary word presence matrix
# 4. **Similarity Computation**: Calculate pairwise cosine similarities

# %% [markdown]
# ## Setup

# %%
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from tnic import TNICPipeline, TextCleaner, TNICProcessor, SimilarityCalculator
from tnic.config import TNICConfig
from tnic.utils import setup_logging

# Setup logging
setup_logging(level="INFO")

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
sns.set_style('whitegrid')

# %% [markdown]
# ## Method 1: End-to-End Pipeline (Recommended)
#
# The easiest way to use the TNIC pipeline is through the `TNICPipeline` class,
# which handles all steps automatically.

# %%
# Define paths
input_dir = Path("../computational_linguistics_exercise/data/rantextsout")
output_dir = Path("../outputs/tnic")

# Create and run pipeline
pipeline = TNICPipeline(output_dir=output_dir)
results = pipeline.run(input_dir=input_dir, save_outputs=True)

# %% [markdown]
# ## Examine Results

# %%
# Print summary statistics
print("=" * 60)
print("TNIC Pipeline Results")
print("=" * 60)
print(f"Number of firms: {results['n_firms']}")
print(f"Corpus size: {results['n_words']} words")
print(f"Mean similarity: {results['mean_similarity']:.4f}")
print(f"Std similarity: {results['std_similarity']:.4f}")
print(f"Execution time: {results['execution_time']:.2f} seconds")
print("=" * 60)

# %%
# View word statistics
word_stats = results['word_stats']
print("\nTop 20 Most Common Words:")
print(word_stats.head(20))

# %%
# View firm statistics
firm_stats = results['firm_stats']
print("\nFirm Statistics:")
print(firm_stats.describe())

# %%
# View most similar firm pairs
pairwise_df = results['pairwise_df']
print("\nTop 10 Most Similar Firm Pairs:")
print(pairwise_df.head(10))

# %%
# View least similar firm pairs
print("\nTop 10 Least Similar Firm Pairs:")
print(pairwise_df.tail(10))

# %% [markdown]
# ## Visualizations

# %%
# Plot similarity distribution
plt.figure(figsize=(10, 6))
plt.hist(pairwise_df['similarity'], bins=50, edgecolor='black', alpha=0.7)
plt.xlabel('Cosine Similarity', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title('Distribution of Pairwise Firm Similarities', fontsize=14, fontweight='bold')
plt.axvline(pairwise_df['similarity'].mean(), color='red', linestyle='--', 
            label=f'Mean = {pairwise_df["similarity"].mean():.3f}')
plt.legend()
plt.tight_layout()
plt.savefig(output_dir / 'similarity_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# %%
# Plot firm word counts
plt.figure(figsize=(12, 6))
firm_stats_sorted = firm_stats.sort_values('n_words', ascending=False)
plt.bar(range(len(firm_stats_sorted)), firm_stats_sorted['n_words'])
plt.xlabel('Firm Index', fontsize=12)
plt.ylabel('Number of Unique Words', fontsize=12)
plt.title('Word Count Distribution Across Firms', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'firm_word_counts.png', dpi=300, bbox_inches='tight')
plt.show()

# %%
# Plot word frequency distribution
plt.figure(figsize=(10, 6))
plt.hist(word_stats['count'], bins=30, edgecolor='black', alpha=0.7)
plt.xlabel('Number of Firms Using Word', fontsize=12)
plt.ylabel('Number of Words', fontsize=12)
plt.title('Word Frequency Distribution', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'word_frequency_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Method 2: Step-by-Step Processing
#
# For more control, you can use individual components of the pipeline.

# %%
# Step 1: Clean text data
config = TNICConfig(min_word_length=2, remove_stopwords=True)
cleaner = TextCleaner(config=config)

# Get list of text files
file_paths = list(input_dir.glob("*.txt"))
print(f"Found {len(file_paths)} text files")

# Clean all files
firm_tokens = cleaner.clean_multiple_files(file_paths)
print(f"Cleaned {len(firm_tokens)} files")
print(f"\nExample - First firm: {list(firm_tokens.keys())[0]}")
print(f"Number of unique tokens: {len(list(firm_tokens.values())[0])}")
print(f"Sample tokens: {list(list(firm_tokens.values())[0])[:20]}")

# %%
# Step 2: Build corpus and binary matrix
processor = TNICProcessor(config=config)
corpus = processor.build_corpus(firm_tokens)
binary_matrix = processor.build_binary_matrix()

print(f"Corpus size: {len(corpus)} words")
print(f"Binary matrix shape: {binary_matrix.shape}")
print(f"Matrix sparsity: {(binary_matrix == 0).sum() / binary_matrix.size * 100:.2f}%")

# %%
# Step 3: Compute similarities
calculator = SimilarityCalculator(config=config)
firm_ids = list(firm_tokens.keys())
similarity_matrix = calculator.compute_similarity(binary_matrix, firm_ids)

print(f"Similarity matrix shape: {similarity_matrix.shape}")
print(f"\nSimilarity statistics:")
print(calculator.compute_summary_statistics())

# %% [markdown]
# ## Find Industry Peers
#
# Get the most similar firms (industry peers) for a specific firm.

# %%
# Pick a firm
example_firm = list(firm_tokens.keys())[0]
print(f"Finding industry peers for firm: {example_firm}\n")

# Get top 10 most similar firms
peers = calculator.get_firm_neighbors(example_firm, n=10)
print("Top 10 Most Similar Firms:")
print(peers)

# %%
# Get peers with similarity > 0.2
peers_threshold = pipeline.get_industry_peers(example_firm, threshold=0.2)
print(f"\nFirms with similarity > 0.2: {len(peers_threshold)}")
print(peers_threshold)

# %% [markdown]
# ## Compare with Hoberg-Phillips TNIC Data (Optional)
#
# If you have the Hoberg-Phillips TNIC database, you can compare your results.

# %%
# Uncomment and run if you have the TNIC data
# tnic_file = Path("../data/hoberg/tnic3_data.txt")
# mapping_file = Path("../computational_linguistics_exercise/data/Map_gvkey_cik.xlsm")
# 
# if tnic_file.exists() and mapping_file.exists():
#     comparison = pipeline.compare_with_hoberg_phillips(
#         tnic_file=tnic_file,
#         year=2018,
#         mapping_file=mapping_file
#     )
#     
#     print("\nComparison with Hoberg-Phillips TNIC:")
#     print(f"Matching pairs: {len(comparison)}")
#     print(f"\nCorrelation between scores:")
#     print(comparison[['score_sample', 'score_tnic']].corr())
#     
#     # Plot comparison
#     plt.figure(figsize=(10, 10))
#     plt.scatter(comparison['score_tnic'], comparison['score_sample'], alpha=0.5)
#     plt.plot([0, 1], [0, 1], 'r--', label='45° line')
#     plt.xlabel('Hoberg-Phillips TNIC Score', fontsize=12)
#     plt.ylabel('Sample TNIC Score', fontsize=12)
#     plt.title('Comparison: Sample vs. Full TNIC Scores', fontsize=14, fontweight='bold')
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(output_dir / 'tnic_comparison.png', dpi=300, bbox_inches='tight')
#     plt.show()

# %% [markdown]
# ## Export Results
#
# All results are automatically saved to the output directory:
# - `binary_matrix.csv`: Word presence matrix (words × firms)
# - `similarity_matrix.csv`: Pairwise similarity matrix (firms × firms)
# - `pairwise_similarities.csv`: Long-format similarity scores
# - `firm_statistics.csv`: Statistics for each firm
# - `word_statistics.csv`: Statistics for each word
# - `similarity_statistics.csv`: Summary statistics
# - `top10_words.png`: Visualization of top words

# %%
print(f"All outputs saved to: {output_dir}")
print("\nGenerated files:")
for file in sorted(output_dir.glob("*")):
    print(f"  - {file.name}")

# %% [markdown]
# ## Conclusion
#
# This notebook demonstrated the complete TNIC pipeline for computing text-based
# industry classifications. The pipeline can be used for:
#
# 1. **Industry Definition**: Identify product market competitors
# 2. **Peer Analysis**: Find similar firms for benchmarking
# 3. **Network Analysis**: Study industry structure and dynamics
# 4. **Event Studies**: Measure spillover effects among related firms
# 5. **Portfolio Construction**: Build peer-based investment strategies
#
# For more information, see the Hoberg-Phillips papers:
# - Hoberg & Phillips (2010) RFS: "Product Market Synergies and Competition..."
# - Hoberg & Phillips (2016) JPE: "Text-Based Network Industries..."

# %%
