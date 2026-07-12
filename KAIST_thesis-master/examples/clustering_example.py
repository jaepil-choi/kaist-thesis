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
# # Fixed Industry Classification Example
#
# This notebook demonstrates the **Fixed Industry Classification** algorithm
# from Hoberg-Phillips (2016, Appendix B).
#
# Unlike TNIC (which allows each firm to have unique peers), fixed industries
# impose **transitivity**: if firms A and B are in the same industry, and firms
# B and C are in the same industry, then A and C must also be in the same industry.
#
# This makes fixed industries comparable to SIC/NAICS classifications.

# %% [markdown]
# ## Setup

# %%
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from tnic import TNICPipeline, FixedIndustryClusterer
from tnic.config import TNICConfig
from tnic.utils import setup_logging

# Setup logging
setup_logging(level="INFO")

# Set display options
pd.set_option('display.max_columns', None)
sns.set_style('whitegrid')

# %% [markdown]
# ## Step 1: Run Basic Pipeline to Get Similarities

# %%
# Define paths
input_dir = Path("../computational_linguistics_exercise/data/rantextsout")
output_dir = Path("../outputs/tnic")

# Run pipeline to get firm similarities
pipeline = TNICPipeline(output_dir=output_dir)
results = pipeline.run(input_dir=input_dir, save_outputs=True)

print(f"Processed {results['n_firms']} firms")
print(f"Corpus: {results['n_words']} words")

# %% [markdown]
# ## Step 2: Create Fixed Industries

# %%
# Get firm similarities (use raw similarities, not adjusted)
# Re-compute raw similarities if we used median adjustment
from tnic import SimilarityCalculator

calculator = SimilarityCalculator()
raw_similarity = calculator.compute_similarity(
    results['binary_df'].values.T,  # Transpose: firms × words
    list(results['binary_df'].index)
)

print(f"Similarity matrix shape: {raw_similarity.shape}")

# %% [markdown]
# ## Step 3: Run Clustering Algorithm
#
# We'll create industries at different granularity levels to compare:
# - **50 industries**: Very coarse (like SIC-1)
# - **100 industries**: Coarse (like SIC-2)
# - **300 industries**: Medium (like SIC-3) ← **H-P use this**
# - **500 industries**: Fine (like SIC-4)

# %%
# Create 300 industries (SIC-3 granularity)
clusterer_300 = FixedIndustryClusterer(n_industries=300)
industries_300 = clusterer_300.fit(
    raw_similarity,
    list(results['binary_df'].index)
)

print(f"\nCreated {len(industries_300)} industries")

# %% [markdown]
# ## Step 4: Analyze Industry Structure

# %%
# Convert to DataFrame
ind_df = clusterer_300.to_dataframe()
print("\nIndustry Assignments:")
print(ind_df.head(20))

# %%
# Industry size distribution
industry_sizes = ind_df.groupby('industry_id').size().sort_values(ascending=False)

print("\nLargest Industries:")
print(industry_sizes.head(10))

print("\nSmallest Industries (single firms):")
print(f"Number of single-firm industries: {(industry_sizes == 1).sum()}")

