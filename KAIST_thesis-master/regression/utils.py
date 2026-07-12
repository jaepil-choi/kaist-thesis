"""
Utility functions for Fama-MacBeth regressions.

Note: This module is kept minimal. Only contains functions used by external scripts.
"""

import pandas as pd
import numpy as np


def standardize_cross_sectional(
    df: pd.DataFrame,
    by_date: bool = True
) -> pd.DataFrame:
    """
    Compute cross-sectional z-scores (standardization).

    For each date (if by_date=True), transforms each variable to have
    mean=0 and std=1 across securities.

    Parameters
    ----------
    df : pd.DataFrame
        Data to standardize. Can be:
        - Wide format (date × security)
        - MultiIndex format (security, date) × variables
    by_date : bool, default True
        If True, standardize within each date (cross-sectional)
        If False, standardize entire series

    Returns
    -------
    pd.DataFrame
        Z-score transformed data

    Examples
    --------
    >>> # Wide format
    >>> returns = pd.DataFrame(...)  # date × security
    >>> z_returns = standardize_cross_sectional(returns, by_date=True)
    """
    # Convert nullable Float64 dtypes to regular float64
    df = df.astype('float64', errors='ignore')

    if isinstance(df.index, pd.MultiIndex):
        # MultiIndex format: (security, date) × variables
        date_level = df.index.names.index('date') if 'date' in df.index.names else 1

        if by_date:
            def standardize_group(group):
                return (group - group.mean()) / group.std()
            standardized = df.groupby(level=date_level).transform(standardize_group)
        else:
            standardized = (df - df.mean()) / df.std()

    else:
        # Wide format: date × security
        if by_date:
            means = df.mean(axis=1)
            stds = df.std(axis=1).replace(0, np.nan)
            standardized = df.sub(means, axis=0).div(stds, axis=0)
            standardized = standardized.replace([np.inf, -np.inf], np.nan)
        else:
            standardized = (df - df.mean()) / df.std()
            standardized = standardized.replace([np.inf, -np.inf], np.nan)

    return standardized
