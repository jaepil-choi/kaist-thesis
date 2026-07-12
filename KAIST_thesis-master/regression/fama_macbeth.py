"""
Fama-MacBeth regression facade.

Provides a simple interface that delegates to different regression strategies:
- DirectStrategy: Skip beta estimation, run cross-sectional regressions directly
- TwoStepStrategy: Estimate betas first, then run cross-sectional regressions

Example usage:
    >>> from regression import FamaMacBethRegression
    >>>
    >>> # Direct method (for momentum studies like Hoberg 2018)
    >>> fm = FamaMacBethRegression(method='direct', newey_west_lags=2)
    >>> result = fm.fit(
    ...     dependent=returns,
    ...     independent={'tnic_ret': tnic_returns, 'log_me': log_me}
    ... )
    >>> result.print_summary()
    >>>
    >>> # Two-step method (for risk factors)
    >>> fm = FamaMacBethRegression(method='two_step', window=36)
    >>> result = fm.fit(
    ...     dependent=returns,
    ...     independent={'mkt_rf': mkt_rf, 'smb': smb, 'hml': hml}
    ... )
"""

import pandas as pd
from typing import Dict, Optional

from .preprocessing import align_and_validate
from .results import FMResults
from .strategies import DirectStrategy, TwoStepStrategy


class FamaMacBethRegression:
    """
    Fama-MacBeth regression facade.

    Delegates to different strategies based on the method parameter.
    Uses the Strategy pattern for clean separation of regression algorithms.

    Parameters
    ----------
    method : str, default 'direct'
        Regression method:
        - 'direct': All variables directly to cross-section (modern approach)
        - 'two_step': All variables through Step 1 beta estimation (FM 1973)

    window : int, default 36
        Rolling window for beta estimation (only used for two_step method)

    min_periods : int, optional
        Minimum observations for beta estimation (only used for two_step)
        Default: window - 6

    newey_west_lags : int, default 2
        Number of lags for Newey-West standard errors

    check_rank : bool, default True
        Check for rank deficiency in cross-sectional regressions

    verbose : bool, default True
        Print diagnostic messages

    Attributes
    ----------
    method : str
        Selected regression method
    _strategy : RegressionStrategy
        Concrete strategy instance (DirectStrategy or TwoStepStrategy)
    """

    def __init__(
        self,
        method: str = 'direct',
        window: int = 36,
        min_periods: Optional[int] = None,
        newey_west_lags: int = 2,
        check_rank: bool = True,
        verbose: bool = True
    ):
        """Initialize Fama-MacBeth regression with specified method."""
        valid_methods = ['direct', 'two_step']
        if method not in valid_methods:
            raise ValueError(
                f"method must be one of {valid_methods}, got '{method}'"
            )

        self.method = method
        self.verbose = verbose

        # Initialize strategy based on method
        if method == 'direct':
            self._strategy = DirectStrategy(
                newey_west_lags=newey_west_lags,
                check_rank=check_rank,
                verbose=verbose
            )
        elif method == 'two_step':
            self._strategy = TwoStepStrategy(
                window=window,
                newey_west_lags=newey_west_lags,
                check_rank=check_rank,
                verbose=verbose
            )

    def fit(
        self,
        dependent: pd.DataFrame,
        independent: Dict[str, pd.DataFrame]
    ) -> FMResults:
        """
        Run Fama-MacBeth regression.

        Parameters
        ----------
        dependent : pd.DataFrame
            Dependent variable (date × security), e.g., monthly returns

        independent : Dict[str, pd.DataFrame]
            Independent variables {name: pd.DataFrame (date × security)}
            E.g., {'tnic_ret': tnic_df, 'log_me': log_me_df}

        Returns
        -------
        FMResults
            Regression results with coefficients, statistics, and diagnostics

        Examples
        --------
        Direct method (Hoberg 2018 style):
        >>> result = fm.fit(
        ...     dependent=returns,
        ...     independent={
        ...         'tnic_ret': tnic_returns,
        ...         'ret_t1': lagged_returns,
        ...         'log_me': log_market_cap
        ...     }
        ... )

        Two-step method (FM 1973 style):
        >>> result = fm.fit(
        ...     dependent=returns,
        ...     independent={'mkt_rf': market, 'smb': size, 'hml': value}
        ... )
        """
        if self.verbose:
            print(f"Running Fama-MacBeth regression (method={self.method})...")

        # Validate and align data
        if self.verbose:
            print("Validating and aligning data...")

        dependent_aligned, independent_aligned, diagnostics = align_and_validate(
            dependent=dependent,
            independent_dict=independent,
            verbose=self.verbose
        )

        # Delegate to strategy
        result = self._strategy.fit(dependent_aligned, independent_aligned)

        if self.verbose:
            print("\nRegression complete!")
            result.print_summary()

        return result
