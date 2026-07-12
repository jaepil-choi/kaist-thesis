"""
Replication of Hoberg et al. (2018) Figure 1, Graph A
"Unconditional Turnover around High-Quintile Peer Shock"
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

print("="*80)
print("FIGURE 1, GRAPH A: TURNOVER AROUND HIGH-QUINTILE PEER SHOCK")
print("="*80)

# ============================================================================
# 1. LOAD DATA
# ============================================================================
print("\n1. Loading data...")

price_wide = pd.read_parquet("data/fnguide/processed/price_wide.parquet")
turnover_wide = pd.read_parquet("data/fnguide/processed/turnover_listed_wide.parquet")
universe_mask = pd.read_parquet("data/fnguide/processed/universe_mask_wide.parquet")

# Load industry classifications (long format)
df_filtered = pd.read_parquet("data/fnguide/processed/dataguide_filtered.parquet")
df_valid = df_filtered[df_filtered['valid_universe']].copy()

print(f"  Price shape: {price_wide.shape}")
print(f"  Turnover shape: {turnover_wide.shape}")
print(f"  Universe mask shape: {universe_mask.shape}")
print(f"  Date range: {price_wide.index.min()} to {price_wide.index.max()}")

print("\n  Price data (first 5 rows, first 5 columns):")
print(price_wide.iloc[:5, :5])

print("\n  Turnover data (first 5 rows, first 5 columns):")
print(turnover_wide.iloc[:5, :5])

print("\n  Valid universe data (first 5 rows):")
print(df_valid[['date', 'symbol', 'symbol_name', 'FnGuide Industry', '수정주가(원)', 'turnover_listed']].head())

# ============================================================================
# 2. CALCULATE MONTHLY RETURNS
# ============================================================================
print("\n2. Calculating monthly returns...")

# Monthly returns (already monthly data at end-of-month)
returns_wide = price_wide.pct_change()

print(f"  Returns shape: {returns_wide.shape}")
print(f"  Non-null returns: {returns_wide.notna().sum().sum():,}")
print(f"  Mean return: {returns_wide.mean().mean():.4f}")
print(f"  Std return: {returns_wide.std().mean():.4f}")

# ============================================================================
# 3. CREATE INDUSTRY MAPPING (DATE-SPECIFIC / CROSS-SECTIONAL)
# ============================================================================
print("\n3. Creating time-varying industry mapping...")

# Create a date-specific industry mapping: {date: {symbol: industry}}
industry_map_by_date = {}

for date in df_valid['date'].unique():
    date_data = df_valid[df_valid['date'] == date]
    industry_map_by_date[date] = dict(zip(date_data['symbol'], date_data['FnGuide Industry']))

print(f"  Total unique dates: {len(industry_map_by_date)}")
print(f"  Example date: {list(industry_map_by_date.keys())[0]}")
print(f"  Symbols on example date: {len(industry_map_by_date[list(industry_map_by_date.keys())[0]])}")

# Calculate average industry statistics across all dates
all_industries = set()
symbols_per_date = []
industries_per_date = []

for date, mapping in industry_map_by_date.items():
    symbols_per_date.append(len(mapping))
    date_industries = set(mapping.values())
    industries_per_date.append(len(date_industries))
    all_industries.update(date_industries)

print(f"\n  Time-series statistics:")
print(f"    Total unique industries (across all time): {len(all_industries)}")
print(f"    Mean symbols per date: {np.mean(symbols_per_date):.1f}")
print(f"    Mean industries per date: {np.mean(industries_per_date):.1f}")

# ============================================================================
# 4. CALCULATE PEER RETURNS (EXCLUDING FOCAL FIRM) - DATE-SPECIFIC
# ============================================================================
print("\n4. Calculating peer returns (using date-specific industry membership)...")

# Initialize peer returns matrix
peer_returns_wide = pd.DataFrame(
    index=returns_wide.index,
    columns=returns_wide.columns,
    dtype=float
)

# Calculate peer returns date-by-date (cross-sectionally)
for date in returns_wide.index:
    if date not in industry_map_by_date:
        continue
    
    # Get industry mapping for this specific date
    date_industry_map = industry_map_by_date[date]
    
    # Group symbols by industry for this date
    date_industry_to_symbols = defaultdict(list)
    for symbol, industry in date_industry_map.items():
        date_industry_to_symbols[industry].append(symbol)
    
    # For each symbol on this date, calculate peer return
    for symbol in date_industry_map.keys():
        if symbol not in returns_wide.columns:
            continue
        
        industry = date_industry_map[symbol]
        # Get peer symbols (exclude focal firm)
        peer_symbols = [s for s in date_industry_to_symbols[industry] 
                       if s != symbol and s in returns_wide.columns]
        
        if len(peer_symbols) > 0:
            # Equal-weighted average of peer returns
            peer_returns_wide.loc[date, symbol] = returns_wide.loc[date, peer_symbols].mean()

print(f"  Peer returns shape: {peer_returns_wide.shape}")
print(f"  Non-null peer returns: {peer_returns_wide.notna().sum().sum():,}")
print(f"  Mean peer return: {peer_returns_wide.mean().mean():.4f}")

print("\n  Peer returns (first 5 rows, first 5 columns):")
print(peer_returns_wide.iloc[:5, :5])

# ============================================================================
# 5. IDENTIFY HIGH-QUINTILE PEER SHOCK EVENTS
# ============================================================================
print("\n5. Identifying high-quintile peer shock events...")

# For each date, calculate cross-sectional quintiles
quintile_threshold = 0.80  # Top 20%

event_matrix = pd.DataFrame(
    index=peer_returns_wide.index,
    columns=peer_returns_wide.columns,
    dtype=bool
)

for date in peer_returns_wide.index:
    # Get peer returns for this date (cross-section)
    peer_returns_date = peer_returns_wide.loc[date]
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
print(f"  Total high-quintile events: {total_events:,}")
print(f"  Events per firm (mean): {event_matrix.sum(axis=0).mean():.1f}")
print(f"  Events per date (mean): {event_matrix.sum(axis=1).mean():.1f}")

# ============================================================================
# 6. EXTRACT TURNOVER WINDOWS
# ============================================================================
print("\n6. Extracting turnover windows around events...")

WINDOW_BEFORE = 3
WINDOW_AFTER = 12
WINDOW_LENGTH = WINDOW_BEFORE + 1 + WINDOW_AFTER  # 16 months total

# Store all turnover windows
turnover_windows = []

# Track used events to avoid overlaps
used_events = set()  # (symbol, date_index)

# Convert dates to indices for easier manipulation
date_to_idx = {date: idx for idx, date in enumerate(turnover_wide.index)}
idx_to_date = {idx: date for date, idx in date_to_idx.items()}

# Iterate through all events in chronological order
for symbol in event_matrix.columns:
    # Get all event dates for this symbol
    event_dates = event_matrix.index[event_matrix[symbol]]
    
    for event_date in event_dates:
        event_idx = date_to_idx[event_date]
        
        # Skip if this event overlaps with a previously used event
        if (symbol, event_idx) in used_events:
            continue
        
        # Check if we have enough data before and after
        if event_idx < WINDOW_BEFORE or event_idx + WINDOW_AFTER >= len(turnover_wide):
            continue
        
        # Extract turnover window (t-3 to t+12)
        start_idx = event_idx - WINDOW_BEFORE
        end_idx = event_idx + WINDOW_AFTER + 1  # +1 for inclusive
        
        turnover_window = turnover_wide.iloc[start_idx:end_idx][symbol].values
        
        # Skip if any turnover is missing
        if pd.isna(turnover_window).any():
            continue
        
        # Skip if any turnover is zero (suspicious)
        if (turnover_window == 0).any():
            continue
        
        # Store this window
        turnover_windows.append(turnover_window)
        
        # Mark this event and overlapping future events as used
        for i in range(WINDOW_LENGTH):
            used_events.add((symbol, event_idx + i))

print(f"  Total valid turnover windows extracted: {len(turnover_windows)}")

if len(turnover_windows) == 0:
    print("\n  ERROR: No valid turnover windows found!")
    exit(1)

# ============================================================================
# 7. AGGREGATE AND NORMALIZE
# ============================================================================
print("\n7. Aggregating and normalizing turnover...")

# Convert to numpy array for easier manipulation
turnover_windows = np.array(turnover_windows)

print(f"  Turnover windows shape: {turnover_windows.shape}")
print(f"  Mean turnover at t=0: {turnover_windows[:, WINDOW_BEFORE].mean():.4f}%")

# Calculate average turnover at each relative time
avg_turnover = turnover_windows.mean(axis=0)

# Normalize by turnover at t=0 (event month)
normalized_turnover = avg_turnover / avg_turnover[WINDOW_BEFORE]

print(f"\n  Normalized turnover (relative to t=0):")
for i, val in enumerate(normalized_turnover):
    rel_month = i - WINDOW_BEFORE
    print(f"    t{rel_month:+3d}: {val:.4f}")

# ============================================================================
# 8. PLOT RESULTS
# ============================================================================
print("\n8. Plotting results...")

fig, ax = plt.subplots(figsize=(12, 6))

# X-axis: relative months
relative_months = np.arange(-WINDOW_BEFORE, WINDOW_AFTER + 1)

# Plot normalized turnover
ax.plot(relative_months, normalized_turnover, 
        marker='o', linewidth=2, markersize=6,
        color='#2E86AB', label='FnGuide Industry')

# Add horizontal line at y=1.0
ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=1)

# Add vertical line at t=0 (event month)
ax.axvline(x=0, color='red', linestyle='--', alpha=0.5, linewidth=1, 
           label='Peer Shock (t=0)')

# Formatting
ax.set_xlabel('Months Relative to High-Quintile Peer Return', fontsize=12)
ax.set_ylabel('Relative Average Stock Turnover', fontsize=12)
ax.set_title('Figure 1A: Turnover Following High-Quintile Peer Shock\n' + 
             f'(FnGuide Industry Classification, N={len(turnover_windows):,} events)',
             fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Set x-axis ticks
ax.set_xticks(relative_months)

# Set y-axis to start from a reasonable minimum
y_min = normalized_turnover.min() * 0.95
y_max = normalized_turnover.max() * 1.05
ax.set_ylim(y_min, y_max)

plt.tight_layout()
plt.savefig('outputs/figure1a_turnover_peer_shock.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved plot to: outputs/figure1a_turnover_peer_shock.png")

plt.show()

# ============================================================================
# 9. STATISTICAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nData coverage:")
print(f"  Date range: {price_wide.index.min().date()} to {price_wide.index.max().date()}")
print(f"  Number of months: {len(price_wide)}")
print(f"  Number of stocks (in wide format): {len(returns_wide.columns)}")
print(f"  Number of industries (across all time): {len(all_industries)}")

print(f"\nEvent statistics:")
print(f"  Total high-quintile events: {total_events:,}")
print(f"  Valid events (with complete data): {len(turnover_windows):,}")
print(f"  Average events per stock: {total_events / len(returns_wide.columns):.1f}")

print(f"\nTurnover statistics:")
print(f"  Mean turnover at t=-3: {avg_turnover[0]:.4f}%")
print(f"  Mean turnover at t=0: {avg_turnover[WINDOW_BEFORE]:.4f}%")
print(f"  Mean turnover at t=+12: {avg_turnover[-1]:.4f}%")

print(f"\nRelative change:")
print(f"  t=-3 to t=0: {(normalized_turnover[WINDOW_BEFORE] / normalized_turnover[0] - 1) * 100:+.2f}%")
print(f"  t=0 to t=+12: {(normalized_turnover[-1] / normalized_turnover[WINDOW_BEFORE] - 1) * 100:+.2f}%")
print(f"  t=-3 to t=+12: {(normalized_turnover[-1] / normalized_turnover[0] - 1) * 100:+.2f}%")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)



