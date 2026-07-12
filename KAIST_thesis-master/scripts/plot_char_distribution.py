"""
Plot character count distribution of Korean business descriptions
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FS")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "A001")

# Output directory
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("CHARACTER COUNT DISTRIBUTION ANALYSIS")
print("=" * 80)

# Connect to MongoDB
print(f"\nConnecting to MongoDB...")
client = MongoClient(f"mongodb://{MONGO_HOST}/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Retrieve business descriptions
print(f"Retrieving business descriptions (section_code: 020100)...")
docs = list(collection.find(
    {"section_code": "020100"},
    {"stock_code": 1, "corp_name": 1, "year": 1, "char_count": 1, "text": 1}
))

print(f"Retrieved {len(docs):,} documents")

# Extract character counts
char_counts = []
for doc in docs:
    # Use char_count field if available, otherwise calculate from text
    if 'char_count' in doc and doc['char_count']:
        char_counts.append(doc['char_count'])
    elif 'text' in doc:
        char_counts.append(len(doc['text']))

char_counts = np.array(char_counts)

print(f"\n" + "=" * 80)
print("STATISTICS")
print("=" * 80)

print(f"\nTotal documents: {len(char_counts):,}")
print(f"Mean: {char_counts.mean():.0f} characters")
print(f"Median: {np.median(char_counts):.0f} characters")
print(f"Std Dev: {char_counts.std():.0f} characters")
print(f"Min: {char_counts.min():,} characters")
print(f"Max: {char_counts.max():,} characters")

# Percentiles
print(f"\nPercentiles:")
for p in [10, 25, 50, 75, 90, 95, 99]:
    val = np.percentile(char_counts, p)
    print(f"  {p:2d}th: {val:10,.0f} characters")

# Distribution by bins
print(f"\nDistribution by size:")
bins = [0, 500, 1000, 2000, 5000, 10000, 50000, float('inf')]
labels = ['<500', '500-1k', '1k-2k', '2k-5k', '5k-10k', '10k-50k', '>50k']
counts = pd.cut(char_counts, bins=bins, labels=labels).value_counts().sort_index()
for label, count in counts.items():
    pct = 100 * count / len(char_counts)
    print(f"  {label:>10s}: {count:5,} ({pct:5.1f}%)")

# Create plots
print(f"\n" + "=" * 80)
print("CREATING PLOTS")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Korean Business Description - Character Count Distribution',
             fontsize=14, fontweight='bold')

# Plot 1: Histogram (full range)
ax1 = axes[0, 0]
ax1.hist(char_counts, bins=50, edgecolor='black', alpha=0.7, color='skyblue')
ax1.set_xlabel('Character Count')
ax1.set_ylabel('Frequency')
ax1.set_title(f'Distribution (Full Range)\nn={len(char_counts):,} documents')
ax1.grid(True, alpha=0.3)

# Add mean and median lines
ax1.axvline(char_counts.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {char_counts.mean():.0f}')
ax1.axvline(np.median(char_counts), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(char_counts):.0f}')
ax1.legend()

# Plot 2: Histogram (zoomed to < 20k chars for better detail)
ax2 = axes[0, 1]
filtered = char_counts[char_counts < 20000]
ax2.hist(filtered, bins=50, edgecolor='black', alpha=0.7, color='lightcoral')
ax2.set_xlabel('Character Count')
ax2.set_ylabel('Frequency')
ax2.set_title(f'Distribution (< 20k chars, zoomed)\nn={len(filtered):,} documents ({100*len(filtered)/len(char_counts):.1f}%)')
ax2.grid(True, alpha=0.3)

# Add mean and median for filtered
ax2.axvline(filtered.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {filtered.mean():.0f}')
ax2.axvline(np.median(filtered), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(filtered):.0f}')
ax2.legend()

# Plot 3: Log scale histogram
ax3 = axes[1, 0]
# Add 1 to avoid log(0)
ax3.hist(char_counts + 1, bins=50, edgecolor='black', alpha=0.7, color='lightgreen')
ax3.set_xlabel('Character Count')
ax3.set_ylabel('Frequency')
ax3.set_title('Distribution (Log Scale)')
ax3.set_xscale('log')
ax3.grid(True, alpha=0.3, which='both')

# Plot 4: Box plot
ax4 = axes[1, 1]
bp = ax4.boxplot([char_counts], vert=True, patch_artist=True,
                  labels=['All Documents'],
                  showmeans=True, meanline=True)
bp['boxes'][0].set_facecolor('lightblue')
ax4.set_ylabel('Character Count')
ax4.set_title('Box Plot (showing outliers)')
ax4.grid(True, alpha=0.3, axis='y')

# Add statistics text
stats_text = f"Mean: {char_counts.mean():.0f}\nMedian: {np.median(char_counts):.0f}\nStd: {char_counts.std():.0f}"
ax4.text(1.15, np.median(char_counts), stats_text, fontsize=10,
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()

# Save plot
output_path = OUTPUT_DIR / "char_count_distribution.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n[OK] Saved plot to: {output_path}")

# Show plot
plt.show()

# Additional analysis: Identify outliers
print(f"\n" + "=" * 80)
print("OUTLIERS (>100k characters)")
print("=" * 80)

outliers = [(doc['stock_code'], doc['corp_name'], doc['year'], doc.get('char_count', len(doc.get('text', ''))))
            for doc in docs
            if (doc.get('char_count', len(doc.get('text', ''))) > 100000)]

if outliers:
    print(f"\nFound {len(outliers)} documents with >100k characters:")
    for stock_code, corp_name, year, count in sorted(outliers, key=lambda x: -x[3])[:20]:
        print(f"  {stock_code} - {year}: {count:,} chars")
else:
    print(f"\nNo documents with >100k characters")

print(f"\n" + "=" * 80)
print("DONE")
print("=" * 80)
