"""
Compare Coverage: Raw vs Cleaned Text Data

This script compares the coverage of raw vs cleaned business descriptions
against the FnGuide universe to verify that the truncation method preserves
firm coverage while removing outlier noise.

Expected Results:
- Raw coverage: Should match MongoDB direct query (~95%)
- Cleaned coverage: Should be identical to raw coverage (100% firm retention)
- Document counts: Cleaned < Raw (due to deduplication)

Usage:
    poetry run python experiments/compare_raw_vs_clean_coverage.py
"""

from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from alpha_excel2.core.facade import AlphaExcel

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configuration
YEARS = [2010, 2011]
START_YEAR = min(YEARS)
END_YEAR = max(YEARS)

print("=" * 80)
print(f"COVERAGE COMPARISON: RAW vs CLEANED ({START_YEAR}-{END_YEAR})")
print("=" * 80)
print()

# ============================================================================
# Step 1: Load FnGuide Universe
# ============================================================================

print("Step 1: Loading FnGuide universe...")
print()

ae_daily = AlphaExcel(
    start_time=f'{START_YEAR}-01-01',
    end_time=f'{END_YEAR}-12-31',
    universe_field=None,
    config_path='./config'
)

fd = ae_daily.field
adj_close_df = fd('fnguide_adj_close').to_df()

print(f"  Loaded adj_close: {adj_close_df.shape} (dates x securities)")
print()

# ============================================================================
# Helper Functions
# ============================================================================

def normalize_symbol(symbol):
    """Remove 'A' prefix from FnGuide symbols"""
    if isinstance(symbol, str) and symbol.startswith('A'):
        return symbol[1:]
    return symbol

def get_universe_by_year(df, years):
    """Get universe firms for each year"""
    universe_by_year = {}

    for year in years:
        year_data = df.loc[f'{year}-01-01':f'{year}-12-31']
        firms_with_data = year_data.notna().any(axis=0)
        firm_symbols_with_prefix = firms_with_data[firms_with_data].index.tolist()

        # Normalize symbols
        firm_symbols = set()
        for symbol in firm_symbols_with_prefix:
            normalized = normalize_symbol(symbol)
            firm_symbols.add(normalized)

        universe_by_year[year] = firm_symbols
        print(f"  {year}: {len(firm_symbols):,} firms in universe")

    return universe_by_year

universe_by_year = get_universe_by_year(adj_close_df, YEARS)
print()

# ============================================================================
# Step 2: Load Raw Parquet
# ============================================================================

print("Step 2: Loading RAW parquet...")
print()

raw_path = Path("data/korean_texts/business_descriptions_raw.parquet")

if not raw_path.exists():
    print(f"  [ERROR] Raw file not found: {raw_path}")
    print("  Please run extraction first")
    exit(1)

df_raw = pd.read_parquet(raw_path)
print(f"  Loaded: {len(df_raw):,} documents")
print(f"  Unique firms: {df_raw['stock_code'].nunique():,}")
print(f"  Columns: {list(df_raw.columns)}")
print()

# ============================================================================
# Step 3: Load Cleaned Parquet
# ============================================================================

print("Step 3: Loading CLEANED parquet...")
print()

clean_path = Path("data/korean_texts/business_descriptions_clean.parquet")

if not clean_path.exists():
    print(f"  [ERROR] Cleaned file not found: {clean_path}")
    print("  Please run cleaning first")
    exit(1)

df_clean = pd.read_parquet(clean_path)
print(f"  Loaded: {len(df_clean):,} documents")
print(f"  Unique firms: {df_clean['stock_code'].nunique():,}")
print(f"  Columns: {list(df_clean.columns)}")
print()

# ============================================================================
# Step 4: Calculate Coverage for Raw Data
# ============================================================================

print("Step 4: Calculating RAW data coverage...")
print()

raw_coverage = {}
for year in YEARS:
    # Handle both string and int year types
    df_year = df_raw[(df_raw['year'] == year) | (df_raw['year'] == str(year))]

    # Get unique firms for this year
    data_firms = set(df_year['stock_code'].unique())
    universe_firms = universe_by_year[year]

    # Calculate matches
    matched = data_firms & universe_firms
    data_only = data_firms - universe_firms
    universe_only = universe_firms - data_firms

    # Calculate coverage
    coverage_pct = (len(matched) / len(universe_firms) * 100) if len(universe_firms) > 0 else 0

    raw_coverage[year] = {
        'data_firms': len(data_firms),
        'universe_firms': len(universe_firms),
        'matched': len(matched),
        'coverage_pct': coverage_pct,
        'data_only': len(data_only),
        'universe_only': len(universe_only)
    }

    print(f"  {year}:")
    print(f"    Documents: {len(df_year):,}")
    print(f"    Data firms: {len(data_firms):,}")
    print(f"    Universe firms: {len(universe_firms):,}")
    print(f"    Matched: {len(matched):,}")
    print(f"    Coverage: {coverage_pct:.2f}%")
    print(f"    Data only (KONEX): {len(data_only):,}")
    print(f"    Universe only (missing): {len(universe_only):,}")
    print()

# ============================================================================
# Step 5: Calculate Coverage for Cleaned Data
# ============================================================================

