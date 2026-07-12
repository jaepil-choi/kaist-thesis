"""
Table 2: Return Comovement Fama-MacBeth Regression (Autoencoder Version)
Adaptation of Hoberg et al. (2018) Table 2 using autoencoder cluster-based peers

This script implements the return comovement analysis examining whether
focal firm returns are predicted by lagged returns of Autoencoder and SIC industry peers.

Methodology:
- Autoencoder peers: Cluster-based grouping from Kim et al. (2020) deep autoencoder
- SIC peers: Traditional FnGuide industry classification

Reference:
- Hoberg, G., & Phillips, G. (2018). Text-based industry momentum. JFQA, 53(6), 2355-2388.
- Kim et al. (2020). Deep learning for text-based industry classification
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

# Add regression module to path
sys.path.insert(0, str(Path(__file__).parent))

from regression import FamaMacBethRegression
from regression.utils import standardize_cross_sectional

# ============================================================================
# Configuration
# ============================================================================

CHECKPOINT_DIR = Path("checkpoints_autoencoder")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("TABLE 2: RETURN COMOVEMENT FAMA-MACBETH REGRESSION (AUTOENCODER)")
print("Hoberg et al. (2018) Methodology with Autoencoder Clusters")
print("=" * 80)
print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# Step 1: Load Checkpoint Data
# ============================================================================

print("Step 1: Loading checkpoint data...")

# Load core data
# Following Hoberg & Phillips (2018) methodology:
# - Autoencoder peers: Equal-weighted (cluster-based peers from deep autoencoder)
# - SIC peers: Value-weighted (more visible peers, following Moskowitz & Grinblatt 1999)
autoencoder_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_03_autoencoder_peer_returns.parquet')  # Equal-weighted
sic_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_04_sic_peer_returns_vw.parquet')  # Value-weighted
own_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_05_own_returns.parquet')

# FF controls are methodology-independent, so load from original checkpoints
ff_controls = pd.read_parquet(Path("checkpoints") / 'checkpoint_06_ff_controls.parquet')

print(f"  Autoencoder peer returns (EW): {autoencoder_ret.shape} (dates x securities)")
print(f"  SIC peer returns (VW):         {sic_ret.shape}")
print(f"  Own returns:                   {own_ret.shape}")
print(f"  FF controls:                   {ff_controls.shape}")

# Extract control variables from MultiIndex
log_be_me = ff_controls.loc['log_be_me']
log_size = ff_controls.loc['log_size']
ret_t1 = ff_controls.loc['ret_t1']
ret_t2_t12 = ff_controls.loc['ret_t2_t12']

print(f"\nControl variables extracted:")
print(f"  log(BE/ME):       {log_be_me.shape}")
print(f"  log(Size):        {log_size.shape}")
print(f"  Return t-1:       {ret_t1.shape}")
print(f"  Return t-2:t-12:  {ret_t2_t12.shape}")

# ============================================================================
# Step 2: Create Individual Monthly Lags
# ============================================================================

print("\nStep 2: Creating individual monthly lags for peer returns...")

# Autoencoder peer returns at different lags (t, t-1, t-2, ..., t-6)
autoencoder_lags = {}
for lag in range(7):
    var_name = f'autoencoder_t{lag}' if lag == 0 else f'autoencoder_t_{lag}'
    autoencoder_lags[var_name] = autoencoder_ret.shift(lag)
    print(f"  {var_name}: shift({lag})")

# SIC peer returns at different lags (t, t-1, t-2, ..., t-6)
sic_lags = {}
for lag in range(7):
    var_name = f'sic_t{lag}' if lag == 0 else f'sic_t_{lag}'
    sic_lags[var_name] = sic_ret.shift(lag)
    print(f"  {var_name}: shift({lag})")

# ============================================================================
# Step 3: Filter to Common Valid Date Range
# ============================================================================

print("\nStep 3: Filtering to common valid date range...")

# Determine common valid date range
# Find latest first valid date across all variables
all_dataframes = {
    'own_ret': own_ret,
    'log_be_me': log_be_me,
    'log_size': log_size,
    'ret_t1': ret_t1,
    'ret_t2_t12': ret_t2_t12,
}
all_dataframes.update(autoencoder_lags)
all_dataframes.update(sic_lags)

first_valid_dates = []
last_valid_dates = []

for name, df in all_dataframes.items():
    all_nan_rows = df.isna().all(axis=1)
    valid_rows = ~all_nan_rows
    if valid_rows.any():
        first_valid_dates.append(valid_rows.idxmax())
        last_valid_dates.append(valid_rows[::-1].idxmax())

# Common date range: latest first, earliest last
common_start = max(first_valid_dates)
common_end = min(last_valid_dates)

print(f"  Common valid date range: {common_start} to {common_end}")
print(f"  Number of dates: {len(own_ret.loc[common_start:common_end])}")

# Filter all variables to common date range
own_ret = own_ret.loc[common_start:common_end]
log_be_me = log_be_me.loc[common_start:common_end]
log_size = log_size.loc[common_start:common_end]
ret_t1 = ret_t1.loc[common_start:common_end]
ret_t2_t12 = ret_t2_t12.loc[common_start:common_end]

for var_name in autoencoder_lags.keys():
    autoencoder_lags[var_name] = autoencoder_lags[var_name].loc[common_start:common_end]

for var_name in sic_lags.keys():
    sic_lags[var_name] = sic_lags[var_name].loc[common_start:common_end]

print(f"  All variables filtered to {len(own_ret)} dates")

# Replace Inf values with NaN in raw data (BEFORE standardization)
print(f"\n  Replacing Inf values with NaN...")
log_be_me = log_be_me.replace([np.inf, -np.inf], np.nan)
log_size = log_size.replace([np.inf, -np.inf], np.nan)
ret_t1 = ret_t1.replace([np.inf, -np.inf], np.nan)
ret_t2_t12 = ret_t2_t12.replace([np.inf, -np.inf], np.nan)
for var_name in autoencoder_lags.keys():
    autoencoder_lags[var_name] = autoencoder_lags[var_name].replace([np.inf, -np.inf], np.nan)
for var_name in sic_lags.keys():
    sic_lags[var_name] = sic_lags[var_name].replace([np.inf, -np.inf], np.nan)
print(f"  Inf values replaced")

# ============================================================================
# Step 3.5: Basic Preprocessing - Drop All-NaN Columns
# ============================================================================

print("\nStep 3.5: Basic preprocessing - dropping all-NaN columns (securities with no data)...")

def drop_all_nan_columns(df, name):
    """Drop columns that are all NaN and return drop statistics."""
    n_cols_before = len(df.columns)
    df_clean = df.dropna(axis=1, how='all')
    n_cols_after = len(df_clean.columns)
    n_dropped = n_cols_before - n_cols_after
    return df_clean, n_cols_before, n_cols_after, n_dropped

# Drop all-NaN columns from each variable
own_ret, own_ret_before, own_ret_after, own_ret_dropped = drop_all_nan_columns(own_ret, 'own_ret')
log_be_me, log_be_me_before, log_be_me_after, log_be_me_dropped = drop_all_nan_columns(log_be_me, 'log_be_me')
log_size, log_size_before, log_size_after, log_size_dropped = drop_all_nan_columns(log_size, 'log_size')
ret_t1, ret_t1_before, ret_t1_after, ret_t1_dropped = drop_all_nan_columns(ret_t1, 'ret_t1')
ret_t2_t12, ret_t2_t12_before, ret_t2_t12_after, ret_t2_t12_dropped = drop_all_nan_columns(ret_t2_t12, 'ret_t2_t12')

# Drop all-NaN columns from lagged variables
autoencoder_lags_clean = {}
autoencoder_drops = {}
for var_name, var_df in autoencoder_lags.items():
    clean_df, before, after, dropped = drop_all_nan_columns(var_df, var_name)
    autoencoder_lags_clean[var_name] = clean_df
    autoencoder_drops[var_name] = dropped

sic_lags_clean = {}
sic_drops = {}
for var_name, var_df in sic_lags.items():
    clean_df, before, after, dropped = drop_all_nan_columns(var_df, var_name)
    sic_lags_clean[var_name] = clean_df
    sic_drops[var_name] = dropped

# Replace original variables with cleaned versions
autoencoder_lags = autoencoder_lags_clean
sic_lags = sic_lags_clean

print(f"\n  All-NaN columns dropped (basic preprocessing):")
print(f"    own_ret:          {own_ret_dropped:4d} columns dropped ({own_ret_before:,} → {own_ret_after:,})")
print(f"    log_be_me:        {log_be_me_dropped:4d} columns dropped ({log_be_me_before:,} → {log_be_me_after:,})")
print(f"    log_size:         {log_size_dropped:4d} columns dropped ({log_size_before:,} → {log_size_after:,})")
print(f"    ret_t1:           {ret_t1_dropped:4d} columns dropped ({ret_t1_before:,} → {ret_t1_after:,})")
print(f"    ret_t2_t12:       {ret_t2_t12_dropped:4d} columns dropped ({ret_t2_t12_before:,} → {ret_t2_t12_after:,})")
print(f"    Autoencoder lags: {sum(autoencoder_drops.values()):4d} total columns dropped across all lags")
print(f"    SIC lags:         {sum(sic_drops.values()):4d} total columns dropped across all lags")

print("\n[OK] Basic preprocessing complete!")

# ============================================================================
# Step 4: Cross-Sectional Standardization
# ============================================================================

print("\nStep 4: Cross-sectional standardization (mean=0, std=1 within each date)...")

# Standardize control variables
standardized_vars = {
    'log_be_me': standardize_cross_sectional(log_be_me, by_date=True),
    'log_size': standardize_cross_sectional(log_size, by_date=True),
    'ret_t1': standardize_cross_sectional(ret_t1, by_date=True),
    'ret_t2_t12': standardize_cross_sectional(ret_t2_t12, by_date=True),
}

print("  Control variables standardized: log_be_me, log_size, ret_t1, ret_t2_t12")

# Standardize Autoencoder peer returns
for var_name, var_df in autoencoder_lags.items():
    standardized_vars[var_name] = standardize_cross_sectional(var_df, by_date=True)

print(f"  Autoencoder variables standardized: {list(autoencoder_lags.keys())}")

# Standardize SIC peer returns
for var_name, var_df in sic_lags.items():
    standardized_vars[var_name] = standardize_cross_sectional(var_df, by_date=True)

print(f"  SIC variables standardized: {list(sic_lags.keys())}")

# ============================================================================
# Step 5: Define Regression Specifications
# ============================================================================

print("\nStep 5: Defining 7 regression specifications...")

# Control variables (used in all specifications)
controls = ['log_be_me', 'log_size', 'ret_t1', 'ret_t2_t12']

# Define specifications following Hoberg Table 2
specifications = {
    'Spec1': {
        'desc': 'Controls + Autoencoder_t + SIC_t',
        'vars': controls + ['autoencoder_t0', 'sic_t0']
    },
    'Spec2': {
        'desc': 'Controls + Autoencoder_t',
        'vars': controls + ['autoencoder_t0']
    },
    'Spec3': {
        'desc': 'Controls + SIC_t',
        'vars': controls + ['sic_t0']
    },
    'Spec4': {
        'desc': 'Controls + Autoencoder_(t to t-3) + SIC_(t to t-3)',
        'vars': controls + ['autoencoder_t0', 'autoencoder_t_1', 'autoencoder_t_2', 'autoencoder_t_3',
                           'sic_t0', 'sic_t_1', 'sic_t_2', 'sic_t_3']
    },
    'Spec5': {
        'desc': 'Controls + Autoencoder_(t to t-6) + SIC_(t to t-6)',
        'vars': controls + ['autoencoder_t0', 'autoencoder_t_1', 'autoencoder_t_2', 'autoencoder_t_3', 'autoencoder_t_4', 'autoencoder_t_5', 'autoencoder_t_6',
                           'sic_t0', 'sic_t_1', 'sic_t_2', 'sic_t_3', 'sic_t_4', 'sic_t_5', 'sic_t_6']
    },
    'Spec6': {
        'desc': 'Controls + Autoencoder_(t-1 to t-3) + SIC_(t-1 to t-3)',
        'vars': controls + ['autoencoder_t_1', 'autoencoder_t_2', 'autoencoder_t_3',
                           'sic_t_1', 'sic_t_2', 'sic_t_3']
    },
    'Spec7': {
        'desc': 'Controls + Autoencoder_(t-1 to t-6) + SIC_(t-1 to t-6)',
        'vars': controls + ['autoencoder_t_1', 'autoencoder_t_2', 'autoencoder_t_3', 'autoencoder_t_4', 'autoencoder_t_5', 'autoencoder_t_6',
                           'sic_t_1', 'sic_t_2', 'sic_t_3', 'sic_t_4', 'sic_t_5', 'sic_t_6']
    },
}

for spec_name, spec_info in specifications.items():
    print(f"  {spec_name}: {spec_info['desc']}")
    print(f"    Variables ({len(spec_info['vars'])}): {', '.join(spec_info['vars'][:5])}{'...' if len(spec_info['vars']) > 5 else ''}")

# ============================================================================
# Step 5.5: Data Coverage Report
# ============================================================================

print("\n" + "=" * 80)
print("DATA COVERAGE REPORT (AFTER BASIC PREPROCESSING)")
print("=" * 80)
print("Note: All-NaN columns already removed in Step 3.5")

def calculate_coverage_by_date(rhs_vars_dict, own_ret):
    """
    Calculate date-by-date coverage for RHS variables relative to own_ret universe.

    Parameters:
    -----------
    rhs_vars_dict : dict
        {variable_name: DataFrame (dates x securities)}
    own_ret : DataFrame
        Dependent variable defining the universe (dates x securities)

    Returns:
    --------
    coverage_stats : dict
        {variable_name: {'mean': X, 'min': Y, 'max': Z, 'universe_mean': N}}
    """
    # Create 2D mask from own_ret
    mask_2d = own_ret.notna()

    # Count universe size per date
    universe_per_date = mask_2d.sum(axis=1)  # Series: dates -> count of securities

    coverage_stats = {}

    for var_name, var_df in rhs_vars_dict.items():
        # Apply mask and count available data per date
        masked_var = var_df.where(mask_2d)  # Set to NaN where mask is False
        rhs_available = masked_var.notna().sum(axis=1)  # Count per date

        # Calculate coverage percentage per date
        coverage_per_date = (rhs_available / universe_per_date) * 100

        # Summary statistics
        coverage_stats[var_name] = {
            'mean': coverage_per_date.mean(),
            'min': coverage_per_date.min(),
            'max': coverage_per_date.max(),
            'universe_mean': universe_per_date.mean()
        }

    return coverage_stats

# Prepare RHS variables (exclude own_ret - it's the reference)
rhs_vars = {
    'log_be_me': log_be_me,
    'log_size': log_size,
    'ret_t1': ret_t1,
    'ret_t2_t12': ret_t2_t12,
}
rhs_vars.update(autoencoder_lags)
rhs_vars.update(sic_lags)

# Calculate coverage relative to own_ret universe
coverage_stats = calculate_coverage_by_date(rhs_vars, own_ret)

# Also calculate own_ret universe statistics
universe_per_date = own_ret.notna().sum(axis=1)
own_ret_stats = {
    'mean_securities': universe_per_date.mean(),
    'min_securities': universe_per_date.min(),
    'max_securities': universe_per_date.max(),
    'total_dates': len(universe_per_date)
}

print(f"\nReference Universe: own_ret (Dependent Variable)")
print(f"  Mean securities per date: {own_ret_stats['mean_securities']:.1f}")
print(f"  Min securities per date:  {own_ret_stats['min_securities']:.0f}")
print(f"  Max securities per date:  {own_ret_stats['max_securities']:.0f}")
print(f"  Total dates: {own_ret_stats['total_dates']}")

print(f"\n{'Variable':<20} {'Mean Cov':>12} {'Min Cov':>10} {'Max Cov':>10}")
print("-" * 55)

# Control Variables
print("\nControl Variables:")
for var in ['log_be_me', 'log_size', 'ret_t1', 'ret_t2_t12']:
    stats = coverage_stats[var]
    print(f"  {var:<18} {stats['mean']:>11.1f}% {stats['min']:>9.1f}% {stats['max']:>9.1f}%")

# Autoencoder Peer Returns
print("\nAutoencoder Peer Returns:")
for var in sorted([k for k in coverage_stats.keys() if k.startswith('autoencoder_')]):
    stats = coverage_stats[var]
    print(f"  {var:<18} {stats['mean']:>11.1f}% {stats['min']:>9.1f}% {stats['max']:>9.1f}%")

# SIC Peer Returns
print("\nSIC Peer Returns:")
for var in sorted([k for k in coverage_stats.keys() if k.startswith('sic_')]):
    stats = coverage_stats[var]
    print(f"  {var:<18} {stats['mean']:>11.1f}% {stats['min']:>9.1f}% {stats['max']:>9.1f}%")

print("\n" + "=" * 80)

# ============================================================================
# Step 6: Run Fama-MacBeth Regressions
# ============================================================================

print("\nStep 6: Running Fama-MacBeth regressions with Newey-West SE (2 lags)...")

# Initialize regression object
# Note: check_rank=False allows regression despite multicollinearity
# This is necessary due to data limitations
fm = FamaMacBethRegression(method='direct', newey_west_lags=2, check_rank=False, verbose=False)

# Store results and tracking info
results = {}
regression_drops = {}

for spec_name, spec_info in specifications.items():
    print(f"\n  Running {spec_name}: {spec_info['desc']}...")

    # Select independent variables for this specification
    independent_vars = {
        var_name: standardized_vars[var_name]
        for var_name in spec_info['vars']
        if var_name in standardized_vars
    }

    # Track observation counts through filtering stages
    tracking = {}

    # Stage 1: Count initial potential observations (all non-NaN cells in dependent variable)
    initial_obs = own_ret.notna().sum().sum()
    tracking['initial_potential'] = initial_obs

    # Stage 2: Identify all-NaN columns for each variable
    dep_all_nan_cols = own_ret.isna().all(axis=0).sum()
    indep_all_nan_cols = {}
    for var_name, var_df in independent_vars.items():
        indep_all_nan_cols[var_name] = var_df.isna().all(axis=0).sum()

    # Stage 3: Filter out all-NaN columns (securities with no data)
    valid_securities = own_ret.columns[~own_ret.isna().all(axis=0)]
    for var_name, var_df in independent_vars.items():
        var_valid = var_df.columns[~var_df.isna().all(axis=0)]
        valid_securities = valid_securities.intersection(var_valid)

    n_securities_before = len(own_ret.columns)
    n_securities_after = len(valid_securities)
    n_securities_dropped = n_securities_before - n_securities_after

    dependent_clean = own_ret[valid_securities]
    independent_clean = {k: v[valid_securities] for k, v in independent_vars.items()}

    # Count observations after column filtering
    obs_after_col_filter = dependent_clean.notna().sum().sum()
    obs_dropped_col_filter = initial_obs - obs_after_col_filter
    tracking['after_col_filter'] = obs_after_col_filter
    tracking['dropped_col_filter'] = obs_dropped_col_filter
    tracking['n_securities_dropped'] = n_securities_dropped

    try:
        # Run regression
        result = fm.fit(
            dependent=dependent_clean,
            independent=independent_clean
        )

        results[spec_name] = result

        # Track final observations used in regression
        tracking['final_obs'] = result.n_obs
        tracking['dropped_in_regression'] = obs_after_col_filter - result.n_obs
        tracking['total_dropped'] = initial_obs - result.n_obs
        tracking['retention_rate'] = (result.n_obs / initial_obs * 100) if initial_obs > 0 else 0

        regression_drops[spec_name] = tracking

        print(f"    ✓ Success: {result.n_obs:,} observations, {result.n_variables} variables")
        print(f"      Sample: {result.n_periods} periods, {result.n_securities} securities")
        print(f"      Dropped {n_securities_dropped} all-NaN securities ({obs_dropped_col_filter:,} obs, {obs_dropped_col_filter/initial_obs*100:.1f}%)")
        print(f"      Dropped in regression: {tracking['dropped_in_regression']:,} obs ({tracking['dropped_in_regression']/initial_obs*100:.1f}%)")
        print(f"      Total retention: {result.n_obs:,} / {initial_obs:,} ({tracking['retention_rate']:.1f}%)")

    except Exception as e:
        print(f"    ✗ Failed: {str(e)}")
        results[spec_name] = None
        regression_drops[spec_name] = tracking

# Print observation drop summary table
print("\n" + "=" * 80)
print("OBSERVATION DROP SUMMARY")
print("=" * 80)
print(f"\n{'Specification':<10} {'Initial':>12} {'After ColFilt':>15} {'Final Used':>12} {'Retention':>12}")
print("-" * 80)

for spec_name in specifications.keys():
    if spec_name in regression_drops and 'final_obs' in regression_drops[spec_name]:
        track = regression_drops[spec_name]
        print(f"{spec_name:<10} {track['initial_potential']:>12,} {track['after_col_filter']:>15,} "
              f"{track['final_obs']:>12,} {track['retention_rate']:>11.1f}%")

print("\n" + "=" * 80)
print("Drop Breakdown (for Spec1 as example):")
if 'Spec1' in regression_drops and 'final_obs' in regression_drops['Spec1']:
    track = regression_drops['Spec1']
    initial = track['initial_potential']
    print(f"  1. Initial potential observations:     {initial:>12,}  (100.0%)")
    print(f"  2. Dropped by all-NaN column filter:   {track['dropped_col_filter']:>12,}  ({track['dropped_col_filter']/initial*100:>5.1f}%)")
    print(f"  3. Remaining after column filter:      {track['after_col_filter']:>12,}  ({track['after_col_filter']/initial*100:>5.1f}%)")
    print(f"  4. Dropped in regression (missing):    {track['dropped_in_regression']:>12,}  ({track['dropped_in_regression']/initial*100:>5.1f}%)")
    print(f"  5. Final observations used:            {track['final_obs']:>12,}  ({track['retention_rate']:>5.1f}%)")
    print(f"\n  Securities: {len(own_ret.columns):,} total → {len(own_ret.columns) - track['n_securities_dropped']:,} used ({track['n_securities_dropped']:,} dropped)")
print("=" * 80 + "\n")

# ============================================================================
# Step 7: Format Results Table
# ============================================================================

print("\nStep 7: Formatting results table...")

def format_coef_tstat(result, var_name):
    """Format coefficient and t-statistic as 'coef (t-stat)'"""
    if result is None:
        return ""

    try:
        coef = result.params[var_name]
        tstat = result.tstats[var_name]

        # Format with significance stars
        pval = result.pvalues[var_name]
        stars = ""
        if pval < 0.001:
            stars = "***"
        elif pval < 0.01:
            stars = "**"
        elif pval < 0.05:
            stars = "*"

        return f"{coef:.4f}{stars}\n({tstat:.2f})"
    except KeyError:
        return ""


def create_regression_table(results_dict, specifications_dict, all_variables):
    """
    Create a formatted regression results table.

    Parameters:
    -----------
    results_dict : dict
        Dictionary mapping specification names to FamaMacBethResults objects
    specifications_dict : dict
        Dictionary mapping specification names to spec info (with 'desc' and 'vars')
    all_variables : list
        List of all possible variable names to include in the table

    Returns:
    --------
    pd.DataFrame
        Formatted results table with variables as rows and specifications as columns
    """
    table_data = []
    for var in all_variables:
        row = {'Variable': var}
        for spec_name in specifications_dict.keys():
            row[spec_name] = format_coef_tstat(results_dict[spec_name], var)
        table_data.append(row)

    results_df = pd.DataFrame(table_data)

    # Add sample statistics row
    sample_stats = {'Variable': 'N observations'}
    for spec_name, result in results_dict.items():
        if result is not None:
            sample_stats[spec_name] = str(result.n_obs)
        else:
            sample_stats[spec_name] = ""

    results_df = pd.concat([results_df, pd.DataFrame([sample_stats])], ignore_index=True)

    return results_df


# Create results DataFrame
all_vars = ['log_be_me', 'log_size', 'ret_t1', 'ret_t2_t12'] + \
           [f'autoencoder_t{i}' if i == 0 else f'autoencoder_t_{i}' for i in range(7)] + \
           [f'sic_t{i}' if i == 0 else f'sic_t_{i}' for i in range(7)]

results_df = create_regression_table(results, specifications, all_vars)


def save_regression_results(results_df, results_dict, specifications_dict,
                            output_prefix, table_title,
                            dependent_var="Month t Own Return",
                            se_method="Newey-West (2 lags)"):
    """
    Save regression results in multiple formats (CSV, Markdown, detailed text).

    Parameters:
    -----------
    results_df : pd.DataFrame
        Formatted results table
    results_dict : dict
        Dictionary of FamaMacBethResults objects
    specifications_dict : dict
        Dictionary of specification info
    output_prefix : str
        Prefix for output filenames (e.g., 'table2_return_comovement_autoencoder')
    table_title : str
        Title for the table (e.g., 'TABLE 2: RETURN COMOVEMENT (Autoencoder)')
    dependent_var : str, optional
        Description of dependent variable
    se_method : str, optional
        Description of standard error method

    Returns:
    --------
    dict
        Dictionary with paths to saved files
    """
    output_files = {}

    # Save to CSV
    csv_file = OUTPUT_DIR / f"{output_prefix}.csv"
    results_df.to_csv(csv_file, index=False)
    output_files['csv'] = csv_file
    print(f"✓ CSV saved to: {csv_file}")

    # Save to Markdown
    md_file = OUTPUT_DIR / f"{output_prefix}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# {table_title}\n\n")
        f.write(f"**Dependent Variable:** {dependent_var}  \n")
        f.write(f"**Standard Errors:** {se_method}  \n")
        f.write("**Significance:** *** p<0.001, ** p<0.01, * p<0.05\n\n")
        f.write(results_df.to_markdown(index=False))
        f.write("\n")
    output_files['markdown'] = md_file
    print(f"✓ Markdown saved to: {md_file}")

    # Save detailed summary
    detail_file = OUTPUT_DIR / f"{output_prefix}_detailed.txt"
    with open(detail_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write(f"{table_title} - DETAILED SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        for spec_name, result in results_dict.items():
            if result is not None:
                f.write(f"\n{spec_name}: {specifications_dict[spec_name]['desc']}\n")
                f.write("-" * 80 + "\n")
                f.write(result.summary().to_string())
                f.write("\n\n")
    output_files['detailed'] = detail_file
    print(f"✓ Detailed summary saved to: {detail_file}")

    return output_files


# ============================================================================
# Step 8: Display and Save Results
# ============================================================================

print("\n" + "=" * 80)
print("TABLE 2 RESULTS: RETURN COMOVEMENT (AUTOENCODER)")
print("=" * 80)
print("\nDependent Variable: Month t Own Return")
print("Standard Errors: Newey-West (2 lags)")
print("Significance: *** p<0.001, ** p<0.01, * p<0.05")
print("\n")

# Display results
print(results_df.to_string(index=False))

# Save results in all formats
print("\n")
saved_files = save_regression_results(
    results_df=results_df,
    results_dict=results,
    specifications_dict=specifications,
    output_prefix="table2_return_comovement_autoencoder",
    table_title="TABLE 2: RETURN COMOVEMENT (Autoencoder)",
    dependent_var="Month t Own Return",
    se_method="Newey-West (2 lags)"
)

# ============================================================================
# Step 9: Run Fama-MacBeth Regressions with t+1 Dependent Variable
# ============================================================================

print("\n" + "=" * 80)
print("STEP 9: FAMA-MACBETH REGRESSIONS WITH t+1 DEPENDENT VARIABLE")
print("=" * 80)
print("\nPredicting next month's return (t+1) using current month (t) information")

# Shift dependent variable forward by 1 month (t+1)
own_ret_t1 = own_ret.shift(-1)

print(f"\nDependent variable: own_ret shifted forward by 1 month")
print(f"  Original range: {own_ret.index[0]} to {own_ret.index[-1]}")
print(f"  t+1 range:      {own_ret_t1.index[0]} to {own_ret_t1.index[-1]}")

# Store results for t+1 regressions
results_t1 = {}

for spec_name, spec_info in specifications.items():
    print(f"\n  Running {spec_name} (t+1): {spec_info['desc']}...")

    # Select independent variables for this specification
    independent_vars = {
        var_name: standardized_vars[var_name]
        for var_name in spec_info['vars']
        if var_name in standardized_vars
    }

    # Remove columns with all-NaN from ANY variable (dependent or independent)
    # Start with dependent variable's valid columns
    valid_securities = own_ret_t1.columns[~own_ret_t1.isna().all(axis=0)]

    # Intersect with valid columns from each independent variable
    for var_name, var_df in independent_vars.items():
        var_valid = var_df.columns[~var_df.isna().all(axis=0)]
        valid_securities = valid_securities.intersection(var_valid)

    # Filter all variables to valid securities only
    dependent_clean = own_ret_t1[valid_securities]
    independent_clean = {k: v[valid_securities] for k, v in independent_vars.items()}

    try:
        # Run regression
        result = fm.fit(
            dependent=dependent_clean,
            independent=independent_clean
        )

        results_t1[spec_name] = result

        print(f"    ✓ Success: {result.n_obs} observations, {result.n_variables} variables")
        print(f"      Sample: {result.n_periods} periods, {result.n_securities} securities")

    except Exception as e:
        print(f"    ✗ Failed: {str(e)}")
        results_t1[spec_name] = None

# ============================================================================
# Step 10: Format Results Table for t+1 Regressions
# ============================================================================

print("\n" + "=" * 80)
print("STEP 10: FORMATTING t+1 REGRESSION RESULTS")
print("=" * 80)

# Create results DataFrame for t+1
results_t1_df = create_regression_table(results_t1, specifications, all_vars)

# Display results
print("\n" + "=" * 80)
print("TABLE 2 RESULTS: RETURN COMOVEMENT (t+1 DEPENDENT VARIABLE, AUTOENCODER)")
print("=" * 80)
print("\nDependent Variable: Month t+1 Own Return")
print("Standard Errors: Newey-West (2 lags)")
print("Significance: *** p<0.001, ** p<0.01, * p<0.05")
print("\n")

print(results_t1_df.to_string(index=False))

# Save results in all formats
print("\n")
saved_files_t1 = save_regression_results(
    results_df=results_t1_df,
    results_dict=results_t1,
    specifications_dict=specifications,
    output_prefix="table2_return_comovement_autoencoder_t1",
    table_title="TABLE 2: RETURN COMOVEMENT (t+1 Prediction, Autoencoder)",
    dependent_var="Month t+1 Own Return (predicted using t information)",
    se_method="Newey-West (2 lags)"
)

# ============================================================================
# Step 11: Sample Statistics
# ============================================================================

print("\n" + "=" * 80)
print("SAMPLE STATISTICS")
print("=" * 80)

print("\n--- Original (t) Regressions ---")
for spec_name, result in results.items():
    if result is not None:
        print(f"\n{spec_name}: {specifications[spec_name]['desc']}")
        print(f"  Observations:  {result.n_obs:,}")
        print(f"  Time periods:  {result.n_periods}")
        print(f"  Securities:    {result.n_securities}")
        print(f"  Variables:     {result.n_variables}")

print("\n--- t+1 Prediction Regressions ---")
for spec_name, result in results_t1.items():
    if result is not None:
        print(f"\n{spec_name}: {specifications[spec_name]['desc']}")
        print(f"  Observations:  {result.n_obs:,}")
        print(f"  Time periods:  {result.n_periods}")
        print(f"  Securities:    {result.n_securities}")
        print(f"  Variables:     {result.n_variables}")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print("\nKey Findings:")
print("1. Check Autoencoder peer return coefficients (should be positive and significant)")
print("2. Check SIC peer return coefficients (should weaken after controlling for Autoencoder)")
print("3. Compare contemporaneous (t) vs lagged (t-1 to t-6) coefficients")
print("4. Examine whether Autoencoder effects persist longer than SIC effects")

print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
