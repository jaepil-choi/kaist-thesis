"""Diagnose dropping for Spec3 (SIC only, no TNIC)"""
import pandas as pd
import numpy as np
from pathlib import Path
from regression.utils import standardize_cross_sectional

CHECKPOINT_DIR = Path("checkpoints")

# Load data
sic_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_04_sic_peer_returns.parquet')
own_ret = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_05_own_returns.parquet')
ff_controls = pd.read_parquet(CHECKPOINT_DIR / 'checkpoint_06_ff_controls.parquet')

log_be_me = ff_controls.loc['log_be_me']
log_size = ff_controls.loc['log_size']
ret_t1 = ff_controls.loc['ret_t1']
ret_t2_t12 = ff_controls.loc['ret_t2_t12']

# Create lags
sic_t0 = sic_ret.shift(0)

# Filter to common date range (without TNIC)
all_df = {'own_ret': own_ret, 'log_be_me': log_be_me, 'log_size': log_size,
          'ret_t1': ret_t1, 'ret_t2_t12': ret_t2_t12, 'sic_t0': sic_t0}

first_dates = []
last_dates = []
for df in all_df.values():
    valid = ~df.isna().all(axis=1)
    if valid.any():
        first_dates.append(valid.idxmax())
        last_dates.append(valid[::-1].idxmax())

common_start = max(first_dates)
common_end = min(last_dates)

print(f"Spec3 (SIC only) - Common date range: {common_start} to {common_end}")
print(f"Number of dates: {len(own_ret.loc[common_start:common_end])}")

# Filter to common range
own_ret = own_ret.loc[common_start:common_end]
log_be_me = log_be_me.loc[common_start:common_end]
log_size = log_size.loc[common_start:common_end]
ret_t1 = ret_t1.loc[common_start:common_end]
ret_t2_t12 = ret_t2_t12.loc[common_start:common_end]
sic_t0 = sic_t0.loc[common_start:common_end]

# Replace Inf with NaN
log_be_me = log_be_me.replace([np.inf, -np.inf], np.nan)
log_size = log_size.replace([np.inf, -np.inf], np.nan)
ret_t1 = ret_t1.replace([np.inf, -np.inf], np.nan)
ret_t2_t12 = ret_t2_t12.replace([np.inf, -np.inf], np.nan)
sic_t0 = sic_t0.replace([np.inf, -np.inf], np.nan)

print(f"\nNaN proportions BEFORE standardization:")
print(f"  own_ret: {own_ret.isna().sum().sum() / own_ret.size * 100:.1f}%")
print(f"  log_be_me: {log_be_me.isna().sum().sum() / log_be_me.size * 100:.1f}%")
print(f"  log_size: {log_size.isna().sum().sum() / log_size.size * 100:.1f}%")
print(f"  ret_t1: {ret_t1.isna().sum().sum() / ret_t1.size * 100:.1f}%")
print(f"  ret_t2_t12: {ret_t2_t12.isna().sum().sum() / ret_t2_t12.size * 100:.1f}%")
print(f"  sic_t0: {sic_t0.isna().sum().sum() / sic_t0.size * 100:.1f}%")

# Standardize
log_be_me_std = standardize_cross_sectional(log_be_me, by_date=True)
log_size_std = standardize_cross_sectional(log_size, by_date=True)
ret_t1_std = standardize_cross_sectional(ret_t1, by_date=True)
ret_t2_t12_std = standardize_cross_sectional(ret_t2_t12, by_date=True)
sic_t0_std = standardize_cross_sectional(sic_t0, by_date=True)

print(f"\nNaN proportions AFTER standardization:")
print(f"  log_be_me_std: {log_be_me_std.isna().sum().sum() / log_be_me_std.size * 100:.1f}%")
print(f"  log_size_std: {log_size_std.isna().sum().sum() / log_size_std.size * 100:.1f}%")
print(f"  ret_t1_std: {ret_t1_std.isna().sum().sum() / ret_t1_std.size * 100:.1f}%")
print(f"  ret_t2_t12_std: {ret_t2_t12_std.isna().sum().sum() / ret_t2_t12_std.size * 100:.1f}%")
print(f"  sic_t0_std: {sic_t0_std.isna().sum().sum() / sic_t0_std.size * 100:.1f}%")

