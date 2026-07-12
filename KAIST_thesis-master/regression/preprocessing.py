"""
Data preprocessing and validation for Fama-MacBeth regressions.

Handles:
- Wide format (date × security) validation
- Conversion to MultiIndex format required by linearmodels
- Missing data diagnostics
- Alignment across multiple DataFrames
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any, Optional
import warnings


def validate_dataframe(
    df: pd.DataFrame,
    name: str,
    require_datetime_index: bool = True
) -> None:
    """
    Validate DataFrame format for Fama-MacBeth regression.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame to validate (expected: date × security)
    name : str
        Variable name for error messages
    require_datetime_index : bool
        If True, require DatetimeIndex

    Raises:
    -------
    TypeError
        If df is not a DataFrame
    ValueError
        If DataFrame format is invalid
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"{name} must be a pandas DataFrame, got {type(df)}"
        )

    if len(df) == 0:
        raise ValueError(f"{name} is empty (0 rows)")

    if len(df.columns) == 0:
        raise ValueError(f"{name} has no columns")

    if require_datetime_index and not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(
            f"{name} must have DatetimeIndex (date × security format). "
            f"Got index type: {type(df.index)}"
        )

    # Check for all-NaN rows or columns
    all_nan_rows = df.isna().all(axis=1).sum()
    all_nan_cols = df.isna().all(axis=0).sum()

    if all_nan_rows > 0:
        warnings.warn(
            f"{name} has {all_nan_rows} rows with all NaN values. "
            "These will be dropped during regression.",
            UserWarning
        )

    if all_nan_cols > 0:
        warnings.warn(
            f"{name} has {all_nan_cols} columns with all NaN values across all dates. "
            "These securities will be excluded from all regressions.",
            UserWarning
        )


def _stack_and_swap(df: pd.DataFrame, name: str = None) -> pd.Series:
    """
    Helper: Stack date×security → (security, date) MultiIndex.

    Parameters
    ----------
    df : pd.DataFrame
        Wide format (date × security)
    name : str, optional
        Name for resulting Series

    Returns
    -------
    pd.Series
        MultiIndex Series (security, date)
    """
    stacked = df.stack(future_stack=True)
    stacked.index.names = ['date', 'security']
    if name:
        stacked.name = name
    return stacked.swaplevel()


