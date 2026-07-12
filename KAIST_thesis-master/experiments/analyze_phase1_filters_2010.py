"""
Phase 1 Filter Analysis for Year 2010

This script applies all Phase 1 filtering steps to year 2010 data
and reports firm counts at each step to understand data loss.

Usage:
    poetry run python experiments/analyze_phase1_filters_2010.py
"""

from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from tnic.data_loader import MongoDBLoader

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

YEAR = 2010

print("=" * 80)
print(f"PHASE 1 FILTER ANALYSIS: YEAR {YEAR}")
print("=" * 80)
print()

# ============================================================================
# STEP 0: Load MongoDB data for 2010
# ============================================================================

print("STEP 0: Baseline (MongoDB)")
print("-" * 80)

with MongoDBLoader() as loader:
    df_mongo = loader.extract_business_descriptions(
        year_range=(YEAR, YEAR),
        section_codes=['020000', '020100'],
        report_types=['A001'],
        fields=['rcept_no', 'rcept_dt', 'year', 'corp_name', 'stock_code',
                'level', 'text', 'char_count']
    )

print(f"Total documents: {len(df_mongo):,}")
print(f"Unique firms (stock_code): {df_mongo['stock_code'].nunique():,}")
print(f"Unique rcept_no: {df_mongo['rcept_no'].nunique():,}")
print()

# Store baseline for comparison
n_docs_baseline = len(df_mongo)
n_firms_baseline = df_mongo['stock_code'].nunique()

df_clean = df_mongo.copy()

# ============================================================================
# STEP 1: Remove zero-length documents
# ============================================================================

print("STEP 1: Remove zero-length documents")
print("-" * 80)

n_before = len(df_clean)
n_firms_before = df_clean['stock_code'].nunique()

df_clean = df_clean[df_clean['char_count'] > 0]

n_removed = n_before - len(df_clean)
n_firms_after = df_clean['stock_code'].nunique()
n_firms_lost = n_firms_before - n_firms_after

print(f"Removed: {n_removed:,} documents")
print(f"Remaining: {len(df_clean):,} documents, {n_firms_after:,} unique firms")
print(f"Firms lost: {n_firms_lost:,}")
print()

# ============================================================================
# STEP 2: Apply 95th percentile cutoff
# ============================================================================

print("STEP 2: Apply 95th percentile cutoff")
print("-" * 80)

# Calculate 95th percentile
cutoff_95 = np.percentile(df_clean['char_count'], 95)

print(f"95th percentile cutoff: {cutoff_95:,.0f} characters")
print()

# Show char_count statistics
print(f"Character count statistics (before cutoff):")
print(f"  Mean: {df_clean['char_count'].mean():,.0f}")
print(f"  Median: {df_clean['char_count'].median():,.0f}")
print(f"  Std: {df_clean['char_count'].std():,.0f}")
print(f"  Min: {df_clean['char_count'].min():,.0f}")
print(f"  Max: {df_clean['char_count'].max():,.0f}")
print()

n_before = len(df_clean)
n_firms_before = df_clean['stock_code'].nunique()

df_clean = df_clean[df_clean['char_count'] <= cutoff_95]

n_removed = n_before - len(df_clean)
pct_removed = 100 * n_removed / n_before
n_firms_after = df_clean['stock_code'].nunique()
n_firms_lost = n_firms_before - n_firms_after

print(f"Removed: {n_removed:,} documents ({pct_removed:.1f}%)")
print(f"Remaining: {len(df_clean):,} documents, {n_firms_after:,} unique firms")
print(f"Firms lost: {n_firms_lost:,}")
print()

# ============================================================================
# STEP 3: Level-based deduplication
# ============================================================================

print("STEP 3: Level-based deduplication (prefer level=2)")
print("-" * 80)

# Check if level field exists
if 'level' not in df_clean.columns:
    df_clean['level'] = 1
    print("[WARNING] 'level' field missing, assuming level=1 for all documents")
else:
    # Show level distribution before
    level_dist_before = df_clean['level'].value_counts().sort_index()
    print(f"Level distribution before:")
    for level, count in level_dist_before.items():
        print(f"  level={level}: {count:,}")
    print()

n_before = len(df_clean)
n_firms_before = df_clean['stock_code'].nunique()

# Sort: prefer level=2 over level=1 for same rcept_no
df_clean = df_clean.sort_values(['rcept_no', 'level'], ascending=[True, False])
df_clean = df_clean.drop_duplicates(subset=['rcept_no'], keep='first')

n_removed = n_before - len(df_clean)
n_firms_after = df_clean['stock_code'].nunique()
n_firms_lost = n_firms_before - n_firms_after

# Show level distribution after
n_level2 = (df_clean['level'] == 2).sum()
n_level1 = (df_clean['level'] == 1).sum()
pct_level2 = 100 * n_level2 / len(df_clean) if len(df_clean) > 0 else 0

print(f"Removed: {n_removed:,} duplicate rcept_no (kept higher level)")
print(f"Remaining: {len(df_clean):,} documents, {n_firms_after:,} unique firms")
print(f"Firms lost: {n_firms_lost:,}")
print()
print(f"Level distribution after:")
print(f"  level=2: {n_level2:,} ({pct_level2:.1f}%)")
print(f"  level=1: {n_level1:,} ({100-pct_level2:.1f}%)")
print()

