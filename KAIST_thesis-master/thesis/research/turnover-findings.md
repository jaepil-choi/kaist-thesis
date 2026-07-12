# Turnover Calculation: Lessons Learned

**Date**: November 10, 2025
**Context**: Replicating Hoberg et al. (2018) Figure 1A - Turnover Around Peer Shocks

## Executive Summary

After extensive trial and error, we identified **two critical errors** in calculating share turnover for event studies:

1. **Normalization Order Error**: Normalizing individual windows first, then averaging (WRONG) vs. averaging first, then normalizing (CORRECT)
2. **Aggregation Error**: Averaging daily turnover ratios (WRONG) vs. aggregating trading values and market caps separately, then calculating ratio (CORRECT)

Both errors led to incorrect turnover patterns and obscured the true economic signal.

---

## The Journey: Two Critical Bugs

### Bug #1: Normalization Order (Discovered First)

#### The Wrong Approach (Initial Implementation)

```python
# WRONG: Normalize first, then average
for each event window:
    normalized_window = window / window[t=0]  # Normalize by event month
    store(normalized_window)

avg_normalized = mean(all_normalized_windows)  # Average normalized windows
```

**Problem**: This created extreme outliers when t=0 turnover was very small, causing spikes in the averaged result.

**Symptom**: Graph showed dramatic spikes and unrealistic patterns.

#### The Right Approach (First Fix)

```python
# CORRECT: Average first, then normalize
avg_turnover = mean(all_windows, axis=0)  # Average across windows first
normalized = avg_turnover / avg_turnover[t=-3]  # Then normalize by t=-3
```

**Insight**: Following Hoberg et al. (2018) methodology - they normalize the averaged turnover, not individual windows.

**Result**: Smooth, interpretable patterns emerged.

---

### Bug #2: Ratio Aggregation (Discovered Second)

#### The Wrong Approach (After Bug #1 Fix)

```python
# WRONG: Average daily turnover ratios
daily_turnover = trading_value / market_cap  # Calculate ratios first
monthly_turnover = daily_turnover.resample('ME').mean()  # Average the ratios
```

**Mathematical Error**:

```
mean(tv�/cap�, tv�/cap�, ..., tv�/cap�) ` (tv� + tv� + ... + tv�) / (cap� + cap� + ... + cap�)
```

**Problem**: Averaging ratios gives equal weight to each day, regardless of market cap size. A small-cap day with high turnover disproportionately affects the result.

**Symptom**: Monthly turnover values seemed reasonable but were mathematically incorrect.

#### The Right Approach (Second Fix - CANONICAL)

```python
# CORRECT: Aggregate first, then calculate ratio
monthly_trading_value = trading_value.resample('ME').sum()  # Total value traded
monthly_market_cap = market_cap.resample('ME').mean()  # Average market cap
monthly_turnover = monthly_trading_value / monthly_market_cap  # Then calculate ratio
```

**Mathematical Logic**:

- **Numerator**: Sum of daily trading values = Total value traded during month
- **Denominator**: Average of daily market caps = Representative firm size during month
- **Ratio**: Fraction of average market cap that changed hands during the month

**Empirical Validation**:

- Wrong method: Mean turnover = 0.026089 (2.6%)
- Correct method: Mean turnover = 0.481800 (48.2%)
- **Difference: ~18x higher with correct method**

---

## Why This Matters: Economic Intuition

### Monthly Turnover Definition

**Correct Interpretation**:
> "During this month, total trading value equaled X% of the company's average market capitalization"

**Example**:

- Company has average market cap of $100M during month
- Total trading value during month = $50M
- **Monthly turnover = 50%**

This means: Half the company's value changed hands during the month.

**Why NOT average daily ratios?**

Daily ratios treat each day equally, but some days have:

- Higher market cap (stock price increased)
- Lower market cap (stock price decreased)

If we average ratios, a low-cap day with high trading gets the same weight as a high-cap day with low trading, which doesn't reflect true economic turnover.

### Normalization in Event Studies

**Why normalize by t=-3 (not t=0)?**

Following Hoberg et al. (2018):

- t=-3 is "normal" pre-event period
- Setting t=-3 = 1.0 allows us to see changes relative to baseline
- Changes at t=0 and beyond show response to peer shock

**Why average first, then normalize?**

Individual normalization creates outliers:

- Firm with t=0 turnover = 0.001% and t=1 turnover = 0.1%
- Normalized: t=1 / t=0 = 100x spike!
- This outlier dominates the average

Averaging first smooths out firm-specific noise:

- Average turnover at t=0 = 2%
- Average turnover at t=1 = 2.5%
- Normalized: 1.25x increase (realistic)

---

## Implementation History

### Stage 1: Initial Naive Implementation

**Code**: `figure1_graph_a.py` (early version)

```python
# Wrong on both counts
daily_turnover = trading_value / market_cap
monthly_turnover = daily_turnover.resample('ME').mean()

