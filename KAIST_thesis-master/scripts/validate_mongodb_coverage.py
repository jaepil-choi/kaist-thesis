"""
Phase 1.1: MongoDB Coverage Check

Purpose:
- Identify firms in MongoDB (currently listed)
- Match with FnGuide universe (all firms including delisted)
- Identify survivorship bias: firms in FnGuide but NOT in MongoDB
- Generate coverage report

Outputs:
- data/korean_texts/matched_firms.csv
- data/korean_texts/unmatched_fnguide_firms.csv
- reports/1.1_mongodb_coverage.md
"""

import os
import sys
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Set console encoding to UTF-8 (for Windows)
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

# Output directories
DATA_DIR = Path("data/korean_texts")
REPORTS_DIR = Path("reports")
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("PHASE 1.1: MONGODB COVERAGE CHECK")
print("=" * 80)
print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==============================================================================
# 1. Connect to MongoDB and get business descriptions
# ==============================================================================

print("\n" + "=" * 80)
print("1. CONNECTING TO MONGODB")
print("=" * 80)

print(f"\nConnecting to: mongodb://{MONGO_HOST}/")
print(f"Database: {DB_NAME}")
print(f"Collection: {COLLECTION_NAME}")

client = MongoClient(f"mongodb://{MONGO_HOST}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Query business overview sections (section_code="020100")
print("\nQuerying business overview sections (section_code='020100')...")

docs = list(collection.find(
    {"section_code": "020100"},
    {"stock_code": 1, "corp_name": 1, "year": 1, "char_count": 1, "rcept_dt": 1}
))

print(f"Retrieved {len(docs):,} documents")

# Convert to DataFrame
df_mongo = pd.DataFrame(docs)

# Get unique stock codes and firms
mongo_stock_codes = set(df_mongo['stock_code'].unique())
print(f"\nUnique stock codes in MongoDB: {len(mongo_stock_codes):,}")

# Show sample
print("\nSample MongoDB stock codes (first 10):")
for code in sorted(mongo_stock_codes)[:10]:
    sample_doc = df_mongo[df_mongo['stock_code'] == code].iloc[0]
    print(f"  {code} - {sample_doc['corp_name']}")

# ==============================================================================
# 2. Load FnGuide data
# ==============================================================================

print("\n" + "=" * 80)
print("2. LOADING FNGUIDE DATA")
print("=" * 80)

fnguide_path = Path("data/fnguide/processed/dataguide_filtered.parquet")

if not fnguide_path.exists():
    print(f"\n[ERROR] FnGuide data not found at: {fnguide_path}")
    print("Please ensure FnGuide data is available.")
    exit(1)

print(f"\nLoading FnGuide data from: {fnguide_path}")
df_fnguide = pd.read_parquet(fnguide_path)

print(f"FnGuide data shape: {df_fnguide.shape}")
print(f"Columns: {list(df_fnguide.columns)}")

# Get unique FnGuide symbols
fnguide_symbols = set(df_fnguide['symbol'].unique())
print(f"\nUnique stock codes in FnGuide: {len(fnguide_symbols):,}")

# Show sample
print("\nSample FnGuide symbols (first 10):")
for symbol in sorted(fnguide_symbols)[:10]:
    print(f"  {symbol}")

# ==============================================================================
# 3. Match MongoDB stock codes with FnGuide
# ==============================================================================

print("\n" + "=" * 80)
print("3. MATCHING MONGODB WITH FNGUIDE")
print("=" * 80)

# MongoDB stock codes are 6 digits (e.g., "000020")
# FnGuide symbols have exchange prefix: "A" for KOSPI, "Q" for KOSDAQ
# We need to add prefix to MongoDB codes

print("\nMongoDB stock code format: '000020' (6 digits)")
print("FnGuide symbol format: 'A000020' (prefix + 6 digits)")
print("\nAdding 'A' prefix to MongoDB codes for matching...")

# Add "A" prefix to MongoDB codes
mongo_codes_with_prefix = {'A' + code for code in mongo_stock_codes}

print(f"MongoDB codes with 'A' prefix: {len(mongo_codes_with_prefix):,}")

# Match with FnGuide
matched_codes = mongo_codes_with_prefix & fnguide_symbols
unmatched_codes = fnguide_symbols - mongo_codes_with_prefix

print(f"\n[RESULTS]")
print(f"  Matched (in both MongoDB and FnGuide): {len(matched_codes):,}")
print(f"  Unmatched (in FnGuide but NOT in MongoDB): {len(unmatched_codes):,}")
print(f"  Coverage: {100 * len(matched_codes) / len(fnguide_symbols):.1f}%")

# Also check for KOSDAQ (Q prefix)
print("\nChecking KOSDAQ (Q prefix)...")
mongo_codes_with_q = {'Q' + code for code in mongo_stock_codes}
matched_q = mongo_codes_with_q & fnguide_symbols
print(f"  Matched with 'Q' prefix (KOSDAQ): {len(matched_q):,}")

# Combine all matches
all_matched = matched_codes | matched_q
all_unmatched = fnguide_symbols - all_matched

print(f"\n[TOTAL RESULTS]")
print(f"  Total matched (A + Q prefixes): {len(all_matched):,}")
print(f"  Total unmatched: {len(all_unmatched):,}")
print(f"  Total coverage: {100 * len(all_matched) / len(fnguide_symbols):.1f}%")

# ==============================================================================
# 4. Create matched firms dataset
# ==============================================================================

print("\n" + "=" * 80)
print("4. CREATING MATCHED FIRMS DATASET")
print("=" * 80)

# Get firm-year coverage for matched firms
matched_mongo_codes = {code[1:] for code in all_matched}  # Remove prefix

df_matched = df_mongo[df_mongo['stock_code'].isin(matched_mongo_codes)].copy()

print(f"\nMatched documents: {len(df_matched):,}")

# Create summary by firm
matched_summary = df_matched.groupby('stock_code').agg({
    'corp_name': 'first',
    'year': lambda x: sorted(x.unique()),
    'char_count': 'mean'
}).reset_index()

matched_summary['num_years'] = matched_summary['year'].apply(len)
matched_summary['year_min'] = matched_summary['year'].apply(min)
matched_summary['year_max'] = matched_summary['year'].apply(max)
matched_summary['avg_char_count'] = matched_summary['char_count'].round(0).astype(int)

# Add FnGuide symbol
matched_summary['fnguide_symbol'] = matched_summary['stock_code'].apply(
    lambda x: 'A' + x if 'A' + x in fnguide_symbols else 'Q' + x
)

# Reorder columns
matched_summary = matched_summary[[
    'stock_code', 'fnguide_symbol', 'corp_name',
    'num_years', 'year_min', 'year_max', 'avg_char_count'
]]

print("\nMatched firms summary:")
print(f"  Total firms: {len(matched_summary):,}")
print(f"  Average years per firm: {matched_summary['num_years'].mean():.1f}")
print(f"  Year range: {matched_summary['year_min'].min()} - {matched_summary['year_max'].max()}")

# Save matched firms
output_path = DATA_DIR / "matched_firms.csv"
matched_summary.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"\n[OK] Saved matched firms to: {output_path}")

