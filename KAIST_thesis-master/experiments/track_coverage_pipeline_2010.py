"""
Complete Coverage Tracking Pipeline for Year 2010

This script tracks coverage at every step from raw MongoDB through
Phase 1 cleaning and Phase 1.5 universe matching/filling.

Demonstrates the improved truncation method and validates against
check_text_coverage.py results.

Usage:
    poetry run python experiments/track_coverage_pipeline_2010.py
"""

from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from tnic.data_loader import MongoDBLoader
from alpha_excel2.core.facade import AlphaExcel

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

YEAR = 2010

# ============================================================================
# Reusable Coverage Checker Function
# ============================================================================

def calculate_coverage(df, year, universe_by_year, step_name):
    """
    Calculate and log coverage for a given step.

    Args:
        df: DataFrame with stock_code and year columns
        year: Year to check (int)
        universe_by_year: Dict[int, Set[str]] from alpha-excel
        step_name: Name of the current step (for logging)

    Returns:
        Dict with coverage stats
    """
    # Handle both string and int year types
    df_year = df[(df['year'] == year) | (df['year'] == str(year))]

    # Get unique firms in data for this year
    data_firms = set(df_year['stock_code'].unique())

    # Get universe firms for this year
    universe_firms = universe_by_year[year]

    # Calculate matches
    matched = data_firms & universe_firms
    data_only = data_firms - universe_firms  # KONEX firms
    universe_only = universe_firms - data_firms  # Missing firms

    # Calculate coverage
    coverage_pct = (len(matched) / len(universe_firms) * 100) if len(universe_firms) > 0 else 0

    # Log results
    print(f"\n{step_name}")
    print(f"  Data firms: {len(data_firms):,}")
    print(f"  Universe firms: {len(universe_firms):,}")
    print(f"  Matched: {len(matched):,}")
    print(f"  Coverage: {coverage_pct:.2f}%")
    print(f"  Data only (KONEX): {len(data_only):,}")
    print(f"  Universe only (missing): {len(universe_only):,}")

    return {
        'step': step_name,
        'data_firms': len(data_firms),
        'universe_firms': len(universe_firms),
        'matched': len(matched),
        'coverage_pct': coverage_pct,
        'data_only': len(data_only),
        'universe_only': len(universe_only)
    }

# ============================================================================
# MAIN PIPELINE
# ============================================================================

print("=" * 80)
print(f"COMPLETE COVERAGE TRACKING PIPELINE: YEAR {YEAR}")
print("=" * 80)
print()

# Store coverage stats for summary
coverage_stats = []

# ============================================================================
# STEP 0: Load Universe
# ============================================================================

print("STEP 0: Loading FnGuide Universe")
print("-" * 80)

ae_daily = AlphaExcel(
    start_time=f'{YEAR}-01-01',
    end_time=f'{YEAR}-12-31',
    universe_field=None,
    config_path='./config'
)

fd = ae_daily.field
adj_close_df = fd('fnguide_adj_close').to_df()

print(f"Loaded adj_close: {adj_close_df.shape} (dates x securities)")

# Count firms with >=1 valid price in the year
year_data = adj_close_df.loc[f'{YEAR}-01-01':f'{YEAR}-12-31']
firms_with_data = year_data.notna().any(axis=0)
firm_symbols_with_prefix = firms_with_data[firms_with_data].index.tolist()

# Normalize symbols (strip 'A' prefix)
firm_symbols = set()
for symbol in firm_symbols_with_prefix:
    if isinstance(symbol, str) and symbol.startswith('A'):
        firm_symbols.add(symbol[1:])
    else:
        firm_symbols.add(symbol)

universe_by_year = {YEAR: firm_symbols}

print(f"Universe {YEAR}: {len(firm_symbols):,} firms")
print()

# ============================================================================
# STEP 1: Raw MongoDB Data
# ============================================================================

print("=" * 80)
print("STEP 1: Raw MongoDB Data")
print("=" * 80)

with MongoDBLoader() as loader:
    df_step1 = loader.extract_business_descriptions(
        year_range=(YEAR, YEAR),
        section_codes=['020000', '020100'],
        report_types=['A001'],
        fields=['rcept_no', 'rcept_dt', 'year', 'corp_name', 'stock_code',
                'level', 'text', 'char_count']
    )

print(f"Total documents: {len(df_step1):,}")

stats = calculate_coverage(df_step1, YEAR, universe_by_year, "STEP 1: Raw MongoDB")
coverage_stats.append(stats)

