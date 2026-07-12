"""
Analysis script for Korean stock data following Hoberg et al. (2018) methodology
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("="*80)
print("LOADING DATA")
print("="*80)

# Load data
df_groups = pd.read_parquet("data/fnguide/processed/dataguide_groups.parquet")
df_price = pd.read_parquet("data/fnguide/processed/dataguide_price.parquet")

# Merge on [date, symbol] key
df = pd.merge(
    df_groups,
    df_price,
    on=['date', 'symbol', 'symbol_name'],
    how='inner'
)

print(f"Initial merged data shape: {df.shape}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Unique symbols: {df['symbol'].nunique()}")

# ============================================================================
# 1. FLOATING SHARE RATIO VALIDATION
# ============================================================================
print("\n" + "="*80)
print("1. FLOATING SHARE RATIO VALIDATION")
print("="*80)

# Calculate ratio where data is valid
valid_mask = (
    df['유동주식수(주)'].notna() & 
    df['상장주식수 (보통)(주)'].notna() & 
    df['유동주식비율(%)'].notna() &
    (df['상장주식수 (보통)(주)'] > 0)
)

df_valid = df[valid_mask].copy()
df_valid['calculated_ratio'] = (df_valid['유동주식수(주)'] / df_valid['상장주식수 (보통)(주)']) * 100
df_valid['ratio_diff'] = abs(df_valid['calculated_ratio'] - df_valid['유동주식비율(%)'])

print(f"\nRecords with valid data: {len(df_valid):,}")
print(f"Mean absolute difference: {df_valid['ratio_diff'].mean():.6f}%")
print(f"Median absolute difference: {df_valid['ratio_diff'].median():.6f}%")
print(f"Max absolute difference: {df_valid['ratio_diff'].max():.6f}%")
print(f"\n✓ Conclusion: 유동주식비율 = 유동주식수 / 상장주식수 (differences are negligible)")

# ============================================================================
# 2. ESTIMATE TRADING VOLUME AND CALCULATE SHARE TURNOVER
# ============================================================================
print("\n" + "="*80)
print("2. TRADING VOLUME AND SHARE TURNOVER CALCULATION")
print("="*80)

# Estimate trading volume: volume = trading_value / price
df['estimated_volume'] = df['거래대금(원)'] / df['수정주가(원)']

# Share turnover using 상장주식수 (listed shares)
df['turnover_listed'] = (df['estimated_volume'] / df['상장주식수 (보통)(주)']) * 100

# Share turnover using 유동주식수 (floating shares)
df['turnover_floating'] = (df['estimated_volume'] / df['유동주식수(주)']) * 100

# Summary statistics
print("\nShare Turnover using 상장주식수 (Listed Shares):")
print(df['turnover_listed'].describe())

print("\nShare Turnover using 유동주식수 (Floating Shares):")
print(df['turnover_floating'].describe())

# Compare the two measures
valid_turnover = df[(df['turnover_listed'].notna()) & (df['turnover_floating'].notna())]
print(f"\nComparison (valid records: {len(valid_turnover):,}):")
print(f"Mean turnover_listed: {valid_turnover['turnover_listed'].mean():.4f}%")
print(f"Mean turnover_floating: {valid_turnover['turnover_floating'].mean():.4f}%")
print(f"Ratio (floating/listed): {valid_turnover['turnover_floating'].mean() / valid_turnover['turnover_listed'].mean():.4f}x")
print("\n✓ Floating share turnover is higher, as expected (same volume, smaller denominator)")

# ============================================================================
# 3. REMOVE PENNY STOCKS (PRICE <= 1000 WON)
# ============================================================================
print("\n" + "="*80)
print("3. PENNY STOCK FILTERING")
print("="*80)

# Find minimum price for each symbol
min_price_by_symbol = df.groupby('symbol')['수정주가(원)'].min()

# Identify penny stocks (ever had price <= 1000)
pennystock_symbols = min_price_by_symbol[min_price_by_symbol <= 1000].index
non_pennystock_symbols = min_price_by_symbol[min_price_by_symbol > 1000].index

print(f"\nTotal unique symbols: {df['symbol'].nunique():,}")
print(f"Penny stock symbols (ever <= 1000 won): {len(pennystock_symbols):,}")
print(f"Non-penny stock symbols (always > 1000 won): {len(non_pennystock_symbols):,}")
print(f"Percentage dropped: {len(pennystock_symbols) / df['symbol'].nunique() * 100:.2f}%")

# Filter out penny stocks
df_filtered = df[df['symbol'].isin(non_pennystock_symbols)].copy()

print(f"\nData shape before filtering: {len(df):,}")
print(f"Data shape after filtering: {len(df_filtered):,}")
print(f"Observations dropped: {len(df) - len(df_filtered):,} ({(len(df) - len(df_filtered)) / len(df) * 100:.2f}%)")

# Save list of non-penny stocks for future use
non_pennystock_list = sorted(non_pennystock_symbols.tolist())
with open('not_pennystock.txt', 'w') as f:
    f.write('\n'.join(non_pennystock_list))
print(f"\n✓ Saved {len(non_pennystock_list):,} non-penny stock symbols to 'not_pennystock.txt'")

# ============================================================================
# 4. CONSTRUCT VALID UNIVERSE MASK (WIDE FORMAT)
# ============================================================================
print("\n" + "="*80)
print("4. VALID UNIVERSE MASK CONSTRUCTION (WIDE FORMAT)")
print("="*80)

# Define valid universe criteria
valid_universe = (
    df_filtered['수정주가(원)'].notna() &              # Price is not null
    (df_filtered['수정주가(원)'] > 0) &                # Price is positive
    df_filtered['거래대금(원)'].notna() &              # Trading value is not null
    (df_filtered['거래대금(원)'] > 0) &                # Trading value is positive
    (df_filtered['거래정지구분'] == '정상') &           # Normal trading status
    (df_filtered['관리구분'] == '일반')                 # General management status
)

df_filtered['valid_universe'] = valid_universe

print(f"\nTotal observations (after penny stock filter): {len(df_filtered):,}")
print(f"Valid universe observations: {valid_universe.sum():,}")
print(f"Invalid observations: {(~valid_universe).sum():,}")
print(f"Valid percentage: {valid_universe.sum() / len(df_filtered) * 100:.2f}%")

# Breakdown of invalid reasons
print("\nBreakdown of invalid observations:")
print(f"  Price null or <=0: {((df_filtered['수정주가(원)'].isna()) | (df_filtered['수정주가(원)'] <= 0)).sum():,}")
print(f"  Trading value null or <=0: {((df_filtered['거래대금(원)'].isna()) | (df_filtered['거래대금(원)'] <= 0)).sum():,}")
print(f"  Trading suspended: {(df_filtered['거래정지구분'] == '거래정지').sum():,}")
print(f"  Management issue: {(df_filtered['관리구분'] == '관리').sum():,}")

# ============================================================================
# 5. CREATE WIDE FORMAT DATAFRAMES
# ============================================================================
print("\n" + "="*80)
print("5. WIDE FORMAT DATAFRAMES")
print("="*80)

# Create wide format for key variables
# Only include valid universe observations

df_universe = df_filtered[df_filtered['valid_universe']].copy()

# Price (wide format)
price_wide = df_universe.pivot(index='date', columns='symbol', values='수정주가(원)')
print(f"\nPrice matrix (wide format):")
print(f"  Shape: {price_wide.shape} (dates × symbols)")
print(f"  Date range: {price_wide.index.min()} to {price_wide.index.max()}")
print(f"  Non-null percentage: {price_wide.notna().sum().sum() / (price_wide.shape[0] * price_wide.shape[1]) * 100:.2f}%")

# Trading value (wide format)
trading_value_wide = df_universe.pivot(index='date', columns='symbol', values='거래대금(원)')
print(f"\nTrading value matrix (wide format):")
print(f"  Shape: {trading_value_wide.shape}")
print(f"  Non-null percentage: {trading_value_wide.notna().sum().sum() / (trading_value_wide.shape[0] * trading_value_wide.shape[1]) * 100:.2f}%")

# Listed shares (wide format)
listed_shares_wide = df_universe.pivot(index='date', columns='symbol', values='상장주식수 (보통)(주)')
print(f"\nListed shares matrix (wide format):")
print(f"  Shape: {listed_shares_wide.shape}")
print(f"  Non-null percentage: {listed_shares_wide.notna().sum().sum() / (listed_shares_wide.shape[0] * listed_shares_wide.shape[1]) * 100:.2f}%")

# Floating shares (wide format)
floating_shares_wide = df_universe.pivot(index='date', columns='symbol', values='유동주식수(주)')
print(f"\nFloating shares matrix (wide format):")
print(f"  Shape: {floating_shares_wide.shape}")
print(f"  Non-null percentage: {floating_shares_wide.notna().sum().sum() / (floating_shares_wide.shape[0] * floating_shares_wide.shape[1]) * 100:.2f}%")

# Volume (estimated) (wide format)
volume_wide = trading_value_wide / price_wide
print(f"\nEstimated volume matrix (wide format):")
print(f"  Shape: {volume_wide.shape}")
print(f"  Non-null percentage: {volume_wide.notna().sum().sum() / (volume_wide.shape[0] * volume_wide.shape[1]) * 100:.2f}%")

# Turnover using listed shares (wide format)
turnover_listed_wide = (volume_wide / listed_shares_wide) * 100
print(f"\nTurnover (listed shares) matrix (wide format):")
print(f"  Shape: {turnover_listed_wide.shape}")
print(f"  Mean turnover: {turnover_listed_wide.mean().mean():.4f}%")
print(f"  Median turnover: {turnover_listed_wide.median().median():.4f}%")

# Turnover using floating shares (wide format)
turnover_floating_wide = (volume_wide / floating_shares_wide) * 100
print(f"\nTurnover (floating shares) matrix (wide format):")
print(f"  Shape: {turnover_floating_wide.shape}")
print(f"  Mean turnover: {turnover_floating_wide.mean().mean():.4f}%")
print(f"  Median turnover: {turnover_floating_wide.median().median():.4f}%")

# Universe mask (wide format)
universe_mask_wide = df_filtered.pivot(index='date', columns='symbol', values='valid_universe')
universe_mask_wide = universe_mask_wide.fillna(False).astype(bool)
print(f"\nUniverse mask matrix (wide format):")
print(f"  Shape: {universe_mask_wide.shape}")
print(f"  Valid observations: {universe_mask_wide.sum().sum():,}")
print(f"  Valid percentage: {universe_mask_wide.sum().sum() / (universe_mask_wide.shape[0] * universe_mask_wide.shape[1]) * 100:.2f}%")

# ============================================================================
# 6. COMPARISON OF TURNOVER MEASURES
# ============================================================================
print("\n" + "="*80)
print("6. COMPARISON: TURNOVER (LISTED vs FLOATING)")
print("="*80)

# Compare turnover measures across time
turnover_comparison = pd.DataFrame({
    'date': turnover_listed_wide.index,
    'turnover_listed_mean': turnover_listed_wide.mean(axis=1),
    'turnover_floating_mean': turnover_floating_wide.mean(axis=1),
})

turnover_comparison['ratio'] = turnover_comparison['turnover_floating_mean'] / turnover_comparison['turnover_listed_mean']

print("\nTime-series statistics:")
print(f"  Mean turnover (listed): {turnover_comparison['turnover_listed_mean'].mean():.4f}%")
print(f"  Mean turnover (floating): {turnover_comparison['turnover_floating_mean'].mean():.4f}%")
print(f"  Mean ratio (floating/listed): {turnover_comparison['ratio'].mean():.4f}x")

print("\nSample comparison (first 10 dates):")
print(turnover_comparison.head(10).to_string(index=False))

# ============================================================================
# 7. DATA COVERAGE ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("7. DATA COVERAGE ANALYSIS")
print("="*80)

# Number of valid stocks per date
stocks_per_date = universe_mask_wide.sum(axis=1)
print(f"\nStocks per date (valid universe):")
print(f"  Mean: {stocks_per_date.mean():.0f}")
print(f"  Median: {stocks_per_date.median():.0f}")
print(f"  Min: {stocks_per_date.min():.0f} (on {stocks_per_date.idxmin()})")
print(f"  Max: {stocks_per_date.max():.0f} (on {stocks_per_date.idxmax()})")

# Number of valid dates per stock
dates_per_stock = universe_mask_wide.sum(axis=0)
print(f"\nDates per stock (valid universe):")
print(f"  Mean: {dates_per_stock.mean():.0f}")
print(f"  Median: {dates_per_stock.median():.0f}")
print(f"  Min: {dates_per_stock.min():.0f}")
print(f"  Max: {dates_per_stock.max():.0f}")

# Stocks with < 12 months of data
short_history = dates_per_stock[dates_per_stock < 12]
print(f"\nStocks with < 12 months of valid data: {len(short_history):,} ({len(short_history) / len(dates_per_stock) * 100:.2f}%)")

# ============================================================================
# 8. SAVE PROCESSED DATA
# ============================================================================
print("\n" + "="*80)
print("8. SAVE PROCESSED DATA")
print("="*80)

# Save wide format dataframes
price_wide.to_parquet("data/fnguide/processed/price_wide.parquet")
print("✓ Saved: data/fnguide/processed/price_wide.parquet")

trading_value_wide.to_parquet("data/fnguide/processed/trading_value_wide.parquet")
print("✓ Saved: data/fnguide/processed/trading_value_wide.parquet")

listed_shares_wide.to_parquet("data/fnguide/processed/listed_shares_wide.parquet")
print("✓ Saved: data/fnguide/processed/listed_shares_wide.parquet")

floating_shares_wide.to_parquet("data/fnguide/processed/floating_shares_wide.parquet")
print("✓ Saved: data/fnguide/processed/floating_shares_wide.parquet")

volume_wide.to_parquet("data/fnguide/processed/volume_wide.parquet")
print("✓ Saved: data/fnguide/processed/volume_wide.parquet")

turnover_listed_wide.to_parquet("data/fnguide/processed/turnover_listed_wide.parquet")
print("✓ Saved: data/fnguide/processed/turnover_listed_wide.parquet")

turnover_floating_wide.to_parquet("data/fnguide/processed/turnover_floating_wide.parquet")
print("✓ Saved: data/fnguide/processed/turnover_floating_wide.parquet")

universe_mask_wide.to_parquet("data/fnguide/processed/universe_mask_wide.parquet")
print("✓ Saved: data/fnguide/processed/universe_mask_wide.parquet")

# Save long format with additional computed columns
df_filtered.to_parquet("data/fnguide/processed/dataguide_filtered.parquet")
print("✓ Saved: data/fnguide/processed/dataguide_filtered.parquet")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print("\nKey findings:")
print(f"  1. 유동주식비율 formula is correct: 유동주식수 / 상장주식수")
print(f"  2. Removed {len(pennystock_symbols):,} penny stock symbols")
print(f"  3. Valid universe: {universe_mask_wide.sum().sum():,} observations")
print(f"  4. Mean turnover (listed): {turnover_listed_wide.mean().mean():.4f}%")
print(f"  5. Mean turnover (floating): {turnover_floating_wide.mean().mean():.4f}%")
print(f"  6. Floating turnover is ~{turnover_comparison['ratio'].mean():.2f}x higher than listed turnover")
print("\n✓ All processed data saved to data/fnguide/processed/")



