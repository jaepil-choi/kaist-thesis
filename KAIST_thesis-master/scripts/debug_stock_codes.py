"""
Debug script to investigate stock code mismatch between MongoDB and FnGuide
"""

import os
from pathlib import Path
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

print("=" * 80)
print("DEBUGGING STOCK CODE MISMATCH")
print("=" * 80)

# Connect to MongoDB
client = MongoClient(f"mongodb://{MONGO_HOST}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Get sample stock codes from MongoDB
mongo_docs = list(collection.find({"section_code": "020100"}, {"stock_code": 1, "corp_name": 1}).limit(20))
mongo_codes = [doc['stock_code'] for doc in mongo_docs if 'stock_code' in doc]

print(f"\n1. MongoDB stock codes (first 20):")
for i, doc in enumerate(mongo_docs[:20], 1):
    code = doc.get('stock_code', 'N/A')
    name = doc.get('corp_name', 'N/A')
    print(f"   {i:2d}. {code:15s} - {name}")
    # Show code properties
    if code != 'N/A':
        print(f"       Type: {type(code)}, Length: {len(str(code))}, Repr: {repr(code)}")

# Load FnGuide data
fnguide_path = Path("data/fnguide/processed/dataguide_filtered.parquet")
if fnguide_path.exists():
    fnguide = pd.read_parquet(fnguide_path)

    print(f"\n2. FnGuide stock symbols (first 20):")
    unique_symbols = fnguide['symbol'].unique()[:20]
    for i, symbol in enumerate(unique_symbols, 1):
        # Get company name
        name = fnguide[fnguide['symbol'] == symbol]['symbol_name'].iloc[0]
        print(f"   {i:2d}. {symbol:15s} - {name}")
        # Show code properties
        print(f"       Type: {type(symbol)}, Length: {len(str(symbol))}, Repr: {repr(symbol)}")

    print(f"\n3. Checking specific codes:")
    # Check if "000020" (from sample) exists in either dataset
    test_code = "000020"

    mongo_has = test_code in [str(doc.get('stock_code', '')) for doc in mongo_docs]
    fnguide_has = test_code in fnguide['symbol'].astype(str).values

    print(f"   Test code: '{test_code}'")
    print(f"   In MongoDB: {mongo_has}")
    print(f"   In FnGuide: {fnguide_has}")

    # Try to find similar codes
    print(f"\n4. FnGuide symbols starting with '000':")
    fnguide_000 = fnguide[fnguide['symbol'].astype(str).str.startswith('000')]['symbol'].unique()[:10]
    for sym in fnguide_000:
        name = fnguide[fnguide['symbol'] == sym]['symbol_name'].iloc[0]
        print(f"      {sym} - {name}")

    print(f"\n5. Data types:")
    print(f"   MongoDB stock_code type: {type(mongo_docs[0]['stock_code']) if mongo_docs else 'N/A'}")
    print(f"   FnGuide symbol type: {fnguide['symbol'].dtype}")

    # Check if numeric vs string
    print(f"\n6. Format analysis:")
    print(f"   MongoDB codes are numeric: {all(str(c).isdigit() for c in mongo_codes if c)}")
    print(f"   FnGuide symbols are numeric: {fnguide['symbol'].astype(str).str.isdigit().all()}")

    # Show sample conversions
    print(f"\n7. Potential format issues:")
    print(f"   MongoDB '000020' as int: {int('000020')} (leading zeros lost!)")
    print(f"   MongoDB '000020' as str: {'000020'}")

    # Check if MongoDB codes are stored as integers
    if mongo_docs:
        sample_code = mongo_docs[0]['stock_code']
        if isinstance(sample_code, int):
            print(f"\n   [PROBLEM FOUND] MongoDB stores stock_code as INTEGER")
            print(f"   Example: {sample_code} should be {sample_code:06d}")
            print(f"   Solution: Convert to 6-digit zero-padded string")
else:
    print(f"\n   FnGuide data not found")

print(f"\n" + "=" * 80)
