"""
Check MongoDB Data Coverage for Years 2010-2011

This script retrieves business description data from MongoDB and shows
basic coverage statistics for the specified columns.

Usage:
    python experiments/check_mongodb_coverage.py
"""

import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from tnic.data_loader import MongoDBLoader

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def main():
    """Retrieve and analyze MongoDB data coverage for 2010-2011."""

    # Columns to retrieve
    fields = [
        'year',
        'corp_name',
        'stock_code',
        'corp_code',
        'level',
        'section_code'
    ]

    print("=" * 70)
    print("MongoDB Data Coverage Check: 2010-2011")
    print("=" * 70)
    print()

    # Initialize MongoDB loader
    with MongoDBLoader() as loader:

        # Retrieve data for 2010 and 2011
        print("Retrieving data from MongoDB...")
        df = loader.extract_business_descriptions(
            year_range=(2010, 2011),
            section_codes=None,  # Get all section codes
            report_types=None,   # Get all report types
            fields=fields
        )

    print(f"\nTotal documents retrieved: {len(df):,}")
    print(f"DataFrame shape: {df.shape}")
    print()

    # Show basic statistics
    print("-" * 70)
    print("Data Summary")
    print("-" * 70)
    print(f"\nColumns: {list(df.columns)}")
    print()

    # CRITICAL: Count unique firms by year (deduplicating by year + stock_code)
    print("=" * 70)
    print("UNIQUE FIRM COVERAGE BY YEAR (year + stock_code)")
    print("=" * 70)
    print()

    # Get unique firm-year combinations
    unique_firm_years = df.drop_duplicates(subset=['year', 'stock_code'])

    print(f"Total unique firm-years: {len(unique_firm_years):,}")
    print()

    # Count by year
    print("Unique firms per year:")
    for year in sorted(df['year'].unique()):
        unique_firms = df[df['year'] == year].drop_duplicates(subset=['year', 'stock_code'])
        print(f"  {year}: {len(unique_firms):,} unique firms")
    print()

    # Year distribution (all documents, not deduplicated)
    print("-" * 70)
    print("All documents by year (before deduplication):")
    year_counts = df['year'].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"  {year}: {count:,} documents")
    print()

    # Overall unique firms (across all years)
    print(f"Total unique stock_codes (across all years): {df['stock_code'].nunique():,}")
    print(f"Total unique corp_codes (across all years): {df['corp_code'].nunique():,}")
    print()

    # Section code distribution
    print("Section code distribution:")
    section_counts = df['section_code'].value_counts().sort_index()
    for section, count in section_counts.items():
        print(f"  {section}: {count:,} documents")
    print()

    # Level distribution
    print("Level distribution:")
    level_counts = df['level'].value_counts().sort_index()
    for level, count in level_counts.items():
        print(f"  Level {level}: {count:,} documents")
    print()

    # Check for missing values
    print("Missing values:")
    missing = df.isnull().sum()
    for col in fields:
        if col in df.columns:
            print(f"  {col}: {missing[col]:,} ({missing[col]/len(df)*100:.1f}%)")
    print()

    # Show sample data
    print("-" * 70)
    print("Sample Data (first 10 rows)")
    print("-" * 70)
    print(df.head(10).to_string())
    print()

    # Year-by-year breakdown by stock_code
    print("-" * 70)
    print("Detailed Breakdown by Year")
    print("-" * 70)
    for year in sorted(df['year'].unique()):
        df_year = df[df['year'] == year]
        unique_firms = df_year['stock_code'].nunique()
        total_docs = len(df_year)

        # Count unique firm-years (this is what TNIC pipeline will use)
        unique_firm_year = df_year.drop_duplicates(subset=['year', 'stock_code'])

        print(f"\n{year}:")
        print(f"  Unique firms (what TNIC will use): {len(unique_firm_year):,}")
        print(f"  Total documents (before dedup): {total_docs:,}")
        print(f"  Avg docs per firm: {total_docs/unique_firms:.1f}")
        print(f"  Multiple documents per firm: {total_docs - len(unique_firm_year):,} duplicates")

    print()
    print("=" * 70)
    print("Analysis complete!")
    print("=" * 70)

    return df


if __name__ == "__main__":
    df = main()