# ============================================================================
# STEP 2: Remove Zero-Length Documents
# ============================================================================

print("=" * 80)
print("STEP 2: Remove Zero-Length Documents")
print("=" * 80)

n_before = len(df_step1)
df_step2 = df_step1[df_step1['char_count'] > 0].copy()
n_removed = n_before - len(df_step2)

print(f"Removed: {n_removed:,} documents")
print(f"Remaining: {len(df_step2):,} documents")

stats = calculate_coverage(df_step2, YEAR, universe_by_year, "STEP 2: After zero-length removal")
coverage_stats.append(stats)

# ============================================================================
# STEP 3: Truncate to 95th Percentile (NEW METHOD)
# ============================================================================

print("=" * 80)
print("STEP 3: Truncate to 95th Percentile (NEW METHOD)")
print("=" * 80)

# Calculate 95th percentile for this year
cutoff_95 = np.percentile(df_step2['char_count'], 95)

print(f"95th percentile cutoff: {cutoff_95:,.0f} characters")
print()

# Count documents to be truncated
n_to_truncate = (df_step2['char_count'] > cutoff_95).sum()
print(f"Documents to truncate: {n_to_truncate:,} ({100*n_to_truncate/len(df_step2):.1f}%)")
print()

# TRUNCATE (not exclude!)
df_step3 = df_step2.copy()
df_step3['text'] = df_step3['text'].str[:int(cutoff_95)]
df_step3['char_count'] = df_step3['text'].str.len()

print(f"Max char_count after truncation: {df_step3['char_count'].max():,.0f}")

stats = calculate_coverage(df_step3, YEAR, universe_by_year, "STEP 3: After truncation")
coverage_stats.append(stats)

# ============================================================================
# STEP 4: Level-Based Deduplication
# ============================================================================

print("=" * 80)
print("STEP 4: Level-Based Deduplication")
print("=" * 80)

n_before = len(df_step3)

# Sort: prefer level=2 over level=1
df_step4 = df_step3.sort_values(['rcept_no', 'level'], ascending=[True, False])
df_step4 = df_step4.drop_duplicates(subset=['rcept_no'], keep='first')

n_removed = n_before - len(df_step4)

print(f"Removed: {n_removed:,} duplicate rcept_no")
print(f"Remaining: {len(df_step4):,} documents")

stats = calculate_coverage(df_step4, YEAR, universe_by_year, "STEP 4: After level dedup")
coverage_stats.append(stats)

# ============================================================================
# STEP 5: Firm-Year Deduplication
# ============================================================================

print("=" * 80)
print("STEP 5: Firm-Year Deduplication")
print("=" * 80)

n_before = len(df_step4)

# Sort by rcept_dt descending (latest first)
df_step5 = df_step4.sort_values('rcept_dt', ascending=False)
df_step5 = df_step5.drop_duplicates(subset=['stock_code', 'year'], keep='first')

n_removed = n_before - len(df_step5)

print(f"Removed: {n_removed:,} duplicate firm-years")
print(f"Final Phase 1: {len(df_step5):,} unique firm-years")

stats = calculate_coverage(df_step5, YEAR, universe_by_year, "STEP 5: After firm-year dedup (END OF PHASE 1)")
coverage_stats.append(stats)

# ============================================================================
# STEP 6: LEFT JOIN onto Universe Index
# ============================================================================

print("=" * 80)
print("STEP 6: LEFT JOIN onto Universe Index (PHASE 1.5 START)")
print("=" * 80)

# Create full universe index
universe_firms_list = list(universe_by_year[YEAR])
universe_index = pd.DataFrame({
    'stock_code': universe_firms_list,
    'year': YEAR
})

print(f"Created universe index: {len(universe_index):,} firm-year slots")

# Ensure year types match
df_step5['year'] = df_step5['year'].astype(str)
universe_index['year'] = universe_index['year'].astype(str)

# LEFT JOIN Phase 1 data onto universe
df_step6 = universe_index.merge(
    df_step5[['stock_code', 'year', 'text', 'char_count', 'corp_name']],
    on=['stock_code', 'year'],
    how='left'
)

n_with_text = df_step6['text'].notna().sum()
n_without_text = df_step6['text'].isna().sum()

print(f"After LEFT JOIN:")
print(f"  Total rows: {len(df_step6):,}")
print(f"  Rows with text: {n_with_text:,}")
print(f"  Rows without text (NaN): {n_without_text:,}")