# %%
# Plot industry size distribution
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.hist(industry_sizes, bins=30, edgecolor='black', alpha=0.7)
plt.xlabel('Industry Size (# firms)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title('Distribution of Industry Sizes (300 Industries)', fontsize=14, fontweight='bold')
plt.axvline(industry_sizes.median(), color='red', linestyle='--', 
            label=f'Median = {industry_sizes.median():.0f}')
plt.legend()

plt.subplot(1, 2, 2)
# Log scale for better visualization
plt.hist(np.log10(industry_sizes + 1), bins=30, edgecolor='black', alpha=0.7)
plt.xlabel('Log10(Industry Size + 1)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title('Distribution (Log Scale)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'industry_size_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Step 5: Compare Different Granularities

# %%
# Create industries at different granularities
granularities = [50, 100, 200, 300, 400, 500]
clusterers = {}

for n_ind in granularities:
    print(f"\nCreating {n_ind} industries...")
    clusterer = FixedIndustryClusterer(n_industries=n_ind)
    industries = clusterer.fit(raw_similarity, list(results['binary_df'].index))
    clusterers[n_ind] = clusterer

# %%
# Compare industry size statistics
comparison_data = []

for n_ind, clusterer in clusterers.items():
    sizes = [len(firms) for firms in clusterer.industries.values()]
    comparison_data.append({
        'n_industries': n_ind,
        'mean_size': np.mean(sizes),
        'median_size': np.median(sizes),
        'max_size': max(sizes),
        'n_single_firm': sum(1 for s in sizes if s == 1),
        'pct_single_firm': 100 * sum(1 for s in sizes if s == 1) / n_ind
    })

comparison_df = pd.DataFrame(comparison_data)
print("\nComparison Across Granularities:")
print(comparison_df.to_string(index=False))

# %%
# Plot comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Mean industry size
axes[0, 0].plot(comparison_df['n_industries'], comparison_df['mean_size'], 'o-', linewidth=2, markersize=8)
axes[0, 0].axvline(300, color='red', linestyle='--', alpha=0.5, label='SIC-3 (300)')
axes[0, 0].set_xlabel('Number of Industries', fontsize=11)
axes[0, 0].set_ylabel('Mean Industry Size', fontsize=11)
axes[0, 0].set_title('Mean Industry Size vs. Granularity', fontsize=12, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# Median industry size
axes[0, 1].plot(comparison_df['n_industries'], comparison_df['median_size'], 'o-', linewidth=2, markersize=8, color='orange')
axes[0, 1].axvline(300, color='red', linestyle='--', alpha=0.5, label='SIC-3 (300)')
axes[0, 1].set_xlabel('Number of Industries', fontsize=11)
axes[0, 1].set_ylabel('Median Industry Size', fontsize=11)
axes[0, 1].set_title('Median Industry Size vs. Granularity', fontsize=12, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(alpha=0.3)

# Max industry size
axes[1, 0].plot(comparison_df['n_industries'], comparison_df['max_size'], 'o-', linewidth=2, markersize=8, color='green')
axes[1, 0].axvline(300, color='red', linestyle='--', alpha=0.5, label='SIC-3 (300)')
axes[1, 0].set_xlabel('Number of Industries', fontsize=11)
axes[1, 0].set_ylabel('Largest Industry Size', fontsize=11)
axes[1, 0].set_title('Largest Industry vs. Granularity', fontsize=12, fontweight='bold')
axes[1, 0].legend()
axes[1, 0].grid(alpha=0.3)

# Percentage single-firm industries
axes[1, 1].plot(comparison_df['n_industries'], comparison_df['pct_single_firm'], 'o-', linewidth=2, markersize=8, color='purple')
axes[1, 1].axvline(300, color='red', linestyle='--', alpha=0.5, label='SIC-3 (300)')
axes[1, 1].set_xlabel('Number of Industries', fontsize=11)
axes[1, 1].set_ylabel('Single-Firm Industries (%)', fontsize=11)
axes[1, 1].set_title('Single-Firm Industries vs. Granularity', fontsize=12, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'granularity_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Step 6: Save Results

# %%
# Save 300-industry classification
clusterer_300.save_industries(output_dir / 'fixed_industries_300.csv')
print(f"\nSaved industry assignments to {output_dir / 'fixed_industries_300.csv'}")

# Save comparison
comparison_df.to_csv(output_dir / 'industry_granularity_comparison.csv', index=False)
print(f"Saved granularity comparison to {output_dir / 'industry_granularity_comparison.csv'}")

# %% [markdown]
# ## Step 7: Compare with TNIC
#
# TNIC (intransitive) vs. Fixed Industries (transitive)

# %%
# Get TNIC peer counts from earlier results
if 'tnic_peers' in results:
    tnic_peers = results['tnic_peers']
    tnic_peer_counts = tnic_peers.sum(axis=1) - 1  # Exclude self
    
    # Get fixed industry peer counts
    fixed_peer_counts = ind_df.groupby('industry_id').size() - 1  # Exclude self
    firm_to_count = {}
    for firm_id in ind_df['firm_id']:
        ind_id = ind_df[ind_df['firm_id'] == firm_id]['industry_id'].values[0]
        firm_to_count[firm_id] = fixed_peer_counts[ind_id]
    
    fixed_counts = [firm_to_count[fid] for fid in results['binary_df'].index]
    
    # Compare
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.hist([tnic_peer_counts, fixed_counts], bins=30, alpha=0.6, 
             label=['TNIC (intransitive)', 'Fixed (transitive)'],
             edgecolor='black')
    plt.xlabel('Number of Peers', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Peer Count Distribution: TNIC vs. Fixed', fontsize=13, fontweight='bold')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.scatter(tnic_peer_counts, fixed_counts, alpha=0.5)
    plt.plot([0, max(max(tnic_peer_counts), max(fixed_counts))], 
             [0, max(max(tnic_peer_counts), max(fixed_counts))], 
             'r--', label='45° line')
    plt.xlabel('TNIC Peers (intransitive)', fontsize=12)
    plt.ylabel('Fixed Industry Peers (transitive)', fontsize=12)
    plt.title('TNIC vs. Fixed Industry Peer Counts', fontsize=13, fontweight='bold')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'tnic_vs_fixed_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\nPeer Count Statistics:")
    print(f"TNIC (intransitive):")
    print(f"  - Mean: {tnic_peer_counts.mean():.1f}")
    print(f"  - Median: {np.median(tnic_peer_counts):.0f}")
    print(f"Fixed Industries (transitive):")
    print(f"  - Mean: {np.mean(fixed_counts):.1f}")
    print(f"  - Median: {np.median(fixed_counts):.0f}")

# %% [markdown]
# ## Conclusion
#
# We've successfully implemented the Fixed Industry Classification algorithm
# from Hoberg-Phillips (2016, Appendix B). Key observations:
#
# 1. **Transitivity**: Fixed industries enforce transitivity (if A~B and B~C, then A~C)
# 2. **Granularity**: Can create any number of industries (we used 300 ≈ SIC-3)
# 3. **Comparison**: Fixed industries typically have MORE peers per firm than TNIC
#    because transitivity forces all industry members to be considered peers
# 4. **Trade-off**: Fixed industries are simpler but TNIC is more flexible

# %%
