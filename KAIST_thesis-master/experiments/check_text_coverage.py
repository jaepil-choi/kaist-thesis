"""
Calculate Text Data Coverage Against FnGuide Universe

This script calculates what percentage of the FnGuide trading universe
has business description text data from MongoDB for each year.

Coverage = (Matched firms with text) / (FnGuide universe) × 100%

Usage:
    poetry run python experiments/check_text_coverage.py

Configuration:
    - YEARS: List of years to analyze (default: [2010, 2011])
    - Can be extended to [2010, 2011, ..., 2024]
"""

import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from alpha_excel2.core.facade import AlphaExcel
from tnic.data_loader import MongoDBLoader

# ============================================================================
# Configuration
# ============================================================================

# Years to analyze (easily customizable)
YEARS = [2010, 2011]

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Determine date range from YEARS
START_YEAR = min(YEARS)
END_YEAR = max(YEARS)

print("=" * 80)
print(f"TEXT DATA COVERAGE: {START_YEAR}-{END_YEAR}")
print("=" * 80)
print(f"Analyzing years: {YEARS}")
print()

# ============================================================================
# Step 1: Load FnGuide Universe (Daily Adjusted Close Prices)
# ============================================================================

print("Step 1: Loading FnGuide universe (fnguide_adj_close)...")

ae_daily = AlphaExcel(
    start_time=f'{START_YEAR}-01-01',
    end_time=f'{END_YEAR}-12-31',
    universe_field=None,  # No universe masking
    config_path='./config'
)

fd = ae_daily.field
adj_close_alpha = fd('fnguide_adj_close')
adj_close_df = adj_close_alpha.to_df()

print(f"  Loaded adj_close: {adj_close_df.shape} (dates × securities)")
print(f"  Date range: {adj_close_df.index[0]} to {adj_close_df.index[-1]}")
print(f"  Total securities: {adj_close_df.shape[1]}")
print()

# ============================================================================
# Helper Functions
# ============================================================================

def normalize_fnguide_symbol(symbol):
    """Remove 'A' prefix from FnGuide symbols"""
    if isinstance(symbol, str) and symbol.startswith('A'):
        return symbol[1:]
    return symbol

def count_universe_firms_by_year(df, year):
    """
    Count firms with at least 1 valid adj_close value in the year.

    Returns:
        n_firms (int): Number of firms in universe
        firm_symbols (list): List of firm symbols in universe
    """
    year_data = df.loc[f'{year}-01-01':f'{year}-12-31']

    # Count columns with at least one non-NaN value
    firms_with_data = year_data.notna().any(axis=0)
    firm_symbols = firms_with_data[firms_with_data].index.tolist()

    return len(firm_symbols), firm_symbols


# ============================================================================
# Step 2: Count Universe Firms by Year
# ============================================================================

print("Step 2: Counting FnGuide universe firms by year...")
print("  (Universe = firms with ≥1 valid adj_close in the year)")
print()

# Count universe firms for each year
universe_data = {}
for year in YEARS:
    n_firms, firm_symbols = count_universe_firms_by_year(adj_close_df, year)
    universe_data[year] = {
        'count': n_firms,
        'symbols': firm_symbols,
        'symbols_normalized': set([normalize_fnguide_symbol(s) for s in firm_symbols])
    }
    print(f"  {year}: {n_firms:,} firms in FnGuide universe")

print()

# ============================================================================
# Step 3: Load MongoDB Text Data
# ============================================================================

print("Step 3: Loading MongoDB text data...")

with MongoDBLoader() as loader:
    df_mongo = loader.extract_business_descriptions(
        year_range=(START_YEAR, END_YEAR),
        section_codes=['020000', '020100'],
        report_types=['A001'],
        fields=['year', 'stock_code', 'corp_name']
    )

print(f"  Total MongoDB documents: {len(df_mongo):,}")
print()

# ============================================================================
# Step 4: Deduplicate MongoDB by (year, stock_code)
# ============================================================================

print("Step 4: Deduplicating MongoDB data by (year, stock_code)...")

df_mongo_unique = df_mongo.drop_duplicates(subset=['year', 'stock_code'])

print(f"  Unique firm-years: {len(df_mongo_unique):,}")
print()

# Count by year and store in dictionary
mongo_data = {}
for year in YEARS:
    mongo_year = df_mongo_unique[df_mongo_unique['year'] == str(year)]
    mongo_data[year] = {
        'count': len(mongo_year),
        'symbols': set(mongo_year['stock_code'].unique())
    }
    print(f"  {year}: {len(mongo_year):,} unique firms with text")

print()

# ============================================================================
# Step 5: Match and Calculate Coverage
# ============================================================================

print("Step 5: Matching MongoDB text data to FnGuide universe...")
print("  Symbol normalization: FnGuide A005930 → 005930")
print("  MongoDB symbols already in 6-digit format")
print()