# Calculate coverage on rows WITH text
stats = calculate_coverage(df_step6[df_step6['text'].notna()], YEAR, universe_by_year, "STEP 6: After LEFT JOIN (firms with text)")
coverage_stats.append(stats)

# ============================================================================
# STEP 7: Forward Fill
# ============================================================================

print("=" * 80)
print("STEP 7: Forward Fill (by firm)")
print("=" * 80)

print("Note: For single year (2010), forward fill has no effect")
print("      (no previous year to fill from)")
print()

df_step7 = df_step6.copy()
df_step7 = df_step7.sort_values(['stock_code', 'year'])

# Forward fill (will not change anything for single year)
for col in ['text', 'char_count', 'corp_name']:
    df_step7[col] = df_step7.groupby('stock_code')[col].ffill()

n_with_text_after = df_step7['text'].notna().sum()
n_filled = n_with_text_after - n_with_text

print(f"Rows with text before: {n_with_text:,}")
print(f"Rows with text after: {n_with_text_after:,}")
print(f"Rows filled: {n_filled:,}")

stats = calculate_coverage(df_step7[df_step7['text'].notna()], YEAR, universe_by_year, "STEP 7: After forward fill")
coverage_stats.append(stats)

# ============================================================================
# STEP 8: Backfill
# ============================================================================

print("=" * 80)
print("STEP 8: Backfill (by firm)")
print("=" * 80)

print("Note: For single year (2010), backfill has no effect")
print("      (no future year to fill from)")
print()

n_before_backfill = df_step7['text'].notna().sum()

df_step8 = df_step7.copy()

# Backfill (will not change anything for single year)
for col in ['text', 'char_count', 'corp_name']:
    df_step8[col] = df_step8.groupby('stock_code')[col].bfill()

n_with_text_after = df_step8['text'].notna().sum()
n_filled = n_with_text_after - n_before_backfill

print(f"Rows with text before: {n_before_backfill:,}")
print(f"Rows with text after: {n_with_text_after:,}")
print(f"Rows filled: {n_filled:,}")

stats = calculate_coverage(df_step8[df_step8['text'].notna()], YEAR, universe_by_year, "STEP 8: After backfill")
coverage_stats.append(stats)

# ============================================================================
# STEP 9: Remove Never-Filed Firms
# ============================================================================

print("=" * 80)
print("STEP 9: Remove Never-Filed Firms (drop NaN)")
print("=" * 80)

n_before = len(df_step8)
n_with_text = df_step8['text'].notna().sum()

df_step9 = df_step8[df_step8['text'].notna()].copy()

n_dropped = n_before - len(df_step9)

print(f"Rows before: {n_before:,}")
print(f"Rows dropped (never filed): {n_dropped:,}")
print(f"Final rows: {len(df_step9):,}")

stats = calculate_coverage(df_step9, YEAR, universe_by_year, "STEP 9: Final (after removing never-filed)")
coverage_stats.append(stats)

# ============================================================================
# Summary Table
# ============================================================================

print("\n" + "=" * 80)
print("COVERAGE SUMMARY")
print("=" * 80)
print()

summary_df = pd.DataFrame(coverage_stats)

print(f"{'Step':<50} | Coverage | Matched | Missing")
print("-" * 80)
print(f"{'Universe (baseline)':<50} | {'100.0%':>8} | {len(universe_by_year[YEAR]):>7,} |       -")

for idx, row in summary_df.iterrows():
    step_name = row['step'].replace(f"STEP {idx+1}: ", "")
    print(f"{step_name:<50} | {row['coverage_pct']:>7.2f}% | {row['matched']:>7,} | {row['universe_only']:>7,}")

print()

# ============================================================================
# Validation
# ============================================================================

print("=" * 80)
print("VALIDATION")
print("=" * 80)
print()

print(f"Final coverage: {coverage_stats[-1]['coverage_pct']:.2f}%")
print(f"Final matched firms: {coverage_stats[-1]['matched']:,}")
print(f"Universe firms: {coverage_stats[-1]['universe_firms']:,}")
print()

print("Expected (from check_text_coverage.py):")
print(f"  Coverage: 94.92%")
print(f"  Matched: 1,720 firms")
print()

final_coverage = coverage_stats[-1]['coverage_pct']
final_matched = coverage_stats[-1]['matched']

if abs(final_coverage - 94.92) < 1.0 and final_matched >= 1700:
    print("[PASS] Coverage matches expected result!")
else:
    print("[WARNING] Coverage differs from expected")

print()
print("=" * 80)
print("PIPELINE COMPLETE")
print("=" * 80)
