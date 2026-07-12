import pandas as pd
import numpy as np

# Load data
print("Loading data...")
df_groups = pd.read_parquet("data/fnguide/processed/dataguide_groups.parquet")
df_price = pd.read_parquet("data/fnguide/processed/dataguide_price.parquet")

print("\n" + "="*80)
print("GROUPS DATA EXPLORATION")
print("="*80)
print(f"\nShape: {df_groups.shape}")
print(f"\nColumns: {df_groups.columns.tolist()}")
print(f"\nData types:\n{df_groups.dtypes}")
print(f"\nFirst few rows:\n{df_groups.head()}")
print(f"\nDate range: {df_groups['date'].min()} to {df_groups['date'].max()}")
print(f"\nUnique symbols: {df_groups['symbol'].nunique()}")

print("\n" + "="*80)
print("PRICE DATA EXPLORATION")
print("="*80)
print(f"\nShape: {df_price.shape}")
print(f"\nColumns: {df_price.columns.tolist()}")
print(f"\nData types:\n{df_price.dtypes}")
print(f"\nFirst few rows:\n{df_price.head()}")
print(f"\nDate range: {df_price['date'].min()} to {df_price['date'].max()}")
print(f"\nUnique symbols: {df_price['symbol'].nunique()}")

# Merge on [date, symbol] key
print("\n" + "="*80)
print("MERGING DATA")
print("="*80)
df_merged = pd.merge(
    df_groups,
    df_price,
    on=['date', 'symbol', 'symbol_name'],
    how='inner'
)
print(f"\nMerged data shape: {df_merged.shape}")
print(f"\nColumns: {df_merged.columns.tolist()}")

print("\n" + "="*80)
print("MERGED DATA EXPLORATION")
print("="*80)
print(f"\nData types:\n{df_merged.dtypes}")
print(f"\nFirst few rows:\n{df_merged.head(10)}")
print(f"\nBasic statistics:\n{df_merged.describe()}")

# Check for missing values
print("\n" + "="*80)
print("MISSING VALUES")
print("="*80)
missing_info = pd.DataFrame({
    'Missing_Count': df_merged.isnull().sum(),
    'Missing_Pct': (df_merged.isnull().sum() / len(df_merged) * 100).round(2)
})
print(missing_info[missing_info['Missing_Count'] > 0])

# Examine key categorical columns
print("\n" + "="*80)
print("CATEGORICAL COLUMNS EXAMINATION")
print("="*80)

print("\n거래정지구분 (Trading Suspension Status):")
print(f"Unique values: {df_merged['거래정지구분'].unique()}")
print(f"Value counts:\n{df_merged['거래정지구분'].value_counts(dropna=False)}")

print("\n관리구분 (Management Classification):")
print(f"Unique values: {df_merged['관리구분'].unique()}")
print(f"Value counts:\n{df_merged['관리구분'].value_counts(dropna=False)}")

# Examine numerical columns
print("\n" + "="*80)
print("KEY NUMERICAL COLUMNS")
print("="*80)

print("\n수정주가(원) [Adjusted Price]:")
print(df_merged['수정주가(원)'].describe())
print(f"Zero/Null count: {(df_merged['수정주가(원)'] <= 0).sum()} / {df_merged['수정주가(원)'].isnull().sum()}")

print("\n거래대금(원) [Trading Value]:")
print(df_merged['거래대금(원)'].describe())
print(f"Zero/Null count: {(df_merged['거래대금(원)'] <= 0).sum()} / {df_merged['거래대금(원)'].isnull().sum()}")

print("\n상장주식수 (보통)(주) [Listed Shares]:")
print(df_merged['상장주식수 (보통)(주)'].describe())
print(f"Zero/Null count: {(df_merged['상장주식수 (보통)(주)'] <= 0).sum()} / {df_merged['상장주식수 (보통)(주)'].isnull().sum()}")

print("\n유동주식수(주) [Floating Shares]:")
print(df_merged['유동주식수(주)'].describe())
print(f"Zero/Null count: {(df_merged['유동주식수(주)'] <= 0).sum()} / {df_merged['유동주식수(주)'].isnull().sum()}")

print("\n유동주식비율(%) [Floating Share Ratio %]:")
print(df_merged['유동주식비율(%)'].describe())

# Check the relationship: 유동주식비율 = 유동주식수 / 상장주식수
print("\n" + "="*80)
print("FLOATING SHARE RATIO VALIDATION")
print("="*80)
# Create a subset where all values are non-null
valid_mask = (
    df_merged['유동주식수(주)'].notna() & 
    df_merged['상장주식수 (보통)(주)'].notna() & 
    df_merged['유동주식비율(%)'].notna() &
    (df_merged['상장주식수 (보통)(주)'] > 0)
)
df_valid = df_merged[valid_mask].copy()

df_valid['calculated_ratio'] = (df_valid['유동주식수(주)'] / df_valid['상장주식수 (보통)(주)']) * 100
df_valid['ratio_diff'] = df_valid['calculated_ratio'] - df_valid['유동주식비율(%)']

print(f"\nRecords with all non-null values: {len(df_valid)}")
print(f"\nCalculated ratio statistics:")
print(df_valid['calculated_ratio'].describe())
print(f"\nReported ratio statistics:")
print(df_valid['유동주식비율(%)'].describe())
print(f"\nDifference statistics:")
print(df_valid['ratio_diff'].describe())
print(f"\nSample comparison (first 20 rows):")
print(df_valid[['symbol', 'date', '유동주식수(주)', '상장주식수 (보통)(주)', 
               '유동주식비율(%)', 'calculated_ratio', 'ratio_diff']].head(20))

# Industry classification
print("\n" + "="*80)
print("INDUSTRY CLASSIFICATIONS")
print("="*80)
print(f"\nFnGuide Sector: {df_merged['FnGuide Sector'].nunique()} unique values")
print(df_merged['FnGuide Sector'].value_counts().head(10))

print(f"\nFnGuide Industry: {df_merged['FnGuide Industry'].nunique()} unique values")
print(df_merged['FnGuide Industry'].value_counts().head(10))

print(f"\n거래소 업종: {df_merged['거래소 업종'].nunique()} unique values")
print(df_merged['거래소 업종'].value_counts().head(10))

print("\n" + "="*80)
print("PRICE DISTRIBUTION")
print("="*80)
price_ranges = [
    (0, 1000, "0-1000 won"),
    (1000, 5000, "1K-5K won"),
    (5000, 10000, "5K-10K won"),
    (10000, 50000, "10K-50K won"),
    (50000, 100000, "50K-100K won"),
    (100000, float('inf'), ">100K won")
]

for low, high, label in price_ranges:
    count = ((df_merged['수정주가(원)'] > low) & (df_merged['수정주가(원)'] <= high)).sum()
    pct = count / len(df_merged) * 100
    print(f"{label}: {count:,} ({pct:.2f}%)")

print("\n" + "="*80)
print("SAMPLE DATA FOR VERIFICATION")
print("="*80)
print("\nRandom sample of 10 rows:")
sample = df_merged.sample(10, random_state=42)
print(sample[['date', 'symbol', 'symbol_name', '수정주가(원)', '거래대금(원)', 
              '상장주식수 (보통)(주)', '유동주식수(주)', '유동주식비율(%)',
              '거래정지구분', '관리구분']].to_string())

print("\n" + "="*80)
print("EDA COMPLETE")
print("="*80)



