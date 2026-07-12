"""
Results container for Fama-MacBeth regressions.

Stores and provides access to:
- Step 1 beta estimates (if two_step or hybrid method)
- Step 2 gamma coefficients (time-series and average)
- Statistical inference (t-stats, p-values, confidence intervals)
- Diagnostics and metadata
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from linearmodels.panel.results import FamaMacBethResults


@dataclass
class FMResults:
    """
    Container for Fama-MacBeth regression results.

    Attributes:
    -----------
    method : str
        Regression method: 'two_step', 'hybrid', or 'direct'

    ## Step 2 Results (Always Present)
    params : pd.Series
        Time-series average of gamma coefficients
    tstats : pd.Series
        t-statistics (Newey-West SE)
    pvalues : pd.Series
        Two-sided p-values
    std_errors : pd.Series
        Newey-West standard errors
    conf_int : pd.DataFrame
        95% confidence intervals (variables × [lower, upper])

    gamma_time_series : pd.DataFrame
        Period-by-period gamma estimates (date × variables)
        Useful for diagnostics and plotting

    ## Step 1 Results (Only for two_step/hybrid)
    betas : dict, optional
        {factor_name: pd.DataFrame (date × security)}
        Rolling beta estimates from Step 1

    ## Diagnostics
    n_obs : int
        Number of observations used
    n_periods : int
        Number of time periods
    n_securities : int
        Number of securities
    n_variables : int
        Number of independent variables

    ## Metadata
    window : int, optional
        Rolling window size used in Step 1
    newey_west_lags : int
        Lags used for Newey-West SE
    r_squared : float, optional
        Average R-squared across periods (if available)

    ## Raw linearmodels Results
    _fm_result : FamaMacBethResults, optional
        Raw results object from linearmodels for advanced access
    """

    method: str

    # Step 2 results (gamma coefficients)
    params: pd.Series
    tstats: pd.Series
    pvalues: pd.Series
    std_errors: pd.Series
    conf_int: pd.DataFrame
    gamma_time_series: pd.DataFrame

    # Step 1 results (betas)
    betas: Optional[Dict[str, pd.DataFrame]] = None

    # Diagnostics
    n_obs: int = 0
    n_periods: int = 0
    n_securities: int = 0
    n_variables: int = 0

    # Metadata
    window: Optional[int] = None
    newey_west_lags: int = 2
    r_squared: Optional[float] = None

    # Raw results
    _fm_result: Optional[FamaMacBethResults] = None

    def __post_init__(self):
        """Validate that method is valid."""
        valid_methods = ['two_step', 'hybrid', 'direct']
        if self.method not in valid_methods:
            raise ValueError(
                f"method must be one of {valid_methods}, got '{self.method}'"
            )

        if self.method in ['two_step', 'hybrid'] and self.betas is None:
            raise ValueError(
                f"betas must be provided for method='{self.method}'"
            )

    def summary(self, alpha: float = 0.05) -> pd.DataFrame:
        """
        Generate summary table of regression results.

        Parameters:
        -----------
        alpha : float
            Significance level for confidence intervals (default: 0.05 for 95% CI)

        Returns:
        --------
        summary : pd.DataFrame
            Table with columns: coef, std_err, t_stat, p_value, ci_lower, ci_upper, sig
        """
        summary_df = pd.DataFrame({
            'coef': self.params,
            'std_err': self.std_errors,
            't_stat': self.tstats,
            'p_value': self.pvalues,
            'ci_lower': self.conf_int.iloc[:, 0],
            'ci_upper': self.conf_int.iloc[:, 1]
        })

        # Add significance stars
        summary_df['sig'] = ''
        summary_df.loc[summary_df['p_value'] < 0.001, 'sig'] = '***'
        summary_df.loc[(summary_df['p_value'] >= 0.001) & (summary_df['p_value'] < 0.01), 'sig'] = '**'
        summary_df.loc[(summary_df['p_value'] >= 0.01) & (summary_df['p_value'] < 0.05), 'sig'] = '*'

        return summary_df

    def print_summary(self, alpha: float = 0.05):
        """
        Pretty-print regression results.

        Parameters:
        -----------
        alpha : float
            Significance level
        """
        print("=" * 70)
        print("FAMA-MACBETH REGRESSION RESULTS")
        print("=" * 70)
        print(f"Method: {self.method}")
        print(f"Observations: {self.n_obs:,}")
        print(f"Time periods: {self.n_periods}")
        print(f"Securities: {self.n_securities}")
        print(f"Variables: {self.n_variables}")

        if self.window is not None:
            print(f"Rolling window (Step 1): {self.window}")

        print(f"Newey-West lags: {self.newey_west_lags}")

        if self.r_squared is not None:
            print(f"Average R-squared: {self.r_squared:.4f}")

        print("\n" + "-" * 70)
        print("COEFFICIENTS")
        print("-" * 70)

        summary = self.summary(alpha=alpha)

        # Format for display
        for var in summary.index:
            row = summary.loc[var]
            print(f"{var:20s}  {row['coef']:8.4f}  "
                  f"({row['std_err']:6.4f})  "
                  f"t={row['t_stat']:6.2f}  "
                  f"p={row['p_value']:6.4f}  {row['sig']}")

        print("-" * 70)
        print("Significance: *** p<0.001, ** p<0.01, * p<0.05")
        print("=" * 70)

    def get_significant_variables(self, alpha: float = 0.05) -> List[str]:
        """
        Get list of statistically significant variables.

        Parameters:
        -----------
        alpha : float
            Significance level

        Returns:
        --------
        significant_vars : list
            Variable names with p-value < alpha
        """
        return self.pvalues[self.pvalues < alpha].index.tolist()

    def get_beta(self, factor_name: str) -> Optional[pd.DataFrame]:
        """
        Get beta estimates for a specific factor.

        Parameters:
        -----------
        factor_name : str
            Name of factor (e.g., 'tnic_ret')

        Returns:
        --------
        beta_df : pd.DataFrame or None
            Beta estimates (date × security) if available
        """
        if self.betas is None:
            return None

        return self.betas.get(factor_name)

    def get_gamma(self, variable_name: str) -> pd.Series:
        """
        Get gamma time series for a specific variable.

        Parameters:
        -----------
        variable_name : str
            Variable name

        Returns:
        --------
        gamma_series : pd.Series
            Time series of gamma estimates
        """
        if variable_name not in self.gamma_time_series.columns:
            raise ValueError(
                f"Variable '{variable_name}' not found. "
                f"Available: {list(self.gamma_time_series.columns)}"
            )

        return self.gamma_time_series[variable_name]

    def plot_gammas(
        self,
        variables: Optional[List[str]] = None,
        figsize: tuple = (12, 6),
        title: Optional[str] = None
    ):
        """
        Plot gamma time series for selected variables.

        Parameters:
        -----------
        variables : list, optional
            Variables to plot (default: all)
        figsize : tuple
            Figure size
        title : str, optional
            Plot title

        Returns:
        --------
        fig, ax : matplotlib Figure and Axes
        """
        import matplotlib.pyplot as plt

        if variables is None:
            variables = self.gamma_time_series.columns.tolist()

        fig, ax = plt.subplots(figsize=figsize)

        for var in variables:
            gamma_series = self.gamma_time_series[var]
            ax.plot(gamma_series.index, gamma_series.values, label=var, marker='o', alpha=0.7)

        ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        ax.set_xlabel('Date')
        ax.set_ylabel('Gamma Coefficient')
        ax.legend()
        ax.grid(True, alpha=0.3)

        if title:
            ax.set_title(title)
        else:
            ax.set_title(f'Fama-MacBeth Gamma Time Series ({self.method})')

        plt.tight_layout()
        return fig, ax

    def to_dict(self) -> Dict:
        """
        Convert results to dictionary for serialization.

        Returns:
        --------
        results_dict : dict
            All results in dictionary format
        """
        results_dict = {
            'method': self.method,
            'params': self.params.to_dict(),
            'tstats': self.tstats.to_dict(),
            'pvalues': self.pvalues.to_dict(),
            'std_errors': self.std_errors.to_dict(),
            'conf_int': self.conf_int.to_dict(),
            'gamma_time_series': self.gamma_time_series.to_dict(),
            'diagnostics': {
                'n_obs': self.n_obs,
                'n_periods': self.n_periods,
                'n_securities': self.n_securities,
                'n_variables': self.n_variables
            },
            'metadata': {
                'window': self.window,
                'newey_west_lags': self.newey_west_lags,
                'r_squared': self.r_squared
            }
        }

        if self.betas is not None:
            results_dict['betas'] = {
                factor: beta_df.to_dict()
                for factor, beta_df in self.betas.items()
            }

        return results_dict

    def save(self, filepath: str):
        """
        Save results to pickle file.

        Parameters:
        -----------
        filepath : str
            Path to save results (e.g., 'results.pkl')
        """
        import pickle

        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str) -> 'FMResults':
        """
        Load results from pickle file.

        Parameters:
        -----------
        filepath : str
            Path to pickled results

        Returns:
        --------
        results : FMResults
            Loaded results object
        """
        import pickle

        with open(filepath, 'rb') as f:
            return pickle.load(f)


def create_results_from_fm(
    fm_result: FamaMacBethResults,
    method: str,
    gamma_time_series: pd.DataFrame,
    betas: Optional[Dict[str, pd.DataFrame]] = None,
    window: Optional[int] = None,
    newey_west_lags: int = 2
) -> FMResults:
    """
    Create FMResults object from linearmodels FamaMacBeth result.

    Parameters:
    -----------
    fm_result : FamaMacBethResults
        Result from linearmodels.panel.FamaMacBeth
    method : str
        Regression method used
    gamma_time_series : pd.DataFrame
        Period-by-period gamma estimates
    betas : dict, optional
        Beta estimates from Step 1
    window : int, optional
        Rolling window size
    newey_west_lags : int
        Newey-West lags used

    Returns:
    --------
    results : FMResults
        Structured results object
    """
    # Extract statistics from linearmodels result
    params = fm_result.params
    tstats = fm_result.tstats
    pvalues = fm_result.pvalues
    std_errors = fm_result.std_errors
    conf_int = fm_result.conf_int()

    # Extract diagnostics
    n_obs = fm_result.nobs
    n_periods = len(gamma_time_series)
    n_securities = n_obs // n_periods if n_periods > 0 else 0
    n_variables = len(params)

    # Extract R-squared if available
    r_squared = getattr(fm_result, 'rsquared', None)

    return FMResults(
        method=method,
        params=params,
        tstats=tstats,
        pvalues=pvalues,
        std_errors=std_errors,
        conf_int=conf_int,
        gamma_time_series=gamma_time_series,
        betas=betas,
        n_obs=n_obs,
        n_periods=n_periods,
        n_securities=n_securities,
        n_variables=n_variables,
        window=window,
        newey_west_lags=newey_west_lags,
        r_squared=r_squared,
        _fm_result=fm_result
    )
