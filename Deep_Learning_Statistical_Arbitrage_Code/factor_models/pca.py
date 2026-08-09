import datetime
import logging
import os
import pprint
from typing import List

import numpy as np
import scipy.linalg
import pandas as pd
from sklearn.linear_model import LinearRegression

from factor_models.utils import compute_monthly_permno_filter, compute_residual_filter


class PCAResidualModelDLAP:
    """
    PCA factor model for estimating residual portfolios.
    
    This class implements a PCA factor model to estimate residual portfolios.
    A varying number of PCA factors may be used.
    
    The model may be estimated over a rolling window of daily data to predict the out-of-sample
    daily returns. The out-of-sample residuals may then be used as arbitrage portfolios. A 
    composition matrix gives the weights of the assets for each residual portfolio. For PCA, the 
    number of residuals estimated is the same as the number of assets, as each asset is residualized 
    by subtracting the projected returns on the factors.

    For DLAP dataset.
    """

    def __init__(
        self,
        output_dir: str,
        path_daily_data: str,
        path_monthly_data_unnormalized: str,
        path_monthly_data: str,
        monthly_data_returns_idx: int,
        monthly_data_market_cap_idx: int,
        debug: bool = False,
    ):
        """
        Initialize the PCA model with required data.
        
        Args:
            output_dir (str): Output directory.
            path_daily_data (str): Path to daily data.
            path_monthly_data_unnormalized (str): Path to unnormalized monthly data.
            path_monthly_data (str): Path to normalized monthly data.
            monthly_data_returns_idx (int): Index of monthly returns in monthly data.
            monthly_data_market_cap_idx (int): Index of monthly market cap in monthly data.
            debug (bool): Debug mode, print more output and diagnostics.
            
        Returns:
            Initialized PCAResidualModelDLAP object.
        """
        logging.info(f"Initializing PCA residual model; called with args \n{pprint.pformat(locals())}")

        self.output_dir = output_dir
        self.debug = debug

        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)
        
        logging.info("Loading data")
        self.monthly_data_unnormalized = np.load(path_monthly_data_unnormalized, allow_pickle=True)['data']
        self.monthly_market_caps = np.nan_to_num(self.monthly_data_unnormalized[:,:,monthly_data_market_cap_idx])
        daily_data = np.load(path_daily_data, allow_pickle=True)
        monthly_data = np.load(path_monthly_data, allow_pickle=True)
        self.monthly_data = monthly_data['data']
        self.daily_data = daily_data['data']
        self.daily_dates = pd.to_datetime(daily_data['date'], format='%Y%m%d')
        self.monthly_dates = pd.to_datetime(monthly_data['date'], format='%Y%m%d')
        self.monthly_data_returns_idx = monthly_data_returns_idx  
        self.monthly_data_market_cap_idx = monthly_data_market_cap_idx
        logging.info("Data loaded")
    
    def estimate_daily_oos_residuals(
        self,
        save: bool,
        initial_oos_year: int,
        size_window: int,
        size_covariance_window: int,
        cap_proportion: float,
        num_factors_list: List[int],
        save_comp_mtx: bool = True,
    ):
        """
        Estimate daily out-of-sample residuals using PCA.

        Args:
            save (bool): Save the residuals and composition matrix.
            initial_oos_year (int): Initial out-of-sample year.
            size_window (int): Size of the factor estimation rolling lookback window.
            size_covariance_window (int): Size of the covariance matrix estimation rolling lookback window.
            cap_proportion (float): Proportion of market cap to use for asset filter.
            num_factors_list (List[int]): List of number of factors to estimate.
            save_comp_mtx (bool): Save the composition matrix, overrides `save`.

        Returns:
            None. Saves the residuals and composition matrix if specified.
        """
        logging.info(f"==> Beginning PCA daily OOS rolling window estimation. Called with args: \n{pprint.pformat(locals())}")
        
        rets_daily = self.daily_data.copy()
        # rets_daily = rdaily[first_oos_daily_idx:,:]
        T, N = self.daily_data.shape
        logging.info(f"Daily returns shape: T {T}, N {N}")
        
        # Prepare dates and initial indices
        logging.info("Processing daily returns")
        first_oos_daily_idx = np.argmax(self.daily_dates.year >= initial_oos_year)
        self.first_oos_daily_idx = first_oos_daily_idx
        first_oos_monthly_idx = np.argmax(self.monthly_dates.year >= initial_oos_year)
        self.first_oos_monthly_idx = first_oos_monthly_idx
        oos_daily_dates = self.daily_dates[first_oos_daily_idx:]
        self.oos_daily_dates = oos_daily_dates
        logging.info(f"First OOS daily index={first_oos_daily_idx}; date={self.daily_dates[first_oos_daily_idx]}")

        logging.info("Computing filter for assets to consider")
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
        # NOTE: runtime can be significantly improved by computing all factors at once in each time step instead of iterating over factors
        for n_factors in num_factors_list:
            logging.info(f"==> Estimating residuals for cap={cap_proportion} factor={n_factors}")

            rets_daily = self.daily_data.copy()

            # Select assets with sufficient data to produce the assets to consider filter (contains all assets we'll consider for training)
            load_filter = True
            try:
                training_data_filename = (
                    f"AvPCA_OOSresiduals_{n_factors}_factors"
                    f"_{initial_oos_year}_initialOOSYear"
                    f"_{size_window}_rollingWindow"
                    f"_{size_covariance_window}_covWindow"
                    f"_{cap_proportion}_Cap"
                    ".npy"
                )
                training_data_filepath = os.path.join(self.output_dir, training_data_filename)
                training_data = np.load(training_data_filepath)
                logging.info(f"Loaded data from '{training_data_filepath}'")
                logging.info("Further filtering data for future policy training/backtest")
                assets_to_consider = compute_residual_filter(training_data)
            except FileNotFoundError:
                logging.info("Computing filter for assets to consider")
                assets_to_consider = np.count_nonzero(monthly_mask[first_oos_monthly_idx-1:], axis=0) >= 1
                load_filter = False
                logging.debug("Optionally, to further reduce dimensionality of composition matrix for policy training, run this function again")
            N_tilde = np.sum(assets_to_consider)
            logging.info(f"Total assets: {N}, Selected assets: {N_tilde}")
            self.assets_to_consider = assets_to_consider

            residuals_oos = np.zeros((T - first_oos_daily_idx, N), dtype=float)
            comp_mtx_oos = np.zeros((T - first_oos_daily_idx, N_tilde, N_tilde), dtype=np.float32)
            idxs_selected_all = np.zeros((T - first_oos_daily_idx, N), dtype=bool)
            monthly_idx = first_oos_monthly_idx - 2
            
            for t in range(T - first_oos_daily_idx):
                if self.daily_dates[first_oos_daily_idx+t-1].month != self.daily_dates[first_oos_daily_idx+t].month:
                    monthly_idx += 1
                
                if load_filter:
                    idxs_not_missing_values = ~np.any(np.isnan(rets_daily[(first_oos_daily_idx + t - size_window):(first_oos_daily_idx + t),:]), axis=0).ravel()
                    if t < 30:
                        idxs_selected = idxs_not_missing_values & monthly_mask[monthly_idx,:] & (np.count_nonzero(training_data[:t,:], axis=0) >= t)
                    else:
                        idxs_selected = idxs_not_missing_values & monthly_mask[monthly_idx,:] & (np.count_nonzero(training_data[:t,:], axis=0) >= 30)
                else:
                    idxs_not_missing_values = ~np.any(np.isnan(rets_daily[(first_oos_daily_idx + t - size_window):(first_oos_daily_idx + t),:]), axis=0).ravel()
                    idxs_selected = idxs_not_missing_values & monthly_mask[monthly_idx,:]
                    idxs_selected_all[t,:] = idxs_selected
                
                if n_factors == 0:
                    residuals_oos[t:(t+1),idxs_selected] = np.nan_to_num(rets_daily[(first_oos_daily_idx+t):(first_oos_daily_idx+t+1),idxs_selected])
                    comp_mtx_oos[t:(t+1),:,:] = np.diag(idxs_selected[assets_to_consider])
                else:
                    rets_cov_window = np.nan_to_num(rets_daily[(first_oos_daily_idx+t-size_covariance_window+1):(first_oos_daily_idx+t+1),idxs_selected])
                    rets_mean = np.mean(rets_cov_window, axis=0, keepdims=True)
                    rets_vol = np.sqrt(np.mean((rets_cov_window-rets_mean)**2, axis=0, keepdims=True))
                    rets_cov_window_normalized = (rets_cov_window - rets_mean) / rets_vol
                    corr = np.dot(rets_cov_window_normalized.T, rets_cov_window_normalized)
                    eigenvalues, eigenvectors = scipy.linalg.eigh(corr, subset_by_index=(corr.shape[0] - n_factors, corr.shape[0] - 1))
                    idxs = np.argsort(-eigenvalues)
                    loadings = eigenvectors.real[:, idxs]
                    factors = np.dot(rets_cov_window[-size_window:, :] / rets_vol, loadings)
                    day_factors = np.dot(np.nan_to_num(rets_daily[first_oos_daily_idx+t, idxs_selected]) / rets_vol, loadings) 
                    old_loadings = loadings
                    regr = LinearRegression(fit_intercept=False, n_jobs=1).fit(factors, rets_cov_window[-size_window:,:])
                    loadings = regr.coef_
                    residuals = np.nan_to_num(rets_daily[first_oos_daily_idx+t, idxs_selected]) - day_factors.dot(loadings.T)
                    residuals_oos[t:(t+1),idxs_selected] = np.nan_to_num(residuals)
                    n_prime = len(rets_cov_window[-1:, :].ravel())
                    matrix_full = np.zeros((N, N))
                    matrix_reduced = np.eye(n_prime) - np.diag(1 / rets_vol.squeeze()) @ old_loadings @ loadings.T
                    idxs_selected_full = idxs_selected.reshape((N,1)) @ idxs_selected.reshape((1,N))
                    matrix_full[idxs_selected_full] = matrix_reduced.ravel()
                    comp_mtx_oos[t:(t+1)] = matrix_full[assets_to_consider][:,assets_to_consider].T 

                    if np.isnan(residuals_oos).any():
                        logging.warning("===> NaNs found in residuals")
                if t % 50 == 0:
                    logging.info(f"At date {t}/{T-first_oos_daily_idx}") 
            
            nan_ct_resid = np.isnan(residuals_oos).sum()
            logging.info(f"Number of NaNs in residuals: {nan_ct_resid}")
            assert nan_ct_resid == 0, "NaNs found in residuals"
            np.nan_to_num(residuals_oos, copy=False)

            self.residuals_oos = residuals_oos
            self.comp_mtx_oos = comp_mtx_oos
            self.idxs_selected_all = idxs_selected_all
            
            if save:
                logging.info("Saving asset filter of shape %s", assets_to_consider.shape)
                assets_to_consider_filepath = os.path.join(self.output_dir, f"assets-to-consider_{initial_oos_year}_initialOOSYear_{cap_proportion}_Cap.npy")
                np.save(assets_to_consider_filepath, assets_to_consider)
                logging.info("Asset filter saved")

                logging.info(f"Saving idxs selected of shape {idxs_selected_all.shape}")
                idxs_selected_all_filepath = os.path.join(self.output_dir, 
                    f"AvPCA_idxs-selected-all"
                    f"_{n_factors}_factors"
                    f"_{initial_oos_year}_initialOOSYear"
                    f"_{size_window}_rollingWindow"
                    f"_{size_covariance_window}_covWindow"
                    f"_{cap_proportion}_Cap"
                    ".npy"
                )
                np.save(idxs_selected_all_filepath, idxs_selected_all)
                logging.info("Idxs selected saved") 

                logging.info(f"Saving residuals of shape {residuals_oos.shape}")
                residuals_filepath = os.path.join(self.output_dir, 
                    f"AvPCA_OOSresiduals"
                    f"_{n_factors}_factors"
                    f"_{initial_oos_year}_initialOOSYear"
                    f"_{size_window}_rollingWindow"
                    f"_{size_covariance_window}_covWindow"
                    f"_{cap_proportion}_Cap"
                    ".npy"
                )
                np.save(residuals_filepath, residuals_oos)
                logging.info("Residuals saved")
                
                if save_comp_mtx:
                    logging.info(f"Saving composition matrix of shape {comp_mtx_oos.shape}")
                    comp_mtx_filepath = os.path.join(self.output_dir, 
                        f"AvPCA_OOSMatrixresiduals"
                        f"_{n_factors}_factors"
                        f"_{initial_oos_year}_initialOOSYear"
                        f"_{size_window}_rollingWindow"
                        f"_{size_covariance_window}_covWindow"
                        f"_{cap_proportion}_Cap"
                        ".npy"
                    )
                    np.save(comp_mtx_filepath, comp_mtx_oos)
                    logging.info("Composition matrix saved")
                else:
                    logging.info("Composition matrix not saved")
                
                logging.info("Results saved")

            logging.info(f"==> Finished PCA residual estimation for: cap={cap_proportion}, factor={n_factors}")
        return
    