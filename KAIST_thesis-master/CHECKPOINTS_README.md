# Checkpoint Caching System

This directory (`checkpoints/`) contains cached intermediate results from the main analysis script to dramatically speed up subsequent runs and enable fast iteration on Fama-MacBeth regressions.

## Quick Start

### First Run (Generate Checkpoints)

```bash
poetry run python text-based-industry-momentum-korea.py --save-checkpoints
```

**Time**: ~17 minutes (full analysis + checkpoint generation)
**Output**: 7 checkpoint files (~2.1 GB total) + manifest.json

### Subsequent Runs (Use Checkpoints)

```bash
poetry run python text-based-industry-momentum-korea.py
```

**Time**: ~3 minutes (skips 14-minute quintile calculation + TNIC building)
**Benefit**: 14+ minutes saved per run

### Validate Checkpoints

```bash
poetry run python text-based-industry-momentum-korea.py --validate-checkpoints
```

Checks file integrity against manifest hashes and reports any corrupted/missing files.

## Checkpoint Files

| Filename | Size | Description | Time Saved |
|----------|------|-------------|-----------|
| `checkpoint_01_quintiles.parquet` | ~680 MB | **CRITICAL**: Quintile rankings for FnGuide and TNIC peer returns | **14 minutes** |
| `checkpoint_02_tnic_peer_dict.pkl` | ~150 MB | TNIC peer lookup dictionary (stock → peers mapping) | 1 minute |
| `checkpoint_03_tnic_peer_returns.parquet` | ~180 MB | TNIC-based peer returns matrix | 51 seconds |
| `checkpoint_04_sic_peer_returns.parquet` | ~180 MB | SIC/FnGuide peer returns matrix | <1 second |
| `checkpoint_05_own_returns.parquet` | ~180 MB | Monthly stock returns (focal firms) | <1 second |
| `checkpoint_06_ff_controls.parquet` | ~720 MB | Fama-French control variables (log BE/ME, Size, past returns) | ~3 minutes |
| `checkpoint_07_universe.pkl` | ~5 MB | Universe definition by year (stock codes) | 28 seconds |

**Total**: ~2.1 GB

## How It Works

### Checkpoint Generation

When `--save-checkpoints` is provided:

1. **Run full analysis** as normal (17 minutes)
2. **Save intermediate results** at strategic points:
   - After peer returns calculation
   - After TNIC infrastructure building
   - **After quintile calculation** (14-minute bottleneck)
   - After Fama-French variables
3. **Generate manifest.json** with file hashes for validation

### Checkpoint Loading

Without `--save-checkpoints`:

- Script checks if checkpoints exist in `checkpoints/`
- If found, loads cached data and skips expensive recalculation
- If not found, calculates from scratch
- **Hash validation** ensures data integrity

### Hash Validation

The system uses MD5 hashes to detect:
- **File corruption** (damaged checkpoint files)
- **Stale data** (source data changed but checkpoint not regenerated)
- **Version mismatches** (different data range or TNIC files)

## When to Regenerate Checkpoints

Regenerate checkpoints (`--save-checkpoints`) when:

1. **Source data updated**:
   - FnGuide data refreshed (price, turnover, financials)
   - TNIC peer relationships recalculated
   - Date range extended

2. **Validation fails**:
   - `--validate-checkpoints` reports hash mismatches
   - Checkpoint files corrupted or incomplete

3. **Code changes** to checkpoint-generating sections:
   - Peer return calculation logic
   - Quintile assignment algorithm
   - Fama-French lag convention

4. **Fresh start**:
   - Delete `checkpoints/` directory
   - Run with `--save-checkpoints`

## Directory Structure

```
checkpoints/
├── checkpoint_01_quintiles.parquet          # Quintile rankings (CRITICAL)
├── checkpoint_01_quintiles.meta.json        # Metadata + hash
├── checkpoint_02_tnic_peer_dict.pkl          # TNIC lookup
├── checkpoint_02_tnic_peer_dict.meta.json
├── checkpoint_03_tnic_peer_returns.parquet
├── checkpoint_03_tnic_peer_returns.meta.json
├── checkpoint_04_sic_peer_returns.parquet
├── checkpoint_04_sic_peer_returns.meta.json
├── checkpoint_05_own_returns.parquet
├── checkpoint_05_own_returns.meta.json
├── checkpoint_06_ff_controls.parquet
├── checkpoint_06_ff_controls.meta.json
├── checkpoint_07_universe.pkl
├── checkpoint_07_universe.meta.json
└── manifest.json                            # Master manifest with all hashes
```

## File Formats

### Parquet Files (.parquet)

- **Use**: DataFrame-based data (returns, quintiles, controls)
- **Pros**: Fast I/O, automatic compression, preserves dtypes
- **Cons**: Requires pandas/pyarrow

### Pickle Files (.pkl)

- **Use**: Python objects (dicts, lists, complex structures)
- **Pros**: Preserves exact Python object structure
- **Cons**: Python-specific, not human-readable

### Metadata Files (.meta.json)

Each checkpoint has a `.meta.json` file containing:
```json
{
  "filename": "checkpoint_01_quintiles.parquet",
  "file_hash": "a1b2c3d4...",
  "file_size_mb": 680.5,
  "created_at": "2025-01-11T10:30:00",
  "data_type": "DataFrame",
  "shape": [189, 1700],
  "columns": ["A000020", "A000050", ...]
}
```

