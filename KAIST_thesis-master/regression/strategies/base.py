"""
Abstract base class for regression strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

from ..cross_section import CrossSectionalRegressor


class RegressionStrategy(ABC):
    """
    Abstract base class for Fama-MacBeth regression strategies.

    Implements the Strategy pattern - different algorithms for the same interface.
    """

    def __init__(
        self,
        newey_west_lags: int = 12,
        check_rank: bool = True,
        verbose: bool = True
    ):
        """
        Initialize regression strategy.

        Parameters
        ----------
        newey_west_lags : int, default 12
            Number of lags for Newey-West standard errors
        check_rank : bool, default True
            Check for rank deficiency in cross-sectional regressions
        verbose : bool, default True
            Print progress messages
        """
        self.newey_west_lags = newey_west_lags
        self.verbose = verbose
        self.cross_section_regressor = CrossSectionalRegressor(
            newey_west_lags=newey_west_lags,
            check_rank=check_rank
        )

    @abstractmethod
    def fit(
        self,
        dependent: pd.DataFrame,
        independent: Dict[str, pd.DataFrame]
    ):
        """
        Fit the Fama-MacBeth regression.

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
        pass
