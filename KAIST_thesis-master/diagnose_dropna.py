"""Diagnose why so many observations are being dropped"""
import pandas as pd
import numpy as np
from pathlib import Path
from regression.utils import standardize_cross_sectional

CHECKPOINT_DIR = Path("checkpoints")

# Load data
tnic_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_03_tnic_peer_returns.parquet')
sic_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_04_sic_peer_returns.parquet')
own_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_05_own_returns.parquet')
ff_controls = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_06_ff_controls.parquet')

log_be_me = ff_controls.loc['log_be_me']
log_size = ff_controls.loc['log_size']
ret_t1 = ff_controls.loc['ret_t1']
ret_t2_t12 = ff_controls.loc['ret_t2_t12']

# Create lags
tnic_t0 = tnic_ret.shift(0)
sic_t0 = sic_ret.shift(0)

# Filter to common date range
all_df = {'own_ret': own_ret, 'log_be_me': log_be_me, 'log_size': log_size,
          'ret_t1': ret_t1, 'ret_t2_t12': ret_t2_t12, 'tnic_t0': tnic_t0, 'sic_t0': sic_t0}

first_dates = []
last_dates = []
for df in all_df.values():
    valid = ~df.isna().all(axis=1)
    if valid.any():
        first_dates.append(valid.idxmax())
        last_dates.append(valid[::-1].idxmax())

common_start = max(first_dates)
common_end = min(last_dates)

print(f"Common date range: {common_start} to {common_end}")
print(f"Number of dates: {len(own_ret.loc[common_start:common_end])}")

# Filter to common range
own_ret = own_ret.loc[common_start:common_end]
log_be_me = log_be_me.loc[common_start:common_end]
log_size = log_size.loc[common_start:common_end]
ret_t1 = ret_t1.loc[common_start:common_end]
ret_t2_t12 = ret_t2_t12.loc[common_start:common_end]
tnic_t0 = tnic_t0.loc[common_start:common_end]
sic_t0 = sic_t0.loc[common_start:common_end]

# Replace Inf with NaN
log_be_me = log_be_me.replace([np.inf, -np.inf], np.nan)
log_size = log_size.replace([np.inf, -np.inf], np.nan)
ret_t1 = ret_t1.replace([np.inf, -np.inf], np.nan)
ret_t2_t12 = ret_t2_t12.replace([np.inf, -np.inf], np.nan)
tnic_t0 = tnic_t0.replace([np.inf, -np.inf], np.nan)
sic_t0 = sic_t0.replace([np.inf, -np.inf], np.nan)

print(f"\nNaN proportions BEFORE standardization:")
print(f"  own_ret: {own_ret.isna().sum().sum() / own_ret.size * 100:.1f}%")
print(f"  log_be_me: {log_be_me.isna().sum().sum() / log_be_me.size * 100:.1f}%")
print(f"  log_size: {log_size.isna().sum().sum() / log_size.size * 100:.1f}%")
print(f"  ret_t1: {ret_t1.isna().sum().sum() / ret_t1.size * 100:.1f}%")
print(f"  ret_t2_t12: {ret_t2_t12.isna().sum().sum() / ret_t2_t12.size * 100:.1f}%")
print(f"  tnic_t0: {tnic_t0.isna().sum().sum() / tnic_t0.size * 100:.1f}%")
print(f"  sic_t0: {sic_t0.isna().sum().sum() / sic_t0.size * 100:.1f}%")

# Standardize
log_be_me_std = standardize_cross_sectional(log_be_me, by_date=True)
log_size_std = standardize_cross_sectional(log_size, by_date=True)
ret_t1_std = standardize_cross_sectional(ret_t1, by_date=True)
ret_t2_t12_std = standardize_cross_sectional(ret_t2_t12, by_date=True)
tnic_t0_std = standardize_cross_sectional(tnic_t0, by_date=True)
sic_t0_std = standardize_cross_sectional(sic_t0, by_date=True)