# ============================================================================
# STEP 4: Firm-year deduplication
# ============================================================================

print("STEP 4: Firm-year deduplication (keep latest rcept_dt)")
print("-" * 80)

# Check for duplicates before deduplication
duplicates = df_clean.groupby(['stock_code', 'year']).size()
n_duplicates = (duplicates > 1).sum()
total_duplicate_docs = (duplicates - 1).sum()

print(f"Duplicate firm-year combinations:")
print(f"  Firms with multiple documents: {n_duplicates:,}")
print(f"  Total duplicate documents: {total_duplicate_docs:,}")
print()

if n_duplicates > 0:
    print(f"Sample duplicates (top 5):")
    duplicate_pairs = duplicates[duplicates > 1].head(5)
    for (stock_code, year), count in duplicate_pairs.items():
        corp_name = df_clean[df_clean['stock_code'] == stock_code]['corp_name'].iloc[0]
        print(f"  {stock_code} ({corp_name}): {count} documents")
    print()

n_before = len(df_clean)
n_firms_before = df_clean['stock_code'].nunique()

# Sort by rcept_dt descending (latest first)
df_clean = df_clean.sort_values('rcept_dt', ascending=False)

# Drop duplicates, keeping first (latest)
df_clean = df_clean.drop_duplicates(subset=['stock_code', 'year'], keep='first')

n_removed = n_before - len(df_clean)
n_firms_after = df_clean['stock_code'].nunique()
n_firms_lost = n_firms_before - n_firms_after

print(f"Removed: {n_removed:,} duplicate documents")
print(f"Final: {len(df_clean):,} unique firm-years, {n_firms_after:,} unique firms")
print(f"Firms lost: {n_firms_lost:,}")
print()

# Sort by stock_code and year
df_clean = df_clean.sort_values(['stock_code', 'year']).reset_index(drop=True)

# ============================================================================
# Summary
# ============================================================================

print("=" * 80)
print("SUMMARY: DATA LOSS AT EACH STEP")
print("=" * 80)
print()

print(f"Step 0: Baseline (MongoDB)")
print(f"  Documents: {n_docs_baseline:,}")
print(f"  Unique firms: {n_firms_baseline:,}")
print()

# Calculate cumulative retention
retention_rate = 100 * len(df_clean) / n_docs_baseline
firm_retention_rate = 100 * df_clean['stock_code'].nunique() / n_firms_baseline

print(f"Final (after all filters)")
print(f"  Documents: {len(df_clean):,} ({retention_rate:.1f}% retention)")
print(f"  Unique firms: {df_clean['stock_code'].nunique():,} ({firm_retention_rate:.1f}% retention)")
print()

# ============================================================================
# Comparison with Phase 1 output
# ============================================================================

print("=" * 80)
print("COMPARISON WITH PHASE 1 OUTPUT")
print("=" * 80)
print()

# Load Phase 1 output
df_phase1 = pd.read_parquet('data/korean_texts/business_descriptions_clean.parquet')
df_phase1_2010 = df_phase1[df_phase1['year'] == str(YEAR)]

print(f"Phase 1 output for {YEAR}:")
print(f"  Documents: {len(df_phase1_2010):,}")
print(f"  Unique firms: {df_phase1_2010['stock_code'].nunique():,}")
print()

print(f"Our calculation for {YEAR}:")
print(f"  Documents: {len(df_clean):,}")
print(f"  Unique firms: {df_clean['stock_code'].nunique():,}")
print()

# Check match
docs_match = len(df_clean) == len(df_phase1_2010)
firms_match = df_clean['stock_code'].nunique() == df_phase1_2010['stock_code'].nunique()

print(f"Documents match: {'YES' if docs_match else 'NO'}")
print(f"Firms match: {'YES' if firms_match else 'NO'}")
print()

if not firms_match:
    # Find differences
    our_firms = set(df_clean['stock_code'].unique())
    phase1_firms = set(df_phase1_2010['stock_code'].unique())

    only_ours = our_firms - phase1_firms
    only_phase1 = phase1_firms - our_firms

    if len(only_ours) > 0:
        print(f"Firms in our calculation but NOT in Phase 1: {len(only_ours)}")
        print(f"  Sample: {list(only_ours)[:5]}")
        print()

    if len(only_phase1) > 0:
        print(f"Firms in Phase 1 but NOT in our calculation: {len(only_phase1)}")
        print(f"  Sample: {list(only_phase1)[:5]}")
        print()

# ============================================================================
# Final Statistics
# ============================================================================

print("=" * 80)
print("FINAL STATISTICS")
print("=" * 80)
print()

print(f"Character count statistics (final):")
print(f"  Mean: {df_clean['char_count'].mean():,.0f}")
print(f"  Median: {df_clean['char_count'].median():,.0f}")
print(f"  Std: {df_clean['char_count'].std():,.0f}")
print(f"  Min: {df_clean['char_count'].min():,.0f}")
print(f"  Max: {df_clean['char_count'].max():,.0f}")
print()

print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
