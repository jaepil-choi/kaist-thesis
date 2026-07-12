# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: kaist-thesis-py3.12
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Thesis: Text-based industry momentum in Korea - Autoencoder Clusters
#
# ## Brief Plan
#
# - Autoencoder cluster data is already created.
# - Using `alpha-excel` package I made, we will replicate the original paper by Hoberg and Phillips (2018) on Korean stock market.
# - This version uses autoencoder clusters instead of TNIC similarity scores.

# %% [markdown]
# ## 0. Import libs, initialize alpha-excel instance with MONTHLY data

# %%
import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
from datetime import datetime

from alpha_excel2.core.facade import AlphaExcel
import checkpoint_utils as cp

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Text-based industry momentum analysis with autoencoder clusters')
parser.add_argument('--save-checkpoints', action='store_true',
                   help='Save intermediate results to checkpoints/ directory')
parser.add_argument('--validate-checkpoints', action='store_true',
                   help='Validate existing checkpoints against manifest')
parser.add_argument('--checkpoint-dir', type=str, default='checkpoints_autoencoder',
                   help='Directory for checkpoint files (default: checkpoints_autoencoder)')

# Only parse args if running as script (not in Jupyter)
if __name__ == "__main__" and not hasattr(sys, 'ps1'):
    args = parser.parse_args()
else:
    # Default args for Jupyter notebook
    args = argparse.Namespace(
        save_checkpoints=False,
        validate_checkpoints=False,
        checkpoint_dir='checkpoints_autoencoder'
    )

CHECKPOINT_DIR = Path(args.checkpoint_dir)
CHECKPOINT_DIR.mkdir(exist_ok=True)

# Global timing tracker
_section_times = {}
_section_start = None
_last_section = None

def print_section(title):
    """Print a formatted section header and track timing"""
    global _section_start, _last_section

    # Record end time of previous section
    if _last_section is not None and _section_start is not None:
        elapsed = time.time() - _section_start
        _section_times[_last_section] = elapsed
        print(f"\n[TIME] Section '{_last_section}' completed in {elapsed:.2f}s ({elapsed/60:.2f}m)")

    # Print new section header
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

    # Start timing new section
    _section_start = time.time()
    _last_section = title

def print_total_time():
    """Print summary of all section times"""
    print("\n" + "=" * 80)
    print("  TIMING SUMMARY")
    print("=" * 80)
    total = 0
    for section, elapsed in _section_times.items():
        print(f"  {section:60s} {elapsed:8.2f}s ({elapsed/60:6.2f}m)")
        total += elapsed
    print("=" * 80)
    print(f"  {'TOTAL':60s} {total:8.2f}s ({total/60:6.2f}m)")
    print("=" * 80 + "\n")

def calculate_summary_stats_single(df, var_name):
    """
    Calculate summary statistics for a single 2D dataframe.

    Parameters:
    -----------
    df : pd.DataFrame
        2D dataframe (dates × securities)
    var_name : str
        Variable name for display

    Returns:
    --------
    dict
        Summary statistics: {'Variable', 'Mean', 'Std Dev', 'Min', 'Median', 'Max', 'N'}
    """
    values = df.stack().dropna()

    return {
        'Variable': var_name,
        'Mean': f'{values.mean():.4f}',
        'Std Dev': f'{values.std():.4f}',
        'Min': f'{values.min():.4f}',
        'Median': f'{values.median():.4f}',
        'Max': f'{values.max():.4f}',
        'N': f'{len(values):,}'
    }

def extract_turnover_windows(share_turnover_df, event_matrix, WINDOW_BEFORE=3, WINDOW_AFTER=12):
    """
    Extract turnover windows around peer shock events.

    Parameters:
    - share_turnover_df: DataFrame of turnover values (dates x symbols)
    - event_matrix: Boolean DataFrame marking high-quintile events
    - WINDOW_BEFORE: Months before event (default 3)
    - WINDOW_AFTER: Months after event (default 12)

    Returns:
    - List of turnover windows (numpy arrays)
    """
    WINDOW_LENGTH = WINDOW_BEFORE + 1 + WINDOW_AFTER

    turnover_windows = []
    used_events = set()
    date_to_idx = {date: idx for idx, date in enumerate(share_turnover_df.index)}

    for symbol in tqdm(event_matrix.columns, desc="Extracting windows"):
        event_dates = event_matrix.index[event_matrix[symbol]]

        for event_date in event_dates:
            event_idx = date_to_idx[event_date]

            # Check if we have enough data before and after
            if event_idx < WINDOW_BEFORE or event_idx + WINDOW_AFTER >= len(share_turnover_df):
                continue

            # Skip if this event's window overlaps with any previously used event
            if (symbol, event_idx - WINDOW_BEFORE) in used_events or (symbol, event_idx + WINDOW_AFTER) in used_events:
                continue

            # Extract turnover window (t-3 to t+12)
            start_idx = event_idx - WINDOW_BEFORE
            end_idx = event_idx + WINDOW_AFTER + 1

            turnover_window = share_turnover_df.iloc[start_idx:end_idx][symbol].values

            # Skip if any turnover is missing
            if pd.isna(turnover_window).any():
                continue

            # Skip if any turnover is near-zero or zero (suspicious)
            if (np.isclose(turnover_window, 0.0)).any():
                continue

            # Store this window
            turnover_windows.append(turnover_window)

            # Mark the entire turnover window as used (t-3 to t+12)
            for i in range(-WINDOW_BEFORE, WINDOW_AFTER + 1):
                used_events.add((symbol, event_idx + i))

    return turnover_windows

def normalize_and_aggregate(turnover_windows, WINDOW_BEFORE=3):
    """
    Normalize turnover windows by first position (t=-WINDOW_BEFORE) and aggregate.

    Parameters:
    - turnover_windows: List of turnover window arrays
    - WINDOW_BEFORE: Number of months before event (determines normalization point)
                     e.g., WINDOW_BEFORE=3 means normalize by t=-3
                     e.g., WINDOW_BEFORE=14 means normalize by t=-14

    Returns:
    - normalized_turnover: Normalized turnover values (numpy array)
    """
    turnover_windows_array = np.array(turnover_windows)

    # Average first, then normalize (matching figure1_graph_a.py)
    avg_turnover = turnover_windows_array.mean(axis=0)

    # Normalize by first position (t=-WINDOW_BEFORE)
    # Index 0 corresponds to t=-WINDOW_BEFORE
    normalized_turnover = avg_turnover / avg_turnover[0]

    return normalized_turnover

