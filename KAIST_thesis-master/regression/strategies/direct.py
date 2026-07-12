"""
Direct strategy for Fama-MacBeth regression.

Skips beta estimation (Step 1) and runs cross-sectional regressions directly.
Appropriate for momentum studies (Hoberg 2018) where variables are already
meaningful (peer returns, lagged returns, characteristics).
"""

from typing import Dict
import pandas as pd

from .base import RegressionStrategy
from ..preprocessing import convert_to_multiindex
from ..results import create_results_from_fm, FMResults


class DirectStrategy(RegressionStrategy):
    """
    Direct Fama-MacBeth strategy - no beta estimation.

    Process:
    1. Convert wide format → MultiIndex format
    2. Run cross-sectional regressions using linearmodels
    3. Compute Newey-West standard errors

    Use case: Modern momentum studies where variables are already meaningful
    """

    def __init__(
        self,
        newey_west_lags: int = 12,
        check_rank: bool = True,
        verbose: bool = True
    ):
        super().__init__(
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
        Fit Fama-MacBeth regression using direct method.

        Parameters
        ----------
        dependent : pd.DataFrame
            Dependent variable in wide format (date × security)
        independent : Dict[str, pd.DataFrame]
            Independent variables in wide format (date × security)

        Returns
        -------
        FMResults
            Regression results object
        """
        if self.verbose:
            print("Method: DIRECT (no beta estimation)")

        # Convert to MultiIndex format
        if self.verbose:
            print("Converting to MultiIndex format...")

        dependent_mi, independent_mi = convert_to_multiindex(
            dependent, independent
        )

        # Run cross-sectional regressions
        if self.verbose:
            print("Running cross-sectional regressions...")

        fm_result = self.cross_section_regressor.run_fama_macbeth(
            dependent=dependent_mi,
            independent=independent_mi
        )

        # Extract period-by-period gammas
        gamma_coeffs = self.cross_section_regressor.run_period_by_period(
            dependent=dependent_mi,
            independent=independent_mi
        )
        gamma_time_series = self.cross_section_regressor.extract_gamma_time_series(
            gamma_coeffs
        )

        # Package results
        result = create_results_from_fm(
            fm_result=fm_result,
            method='direct',
            gamma_time_series=gamma_time_series,
            betas=None,
            window=None,
            newey_west_lags=self.newey_west_lags
        )

        return result
