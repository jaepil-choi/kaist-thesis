"""
Calculate Year-by-Year Membership Pairs Fraction for ALL FnGuide Classification Levels

Calculates membership pairs fraction for all available FnGuide classification levels
to help choose the most appropriate one for TNIC calibration.

Author: Generated for KAIST Thesis
Date: 2025-10-29
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Set console encoding for Korean text on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Directories
DATA_DIR = project_root / "data"
FNGUIDE_DIR = DATA_DIR / "fnguide" / "processed"


def calculate_membership_pairs_for_year(df_year, industry_col):
    """
    Calculate membership pairs fraction for a single year.

    Args:
        df_year: DataFrame with firms for this year
        industry_col: Column name for industry classification

    Returns:
        Dictionary with statistics
    """
    # Remove null values
    df_clean = df_year[df_year[industry_col].notna()].copy()

    # Total firms
    N = len(df_clean)

    if N == 0:
        return None

    # Total possible pairs
    total_possible_pairs = N * (N - 1) / 2

    # Group by industry
    industry_counts = df_clean[industry_col].value_counts()

    # Calculate membership pairs per group
    total_membership_pairs = 0

    for M_i in industry_counts:
        pairs_in_group = M_i * (M_i - 1) / 2
        total_membership_pairs += pairs_in_group

    # Calculate fraction
    fraction = total_membership_pairs / total_possible_pairs if total_possible_pairs > 0 else 0

    return {
        'N': int(N),
        'N_null': int(len(df_year) - N),
        'num_groups': len(industry_counts),
        'total_membership_pairs': int(total_membership_pairs),
        'total_possible_pairs': int(total_possible_pairs),
        'fraction': float(fraction),
        'fraction_pct': float(fraction * 100)
    }


def analyze_classification_level(df_eoy, level_name, industry_col):
    """
    Analyze a single classification level across all years.

    Returns:
        DataFrame with year-by-year results
    """
    print(f"\n{'=' * 80}")
    print(f"{level_name}")
    print(f"Column: {industry_col}")
    print(f"{'=' * 80}")

    results = {}

    for year in sorted(df_eoy['year'].unique()):
        df_year = df_eoy[df_eoy['year'] == year].copy()

        # Remove duplicates (keep one row per firm per year)
        df_year = df_year.drop_duplicates(subset=['stock_code'], keep='first')

        result = calculate_membership_pairs_for_year(df_year, industry_col)

        if result:
            results[year] = result

    # Display results
    print(f"\n{'Year':<6} {'Firms':<8} {'Null':<8} {'Groups':<8} {'Membership':<14} {'Total':<14} {'Fraction':<12}")
    print(f"{'':6} {'':8} {'':8} {'':8} {'Pairs':<14} {'Pairs':<14} {'(%)':<12}")
    print("-" * 90)

    for year in sorted(results.keys()):
        r = results[year]
        print(f"{year:<6} {r['N']:<8,} {r['N_null']:<8,} {r['num_groups']:<8} "
              f"{r['total_membership_pairs']:<14,} {r['total_possible_pairs']:<14,} "
              f"{r['fraction_pct']:<12.4f}")

    # Summary statistics
    fractions = [r['fraction_pct'] for r in results.values()]
    firms = [r['N'] for r in results.values()]
    nulls = [r['N_null'] for r in results.values()]

    print(f"\n{'SUMMARY STATISTICS'}")
    print("-" * 90)
    print(f"Fraction of membership pairs:")
    print(f"  Mean: {np.mean(fractions):.4f}%")
    print(f"  Median: {np.median(fractions):.4f}%")
    print(f"  Std: {np.std(fractions):.4f}%")
    print(f"  Min: {np.min(fractions):.4f}% (year {min(results.keys(), key=lambda y: results[y]['fraction_pct'])})")
    print(f"  Max: {np.max(fractions):.4f}% (year {max(results.keys(), key=lambda y: results[y]['fraction_pct'])})")

    print(f"\nFirms per year:")
    print(f"  Mean: {np.mean(firms):.0f}")
    print(f"  Range: {np.min(firms):,} to {np.max(firms):,}")

    if np.max(nulls) > 0:
        print(f"\n⚠️  NULL VALUES DETECTED:")
        print(f"  Mean null per year: {np.mean(nulls):.0f}")
        print(f"  Max null: {np.max(nulls):,} ({np.max(nulls) / (np.max(firms) + np.max(nulls)) * 100:.1f}% of firms)")

    return pd.DataFrame.from_dict(results, orient='index')


def main():
    print("=" * 80)
    print("CALCULATE MEMBERSHIP PAIRS FRACTION FOR ALL FNGUIDE LEVELS")
    print("=" * 80)

    print("\nMethodology (Hoberg & Phillips 2016, Section II.C):")
    print("  - Membership pair = two firms in same industry")
    print("  - Fraction = membership pairs / total possible pairs")
    print("  - Used to calibrate TNIC threshold")

    # Load FnGuide data
    print("\n" + "=" * 80)
    print("1. LOADING FNGUIDE DATA")
    print("=" * 80)

    fnguide_path = FNGUIDE_DIR / "dataguide_groups.parquet"
    print(f"\nLoading: {fnguide_path}")

    df = pd.read_parquet(fnguide_path)
    print(f"Loaded {len(df):,} rows")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique firms: {df['symbol'].nunique():,}")

    # Clean stock codes
    df['stock_code'] = df['symbol'].str.replace('A', '', regex=False)

    # Filter for end-of-year dates only (December)
    print("\n[FILTERING] End-of-year dates only (December)")
    df['year'] = pd.to_datetime(df['date']).dt.year
    df['month'] = pd.to_datetime(df['date']).dt.month

    # Keep only December dates (EOY)
    df_eoy = df[df['month'] == 12].copy()

    print(f"After EOY filter: {len(df_eoy):,} rows")
    print(f"Years available: {sorted(df_eoy['year'].unique())}")

    # Classification levels to analyze
    levels = [
        ('FnGuide Sector (Broadest)', 'FnGuide Sector'),
        ('FnGuide Industry Group 27 (≈ SIC-3)', 'FnGuide Industry Group 27'),
        ('FnGuide Industry Group (25 categories)', 'FnGuide Industry Group'),
        ('FnGuide Industry (Finest)', 'FnGuide Industry'),
    ]

    # Analyze each level
    print("\n" + "=" * 80)
    print("2. CALCULATING MEMBERSHIP PAIRS FRACTION BY LEVEL AND YEAR")
    print("=" * 80)

    all_results = {}

    for level_name, col_name in levels:
        if col_name in df_eoy.columns:
            df_results = analyze_classification_level(df_eoy, level_name, col_name)
            all_results[level_name] = df_results
        else:
            print(f"\n[WARNING] Column '{col_name}' not found in data, skipping")

    # Overall comparison
    print("\n" + "=" * 80)
    print("3. OVERALL COMPARISON")
    print("=" * 80)

    print(f"\n{'Level':<45} {'Avg %':<12} {'Range':<25} {'Coverage':<15}")
    print("-" * 100)

    for level_name, df_results in all_results.items():
        avg_pct = df_results['fraction_pct'].mean()
        min_pct = df_results['fraction_pct'].min()
        max_pct = df_results['fraction_pct'].max()

        # Check coverage (null counts)
        has_nulls = df_results['N_null'].max() > 0
        coverage_str = "INCOMPLETE ⚠️" if has_nulls else "Complete ✓"

        print(f"{level_name:<45} {avg_pct:<12.4f} {min_pct:.4f} - {max_pct:.4f}{'':5} {coverage_str:<15}")

    print("\n" + "=" * 80)
    print("4. COMPARISON WITH HOBERG & PHILLIPS (2016)")
    print("=" * 80)

    hp_baseline = 2.05
    print(f"\nH&P SIC-3 membership fraction: {hp_baseline}%")
    print(f"\nDistance from H&P baseline:")
    print("-" * 60)

    distances = []
    for level_name, df_results in all_results.items():
        avg_pct = df_results['fraction_pct'].mean()
        diff = avg_pct - hp_baseline
        distances.append((level_name, avg_pct, abs(diff)))
        print(f"{level_name:<45} {diff:+.4f}%")

    # Find closest
    closest = min(distances, key=lambda x: x[2])
    print(f"\n✓ Closest to H&P baseline: {closest[0]}")
    print(f"  ({closest[1]:.4f}% vs {hp_baseline}%, diff: {abs(closest[1] - hp_baseline):.4f}%)")

    print("\n" + "=" * 80)
    print("5. RECOMMENDATIONS")
    print("=" * 80)

    print("\nBased on the analysis:")
    print("\n1. If prioritizing H&P methodology replication:")
    print(f"   → Use: {closest[0]}")
    print(f"   → Closest to H&P's 2.05% baseline")

    print("\n2. If prioritizing complete coverage:")
    complete_coverage = [(name, df['N'].mean()) for name, df in all_results.items()
                        if df['N_null'].max() == 0]
    if complete_coverage:
        best_coverage = max(complete_coverage, key=lambda x: x[1])
        print(f"   → Use: {best_coverage[0]}")
        print(f"   → Covers all {best_coverage[1]:.0f} firms on average")

    print("\n3. If prioritizing granularity:")
    max_groups = [(name, df['num_groups'].iloc[0]) for name, df in all_results.items()]
    finest = max(max_groups, key=lambda x: x[1])
    print(f"   → Use: {finest[0]}")
    print(f"   → {finest[1]} distinct industry categories")

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

    print("\n[NEXT STEP]")
    print("  Choose a classification level and use its year-by-year fractions")
    print("  to calibrate TNIC threshold in Phase 4.2")


if __name__ == "__main__":
    main()