# ==============================================================================
# 5. Create unmatched firms dataset (SURVIVORSHIP BIAS)
# ==============================================================================

print("\n" + "=" * 80)
print("5. CREATING UNMATCHED FIRMS DATASET (SURVIVORSHIP BIAS)")
print("=" * 80)

print("\nUnmatched firms = firms in FnGuide but NOT in MongoDB")
print("These are likely delisted or inactive firms")

# Get FnGuide info for unmatched firms
df_unmatched_fnguide = df_fnguide[df_fnguide['symbol'].isin(all_unmatched)].copy()

print(f"\nUnmatched firm observations: {len(df_unmatched_fnguide):,}")

# Create summary by firm
if len(df_unmatched_fnguide) > 0:
    unmatched_summary = df_unmatched_fnguide.groupby('symbol').agg({
        'symbol_name': 'first',
        'date': ['min', 'max', 'count']
    }).reset_index()

    unmatched_summary.columns = ['symbol', 'corp_name', 'date_min', 'date_max', 'num_observations']

    # Convert dates
    unmatched_summary['year_min'] = pd.to_datetime(unmatched_summary['date_min']).dt.year
    unmatched_summary['year_max'] = pd.to_datetime(unmatched_summary['date_max']).dt.year

    print(f"\nUnmatched firms summary:")
    print(f"  Total firms: {len(unmatched_summary):,}")
    print(f"  Year range: {unmatched_summary['year_min'].min()} - {unmatched_summary['year_max'].max()}")

    # Save unmatched firms
    output_path = DATA_DIR / "unmatched_fnguide_firms.csv"
    unmatched_summary.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n[OK] Saved unmatched firms to: {output_path}")

    # Show sample
    print("\nSample unmatched firms (first 20):")
    for idx, row in unmatched_summary.head(20).iterrows():
        print(f"  {row['symbol']} - {row['corp_name']} ({row['year_min']}-{row['year_max']})")
else:
    print("\n[INFO] No unmatched firms found")

# ==============================================================================
# 6. Generate coverage report
# ==============================================================================

print("\n" + "=" * 80)
print("6. GENERATING COVERAGE REPORT")
print("=" * 80)

# Create firm-year coverage matrix
coverage_data = []

for year in range(2010, 2026):
    year_str = str(year)

    # Firms in MongoDB for this year
    mongo_firms = set(df_mongo[df_mongo['year'] == year_str]['stock_code'].unique())

    # Firms in FnGuide for this year
    fnguide_year = df_fnguide[pd.to_datetime(df_fnguide['date']).dt.year == year]
    fnguide_firms = set(fnguide_year['symbol'].unique())

    # Match
    mongo_with_prefix = {'A' + code for code in mongo_firms} | {'Q' + code for code in mongo_firms}
    matched_year = mongo_with_prefix & fnguide_firms

    coverage_data.append({
        'year': year,
        'mongodb_firms': len(mongo_firms),
        'fnguide_firms': len(fnguide_firms),
        'matched_firms': len(matched_year),
        'coverage_pct': 100 * len(matched_year) / len(fnguide_firms) if len(fnguide_firms) > 0 else 0
    })

