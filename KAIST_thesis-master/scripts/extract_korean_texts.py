"""
Phase 1.2: Extract and Clean Business Descriptions

Purpose:
- Extract business descriptions from MongoDB
- Deduplicate: Keep latest entry per firm-year
- Filter character count outliers (95th percentile cutoff)
- Create clean firm-year panel

Outputs:
- data/korean_texts/business_descriptions_raw.parquet
- data/korean_texts/business_descriptions_clean.parquet
- data/korean_texts/text_samples.csv
- data/korean_texts/char_count_distribution.png
- reports/1.2_data_extraction.md
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Set console encoding to UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

# Output directories
DATA_DIR = Path("data/korean_texts")
REPORTS_DIR = Path("reports")
OUTPUT_DIR = Path("outputs")
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("PHASE 1.2: EXTRACT AND CLEAN BUSINESS DESCRIPTIONS")
print("=" * 80)
print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==============================================================================
# 1. Extract business descriptions from MongoDB
# ==============================================================================

print("\n" + "=" * 80)
print("1. EXTRACTING FROM MONGODB")
print("=" * 80)

print(f"\nConnecting to: mongodb://{MONGO_HOST}/")
client = MongoClient(f"mongodb://{MONGO_HOST}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ==============================================================================
# 0. MongoDB document count analysis
# ==============================================================================

print("\n" + "=" * 80)
print("0. MONGODB DOCUMENT COUNT ANALYSIS")
print("=" * 80)

# Count total documents
total_in_db = collection.count_documents({})
print(f"\nTotal documents in MongoDB: {total_in_db:,}")

# Count by year
pipeline = [
    {"$group": {"_id": "$year", "count": {"$sum": 1}}},
    {"$sort": {"_id": 1}}
]
year_counts_db = {item['_id']: item['count'] for item in collection.aggregate(pipeline)}

print("\nDocuments per year in MongoDB:")
for year in sorted(year_counts_db.keys()):
    print(f"  {year}: {year_counts_db[year]:,}")

# Count by level
pipeline = [
    {"$group": {"_id": "$level", "count": {"$sum": 1}}},
    {"$sort": {"_id": 1}}
]
level_counts_db = list(collection.aggregate(pipeline))
print("\nDocuments by level:")
for item in level_counts_db:
    level = item['_id'] if item['_id'] is not None else "null"
    print(f"  level={level}: {item['count']:,}")

print("\n[EXPECTED] After extraction and deduplication:")
print(f"  Should extract: {total_in_db:,} documents")
print(f"  After level deduplication: Will depend on level=1/2 overlap")
print(f"  After firm-year deduplication: Will depend on multiple reports")

# ==============================================================================
# 1. Extract business descriptions from MongoDB (CONTINUED)
# ==============================================================================

print("\nQuerying ALL documents (no section_code filter)...")

docs = list(collection.find(
    {},  # No filter - collection already has 020000 OR 020100
    {"stock_code": 1, "corp_name": 1, "year": 1, "text": 1, "char_count": 1, "rcept_dt": 1, "rcept_no": 1, "level": 1}
))

print(f"Retrieved {len(docs):,} documents")
print(f"[SANITY CHECK] Expected {total_in_db:,}, got {len(docs):,}")
if len(docs) != total_in_db:
    print(f"  [WARNING] Mismatch: {abs(len(docs) - total_in_db):,} documents difference")

# Convert to DataFrame
df_raw = pd.DataFrame(docs)

# Remove _id field (not needed)
if '_id' in df_raw.columns:
    df_raw = df_raw.drop('_id', axis=1)

print(f"\nDataFrame shape: {df_raw.shape}")
print(f"Columns: {list(df_raw.columns)}")

# Sanity check: Compare extracted year counts vs MongoDB
print("\n[SANITY CHECK] Year distribution comparison:")
print(f"{'Year':<6} {'MongoDB':<10} {'Extracted':<10} {'Match':<10}")
print("-" * 40)
year_counts_extracted = df_raw['year'].value_counts().sort_index()
for year in sorted(set(list(year_counts_db.keys()) + list(year_counts_extracted.index))):
    mongo_count = year_counts_db.get(year, 0)
    extracted_count = year_counts_extracted.get(year, 0)
    match = "OK" if mongo_count == extracted_count else f"DIFF: {abs(mongo_count - extracted_count)}"
    print(f"{year:<6} {mongo_count:<10,} {extracted_count:<10,} {match:<10}")

# Save raw data
output_path = DATA_DIR / "business_descriptions_raw.parquet"
df_raw.to_parquet(output_path, index=False)
print(f"\n[OK] Saved raw data to: {output_path}")

# ==============================================================================
# 2. Character count distribution analysis
# ==============================================================================

print("\n" + "=" * 80)
print("2. CHARACTER COUNT DISTRIBUTION")
print("=" * 80)

print(f"\nBasic statistics:")
print(f"  Mean: {df_raw['char_count'].mean():,.0f}")
print(f"  Median: {df_raw['char_count'].median():,.0f}")
print(f"  Min: {df_raw['char_count'].min():,}")
print(f"  Max: {df_raw['char_count'].max():,}")

# Percentiles
percentiles = [50, 75, 90, 95, 99]
print(f"\nPercentiles:")
for p in percentiles:
    val = np.percentile(df_raw['char_count'], p)
    print(f"  {p}%: {val:>10,.0f}")

# Calculate 95th percentile cutoff
cutoff_95 = np.percentile(df_raw['char_count'], 95)
print(f"\n95th percentile cutoff: {cutoff_95:,.0f} characters")

# Visualize distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Character Count Distribution - Before/After Filtering', fontsize=14, fontweight='bold')

# Before filtering
ax1 = axes[0]
ax1.hist(df_raw['char_count'], bins=100, edgecolor='black', alpha=0.7, color='skyblue')
ax1.set_xlabel('Character Count')
ax1.set_ylabel('Frequency')
ax1.set_title(f'Before Filtering (n={len(df_raw):,})')
ax1.axvline(df_raw['char_count'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df_raw["char_count"].mean():,.0f}')
ax1.axvline(df_raw['char_count'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: {df_raw["char_count"].median():,.0f}')
ax1.axvline(cutoff_95, color='orange', linestyle=':', linewidth=2, label=f'95th: {cutoff_95:,.0f}')
ax1.legend()
ax1.grid(True, alpha=0.3)

# After filtering (preview)
df_filtered_preview = df_raw[df_raw['char_count'] <= cutoff_95]
ax2 = axes[1]
ax2.hist(df_filtered_preview['char_count'], bins=100, edgecolor='black', alpha=0.7, color='lightcoral')
ax2.set_xlabel('Character Count')
ax2.set_ylabel('Frequency')
ax2.set_title(f'After 95th Percentile Filter (n={len(df_filtered_preview):,})')
ax2.axvline(df_filtered_preview['char_count'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df_filtered_preview["char_count"].mean():,.0f}')
ax2.axvline(df_filtered_preview['char_count'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: {df_filtered_preview["char_count"].median():,.0f}')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()

output_path = DATA_DIR / "char_count_distribution.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n[OK] Saved distribution plot to: {output_path}")
plt.close()

# ==============================================================================
# 3. Deduplication analysis
# ==============================================================================

print("\n" + "=" * 80)
print("3. DEDUPLICATION ANALYSIS")
print("=" * 80)

# Check for duplicates
duplicates = df_raw.groupby(['stock_code', 'year']).size()
n_duplicates = (duplicates > 1).sum()
total_duplicate_docs = (duplicates - 1).sum()

print(f"\nDuplicate firm-year combinations:")
print(f"  Unique firm-years with duplicates: {n_duplicates:,}")
print(f"  Total duplicate documents: {total_duplicate_docs:,}")

if n_duplicates > 0:
    print(f"\nSample duplicates:")
    duplicate_pairs = duplicates[duplicates > 1].head(10)
    for (stock_code, year), count in duplicate_pairs.items():
        print(f"  {stock_code} ({year}): {count} documents")

# ==============================================================================
# 4. Cleaning pipeline
# ==============================================================================

print("\n" + "=" * 80)
print("4. CLEANING PIPELINE")
print("=" * 80)

df_clean = df_raw.copy()

# Step 1: Remove zero-length documents
print(f"\nStep 1: Remove zero-length documents")
n_before = len(df_clean)
df_clean = df_clean[df_clean['char_count'] > 0]
n_removed = n_before - len(df_clean)
print(f"  Removed: {n_removed:,} documents")
print(f"  Remaining: {len(df_clean):,} documents")

# Step 2: Apply 95th percentile cutoff
print(f"\nStep 2: Apply 95th percentile cutoff ({cutoff_95:,.0f} characters)")
n_before = len(df_clean)
df_clean = df_clean[df_clean['char_count'] <= cutoff_95]
n_removed = n_before - len(df_clean)
pct_removed = 100 * n_removed / n_before
print(f"  Removed: {n_removed:,} documents ({pct_removed:.1f}%)")
print(f"  Remaining: {len(df_clean):,} documents")

# Step 3: Level-based deduplication (prefer level=2)
print(f"\nStep 3: Level-based deduplication (prefer level=2)")
n_before = len(df_clean)

# Handle missing level field
if 'level' not in df_clean.columns:
    df_clean['level'] = 1
    print(f"  [WARNING] 'level' field missing, assuming level=1 for all documents")
else:
    # Show level distribution before deduplication
    level_dist_before = df_clean['level'].value_counts().sort_index()
    print(f"  Level distribution before:")
    for level, count in level_dist_before.items():
        print(f"    level={level}: {count:,}")

# Sort: prefer level=2 over level=1 for same rcept_no
df_clean = df_clean.sort_values(['rcept_no', 'level'], ascending=[True, False])
df_clean = df_clean.drop_duplicates(subset=['rcept_no'], keep='first')

n_removed = n_before - len(df_clean)
n_level2 = (df_clean['level'] == 2).sum()
n_level1 = (df_clean['level'] == 1).sum()
pct_level2 = 100 * n_level2 / len(df_clean) if len(df_clean) > 0 else 0

print(f"  Removed: {n_removed:,} duplicate rcept_no (kept higher level)")
print(f"  Remaining: {len(df_clean):,} documents")
print(f"  Level distribution after:")
print(f"    level=2: {n_level2:,} ({pct_level2:.1f}%)")
print(f"    level=1: {n_level1:,} ({100-pct_level2:.1f}%)")

# Step 4: Firm-year deduplication (keep latest per firm-year)
print(f"\nStep 4: Firm-year deduplication (keep latest rcept_dt)")
n_before = len(df_clean)

# Sort by rcept_dt descending (latest first)
df_clean = df_clean.sort_values('rcept_dt', ascending=False)

# Drop duplicates, keeping first (latest)
df_clean = df_clean.drop_duplicates(subset=['stock_code', 'year'], keep='first')

n_removed = n_before - len(df_clean)
print(f"  Removed: {n_removed:,} duplicate documents")
print(f"  Remaining: {len(df_clean):,} unique firm-years")

# Sort by stock_code and year
df_clean = df_clean.sort_values(['stock_code', 'year']).reset_index(drop=True)

# ==============================================================================
# 5. Summary statistics
# ==============================================================================

print("\n" + "=" * 80)
print("5. SUMMARY STATISTICS (CLEAN DATA)")
print("=" * 80)

print(f"\nFirm-year panel:")
print(f"  Total observations: {len(df_clean):,}")
print(f"  Unique firms: {df_clean['stock_code'].nunique():,}")
print(f"  Unique years: {df_clean['year'].nunique()}")
print(f"  Year range: {df_clean['year'].min()} - {df_clean['year'].max()}")

print(f"\nObservations per year:")
year_counts = df_clean['year'].value_counts().sort_index()

print("\n[FINAL SANITY CHECK] Year distribution after all cleaning:")
print(f"{'Year':<6} {'MongoDB':<10} {'Final':<10} {'% Retained':<12}")
print("-" * 45)
for year in sorted(set(list(year_counts_db.keys()) + list(year_counts.index))):
    mongo_count = year_counts_db.get(year, 0)
    final_count = year_counts.get(year, 0)
    pct_retained = 100 * final_count / mongo_count if mongo_count > 0 else 0
    print(f"{year:<6} {mongo_count:<10,} {final_count:<10,} {pct_retained:<12.1f}%")

total_final = len(df_clean)
total_expected = sum(year_counts_db.values())
pct_retained_total = 100 * total_final / total_expected if total_expected > 0 else 0
print("-" * 45)
print(f"{'TOTAL':<6} {total_expected:<10,} {total_final:<10,} {pct_retained_total:<12.1f}%")

print("\n[EXPECTED] Retention rate should be 70-90% after deduplication")
if pct_retained_total < 50:
    print(f"  [WARNING] Retention rate {pct_retained_total:.1f}% is too low - investigate!")
elif pct_retained_total > 95:
    print(f"  [WARNING] Retention rate {pct_retained_total:.1f}% is too high - deduplication may not be working!")

print(f"\nCharacter count statistics (after cleaning):")
print(f"  Mean: {df_clean['char_count'].mean():,.0f}")
print(f"  Median: {df_clean['char_count'].median():,.0f}")
print(f"  Min: {df_clean['char_count'].min():,}")
print(f"  Max: {df_clean['char_count'].max():,}")

# ==============================================================================
# 6. Save clean data
# ==============================================================================

print("\n" + "=" * 80)
print("6. SAVING CLEAN DATA")
print("=" * 80)

# Save clean data
output_path = DATA_DIR / "business_descriptions_clean.parquet"
df_clean.to_parquet(output_path, index=False)
print(f"\n[OK] Saved clean data to: {output_path}")

# Save 20 random samples for manual inspection
samples = df_clean.sample(min(20, len(df_clean)), random_state=42)
samples_export = samples[['stock_code', 'corp_name', 'year', 'char_count', 'text']].copy()
samples_export['text_preview'] = samples_export['text'].str[:500] + '...'
samples_export = samples_export.drop('text', axis=1)

output_path = DATA_DIR / "text_samples.csv"
samples_export.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"[OK] Saved text samples to: {output_path}")

# ==============================================================================
# 7. Generate markdown report
# ==============================================================================

print("\n" + "=" * 80)
print("7. GENERATING REPORT")
print("=" * 80)

report_path = REPORTS_DIR / "1.2_data_extraction.md"

with open(report_path, 'w', encoding='utf-8') as f:
    f.write(f"# Phase 1.2: Extract and Clean Business Descriptions\n\n")
    f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    f.write("## Objective\n\n")
    f.write("Extract business descriptions from MongoDB, deduplicate, and filter outliers.\n\n")

    f.write("## Data Extraction\n\n")
    f.write(f"- **Source**: MongoDB {MONGO_HOST} / {DB_NAME} / {COLLECTION_NAME}\n")
    f.write(f"- **Total documents in MongoDB**: {total_in_db:,}\n")
    f.write(f"- **Section Codes**: 020000 (old data) OR 020100 (new data)\n")
    f.write(f"- **Raw documents retrieved**: {len(df_raw):,}\n")
    f.write(f"- **Level field handling**: Prefer level=2 (individual sections) over level=1 (merged text)\n\n")

    f.write("## Character Count Distribution\n\n")
    f.write(f"### Before Filtering\n\n")
    f.write(f"- **Mean**: {df_raw['char_count'].mean():,.0f} characters\n")
    f.write(f"- **Median**: {df_raw['char_count'].median():,.0f} characters\n")
    f.write(f"- **Min**: {df_raw['char_count'].min():,} characters\n")
    f.write(f"- **Max**: {df_raw['char_count'].max():,} characters\n\n")

    f.write(f"### Percentiles\n\n")
    f.write("| Percentile | Character Count |\n")
    f.write("|------------|----------------|\n")
    for p in [50, 75, 90, 95, 99]:
        val = np.percentile(df_raw['char_count'], p)
        f.write(f"| {p}% | {val:,.0f} |\n")
    f.write("\n")

    f.write("## Cleaning Pipeline\n\n")
    f.write(f"### Step 1: Remove Zero-Length Documents\n\n")
    n_zero = (df_raw['char_count'] == 0).sum()
    f.write(f"- **Removed**: {n_zero:,} documents with zero characters\n\n")

    f.write(f"### Step 2: Apply 95th Percentile Cutoff\n\n")
    f.write(f"- **Cutoff**: {cutoff_95:,.0f} characters (95th percentile)\n")
    f.write(f"- **Removed**: {(df_raw['char_count'] > cutoff_95).sum():,} documents ({100 * (df_raw['char_count'] > cutoff_95).sum() / len(df_raw):.1f}%)\n")
    f.write(f"- **Rationale**: Remove extreme outliers (likely mis-extracted data)\n\n")

    f.write(f"### Step 3: Level-Based Deduplication\n\n")
    f.write(f"- **Strategy**: Prefer level=2 (individual sections) over level=1 (merged text) for duplicate rcept_no\n")
    f.write(f"- **Level=2 documents**: {n_level2:,} ({pct_level2:.1f}%)\n")
    f.write(f"- **Level=1 documents**: {n_level1:,} ({100-pct_level2:.1f}%)\n\n")

    f.write(f"### Step 4: Firm-Year Deduplication\n\n")
    f.write(f"- **Strategy**: Keep latest entry per firm-year (sorted by `rcept_dt`)\n")
    f.write(f"- **Duplicate firm-years**: {n_duplicates:,}\n")
    f.write(f"- **Duplicate documents removed**: {total_duplicate_docs:,}\n\n")

    f.write("## Clean Data Summary\n\n")
    f.write(f"### Panel Structure\n\n")
    f.write(f"- **Total observations**: {len(df_clean):,} firm-years\n")
    f.write(f"- **Unique firms**: {df_clean['stock_code'].nunique():,}\n")
    f.write(f"- **Year range**: {df_clean['year'].min()} - {df_clean['year'].max()}\n\n")

    f.write(f"### Observations per Year\n\n")
    f.write("| Year | Count |\n")
    f.write("|------|-------|\n")
    for year, count in year_counts.items():
        f.write(f"| {year} | {count:,} |\n")
    f.write("\n")

    f.write(f"### Character Count Statistics (After Cleaning)\n\n")
    f.write(f"- **Mean**: {df_clean['char_count'].mean():,.0f} characters\n")
    f.write(f"- **Median**: {df_clean['char_count'].median():,.0f} characters\n")
    f.write(f"- **Min**: {df_clean['char_count'].min():,} characters\n")
    f.write(f"- **Max**: {df_clean['char_count'].max():,} characters\n\n")

    f.write("## Output Files\n\n")
    f.write("- `data/korean_texts/business_descriptions_raw.parquet` - Raw MongoDB data\n")
    f.write("- `data/korean_texts/business_descriptions_clean.parquet` - Clean firm-year panel\n")
    f.write("- `data/korean_texts/text_samples.csv` - 20 random samples for inspection\n")
    f.write("- `data/korean_texts/char_count_distribution.png` - Distribution plot\n\n")

    f.write("## Next Steps\n\n")
    f.write("1. Proceed to Phase 2.1: Test Korean tokenization with kiwipiepy\n")

print(f"\n[OK] Saved report to: {report_path}")

# ==============================================================================
# Summary
# ==============================================================================

print("\n" + "=" * 80)
print("PHASE 1.2 COMPLETE")
print("=" * 80)

print(f"\n[SUMMARY]")
print(f"  Raw documents: {len(df_raw):,}")
print(f"  Clean firm-years: {len(df_clean):,}")
print(f"  Unique firms: {df_clean['stock_code'].nunique():,}")
print(f"  Year range: {df_clean['year'].min()} - {df_clean['year'].max()}")
print(f"  Avg char count: {df_clean['char_count'].mean():,.0f}")

print(f"\n[OUTPUT FILES]")
print(f"  {DATA_DIR / 'business_descriptions_raw.parquet'}")
print(f"  {DATA_DIR / 'business_descriptions_clean.parquet'}")
print(f"  {DATA_DIR / 'text_samples.csv'}")
print(f"  {DATA_DIR / 'char_count_distribution.png'}")
print(f"  {report_path}")

print(f"\n[NEXT STEP]")
print(f"  Run Phase 2.1: python scripts/test_korean_tokenization.py")

print("\n" + "=" * 80)