### Manifest File (manifest.json)

Master file tracking all checkpoints:
```json
{
  "created_at": "2025-01-11T10:30:00",
  "source_metadata": {
    "monthly_returns_range": "2010-01-31_2025-09-30",
    "tnic_data_hash": "e5f6g7h8...",
    "tnic_files_count": 16
  },
  "checkpoints": {
    "checkpoint_01_quintiles": {...},
    ...
  }
}
```

## Troubleshooting

### "Checkpoint not found" - Expected

On first run, no checkpoints exist yet. Run with `--save-checkpoints`.

### "Hash mismatch" Warning

**Cause**: Checkpoint file hash doesn't match manifest

**Fix**:
```bash
# Delete stale checkpoint
rm checkpoints/checkpoint_01_quintiles.parquet*

# Or regenerate all
rm -rf checkpoints/
poetry run python text-based-industry-momentum-korea.py --save-checkpoints
```

### "File corrupted" Warning

**Cause**: Checkpoint file damaged or incomplete

**Fix**: Same as hash mismatch - regenerate affected checkpoint or all checkpoints

### Disk Space Issues

**Total size**: ~2.1 GB

**To free space** (lose all caching benefits):
```bash
rm -rf checkpoints/
```

**To keep critical checkpoint only** (quintiles):
```bash
cd checkpoints/
ls | grep -v "checkpoint_01_quintiles" | xargs rm
# Keeps only quintiles (680 MB) - still saves 14 minutes
```

## Implementation Details

### checkpoint_utils.py

Core utility module providing:
- `save_checkpoint()` - Save data with automatic hashing
- `load_checkpoint()` - Load data with validation
- `compute_file_hash()` - MD5 hash computation
- `create_manifest()` - Generate manifest with metadata
- `validate_checkpoints()` - Integrity checking
- `compute_source_hash()` - Hash source data for staleness detection

### Integration Points

Checkpoints are saved at these locations in `text-based-industry-momentum-korea.py`:

1. **Line ~537**: Core returns (SIC peer returns, own returns)
2. **Line ~956**: Universe definition
3. **Line ~1090**: TNIC peer lookup dictionary
4. **Line ~1195**: TNIC peer returns
5. **Line ~1533**: **Quintile rankings** (CRITICAL - 14 minutes)
6. **Line ~1944**: Fama-French controls

## Advanced Usage

### Custom Checkpoint Directory

```bash
poetry run python text-based-industry-momentum-korea.py \
  --save-checkpoints \
  --checkpoint-dir my_custom_checkpoints/
```

### Jupyter Notebook Usage

Checkpoints work seamlessly in Jupyter:

```python
# In notebook cell
import sys
sys.argv = ['']  # Reset argv for argparse

# Run with default args (no checkpoint generation)
%run text-based-industry-momentum-korea.py

# To save checkpoints in Jupyter, modify args manually:
args.save_checkpoints = True
```

## Performance Benchmarks

### Full Run (No Checkpoints)

| Section | Time |
|---------|------|
| Initialize | 0.01 min |
| Load data | 0.52 min |
| TNIC building | 1.32 min |
| **Quintile calculation** | **13.95 min** |
| Fama-French controls | 0.15 min |
| Table 1 | 0.17 min |
| **TOTAL** | **17.41 min** |

### With Checkpoints (Second Run)

| Section | Time |
|---------|------|
| Initialize | 0.01 min |
| Load checkpoints | 0.05 min |
| Table 1 | 0.17 min |
| **TOTAL** | **~3 min** |

**Speedup**: 5.8×

## Best Practices

1. **Generate checkpoints immediately after successful full run**
   ```bash
   poetry run python text-based-industry-momentum-korea.py --save-checkpoints
   ```

2. **Validate before important analysis**
   ```bash
   poetry run python text-based-industry-momentum-korea.py --validate-checkpoints
   ```

3. **Regenerate after data updates**
   ```bash
   rm -rf checkpoints/
   poetry run python text-based-industry-momentum-korea.py --save-checkpoints
   ```

4. **Keep checkpoints/ in .gitignore**
   - Checkpoints are large (~2GB)
   - Easy to regenerate
   - Machine-specific (depends on local data)

5. **Document checkpoint versions**
   - Add git commit hash to manifest
   - Note data version/date range
   - Track code changes affecting checkpoints

## Future Enhancements

Potential improvements:

1. **Selective regeneration**: `--regenerate quintiles` to refresh only one checkpoint
2. **Compression**: Use xz/bz2 for smaller files (trade speed for space)
3. **Cloud storage**: Upload/download checkpoints from S3/GCS for team sharing
4. **Version control**: Track checkpoint versions aligned with git commits
5. **Partial loading**: Load only needed checkpoints for specific analyses

## Summary

Checkpoint caching transforms the analysis workflow:

**Before**: 17-minute wait for every regression iteration

**After**: 3-minute wait (14+ minutes saved)

**Key benefit**: Enables rapid iteration on Fama-MacBeth regressions (Tables 2-10) without re-running expensive Figure 1 calculations.