# Remove all-NaN columns (Step 2 filter)
valid_cols = own_ret.columns[~own_ret.isna().all(axis=0)]
print(f"\nStep 2 - Column filter:")
print(f"  own_ret valid columns: {len(valid_cols)} / {len(own_ret.columns)}")

for var_name, var_df in [('log_be_me', log_be_me_std), ('log_size', log_size_std),
                          ('ret_t1', ret_t1_std), ('ret_t2_t12', ret_t2_t12_std),
                          ('sic_t0', sic_t0_std)]:
    var_valid = var_df.columns[~var_df.isna().all(axis=0)]
    print(f"  {var_name} valid columns: {len(var_valid)} / {len(var_df.columns)}")
    valid_cols = valid_cols.intersection(var_valid)
    print(f"    after intersection: {len(valid_cols)}")

print(f"\nValid securities after removing all-NaN columns: {len(valid_cols)}")

# Filter to valid columns
dep = own_ret[valid_cols]
indep_dict = {
    'log_be_me': log_be_me_std[valid_cols],
    'log_size': log_size_std[valid_cols],
    'ret_t1': ret_t1_std[valid_cols],
    'ret_t2_t12': ret_t2_t12_std[valid_cols],
    'sic_t0': sic_t0_std[valid_cols]
}

print(f"\nNaN proportions after filtering to valid securities:")
for var_name, var_df in indep_dict.items():
    print(f"  {var_name}: {var_df.isna().sum().sum() / var_df.size * 100:.1f}%")

# Stack to MultiIndex (Step 3 filter)
dep_long = dep.stack()
indep_long = pd.DataFrame({k: v.stack() for k, v in indep_dict.items()})

print(f"\nStep 3 - Stack filter:")
print(f"  Total possible observations: {dep.shape[0]} dates × {dep.shape[1]} securities = {dep.shape[0] * dep.shape[1]}")
print(f"  After .stack(): {len(dep_long)} observations")
print(f"  Dropped by stack: {dep.shape[0] * dep.shape[1] - len(dep_long)} ({(dep.shape[0] * dep.shape[1] - len(dep_long))/(dep.shape[0] * dep.shape[1])*100:.1f}%)")

# Combine (Step 4 listwise deletion)
combined = pd.concat([dep_long.rename('dependent'), indep_long], axis=1)
print(f"\nStep 4 - Before listwise deletion (dropna):")
print(f"  Combined shape: {combined.shape}")

# Count NaN per column
print(f"\n  NaN counts by variable:")
for col in combined.columns:
    n_nan = combined[col].isna().sum()
    print(f"    {col}: {n_nan} / {len(combined)} = {n_nan/len(combined)*100:.1f}%")

# Check how many rows have ANY NaN
any_nan = combined.isna().any(axis=1).sum()
print(f"\n  Rows with ANY NaN: {any_nan} / {len(combined)} = {any_nan/len(combined)*100:.1f}%")

# Drop NaN
combined_clean = combined.dropna()
print(f"\nAfter dropna():")
print(f"  Remaining observations: {len(combined_clean)}")
print(f"  Dropped by listwise deletion: {len(combined) - len(combined_clean)} ({(len(combined) - len(combined_clean))/len(combined)*100:.1f}%)")

# Analyze WHICH variable is causing most drops
print(f"\n=== WHICH VARIABLE CAUSES MOST DROPS (Spec3) ===")
for col in combined.columns:
    temp = combined.dropna(subset=[col])
    dropped_by_this = len(combined) - len(temp)
    print(f"  {col}: {dropped_by_this} rows ({dropped_by_this/len(combined)*100:.1f}%)")

print(f"\n=== SUMMARY ===")
print(f"Total drop rate across all 4 steps: {(1 - len(combined_clean)/(dep.shape[0] * dep.shape[1]))*100:.1f}%")
print(f"  Step 1 (date filter): Kept {dep.shape[0]} dates")
print(f"  Step 2 (column filter): Kept {dep.shape[1]} securities")
print(f"  Step 3 (.stack()): Dropped {dep.shape[0] * dep.shape[1] - len(dep_long)} obs")
print(f"  Step 4 (listwise deletion): Dropped {len(combined) - len(combined_clean)} obs")
print(f"Final: {len(combined_clean)} observations from {dep.shape[0]} dates × {dep.shape[1]} securities")
