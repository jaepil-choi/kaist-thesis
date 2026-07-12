"""
Experimental Script: Check FnGuide Data for Survivorship Bias

Purpose:
- Investigate if FnGuide monthly price data has survivorship bias
- Expected: Stock count should be relatively flat over time (with some growth)
- Problem: Universe coverage constantly increasing suggests survivorship bias

Data Source:
- data/fnguide/price_monthly/ (hive-partitioned by year/month)

Author: Claude Code
Date: 2025-11-11
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import duckdb

# ============================================================================
# Configuration
# ============================================================================

DATA_DIR = Path("data/fnguide/price_monthly")
START_DATE = "2010-01-01"
END_DATE = "2024-12-31"

print("=" * 80)
print("  FnGuide Monthly Price Data - Survivorship Bias Check")
print("=" * 80)
print()

# ============================================================================
# Step 1: Read Data Using DuckDB (Same as config/data.yaml)
# ============================================================================

print("Step 1: Reading FnGuide monthly price data...")
print(f"  Date range: {START_DATE} to {END_DATE}")
print(f"  Data directory: {DATA_DIR}")
print()

# Query matches the structure in config/data.yaml (monthly_adj_close)
query = f"""
    SELECT
      date,
      symbol,
      monthly_adj_close
    FROM read_parquet('data/fnguide/price_monthly/**/*.parquet', hive_partitioning=true)
    WHERE date >= '{START_DATE}'
      AND date <= '{END_DATE}'
    ORDER BY date, symbol
