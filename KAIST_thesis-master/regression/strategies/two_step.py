"""
Two-step strategy for Fama-MacBeth regression.

Implements the original Fama-MacBeth (1973) procedure:
Step 1: Estimate rolling betas for all variables
Step 2: Run cross-sectional regressions on estimated betas

Appropriate for traditional risk factor analysis.
"""

from typing import Dict
import pandas as pd

from .base import RegressionStrategy
from ..preprocessing import convert_to_multiindex
from ..rolling_beta import RollingBetaEstimator
from ..results import create_results_from_fm, FMResults


class TwoStepStrategy(RegressionStrategy):
    """
    Two-step Fama-MacBeth strategy with beta estimation.

    Process:
    1. Estimate rolling betas for ALL variables using time-series regressions
    2. Use estimated betas as independent variables in cross-sectional regressions
    3. Time-series average of coefficients with Newey-West standard errors

    Use case: Traditional CAPM/factor models where you want to estimate risk loadings
    """

    def __init__(
        self,
        window: int = 60,
        newey_west_lags: int = 12,
        check_rank: bool = True,
        verbose: bool = True
    ):
        """
        Initialize two-step strategy.

        Parameters
        ----------
        window : int, default 60
            Rolling window for beta estimation (in periods)
        newey_west_lags : int, default 12
            Number of lags for Newey-West standard errors
        check_rank : bool, default True
            Check for rank deficiency in cross-sectional regressions
        verbose : bool, default True
            Print progress messages
        """
        super().__init__(
            newey_west_lags=newey_west_lags,
            check_rank=check_rank,
            verbose=verbose
        )
        self.window = window
        self.beta_estimator = RollingBetaEstimator(window=window)

    def fit(
        self,
        dependent: pd.DataFrame,
        independent: Dict[str, pd.DataFrame]
    ) -> FMResults:
        """
        Fit Fama-MacBeth regression using two-step method.

        Parameters
        ----------
        dependent : pd.DataFrame
            Dependent variable in wide format (date × security)
        independent : Dict[str, pd.DataFrame]
            Independent variables in wide format (date × security)

        Returns
        -------
        FMResults
            Regression results object with estimated betas
        """
        if self.verbose:
            print("Method: TWO-STEP (all variables through beta estimation)")

        # Step 1: Estimate betas for ALL variables
        if self.verbose:
            print(f"Step 1: Estimating rolling betas (window={self.window})...")

        betas, alphas = self.beta_estimator.estimate_betas_with_constant(
            dependent=dependent,
            factors=independent
        )

        # Step 2: Use betas as independent variables in cross-section
        if self.verbose:
            print("Step 2: Running cross-sectional regressions on betas...")

        # Align dependent with betas (betas have NaN for first window-1 periods)
        # Find dates with valid beta estimates
        first_beta_df = list(betas.values())[0]
        valid_dates = first_beta_df.dropna(how='all').index

        # Subset dependent to matching dates
        dependent_aligned = dependent.loc[valid_dates]

        # Subset betas to matching dates
        betas_aligned = {k: v.loc[valid_dates] for k, v in betas.items()}

        # Convert to MultiIndex
        dependent_mi, betas_mi = convert_to_multiindex(dependent_aligned, betas_aligned)

        # Run cross-sectional regressions
        fm_result = self.cross_section_regressor.run_fama_macbeth(
            dependent=dependent_mi,
            independent=betas_mi
        )

        # Extract period-by-period gammas
        gamma_coeffs = self.cross_section_regressor.run_period_by_period(
            dependent=dependent_mi,
            independent=betas_mi
        )
        gamma_time_series = self.cross_section_regressor.extract_gamma_time_series(
            gamma_coeffs
        )

        # Package results
        result = create_results_from_fm(
            fm_result=fm_result,
            method='two_step',
            gamma_time_series=gamma_time_series,
            betas=betas,  # Store estimated betas
            window=self.window,
            newey_west_lags=self.newey_west_lags
        )

        return result