print(f"\nNaN proportions AFTER standardization:")
print(f"  log_be_me_std: {log_be_me_std.isna().sum().sum() / log_be_me_std.size * 100:.1f}%")
print(f"  log_size_std: {log_size_std.isna().sum().sum() / log_size_std.size * 100:.1f}%")
print(f"  ret_t1_std: {ret_t1_std.isna().sum().sum() / ret_t1_std.size * 100:.1f}%")
print(f"  ret_t2_t12_std: {ret_t2_t12_std.isna().sum().sum() / ret_t2_t12_std.size * 100:.1f}%")
print(f"  tnic_t0_std: {tnic_t0_std.isna().sum().sum() / tnic_t0_std.size * 100:.1f}%")
print(f"  sic_t0_std: {sic_t0_std.isna().sum().sum() / sic_t0_std.size * 100:.1f}%")

# Remove all-NaN columns
valid_cols = own_ret.columns[~own_ret.isna().all(axis=0)]
for var_df in [log_be_me_std, log_size_std, ret_t1_std, ret_t2_t12_std, tnic_t0_std, sic_t0_std]:
    var_valid = var_df.columns[~var_df.isna().all(axis=0)]
    valid_cols = valid_cols.intersection(var_valid)

print(f"\nValid securities after removing all-NaN columns: {len(valid_cols)}")

# Filter to valid columns (THIS IS WHAT THE SCRIPT DOES)
dep = own_ret[valid_cols]
indep_dict = {
    'log_be_me': log_be_me_std[valid_cols],
    'log_size': log_size_std[valid_cols],
    'ret_t1': ret_t1_std[valid_cols],
    'ret_t2_t12': ret_t2_t12_std[valid_cols],
    'tnic_t0': tnic_t0_std[valid_cols],
    'sic_t0': sic_t0_std[valid_cols]
}

print(f"\nNaN proportions after filtering to valid securities:")
for var_name, var_df in indep_dict.items():
    print(f"  {var_name}: {var_df.isna().sum().sum() / var_df.size * 100:.1f}%")

# Stack to MultiIndex (THIS IS WHAT CONVERT_TO_MULTIINDEX DOES)
dep_long = dep.stack()
indep_long = pd.DataFrame({k: v.stack() for k, v in indep_dict.items()})

print(f"\nAfter stacking to MultiIndex:")
print(f"  Total possible observations: {dep.shape[0]} dates × {dep.shape[1]} securities = {dep.shape[0] * dep.shape[1]}")
print(f"  Actually stacked observations: {len(dep_long)}")
print(f"  Dropped by stack (all-NaN rows): {dep.shape[0] * dep.shape[1] - len(dep_long)}")

# Combine and count NaN (THIS IS WHAT RUN_FAMA_MACBETH DOES)
combined = pd.concat([dep_long.rename('dependent'), indep_long], axis=1)
print(f"\nCombined DataFrame:")
print(f"  Shape: {combined.shape}")
print(f"  Total cells: {combined.size}")

# Count NaN per column
print(f"\nNaN counts by variable:")
for col in combined.columns:
    n_nan = combined[col].isna().sum()
    print(f"  {col}: {n_nan} / {len(combined)} = {n_nan/len(combined)*100:.1f}%")

# Check how many rows have ANY NaN
any_nan = combined.isna().any(axis=1).sum()
print(f"\nRows with ANY NaN: {any_nan} / {len(combined)} = {any_nan/len(combined)*100:.1f}%")

# Drop NaN
combined_clean = combined.dropna()
print(f"\nAfter dropna():")
print(f"  Remaining observations: {len(combined_clean)}")
print(f"  Dropped: {len(combined) - len(combined_clean)} ({(len(combined) - len(combined_clean))/len(combined)*100:.1f}%)")

# Analyze WHICH variable is causing most drops
print(f"\n=== DIAGNOSING WHICH VARIABLE CAUSES MOST DROPS ===")
for col in combined.columns:
    # Drop rows where THIS column is NaN
    temp = combined.dropna(subset=[col])
    dropped_by_this = len(combined) - len(temp)
    print(f"{col}: Would drop {dropped_by_this} rows ({dropped_by_this/len(combined)*100:.1f}%) if only checking this variable")