df_coverage = pd.DataFrame(coverage_data)

print("\nYearly coverage:")
print(df_coverage.to_string(index=False))

# Save coverage report
output_path = DATA_DIR / "coverage_report.csv"
df_coverage.to_csv(output_path, index=False)
print(f"\n[OK] Saved coverage report to: {output_path}")

# ==============================================================================
# 7. Generate markdown report
# ==============================================================================

print("\n" + "=" * 80)
print("7. GENERATING MARKDOWN REPORT")
print("=" * 80)

report_path = REPORTS_DIR / "1.1_mongodb_coverage.md"

with open(report_path, 'w', encoding='utf-8') as f:
    f.write(f"# Phase 1.1: MongoDB Coverage Check\n\n")
    f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    f.write("## Objective\n\n")
    f.write("Validate MongoDB data coverage and identify survivorship bias.\n\n")

    f.write("## Data Sources\n\n")
    f.write(f"- **MongoDB**: {MONGO_HOST} / {DB_NAME} / {COLLECTION_NAME}\n")
    f.write(f"- **Section Code**: 020100 (Business Overview)\n")
    f.write(f"- **FnGuide**: {fnguide_path}\n\n")

    f.write("## Key Findings\n\n")
    f.write(f"### Overall Coverage\n\n")
    f.write(f"- **MongoDB documents**: {len(df_mongo):,}\n")
    f.write(f"- **Unique firms in MongoDB**: {len(mongo_stock_codes):,}\n")
    f.write(f"- **Unique firms in FnGuide**: {len(fnguide_symbols):,}\n")
    f.write(f"- **Matched firms**: {len(all_matched):,}\n")
    f.write(f"- **Coverage**: {100 * len(all_matched) / len(fnguide_symbols):.1f}%\n\n")

    f.write(f"### Survivorship Bias\n\n")
    f.write(f"- **Unmatched firms** (in FnGuide but NOT in MongoDB): {len(all_unmatched):,}\n")
    f.write(f"- These are likely delisted or inactive firms\n")
    f.write(f"- Will be collected later using name-based search\n\n")

    f.write("### Matched Firms Statistics\n\n")
    f.write(f"- **Total matched firms**: {len(matched_summary):,}\n")
    f.write(f"- **Average years per firm**: {matched_summary['num_years'].mean():.1f}\n")
    f.write(f"- **Year range**: {matched_summary['year_min'].min()} - {matched_summary['year_max'].max()}\n")
    f.write(f"- **Average text length**: {matched_summary['avg_char_count'].mean():,.0f} characters\n\n")

    f.write("## Yearly Coverage\n\n")
    f.write("| Year | MongoDB Firms | FnGuide Firms | Matched | Coverage % |\n")
    f.write("|------|---------------|---------------|---------|------------|\n")
    for _, row in df_coverage.iterrows():
        f.write(f"| {row['year']} | {row['mongodb_firms']:,} | {row['fnguide_firms']:,} | {row['matched_firms']:,} | {row['coverage_pct']:.1f}% |\n")
    f.write("\n")

    f.write("## Output Files\n\n")
    f.write("- `data/korean_texts/matched_firms.csv` - Firms in both MongoDB and FnGuide\n")
    f.write("- `data/korean_texts/unmatched_fnguide_firms.csv` - Firms in FnGuide but NOT in MongoDB (survivorship bias)\n")
    f.write("- `data/korean_texts/coverage_report.csv` - Yearly coverage statistics\n\n")

    f.write("## Next Steps\n\n")
    f.write("1. Proceed to Phase 1.2: Extract and clean business descriptions\n")
    f.write("2. Future: Collect unmatched firms using name-based search to address survivorship bias\n")

print(f"\n[OK] Saved markdown report to: {report_path}")

# ==============================================================================
# Summary
# ==============================================================================

print("\n" + "=" * 80)
print("PHASE 1.1 COMPLETE")
print("=" * 80)

print(f"\n[SUMMARY]")
print(f"  Total MongoDB documents: {len(df_mongo):,}")
print(f"  Matched firms: {len(all_matched):,}")
print(f"  Unmatched firms (survivorship bias): {len(all_unmatched):,}")
print(f"  Coverage: {100 * len(all_matched) / len(fnguide_symbols):.1f}%")

print(f"\n[OUTPUT FILES]")
print(f"  {DATA_DIR / 'matched_firms.csv'}")
print(f"  {DATA_DIR / 'unmatched_fnguide_firms.csv'}")
print(f"  {DATA_DIR / 'coverage_report.csv'}")
print(f"  {report_path}")

print(f"\n[NEXT STEP]")
print(f"  Run Phase 1.2: python scripts/extract_korean_texts.py")

print("\n" + "=" * 80)