def plot_results(relative_months, normalized_turnover, n_events, method_name, WINDOW_BEFORE=3, normalization_point=-3, legend_label=None, color='#2E86AB'):
    """
    Plot Figure 1A: Turnover around peer shocks.

    Parameters:
    - relative_months: X-axis values (e.g., -15 to +15)
    - normalized_turnover: Normalized turnover values
    - n_events: Number of event windows
    - method_name: String describing the method (for title)
    - WINDOW_BEFORE: Number of months before event (determines window start)
    - normalization_point: Which relative month was used for normalization (default -3)
    - legend_label: Label for the data series in legend (default: method_name)
    - color: Color for the line plot (default: '#2E86AB')

    Returns:
    - fig, ax: Matplotlib figure and axis objects
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Use legend_label if provided, otherwise use method_name
    if legend_label is None:
        legend_label = method_name

    ax.plot(relative_months, normalized_turnover,
            marker='o', linewidth=2, markersize=6,
            color=color, label=legend_label)

    # Add horizontal line at y=1.0
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=1)

    # Add vertical line at t=0 (event month)
    ax.axvline(x=0, color='red', linestyle='--', alpha=0.5, linewidth=1,
               label='Peer Shock (t=0)')

    # Add vertical line at normalization point
    ax.axvline(x=normalization_point, color='blue', linestyle='--', alpha=0.5, linewidth=1,
               label=f't={normalization_point} (Normalization Point)')

    # Formatting
    ax.set_xlabel('Months Relative to High-Quintile Peer Return', fontsize=12)
    ax.set_ylabel('Relative Average Stock Turnover', fontsize=12)
    ax.set_title(f'Figure 1A: Turnover Following High-Quintile Peer Shock\n' +
                 f'({method_name}, N={n_events:,} events)',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(relative_months)

    # Set y-axis limits
    y_min = normalized_turnover.min() * 0.95
    y_max = normalized_turnover.max() * 1.05
    ax.set_ylim(y_min, y_max)

    plt.tight_layout()

    return fig, ax

def plot_comparison(relative_months, turnover_data_list, WINDOW_BEFORE=3, normalization_point=-3, title_suffix=""):
    """
    Plot comparison of multiple turnover series on the same chart.

    Parameters:
    - relative_months: X-axis values (e.g., -3 to +12)
    - turnover_data_list: List of dicts, each containing:
        - 'data': normalized turnover array
        - 'label': legend label
        - 'color': line color
        - 'marker': marker style (default: 'o')
        - 'n_events': number of events (for label)
    - WINDOW_BEFORE: Number of months before event (default 3)
    - normalization_point: Which relative month was used for normalization (default -3)
    - title_suffix: Additional text for title (default: "")

    Returns:
    - fig, ax: Matplotlib figure and axis objects
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot each series
    for series_info in turnover_data_list:
        data = series_info['data']
        label = series_info['label']
        color = series_info['color']
        marker = series_info.get('marker', 'o')
        n_events = series_info.get('n_events', None)

        # Add event count to label if provided
        if n_events is not None:
            label = f"{label} (N={n_events:,})"

        ax.plot(relative_months, data,
                marker=marker, linewidth=2, markersize=6,
                color=color, label=label)

    # Add horizontal line at y=1.0
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=1)

    # Add vertical line at t=0 (event month)
    ax.axvline(x=0, color='red', linestyle='--', alpha=0.5, linewidth=1,
               label='Peer Shock (t=0)')

    # Add vertical line at normalization point
    ax.axvline(x=normalization_point, color='blue', linestyle='--', alpha=0.5, linewidth=1,
               label=f't={normalization_point} (Normalization Point)')

    # Formatting
    ax.set_xlabel('Months Relative to High-Quintile Peer Return', fontsize=12)
    ax.set_ylabel('Relative Average Stock Turnover', fontsize=12)

    title = 'Figure 1A: Turnover Following High-Quintile Peer Shock'
    if title_suffix:
        title += f'\n{title_suffix}'

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(relative_months)

    # Set y-axis limits based on all data
    all_data = np.concatenate([series['data'] for series in turnover_data_list])
    y_min = all_data.min() * 0.95
    y_max = all_data.max() * 1.05
    ax.set_ylim(y_min, y_max)

    plt.tight_layout()

    return fig, ax

# %%
# ========================================================================
#  SECTION 1: INITIALIZE WITH MONTHLY FIELD AS UNIVERSE
# ========================================================================

print_section("Initialize AlphaExcel with monthly_adj_close as Universe")

print("""
Using monthly_adj_close as the universe field:
- This is a MONTHLY field (one value per month)
- config/data.yaml: forward_fill=true for monthly fields
- Universe mask derived as: ~monthly_adj_close.isna()
- Forward-filled to daily frequency automatically
""")

print("\nInitializing AlphaExcel...")
print("  universe_field='monthly_adj_close'")
print("  Time range: 2010-01-01 to 2025-09-30")
print("")

ae_monthly = AlphaExcel(
    start_time='2010-01-01',
    end_time='2025-09-30',
    universe_field='monthly_adj_close',  # Use monthly field for universe
    config_path='./config'
)

print(f"[OK] AlphaExcel initialized successfully!")
print(f"     Universe field: monthly_adj_close")
print(f"     Time range: {ae_monthly._start_time} to {ae_monthly._end_time}")
print(f"     Universe shape: {ae_monthly._universe_mask._data.shape}")

# %%
# Initialize operators and field accessor for monthly instance
om = ae_monthly.ops
fm = ae_monthly.field

# %%
# ========================================================================
#  SECTION 2: INITIALIZE SECOND INSTANCE FOR DAILY DATA (TURNOVER)
# ========================================================================

print_section("Initialize Second AlphaExcel Instance for Daily Data")

print("""
Why second instance?
- Monthly instance (ae): For peer returns calculation (elegant with monthly data)
- Daily instance (ae_daily): For turnover calculation (need daily average, not end-of-month)
- This gives us best of both worlds!
""")

print("\nInitializing daily AlphaExcel...")
print("  universe_field=None (no universe masking)")
print("  Time range: 2010-01-01 to 2025-09-30")
print("")

ae_daily = AlphaExcel(
    start_time='2010-01-01',
    end_time='2025-09-30',
    universe_field=None,  # No universe masking for daily data
    config_path='./config'
)

print(f"[OK] Daily AlphaExcel initialized successfully!")
print(f"     Universe field: None (no masking)")
print(f"     Time range: {ae_daily._start_time} to {ae_daily._end_time}")

# %%
# Initialize operators and field accessor for daily instance
od = ae_daily.ops
fd = ae_daily.field

# %% [markdown]
# ## 3. Load Monthly Data for Peer Returns
#
# Monthly fields (from monthly instance):
# - fnguide_industry_group: Industry classification
# - monthly_return_pct: Monthly returns

# %%
print_section("Load Monthly Data for Peer Returns")

print("Loading industry classification data...")
industry_group = fm('fnguide_industry_group')
sector = fm('fnguide_sector')

print("\n[OK] Monthly classification fields loaded!")

# %% [markdown]
# ## 4. Calculate Share Turnover from Daily Data
#
# Why daily data?
# - Monthly aggregated data only captures end-of-month values
# - We need AVERAGE turnover during the month
# - Solution: Calculate daily turnover, then resample to monthly mean

# %%
print_section("Calculate Share Turnover from Daily Data")

print("Step 1: Load daily trading data...")
trading_value_daily = fd('fnguide_trading_value')
market_cap_daily = fd('fnguide_market_cap')

print("\nStep 2: Convert to DataFrames...")
trading_value_df = trading_value_daily.to_df()
market_cap_df = market_cap_daily.to_df()

print(f"  Trading value shape: {trading_value_df.shape}")
print(f"  Market cap shape: {market_cap_df.shape}")

print("\nStep 3: Aggregate to monthly first, then calculate turnover ratio...")
# CORRECT: Aggregate first, then calculate ratio (not average of ratios!)
# Sum trading value over month (total value traded)
monthly_trading_value = trading_value_df.resample('ME').sum()
# Average market cap over month (average market cap during month)
monthly_market_cap = market_cap_df.resample('ME').mean()

print(f"  Monthly trading value shape: {monthly_trading_value.shape}")
print(f"  Monthly market cap shape: {monthly_market_cap.shape}")
print(f"  Monthly trading value mean: {monthly_trading_value.mean().mean():,.0f}")
print(f"  Monthly market cap mean: {monthly_market_cap.mean().mean():,.0f}")

print("\nStep 4: Calculate turnover ratio = sum(trading_value) / mean(market_cap)...")
share_turnover_df = monthly_trading_value / monthly_market_cap

print(f"  Monthly turnover shape: {share_turnover_df.shape}")
print(f"  Monthly turnover mean: {share_turnover_df.mean().mean():.6f}")
print(f"  Monthly turnover median: {share_turnover_df.median().median():.6f}")

print("\n[OK] Share turnover calculated from daily data (aggregated to monthly)!")

# %% [markdown]
# ## 5. Calculate Industry Peer Returns (Monthly Data)
#
# For each firm i in industry G at time t:
# - Equal-weighted peer return = average of all other firms in same industry
#   - Formula: peer_return_i = (sum of all returns in G - return_i) / (N_G - 1)
# - Value-weighted peer return = cap-weighted average of all other firms
#   - Formula: peer_return_i = (sum of cap*ret in G - cap_i*ret_i) / (sum of cap in G - cap_i)
# - This excludes the focal firm from its own peer calculation

# %%
print_section("Calculate Industry Peer Returns")

print("Loading monthly returns...")
monthly_returns = fm('monthly_return_pct') / 100

print("Loading monthly market cap...")
cap_monthly = fm('fnguide_market_cap')

print("\nCalculating equal-weighted peer returns...")
sic_peer_returns_ew = (om.group_sum(monthly_returns, industry_group) - monthly_returns) / (om.group_count(industry_group) - 1)

print("Calculating value-weighted peer returns...")
numerator = om.group_sum(cap_monthly * monthly_returns, industry_group) - cap_monthly * monthly_returns
denominator = om.group_sum(cap_monthly, industry_group) - cap_monthly
sic_peer_returns_vw = numerator / denominator

print("\n[OK] Peer returns calculated (both EW and VW)!")

# %% [markdown]
# ## 6. Convert AlphaData to DataFrame

# %%
print_section("Convert to DataFrames")

monthly_returns_df = monthly_returns.to_df()
sic_peer_returns_ew_df = sic_peer_returns_ew.to_df()
sic_peer_returns_vw_df = sic_peer_returns_vw.to_df()

