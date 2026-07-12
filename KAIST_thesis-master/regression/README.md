# Fama-MacBeth Regression Module

Flexible implementation of Fama-MacBeth two-step regression procedure supporting three methodologies:

1. **Direct** (modern momentum studies): All variables directly to cross-sectional regression
2. **Hybrid** (Fama-French 1992): Factors through Step 1, characteristics direct
3. **Pure two-step** (Fama-MacBeth 1973): All variables through Step 1 beta estimation

## Quick Start

```python
from regression import FamaMacBethRegression

# Direct method (for momentum studies like Hoberg 2018)
fm = FamaMacBethRegression(method='direct', newey_west_lags=2)

result = fm.fit(
    dependent=returns,  # pd.DataFrame (date × security)
    independent={
        'tnic_ret': tnic_returns,   # TNIC peer returns
        'log_me': log_market_cap,    # Log market cap
        'log_be_me': log_btm         # Log book-to-market
    }
)

result.print_summary()
```

## Methods

### 1. Direct Method

**Use case**: Momentum studies (Hoberg 2018), where variables are already peer returns or other directly-measured quantities.

**Process**: Skips Step 1, runs cross-sectional OLS at each date directly.

```python
fm = FamaMacBethRegression(method='direct')

result = fm.fit(
    dependent=returns,
    independent={'tnic_ret': tnic_returns, 'log_me': log_me}
)
```

### 2. Hybrid Method

**Use case**: Fama-French (1992) style, combining noisy factors (need beta estimation) with precise characteristics (use directly).

**Process**:
- Step 1: Estimate betas for specified factors only
- Step 2: Use estimated betas + characteristics in cross-section

```python
fm = FamaMacBethRegression(method='hybrid', window=36)

result = fm.fit(
    dependent=returns,
    independent={
        'mkt_rf': market_excess,  # Factor → Step 1
        'smb': size_factor,       # Factor → Step 1
        'log_me': log_cap,        # Characteristic → direct
        'log_be_me': log_btm      # Characteristic → direct
    },
    factors=['mkt_rf', 'smb']  # Specify factors for Step 1
)
```

### 3. Pure Two-Step Method

**Use case**: Fama-MacBeth (1973) original, for traditional risk factor analysis.

**Process**:
- Step 1: Estimate rolling betas for ALL variables
- Step 2: Cross-sectional regression on estimated betas

```python
fm = FamaMacBethRegression(method='two_step', window=60)

result = fm.fit(
    dependent=returns,
    independent={
        'mkt_rf': market,
        'smb': size_factor,
        'hml': value_factor
    }
)
```

## Input Data Format

**Required**: Wide format DataFrames (date × security)

```python
# Example structure
returns = pd.DataFrame({
    'SEC001': [0.01, 0.02, ...],
    'SEC002': [0.03, -0.01, ...],
    ...
}, index=pd.DatetimeIndex(['2020-01-31', '2020-02-29', ...]))
```

All DataFrames must:
- Have DatetimeIndex (dates as index)
- Have identical column names (security IDs)
- Be aligned on same dates and securities

The module will:
- Validate format
- Align data across variables
- Convert internally to MultiIndex format required by linearmodels
- Handle missing data gracefully

## Results Object

The `FMResults` object provides access to:

```python
# Regression coefficients
result.params           # Time-series average
result.tstats           # t-statistics (Newey-West SE)
result.pvalues          # p-values

# Time-series of gammas (cross-sectional coefficients)
result.gamma_time_series  # pd.DataFrame (date × variables)

# Betas (for two_step/hybrid methods)
result.betas            # Dict[str, pd.DataFrame]
beta_tnic = result.get_beta('tnic_ret')  # (date × security)

# Summary and diagnostics
result.summary()        # pd.DataFrame with statistics
result.print_summary()  # Pretty-print results

# Save/load
result.save('results.pkl')
FMResults.load('results.pkl')
```

## Parameters

### FamaMacBethRegression

- `method` (str): 'direct', 'hybrid', or 'two_step'
- `window` (int): Rolling window for beta estimation (default: 36)
- `min_periods` (int): Minimum observations for beta estimation (default: window - 6)
- `newey_west_lags` (int): Lags for Newey-West SE (default: 2)
- `verbose` (bool): Print diagnostic messages (default: True)

## Module Structure

```
regression/
├── __init__.py              # Main exports
├── fama_macbeth.py          # Orchestrator class
├── rolling_beta.py          # Step 1: Rolling beta estimation
├── cross_section.py         # Step 2: Cross-sectional regressions
├── results.py               # Results container
├── preprocessing.py         # Data validation and alignment
├── utils.py                 # Helper functions
└── README.md               # This file
```

