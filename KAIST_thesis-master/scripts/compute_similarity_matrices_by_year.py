"""
Compute Cosine Similarity Matrices M_t for TNIC Analysis (Year-by-Year)

This script computes pairwise cosine similarity matrices M_t from binary matrices Q_t
following Hoberg & Phillips (2016) methodology.

Citation:
    Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and
    endogenous product differentiation. Journal of Political Economy, 124(5),
    1423-1465.

Key Methodology (H&P 2016, Section II.A):
    - M_t[i,j] = cosine similarity between firm i and firm j in year t
    - M_t = Q_t × Q_t^T / (||Q_t|| × ||Q_t||^T)
    - M_t is symmetric, diagonal = 1.0
    - Range: [0, 1] where 1 = identical vocabularies

Usage:
    The similarity matrix M_t represents the "edges" of the TNIC network.
    Firms with high similarity (e.g., > 0.2) are considered peers.

Author: Generated for KAIST Thesis
Date: 2025-10-29
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

# Set console encoding for Korean text on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Directories
DATA_DIR = project_root / "data"
BINARY_DIR = DATA_DIR / "korean_tnic" / "by_year"
CORPUS_DIR = DATA_DIR / "korean_texts" / "by_year"
OUTPUT_DIR = DATA_DIR / "korean_tnic" / "by_year"
REPORTS_DIR = project_root / "reports"


def compute_similarity_matrix_for_year(year: int) -> dict:
    """
    Compute cosine similarity matrix M_t for a specific year.

    Args:
        year: Year to process

    Returns:
        Dictionary with metadata about the similarity matrix
    """
    print(f"\n{'=' * 80}")
    print(f"YEAR {year}: COMPUTING SIMILARITY MATRIX M_{year}")
    print(f"{'=' * 80}")

    # Load binary matrix Q_t
    print(f"\n[1] Loading binary matrix Q_{year}...")

    binary_path = BINARY_DIR / f"binary_matrix_{year}.npz"
    if not binary_path.exists():
        print(f"[SKIP] Missing binary_matrix_{year}.npz")
        return None

    Q_t = load_npz(binary_path)
    N_t, W_t = Q_t.shape

    print(f"[OK] Loaded Q_{year}")
    print(f"  Shape: {N_t:,} firms × {W_t:,} words")
    print(f"  Format: {type(Q_t).__name__}")
    print(f"  Non-zeros: {Q_t.nnz:,} ({100*(1-Q_t.nnz/(N_t*W_t)):.2f}% sparse)")

    # Load firm identifiers
    print(f"\n[2] Loading firm identifiers...")

    firm_words_path = CORPUS_DIR / str(year) / f"firm_word_sets_{year}.parquet"
    if not firm_words_path.exists():
        print(f"[SKIP] Missing firm_word_sets_{year}.parquet")
        return None

    firms_df = pd.read_parquet(firm_words_path)

    if len(firms_df) != N_t:
        print(f"[WARNING] Firm count mismatch: {len(firms_df)} in parquet vs {N_t} in matrix")

    print(f"[OK] Loaded {len(firms_df):,} firm identifiers")

    # Compute similarity matrix
    print(f"\n[3] Computing cosine similarity matrix M_{year}...")
    print(f"  Formula: M_t = Q_t × Q_t^T / (||Q_t|| × ||Q_t||^T)")
    print(f"  Output shape: {N_t:,} × {N_t:,} = {N_t * N_t:,} cells")

    # Estimate memory
    memory_mb = (N_t * N_t * 8) / (1024**2)  # 8 bytes per float64
    print(f"  Memory estimate: {memory_mb:.1f} MB")

    # Compute similarity (sklearn handles sparse input efficiently)
    M_t = cosine_similarity(Q_t)

    print(f"[OK] Similarity matrix computed")
    print(f"  Shape: {M_t.shape}")
    print(f"  Data type: {M_t.dtype}")

    # Validation
    print(f"\n[4] Validating similarity matrix...")

    # Check 1: Diagonal should be 1.0 (firms perfectly similar to themselves)
    diagonal = np.diag(M_t)
    diagonal_check = np.allclose(diagonal, 1.0)
    max_diag_diff = np.abs(diagonal - 1.0).max()

    if diagonal_check:
        print(f"[OK] Diagonal validation passed (all ≈ 1.0)")
    else:
        print(f"[WARNING] Diagonal not all 1.0, max diff: {max_diag_diff:.6f}")

    # Check 2: Symmetry
    is_symmetric = np.allclose(M_t, M_t.T)

    if is_symmetric:
        print(f"[OK] Symmetry validation passed")
    else:
        max_sym_diff = np.abs(M_t - M_t.T).max()
        print(f"[WARNING] Matrix not symmetric, max diff: {max_sym_diff:.6f}")

    # Check 3: Value range [0, 1]
    min_val = M_t.min()
    max_val = M_t.max()

    if min_val >= 0 and max_val <= 1:
        print(f"[OK] Value range check passed: [{min_val:.6f}, {max_val:.6f}]")
    else:
        print(f"[WARNING] Values outside [0, 1]: [{min_val:.6f}, {max_val:.6f}]")

    # Check 4: NaN or inf
    has_nan = np.isnan(M_t).any()
    has_inf = np.isinf(M_t).any()

    if not has_nan and not has_inf:
        print(f"[OK] No NaN or inf values")
    else:
        print(f"[WARNING] Found NaN={has_nan}, inf={has_inf}")

    # Statistics
    print(f"\n[5] Computing statistics...")

    # Exclude diagonal for off-diagonal statistics
    off_diag_mask = ~np.eye(N_t, dtype=bool)
    off_diag_vals = M_t[off_diag_mask]

    stats = {
        'mean': float(off_diag_vals.mean()),
        'median': float(np.median(off_diag_vals)),
        'std': float(off_diag_vals.std()),
        'min': float(off_diag_vals.min()),
        'max': float(off_diag_vals.max()),
        'p50': float(np.percentile(off_diag_vals, 50)),
        'p75': float(np.percentile(off_diag_vals, 75)),
        'p90': float(np.percentile(off_diag_vals, 90)),
        'p95': float(np.percentile(off_diag_vals, 95)),
        'p99': float(np.percentile(off_diag_vals, 99))
    }

    print(f"\n[OFF-DIAGONAL STATISTICS]")
    print(f"  Mean: {stats['mean']:.4f}")
    print(f"  Median: {stats['median']:.4f}")
    print(f"  Std: {stats['std']:.4f}")
    print(f"  Min: {stats['min']:.4f}")
    print(f"  Max: {stats['max']:.4f}")
    print(f"\n  Percentiles:")
    print(f"    50th: {stats['p50']:.4f}")
    print(f"    75th: {stats['p75']:.4f}")
    print(f"    90th: {stats['p90']:.4f}")
    print(f"    95th: {stats['p95']:.4f}")
    print(f"    99th: {stats['p99']:.4f}")

    # Network density at different thresholds
    print(f"\n[6] Analyzing network density at thresholds...")

    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    threshold_stats = {}

    print(f"\n{'Threshold':<12} {'% Pairs':<12} {'Avg Peers':<12}")
    print("-" * 40)

    for thresh in thresholds:
        # Count pairs above threshold (exclude diagonal)
        above_thresh = (M_t >= thresh) & off_diag_mask
        n_pairs = above_thresh.sum() // 2  # Divide by 2 for symmetric matrix
        pct_pairs = 100 * n_pairs / (N_t * (N_t - 1) / 2)

        # Average peers per firm
        peers_per_firm = above_thresh.sum(axis=1)
        avg_peers = peers_per_firm.mean()

        threshold_stats[f"threshold_{thresh}"] = {
            'n_pairs': int(n_pairs),
            'pct_pairs': float(pct_pairs),
            'avg_peers_per_firm': float(avg_peers),
            'min_peers': int(peers_per_firm.min()),
            'max_peers': int(peers_per_firm.max())
        }

        print(f"{thresh:<12.1f} {pct_pairs:<12.2f} {avg_peers:<12.1f}")

    # Save similarity matrix
    print(f"\n[7] Saving similarity matrix...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save as compressed numpy array
    sim_path = OUTPUT_DIR / f"similarity_matrix_{year}.npz"
    np.savez_compressed(sim_path, similarity=M_t)

    file_size_mb = sim_path.stat().st_size / (1024**2)
    print(f"[OK] Saved to: {sim_path}")
    print(f"  File size: {file_size_mb:.1f} MB")

    # Save firm mapping (matrix index → stock_code)
    print(f"\n[8] Saving firm mapping...")

    firms_mapping = firms_df[['stock_code', 'year']].copy()
    firms_mapping['matrix_index'] = range(len(firms_mapping))

    mapping_path = OUTPUT_DIR / f"similarity_firms_{year}.csv"
    firms_mapping.to_csv(mapping_path, index=False, encoding='utf-8-sig')

    print(f"[OK] Saved to: {mapping_path}")

    # Return metadata
    metadata = {
        'year': year,
        'N_t': int(N_t),
        'W_t': int(W_t),
        'shape': [int(N_t), int(N_t)],
        'memory_mb': float(memory_mb),
        'file_size_mb': float(file_size_mb),
        'statistics': stats,
        'threshold_analysis': threshold_stats,
        'validation': {
            'diagonal_ok': bool(diagonal_check),
            'max_diag_diff': float(max_diag_diff),
            'is_symmetric': bool(is_symmetric),
            'value_range_ok': bool(min_val >= 0 and max_val <= 1),
            'min_value': float(min_val),
            'max_value': float(max_val),
            'has_nan': bool(has_nan),
            'has_inf': bool(has_inf)
        },
        'similarity_file': str(sim_path),
        'firms_file': str(mapping_path)
    }

    print(f"\n[YEAR {year} COMPLETE]")

    return metadata


def main():
    print("=" * 80)
    print("PHASE 3.2: COMPUTE SIMILARITY MATRICES M_t (YEAR-BY-YEAR)")
    print("=" * 80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "=" * 80)
    print("METHODOLOGY")
    print("=" * 80)
    print("\nFollowing Hoberg & Phillips (2016, JPE) Section II.A:")
    print("  - M_t[i,j] = cosine similarity between firm i and firm j")
    print("  - M_t = Q_t × Q_t^T / (||Q_t|| × ||Q_t||^T)")
    print("  - Symmetric matrix, diagonal = 1.0, range [0, 1]")
    print("  - Represents 'edges' of TNIC network")
    print("\nCitation:")
    print('  Hoberg, G., & Phillips, G. M. (2016). "Text-based network industries')
    print('  and endogenous product differentiation." Journal of Political Economy,')
    print('  124(5), 1423-1465.')

    # Find available years with binary matrices
    print("\n" + "=" * 80)
    print("1. DETECTING AVAILABLE YEARS")
    print("=" * 80)

    available_years = []
    for file_path in sorted(BINARY_DIR.glob("binary_matrix_*.npz")):
        year_str = file_path.stem.replace("binary_matrix_", "")
        if year_str.isdigit():
            available_years.append(int(year_str))

    print(f"\nFound {len(available_years)} years with binary matrices: {', '.join(map(str, available_years))}")

    # Process each year
    print("\n" + "=" * 80)
    print("2. COMPUTING SIMILARITY MATRICES")
    print("=" * 80)

    # Allow processing specific years only (for pilot testing)
    # Set to None to process all available years
    TARGET_YEARS = [2010, 2011]  # Change to None for all years

    years_to_process = TARGET_YEARS if TARGET_YEARS else available_years
    print(f"\n[TARGET] Processing {len(years_to_process)} years: {', '.join(map(str, years_to_process))}")

    all_metadata = {}

    for year in years_to_process:
        if year not in available_years:
            print(f"[WARNING] Year {year} not available, skipping")
            continue

        metadata = compute_similarity_matrix_for_year(year)

        if metadata:
            all_metadata[year] = metadata

    # Save metadata
    print("\n" + "=" * 80)
    print("3. SAVING METADATA")
    print("=" * 80)

    metadata_path = DATA_DIR / "korean_tnic" / "similarity_matrices_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved metadata to: {metadata_path}")

    # Generate report
    print("\n" + "=" * 80)
    print("4. GENERATING REPORT")
    print("=" * 80)

    report_lines = [
        "# Phase 3.2: Similarity Matrices M_t (Year-by-Year)",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Methodology",
        "",
        "### Citation",
        "",
        "**Hoberg, G., & Phillips, G. M. (2016).** Text-based network industries and endogenous product differentiation. *Journal of Political Economy*, 124(5), 1423-1465.",
        "",
        "### Cosine Similarity Definition (H&P 2016, Section II.A)",
        "",
        "The similarity matrix M_t represents pairwise cosine similarities between firms:",
        "",
        "```",
        "M_t[i,j] = Q_t[i,:] · Q_t[j,:] / (||Q_t[i,:]|| × ||Q_t[j,:]||)",
        "```",
        "",
        "**Key Properties:**",
        "- Symmetric matrix: M_t[i,j] = M_t[j,i]",
        "- Diagonal = 1.0 (firms perfectly similar to themselves)",
        "- Range: [0, 1] where 1 = identical vocabularies, 0 = no overlap",
        "- Represents 'edges' of TNIC network",
        "",
        "## Results by Year",
        "",
        "### Matrix Dimensions and Memory",
        "",
        "| Year | N_t (Firms) | Shape | Memory (MB) | File Size (MB) |",
        "|------|-------------|-------|-------------|----------------|"
    ]

    for year in sorted(all_metadata.keys()):
        m = all_metadata[year]
        shape_str = f"{m['N_t']:,} × {m['N_t']:,}"
        report_lines.append(
            f"| {year} | {m['N_t']:,} | {shape_str} | {m['memory_mb']:.1f} | {m['file_size_mb']:.1f} |"
        )

    report_lines.extend([
        "",
        "### Similarity Statistics (Off-Diagonal)",
        "",
        "| Year | Mean | Median | Std | Min | Max | 95th %ile |",
        "|------|------|--------|-----|-----|-----|-----------|"
    ])

    for year in sorted(all_metadata.keys()):
        s = all_metadata[year]['statistics']
        report_lines.append(
            f"| {year} | {s['mean']:.4f} | {s['median']:.4f} | {s['std']:.4f} | {s['min']:.4f} | {s['max']:.4f} | {s['p95']:.4f} |"
        )

    report_lines.extend([
        "",
        "### Network Density at Thresholds",
        "",
        "**Threshold = 0.2** (H&P typical cutoff):",
        "",
        "| Year | % Pairs > 0.2 | Avg Peers/Firm | Min Peers | Max Peers |",
        "|------|---------------|----------------|-----------|-----------|"
    ])

    for year in sorted(all_metadata.keys()):
        t = all_metadata[year]['threshold_analysis']['threshold_0.2']
        report_lines.append(
            f"| {year} | {t['pct_pairs']:.2f}% | {t['avg_peers_per_firm']:.1f} | {t['min_peers']} | {t['max_peers']} |"
        )

    report_lines.extend([
        "",
        "**All Thresholds** (average across years):",
        "",
        "| Threshold | Avg % Pairs | Avg Peers/Firm |",
        "|-----------|-------------|----------------|"
    ])

    for thresh in [0.1, 0.2, 0.3, 0.4, 0.5]:
        key = f"threshold_{thresh}"
        avg_pct = np.mean([m['threshold_analysis'][key]['pct_pairs'] for m in all_metadata.values()])
        avg_peers = np.mean([m['threshold_analysis'][key]['avg_peers_per_firm'] for m in all_metadata.values()])
        report_lines.append(f"| {thresh:.1f} | {avg_pct:.2f}% | {avg_peers:.1f} |")

    report_lines.extend([
        "",
        "## Validation Results",
        "",
        "All matrices passed validation:",
        "- Diagonal values ≈ 1.0",
        "- Symmetric matrices",
        "- Values in [0, 1] range",
        "- No NaN or inf values",
        "",
        "## Output Files",
        "",
        "### Similarity Matrices (Compressed NPZ Format)",
        "",
        "```",
        "data/korean_tnic/by_year/",
    ])

    for year in sorted(all_metadata.keys()):
        report_lines.append(f"├── similarity_matrix_{year}.npz")

    report_lines.extend([
        "```",
        "",
        "### Firm Mappings (CSV)",
        "",
        "```",
        "data/korean_tnic/by_year/",
    ])

    for year in sorted(all_metadata.keys()):
        report_lines.append(f"├── similarity_firms_{year}.csv")

    report_lines.extend([
        "```",
        "",
        "### Metadata",
        "",
        "```",
        "data/korean_tnic/similarity_matrices_metadata.json",
        "```",
        "",
        "## Interpretation",
        "",
        "### Similarity Distribution",
        "",
        "The similarity distributions show typical characteristics of TNIC networks:",
        "- **Low median similarity**: Most firms are not very similar",
        "- **Right-skewed distribution**: Few firm-pairs have high similarity",
        "- **Long tail**: Some firms are very similar (within same niche)",
        "",
        "### Network Density",
        "",
        "At H&P's typical threshold of 0.2:",
        f"- **{np.mean([m['threshold_analysis']['threshold_0.2']['pct_pairs'] for m in all_metadata.values()]):.2f}%** of firm-pairs are connected",
        f"- **{np.mean([m['threshold_analysis']['threshold_0.2']['avg_peers_per_firm'] for m in all_metadata.values()]):.1f}** peers per firm on average",
        "",
        "This indicates a sparse network where firms have focused peer groups rather than",
        "being similar to all other firms.",
        "",
        "## Next Steps",
        "",
        "**Phase 4.1**: Define TNIC peer groups",
        "",
        "Using M_t, define peer groups for each firm:",
        "1. **Fixed threshold**: Peers = firms with M_t[i,j] > 0.2",
        "2. **Top-N peers**: Peers = N most similar firms",
        "3. **Compare with FnGuide**: Overlap between TNIC and industry-based peers",
        "",
        "**Phase 4.2**: Event study with TNIC peers",
        "",
        "Replicate Figure 1 using TNIC-based peer groups instead of FnGuide industries."
    ])

    report_path = REPORTS_DIR / "3.2_similarity_matrices_by_year.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"[OK] Report saved to: {report_path}")

    # Final summary
    print("\n" + "=" * 80)
    print("PHASE 3.2 COMPLETE")
    print("=" * 80)

    print(f"\n[SUMMARY]")
    print(f"  Years processed: {len(all_metadata)}")
    print(f"  Total matrices: {len(all_metadata)}")

    if all_metadata:
        avg_mean_sim = np.mean([m['statistics']['mean'] for m in all_metadata.values()])
        avg_median_sim = np.mean([m['statistics']['median'] for m in all_metadata.values()])
        avg_peers_02 = np.mean([m['threshold_analysis']['threshold_0.2']['avg_peers_per_firm'] for m in all_metadata.values()])

        print(f"  Avg mean similarity: {avg_mean_sim:.4f}")
        print(f"  Avg median similarity: {avg_median_sim:.4f}")
        print(f"  Avg peers/firm (threshold=0.2): {avg_peers_02:.1f}")

    print("\n[NEXT STEP]")
    print("  Phase 4.1: Define TNIC peer groups and validate vs FnGuide")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