print(f"Monthly returns shape: {monthly_returns_df.shape}")
print(f"SIC peer returns (EW) shape: {sic_peer_returns_ew_df.shape}")
print(f"SIC peer returns (VW) shape: {sic_peer_returns_vw_df.shape}")
print(f"Share turnover shape: {share_turnover_df.shape}")

# Display comparison statistics
print("\n=== Comparison: Equal-Weighted vs Value-Weighted ===")
print(f"EW mean: {sic_peer_returns_ew_df.mean().mean():.6f}")
print(f"VW mean: {sic_peer_returns_vw_df.mean().mean():.6f}")
print(f"EW std:  {sic_peer_returns_ew_df.std().mean():.6f}")
print(f"VW std:  {sic_peer_returns_vw_df.std().mean():.6f}")
print(f"Correlation: {sic_peer_returns_ew_df.corrwith(sic_peer_returns_vw_df, axis=0).mean():.4f}")

# For backward compatibility with rest of script, use EW as default
# (Both EW and VW are saved in checkpoints for future analysis)
sic_peer_returns_df = sic_peer_returns_ew_df

print("\n[OK] All data converted to DataFrames!")

# Checkpoint: Save core return data
if args.save_checkpoints:
    print("\n[CHECKPOINT] Saving core return data...")
    cp.save_checkpoint(monthly_returns_df, 'checkpoint_05_own_returns.parquet', CHECKPOINT_DIR)
    cp.save_checkpoint(sic_peer_returns_ew_df, 'checkpoint_04_sic_peer_returns_ew.parquet', CHECKPOINT_DIR)
    cp.save_checkpoint(sic_peer_returns_vw_df, 'checkpoint_04_sic_peer_returns_vw.parquet', CHECKPOINT_DIR)

# %% [markdown]
# ## 7. Identify High-Quintile Peer Shock Events
#
# Event definition:
# - High-quintile = top 20% of cross-sectional peer returns each month
# - For each month, calculate 80th percentile of all peer returns
# - Mark firms whose peer return >= threshold as having an event

# %%
print_section("Identify High-Quintile Peer Shock Events")

quintile_threshold = 0.80  # Top 20%

print(f"Quintile threshold: {quintile_threshold} (top {(1-quintile_threshold)*100:.0f}%)")
print("\nIdentifying events cross-sectionally for each month...")

event_matrix = pd.DataFrame(
    index=sic_peer_returns_df.index,
    columns=sic_peer_returns_df.columns,
    dtype=bool
)

for date in sic_peer_returns_df.index:
    # Get peer returns for this date (cross-section)
    peer_returns_date = sic_peer_returns_df.loc[date]
    valid_returns = peer_returns_date.dropna()

    if len(valid_returns) > 0:
        # Calculate 80th percentile
        threshold = valid_returns.quantile(quintile_threshold)

        # Mark events (peer return >= threshold)
        event_matrix.loc[date] = peer_returns_date >= threshold
    else:
        event_matrix.loc[date] = False

event_matrix = event_matrix.fillna(False)

total_events = event_matrix.sum().sum()
print(f"\n[OK] Events identified!")
print(f"     Total events: {total_events:,}")
print(f"     Mean events per firm: {event_matrix.sum(axis=0).mean():.1f}")
print(f"     Mean events per month: {event_matrix.sum(axis=1).mean():.1f}")

# %% [markdown]
# ## 8. Extract Turnover Windows Around Events
#
# Window structure:
# - t-3 to t+12 (16 months total)
# - t=0 is the event month (high-quintile peer shock)
# - Require complete data (no missing turnover values)
# - Prevent overlapping windows (earlier events take priority)

# %%
WINDOW_BEFORE = 3
WINDOW_AFTER = 12
WINDOW_LENGTH = WINDOW_BEFORE + 1 + WINDOW_AFTER  # 16 months total

print_section("Extract Turnover Windows - Method 1: Daily Aggregation")
turnover_windows_daily = extract_turnover_windows(
    share_turnover_df,
    event_matrix,
    WINDOW_BEFORE,
    WINDOW_AFTER
)
print(f"[OK] Daily method: {len(turnover_windows_daily):,} valid windows")
print(f"     Acceptance rate: {len(turnover_windows_daily) / total_events * 100:.1f}%")

# %% [markdown]
# ## 9. Normalize and Aggregate
#
# Paper methodology: "All results are scaled so that the first month has unit turnover"
# - First month = t=-3
# - Average first, then normalize

# %%
print_section("Normalize - Method 1: Daily Aggregation")
normalized_turnover_daily = normalize_and_aggregate(turnover_windows_daily, WINDOW_BEFORE)
print(f"[OK] Daily method normalized!")
print(f"Normalized turnover (t={-WINDOW_BEFORE} = 1.0):")
for i, val in enumerate(normalized_turnover_daily):
    rel_month = i - WINDOW_BEFORE
    print(f"  t{rel_month:+3d}: {val:.4f}")

# %% [markdown]
# ## 10. Plot Results: Figure 1A
#
# Plot normalized turnover around peer shocks
# - Normalized by t=-3 (paper's method: first month has unit turnover)
# - Shows turnover pattern from t-3 to t+12 months

# %%
relative_months = np.arange(-WINDOW_BEFORE, WINDOW_AFTER + 1)

print_section("Plot Figure 1A - Method 1: Daily Aggregation")
fig1, ax1 = plot_results(
    relative_months,
    normalized_turnover_daily,
    len(turnover_windows_daily),
    "FnGuide Industry (Daily Aggregation)",
    WINDOW_BEFORE,
    -WINDOW_BEFORE,  # Normalization point is t=-3
    legend_label="FnGuide Industry",
    color='#2E86AB'
)
plt.show()
print("[OK] Daily aggregation plot complete!")

print("\n" + "=" * 80)
print("  FNGUIDE BASELINE ANALYSIS COMPLETE!")
print("=" * 80)

# %%

# %% [markdown]
# ## 11. Load Autoencoder Similarity Data
#
# Load pairwise cosine similarity matrices produced by the tnic_dl pipeline.
# - Files: data/korean_tnic_dl/by_year/{year}/similarity_autoencoder_{year}.npz  (sparse CSR)
#          data/korean_tnic_dl/by_year/{year}/firm_info_{year}.parquet            (stock_code index)
# - Peers are defined by cosine similarity > threshold on 10-dim embeddings,
#   NOT by cluster membership (Kim et al. 2020: "pairwise cosine similarity scores").
# - This replaces the previous cluster-based approach which was structurally
#   equivalent to FnGuide's fixed partition and lost the asymmetric peer benefit.

# %%
from scipy.sparse import load_npz as _load_npz

print_section("Load Autoencoder Similarity Data from deep learning module outputs")

# Define path to autoencoder data directory
autoencoder_data_dir = Path("data/korean_tnic_dl/by_year")

# Years to load (2010-2025)
autoencoder_years = range(2010, 2026)

print("Loading autoencoder similarity matrices and firm info from all years...")
autoencoder_sim_data = {}  # year → {'similarity': sparse_csr_matrix, 'firm_info': DataFrame}

for year in tqdm(autoencoder_years, desc="Loading similarity files"):
    year_dir = autoencoder_data_dir / str(year)
    sim_path  = year_dir / f"similarity_autoencoder_{year}.npz"
    info_path = year_dir / f"firm_info_{year}.parquet"

    if sim_path.exists() and info_path.exists():
        sim_matrix = _load_npz(str(sim_path))          # scipy sparse CSR (N × N)
        firm_info  = pd.read_parquet(info_path)
        # Normalise stock_code to 6-digit zero-padded string
        firm_info['stock_code'] = firm_info['stock_code'].astype(str).str.zfill(6)

        autoencoder_sim_data[year] = {
            'similarity': sim_matrix,
            'firm_info':  firm_info,
        }
        print(f"  [OK] {year}: {sim_matrix.shape[0]:,} firms, "
              f"NNZ={sim_matrix.nnz:,}, "
              f"density={sim_matrix.nnz / sim_matrix.shape[0]**2 * 100:.2f}%")
    else:
        missing = []
        if not sim_path.exists():  missing.append("similarity.npz")
        if not info_path.exists(): missing.append("firm_info.parquet")
        print(f"  [MISSING] {year}: {', '.join(missing)}")

years_loaded = sorted(autoencoder_sim_data.keys())
print(f"\n[OK] Autoencoder similarity data loaded for {len(years_loaded)} years: "
      f"{min(years_loaded) if years_loaded else 'N/A'} – {max(years_loaded) if years_loaded else 'N/A'}")

