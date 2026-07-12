"""
Simple MongoDB data check - just retrieve and display
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

print("=" * 80)
print("MONGODB CONNECTION CHECK")
print("=" * 80)

# Connect
print(f"\nConnecting to: mongodb://{MONGO_HOST}/")
print(f"Database: {DB_NAME}")
print(f"Collection: {COLLECTION_NAME}")

client = MongoClient(f"mongodb://{MONGO_HOST}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Count total documents
total = collection.count_documents({})
print(f"\nTotal documents: {total:,}")

# Check section codes
section_codes = collection.distinct("section_code")
print(f"\nSection codes: {section_codes}")

# Count business overview section (020100)
business_count = collection.count_documents({"section_code": "020100"})
print(f"Business overview documents (020100): {business_count:,}")

# Get a few sample documents
print("\n" + "=" * 80)
print("SAMPLE DOCUMENTS (first 5)")
print("=" * 80)

samples = list(collection.find({"section_code": "020100"}).limit(5))

for i, doc in enumerate(samples, 1):
    print(f"\n--- Document {i} ---")
    print(f"Stock code: {doc.get('stock_code')}")
    print(f"Company: {doc.get('corp_name')}")
    print(f"Year: {doc.get('year')}")
    print(f"Section: {doc.get('section_title')}")
    print(f"Text length: {len(doc.get('text', ''))} characters")
    print(f"Text preview: {doc.get('text', '')[:200]}...")

# Year distribution
print("\n" + "=" * 80)
print("YEAR DISTRIBUTION")
print("=" * 80)

pipeline = [
    {"$match": {"section_code": "020100"}},
    {"$group": {"_id": "$year", "count": {"$sum": 1}}},
    {"$sort": {"_id": 1}}
]

year_counts = list(collection.aggregate(pipeline))
for item in year_counts:
    print(f"  {item['_id']}: {item['count']:,} documents")

# Unique firms
unique_firms = len(collection.distinct("stock_code", {"section_code": "020100"}))
print(f"\nUnique firms: {unique_firms:,}")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
