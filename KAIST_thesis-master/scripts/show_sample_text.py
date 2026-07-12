"""
Show sample text from a document with ~10k characters
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

# Connect
client = MongoClient(f"mongodb://{MONGO_HOST}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Find a document with char_count around 10,000
target_size = 10000
tolerance = 2000

doc = collection.find_one({
    "section_code": "020100",
    "char_count": {"$gte": target_size - tolerance, "$lte": target_size + tolerance}
})

if doc:
    print("=" * 80)
    print("SAMPLE DOCUMENT (~10k characters)")
    print("=" * 80)
    print(f"\nStock code: {doc.get('stock_code')}")
    print(f"Company: {doc.get('corp_name')}")
    print(f"Year: {doc.get('year')}")
    print(f"Section: {doc.get('section_title')}")
    print(f"Character count: {doc.get('char_count', len(doc.get('text', ''))):,}")
    print(f"\n" + "=" * 80)
    print("FULL TEXT:")
    print("=" * 80)
    print(doc.get('text', ''))
    print("\n" + "=" * 80)
else:
    print("No document found in target range")
