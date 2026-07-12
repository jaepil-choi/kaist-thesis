"""
Analyze All FnGuide Classification Levels

Shows statistics for each available FnGuide classification level to help
choose which one to use for TNIC calibration.

Author: Generated for KAIST Thesis
Date: 2025-10-29
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Set console encoding for Korean text and special characters on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Directories
DATA_DIR = project_root / "data"
FNGUIDE_DIR = DATA_DIR / "fnguide" / "processed"


def calculate_membership_fraction(df, industry_col):
    """Calculate membership pairs fraction for given classification."""
    N = len(df)
    if N == 0:
        return None

    total_possible_pairs = N * (N - 1) / 2
    industry_counts = df[industry_col].value_counts()

    total_membership_pairs = 0
    for M_i in industry_counts:
        pairs_in_group = M_i * (M_i - 1) / 2
        total_membership_pairs += pairs_in_group

    fraction = total_membership_pairs / total_possible_pairs if total_possible_pairs > 0 else 0
    return fraction


def analyze_classification_level(df, level_name, industry_col):
    """Analyze a single classification level."""
    print(f"\n{'=' * 80}")
    print(f"{level_name}")
    print(f"{'=' * 80}")

    # Remove nulls
    df_clean = df[df[industry_col].notna()].copy()
    null_count = len(df) - len(df_clean)

    if null_count > 0:
        print(f"[WARNING] {null_count} firms have null values, excluded from analysis")

    # Get unique categories
    categories = df_clean[industry_col].unique()
    n_categories = len(categories)

    # Category distribution
    category_counts = df_clean[industry_col].value_counts()

    # Membership pairs fraction
    membership_fraction = calculate_membership_fraction(df_clean, industry_col)

    print(f"\nNumber of categories: {n_categories}")
    print(f"Total firms: {len(df_clean):,}")
    print(f"Membership pairs fraction: {membership_fraction * 100:.4f}%")

    print(f"\nFirms per category:")
    print(f"  Mean: {category_counts.mean():.1f}")
    print(f"  Median: {category_counts.median():.1f}")
    print(f"  Std: {category_counts.std():.1f}")
    print(f"  Min: {category_counts.min()}")
    print(f"  Max: {category_counts.max()}")

    print(f"\nTop 5 largest categories:")
    for cat, count in category_counts.head().items():
        print(f"  {cat}: {count} firms")

    return {
        'level': level_name,
        'n_categories': n_categories,
        'n_firms': len(df_clean),
        'membership_fraction_pct': membership_fraction * 100,
        'mean_firms_per_cat': category_counts.mean(),
        'median_firms_per_cat': category_counts.median(),
    }


def main():
    print("=" * 80)
    print("FNGUIDE CLASSIFICATION LEVELS ANALYSIS")
    print("=" * 80)

    print("\nPurpose: Compare different FnGuide classification levels to choose")
    print("         appropriate baseline for TNIC calibration")

    # Load FnGuide data
    print("\n" + "=" * 80)
    print("LOADING DATA")
    print("=" * 80)

    fnguide_path = FNGUIDE_DIR / "dataguide_groups.parquet"
    print(f"\nLoading: {fnguide_path}")

    df = pd.read_parquet(fnguide_path)
    print(f"Loaded {len(df):,} rows")

    # Filter for latest year EOY data
    df['year'] = pd.to_datetime(df['date']).dt.year
    df['month'] = pd.to_datetime(df['date']).dt.month

    # Find latest year with December data
    df_dec = df[df['month'] == 12]
    latest_year = df_dec['year'].max()
    df_latest = df[(df['year'] == latest_year) & (df['month'] == 12)].copy()

    # Clean stock codes
    df_latest['stock_code'] = df_latest['symbol'].str.replace('A', '', regex=False)

    # Remove duplicates
    df_latest = df_latest.drop_duplicates(subset=['stock_code'], keep='first')

    print(f"Using latest year: {latest_year}")
    print(f"Unique firms: {len(df_latest):,}")

    # Classification levels to analyze
    levels = [
        ('FnGuide Sector (Broadest)', 'FnGuide Sector'),
        ('FnGuide Industry Group 27 (≈ SIC-3)', 'FnGuide Industry Group 27'),
        ('FnGuide Industry Group', 'FnGuide Industry Group'),
        ('FnGuide Industry (Finest)', 'FnGuide Industry'),
    ]

    # Analyze each level
    results = []
    for level_name, col_name in levels:
        if col_name in df_latest.columns:
            result = analyze_classification_level(df_latest, level_name, col_name)
            results.append(result)

    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)

    print(f"\n{'Level':<40} {'Categories':<12} {'Firms':<10} {'Membership %':<15}")
    print("-" * 80)

    for r in results:
        print(f"{r['level']:<40} {r['n_categories']:<12} {r['n_firms']:<10,} {r['membership_fraction_pct']:<15.4f}")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("\n1. For coarse industry definition (like SIC-2):")
    print("   → Use 'FnGuide Sector'")

    print("\n2. For standard industry definition (like SIC-3):")
    print("   → Use 'FnGuide Industry Group 27' (closest to H&P 2016)")

    print("\n3. For fine-grained industry definition:")
    print("   → Use 'FnGuide Industry'")

    print("\n[COMPARISON WITH H&P 2016]")
    print("  H&P SIC-3 membership fraction: 2.05%")

    # Find which level is closest to 2.05%
    hp_baseline = 2.05
    differences = [(r, abs(r['membership_fraction_pct'] - hp_baseline)) for r in results]
    closest = min(differences, key=lambda x: x[1])

    print(f"  Closest match: {closest[0]['level']}")
    print(f"                 {closest[0]['membership_fraction_pct']:.4f}% (diff: {closest[1]:+.4f}%)")

    print("\n[NOTE] Korean market appears denser than US market at all levels")
    print("       This may reflect different industry structure or market size")


if __name__ == "__main__":
    main()