# Perform matching for each year
matching_results = {}
for year in YEARS:
    universe_normalized = universe_data[year]['symbols_normalized']
    mongo_symbols = mongo_data[year]['symbols']

    # Calculate matches
    matched = universe_normalized & mongo_symbols
    mongo_only = mongo_symbols - universe_normalized
    fnguide_only = universe_normalized - mongo_symbols

    # Calculate coverage
    universe_count = universe_data[year]['count']
    coverage = (len(matched) / universe_count * 100) if universe_count > 0 else 0

    matching_results[year] = {
        'matched': matched,
        'mongo_only': mongo_only,
        'fnguide_only': fnguide_only,
        'coverage': coverage
    }

    print(f"  {year}: {len(matched):,} matched / {universe_count:,} universe = {coverage:.2f}%")

print()

# ============================================================================
# Step 6: Display Summary Table
# ============================================================================

print("=" * 80)
print("SUMMARY TABLE")
print("=" * 80)
print()

results = []
for year in YEARS:
    results.append({
        'Year': year,
        'FnGuide_Universe': universe_data[year]['count'],
        'MongoDB_Text': mongo_data[year]['count'],
        'Matched': len(matching_results[year]['matched']),
        'Coverage_%': f"{matching_results[year]['coverage']:.2f}%"
    })

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))
print()

# ============================================================================
# Step 7: Load Market Cap for Significance Analysis
# ============================================================================

print("Step 7: Loading market cap data to assess significance of missing firms...")
print()

market_cap_alpha = fd('fnguide_market_cap')
market_cap_df = market_cap_alpha.to_df()

print(f"  Loaded market_cap: {market_cap_df.shape} (dates × securities)")
print()

# ============================================================================
# Step 8: Unmatched Diagnostics with Market Cap Analysis
# ============================================================================

print("=" * 80)
print("UNMATCHED DIAGNOSTICS")
print("=" * 80)
print()

# Create stock_code to corp_name mapping from MongoDB data
stock_name_map = df_mongo_unique.set_index('stock_code')['corp_name'].to_dict()

for year in YEARS:
    print(f"{year}:")

    # MongoDB firms not in FnGuide (KONEX firms)
    mongo_only = matching_results[year]['mongo_only']
    print(f"  MongoDB firms NOT in FnGuide: {len(mongo_only):,} firms")
    print(f"    (These are likely KONEX firms excluded from FnGuide universe)")
    if len(mongo_only) > 0:
        sample_mongo_only = sorted(list(mongo_only))[:20]
        print(f"    Sample (first 20): {sample_mongo_only}")
    print()

    # FnGuide firms without text - analyze market cap significance
    fnguide_only = matching_results[year]['fnguide_only']
    print(f"  FnGuide firms WITHOUT text: {len(fnguide_only):,} firms")
    print(f"    (Analyzing significance by market cap...)")
    print()

    if len(fnguide_only) > 0:
        # Get market cap data for this year
        market_cap_year = market_cap_df.loc[f'{year}-01-01':f'{year}-12-31']

        # Build analysis for missing firms
        missing_firms = []
        for stock_code in fnguide_only:
            # Add 'A' prefix back to match FnGuide format
            fnguide_symbol = f'A{stock_code}'

            if fnguide_symbol in market_cap_year.columns:
                # Get average market cap for the year
                avg_market_cap = market_cap_year[fnguide_symbol].mean()

                # Get stock name from MongoDB data (if available)
                corp_name = stock_name_map.get(stock_code, 'N/A')

                missing_firms.append({
                    'stock_code': stock_code,
                    'corp_name': corp_name,
                    'fnguide_symbol': fnguide_symbol,
                    'avg_market_cap_krw': round(avg_market_cap, 1)
                })

        # Create DataFrame and sort by market cap
        missing_df = pd.DataFrame(missing_firms)
        missing_df = missing_df.sort_values('avg_market_cap_krw', ascending=False)

        # Save to CSV
        output_path = Path(f'experiments/missing_firms_{year}.csv')
        missing_df.to_csv(output_path, index=False)
        print(f"    Saved detailed list to: {output_path}")

        # Show summary statistics
        total_market_cap_missing = missing_df['avg_market_cap_krw'].sum()
        total_market_cap_all = market_cap_year.mean().sum()
        pct_market_cap = (total_market_cap_missing / total_market_cap_all * 100) if total_market_cap_all > 0 else 0

        print(f"    Total market cap of missing firms: {total_market_cap_missing:,.1f} KRW")
        print(f"    As % of total universe market cap: {pct_market_cap:.1f}%")
        print(f"    Top 5 missing firms by market cap:")
        for idx, row in missing_df.head(5).iterrows():
            print(f"      {row['stock_code']} ({row['corp_name']}): {row['avg_market_cap_krw']:,.1f} KRW")

    print()

# ============================================================================
# Step 9: Sample Matched Firms
# ============================================================================

print("=" * 80)
print("SAMPLE MATCHED FIRMS")
print("=" * 80)
print()

for year in YEARS:
    matched = matching_results[year]['matched']
    print(f"{year} (first 10 matched firms):")
    if len(matched) > 0:
        sample_matched = sorted(list(matched))[:10]
        print(f"  {sample_matched}")
    else:
        print("  No matched firms")
    print()

# ============================================================================
# Step 10: Summary
# ============================================================================

print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print()

for year in YEARS:
    matched = matching_results[year]['matched']
    universe_count = universe_data[year]['count']
    coverage = matching_results[year]['coverage']
    print(f"[OK] {year} Text Coverage: {coverage:.2f}% ({len(matched):,}/{universe_count:,} firms)")

print()
