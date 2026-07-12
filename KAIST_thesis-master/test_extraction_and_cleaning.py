"""
Test Phase 1 (Extraction) and Phase 1b (Cleaning) in Pipeline

This script tests the complete data extraction and cleaning flow.
"""

from pathlib import Path
from dotenv import load_dotenv
from tnic.pipeline import TNICPipeline

# Load environment variables
load_dotenv()

print("=" * 80)
print("TESTING PHASE 1 + PHASE 1b: EXTRACTION & CLEANING")
print("=" * 80)
print()

# Initialize pipeline
pipeline = TNICPipeline(config_path='./config')

# Run extraction and cleaning phases
print("Running Phase 1 (Extraction) and Phase 1b (Cleaning)...")
print("-" * 80)

result = pipeline.run(
    start_from_phase='extraction',
    force=True,
    validate_deps=False
)

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()

# Phase 1: Extraction
if 'extraction' in result:
    print("PHASE 1: EXTRACTION")
    print("-" * 80)
    if result['extraction']['status'] == 'success':
        print(f"[OK] Extraction completed successfully!")
        print(f"  Output: {result['extraction']['output']}")
        print(f"  Firm-years: {result['extraction']['n_firm_years']:,}")
    else:
        print(f"[ERROR] Extraction failed: {result['extraction'].get('error', 'Unknown error')}")
    print()

# Phase 1b: Cleaning
if 'cleaning' in result:
    print("PHASE 1b: CLEANING")
    print("-" * 80)
    if result['cleaning']['status'] == 'success':
        print(f"[OK] Cleaning completed successfully!")
        print()
        print(f"  Output: {result['cleaning']['output']}")
        print(f"  Stats file: {result['cleaning']['stats_file']}")
        print()
        print(f"  Initial documents: {result['cleaning']['n_initial']:,}")
        print(f"  Final documents: {result['cleaning']['n_final']:,}")
        print(f"  Document retention: {result['cleaning']['retention_rate_pct']:.1f}%")
        print()
        print(f"  Initial firms: {result['cleaning']['n_firms_initial']:,}")
        print(f"  Final firms: {result['cleaning']['n_firms_final']:,}")
        print(f"  Firm retention: {result['cleaning']['firm_retention_rate_pct']:.1f}%")
        print()
        print(f"  Removed zero-length: {result['cleaning']['n_removed_zero_length']:,}")
        print(f"  Truncated (95th percentile): {result['cleaning']['truncation_stats']['total_truncated']:,}")
        print(f"  Removed level dedup: {result['cleaning']['n_removed_level_dedup']:,}")
        print(f"  Removed firm-year dedup: {result['cleaning']['n_removed_firmyear_dedup']:,}")
    else:
        print(f"[ERROR] Cleaning failed: {result['cleaning'].get('error', 'Unknown error')}")
    print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
