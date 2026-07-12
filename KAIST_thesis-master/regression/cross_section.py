"""
Cross-sectional regression for Fama-MacBeth Step 2.

Runs cross-sectional regression at each time period using linearmodels.
Supports time-series aggregation with Newey-West standard errors.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from linearmodels.panel import FamaMacBeth
from linearmodels.panel.results import FamaMacBethResults
import warnings


class CrossSectionalRegressor:
    """
    Runs Fama-MacBeth cross-sectional regressions using linearmodels.

    Performs Step 2 of Fama-MacBeth procedure:
    - Cross-sectional regression at each date
    - Time-series average of coefficients
    - Newey-West standard errors for autocorrelation

    Parameters:
    -----------
    newey_west_lags : int
        Number of lags for Newey-West SE (default: 2)
    drop_missing : bool
        If True, drop observations with missing values (default: True)

    Attributes:
    -----------
    newey_west_lags : int
        Lags used for Newey-West SE
    """

    def __init__(
        self,
        newey_west_lags: int = 2,
        drop_missing: bool = True,
        check_rank: bool = True
    ):
        if newey_west_lags < 0:
            raise ValueError(
                f"newey_west_lags must be non-negative, got {newey_west_lags}"
            )

        self.newey_west_lags = newey_west_lags
        self.drop_missing = drop_missing
        self.check_rank = check_rank

    def run_fama_macbeth(
        self,
        dependent: pd.Series,
        independent: pd.DataFrame
    ) -> FamaMacBethResults:
        """
        Run Fama-MacBeth regression using linearmodels.

        Uses linearmodels.panel.FamaMacBeth which:
        1. Runs cross-sectional OLS at each date
        2. Computes time-series average of coefficients
        3. Applies Newey-West SE for autocorrelation

        Parameters:
        -----------
        dependent : pd.Series
            Dependent variable with MultiIndex (security, date)
        independent : pd.DataFrame
            Independent variables with MultiIndex (security, date) × variables

        Returns:
        --------
        result : FamaMacBethResults
            Regression results from linearmodels

        Notes:
        ------
        - MultiIndex format is REQUIRED: (security, date)
        - Missing values handled according to drop_missing parameter
        - Newey-West bandwidth set to self.newey_west_lags

        Examples:
        ---------
        >>> regressor = CrossSectionalRegressor(newey_west_lags=2)
        >>> result = regressor.run_fama_macbeth(
        ...     dependent=returns_mi,  # MultiIndex (security, date)
        ...     independent=betas_mi    # MultiIndex (security, date) × factors
        ... )
        >>> print(result.summary)
        """
        # Drop missing if requested
        if self.drop_missing:
            combined = pd.concat([dependent, independent], axis=1)
            combined_clean = combined.dropna()

            if len(combined_clean) == 0:
                raise ValueError(
                    "All observations dropped due to missing values. "
                    "Check your data for excessive NaN."
                )

            dependent_clean = combined_clean.iloc[:, 0]
            independent_clean = combined_clean.iloc[:, 1:]

            n_dropped = len(combined) - len(combined_clean)
            if n_dropped > 0:
                warnings.warn(
                    f"Dropped {n_dropped} observations (rows) ({n_dropped/len(combined)*100:.1f}%) "
                    "due to missing values (pairwise complete data required).",
                    UserWarning
                )
        else:
            # Validate inputs only if not dropping (after drop they're guaranteed to match)
            self._validate_inputs(dependent, independent)
            dependent_clean = dependent
            independent_clean = independent

        # Check sufficient data
        n_obs = len(dependent_clean)
        n_vars = len(independent_clean.columns)

        if n_obs < n_vars + 10:
            warnings.warn(
                f"Only {n_obs} observations for {n_vars} variables. "
                "Regression may be unreliable.",
                UserWarning
            )

        # Run Fama-MacBeth regression
        try:
            model = FamaMacBeth(
                dependent=dependent_clean,
                exog=independent_clean,
                check_rank=self.check_rank
            )

            result = model.fit(
                cov_type='kernel',
                bandwidth=self.newey_west_lags
            )

            return result

        except Exception as e:
            raise RuntimeError(
                f"Fama-MacBeth regression failed: {str(e)}\n"
                f"Check that data is properly formatted with MultiIndex (security, date)."
            ) from e

    def run_period_by_period(
        self,
        dependent: pd.Series,
        independent: pd.DataFrame
    ) -> Dict[pd.Timestamp, Dict[str, float]]:
        """
        Run cross-sectional regression separately for each period.

        Returns coefficient estimates for each date instead of time-series average.

        Parameters:
        -----------
        dependent : pd.Series
            MultiIndex (security, date)
        independent : pd.DataFrame
            MultiIndex (security, date) × variables

        Returns:
        --------
        coefficients : dict
            {date: {variable: coefficient}}

        Examples:
        ---------
        >>> coefficients = regressor.run_period_by_period(returns_mi, betas_mi)
        >>> # coefficients[pd.Timestamp('2020-01-31')] = {'tnic_ret': 0.53, 'log_me': -0.02, ...}
        """
        # Skip validation if drop_missing=True, since indices may have changed after dropna in run_fama_macbeth
        if not self.drop_missing:
            self._validate_inputs(dependent, independent)

        # Get unique dates
        dates = dependent.index.get_level_values('date').unique()

        coefficients = {}

        for date in dates:
            # Extract cross-section for this date
            y_t = dependent.xs(date, level='date')
            X_t = independent.xs(date, level='date')

            # Drop missing
            if self.drop_missing:
                combined = pd.concat([y_t, X_t], axis=1)
                combined_clean = combined.dropna()

                if len(combined_clean) < len(X_t.columns) + 2:
                    # Insufficient observations for this date
                    coefficients[date] = {col: np.nan for col in X_t.columns}
                    continue

                y_t = combined_clean.iloc[:, 0]
                X_t = combined_clean.iloc[:, 1:]

            # Run OLS for this cross-section
            try:
                from sklearn.linear_model import LinearRegression

                model = LinearRegression()
                model.fit(X_t.values, y_t.values)

                # Store coefficients
                coefficients[date] = {
                    col: coef for col, coef in zip(X_t.columns, model.coef_)
                }

            except Exception as e:
                warnings.warn(
                    f"Cross-sectional regression failed for date {date}: {str(e)}",
                    UserWarning
                )
                coefficients[date] = {col: np.nan for col in X_t.columns}

        return coefficients

    def extract_gamma_time_series(
        self,
        coefficients: Dict[pd.Timestamp, Dict[str, float]]
    ) -> pd.DataFrame:
        """
        Convert period-by-period coefficients to time-series DataFrame.

        Parameters:
        -----------
        coefficients : dict
            Output from run_period_by_period()

        Returns:
        --------
        gammas : pd.DataFrame
            Time-series of coefficients (date × variables)
        """
        # Convert nested dict to DataFrame
        gammas = pd.DataFrame.from_dict(coefficients, orient='index')
        gammas.index.name = 'date'

        return gammas

    def _validate_inputs(
        self,
        dependent: pd.Series,
        independent: pd.DataFrame
    ) -> None:
        """
        Validate MultiIndex format required by linearmodels.

        Raises:
        -------
        TypeError
            If inputs are not Series/DataFrame
        ValueError
            If MultiIndex format is incorrect or indices don't match
        """
        if not isinstance(dependent, pd.Series):
            raise TypeError(
                f"dependent must be pandas Series, got {type(dependent)}"
            )

        if not isinstance(independent, pd.DataFrame):
            raise TypeError(
                f"independent must be pandas DataFrame, got {type(independent)}"
            )

        # Check MultiIndex format
        if not isinstance(dependent.index, pd.MultiIndex):
            raise ValueError(
                "dependent must have MultiIndex (security, date). "
                f"Got index type: {type(dependent.index)}"
            )

        if not isinstance(independent.index, pd.MultiIndex):
            raise ValueError(
                "independent must have MultiIndex (security, date). "
                f"Got index type: {type(independent.index)}"
            )

        # Check level names
        if dependent.index.names != ['security', 'date']:
            raise ValueError(
                "dependent MultiIndex must have names ['security', 'date']. "
                f"Got: {dependent.index.names}"
            )

        if independent.index.names != ['security', 'date']:
            raise ValueError(
                "independent MultiIndex must have names ['security', 'date']. "
                f"Got: {independent.index.names}"
            )

        # Check indices match
        if not dependent.index.equals(independent.index):
            raise ValueError(
                "dependent and independent must have identical indices. "
                "Use preprocessing.align_and_validate() to align data."
            )

        # Check for variables
        if len(independent.columns) == 0:
            raise ValueError("independent has no columns (no variables)")


def run_cross_sectional_regression(
    dependent: pd.Series,
    independent: pd.DataFrame,
    newey_west_lags: int = 2
) -> FamaMacBethResults:
    """
    Convenience function for Fama-MacBeth regression.

    Parameters:
    -----------
    dependent : pd.Series
        MultiIndex (security, date)
    independent : pd.DataFrame
        MultiIndex (security, date) × variables
    newey_west_lags : int
        Lags for Newey-West SE

    Returns:
    --------
    result : FamaMacBethResults
        Regression results

    Examples:
    ---------
    >>> result = run_cross_sectional_regression(
    ...     dependent=returns_mi,
    ...     independent=betas_mi,
    ...     newey_west_lags=2
    ... )
    >>> print(result.summary)
    """
    regressor = CrossSectionalRegressor(newey_west_lags=newey_west_lags)
    return regressor.run_fama_macbeth(dependent, independent)


def extract_coefficients_and_stats(
    result: FamaMacBethResults
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Extract key statistics from FamaMacBeth results.

    Parameters:
    -----------
    result : FamaMacBethResults
        Results from linearmodels FamaMacBeth

    Returns:
    --------
    coefficients : pd.Series
        Time-series average of coefficients
    t_stats : pd.Series
        t-statistics (using Newey-West SE)
    p_values : pd.Series
        Two-sided p-values

    Examples:
    ---------
    >>> coefs, t_stats, p_vals = extract_coefficients_and_stats(result)
    >>> print(f"TNIC beta: {coefs['tnic_ret']:.4f} (t={t_stats['tnic_ret']:.2f})")
    """
    coefficients = result.params
    t_stats = result.tstats
    p_values = result.pvalues

    return coefficients, t_stats, p_values