# %% [markdown]
# ## 12. Stock Code Conversion Functions
#
# Create functions to convert between FnGuide and autoencoder stock code formats
# - FnGuide format: "A" + 6-digit code (e.g., "A000020")
# - Autoencoder format: 6-digit code (e.g., "000020")

# %%
print_section("Define Stock Code Conversion Functions")

def fnguide_to_autoencoder(fnguide_code):
    """
    Convert FnGuide stock code format to autoencoder format.

    FnGuide: "A000020" -> Autoencoder: "000020"

    Args:
        fnguide_code: Stock code with "A" prefix

    Returns:
        Stock code without prefix (6-digit zero-padded)
    """
    code_str = str(fnguide_code)
    if len(code_str) > 6 and code_str[0].isalpha():
        return code_str[1:]  # Remove first character (prefix)
    return code_str

def autoencoder_to_fnguide(autoencoder_code):
    """
    Convert autoencoder stock code format to FnGuide format.

    Autoencoder: "000020" -> FnGuide: "A000020"

    Args:
        autoencoder_code: 6-digit zero-padded stock code

    Returns:
        Stock code with "A" prefix
    """
    code_str = str(autoencoder_code)
    # Ensure 6-digit zero-padding
    code_str = code_str.zfill(6)
    if len(code_str) == 6 and code_str.isdigit():
        return "A" + code_str
    return code_str

# Test conversion functions
print("Testing conversion functions:\n")
test_cases = [
    ("A000020", "000020"),
    ("A005930", "005930"),
    ("A035720", "035720"),
]

all_passed = True
for fnguide, expected_autoencoder in test_cases:
    converted = fnguide_to_autoencoder(fnguide)
    reverse = autoencoder_to_fnguide(converted)
    passed = (converted == expected_autoencoder) and (reverse == fnguide)
    status = "[OK]" if passed else "[FAIL]"
    print(f"  {status} {fnguide} -> {converted} -> {reverse}")
    print(f"      Expected autoencoder: {expected_autoencoder}, Match: {converted == expected_autoencoder}")
    all_passed = all_passed and passed

if all_passed:
    print("\n[OK] All conversion tests passed!")
else:
    print("\n[WARNING] Some conversion tests failed!")

# %%

# %% [markdown]
# ## 13. Define Universe for Fair Autoencoder vs FnGuide Comparison
#
# To ensure fair comparison between autoencoder and FnGuide peer returns:
# - Extract universe from sic_peer_returns_df (non-NaN values at end-of-year)
# - Calculate autoencoder peer returns only for stocks in this universe
# - This controls for survivorship bias and data availability differences

# %%
print_section("Define Universe for Fair Comparison")

print("Extracting end-of-year (EOY) observations from sic_peer_returns_df...")
print("  Using resample('YE') for robust year-end selection\n")

# Use resample to get year-end (more robust than filtering for day==31)
# This handles non-trading days automatically
# Note: Use 'A' for older pandas, 'YE' for pandas >= 2.2
try:
    eoy_data = sic_peer_returns_df.resample('YE').last()
except ValueError:
    # Fallback for older pandas versions
    eoy_data = sic_peer_returns_df.resample('A').last()

eoy_dates = eoy_data.dropna(how='all').index

# Filter to only dates that actually exist in sic_peer_returns_df
eoy_dates = eoy_dates.intersection(sic_peer_returns_df.index)

print(f"  Found {len(eoy_dates)} EOY dates: {eoy_dates.year.min()} - {eoy_dates.year.max()}")

# Build universe dictionary: year → list of stock codes (in autoencoder format)
universe_by_year = {}

for eoy_date in eoy_dates:
    year = eoy_date.year

    # Get all stocks with non-NaN peer returns at this EOY date
    valid_stocks_fnguide = sic_peer_returns_df.loc[eoy_date].dropna().index.tolist()

    # Convert to autoencoder format (remove "A" prefix)
    valid_stocks_autoencoder = [fnguide_to_autoencoder(s) for s in valid_stocks_fnguide]

    universe_by_year[year] = valid_stocks_autoencoder
    print(f"  {year}: {len(valid_stocks_autoencoder)} stocks in universe (converted to autoencoder format)")

print(f"\n[OK] Universe defined for {len(universe_by_year)} years!")
print(f"     Average stocks per year: {np.mean([len(v) for v in universe_by_year.values()]):.0f}")
print(f"     Min stocks: {min([len(v) for v in universe_by_year.values()])}")
print(f"     Max stocks: {max([len(v) for v in universe_by_year.values()])}")

# Checkpoint: Save universe
if args.save_checkpoints:
    print("\n[CHECKPOINT] Saving universe_by_year...")
    cp.save_checkpoint(universe_by_year, 'checkpoint_07_universe.pkl', CHECKPOINT_DIR)

# %%
print("\nPlotting universe coverage over time...")