print("Step 5: Calculating CLEANED data coverage...")
print()

clean_coverage = {}
for year in YEARS:
    # Handle both string and int year types
    df_year = df_clean[(df_clean['year'] == year) | (df_clean['year'] == str(year))]

    # Get unique firms for this year
    data_firms = set(df_year['stock_code'].unique())
    universe_firms = universe_by_year[year]

    # Calculate matches
    matched = data_firms & universe_firms
    data_only = data_firms - universe_firms
    universe_only = universe_firms - data_firms

    # Calculate coverage
    coverage_pct = (len(matched) / len(universe_firms) * 100) if len(universe_firms) > 0 else 0

    clean_coverage[year] = {
        'data_firms': len(data_firms),
        'universe_firms': len(universe_firms),
        'matched': len(matched),
        'coverage_pct': coverage_pct,
        'data_only': len(data_only),
        'universe_only': len(universe_only)
    }

    print(f"  {year}:")
    print(f"    Documents: {len(df_year):,}")
    print(f"    Data firms: {len(data_firms):,}")
    print(f"    Universe firms: {len(universe_firms):,}")
    print(f"    Matched: {len(matched):,}")
    print(f"    Coverage: {coverage_pct:.2f}%")
    print(f"    Data only (KONEX): {len(data_only):,}")
    print(f"    Universe only (missing): {len(universe_only):,}")
    print()

# ============================================================================
# Step 6: Comparison Summary
# ============================================================================

print("=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)
print()

print(f"{'Year':<6} | {'Stage':<10} | {'Documents':>10} | {'Firms':>8} | {'Matched':>8} | {'Coverage':>10}")
print("-" * 80)

for year in YEARS:
    # Raw
    raw_docs = len(df_raw[(df_raw['year'] == year) | (df_raw['year'] == str(year))])
    print(f"{year:<6} | {'Raw':<10} | {raw_docs:>10,} | {raw_coverage[year]['data_firms']:>8,} | {raw_coverage[year]['matched']:>8,} | {raw_coverage[year]['coverage_pct']:>9.2f}%")

    # Cleaned
    clean_docs = len(df_clean[(df_clean['year'] == year) | (df_clean['year'] == str(year))])
    print(f"{year:<6} | {'Cleaned':<10} | {clean_docs:>10,} | {clean_coverage[year]['data_firms']:>8,} | {clean_coverage[year]['matched']:>8,} | {clean_coverage[year]['coverage_pct']:>9.2f}%")

    # Difference
    doc_diff = clean_docs - raw_docs
    firm_diff = clean_coverage[year]['data_firms'] - raw_coverage[year]['data_firms']
    coverage_diff = clean_coverage[year]['coverage_pct'] - raw_coverage[year]['coverage_pct']

    print(f"{year:<6} | {'Difference':<10} | {doc_diff:>10,} | {firm_diff:>8,} | {clean_coverage[year]['matched'] - raw_coverage[year]['matched']:>8,} | {coverage_diff:>9.2f}%")
    print()

# ============================================================================
# Step 7: Validation
# ============================================================================

print("=" * 80)
print("VALIDATION")
print("=" * 80)
print()

all_passed = True

for year in YEARS:
    print(f"{year}:")

    # Check 1: Coverage should be maintained
    coverage_diff = abs(clean_coverage[year]['coverage_pct'] - raw_coverage[year]['coverage_pct'])
    if coverage_diff < 0.1:  # Allow tiny floating point differences
        print(f"  [PASS] Coverage maintained: {raw_coverage[year]['coverage_pct']:.2f}% → {clean_coverage[year]['coverage_pct']:.2f}%")
    else:
        print(f"  [FAIL] Coverage changed: {raw_coverage[year]['coverage_pct']:.2f}% → {clean_coverage[year]['coverage_pct']:.2f}%")
        all_passed = False

    # Check 2: Firm count should be same or higher (after dedup)
    firm_diff = clean_coverage[year]['data_firms'] - raw_coverage[year]['data_firms']
    if firm_diff >= 0:
        print(f"  [PASS] Firms preserved: {raw_coverage[year]['data_firms']:,} → {clean_coverage[year]['data_firms']:,} ({firm_diff:+,})")
    else:
        print(f"  [FAIL] Firms lost: {raw_coverage[year]['data_firms']:,} → {clean_coverage[year]['data_firms']:,} ({firm_diff:+,})")
        all_passed = False

    # Check 3: Documents should decrease (due to deduplication)
    raw_docs = len(df_raw[(df_raw['year'] == year) | (df_raw['year'] == str(year))])
    clean_docs = len(df_clean[(df_clean['year'] == year) | (df_clean['year'] == str(year))])
    doc_diff = clean_docs - raw_docs

    if doc_diff <= 0:
        print(f"  [PASS] Documents reduced (dedup): {raw_docs:,} → {clean_docs:,} ({doc_diff:,})")
    else:
        print(f"  [WARNING] Documents increased: {raw_docs:,} → {clean_docs:,} ({doc_diff:+,})")

    print()

print("=" * 80)
if all_passed:
    print("[SUCCESS] All validation checks passed!")
    print("Truncation method successfully preserves firm coverage.")
else:
    print("[FAILED] Some validation checks failed.")
print("=" * 80)
print()