for each window:
    normalized_window = window / window[t=0]

avg_normalized = mean(all_normalized_windows)
```

**Result**: Spiky, unrealistic patterns with extreme values.

### Stage 2: Fixed Normalization Order

**Code**: `text-based-industry-momentum-korea.py` (intermediate)

```python
# Fixed normalization, but still wrong aggregation
daily_turnover = trading_value / market_cap  # Still wrong!
monthly_turnover = daily_turnover.resample('ME').mean()

avg_turnover = mean(all_windows, axis=0)  # Fixed: average first
normalized = avg_turnover / avg_turnover[t=-3]  # Then normalize
```

**Result**: Smooth patterns, but turnover magnitudes too low (2.6% vs expected ~48%).

### Stage 3: Fixed Both (CANONICAL METHOD)

**Code**: `text-based-industry-momentum-korea.py` (current, Nov 10 2025)

```python
# Both fixes applied
monthly_trading_value = trading_value.resample('ME').sum()  # Aggregate first
monthly_market_cap = market_cap.resample('ME').mean()
monthly_turnover = monthly_trading_value / monthly_market_cap  # Then ratio

avg_turnover = mean(all_windows, axis=0)  # Average first
normalized = avg_turnover / avg_turnover[t=-3]  # Then normalize
```

**Result**: Correct magnitudes (48% turnover) and smooth, interpretable patterns.

---

## Canonical Formula

### Monthly Share Turnover (from Daily Data)

```
Monthly Turnover = �(Daily Trading Value) / mean(Daily Market Cap)
```

Where:

- **�(Daily Trading Value)**: Sum of trading value across all trading days in month
- **mean(Daily Market Cap)**: Average market capitalization across all trading days in month

### Alternative Formula (Using Volume/Shares - Future Work)

```
Monthly Turnover = �(Daily Trading Volume) / mean(Daily Shares Outstanding)
```

**Note**: We will switch to this formula once we have `shares_outstanding` data in daily frequency. The logic is identical - aggregate flow variable (volume), divide by average stock variable (shares).

---

## Key Takeaways

### Mathematical Principles

1. **Ratios must be computed AFTER aggregation, not before**
   - Never average pre-computed ratios
   - Always aggregate numerator and denominator separately

2. **In event studies, average BEFORE normalizing**
   - Normalization amplifies noise in individual time series
   - Averaging first smooths out idiosyncratic variation

3. **Flow vs. Stock variables**
   - Flow (trading value, volume): SUM over period
   - Stock (market cap, shares): AVERAGE over period

### Practical Implications

1. **Order matters in every step**:
   - Step 1: Aggregate daily data � monthly (sum flows, average stocks)
   - Step 2: Calculate ratios (flow / stock)
   - Step 3: Extract event windows
   - Step 4: Average windows across events
   - Step 5: Normalize by baseline (t=-3)

2. **Data validation**:
   - Monthly turnover of 2.6% seemed plausible but was wrong
   - Monthly turnover of 48% seems high but is mathematically correct
   - Always check: Does the formula match the economic definition?

3. **Why it took so long**:
   - Both bugs produced "reasonable-looking" results
   - Required deep understanding of event study methodology
   - Required careful mathematical reasoning about ratio aggregation

---

## Comparison: Wrong vs. Right Methods

| Aspect | Wrong Method | Correct Method |
|--------|--------------|----------------|
| **Daily � Monthly** | `mean(tv/cap)` | `sum(tv) / mean(cap)` |
| **Mean Turnover** | 2.6% | 48.2% |
| **Normalization** | Per-window first | Average first |
| **Pattern Quality** | Spiky with outliers | Smooth and interpretable |
| **Economic Meaning** | Unclear | Clear: % of market cap traded |

### Why Wrong Method Seemed Reasonable

1. **Low values (2.6%)**: Matched intuition about "monthly" turnover
2. **Smooth after normalization fix**: Averaging first hid the aggregation error
3. **No obvious red flags**: Required understanding the mathematical definition to spot

### How We Caught It

User's critical insight:
> "monthly turnover should be = (average trade value) / (average market cap) but you're calculating the mean of daily turnover. (tv1 + tv2) / (cap1 + cap2) != (tv1/cap1 + tv2/cap2) /2"

This immediately revealed the aggregation error.

---

## Code Reference

### Location

`text-based-industry-momentum-korea.py` lines 280-293 (as of Nov 10, 2025)

### Canonical Implementation

```python
print("\nStep 3: Aggregate to monthly first, then calculate turnover ratio...")
# CORRECT: Aggregate first, then calculate ratio (not average of ratios!)
# Sum trading value over month (total value traded)
monthly_trading_value = trading_value_df.resample('ME').sum()
# Average market cap over month (average market cap during month)
monthly_market_cap = market_cap_df.resample('ME').mean()