def convert_to_multiindex(
    dependent: pd.DataFrame,
    independent_dict: Dict[str, pd.DataFrame]
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Convert wide format DataFrames to MultiIndex format required by linearmodels.

    Transforms date × security format → (security, date) MultiIndex.

    Parameters
    ----------
    dependent : pd.DataFrame
        Dependent variable (date × security)
    independent_dict : Dict[str, pd.DataFrame]
        Independent variables {name: DataFrame (date × security)}

    Returns
    -------
    dependent_mi : pd.Series
        MultiIndex Series (security, date)
    independent_mi : pd.DataFrame
        MultiIndex DataFrame (security, date) × variables
    """
    # Stack dependent variable
    dependent_mi = _stack_and_swap(dependent)

    # Stack and combine independent variables
    independent_mi = pd.concat(
        [_stack_and_swap(df, name=var_name)
         for var_name, df in independent_dict.items()],
        axis=1
    )

    return dependent_mi, independent_mi


def check_coverage(
    df_dict: Dict[str, pd.DataFrame],
    min_periods: Optional[int] = None,
    min_securities: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate diagnostic report on data coverage and missing values.

    Parameters
    ----------
    df_dict : Dict[str, pd.DataFrame]
        Independent variables {name: DataFrame (date × security)}
    min_periods : int, optional
        Warn if securities have fewer observations
    min_securities : int, optional
        Warn if dates have fewer securities

    Returns
    -------
    Dict[str, Any]
        Diagnostic report with warnings and coverage statistics
    """
    first_df = list(df_dict.values())[0]
    report = {
        'n_periods': len(first_df),
        'n_securities': len(first_df.columns),
        'warnings': [],
        'missing_by_variable': {}
    }

    # Check missing values and securities per date
    for var_name, var_df in df_dict.items():
        # Missing values
        n_missing = var_df.isna().sum().sum()
        pct_missing = n_missing / var_df.size * 100
        report['missing_by_variable'][var_name] = {
            'n_missing': int(n_missing),
            'pct_missing': round(pct_missing, 2)
        }

        if pct_missing > 50:
            report['warnings'].append(
                f"{var_name}: {pct_missing:.1f}% missing values"
            )

        # Securities per date (critical for cross-sectional regression)
        securities_per_date = var_df.notna().sum(axis=1)
        min_sec = securities_per_date.min()

        if min_sec == 0:
            n_zero = (securities_per_date == 0).sum()
            report['warnings'].append(
                f"{var_name}: {n_zero} dates have zero securities"
            )
        elif min_securities and min_sec < min_securities:
            report['warnings'].append(
                f"{var_name}: Min securities per date = {min_sec} (< {min_securities})"
            )

    return report


def print_diagnostics(report: Dict[str, Any]) -> None:
    """
    Pretty-print diagnostics report.

    Parameters:
    -----------
    report : dict
        Output from check_coverage()
    """
    print("=" * 60)
    print("DATA COVERAGE DIAGNOSTICS")
    print("=" * 60)

    print(f"\nSample size: {report['n_periods']} periods × {report['n_securities']} securities")

    print("\nMissing values by variable:")
    for var_name, stats in report['missing_by_variable'].items():
        print(f"  {var_name:20s}: {stats['n_missing']:6d} ({stats['pct_missing']:5.2f}%)")

    if 'securities_per_date' in report:
        print("\nSecurities per date (for Fama-MacBeth cross-sections):")
        for var_name, stats in report['securities_per_date'].items():
            print(f"  {var_name:20s}: mean={stats['mean']:6.1f}, min={stats['min']:4d}, max={stats['max']:4d}")

    if report['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in report['warnings']:
            print(f"  - {warning}")

    if report['insufficient_periods']:
        print("\nSecurities with insufficient periods:")
        for var_name, insufficient in report['insufficient_periods'].items():
            print(f"  {var_name}: {len(insufficient)} securities")

    if report['insufficient_securities']:
        print("\nDates with insufficient securities:")
        for var_name, insufficient in report['insufficient_securities'].items():
            print(f"  {var_name}: {len(insufficient)} dates")

    print("=" * 60)


def align_and_validate(
    dependent: pd.DataFrame,
    independent_dict: Dict[str, pd.DataFrame],
    min_periods: Optional[int] = None,
    min_securities: Optional[int] = None,
    verbose: bool = True
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], Dict[str, Any]]:
    """
    Validate, align, and diagnose data for Fama-MacBeth regression.

    This is the main preprocessing function that should be called before
    running regressions.

    Parameters:
    -----------
    dependent : pd.DataFrame
        Dependent variable (date × security)
    independent_dict : dict
        {variable_name: DataFrame (date × security)}
    min_periods : int, optional
        Minimum periods per security for diagnostics
    min_securities : int, optional
        Minimum securities per period for diagnostics
    verbose : bool
        If True, print diagnostics

    Returns:
    --------
    dependent_aligned : pd.DataFrame
        Aligned dependent variable
    independent_aligned : dict
        Aligned independent variables
    diagnostics : dict
        Coverage report from check_coverage()

    Raises:
    -------
    TypeError, ValueError
        If validation fails
    """
    # Validate all DataFrames
    validate_dataframe(dependent, "dependent")

    for var_name, var_df in independent_dict.items():
        validate_dataframe(var_df, var_name)

    # Find common dates (required for stacking to MultiIndex)
    common_dates = dependent.index
    for var_name, var_df in independent_dict.items():
        common_dates = common_dates.intersection(var_df.index)

    # For securities, take the UNION not intersection
    # This allows different securities to be available at different dates
    # (proper unbalanced panel for Fama-MacBeth)
    all_securities = dependent.columns
    for var_name, var_df in independent_dict.items():
        all_securities = all_securities.union(var_df.columns)

    if len(common_dates) == 0:
        raise ValueError(
            "No common dates found across all variables. "
            "Check that all DataFrames have overlapping time periods."
        )

    # Note: We no longer require common securities across all variables
    # Each date's cross-sectional regression will use available securities for that date

    # Reindex all DataFrames to common dates and all securities
    # This creates NaN for missing security-date combinations
    dependent_aligned = dependent.reindex(index=common_dates, columns=all_securities)

    independent_aligned = {}
    for var_name, var_df in independent_dict.items():
        independent_aligned[var_name] = var_df.reindex(index=common_dates, columns=all_securities)

    # Run diagnostics
    all_data = {'dependent': dependent_aligned, **independent_aligned}
    diagnostics = check_coverage(all_data, min_periods, min_securities)

    if verbose:
        print_diagnostics(diagnostics)

    return dependent_aligned, independent_aligned, diagnostics