"""

print("Executing DuckDB query...")
df = duckdb.query(query).to_df()

print(f"\n[OK] Data loaded!")
print(f"     Total rows: {len(df):,}")
print(f"     Unique dates: {df['date'].nunique()}")
print(f"     Unique symbols: {df['symbol'].nunique()}")
print(f"     Date range: {df['date'].min()} to {df['date'].max()}")
print()

# ============================================================================
# Step 2: Display Sample Data
# ============================================================================

print("Step 2: Sample data (first 20 rows):")
print()
print(df.head(20))
print()

print("Sample data (last 20 rows):")
print()
print(df.tail(20))
print()

# ============================================================================
# Step 3: Check Data Quality
# ============================================================================

print("Step 3: Data quality checks...")
print()

# Check for NaN values
nan_count = df['monthly_adj_close'].isna().sum()
print(f"  NaN values in monthly_adj_close: {nan_count:,} ({nan_count/len(df)*100:.2f}%)")

# Check date frequency
date_counts = df.groupby('date').size()
print(f"\n  Date statistics:")
print(f"    Total dates: {len(date_counts)}")
print(f"    Min stocks per date: {date_counts.min()}")
print(f"    Max stocks per date: {date_counts.max()}")
print(f"    Mean stocks per date: {date_counts.mean():.1f}")
print(f"    Median stocks per date: {date_counts.median():.0f}")
print()

# ============================================================================
# Step 4: Analyze Stock Count Over Time (Survivorship Bias Test)
# ============================================================================

print("Step 4: Analyzing stock count over time (survivorship bias test)...")
print()

# Count stocks per date (non-NaN monthly_adj_close)
stock_count_by_date = df[df['monthly_adj_close'].notna()].groupby('date').size()

# Convert to DataFrame for easier analysis
stock_count_df = pd.DataFrame({
    'date': pd.to_datetime(stock_count_by_date.index),
    'stock_count': stock_count_by_date.values
})

print("Stock count statistics by year:")
print()

for year in range(2010, 2025):
    year_data = stock_count_df[stock_count_df['date'].dt.year == year]
    if len(year_data) > 0:
        print(f"  {year}: min={year_data['stock_count'].min():4d}, "
              f"max={year_data['stock_count'].max():4d}, "
              f"mean={year_data['stock_count'].mean():6.1f}, "
              f"months={len(year_data):2d}")

print()

# Calculate trend
first_year_avg = stock_count_df[stock_count_df['date'].dt.year == 2010]['stock_count'].mean()
last_year_avg = stock_count_df[stock_count_df['date'].dt.year == 2024]['stock_count'].mean()
growth_rate = (last_year_avg - first_year_avg) / first_year_avg * 100

print(f"Overall trend:")
print(f"  2010 average: {first_year_avg:.0f} stocks")
print(f"  2024 average: {last_year_avg:.0f} stocks")
print(f"  Growth: {growth_rate:.1f}%")
print()

# ============================================================================
# Step 5: Check for Delisted/Missing Stocks
# ============================================================================

print("Step 5: Checking for delisted stocks (stocks that disappear)...")
print()

# Get stocks that appear in early period but not in late period
early_period = df[df['date'] < '2012-01-01']['symbol'].unique()
late_period = df[df['date'] > '2022-01-01']['symbol'].unique()

early_only = set(early_period) - set(late_period)
late_only = set(late_period) - set(early_period)

print(f"  Stocks in 2010-2011 only (disappeared): {len(early_only)}")
print(f"  Stocks in 2022-2024 only (new): {len(late_only)}")
print()

if len(early_only) > 0:
    print(f"  Sample of disappeared stocks: {list(early_only)[:10]}")
    print()

# ============================================================================
# Step 6: Plot Stock Count Over Time
# ============================================================================

print("Step 6: Plotting stock count over time...")
print()

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Plot 1: Raw stock count
ax1 = axes[0]
ax1.plot(stock_count_df['date'], stock_count_df['stock_count'],
         linewidth=2, color='#2E86AB', alpha=0.7)
ax1.set_xlabel('Date', fontsize=12)
ax1.set_ylabel('Number of Stocks', fontsize=12)
ax1.set_title('Stock Count Over Time (Non-NaN monthly_adj_close)',
              fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.axhline(y=first_year_avg, color='red', linestyle='--', alpha=0.5, label=f'2010 avg ({first_year_avg:.0f})')
ax1.axhline(y=last_year_avg, color='green', linestyle='--', alpha=0.5, label=f'2024 avg ({last_year_avg:.0f})')
ax1.legend()

# Plot 2: Year-over-year comparison
ax2 = axes[1]
yearly_stats = []
for year in range(2010, 2025):
    year_data = stock_count_df[stock_count_df['date'].dt.year == year]
    if len(year_data) > 0:
        yearly_stats.append({
            'year': year,
            'mean': year_data['stock_count'].mean(),
            'min': year_data['stock_count'].min(),
            'max': year_data['stock_count'].max()
        })

yearly_df = pd.DataFrame(yearly_stats)
ax2.plot(yearly_df['year'], yearly_df['mean'], marker='o', linewidth=2,
         markersize=8, color='#2E86AB', label='Mean')
ax2.fill_between(yearly_df['year'], yearly_df['min'], yearly_df['max'],
                  alpha=0.3, color='#2E86AB', label='Min-Max Range')
ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Number of Stocks', fontsize=12)
ax2.set_title('Yearly Stock Count Statistics', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_xticks(yearly_df['year'])

plt.tight_layout()
plt.savefig('experiments/fnguide_survivorship_bias_check.png', dpi=150, bbox_inches='tight')
print("[OK] Plot saved to: experiments/fnguide_survivorship_bias_check.png")
plt.show()

# ============================================================================
# Step 7: Check Individual Stock Continuity
# ============================================================================

print("\nStep 7: Checking individual stock data continuity...")
print()

# Get date range for each stock
stock_ranges = df.groupby('symbol').agg({
    'date': ['min', 'max', 'count']
}).reset_index()
stock_ranges.columns = ['symbol', 'first_date', 'last_date', 'n_months']

# Convert to datetime
stock_ranges['first_date'] = pd.to_datetime(stock_ranges['first_date'])
stock_ranges['last_date'] = pd.to_datetime(stock_ranges['last_date'])

# Calculate expected months (should be ~180 for 2010-2024, 15 years)
stock_ranges['expected_months'] = (
    (stock_ranges['last_date'].dt.year - stock_ranges['first_date'].dt.year) * 12 +
    (stock_ranges['last_date'].dt.month - stock_ranges['first_date'].dt.month) + 1
)
stock_ranges['coverage_pct'] = stock_ranges['n_months'] / stock_ranges['expected_months'] * 100

# Stocks with gaps (coverage < 95%)
stocks_with_gaps = stock_ranges[stock_ranges['coverage_pct'] < 95.0]

print(f"  Total stocks: {len(stock_ranges)}")
print(f"  Stocks with data gaps (coverage < 95%): {len(stocks_with_gaps)} ({len(stocks_with_gaps)/len(stock_ranges)*100:.1f}%)")
print()

# Sample stocks with gaps
if len(stocks_with_gaps) > 0:
    print("  Sample stocks with gaps:")
    print(stocks_with_gaps.head(10)[['symbol', 'first_date', 'last_date', 'n_months', 'coverage_pct']])
    print()

# Stocks that recently appeared (started after 2020)
recent_stocks = stock_ranges[stock_ranges['first_date'] > '2020-01-01']
print(f"  Stocks that first appeared after 2020: {len(recent_stocks)}")

# Stocks that disappeared (ended before 2023)
disappeared_stocks = stock_ranges[stock_ranges['last_date'] < '2023-01-01']
print(f"  Stocks that disappeared before 2023: {len(disappeared_stocks)}")
print()

# ============================================================================
# Summary and Diagnosis
# ============================================================================

print("=" * 80)
print("  DIAGNOSIS: Survivorship Bias Assessment")
print("=" * 80)
print()

print(f"1. Stock count trend: {growth_rate:+.1f}% from 2010 to 2024")
if growth_rate > 30:
    print("   [WARNING] Very high growth suggests potential survivorship bias")
elif growth_rate > 15:
    print("   [CAUTION] Moderate growth, may indicate survivorship bias")
else:
    print("   [OK] Growth rate consistent with market expansion")
print()

print(f"2. Disappeared stocks: {len(disappeared_stocks)} ({len(disappeared_stocks)/len(stock_ranges)*100:.1f}%)")
if len(disappeared_stocks) < len(stock_ranges) * 0.05:
    print("   [WARNING] Very few delisted stocks suggests survivorship bias")
else:
    print("   [OK] Reasonable number of delisted stocks")
print()

print(f"3. Data gaps: {len(stocks_with_gaps)} stocks ({len(stocks_with_gaps)/len(stock_ranges)*100:.1f}%)")
if len(stocks_with_gaps) > len(stock_ranges) * 0.1:
    print("   [CAUTION] Many stocks have data gaps")
else:
    print("   [OK] Most stocks have continuous data")
print()

print("Conclusion:")
if growth_rate > 30 and len(disappeared_stocks) < len(stock_ranges) * 0.05:
    print("  [LIKELY SURVIVORSHIP BIAS] Data strongly suggests survivorship bias")
    print("     - Stock count increasing too much")
    print("     - Too few delisted/disappeared stocks")
    print()
    print("  Recommendation: Check ETL pipeline for handling delisted stocks")
elif growth_rate > 15:
    print("  [POSSIBLE SURVIVORSHIP BIAS] Some indicators suggest bias")
    print()
    print("  Recommendation: Investigate further, check delisting handling")
else:
    print("  [NO CLEAR SURVIVORSHIP BIAS] Data appears reasonable")
    print()
    print("  Note: Market growth can explain increasing stock counts")

print()
print("=" * 80)
print("  Analysis complete!")
print("=" * 80)