# Count non-NaN stocks cross-sectionally for each date
universe_coverage = sic_peer_returns_df.count(axis=1)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(universe_coverage.index, universe_coverage.values, linewidth=2, color='#2E86AB')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Number of Stocks in Universe', fontsize=12)
ax.set_title('Universe Coverage Over Time (FnGuide Non-NaN Stocks)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print(f"  Min stocks: {universe_coverage.min()} on {universe_coverage.idxmin().strftime('%Y-%m-%d')}")
print(f"  Max stocks: {universe_coverage.max()} on {universe_coverage.idxmax().strftime('%Y-%m-%d')}")
print(f"  Mean stocks: {universe_coverage.mean():.0f}")

print("\n[OK] Universe coverage plot complete!")

# %% [markdown]
# ## 14. Build Cosine Similarity-Based Peer Lookup Dictionary
#
# Defines peers using pairwise cosine similarity on 10-dim autoencoder embeddings,
# replacing the previous cluster-membership approach.
#
# Kim et al. (2020): "Compute pairwise cosine similarity scores between firms
# using the 10-dimensional reduced feature vectors."
#
# A fixed threshold (SIMILARITY_THRESHOLD) is applied; firms j with
# similarity(i, j) > threshold are defined as peers of i.
# This preserves the asymmetric peer relationship that cluster membership lost.

# %%
print_section("Build Cosine Similarity-Based Peer Lookup Dictionary")

# Similarity threshold: matches tnic_dl.similarity.threshold in config/tnic_dl.yaml
SIMILARITY_THRESHOLD = 0.20

print(f"Peer definition: cosine similarity on 10-dim embeddings > {SIMILARITY_THRESHOLD}")
print(f"  (Fixed threshold; can be calibrated to FnGuide membership fraction later)\n")

# Dictionary: (stock_code, year) → list of peer stock_codes (similarity > threshold)
autoencoder_peer_dict = {}

# Statistics tracking (same keys as before for downstream compatibility)
peer_counts_by_year = {}
orphan_missing_autoencoder = set()  # Stocks in universe but with no similarity data

for year in tqdm(range(2010, 2026), desc="Building cosine-sim peer lookup"):
    if year not in autoencoder_sim_data:
        # No similarity data for this year — all universe stocks are orphans
        for stock_code in universe_by_year.get(year, []):
            orphan_missing_autoencoder.add(stock_code)
        continue

    sim_matrix = autoencoder_sim_data[year]['similarity']   # sparse CSR (N × N)
    firm_info  = autoencoder_sim_data[year]['firm_info']    # DataFrame with 'stock_code'

    # Build index → stock_code lookup (O(1) per firm)
    idx_to_code = firm_info['stock_code'].tolist()
    code_to_idx = {code: i for i, code in enumerate(idx_to_code)}

    N = sim_matrix.shape[0]
    sim_dense = sim_matrix.toarray()  # (N × N) dense float32

    peer_counts_this_year = []

    for i in range(N):
        stock_code_i = idx_to_code[i]

        # All firms j where similarity > threshold, excluding self
        peer_mask    = sim_dense[i] > SIMILARITY_THRESHOLD
        peer_mask[i] = False
        peer_indices = np.where(peer_mask)[0]

        peers = [idx_to_code[j] for j in peer_indices]
        autoencoder_peer_dict[(stock_code_i, year)] = peers
        peer_counts_this_year.append(len(peers))

    if peer_counts_this_year:
        peer_counts_by_year[year] = {
            'mean':     float(np.mean(peer_counts_this_year)),
            'median':   float(np.median(peer_counts_this_year)),
            'std':      float(np.std(peer_counts_this_year)),
            'max':      int(np.max(peer_counts_this_year)),
            'n_stocks': len(peer_counts_this_year),
        }

    # Track universe stocks with no similarity data
    ae_stocks_this_year = set(idx_to_code)
    for stock_code in universe_by_year.get(year, []):
        if stock_code not in ae_stocks_this_year:
            orphan_missing_autoencoder.add(stock_code)

print(f"\n[OK] Cosine similarity peer lookup dictionary built!")
print(f"     Total (stock, year) pairs: {len(autoencoder_peer_dict):,}")
print(f"     Stocks in universe with no similarity data: {len(orphan_missing_autoencoder):,}")

print("\nPeer statistics by year (cosine similarity > threshold):")
for year in sorted(peer_counts_by_year.keys()):
    stats = peer_counts_by_year[year]
    print(f"  {year}: {stats['n_stocks']:4d} stocks, "
          f"avg peers={stats['mean']:5.1f}, "
          f"median={stats['median']:4.0f}, "
          f"max={stats['max']:3d}")

all_peer_counts = [len(peers) for peers in autoencoder_peer_dict.values()]
if all_peer_counts:
    print(f"\nOverall cosine-similarity peer statistics (all years):")
    print(f"  Average peers per stock: {np.mean(all_peer_counts):.1f}")
    print(f"  Median peers per stock:  {np.median(all_peer_counts):.0f}")
    print(f"  Std dev:                 {np.std(all_peer_counts):.1f}")
    print(f"  Max peers:               {np.max(all_peer_counts)}")
    print(f"  Min peers:               {np.min(all_peer_counts)}")

# Checkpoint: Save peer dictionary
if args.save_checkpoints:
    print("\n[CHECKPOINT] Saving cosine similarity peer lookup dictionary...")
    cp.save_checkpoint(autoencoder_peer_dict, 'checkpoint_02_autoencoder_peer_dict.pkl', CHECKPOINT_DIR)

# %% [markdown]
# ## 15. Calculate Autoencoder-Based Peer Returns
#
# Calculate peer returns using cosine similarity-based autoencoder peers:
# - Use 1-year lag: 2010 similarity data → 2011 peer returns (avoid look-ahead bias)
# - Only calculate for stocks in universe (fair comparison with FnGuide)
# - Equal-weighted peer returns (matching paper methodology)
# - Handle missing data gracefully (NaN for stocks with no similarity data or below threshold)

# %%
print_section("Calculate Autoencoder-Based Peer Returns")

print("Initializing empty panel (same structure as monthly_returns_df)...")

# Initialize empty DataFrame with same shape as monthly_returns
autoencoder_peer_returns_df = pd.DataFrame(
    index=monthly_returns_df.index,
    columns=monthly_returns_df.columns,
    dtype=float
)

print(f"  Panel shape: {autoencoder_peer_returns_df.shape}")
print(f"  Date range: {autoencoder_peer_returns_df.index.min()} to {autoencoder_peer_returns_df.index.max()}")

print("\nCalculating autoencoder peer returns with 1-year lag...")
print("  (2010 clusters -> 2011 months, 2011 clusters -> 2012 months, etc.)\n")

# Track statistics
n_calculated = 0
n_no_peers = 0
n_orphans = 0
n_skipped_no_clusters = 0

# Calculate autoencoder peer returns
for date in tqdm(monthly_returns_df.index, desc="Processing dates"):
    current_year = date.year

    # Use previous year's cluster data (1-year lag to avoid look-ahead bias)
    # 2010 clusters -> 2011 months, 2011 clusters -> 2012 months
    if current_year >= 2011:
        cluster_year = current_year - 1
    else:
        # Skip 2010 (no clusters for 2009)
        n_skipped_no_clusters += len(monthly_returns_df.columns)
        continue

    # Get universe for current year (stock codes in autoencoder format)
    universe_stocks_autoencoder = universe_by_year.get(current_year, [])

    for stock_code_autoencoder in universe_stocks_autoencoder:
        # stock_code_autoencoder is in autoencoder format (e.g., "000020")

        # Lookup cluster peers for this stock-year (peers are also in autoencoder format)
        peers_autoencoder = autoencoder_peer_dict.get((stock_code_autoencoder, cluster_year), [])

        if len(peers_autoencoder) > 0:
            # Convert peer codes to FnGuide format for indexing monthly_returns_df
            peers_fnguide = [autoencoder_to_fnguide(p) for p in peers_autoencoder]

            # Filter to only peers that exist in monthly_returns columns
            valid_peers = [p for p in peers_fnguide if p in monthly_returns_df.columns]

            if len(valid_peers) > 0:
                peer_returns = monthly_returns_df.loc[date, valid_peers]

                # Equal-weighted average (NaN automatically excluded by .mean())
                # Store using FnGuide format (to match monthly_returns_df columns)
                stock_code_fnguide = autoencoder_to_fnguide(stock_code_autoencoder)
                autoencoder_peer_returns_df.loc[date, stock_code_fnguide] = peer_returns.mean()
                n_calculated += 1
            else:
                # Peers exist but none have return data
                stock_code_fnguide = autoencoder_to_fnguide(stock_code_autoencoder)
                autoencoder_peer_returns_df.loc[date, stock_code_fnguide] = np.nan
                n_no_peers += 1
        else:
            # No cluster peers for this stock-year (orphan or single-stock cluster)
            stock_code_fnguide = autoencoder_to_fnguide(stock_code_autoencoder)
            autoencoder_peer_returns_df.loc[date, stock_code_fnguide] = np.nan

            if stock_code_autoencoder in orphan_missing_autoencoder:
                n_orphans += 1
            else:
                n_no_peers += 1

print(f"\n[OK] Autoencoder peer returns calculated!")
print(f"     Successfully calculated: {n_calculated:,} stock-dates")
print(f"     No cluster peers: {n_no_peers:,} stock-dates")
print(f"     Orphan stocks (missing clusters): {n_orphans:,} stock-dates")
print(f"     Skipped (no clusters for year): {n_skipped_no_clusters:,} stock-dates")

# Summary statistics
print(f"\nAutoencoder peer return statistics:")
print(f"  Shape: {autoencoder_peer_returns_df.shape}")
print(f"  Non-NaN values: {autoencoder_peer_returns_df.count().sum():,} ({autoencoder_peer_returns_df.count().sum() / autoencoder_peer_returns_df.size * 100:.1f}%)")
print(f"  Mean: {autoencoder_peer_returns_df.mean().mean():.6f}")
print(f"  Std: {autoencoder_peer_returns_df.std().mean():.6f}")
print(f"  Min: {autoencoder_peer_returns_df.min().min():.6f}")
print(f"  Max: {autoencoder_peer_returns_df.max().max():.6f}")

# Checkpoint: Save autoencoder peer returns
if args.save_checkpoints:
    print("\n[CHECKPOINT] Saving autoencoder peer returns...")
    cp.save_checkpoint(autoencoder_peer_returns_df, 'checkpoint_03_autoencoder_peer_returns.parquet', CHECKPOINT_DIR)

# %% [markdown]
# ## 16. Identify Autoencoder High-Quintile Peer Shock Events
#
# Event definition (same methodology as FnGuide):
# - High-quintile = top 20% of cross-sectional autoencoder peer returns each month
# - For each month, calculate 80th percentile of all autoencoder peer returns
# - Mark firms whose autoencoder peer return >= threshold as having an event

# %%
print_section("Identify Autoencoder High-Quintile Peer Shock Events")

quintile_threshold = 0.80  # Top 20%

print(f"Quintile threshold: {quintile_threshold} (top {(1-quintile_threshold)*100:.0f}%)")
print("\nIdentifying autoencoder events cross-sectionally for each month...")

autoencoder_event_matrix = pd.DataFrame(
    index=autoencoder_peer_returns_df.index,
    columns=autoencoder_peer_returns_df.columns,
    dtype=bool
)

for date in autoencoder_peer_returns_df.index:
    # Get autoencoder peer returns for this date (cross-section)
    peer_returns_date = autoencoder_peer_returns_df.loc[date]
    valid_returns = peer_returns_date.dropna()

    if len(valid_returns) > 0:
        # Calculate 80th percentile
        threshold = valid_returns.quantile(quintile_threshold)

        # Mark events (peer return >= threshold)
        autoencoder_event_matrix.loc[date] = peer_returns_date >= threshold
    else:
        autoencoder_event_matrix.loc[date] = False

autoencoder_event_matrix = autoencoder_event_matrix.fillna(False)

total_autoencoder_events = autoencoder_event_matrix.sum().sum()
print(f"\n[OK] Autoencoder events identified!")
print(f"     Total events: {total_autoencoder_events:,}")
print(f"     Mean events per firm: {autoencoder_event_matrix.sum(axis=0).mean():.1f}")
print(f"     Mean events per month: {autoencoder_event_matrix.sum(axis=1).mean():.1f}")

# Compare with FnGuide events
print(f"\nComparison with FnGuide:")
print(f"     FnGuide total events: {total_events:,}")
print(f"     Autoencoder total events: {total_autoencoder_events:,}")
print(f"     Ratio (Autoencoder/FnGuide): {total_autoencoder_events / total_events:.2f}")

# %% [markdown]
# ## 17. Extract Autoencoder Turnover Windows Around Events
#
# Window structure (same as FnGuide):
# - t-3 to t+12 (16 months total)
# - t=0 is the event month (high-quintile autoencoder peer shock)
# - Require complete data (no missing turnover values)
# - Prevent overlapping windows (earlier events take priority)

# %%
print_section("Extract Autoencoder Turnover Windows")

turnover_windows_autoencoder = extract_turnover_windows(
    share_turnover_df,
    autoencoder_event_matrix,
    WINDOW_BEFORE,
    WINDOW_AFTER
)

print(f"[OK] Autoencoder method: {len(turnover_windows_autoencoder):,} valid windows")
print(f"     Acceptance rate: {len(turnover_windows_autoencoder) / total_autoencoder_events * 100:.1f}%")

print(f"\nComparison with FnGuide:")
print(f"     FnGuide valid windows: {len(turnover_windows_daily):,}")
print(f"     Autoencoder valid windows: {len(turnover_windows_autoencoder):,}")
print(f"     Ratio (Autoencoder/FnGuide): {len(turnover_windows_autoencoder) / len(turnover_windows_daily):.2f}")

# %% [markdown]
# ## 18. Normalize and Plot Autoencoder Figure 1A
#
# Paper methodology: "All results are scaled so that the first month has unit turnover"
# - First month = t=-3
# - Average first, then normalize
# - Compare with FnGuide baseline

# %%
print_section("Normalize Autoencoder Turnover")

normalized_turnover_autoencoder = normalize_and_aggregate(turnover_windows_autoencoder, WINDOW_BEFORE)

print(f"[OK] Autoencoder method normalized!")
print(f"Normalized turnover (t={-WINDOW_BEFORE} = 1.0):")
for i, val in enumerate(normalized_turnover_autoencoder):
    rel_month = i - WINDOW_BEFORE
    print(f"  t{rel_month:+3d}: {val:.4f}")

# %%
print_section("Plot Figure 1A - Autoencoder Clusters")

relative_months = np.arange(-WINDOW_BEFORE, WINDOW_AFTER + 1)

fig_autoencoder, ax_autoencoder = plot_results(
    relative_months,
    normalized_turnover_autoencoder,
    len(turnover_windows_autoencoder),
    "Autoencoder Clusters",
    WINDOW_BEFORE,
    -WINDOW_BEFORE,  # Normalization point is t=-3
    legend_label="Autoencoder Clusters",
    color='#F26419'
)
plt.show()
print("[OK] Autoencoder plot complete!")

# %% [markdown]
# ## 19. Comparison Plot: FnGuide vs Autoencoder
#
# Direct visual comparison of turnover patterns:
# - FnGuide Industry (highly visible peers)
# - Autoencoder Clusters (less visible peers)
#
# Hypothesis: Autoencoder should show longer persistence due to investor inattention

# %%
print_section("Plot Comparison: FnGuide vs Autoencoder")

# Prepare data for comparison plot
turnover_series = [
    {
        'data': normalized_turnover_daily,
        'label': 'FnGuide Industry',
        'color': '#2E86AB',
        'marker': 'o',
        'n_events': len(turnover_windows_daily)
    },
    {
        'data': normalized_turnover_autoencoder,
        'label': 'Autoencoder Clusters',
        'color': '#F26419',
        'marker': 's',
        'n_events': len(turnover_windows_autoencoder)
    }
]

fig_comparison, ax_comparison = plot_comparison(
    relative_months,
    turnover_series,
    WINDOW_BEFORE=WINDOW_BEFORE,
    normalization_point=-WINDOW_BEFORE,
    title_suffix="Comparison: FnGuide Industry vs Autoencoder Clusters"
)

# Save Figure 1A
output_path_1a = Path("outputs") / "figure1a_unconditional_turnover_autoencoder.png"
output_path_1a.parent.mkdir(parents=True, exist_ok=True)
fig_comparison.savefig(output_path_1a, dpi=300, bbox_inches='tight')
print(f"[OK] Saved Figure 1A to: {output_path_1a}")

plt.show()

print("[OK] Comparison plot complete!")

# %% [markdown]
# ## 20. Statistical Comparison: FnGuide vs Autoencoder
#
# Quantitative comparison of turnover patterns:
# - Event counts
# - Turnover persistence (t=0, t+6, t+12)
# - Hypothesis testing

# %%
print_section("Statistical Comparison: FnGuide vs Autoencoder")

print("Event Statistics:")
print(f"  FnGuide total events: {total_events:,}")
print(f"  Autoencoder total events: {total_autoencoder_events:,}")
print(f"  FnGuide valid windows: {len(turnover_windows_daily):,} ({len(turnover_windows_daily)/total_events*100:.1f}% acceptance)")
print(f"  Autoencoder valid windows: {len(turnover_windows_autoencoder):,} ({len(turnover_windows_autoencoder)/total_autoencoder_events*100:.1f}% acceptance)")

print("\nNormalized Turnover at Key Time Points:")
print(f"  {'Time':<10} {'FnGuide':>12} {'Autoencoder':>12} {'Difference':>12}")
print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*12}")

