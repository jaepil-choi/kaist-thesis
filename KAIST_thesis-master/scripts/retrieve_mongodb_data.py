"""
MongoDB Data Retrieval Script

Retrieves Korean business descriptions from MongoDB (DART financial reports)
for use in Hoberg & Phillips TNIC replication.

Usage:
    python scripts/retrieve_mongodb_data.py
"""

import os
from pathlib import Path
from typing import Dict, List
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

# Output directory
OUTPUT_DIR = Path("data/korean_texts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("MONGODB DATA RETRIEVAL - DART BUSINESS DESCRIPTIONS")
print("=" * 80)

# ============================================================================
# 1. CONNECT TO MONGODB
# ============================================================================
print(f"\n1. Connecting to MongoDB...")
print(f"   Host: {MONGO_HOST}")
print(f"   Database: {DB_NAME}")
print(f"   Collection: {COLLECTION_NAME}")

try:
    client = MongoClient(f"mongodb://{MONGO_HOST}/")
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Test connection
    total_docs = collection.count_documents({})
    print(f"   [OK] Connected successfully")
    print(f"   Total documents in collection: {total_docs:,}")

except Exception as e:
    print(f"   [ERROR] Connection failed: {e}")
    exit(1)

# ============================================================================
# 2. EXPLORE DATA STRUCTURE
# ============================================================================
print(f"\n2. Exploring data structure...")

# Get sample document
sample_doc = collection.find_one()
if sample_doc:
    print(f"   Available fields: {list(sample_doc.keys())}")

    # Check if structure matches our expectation
    expected_fields = ['stock_code', 'corp_name', 'year', 'section_code', 'section_title', 'text']
    missing_fields = [f for f in expected_fields if f not in sample_doc]

    if missing_fields:
        print(f"   [WARNING] Missing expected fields: {missing_fields}")
        print(f"   Sample document keys: {sample_doc.keys()}")
    else:
        print(f"   [OK] All expected fields present")

    # Show sample document structure
    if 'stock_code' in sample_doc:
        print(f"\n   Sample document:")
        print(f"     stock_code: {sample_doc.get('stock_code')}")
        print(f"     corp_name: {sample_doc.get('corp_name')}")
        print(f"     year: {sample_doc.get('year')}")
        print(f"     section_code: {sample_doc.get('section_code')}")
        print(f"     section_title: {sample_doc.get('section_title')}")
        if 'text' in sample_doc:
            text_preview = sample_doc.get('text', '')[:100]
            print(f"     text: {text_preview}...")
            print(f"     text length: {len(sample_doc.get('text', ''))} chars")
else:
    print(f"   [ERROR] No documents found in collection")
    exit(1)

# Check available section codes
print(f"\n3. Analyzing section codes...")
section_codes = collection.distinct("section_code")
print(f"   Unique section codes: {len(section_codes)}")
print(f"   Section codes: {sorted(section_codes)[:10]}...")  # Show first 10

# Count documents by section code
section_counts = {}
for code in section_codes:
    count = collection.count_documents({"section_code": code})
    section_counts[code] = count

# Find business overview section (usually 020100 or similar)
business_section_candidates = [
    code for code in section_codes
    if code.startswith("02") or "사업" in collection.find_one({"section_code": code}, {"section_title": 1}).get("section_title", "")
]

print(f"   Business-related sections: {business_section_candidates[:5]}")

# Check if section_code 020100 exists (business overview)
business_section = "020100"
business_count = section_counts.get(business_section, 0)

if business_count > 0:
    print(f"\n   [OK] Found business overview section: {business_section}")
    print(f"     Documents: {business_count:,}")

    # Show sample title
    sample_business = collection.find_one({"section_code": business_section})
    if sample_business:
        print(f"     Sample title: {sample_business.get('section_title', 'N/A')}")
else:
    print(f"\n   [WARNING] Section {business_section} not found")
    print(f"     Available sections with counts:")
    for code, count in sorted(section_counts.items(), key=lambda x: -x[1])[:10]:
        sample = collection.find_one({"section_code": code})
        title = sample.get('section_title', 'N/A') if sample else 'N/A'
        print(f"       {code}: {count:,} docs - {title}")

    # Ask user to specify correct section code
    print(f"\n   Please update business_section variable in script if needed.")
    business_section = input("   Enter business overview section code (or press Enter for '020100'): ").strip() or "020100"

# ============================================================================
# 4. QUERY BUSINESS DESCRIPTIONS
# ============================================================================
print(f"\n4. Querying business descriptions (section_code: {business_section})...")

query = {"section_code": business_section}
business_docs = list(collection.find(query))

print(f"   Retrieved {len(business_docs):,} documents")

if len(business_docs) == 0:
    print(f"   [ERROR] No documents found with section_code={business_section}")
    print(f"   Please check section codes above and update the script.")
    exit(1)

# Convert to DataFrame for analysis
df = pd.DataFrame(business_docs)
print(f"\n   DataFrame shape: {df.shape}")
print(f"   Columns: {list(df.columns)}")

# ============================================================================
# 5. DATA QUALITY CHECKS
# ============================================================================
print(f"\n5. Data quality checks...")

# Check for required fields
required_fields = ['stock_code', 'corp_name', 'year', 'text']
for field in required_fields:
    if field in df.columns:
        missing = df[field].isna().sum()
        print(f"   {field}: {len(df) - missing:,} / {len(df):,} ({100 * (len(df) - missing) / len(df):.1f}% complete)")
        if missing > 0:
            print(f"     [WARNING] {missing} missing values")
    else:
        print(f"   [ERROR] {field}: NOT FOUND IN DATA")

# Text length statistics
if 'text' in df.columns:
    df['text_length'] = df['text'].fillna('').apply(len)
    print(f"\n   Text length statistics:")
    print(f"     Mean: {df['text_length'].mean():.0f} characters")
    print(f"     Median: {df['text_length'].median():.0f} characters")
    print(f"     Min: {df['text_length'].min()} characters")
    print(f"     Max: {df['text_length'].max():,} characters")
    print(f"     Empty texts: {(df['text_length'] == 0).sum()}")

    # Histogram
    print(f"\n   Text length distribution:")
    bins = [0, 500, 1000, 2000, 5000, 10000, float('inf')]
    labels = ['<500', '500-1k', '1k-2k', '2k-5k', '5k-10k', '>10k']
    df['text_length_bin'] = pd.cut(df['text_length'], bins=bins, labels=labels)
    print(df['text_length_bin'].value_counts().sort_index())

# Year coverage
if 'year' in df.columns:
    print(f"\n   Year coverage:")
    year_counts = df['year'].value_counts().sort_index()
    print(f"     Years: {df['year'].min()} to {df['year'].max()}")
    print(f"     Documents per year:")
    for year, count in year_counts.items():
        print(f"       {year}: {count:,} firms")

# Unique firms
if 'stock_code' in df.columns:
    unique_firms = df['stock_code'].nunique()
    print(f"\n   Unique firms (stock_code): {unique_firms:,}")

    # Firms per year
    if 'year' in df.columns:
        firms_per_year = df.groupby('year')['stock_code'].nunique()
        print(f"     Mean firms per year: {firms_per_year.mean():.0f}")
        print(f"     Range: {firms_per_year.min()} to {firms_per_year.max()}")

# ============================================================================
# 6. MATCH WITH FNGUIDE DATA
# ============================================================================
print(f"\n6. Matching with FnGuide data...")

fnguide_path = Path("data/fnguide/processed/dataguide_filtered.parquet")
if fnguide_path.exists():
    try:
        fnguide = pd.read_parquet(fnguide_path)
        print(f"   [OK] Loaded FnGuide data: {len(fnguide):,} rows, {fnguide['symbol'].nunique():,} unique symbols")

        # Match stock codes
        # NOTE: FnGuide prefixes codes with 'A' (KOSPI) or 'Q' (KOSDAQ)
        # MongoDB has pure numeric codes
        if 'stock_code' in df.columns:
            mongo_codes = set(df['stock_code'].dropna().unique())

            # Add 'A' prefix to MongoDB codes to match FnGuide format
            mongo_codes_with_prefix = {'A' + code for code in mongo_codes}

            fnguide_codes = set(fnguide['symbol'].dropna().unique())

            overlap = mongo_codes_with_prefix & fnguide_codes
            only_mongo = mongo_codes_with_prefix - fnguide_codes
            only_fnguide = fnguide_codes - mongo_codes_with_prefix

            # Create mapping: MongoDB code -> FnGuide symbol
            df['symbol'] = 'A' + df['stock_code']

            print(f"\n   Match results:")
            print(f"     Firms in both datasets: {len(overlap):,} ({100 * len(overlap) / len(mongo_codes):.1f}% of MongoDB)")
            print(f"     Only in MongoDB: {len(only_mongo):,}")
            print(f"     Only in FnGuide: {len(only_fnguide):,}")

            # Filter to matched firms only
            df_matched = df[df['symbol'].isin(overlap)].copy()
            print(f"\n   Filtered to matched firms: {len(df_matched):,} documents")
            print(f"     Unique firms: {df_matched['stock_code'].nunique():,} ({df_matched['symbol'].nunique():,} with 'A' prefix)")

            # Save match statistics
            match_stats = pd.DataFrame({
                'total_mongo_firms': [len(mongo_codes)],
                'total_fnguide_firms': [len(fnguide_codes)],
                'matched_firms': [len(overlap)],
                'only_mongo': [len(only_mongo)],
                'only_fnguide': [len(only_fnguide)],
                'match_rate': [100 * len(overlap) / len(mongo_codes)]
            })
            match_stats.to_csv(OUTPUT_DIR / "match_statistics.csv", index=False)
            print(f"   [OK] Saved match statistics to: {OUTPUT_DIR / 'match_statistics.csv'}")

        else:
            print(f"   [WARNING] Cannot match: stock_code field not found")
            df_matched = df.copy()

    except Exception as e:
        print(f"   [WARNING] Could not load FnGuide data: {e}")
        print(f"   Proceeding without matching...")
        df_matched = df.copy()
else:
    print(f"   [WARNING] FnGuide data not found at: {fnguide_path}")
    print(f"   Proceeding without matching...")
    df_matched = df.copy()

# ============================================================================
# 7. SAVE EXTRACTED DATA
# ============================================================================
print(f"\n7. Saving extracted data...")

# Convert MongoDB ObjectId to string for parquet compatibility
if '_id' in df_matched.columns:
    df_matched['_id'] = df_matched['_id'].astype(str)
if 'parsed_at' in df_matched.columns:
    df_matched['parsed_at'] = df_matched['parsed_at'].astype(str)

# Save complete dataset as parquet
output_path = OUTPUT_DIR / "business_descriptions.parquet"
df_matched.to_parquet(output_path, index=False)
print(f"   [OK] Saved complete dataset: {output_path}")
print(f"     Shape: {df_matched.shape}")

# Save as CSV (smaller sample for inspection)
csv_path = OUTPUT_DIR / "business_descriptions_sample.csv"
sample_size = min(100, len(df_matched))
df_matched.head(sample_size).to_csv(csv_path, index=False)
print(f"   [OK] Saved sample (first {sample_size} rows): {csv_path}")

# Save summary statistics
summary_stats = pd.DataFrame({
    'metric': [
        'total_documents',
        'unique_firms',
        'unique_years',
        'year_min',
        'year_max',
        'mean_text_length',
        'median_text_length',
        'empty_texts'
    ],
    'value': [
        len(df_matched),
        df_matched['stock_code'].nunique() if 'stock_code' in df_matched.columns else 0,
        df_matched['year'].nunique() if 'year' in df_matched.columns else 0,
        df_matched['year'].min() if 'year' in df_matched.columns else None,
        df_matched['year'].max() if 'year' in df_matched.columns else None,
        df_matched['text_length'].mean() if 'text_length' in df_matched.columns else 0,
        df_matched['text_length'].median() if 'text_length' in df_matched.columns else 0,
        (df_matched['text_length'] == 0).sum() if 'text_length' in df_matched.columns else 0
    ]
})
summary_stats.to_csv(OUTPUT_DIR / "summary_statistics.csv", index=False)
print(f"   [OK] Saved summary statistics: {OUTPUT_DIR / 'summary_statistics.csv'}")

# Save by firm-year for easy lookup
if 'stock_code' in df_matched.columns and 'year' in df_matched.columns:
    # Create firm-year pivot
    df_pivot = df_matched.copy()

    # For duplicate firm-year pairs, keep the one with longest text
    if 'text_length' not in df_pivot.columns:
        df_pivot['text_length'] = df_pivot['text'].fillna('').apply(len)

    df_pivot = df_pivot.sort_values('text_length', ascending=False)
    df_pivot = df_pivot.drop_duplicates(subset=['stock_code', 'year'], keep='first')

    duplicates_removed = len(df_matched) - len(df_pivot)
    if duplicates_removed > 0:
        print(f"   [INFO] Removed {duplicates_removed} duplicate firm-year pairs (kept longest text)")

    # Save
    pivot_path = OUTPUT_DIR / "business_descriptions_by_firm_year.parquet"
    df_pivot.to_parquet(pivot_path, index=False)
    print(f"   [OK] Saved firm-year dataset: {pivot_path}")
    print(f"     Shape: {df_pivot.shape}")

# ============================================================================
# 8. GENERATE REPORT
# ============================================================================
print(f"\n" + "=" * 80)
print("DATA RETRIEVAL COMPLETE")
print("=" * 80)

print(f"\nSummary:")
print(f"  Total documents retrieved: {len(df_matched):,}")
print(f"  Unique firms: {df_matched['stock_code'].nunique() if 'stock_code' in df_matched.columns else 'N/A'}")
print(f"  Year range: {df_matched['year'].min() if 'year' in df_matched.columns else 'N/A'} to {df_matched['year'].max() if 'year' in df_matched.columns else 'N/A'}")
print(f"  Mean text length: {df_matched['text_length'].mean():.0f} characters" if 'text_length' in df_matched.columns else "")

print(f"\nOutput files:")
print(f"  {OUTPUT_DIR / 'business_descriptions.parquet'}")
print(f"  {OUTPUT_DIR / 'business_descriptions_by_firm_year.parquet'}")
print(f"  {OUTPUT_DIR / 'summary_statistics.csv'}")
print(f"  {OUTPUT_DIR / 'match_statistics.csv'}" if fnguide_path.exists() else "")

print(f"\nNext steps:")
print(f"  1. Review summary_statistics.csv")
print(f"  2. Inspect business_descriptions_sample.csv")
print(f"  3. Run Korean text preprocessing (to be developed)")

print(f"\n" + "=" * 80)
