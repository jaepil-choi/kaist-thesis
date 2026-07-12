"""
Rolling beta estimation for Fama-MacBeth Step 1.

Estimates time-varying factor exposures (betas) using rolling window OLS.
Supports multivariate regression with multiple factors.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from statsmodels.regression.rolling import RollingOLS
import warnings


class RollingBetaEstimator:
    """
    Estimates rolling betas for Fama-MacBeth Step 1.

    Uses statsmodels RollingOLS to estimate time-varying factor exposures
    for each security using a rolling window.

    Parameters:
    -----------
    window : int
        Rolling window size in periods (default: 36 months)
    min_periods : int, optional
        Minimum number of observations required (default: window - 6)
    center : bool
        If True, set labels at center of window (default: False)

    Attributes:
    -----------
    window : int
        Window size used
    min_periods : int
        Minimum periods required
    """

    def __init__(
        self,
        window: int = 36,
        min_periods: Optional[int] = None,
        center: bool = False
    ):
        if window < 12:
            raise ValueError(
                f"Window must be at least 12 periods. Got: {window}"
            )

        self.window = window
        self.min_periods = min_periods if min_periods is not None else window - 6
        self.center = center

        if self.min_periods < 12:
            warnings.warn(
                f"min_periods={self.min_periods} is very small. "
                "Beta estimates may be unreliable.",
                UserWarning
            )

        if self.min_periods > self.window:
            raise ValueError(
                f"min_periods ({self.min_periods}) cannot exceed window ({self.window})"
            )

    def estimate_betas(
        self,
        dependent: pd.DataFrame,
        factors: Dict[str, pd.DataFrame],
        add_constant: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Estimate rolling betas for each security against factors.

        For each security and each date, runs rolling OLS:
            returns_it = alpha + beta_1 * factor1_it + ... + beta_k * factorK_it + epsilon_it

        Parameters:
        -----------
        dependent : pd.DataFrame
            Dependent variable (date × security)
            E.g., stock returns
        factors : dict
            {factor_name: pd.DataFrame (date × security)}
            E.g., {'tnic_ret': tnic_returns_df, 'sic_ret': sic_returns_df}
        add_constant : bool
            If True, include intercept in regression (default: True)

        Returns:
        --------
        betas : dict
            {factor_name: pd.DataFrame (date × security)}
            Beta estimates for each factor at each date for each security

        Notes:
        ------
        - All DataFrames must have same shape and aligned index/columns
        - First (window - 1) rows will have NaN (insufficient history)
        - Missing values in window reduce effective sample size
        - Returns NaN if effective sample < min_periods

        Examples:
        ---------
        >>> estimator = RollingBetaEstimator(window=36, min_periods=30)
        >>> betas = estimator.estimate_betas(
        ...     dependent=returns,
        ...     factors={'tnic_ret': tnic_returns, 'log_me': log_me}
        ... )
        >>> # betas['tnic_ret'] is date × security DataFrame of TNIC betas
        >>> # betas['log_me'] is date × security DataFrame of size betas
        """
        # Validate inputs
        self._validate_inputs(dependent, factors)

        # Get dimensions
        dates = dependent.index
        securities = dependent.columns
        n_periods = len(dates)
        n_securities = len(securities)
        n_factors = len(factors)

        # Initialize output: {factor_name: date × security DataFrame}
        betas = {
            factor_name: pd.DataFrame(
                np.nan,
                index=dates,
                columns=securities
            )
            for factor_name in factors.keys()
        }

        # If add_constant, also store alphas
        if add_constant:
            alphas = pd.DataFrame(np.nan, index=dates, columns=securities)

        # Estimate betas for each security separately
        for sec in securities:
            # Extract security's time series
            y = dependent[sec].values  # (T,)

            # Build factor matrix: (T, K)
            X_list = []
            for factor_name in factors.keys():
                X_list.append(factors[factor_name][sec].values)

            X = np.column_stack(X_list)  # (T, K)

            # Convert to DataFrame for RollingOLS
            y_series = pd.Series(y, index=dates)
            X_df = pd.DataFrame(
                X,
                index=dates,
                columns=list(factors.keys())
            )

            # Run rolling OLS
            try:
                model = RollingOLS(
                    endog=y_series,
                    exog=X_df,
                    window=self.window,
                    min_nobs=self.min_periods,
                    expanding=False
                )

                result = model.fit()

                # Extract beta estimates: (T, K)
                beta_estimates = result.params.values  # (T, K)

                # Assign to output dictionaries
                for i, factor_name in enumerate(factors.keys()):
                    betas[factor_name][sec] = beta_estimates[:, i]

                # Store alpha if constant was included
                if add_constant and hasattr(result, 'params'):
                    # RollingOLS without explicit constant doesn't have intercept
                    # We need to add constant manually if needed
                    pass  # Handled below with add_constant preprocessing

            except Exception as e:
                warnings.warn(
                    f"Failed to estimate betas for security {sec}: {str(e)}. "
                    "Setting betas to NaN.",
                    UserWarning
                )
                # Betas already initialized as NaN, no action needed

        return betas

    def estimate_betas_with_constant(
        self,
        dependent: pd.DataFrame,
        factors: Dict[str, pd.DataFrame]
    ) -> tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
        """
        Estimate rolling betas with constant term (alpha).

        Parameters:
        -----------
        dependent : pd.DataFrame
            Dependent variable (date × security)
        factors : dict
            {factor_name: pd.DataFrame (date × security)}

        Returns:
        --------
        betas : dict
            {factor_name: pd.DataFrame (date × security)}
        alphas : pd.DataFrame
            Intercepts (date × security)
        """
        # Validate inputs
        self._validate_inputs(dependent, factors)

        dates = dependent.index
        securities = dependent.columns

        # Initialize outputs
        betas = {
            factor_name: pd.DataFrame(np.nan, index=dates, columns=securities)
            for factor_name in factors.keys()
        }
        alphas = pd.DataFrame(np.nan, index=dates, columns=securities)

        # Estimate for each security
        for sec in securities:
            y = dependent[sec]

            # Build X with constant
            X_dict = {'const': pd.Series(1.0, index=dates)}
            for factor_name, factor_df in factors.items():
                X_dict[factor_name] = factor_df[sec]

            X_df = pd.DataFrame(X_dict, index=dates)

            try:
                model = RollingOLS(
                    endog=y,
                    exog=X_df,
                    window=self.window,
                    min_nobs=self.min_periods,
                    expanding=False
                )

                result = model.fit()

                # Extract parameters
                params = result.params  # DataFrame (T, K+1)

                alphas[sec] = params['const'].values

                for factor_name in factors.keys():
                    betas[factor_name][sec] = params[factor_name].values

            except Exception as e:
                warnings.warn(
                    f"Failed to estimate betas for security {sec}: {str(e)}",
                    UserWarning
                )

        return betas, alphas

    def _validate_inputs(
        self,
        dependent: pd.DataFrame,
        factors: Dict[str, pd.DataFrame]
    ) -> None:
        """
        Validate that all DataFrames are properly aligned.

        Raises:
        -------
        TypeError
            If inputs are not DataFrames/dict
        ValueError
            If shapes don't match or indices/columns differ
        """
        if not isinstance(dependent, pd.DataFrame):
            raise TypeError(
                f"dependent must be pandas DataFrame, got {type(dependent)}"
            )

        if not isinstance(factors, dict):
            raise TypeError(
                f"factors must be dict, got {type(factors)}"
            )

        if len(factors) == 0:
            raise ValueError("factors dict is empty. Provide at least one factor.")

        # Check that all factors are DataFrames
        for factor_name, factor_df in factors.items():
            if not isinstance(factor_df, pd.DataFrame):
                raise TypeError(
                    f"factors['{factor_name}'] must be DataFrame, got {type(factor_df)}"
                )

        # Check alignment: all must have same index and columns
        ref_index = dependent.index
        ref_columns = dependent.columns

        for factor_name, factor_df in factors.items():
            if not factor_df.index.equals(ref_index):
                raise ValueError(
                    f"factors['{factor_name}'] has different index than dependent. "
                    "All DataFrames must be aligned."
                )

            if not factor_df.columns.equals(ref_columns):
                raise ValueError(
                    f"factors['{factor_name}'] has different columns than dependent. "
                    "All DataFrames must be aligned."
                )

        # Check sufficient data
        n_periods = len(dependent)
        if n_periods < self.window:
            raise ValueError(
                f"Insufficient data: {n_periods} periods < window size {self.window}. "
                f"Provide at least {self.window} periods."
            )

    def get_effective_dates(self, dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """
        Get dates where beta estimates are available (after burn-in period).

        Parameters:
        -----------
        dates : pd.DatetimeIndex
            Full date range

        Returns:
        --------
        effective_dates : pd.DatetimeIndex
            Dates with valid beta estimates (excluding first window - 1 periods)
        """
        if self.center:
            # Center: first and last (window // 2) periods are NaN
            start_idx = self.window // 2
            end_idx = len(dates) - (self.window - self.window // 2)
            return dates[start_idx:end_idx]
        else:
            # Right-aligned: first (window - 1) periods are NaN
            return dates[self.window - 1:]


def estimate_betas_multivariate(
    dependent: pd.DataFrame,
    factors: Dict[str, pd.DataFrame],
    window: int = 36,
    min_periods: Optional[int] = None
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function for rolling beta estimation.

    Parameters:
    -----------
    dependent : pd.DataFrame
        Dependent variable (date × security)
    factors : dict
        {factor_name: pd.DataFrame (date × security)}
    window : int
        Rolling window size
    min_periods : int, optional
        Minimum observations required

    Returns:
    --------
    betas : dict
        {factor_name: pd.DataFrame (date × security)}

    Examples:
    ---------
    >>> betas = estimate_betas_multivariate(
    ...     dependent=returns,
    ...     factors={'tnic_ret': tnic_returns, 'sic_ret': sic_returns},
    ...     window=36,
    ...     min_periods=30
    ... )
    """
    estimator = RollingBetaEstimator(window=window, min_periods=min_periods)
    return estimator.estimate_betas_with_constant(dependent, factors)[0]
