"""
Visualization Script for TNIC Networks
t-SNE Visualization of High-Dimensional Embeddings

This script visualizes text-based industry networks using t-SNE dimensionality reduction:
- Autoencoder embeddings (10D → 2D)
- TNIC embeddings (optional, if available)
- Color-coded by cluster/industry assignments

Usage:
    python visualize-tnic.py --year 2010
    python visualize-tnic.py --year 2010 --method autoencoder
    python visualize-tnic.py --year 2010 --method both --interactive
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.manifold import TSNE
from datetime import datetime

# Optional: plotly for interactive visualization
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not available. Install with 'pip install plotly' for interactive plots.")

# ============================================================================
# Configuration
# ============================================================================

AUTOENCODER_DATA_DIR = Path("data/korean_tnic_dl/by_year")
TNIC_DATA_DIR = Path("data/korean_tnic/by_year")  # Traditional TNIC (if available)
OUTPUT_DIR = Path("outputs/visualizations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# t-SNE parameters
TSNE_PERPLEXITY = 30      # Typical range: 5-50 (smaller for small datasets)
TSNE_N_ITER = 1000        # Number of iterations
TSNE_RANDOM_STATE = 42    # For reproducibility

# Visualization parameters
FIGURE_SIZE = (14, 10)
DPI = 300
ALPHA = 0.6
POINT_SIZE = 50

print("=" * 80)
print("TNIC NETWORK VISUALIZATION - t-SNE Analysis")
print("=" * 80)
print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# Argument Parsing
# ============================================================================

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Visualize TNIC networks using t-SNE')
    parser.add_argument('--year', type=int, required=True, help='Year to visualize (e.g., 2010)')
    parser.add_argument('--method', type=str, default='autoencoder',
                        choices=['autoencoder', 'tnic', 'both'],
                        help='Which method to visualize')
    parser.add_argument('--perplexity', type=int, default=TSNE_PERPLEXITY,
                        help='t-SNE perplexity parameter (default: 30)')
    parser.add_argument('--interactive', action='store_true',
                        help='Generate interactive plotly visualization (requires plotly)')
    parser.add_argument('--color-by', type=str, default='cluster',
                        choices=['cluster', 'industry', 'both'],
                        help='Color points by cluster or FnGuide industry')
    return parser.parse_args()

# ============================================================================
# Data Loading Functions
# ============================================================================

def load_autoencoder_data(year):
    """Load autoencoder embeddings and cluster assignments."""
    year_dir = AUTOENCODER_DATA_DIR / str(year)

    embeddings_path = year_dir / f"embeddings_autoencoder_{year}.npy"
    clusters_path = year_dir / f"clusters_autoencoder_{year}.csv"

    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings not found: {embeddings_path}")
    if not clusters_path.exists():
        raise FileNotFoundError(f"Clusters not found: {clusters_path}")

    embeddings = np.load(embeddings_path)
    clusters_df = pd.read_csv(clusters_path, dtype={'stock_code': str})

    print(f"[Autoencoder] Loaded {len(embeddings)} firms")
    print(f"  Embeddings shape: {embeddings.shape}")
    print(f"  Clusters: {clusters_df['cluster'].nunique()} unique clusters")
    print(f"  Cluster size range: {clusters_df['cluster'].value_counts().min()} - {clusters_df['cluster'].value_counts().max()} firms")

    return embeddings, clusters_df


def load_tnic_data(year):
    """Load traditional TNIC embeddings (if available)."""
    year_dir = TNIC_DATA_DIR / str(year)

    embeddings_path = year_dir / f"embeddings_tnic_{year}.npy"

    if not embeddings_path.exists():
        raise FileNotFoundError(f"TNIC embeddings not found: {embeddings_path}")

    embeddings = np.load(embeddings_path)

    print(f"[TNIC] Loaded {len(embeddings)} firms")
    print(f"  Embeddings shape: {embeddings.shape}")

    return embeddings


def load_fnguide_industries():
    """Load FnGuide industry classifications for comparison."""
    fnguide_path = Path("data/fnguide/processed/dataguide_filtered.parquet")

    if not fnguide_path.exists():
        print("  Warning: FnGuide data not found. Cannot color by industry.")
        return None

    df = pd.read_parquet(fnguide_path)

    # Extract unique stock_code and industry mapping
    industry_map = df[['symbol', 'FnGuide Industry']].drop_duplicates('symbol')
    industry_map.columns = ['stock_code', 'industry']

    # Convert FnGuide code format (A000020) to autoencoder format (000020)
    industry_map['stock_code'] = industry_map['stock_code'].str.replace('A', '', regex=False)

    print(f"[FnGuide] Loaded {len(industry_map)} firm-industry mappings")
    print(f"  Unique industries: {industry_map['industry'].nunique()}")

    return industry_map


# ============================================================================
# t-SNE Transformation
# ============================================================================

def apply_tsne(embeddings, perplexity=30, max_iter=1000, random_state=42):
    """Apply t-SNE to reduce embeddings to 2D."""
    print(f"\nApplying t-SNE transformation...")
    print(f"  Input shape: {embeddings.shape}")
    print(f"  Perplexity: {perplexity}")
    print(f"  Max iterations: {max_iter}")
    print(f"  This may take 1-2 minutes for ~1800 samples...")

    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        max_iter=max_iter,  # Changed from n_iter to max_iter
        random_state=random_state,
        verbose=0,  # Reduce verbosity to avoid output confusion
        method='barnes_hut',  # Faster for large datasets
        angle=0.5
    )

    print(f"  Running t-SNE...")
    embeddings_2d = tsne.fit_transform(embeddings)

    print(f"  ✓ t-SNE complete!")
    print(f"  Output shape: {embeddings_2d.shape}")

    return embeddings_2d


# ============================================================================
# Static Visualization (Matplotlib)
# ============================================================================

def plot_tsne_static(embeddings_2d, labels, label_name, title, output_path,
                     point_size=POINT_SIZE, alpha=ALPHA, cmap='tab20'):
    """Create static t-SNE scatter plot."""
    print(f"\nCreating static plot: {output_path}")

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    # Handle NaN values - replace with a placeholder string
    labels_clean = labels.fillna('Unknown')

    # Convert labels to numeric if they're strings
    if labels_clean.dtype == 'object':
        unique_labels = sorted(labels_clean.unique())
        label_map = {label: i for i, label in enumerate(unique_labels)}
        numeric_labels = labels_clean.map(label_map)
    else:
        numeric_labels = labels_clean
        unique_labels = sorted(labels_clean.unique())

    scatter = ax.scatter(
        embeddings_2d[:, 0],
        embeddings_2d[:, 1],
        c=numeric_labels,
        cmap=cmap,
        alpha=alpha,
        s=point_size,
        edgecolors='black',
        linewidths=0.5
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, label=label_name)

    # If we have string labels, show them in colorbar
    if labels_clean.dtype == 'object' and len(unique_labels) <= 20:
        cbar.set_ticks(range(len(unique_labels)))
        cbar.set_ticklabels(unique_labels)

    ax.set_xlabel('t-SNE Dimension 1', fontsize=12)
    ax.set_ylabel('t-SNE Dimension 2', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Add grid for better readability
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    print(f"  Saved to: {output_path}")

    plt.close()


def plot_cluster_statistics(clusters_df, output_path):
    """Plot cluster size distribution."""
    print(f"\nCreating cluster statistics plot: {output_path}")

    cluster_sizes = clusters_df['cluster'].value_counts().sort_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Bar plot
    axes[0].bar(cluster_sizes.index, cluster_sizes.values, color='steelblue', alpha=0.7)
    axes[0].set_xlabel('Cluster ID', fontsize=12)
    axes[0].set_ylabel('Number of Firms', fontsize=12)
    axes[0].set_title('Cluster Size Distribution (Bar)', fontsize=13, fontweight='bold')
    axes[0].grid(True, alpha=0.3, axis='y')

    # Histogram
    axes[1].hist(cluster_sizes.values, bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    axes[1].set_xlabel('Cluster Size (# Firms)', fontsize=12)
    axes[1].set_ylabel('Frequency (# Clusters)', fontsize=12)
    axes[1].set_title('Cluster Size Distribution (Histogram)', fontsize=13, fontweight='bold')
    axes[1].grid(True, alpha=0.3, axis='y')

    # Add statistics
    stats_text = f"Total Clusters: {len(cluster_sizes)}\n"
    stats_text += f"Mean Size: {cluster_sizes.mean():.1f}\n"
    stats_text += f"Median Size: {cluster_sizes.median():.1f}\n"
    stats_text += f"Min Size: {cluster_sizes.min()}\n"
    stats_text += f"Max Size: {cluster_sizes.max()}"

    axes[1].text(0.98, 0.97, stats_text,
                transform=axes[1].transAxes,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    print(f"  Saved to: {output_path}")

    plt.close()


# ============================================================================
# Interactive Visualization (Plotly)
# ============================================================================

def plot_tsne_interactive(embeddings_2d, clusters_df, label_col, title, output_path):
    """Create interactive plotly t-SNE visualization."""
    if not PLOTLY_AVAILABLE:
        print("  Skipping interactive plot (plotly not available)")
        return

    print(f"\nCreating interactive plot: {output_path}")

    # Prepare dataframe for plotly
    plot_df = clusters_df.copy()
    plot_df['x'] = embeddings_2d[:, 0]
    plot_df['y'] = embeddings_2d[:, 1]

    # Create hover text with firm details
    plot_df['hover_text'] = (
        "Stock Code: " + plot_df['stock_code'].astype(str) + "<br>" +
        label_col + ": " + plot_df[label_col].astype(str)
    )

    fig = px.scatter(
        plot_df,
        x='x',
        y='y',
        color=label_col,
        hover_data=['stock_code'],
        title=title,
        labels={'x': 't-SNE Dimension 1', 'y': 't-SNE Dimension 2'},
        color_continuous_scale='Viridis' if plot_df[label_col].dtype != 'object' else None,
        color_discrete_sequence=px.colors.qualitative.Light24 if plot_df[label_col].dtype == 'object' else None
    )

    fig.update_traces(
        marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color='DarkSlateGrey')),
        selector=dict(mode='markers')
    )

    fig.update_layout(
        width=1200,
        height=800,
        font=dict(size=12),
        title_font_size=16
    )

    fig.write_html(output_path)
    print(f"  Saved to: {output_path}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    # Parse arguments
    args = parse_arguments()
    year = args.year
    method = args.method
    perplexity = args.perplexity
    interactive = args.interactive
    color_by = args.color_by

    print(f"Configuration:")
    print(f"  Year: {year}")
    print(f"  Method: {method}")
    print(f"  t-SNE perplexity: {perplexity}")
    print(f"  Interactive plots: {interactive and PLOTLY_AVAILABLE}")
    print(f"  Color by: {color_by}")
    print()

    print("\n" + "=" * 80)
    print("STEP 1: LOAD DATA")
    print("=" * 80)

    # Load autoencoder data
    if method in ['autoencoder', 'both']:
        embeddings_auto, clusters_df = load_autoencoder_data(year)

        # Load FnGuide industries if requested
        if color_by in ['industry', 'both']:
            industry_map = load_fnguide_industries()
            if industry_map is not None:
                clusters_df = clusters_df.merge(industry_map, on='stock_code', how='left')
            else:
                print("  Warning: Falling back to cluster coloring only")
                color_by = 'cluster'

    # Load TNIC data (if requested and available)
    if method in ['tnic', 'both']:
        try:
            embeddings_tnic = load_tnic_data(year)
        except FileNotFoundError as e:
            print(f"  Warning: {e}")
            if method == 'tnic':
                print("  Error: TNIC data required but not found. Exiting.")
                return
            method = 'autoencoder'

    print("\n" + "=" * 80)
    print("STEP 2: APPLY t-SNE TRANSFORMATION")
    print("=" * 80)

    # Apply t-SNE to autoencoder embeddings
    if method in ['autoencoder', 'both']:
        embeddings_2d_auto = apply_tsne(embeddings_auto, perplexity=perplexity,
                                        max_iter=TSNE_N_ITER, random_state=TSNE_RANDOM_STATE)

    # Apply t-SNE to TNIC embeddings (if applicable)
    if method in ['tnic', 'both']:
        embeddings_2d_tnic = apply_tsne(embeddings_tnic, perplexity=perplexity,
                                        max_iter=TSNE_N_ITER, random_state=TSNE_RANDOM_STATE)

    print("\n" + "=" * 80)
    print("STEP 3: CREATE VISUALIZATIONS")
    print("=" * 80)

    # Plot autoencoder results
    if method in ['autoencoder', 'both']:
        # Colored by cluster
        if color_by in ['cluster', 'both']:
            output_path = OUTPUT_DIR / f"tsne_autoencoder_clusters_{year}.png"
            plot_tsne_static(
                embeddings_2d_auto,
                clusters_df['cluster'],
                'Cluster ID',
                f't-SNE Visualization of Autoencoder Embeddings ({year})\nColored by Cluster (K={clusters_df["cluster"].nunique()})',
                output_path
            )

            if interactive:
                output_path_html = OUTPUT_DIR / f"tsne_autoencoder_clusters_{year}.html"
                plot_tsne_interactive(embeddings_2d_auto, clusters_df, 'cluster',
                                    f't-SNE: Autoencoder Clusters ({year})', output_path_html)

        # Colored by FnGuide industry
        if color_by in ['industry', 'both'] and 'industry' in clusters_df.columns:
            output_path = OUTPUT_DIR / f"tsne_autoencoder_industry_{year}.png"
            plot_tsne_static(
                embeddings_2d_auto,
                clusters_df['industry'],
                'FnGuide Industry',
                f't-SNE Visualization of Autoencoder Embeddings ({year})\nColored by FnGuide Industry',
                output_path,
                cmap='tab20c'
            )

            if interactive:
                output_path_html = OUTPUT_DIR / f"tsne_autoencoder_industry_{year}.html"
                plot_tsne_interactive(embeddings_2d_auto, clusters_df, 'industry',
                                    f't-SNE: Autoencoder (FnGuide Industry) ({year})', output_path_html)

        # Cluster statistics
        stats_path = OUTPUT_DIR / f"cluster_statistics_{year}.png"
        plot_cluster_statistics(clusters_df, stats_path)

    # Plot TNIC results (if applicable)
    if method in ['tnic', 'both']:
        output_path = OUTPUT_DIR / f"tsne_tnic_{year}.png"
        # Note: We don't have cluster labels for TNIC, so color by density or use default
        print("  Note: TNIC visualization not fully implemented (no cluster labels)")

    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE!")
    print("=" * 80)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