## Data Handling

### Missing Data

The module handles:
- New listings (security appears mid-sample)
- Delistings (security disappears mid-sample)
- Trading halts (sporadic missing returns)
- Missing peer data (first periods without TNIC data)

**Strategy**: Observations with missing values are dropped. Preprocessing validates data coverage and warns about potential issues.

### Alignment

When data don't align perfectly:

```python
# Automatic alignment
dependent_aligned, independent_aligned, diagnostics = align_and_validate(
    dependent=returns,
    independent_dict={'tnic_ret': tnic_returns, 'log_me': log_me},
    verbose=True
)
```

Prints diagnostic report:
- Sample size (periods × securities)
- Missing values by variable
- Coverage statistics

### Edge Cases

- **Too few securities**: Module warns if cross-section < variables + 10
- **Too few periods**: Module requires at least `window` periods for two_step/hybrid
- **Rank deficiency**: If variables are perfectly collinear, linearmodels will raise error

## Examples

### Example 1: Hoberg (2018) Replication

```python
from regression import FamaMacBethRegression

# Direct method - appropriate for peer returns
fm = FamaMacBethRegression(
    method='direct',
    newey_west_lags=2,  # Standard in literature
    verbose=True
)

result = fm.fit(
    dependent=monthly_returns,
    independent={
        'tnic_ret': tnic_peer_returns,      # TNIC peer returns
        'sic_ret': sic_peer_returns,        # SIC peer returns
        'ret_t1': lagged_returns_1m,        # Past 1-month return
        'ret_t2_t12': lagged_returns_2_12m, # Past 2-12 month return
        'log_me': log_market_cap,           # Firm size
        'log_be_me': log_book_to_market     # Value
    }
)

# Check significance of TNIC peer return coefficient
if 'tnic_ret' in result.get_significant_variables(alpha=0.05):
    print(f"TNIC coefficient: {result.params['tnic_ret']:.4f}")
    print(f"t-stat: {result.tstats['tnic_ret']:.2f}")
```

### Example 2: Fama-French Three-Factor Model

```python
# Hybrid method - factors through Step 1, characteristics direct
fm = FamaMacBethRegression(
    method='hybrid',
    window=60,  # 5-year rolling window
    newey_west_lags=2
)

result = fm.fit(
    dependent=excess_returns,
    independent={
        'mkt_rf': market_excess,
        'smb': size_factor,
        'hml': value_factor,
        'log_me': log_market_cap,
        'log_be_me': log_book_to_market
    },
    factors=['mkt_rf', 'smb', 'hml']  # Only these go through Step 1
)

# Access factor betas
beta_market = result.get_beta('mkt_rf')  # (date × security) DataFrame
print(f"Market beta for SEC001 in 2020-01: {beta_market.loc['2020-01-31', 'SEC001']:.3f}")
```

### Example 3: Traditional CAPM

```python
# Pure two-step method
fm = FamaMacBethRegression(
    method='two_step',
    window=60,
    min_periods=48  # Require at least 48 months
)

result = fm.fit(
    dependent=excess_returns,
    independent={'mkt_rf': market_excess}
)

# Plot time series of market risk premium (gamma_mkt)
import matplotlib.pyplot as plt

gamma_mkt = result.get_gamma('mkt_rf')
plt.plot(gamma_mkt.index, gamma_mkt.values)
plt.axhline(result.params['mkt_rf'], color='red', linestyle='--',
            label=f'Average: {result.params["mkt_rf"]:.2%}/month')
plt.title('Time-Varying Market Risk Premium')
plt.legend()
plt.show()
```

## Testing

Run comprehensive tests:

```bash
pytest tests/test_fama_macbeth.py -v
```

Tests cover:
- All 3 methods (direct, hybrid, two_step)
- 7 data scenarios (perfect, missing peer, new listing, delisting, annual characteristics, trading halt, too few securities)
- Preprocessing and validation
- Rolling beta estimation
- Results object functionality
- Error handling

## References

- Fama, E. F., & MacBeth, J. D. (1973). Risk, return, and equilibrium: Empirical tests. *Journal of Political Economy*, 81(3), 607-636.
- Fama, E. F., & French, K. R. (1992). The cross-section of expected stock returns. *The Journal of Finance*, 47(2), 427-465.
- Hoberg, G., & Phillips, G. (2018). Text-based industry momentum. *Journal of Financial and Quantitative Analysis*, 53(6), 2355-2388.

## Dependencies

- pandas
- numpy
- statsmodels (for rolling OLS)
- linearmodels (for Fama-MacBeth cross-sectional regressions)
- scikit-learn (for fallback OLS in period-by-period regressions)