print("\nStep 4: Calculate turnover ratio = sum(trading_value) / mean(market_cap)...")
share_turnover_df = monthly_trading_value / monthly_market_cap
```

### Normalization (lines in `normalize_and_aggregate()` function)

```python
def normalize_and_aggregate(turnover_windows, WINDOW_BEFORE=3):
    """Normalize turnover windows by t=-3 and aggregate."""
    turnover_windows_array = np.array(turnover_windows)
    avg_turnover = turnover_windows_array.mean(axis=0)  # Average first
    normalized_turnover = avg_turnover / avg_turnover[0]  # Then normalize by t=-3
    return normalized_turnover
```

---

## Future Work

### Next Steps

1. **Validate with volume/shares data**
   - Add `shares_outstanding` to daily data
   - Compute: `monthly_turnover = sum(daily_volume) / mean(daily_shares)`
   - Should match current method (trading_value = volume � price, market_cap = shares � price)

2. **Compare with monthly direct data**
   - We have `monthly_trading_volume` and `monthly_float_shares` in data
   - Check if `monthly_trading_volume` is pre-aggregated (sum) or snapshot (end-of-month)
   - Document any discrepancies

3. **Cross-validation**
   - Run both methods (daily aggregated vs. monthly direct) side-by-side
   - Analyze differences in event study results
   - Document which method to use and why

### Open Questions

1. **What does `monthly_trading_volume` in our data represent?**
   - Sum of daily volumes during month? (consistent with our method)
   - End-of-month snapshot? (different definition)
   - Average daily volume? (would be wrong)

2. **Should we use listed shares or float shares?**
   - Listed shares: All outstanding shares
   - Float shares: Shares available for trading (excludes locked-up shares)
   - Hoberg et al. likely use float shares (more relevant for turnover)

---

## Lessons for Future Research

### General Principles

1. **Question everything, even when it looks right**
   - Smooth graphs don't guarantee correct methodology
   - Plausible magnitudes don't guarantee correct math

2. **Understand the economic definition first**
   - What does "monthly turnover" mean economically?
   - Then implement the formula that matches that definition

3. **Beware of "pre-computed" ratios**
   - Always check: Is this ratio computed before or after aggregation?
   - If after, you can aggregate further
   - If before, you must re-aggregate the components

4. **Event studies are tricky**
   - Normalization amplifies errors in individual series
   - Always average before normalizing unless you have strong reason not to

### Common Pitfalls

1. **Averaging ratios**: Almost never correct
2. **Normalizing before averaging**: Creates outliers
3. **Assuming data definitions**: Always verify what "monthly" means
4. **Trusting reasonable-looking results**: Dig deeper

### How to Avoid These Bugs

1. **Write down the math explicitly**:

   ```
   Want: Monthly turnover = Total Value Traded / Average Market Cap
   Have: Daily trading_value[t], Daily market_cap[t]

   Step 1: Total_Value = � trading_value[t] over month
   Step 2: Avg_Cap = mean(market_cap[t]) over month
   Step 3: Turnover = Total_Value / Avg_Cap
   ```

2. **Implement exactly as written**:

   ```python
   total_value = trading_value.resample('ME').sum()  # Step 1
   avg_cap = market_cap.resample('ME').mean()        # Step 2
   turnover = total_value / avg_cap                   # Step 3
   ```

3. **Validate against economic intuition**:
   - Is 2.6% monthly turnover reasonable? (Seemed yes, but was wrong)
   - Is 48% monthly turnover reasonable? (Seems high, but is correct for Korean market)
   - Check literature for typical values

---

## Timeline

- **October 2025**: Initial implementation with both bugs
- **Early November 2025**: Fixed normalization order (Bug #1)
  - Result: Smooth patterns but wrong magnitudes
- **November 10, 2025**: Fixed ratio aggregation (Bug #2)
  - User identified the mathematical error
  - Implemented canonical method
  - **Result: Both correct patterns AND correct magnitudes**

---

## Acknowledgment

This breakthrough came from user's sharp mathematical insight about ratio aggregation. The error was subtle because:

1. It produced smooth results after fixing Bug #1
2. The magnitudes (2.6%) seemed plausible
3. It required deep understanding of what "monthly turnover" means

The lesson: Always question the fundamentals, even when results look reasonable.

---

## References

- Hoberg, G., & Phillips, G. M. (2018). Text-based industry momentum. *Journal of Financial and Quantitative Analysis*, 53(6), 2355-2388.
  - Figure 1: Turnover around peer shocks
  - Methodology: Average turnover first, then normalize by pre-event period

---

**Last Updated**: November 10, 2025
**Status**:  CANONICAL METHOD ESTABLISHED
**Next**: Validate with volume/shares data and compare with monthly direct data
