import datetime
import os
import logging
import pprint
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from factor_models.utils import compute_monthly_permno_filter, compute_residual_filter, fast_nan_to_num_3d


class FamaFrenchResidualModelDLAP:
    """
    Fama-French factor model for estimating residual portfolios.
    
    This class implements a Fama-French factor model to estimate residual portfolios.
    Fama-French factors used are market, size, value, profitability, investment, momentum, 
    long-term reversal, and short-term reversal. 
    
    The model may be estimated over a rolling window of daily data to predict the out-of-sample
    daily returns. The out-of-sample residuals may then be used as arbitrage portfolios. A 
    composition matrix gives the weights of the assets for each residual portfolio. The composition
    matrix includes the original Fama-French factors as assets, which can be approximated in practice 
    by appropriate ETFs. Consequently, there are slightly more assets than residuals for the 
    Fama-French residuals model.

    For DLAP dataset.
    """

    def __init__(
        self,
        output_dir: str,
        daily_returns_path: str,
        monthly_data_unnormalized_path: str,
        monthly_data_path: str,
        daily_fama_french_8_factors_path: str,
        monthly_data_returns_idx: int,
        monthly_data_market_cap_idx: int,
        debug: bool = False,
    ):
        """
        Initialize FamaFrench residuals model with required data paths.
        
        Args:
            output_dir (str): Directory for saving output files.
            daily_returns_path (str): Path to daily returns data file.
            monthly_data_unnormalized_path (str): Path to unnormalized monthly data.
            monthly_data_path (str): Path to normalized monthly data.
            daily_fama_french_8_factors_path (str): Path to Fama-French 8 factors data.
            monthly_data_returns_idx (int): Index of the returns column in the monthly data.
            monthly_data_market_cap_idx (int): Index of the market capitalization column in the monthly data.

        Returns:
            Initialized FamaFrenchResidualModelDLAP instance.
        """
        logging.info("Initializing Fama-French residual model")
        
        self.output_dir = output_dir
        self.debug = debug
        
        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)

        logging.info("Loading data")
        self.monthly_data_unnormalized = np.load(monthly_data_unnormalized_path, allow_pickle=True)['data']
        self.monthly_market_caps = np.nan_to_num(self.monthly_data_unnormalized[:,:,monthly_data_market_cap_idx])
        daily_data = np.load(daily_returns_path, allow_pickle=True)
        monthly_data = np.load(monthly_data_path, allow_pickle=True)
        self.monthly_data = monthly_data['data']
        self.daily_data = daily_data['data']
        self.daily_dates = pd.to_datetime(daily_data['date'], format='%Y%m%d')
        self.monthly_dates = pd.to_datetime(monthly_data['date'], format='%Y%m%d')
        self.daily_ff_factors = pd.read_csv(daily_fama_french_8_factors_path, index_col=0) / 100
        self.monthly_data_returns_idx = monthly_data_returns_idx
        self.monthly_data_market_cap_idx = monthly_data_market_cap_idx
        logging.info("Loaded data")

    def estimate_daily_oos_residuals(
        self,
        save: bool,
        initial_oos_year: int,
        size_window: int,
        cap_proportion: float,
        num_factors_list: List[int],
        save_comp_mtx: bool = True,
    ):
        """
        Estimate out-of-sample residuals using a rolling window.
        
        Args:
            save (bool): Save the residuals and composition matrix.
            initial_oos_year (int): Initial out-of-sample year.
            size_window (int): Size of the factor estimation rolling lookback window.
            cap_proportion (float): Proportion of market cap to use for asset filter.
            num_factors_list (List[int]): List of number of factors to estimate.
            save_comp_mtx (bool): Save the composition matrix, overrides `save`.
            
        Returns:
            None. Saves the residuals and composition matrix if specified.
        """
        logging.info(f"==> Beginning Fama-French daily OOS rolling window estimation. Called with args: \n{pprint.pformat(locals())}")
        
        rets_daily = self.daily_data.copy()
        T, N = rets_daily.shape
        logging.info(f"Daily returns shape: T {T}, N {N}")
        
        # Prepare dates and initial indices
        logging.info("Processing daily returns")
        first_oos_daily_idx = np.argmax(self.daily_dates.year >= initial_oos_year)
        self.first_oos_daily_idx = first_oos_daily_idx
        first_oos_monthly_idx = np.argmax(self.monthly_dates.year >= initial_oos_year)
        self.first_oos_monthly_idx = first_oos_monthly_idx
        oos_daily_dates = self.daily_dates[first_oos_daily_idx:]
        self.oos_daily_dates = oos_daily_dates
        first_oos_ff_daily_idx = np.argmax(self.daily_ff_factors.index >= initial_oos_year * 10_000)
        self.first_oos_ff_daily_idx = first_oos_ff_daily_idx
        logging.info(f"First OOS daily index={first_oos_daily_idx}; date={self.daily_dates[first_oos_daily_idx]}")
        
        monthly_mask = compute_monthly_permno_filter(
            self.monthly_data_unnormalized, 
            self.monthly_data[:,:,self.monthly_data_returns_idx], 
            cap_proportion, 
            self.monthly_data_market_cap_idx,
            use_market_cap_filter=True,
            use_non_nan_chars_filter=True,
            use_non_nan_return_filter=True,
        )
        self.monthly_mask = monthly_mask

        logging.info("Estimating residuals")
        for n_factors in num_factors_list:
            logging.info(f"==> Estimating residuals for cap={cap_proportion} factor={n_factors}")
            
            # Select assets with sufficient data to produce the assets to consider filter (contains all assets we'll consider for training)
            try:
                training_data_filename = (
                    f"DailyFamaFrench_OOSresiduals_{n_factors}_factors"
                    f"_{initial_oos_year}_initialOOSYear"
                    f"_{size_window}_rollingWindow"
                    f"_{cap_proportion}_Cap"
                    f".npy"
                )
                training_data_filepath = os.path.join(self.output_dir, training_data_filename)
                training_data = np.load(training_data_filepath)
                logging.info(f"Loaded data from '{training_data_filepath}'")
                logging.info("Further filtering data for future policy training/backtest")
                assets_to_consider = compute_residual_filter(training_data)
            except FileNotFoundError:
                logging.info("Computing filter for assets to consider")
                assets_to_consider = np.count_nonzero(monthly_mask[first_oos_monthly_idx-1:], axis=0) >= 1
                logging.debug("Optionally, to further reduce dimensionality of composition matrix for policy training/backtest, run this function again")
            N_tilde = np.sum(assets_to_consider)
            logging.info(f"Total assets: {N}, Selected assets: {N_tilde}")
            self.assets_to_consider = assets_to_consider

            residuals_oos = np.zeros((T - first_oos_daily_idx, N), dtype=float)
            comp_mtx_oos = np.zeros((T - first_oos_daily_idx, N_tilde, N_tilde + n_factors), dtype=np.float32)
            not_missing_oos = np.zeros((T - first_oos_daily_idx), dtype=float)
            idxs_selected_all = np.zeros((T - first_oos_daily_idx, N), dtype=bool)
            monthly_idx = first_oos_monthly_idx - 2  # ensures monthly mask is always backward-looking

            for t in range(T - first_oos_daily_idx):
                if self.daily_dates[first_oos_daily_idx + t - 1].month != self.daily_dates[first_oos_daily_idx + t].month:
                    monthly_idx += 1
                
                # Select only permnos which were tradeable last month and have all non-missing values in the past size_window days
                idxs_not_missing_values = ~np.any(np.isnan(rets_daily[(first_oos_daily_idx + t - size_window):(first_oos_daily_idx + t),:]), axis=0).ravel()
                idxs_selected = idxs_not_missing_values & monthly_mask[monthly_idx,:]  # (N,)
                not_missing_oos[t] = np.sum(idxs_not_missing_values)
                idxs_selected_all[t,:] = idxs_selected

                if t % 100 == 0:
                    logging.info("At date %s", oos_daily_dates[t])
                
                if n_factors == 0:
                    residuals_oos[t:(t+1), idxs_selected] = rets_daily[(first_oos_daily_idx + t):(first_oos_daily_idx + t + 1), idxs_selected]
                    comp_mtx_oos[t:(t+1), :, :N_tilde] = np.diag(idxs_selected[assets_to_consider])
                else:
                    Y = rets_daily[(first_oos_daily_idx + t - size_window):(first_oos_daily_idx + t), idxs_selected]
                    X = self.daily_ff_factors.values[(first_oos_ff_daily_idx + t - size_window):(first_oos_ff_daily_idx + t), :n_factors]
                    regr = LinearRegression(fit_intercept=False, n_jobs=1).fit(X, Y)
                    loadings = regr.coef_.T  # (nFactors x N)
                    
                    oos_returns = rets_daily[(first_oos_daily_idx + t):(first_oos_daily_idx + t + 1), idxs_selected]
                    factors = self.daily_ff_factors.values[(first_oos_ff_daily_idx + t):(first_oos_ff_daily_idx + t + 1), :n_factors]  # (T x nFactors)
                    residuals = oos_returns - factors.dot(loadings)
                    residuals_oos[t:(t+1), idxs_selected] = np.nan_to_num(residuals, copy=False)
                    
                    loadings_all = np.zeros((N, n_factors))
                    loadings_all[idxs_selected] = -loadings.T
                    comp_mtx_oos[t, :, :N_tilde] = np.diag(idxs_selected[assets_to_consider])
                    # idxs_selected is by definition always a subset of assets_to_consider
                    comp_mtx_oos[t, :, N_tilde:] = np.nan_to_num(loadings_all[assets_to_consider], copy=False)
            
            np.nan_to_num(residuals_oos, copy=False)

            self.residuals_oos = residuals_oos
            self.comp_mtx_oos = comp_mtx_oos
            self.not_missing_oos = not_missing_oos
            self.idxs_selected_all = idxs_selected_all
            
            if save:
                logging.info("Saving asset filter of shape %s", assets_to_consider.shape)
                assets_to_consider_filename = f"assets-to-consider_{initial_oos_year}_initialOOSYear_{cap_proportion}_Cap.npy"
                np.save(os.path.join(self.output_dir, assets_to_consider_filename), assets_to_consider)
                logging.info("Asset filter saved")

                logging.info(f"Saving idxs selected of shape {idxs_selected_all.shape}")
                idxs_selected_filename = f"DailyFamaFrench_idxs-selected-all_{n_factors}_factors_{initial_oos_year}_initialOOSYear_{size_window}_rollingWindow_{cap_proportion}_Cap.npy"
                np.save(os.path.join(self.output_dir, idxs_selected_filename), idxs_selected_all)
                logging.info("Idxs selected saved")

                logging.info(f"Saving residuals of shape {residuals_oos.shape}")
                residuals_filename = f"DailyFamaFrench_OOSresiduals_{n_factors}_factors_{initial_oos_year}_initialOOSYear_{size_window}_rollingWindow_{cap_proportion}_Cap.npy"
                np.save(os.path.join(self.output_dir, residuals_filename), residuals_oos)
                logging.info("Residuals saved")
                
                if save_comp_mtx:
                    logging.info(f"Saving composition matrix of shape {comp_mtx_oos.shape}")
                    comp_mtx_filename = f"DailyFamaFrench_OOSMatrixresiduals_{n_factors}_factors_{initial_oos_year}_initialOOSYear_{size_window}_rollingWindow_{cap_proportion}_Cap.npy"
                    np.save(os.path.join(self.output_dir, comp_mtx_filename), comp_mtx_oos)
                    logging.info("Composition matrix saved")
                
                logging.info("Results saved")

            logging.info(f"==> Finished Fama-French residual estimation for: cap={cap_proportion}, factor={n_factors}")
        return