key_points = [
    (-3, "t=-3 (norm)", -3),
    (0, "t=0 (event)", 0),
    (3, "t=+3", 3),
    (6, "t=+6", 6),
    (9, "t=+9", 9),
    (12, "t=+12", 12)
]

for rel_month, label, idx_offset in key_points:
    idx = WINDOW_BEFORE + idx_offset
    fnguide_val = normalized_turnover_daily[idx]
    autoencoder_val = normalized_turnover_autoencoder[idx]
    diff = autoencoder_val - fnguide_val
    print(f"  {label:<10} {fnguide_val:12.4f} {autoencoder_val:12.4f} {diff:+12.4f}")

print("\nTurnover Persistence Analysis:")
# Calculate average turnover in post-event windows
post_event_early = slice(WINDOW_BEFORE + 1, WINDOW_BEFORE + 4)  # t+1 to t+3
post_event_mid = slice(WINDOW_BEFORE + 4, WINDOW_BEFORE + 7)    # t+4 to t+6
post_event_late = slice(WINDOW_BEFORE + 7, WINDOW_BEFORE + 13)  # t+7 to t+12

fnguide_early = normalized_turnover_daily[post_event_early].mean()
fnguide_mid = normalized_turnover_daily[post_event_mid].mean()
fnguide_late = normalized_turnover_daily[post_event_late].mean()

autoencoder_early = normalized_turnover_autoencoder[post_event_early].mean()
autoencoder_mid = normalized_turnover_autoencoder[post_event_mid].mean()
autoencoder_late = normalized_turnover_autoencoder[post_event_late].mean()

print(f"  Average turnover t+1 to t+3:")
print(f"    FnGuide: {fnguide_early:.4f}")
print(f"    Autoencoder: {autoencoder_early:.4f}")
print(f"    Difference: {autoencoder_early - fnguide_early:+.4f}")

print(f"  Average turnover t+4 to t+6:")
print(f"    FnGuide: {fnguide_mid:.4f}")
print(f"    Autoencoder: {autoencoder_mid:.4f}")
print(f"    Difference: {autoencoder_mid - fnguide_mid:+.4f}")

print(f"  Average turnover t+7 to t+12:")
print(f"    FnGuide: {fnguide_late:.4f}")
print(f"    Autoencoder: {autoencoder_late:.4f}")
print(f"    Difference: {autoencoder_late - fnguide_late:+.4f}")

print("\n" + "=" * 80)
print("  AUTOENCODER FIGURE 1A ANALYSIS COMPLETE!")
print("=" * 80)

# %% [markdown]
# ## 21. Calculate Quintile Rankings for Both Peer Groups
#
# For Graph B, we need to identify conditional events:
# - FnGuide Q5 AND Autoencoder Q3 (visible shock, invisible control)
# - Autoencoder Q5 AND FnGuide Q3 (invisible shock, visible control)
#
# Methodology:
# - Use pd.qcut() for quintile assignment (equal-sized bins)
# - Use pd.quantile() for threshold reporting (transparency)
# - Handle ties with duplicates='drop'

