"""
Show Korean text with proper encoding
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Set console encoding to UTF-8
if sys.platform == 'win32':
    # For Windows, set console to UTF-8
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

print("=" * 80)
print("KOREAN TEXT DISPLAY TEST")
print("=" * 80)

# Connect
client = MongoClient(f"mongodb://{MONGO_HOST}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Find a document with ~10k characters
target_size = 10000
tolerance = 2000

doc = collection.find_one({
    "section_code": "020100",
    "char_count": {"$gte": target_size - tolerance, "$lte": target_size + tolerance}
})

if doc:
    print(f"\nStock code: {doc.get('stock_code')}")
    print(f"Company: {doc.get('corp_name')}")
    print(f"Year: {doc.get('year')}")
    print(f"Section: {doc.get('section_title')}")
    print(f"Character count: {doc.get('char_count', len(doc.get('text', ''))):,}")

    # Get text
    text = doc.get('text', '')

    print(f"\n" + "=" * 80)
    print("TEXT (first 2000 characters):")
    print("=" * 80)

    # Print first 2000 characters
    print(text[:2000])

    print("\n" + "=" * 80)
    print("TEXT ENCODING INFO:")
    print("=" * 80)
    print(f"Text type: {type(text)}")
    print(f"Text length: {len(text)}")

    # Try to detect encoding issues
    try:
        # Check if it's already UTF-8
        if isinstance(text, str):
            print("Text is already a Python string (should be UTF-8)")
            # Show first few characters in different representations
            sample = text[:100]
            print(f"\nFirst 100 chars:")
            print(sample)
            print(f"\nUnicode repr (first 50):")
            print(repr(sample[:50]))
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No document found")

# Show a few more samples
print("\n" + "=" * 80)
print("ADDITIONAL SAMPLES (short excerpts)")
print("=" * 80)

samples = list(collection.find(
    {"section_code": "020100", "char_count": {"$gte": 1000, "$lte": 3000}},
    {"stock_code": 1, "corp_name": 1, "year": 1, "text": 1}
).limit(5))

for i, doc in enumerate(samples, 1):
    print(f"\n--- Sample {i} ---")
    print(f"Stock: {doc.get('stock_code')} - {doc.get('corp_name')} ({doc.get('year')})")
    text = doc.get('text', '')
    print(f"Text preview (200 chars):")
    print(text[:200])

print("\n" + "=" * 80)
