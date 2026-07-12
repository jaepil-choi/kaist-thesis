"""
Calculate Year-by-Year Membership Pairs Fraction for FnGuide Industry Groups

This script calculates the fraction of membership pairs for FnGuide Industry Group 27
classification (Korean equivalent of SIC-3) to use as calibration targets for TNIC
threshold following Hoberg & Phillips (2016) methodology.

Citation:
    Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and
    endogenous product differentiation. Journal of Political Economy, 124(5),
    1423-1465.

Membership Pairs Calculation (H&P 2016, Section II.C):
    - Membership pair = two firms in same industry
    - For group i with M_i firms: membership pairs = M_i(M_i-1)/2
    - Total membership pairs = Σ[M_i(M_i-1)/2] for all groups
    - Total possible pairs = N(N-1)/2 where N = total firms
    - Fraction = Total membership pairs / Total possible pairs

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


def calculate_membership_pairs_for_year(df_year, industry_col='FnGuide Industry Group 27'):
    """
    Calculate membership pairs fraction for a single year.

    Args:
        df_year: DataFrame with firms for this year
        industry_col: Column name for industry classification

    Returns:
        Dictionary with statistics
    """
    # Total firms
    N = len(df_year)

    if N == 0:
        return None

    # Total possible pairs
    total_possible_pairs = N * (N - 1) / 2

    # Group by industry
    industry_counts = df_year[industry_col].value_counts()

    # Calculate membership pairs per group
    membership_pairs_per_group = {}
    total_membership_pairs = 0

    for industry, M_i in industry_counts.items():
        pairs_in_group = M_i * (M_i - 1) / 2
        membership_pairs_per_group[industry] = {
            'firms': int(M_i),
            'pairs': int(pairs_in_group)
        }
        total_membership_pairs += pairs_in_group

    # Calculate fraction
    fraction = total_membership_pairs / total_possible_pairs if total_possible_pairs > 0 else 0

    return {
        'N': int(N),
        'num_groups': len(industry_counts),
        'total_membership_pairs': int(total_membership_pairs),
        'total_possible_pairs': int(total_possible_pairs),
        'fraction': float(fraction),
        'fraction_pct': float(fraction * 100),
        'group_details': membership_pairs_per_group
    }


def main():
    print("=" * 80)
    print("CALCULATE FNGUIDE MEMBERSHIP PAIRS FRACTION (YEAR-BY-YEAR)")
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

    # Check for null values in industry classification
    industry_col = 'FnGuide Industry Group 27'
    null_count = df_eoy[industry_col].isna().sum()
    if null_count > 0:
        print(f"\n[WARNING] {null_count} firms have null {industry_col}, will be excluded")
        df_eoy = df_eoy[df_eoy[industry_col].notna()].copy()

    # Calculate for each year
    print("\n" + "=" * 80)
    print("2. CALCULATING MEMBERSHIP PAIRS FRACTION BY YEAR")
    print("=" * 80)

    results = {}

    for year in sorted(df_eoy['year'].unique()):
        df_year = df_eoy[df_eoy['year'] == year].copy()

        # Remove duplicates (keep one row per firm per year)
        df_year = df_year.drop_duplicates(subset=['stock_code'], keep='first')

        result = calculate_membership_pairs_for_year(df_year, industry_col)

        if result:
            results[year] = result

    # Display results
    print("\n" + "=" * 80)
    print("3. RESULTS")
    print("=" * 80)

    print(f"\n{'Year':<6} {'Firms':<8} {'Groups':<8} {'Membership':<14} {'Total':<14} {'Fraction':<12}")
    print(f"{'':6} {'':8} {'':8} {'Pairs':<14} {'Pairs':<14} {'(%)':<12}")
    print("-" * 80)

    for year in sorted(results.keys()):
        r = results[year]
        print(f"{year:<6} {r['N']:<8,} {r['num_groups']:<8} "
              f"{r['total_membership_pairs']:<14,} {r['total_possible_pairs']:<14,} "
              f"{r['fraction_pct']:<12.4f}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("4. SUMMARY STATISTICS")
    print("=" * 80)

    fractions = [r['fraction_pct'] for r in results.values()]

    print(f"\nFraction of membership pairs across all years:")
    print(f"  Mean: {np.mean(fractions):.4f}%")
    print(f"  Median: {np.median(fractions):.4f}%")
    print(f"  Std: {np.std(fractions):.4f}%")
    print(f"  Min: {np.min(fractions):.4f}% (year {min(results.keys(), key=lambda y: results[y]['fraction_pct'])})")
    print(f"  Max: {np.max(fractions):.4f}% (year {max(results.keys(), key=lambda y: results[y]['fraction_pct'])})")

    print("\n[COMPARISON]")
    print(f"  H&P (2016) SIC-3 baseline: 2.05%")
    print(f"  Our FnGuide Industry Group 27 average: {np.mean(fractions):.4f}%")
    print(f"  Difference: {np.mean(fractions) - 2.05:+.4f}%")

    # Show top 5 largest groups for latest year
    print("\n" + "=" * 80)
    print("5. TOP GROUPS (LATEST YEAR)")
    print("=" * 80)

    latest_year = max(results.keys())
    latest_result = results[latest_year]

    print(f"\nYear {latest_year} - Top 5 largest industry groups:")
    print(f"{'Industry':<30} {'Firms':<8} {'Pairs':<10}")
    print("-" * 50)

    sorted_groups = sorted(latest_result['group_details'].items(),
                          key=lambda x: x[1]['firms'], reverse=True)

    for industry, stats in sorted_groups[:5]:
        print(f"{str(industry):<30} {stats['firms']:<8} {stats['pairs']:<10,}")

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)

    print("\n[NEXT STEP]")
    print("  Use these fractions to calibrate TNIC threshold in Phase 4.2")
    print("  For each year, find threshold where TNIC membership pairs ≈ FnGuide fraction")


if __name__ == "__main__":
    main()