# %%
print_section("Calculate Quintile Rankings for Both Peer Groups")

print("Creating quintile matrices for FnGuide and Autoencoder peer returns...")
print("  Method: pd.qcut() for assignment (equal-sized bins)")
print("  Reporting: pd.quantile() for thresholds (transparency)\n")

# Initialize quintile matrices
quintile_fnguide = pd.DataFrame(
    index=sic_peer_returns_df.index,
    columns=sic_peer_returns_df.columns,
    dtype='Int64'  # Nullable integer type
)

quintile_autoencoder = pd.DataFrame(
    index=autoencoder_peer_returns_df.index,
    columns=autoencoder_peer_returns_df.columns,
    dtype='Int64'
)

# Track quintile assignment statistics
n_success_fnguide = 0
n_success_autoencoder = 0
n_fail_fnguide = 0
n_fail_autoencoder = 0

# Sample dates for threshold reporting (first, middle, last)
sample_dates = [
    sic_peer_returns_df.index[0],
    sic_peer_returns_df.index[len(sic_peer_returns_df)//2],
    sic_peer_returns_df.index[-1]
]

print("Calculating quintiles for each month...")
for date in sic_peer_returns_df.index:
    # FnGuide quintiles
    try:
        quintile_fnguide.loc[date] = pd.qcut(
            sic_peer_returns_df.loc[date],
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates='drop'
        )
        n_success_fnguide += 1

        # Report thresholds for sample dates
        if date in sample_dates:
            q20 = sic_peer_returns_df.loc[date].quantile(0.20)
            q40 = sic_peer_returns_df.loc[date].quantile(0.40)
            q60 = sic_peer_returns_df.loc[date].quantile(0.60)
            q80 = sic_peer_returns_df.loc[date].quantile(0.80)
            print(f"  {date.strftime('%Y-%m-%d')} FnGuide quintile breakpoints:")
            print(f"    Q1-Q2: {q20:+.4f}, Q2-Q3: {q40:+.4f}, Q3-Q4: {q60:+.4f}, Q4-Q5: {q80:+.4f}")
    except (ValueError, TypeError) as e:
        quintile_fnguide.loc[date] = pd.NA
        n_fail_fnguide += 1

    # Autoencoder quintiles
    try:
        quintile_autoencoder.loc[date] = pd.qcut(
            autoencoder_peer_returns_df.loc[date],
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates='drop'
        )
        n_success_autoencoder += 1

        # Report thresholds for sample dates
        if date in sample_dates:
            q20 = autoencoder_peer_returns_df.loc[date].quantile(0.20)
            q40 = autoencoder_peer_returns_df.loc[date].quantile(0.40)
            q60 = autoencoder_peer_returns_df.loc[date].quantile(0.60)
            q80 = autoencoder_peer_returns_df.loc[date].quantile(0.80)
            print(f"  {date.strftime('%Y-%m-%d')} Autoencoder quintile breakpoints:")
            print(f"    Q1-Q2: {q20:+.4f}, Q2-Q3: {q40:+.4f}, Q3-Q4: {q60:+.4f}, Q4-Q5: {q80:+.4f}")
    except (ValueError, TypeError) as e:
        quintile_autoencoder.loc[date] = pd.NA
        n_fail_autoencoder += 1

print(f"\n[OK] Quintile assignment complete!")
print(f"     FnGuide: {n_success_fnguide} successful, {n_fail_fnguide} failed")
print(f"     Autoencoder: {n_success_autoencoder} successful, {n_fail_autoencoder} failed")

# Verify quintile distributions
print(f"\nQuintile distribution check (should be ~20% each):")
for q in [1, 2, 3, 4, 5]:
    fnguide_pct = (quintile_fnguide == q).sum().sum() / quintile_fnguide.notna().sum().sum() * 100
    autoencoder_pct = (quintile_autoencoder == q).sum().sum() / quintile_autoencoder.notna().sum().sum() * 100
    print(f"  Q{q}: FnGuide {fnguide_pct:.1f}%, Autoencoder {autoencoder_pct:.1f}%")

# Checkpoint: Save quintiles (CRITICAL - saves 14 minutes!)
if args.save_checkpoints:
    print("\n[CHECKPOINT] Saving quintile rankings (14-minute calculation)...")
    # Combine into single file with multi-level index
    quintiles_combined = pd.concat([
        quintile_fnguide,
        quintile_autoencoder
    ], keys=['fnguide', 'autoencoder'], names=['source', 'date'])
    cp.save_checkpoint(quintiles_combined, 'checkpoint_01_quintiles_autoencoder.parquet', CHECKPOINT_DIR,
                      metadata={'description': 'Quintile rankings for both FnGuide and Autoencoder peer returns'})

# %% [markdown]
# ## 22. Identify Conditional Events (Graph B)
#
# Event definitions:
# - Event Type 1: FnGuide Q5 AND Autoencoder Q3 (visible shock without invisible shock)
# - Event Type 2: Autoencoder Q5 AND FnGuide Q3 (invisible shock without visible shock)
#
# These events are mutually exclusive and test clean separation of peer group effects.

# %%
print_section("Identify Conditional Events (Graph B)")

print("Event definitions:")
print("  Type 1: FnGuide Q5 AND Autoencoder Q3 (visible shock, invisible control)")
print("  Type 2: Autoencoder Q5 AND FnGuide Q3 (invisible shock, visible control)\n")

# Event Type 1: FnGuide Q5 AND Autoencoder Q3
event_fnguide_only = (quintile_fnguide == 5) & (quintile_autoencoder == 3)
event_fnguide_only = event_fnguide_only.fillna(False)

# Event Type 2: Autoencoder Q5 AND FnGuide Q3
event_autoencoder_only = (quintile_autoencoder == 5) & (quintile_fnguide == 3)
event_autoencoder_only = event_autoencoder_only.fillna(False)

# Count events
total_fnguide_only = event_fnguide_only.sum().sum()
total_autoencoder_only = event_autoencoder_only.sum().sum()

print(f"[OK] Conditional events identified!")
print(f"\nEvent Type 1 (FnGuide Q5 & Autoencoder Q3):")
print(f"  Total events: {total_fnguide_only:,}")
print(f"  Mean events per firm: {event_fnguide_only.sum(axis=0).mean():.1f}")
print(f"  Mean events per month: {event_fnguide_only.sum(axis=1).mean():.1f}")

print(f"\nEvent Type 2 (Autoencoder Q5 & FnGuide Q3):")
print(f"  Total events: {total_autoencoder_only:,}")
print(f"  Mean events per firm: {event_autoencoder_only.sum(axis=0).mean():.1f}")
print(f"  Mean events per month: {event_autoencoder_only.sum(axis=1).mean():.1f}")

# Compare with unconditional events (Graph A)
print(f"\nComparison with Graph A (unconditional events):")
print(f"  FnGuide Q5 (any Autoencoder): {total_events:,} events")
print(f"  FnGuide Q5 & Autoencoder Q3: {total_fnguide_only:,} events ({total_fnguide_only/total_events*100:.1f}%)")
print(f"  Autoencoder Q5 (any FnGuide): {total_autoencoder_events:,} events")
print(f"  Autoencoder Q5 & FnGuide Q3: {total_autoencoder_only:,} events ({total_autoencoder_only/total_autoencoder_events*100:.1f}%)")

# Check mutual exclusivity
overlap = (event_fnguide_only & event_autoencoder_only).sum().sum()
print(f"\nMutual exclusivity check:")
print(f"  Events in both types: {overlap} (should be 0)")

# %% [markdown]
# ## 23. Extract Turnover Windows for Conditional Events
#
# Extract turnover windows (t-3 to t+12) separately for each event type:
# - FnGuide-only events
# - Autoencoder-only events
#
# Use same extraction logic as Graph A (reuse function).

# %%
print_section("Extract Turnover Windows for Conditional Events")

print("Extracting windows for FnGuide-only events (FnGuide Q5 & Autoencoder Q3)...")
turnover_windows_fnguide_only = extract_turnover_windows(
    share_turnover_df,
    event_fnguide_only,
    WINDOW_BEFORE,
    WINDOW_AFTER
)

print(f"[OK] FnGuide-only: {len(turnover_windows_fnguide_only):,} valid windows")
print(f"     Acceptance rate: {len(turnover_windows_fnguide_only) / total_fnguide_only * 100:.1f}%")

print("\nExtracting windows for Autoencoder-only events (Autoencoder Q5 & FnGuide Q3)...")
turnover_windows_autoencoder_only = extract_turnover_windows(
    share_turnover_df,
    event_autoencoder_only,
    WINDOW_BEFORE,
    WINDOW_AFTER
)

print(f"[OK] Autoencoder-only: {len(turnover_windows_autoencoder_only):,} valid windows")
print(f"     Acceptance rate: {len(turnover_windows_autoencoder_only) / total_autoencoder_only * 100:.1f}%")

print(f"\nComparison with Graph A:")
print(f"  Graph A FnGuide (unconditional): {len(turnover_windows_daily):,} windows")
print(f"  Graph B FnGuide-only (conditional): {len(turnover_windows_fnguide_only):,} windows ({len(turnover_windows_fnguide_only)/len(turnover_windows_daily)*100:.1f}%)")
print(f"  Graph A Autoencoder (unconditional): {len(turnover_windows_autoencoder):,} windows")
print(f"  Graph B Autoencoder-only (conditional): {len(turnover_windows_autoencoder_only):,} windows ({len(turnover_windows_autoencoder_only)/len(turnover_windows_autoencoder)*100:.1f}%)")

# %% [markdown]
# ## 24. Normalize and Plot Graph B
#
# Normalize turnover by t=-3 and create comparison plot:
# - FnGuide-only events (visible shock, invisible control)
# - Autoencoder-only events (invisible shock, visible control)
#
# Expected pattern (H&P 2018):
# - FnGuide-only: Immediate spike at t=0, quick reversion
# - Autoencoder-only: Delayed response, persistent elevation

# %%
print_section("Normalize Turnover for Graph B")

# Normalize FnGuide-only events
normalized_turnover_fnguide_only = normalize_and_aggregate(
    turnover_windows_fnguide_only,
    WINDOW_BEFORE
)

print(f"[OK] FnGuide-only normalized!")
print(f"Normalized turnover (t={-WINDOW_BEFORE} = 1.0):")
for i, val in enumerate(normalized_turnover_fnguide_only):
    rel_month = i - WINDOW_BEFORE
    print(f"  t{rel_month:+3d}: {val:.4f}")

# Normalize Autoencoder-only events
print(f"\n")
normalized_turnover_autoencoder_only = normalize_and_aggregate(
    turnover_windows_autoencoder_only,
    WINDOW_BEFORE
)

print(f"[OK] Autoencoder-only normalized!")
print(f"Normalized turnover (t={-WINDOW_BEFORE} = 1.0):")
for i, val in enumerate(normalized_turnover_autoencoder_only):
    rel_month = i - WINDOW_BEFORE
    print(f"  t{rel_month:+3d}: {val:.4f}")

# %%
print_section("Plot Figure 1B - Conditional Turnover")

relative_months = np.arange(-WINDOW_BEFORE, WINDOW_AFTER + 1)

# Prepare data for comparison plot
turnover_series_conditional = [
    {
        'data': normalized_turnover_fnguide_only,
        'label': 'FnGuide Q5 & Autoencoder Q3',
        'color': '#2E86AB',
        'marker': 'o',
        'n_events': len(turnover_windows_fnguide_only)
    },
    {
        'data': normalized_turnover_autoencoder_only,
        'label': 'Autoencoder Q5 & FnGuide Q3',
        'color': '#F26419',
        'marker': 's',
        'n_events': len(turnover_windows_autoencoder_only)
    }
]

fig_graph_b, ax_graph_b = plot_comparison(
    relative_months,
    turnover_series_conditional,
    WINDOW_BEFORE=WINDOW_BEFORE,
    normalization_point=-WINDOW_BEFORE,
    title_suffix="Graph B: Conditional Events (Peer Group Separation)"
)

# Save Figure 1B
output_path_1b = Path("outputs") / "figure1b_conditional_turnover_autoencoder.png"
output_path_1b.parent.mkdir(parents=True, exist_ok=True)
fig_graph_b.savefig(output_path_1b, dpi=300, bbox_inches='tight')
print(f"[OK] Saved Figure 1B to: {output_path_1b}")

plt.show()

print("[OK] Graph B plot complete!")

# %% [markdown]
# ## 25. Statistical Comparison: Conditional vs Unconditional Events
#
# Compare Graph A (unconditional) vs Graph B (conditional) patterns:
# - Test H&P hypothesis about delayed attention to less visible peers
# - Analyze persistence differences
# - Quantify the separation effect

# %%
print_section("Statistical Comparison: Graph B vs Graph A")

print("=" * 80)
print("GRAPH A (UNCONDITIONAL) vs GRAPH B (CONDITIONAL)")
print("=" * 80)

print("\nEvent Counts:")
print(f"  Graph A - FnGuide (any Autoencoder):")
print(f"    Events: {total_events:,}, Windows: {len(turnover_windows_daily):,}")
print(f"  Graph B - FnGuide Q5 & Autoencoder Q3:")
print(f"    Events: {total_fnguide_only:,}, Windows: {len(turnover_windows_fnguide_only):,}")
print(f"    Ratio: {total_fnguide_only/total_events:.1%} of unconditional")

print(f"\n  Graph A - Autoencoder (any FnGuide):")
print(f"    Events: {total_autoencoder_events:,}, Windows: {len(turnover_windows_autoencoder):,}")
print(f"  Graph B - Autoencoder Q5 & FnGuide Q3:")
print(f"    Events: {total_autoencoder_only:,}, Windows: {len(turnover_windows_autoencoder_only):,}")
print(f"    Ratio: {total_autoencoder_only/total_autoencoder_events:.1%} of unconditional")

print("\n" + "=" * 80)
print("KEY COMPARISONS AT CRITICAL TIME POINTS")
print("=" * 80)

# Comparison table
key_points = [
    (-3, "t=-3 (norm)", -3),
    (0, "t=0 (event)", 0),
    (3, "t=+3", 3),
    (6, "t=+6", 6),
    (9, "t=+9", 9),
    (12, "t=+12", 12)
]

print("\nGraph B Conditional Events:")
print(f"{'Time Point':<12} {'FnGuide-only':<15} {'Auto-only':<15} {'Difference':>12}")
print("-" * 60)

for rel_month, label, idx_offset in key_points:
    idx = WINDOW_BEFORE + idx_offset
    fnguide_val = normalized_turnover_fnguide_only[idx]
    autoencoder_val = normalized_turnover_autoencoder_only[idx]
    diff = autoencoder_val - fnguide_val
    print(f"{label:<12} {fnguide_val:12.4f}    {autoencoder_val:12.4f}    {diff:+12.4f}")

print("\nTurnover Persistence Analysis (Graph B):")
# Calculate average turnover in post-event windows
post_event_early = slice(WINDOW_BEFORE + 1, WINDOW_BEFORE + 4)  # t+1 to t+3
post_event_mid = slice(WINDOW_BEFORE + 4, WINDOW_BEFORE + 7)    # t+4 to t+6
post_event_late = slice(WINDOW_BEFORE + 7, WINDOW_BEFORE + 13)  # t+7 to t+12

fnguide_early_cond = normalized_turnover_fnguide_only[post_event_early].mean()
fnguide_mid_cond = normalized_turnover_fnguide_only[post_event_mid].mean()
fnguide_late_cond = normalized_turnover_fnguide_only[post_event_late].mean()

autoencoder_early_cond = normalized_turnover_autoencoder_only[post_event_early].mean()
autoencoder_mid_cond = normalized_turnover_autoencoder_only[post_event_mid].mean()
autoencoder_late_cond = normalized_turnover_autoencoder_only[post_event_late].mean()

print(f"  Average turnover t+1 to t+3:")
print(f"    FnGuide-only: {fnguide_early_cond:.4f}")
print(f"    Autoencoder-only: {autoencoder_early_cond:.4f}")
print(f"    Difference: {autoencoder_early_cond - fnguide_early_cond:+.4f}")

print(f"  Average turnover t+4 to t+6:")
print(f"    FnGuide-only: {fnguide_mid_cond:.4f}")
print(f"    Autoencoder-only: {autoencoder_mid_cond:.4f}")
print(f"    Difference: {autoencoder_mid_cond - fnguide_mid_cond:+.4f}")

print(f"  Average turnover t+7 to t+12:")
print(f"    FnGuide-only: {fnguide_late_cond:.4f}")
print(f"    Autoencoder-only: {autoencoder_late_cond:.4f}")
print(f"    Difference: {autoencoder_late_cond - fnguide_late_cond:+.4f}")

print("\n" + "=" * 80)
print("  AUTOENCODER FIGURE 1B ANALYSIS COMPLETE!")
print("=" * 80)

# %%
# Print timing summary
print_total_time()
