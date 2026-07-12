"""
Checkpoint management utilities for caching expensive intermediate results.

Provides functions to save/load checkpoints with hash-based validation
to ensure data consistency across runs.
"""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime

import pandas as pd
import numpy as np


def compute_file_hash(filepath: Union[str, Path], algorithm: str = 'md5') -> str:
    """
    Compute hash of a file for validation.

    Parameters:
    -----------
    filepath : str or Path
        Path to file to hash
    algorithm : str
        Hash algorithm ('md5', 'sha256', etc.)

    Returns:
    --------
    str
        Hex digest of file hash
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    hash_obj = hashlib.new(algorithm)

    # Read file in chunks to handle large files
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def compute_dataframe_hash(df: pd.DataFrame, algorithm: str = 'md5') -> str:
    """
    Compute hash of DataFrame contents for validation.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame to hash
    algorithm : str
        Hash algorithm

    Returns:
    --------
    str
        Hex digest of DataFrame hash
    """
    hash_obj = hashlib.new(algorithm)

    # Hash shape
    hash_obj.update(str(df.shape).encode())

    # Hash index (first, last, and length to avoid hashing entire index)
    if len(df) > 0:
        hash_obj.update(str(df.index[0]).encode())
        hash_obj.update(str(df.index[-1]).encode())
    hash_obj.update(str(len(df)).encode())

    # Hash column names
    hash_obj.update(str(df.columns.tolist()).encode())

    # Hash sample of values (for speed)
    if len(df) > 0 and len(df.columns) > 0:
        # Sample 100 random cells
        n_samples = min(100, df.size)
        sample_indices = np.random.choice(df.size, n_samples, replace=False)
        flat_values = df.values.flatten()
        for idx in sample_indices:
            val = flat_values[idx]
            if pd.notna(val):
                hash_obj.update(str(val).encode())

    return hash_obj.hexdigest()


def save_checkpoint(
    data: Union[pd.DataFrame, Dict, Any],
    filename: str,
    checkpoint_dir: Union[str, Path] = 'checkpoints',
    metadata: Optional[Dict] = None
) -> Path:
    """
    Save data to checkpoint file.

    Parameters:
    -----------
    data : DataFrame, dict, or pickle-able object
        Data to save
    filename : str
        Checkpoint filename (with extension)
    checkpoint_dir : str or Path
        Directory for checkpoints
    metadata : dict, optional
        Additional metadata to include

    Returns:
    --------
    Path
        Path to saved checkpoint file
    """
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(exist_ok=True)

    filepath = checkpoint_dir / filename

    # Save based on file extension
    if filename.endswith('.parquet'):
        if not isinstance(data, pd.DataFrame):
            raise TypeError(f"Parquet format requires DataFrame, got {type(data)}")
        data.to_parquet(filepath, compression='snappy')

    elif filename.endswith('.pkl') or filename.endswith('.pickle'):
        with open(filepath, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    elif filename.endswith('.csv'):
        if not isinstance(data, pd.DataFrame):
            raise TypeError(f"CSV format requires DataFrame, got {type(data)}")
        data.to_csv(filepath)

    else:
        raise ValueError(f"Unsupported file extension: {filename}")

    # Compute hash of saved file
    file_hash = compute_file_hash(filepath)

    # Save metadata
    meta_path = filepath.with_suffix('.meta.json')
    meta = {
        'filename': filename,
        'file_hash': file_hash,
        'file_size_mb': filepath.stat().st_size / 1e6,
        'created_at': datetime.now().isoformat(),
        'data_type': str(type(data).__name__)
    }

    if isinstance(data, pd.DataFrame):
        meta['shape'] = list(data.shape)
        meta['columns'] = list(data.columns[:10])  # First 10 columns only

    if metadata:
        meta.update(metadata)

    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"  [SAVED] {filename} ({meta['file_size_mb']:.1f} MB, hash: {file_hash[:8]}...)")

    return filepath


def load_checkpoint(
    filename: str,
    checkpoint_dir: Union[str, Path] = 'checkpoints',
    validate_hash: bool = True,
    expected_hash: Optional[str] = None
) -> Optional[Any]:
    """
    Load data from checkpoint file with optional hash validation.

    Parameters:
    -----------
    filename : str
        Checkpoint filename
    checkpoint_dir : str or Path
        Directory for checkpoints
    validate_hash : bool
        Whether to validate file hash against metadata
    expected_hash : str, optional
        Expected file hash (from manifest)

    Returns:
    --------
    Data from checkpoint, or None if not found/invalid
    """
    checkpoint_dir = Path(checkpoint_dir)
    filepath = checkpoint_dir / filename

    if not filepath.exists():
        return None

    # Load metadata
    meta_path = filepath.with_suffix('.meta.json')
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # Validate hash if requested
    if validate_hash:
        stored_hash = metadata.get('file_hash')
        if expected_hash and stored_hash != expected_hash:
            print(f"  [WARNING] Hash mismatch for {filename}: expected {expected_hash[:8]}, got {stored_hash[:8]}")
            print(f"            Checkpoint may be stale. Consider regenerating with --save-checkpoints")
            return None

        # Recompute hash and compare
        current_hash = compute_file_hash(filepath)
        if stored_hash and current_hash != stored_hash:
            print(f"  [WARNING] File corrupted: {filename}")
            print(f"            Expected hash {stored_hash[:8]}, got {current_hash[:8]}")
            return None

    # Load data
    try:
        if filename.endswith('.parquet'):
            data = pd.read_parquet(filepath)

        elif filename.endswith('.pkl') or filename.endswith('.pickle'):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)

        elif filename.endswith('.csv'):
            data = pd.read_csv(filepath, index_col=0)

        else:
            raise ValueError(f"Unsupported file extension: {filename}")

        file_size_mb = filepath.stat().st_size / 1e6
        print(f"  [LOADED] {filename} ({file_size_mb:.1f} MB)")

        return data

    except Exception as e:
        print(f"  [ERROR] Failed to load {filename}: {e}")
        return None


def checkpoint_exists(
    filename: str,
    checkpoint_dir: Union[str, Path] = 'checkpoints'
) -> bool:
    """Check if checkpoint file exists."""
    checkpoint_dir = Path(checkpoint_dir)
    return (checkpoint_dir / filename).exists()


def create_manifest(
    checkpoint_dir: Union[str, Path] = 'checkpoints',
    source_metadata: Optional[Dict] = None
) -> Dict:
    """
    Create manifest.json with all checkpoint metadata and source hashes.

    Parameters:
    -----------
    checkpoint_dir : str or Path
        Directory containing checkpoints
    source_metadata : dict, optional
        Metadata about source data (date ranges, file hashes, etc.)

    Returns:
    --------
    dict
        Manifest data
    """
    checkpoint_dir = Path(checkpoint_dir)

    manifest = {
        'created_at': datetime.now().isoformat(),
        'source_metadata': source_metadata or {},
        'checkpoints': {}
    }

    # Collect metadata from all .meta.json files
    for meta_path in sorted(checkpoint_dir.glob('*.meta.json')):
        with open(meta_path, 'r') as f:
            checkpoint_meta = json.load(f)

        checkpoint_name = meta_path.stem.replace('.meta', '')
        manifest['checkpoints'][checkpoint_name] = checkpoint_meta

    # Save manifest
    manifest_path = checkpoint_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[MANIFEST] Created manifest with {len(manifest['checkpoints'])} checkpoints")
    print(f"           Saved to: {manifest_path}")

    return manifest


def load_manifest(
    checkpoint_dir: Union[str, Path] = 'checkpoints'
) -> Optional[Dict]:
    """Load manifest.json if it exists."""
    checkpoint_dir = Path(checkpoint_dir)
    manifest_path = checkpoint_dir / 'manifest.json'

    if not manifest_path.exists():
        return None

    with open(manifest_path, 'r') as f:
        return json.load(f)


def validate_checkpoints(
    checkpoint_dir: Union[str, Path] = 'checkpoints',
    verbose: bool = True
) -> bool:
    """
    Validate all checkpoints against manifest.

    Parameters:
    -----------
    checkpoint_dir : str or Path
        Directory containing checkpoints
    verbose : bool
        Print validation details

    Returns:
    --------
    bool
        True if all checkpoints valid, False otherwise
    """
    checkpoint_dir = Path(checkpoint_dir)
    manifest = load_manifest(checkpoint_dir)

    if not manifest:
        if verbose:
            print("[WARNING] No manifest found. Cannot validate checkpoints.")
        return False

    all_valid = True

    for checkpoint_name, meta in manifest['checkpoints'].items():
        filename = meta['filename']
        expected_hash = meta.get('file_hash')

        if not checkpoint_exists(filename, checkpoint_dir):
            if verbose:
                print(f"  [MISSING] {filename}")
            all_valid = False
            continue

        # Validate hash
        filepath = checkpoint_dir / filename
        current_hash = compute_file_hash(filepath)

        if current_hash != expected_hash:
            if verbose:
                print(f"  [INVALID] {filename} (hash mismatch)")
            all_valid = False
        else:
            if verbose:
                print(f"  [VALID] {filename}")

    return all_valid


def compute_source_hash(
    monthly_returns_df: pd.DataFrame,
    tnic_data_dir: Union[str, Path]
) -> Dict[str, str]:
    """
    Compute hashes of source data for validation.

    Parameters:
    -----------
    monthly_returns_df : pd.DataFrame
        Core returns data
    tnic_data_dir : str or Path
        Directory containing TNIC CSV files

    Returns:
    --------
    dict
        Source data hashes
    """
    tnic_data_dir = Path(tnic_data_dir)

    # Hash date range of returns (proxy for AlphaExcel data version)
    date_range_str = f"{monthly_returns_df.index.min()}_{monthly_returns_df.index.max()}"
    date_hash = hashlib.md5(date_range_str.encode()).hexdigest()

    # Hash all TNIC files
    tnic_files = sorted(tnic_data_dir.glob('tnic_all_pairs_*.csv'))
    tnic_hash_obj = hashlib.md5()
    for tnic_file in tnic_files:
        with open(tnic_file, 'rb') as f:
            tnic_hash_obj.update(f.read())
    tnic_hash = tnic_hash_obj.hexdigest()

    return {
        'monthly_returns_range': date_range_str,
        'monthly_returns_range_hash': date_hash,
        'tnic_data_hash': tnic_hash,
        'tnic_files_count': len(tnic_files)
    }
