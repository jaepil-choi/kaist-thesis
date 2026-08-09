import datetime
import logging
import os
import pprint
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from factor_models.utils import compute_monthly_permno_filter, compute_residual_filter


def get_sharpe_tangency_portfolio(returns: np.ndarray) -> float:
    """
    Returns the Sharpe ratio of the tangency portfolio given returns.

    Args:
        returns (np.ndarray): Returns of shape (T, N)

    Returns:
        float: Sharpe ratio
    """
    if returns.shape[1] == 1:
        return np.abs(np.mean(returns)) / np.std(returns)
    else:
        mean_ret = np.mean(returns, axis=0, keepdims=True)
        cov_ret = np.cov(returns.T)
        return float(np.sqrt(mean_ret @ np.linalg.solve(cov_ret, mean_ret.T)))


def get_tangency_portfolio(returns: np.ndarray) -> np.ndarray:
    """
    Returns the tangency portfolio weights given returns.

    Args:
        returns (np.ndarray): Returns of shape (T, N)

    Returns:
        np.ndarray: Weights of shape (N,)
    """
    if returns.shape[1] == 1:
        return 1
    else:
        mean_ret = np.mean(returns, axis=0, keepdims=True)
        cov_ret = np.cov(returns.T)
        weights = np.linalg.solve(cov_ret, mean_ret.T)
        return weights.T / np.sum(weights)


class IPCAResidualModelDLAP:
    """
    IPCA factor model for estimating residual portfolios.

    This class implements an IPCA factor model to estimate residual portfolios.
    A varying number of IPCA factors may be used.

    The model estimates a dimensionality reduction matrix for characteristics,
    Gamma, over a rolling window of monthly characteristics data. Gamma is used
    to estimate the relationship between factors and returns over a rolling window
    of daily data to predict the out-of-sample daily returns. The out-of-sample
    residuals may then be used as arbitrage portfolios. A composition matrix gives
    the weights of the assets for each residual portfolio.

    For DLAP dataset.
    """

    def __init__(
        self,
        output_dir: str,
        path_monthly_data: str,
        path_daily_data: str,
        path_monthly_data_unnormalized: str,
        num_characteristics: int,
        monthly_data_returns_idx: int,
        monthly_data_market_cap_idx: int,
        debug: bool,
    ):
        """
        Initializes the IPCA residual model with required data paths.

        Args:
            output_dir (str): Directory for saving output files.
            path_monthly_data (str): Path to monthly data file.
            path_daily_data (str): Path to daily data file.
            path_monthly_data_unnormalized (str): Path to unnormalized monthly data file.
            num_characteristics (int): Number of characteristics (denoted as L in the IPCA paper).
            monthly_data_returns_idx (int): Index of the returns column in monthly data.
            monthly_data_market_cap_idx (int): Index of the market capitalization column in monthly data.
            debug (bool): Flag to enable debugging mode.

        Returns:
            An instance of IPCAResidualModelDLAP.
        """
        logging.info(
            f"Initializing IPCA residual model; called with args \n{pprint.pformat(locals())}"
        )

        self.num_characteristics = num_characteristics
        self.output_dir = output_dir
        self.monthly_data_returns_idx = monthly_data_returns_idx
        self.monthly_data_market_cap_idx = monthly_data_market_cap_idx
        self.debug = debug

        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)

        logging.info("Loading data")
        monthly_data = np.load(path_monthly_data, allow_pickle=True)
        daily_data = np.load(path_daily_data, allow_pickle=True)
        self.monthly_data = monthly_data["data"]
        self.daily_data = daily_data["data"]
        self.monthly_data_unnormalized = np.load(
            path_monthly_data_unnormalized, allow_pickle=True
        )["data"]
        self.monthly_caps = np.nan_to_num(self.monthly_data_unnormalized[:, :, 19])

        self.daily_dates = pd.to_datetime(daily_data["date"], format="%Y%m%d")
        self.monthly_dates = pd.to_datetime(monthly_data["date"], format="%Y%m%d")
        self.weight_matrices = []
        self.monthly_mask = np.zeros(0)
        self.weighted = False
        logging.info("Data loaded")

    def step_factors(
        self, R_list, Z_list, Gamma, calculate_residual=False, start_idx=0
    ):
        """
        Estimates the factors using the provided returns and characteristics.

        In this function, I are the characteristics denoted as Z in the IPCA paper.

        Args:
            R_list (list): A list of return arrays for each time step.
            Z_list (list): A list of characteristic arrays for each time step.
            Gamma (ndarray): The factor loading matrix.
            calculate_residual (bool): Flag to calculate residuals if set to True.
            start_idx (int): The starting index for the calculations.

        Returns:
            A list of estimated factors for each time step and, if requested, the calculated residuals.
        """
        f_list = []
        if calculate_residual:
            residual_list = []
        for t, rzTuple in enumerate(zip(R_list, Z_list)):
            R_t, Z_t = rzTuple
            beta_t = Z_t.dot(Gamma)
            try:
                if self.weighted:
                    W_t = self.weight_matrices[t + start_idx]
                    A = beta_t.T @ W_t @ beta_t
                    f_t = np.linalg.solve(A, beta_t.T @ W_t @ R_t)
                else:
                    A = beta_t.T.dot(beta_t)
                    f_t = np.linalg.solve(A, beta_t.T.dot(R_t))
            except np.linalg.LinAlgError as err:
                logging.info(str(err))
                if self.weighted:
                    W_t = self.weight_matrices[t + start_idx]
                    f_t = np.linalg.pinv(beta_t.T @ W_t @ beta_t).dot(
                        beta_t.T @ W_t @ R_t
                    )
                else:
                    f_t = np.linalg.pinv(beta_t.T.dot(beta_t)).dot(beta_t.T.dot(R_t))
            f_list.append(f_t)
            if calculate_residual:
                residual_list.append(R_t - beta_t.dot(f_t))
        if calculate_residual:
            return f_list, residual_list
        else:
            return f_list, None

    def step_gamma(self, R_list, Z_list, f_list, n_factors, start_idx=0):
        """
        Estimates the gamma matrix using the provided returns, characteristics, and factors.

        This function constructs a system of equations to solve for the gamma matrix that relates
        the factors to the characteristics and returns. The solution is computed using either
        direct solving or pseudo-inversion in case of singularities.

        Args:
            R_list (list): A list of return arrays for each time step.
            Z_list (list): A list of characteristic arrays for each time step.
            f_list (list): A list of factor estimates for each time step.
            n_factors (int): The number of factors to estimate.
            start_idx (int): The starting index for the calculations.

        Returns:
            ndarray: The estimated gamma matrix reshaped to dimensions (num_characteristics, n_factors).
        """
        A = np.zeros(
            (self.num_characteristics * n_factors, self.num_characteristics * n_factors)
        )
        b = np.zeros((self.num_characteristics * n_factors, 1))
        for t, rzf_tuple in enumerate(zip(R_list, Z_list, f_list)):
            R_t, Z_t, f_t = rzf_tuple
            tmp_t = np.kron(Z_t, f_t.T)
            if self.weighted:
                W_t = self.weight_matrices[t + start_idx]
                A += tmp_t.T @ W_t @ tmp_t
                b += tmp_t.T @ W_t @ R_t
            else:
                A += tmp_t.T.dot(tmp_t)
                b += tmp_t.T.dot(R_t)
        try:
            Gamma = np.linalg.solve(A, b)
        except np.linalg.LinAlgError as err:
            logging.info(str(err))
            Gamma = np.linalg.pinv(A).dot(b)
        return Gamma.reshape((self.num_characteristics, n_factors))

    def initialize_gamma(self, R_list, Z_list, n_factors, start_idx=0):
        """
        Initialize the gamma matrix for the factor model.

        This function computes the initial gamma values based on the provided
        return lists (R_list) and characteristic lists (Z_list). It uses
        either weighted or unweighted calculations based on the 'weighted'
        attribute of the class. The estimated gamma matrix is derived from
        the eigenvectors of the covariance matrix of the returns and
        characteristics.

        Args:
            R_list (list): A list of return arrays for each time step.
            Z_list (list): A list of characteristic arrays for each time step.
            n_factors (int): The number of factors to estimate.
            start_idx (int): The starting index for the calculations (default is 0).

        Returns:
            ndarray: The estimated gamma matrix reshaped to dimensions
                      (num_characteristics, n_factors).
        """
        T = len(R_list)
        X = np.zeros((T, self.num_characteristics))
        for t in range(T):
            if self.weighted:
                W_t = self.weight_matrices[t + start_idx]
                X[t, :] = np.squeeze(Z_list[t].T @ W_t @ R_list[t]) / len(R_list[t])
            else:
                X[t, :] = np.squeeze(Z_list[t].T.dot(R_list[t])) / len(R_list[t])
        eig_values, eig_vectors = np.linalg.eig(X.T.dot(X))
        Gamma = eig_vectors[:, :n_factors]
        return Gamma

    def initialize_factors(self, R_list, Z_list, n_factors, start_idx=0):
        """
        Initializes the factors for the IPCA model using PCA.

        This function computes the initial factors from the provided return lists
        and characteristic lists. It uses either weighted or unweighted calculations
        based on the 'weighted' attribute of the class. The estimated factors are
        obtained from the PCA of the characteristics data.

        Args:
            R_list (list): A list of return arrays for each time step.
            Z_list (list): A list of characteristic arrays for each time step.
            n_factors (int): The number of factors to estimate.
            start_idx (int): The starting index for the calculations (default is 0).

        Returns:
            list: A list of estimated factors for each time step, split into separate arrays.
        """
        T = len(R_list)
        X = np.zeros((T, self.num_characteristics))
        for t in range(T):
            if self.weighted:
                W_t = self.weight_matrices[t + start_idx]
                X[t, :] = np.squeeze(Z_list[t].T @ W_t @ R_list[t]) / len(R_list[t])
            else:
                X[t, :] = np.squeeze(Z_list[t].T.dot(R_list[t])) / len(R_list[t])
        pca = PCA(n_components=n_factors)
        pca.fit(X.T)  # pca.components_ matrix is of shape nFactors x T
        f_list = pca.components_
        return np.split(f_list, f_list.shape[1], axis=1)

    def nanl2norm(self, x):
        return np.sqrt(np.nansum(np.square(x)))

    def estimate_daily_oos_residuals(
        self,
        save: bool,
        weighted: bool,
        cap_proportion: float,
        num_factors_list: List[int],
        initial_months: int,
        size_window: int,
        reestimation_freq: int,
        max_iters: int,
        tol: float,
        log_freq: int,
        compute_residuals: bool = True,
        save_beta: bool = False,
        save_gamma: bool = False,
        save_rmonth: bool = False,
        save_mask: bool = False,
        save_sparse_weights_month: bool = False,
        save_factors: bool = False,
        save_factors_month: bool = False,
        save_all_monthly_factors: bool = False,
        skip_oos: bool = False,
    ):
        """
        Estimates the out-of-sample (OOS) daily residuals using a rolling window approach.

        This function applies an IPCA-based factor model to estimate residual portfolios over
        a specified initial period and window size. It computes the residuals for the daily
        returns, taking into account the specified factors and caps. The function can save
        various outputs including masks, weights, and factor estimates. Optional logging
        may be enabled to aid debugging.

        Important notes:
        - cap_proportion is typically set to 0.01 or 0.001
        - size_window must divide (months of data - training months)
        - initial_months must be >= size_window
        - The betas are constant each month (so essentially constant at the daily level), while the factors change daily

        Args:
            save (bool): Whether to save the residuals and composition matrices to disk.
            weighted (bool): Whether to use weighted regression for estimation (currently based on asset volatility weights).
            cap_proportion (float): Proportion of market cap to consider for asset selection.
            num_factors_list (list): List of integers specifying the number of factors to consider.
            initial_months (int): Number of months to use for the initial training period.
            size_window (int): Size of the rolling window for estimation of Gamma, in days.
            reestimation_freq (int): Frequency of re-estimation of Gamma, in months.
            max_iters (int): Maximum number of iterations for convergence.
            tol (float): Tolerance for convergence.
            log_freq (int): Frequency of logging progress.
            compute_residuals (bool): Whether to compute the residuals.
            save_beta (bool): Whether to save the beta estimates.
            save_gamma (bool): Whether to save the gamma estimates.
            save_rmonth (bool): Whether to save the monthly returns.
            save_mask (bool): Whether to save the asset mask.
            save_sparse_weights_month (bool): Whether to save the sparse weights for the month.
            save_factors (bool): Whether to save the factor estimates.
            save_factors_month (bool): Whether to save the monthly factor estimates.
            save_all_monthly_factors (bool): Whether to save all monthly factor estimates.
            skip_oos (bool): Whether to skip the out-of-sample estimation.

        Returns:
            None, but various outputs are saved to disk if specified.
        """
        logging.info(
            f"Beginning IPCA daily OOS rolling window estimation. Called with args: \n{pprint.pformat(locals())}"
        )

        R = self.monthly_data[:, :, self.monthly_data_returns_idx]  # returns
        chars_selector = [
            x
            for x in range(self.monthly_data.shape[2])
            if x != self.monthly_data_returns_idx
        ]
        if self.debug:
            logging.info(
                f"Selecting chars from monthly data in indices {chars_selector}"
            )
        Z = self.monthly_data[:, :, chars_selector]  # characteristics

        logging.info("Computing filter for assets to consider")
        monthly_mask = compute_monthly_permno_filter(
            self.monthly_data_unnormalized,
            R,
            cap_proportion,
            self.monthly_data_market_cap_idx,
            use_non_nan_return_filter=True,
            use_market_cap_filter=True,
            use_non_nan_chars_filter=True,
        )
        self.monthly_mask = monthly_mask
        if save_mask:
            mask_path = os.path.join(self.output_dir, f"mask_{cap_proportion}_cap.npy")
            np.save(mask_path, monthly_mask)

        R_reshape = np.expand_dims(R[monthly_mask], axis=1)
        Z_reshape = Z[monthly_mask]
        splits = np.sum(
            monthly_mask, axis=1
        ).cumsum()[
            :-1
        ]  # np.sum(mask, axis=1) how many stocks we have per year; the other cumulatively except for the last one
        R_list = np.split(R_reshape, splits)
        Z_list = np.split(Z_reshape, splits)
        self.R_list = R_list
        self.Z_list = Z_list
        n_windows = int((R.shape[0] - initial_months) / reestimation_freq)
        logging.info(f"Number of estimation windows: {n_windows}")

        if weighted:
            raise NotImplementedError(
                "Weighted IPCA not yet implemented."
            )

        first_oos_date = datetime.datetime(
            self.daily_dates.year[0], self.daily_dates.month[0], 1
        ) + pd.DateOffset(months=initial_months)
        self.first_oos_date = first_oos_date
        first_oos_daily_idx = np.argmax(self.daily_dates >= first_oos_date)
        self.first_oos_daily_idx = first_oos_daily_idx
        initial_oos_year = self.daily_dates[first_oos_daily_idx].year
        self.initial_oos_year = initial_oos_year
        logging.info(
            f"First OOS daily index: {first_oos_daily_idx}; First OOS year: {initial_oos_year}"
        )
        logging.info(f"self.daily_data.shape[0] {self.daily_data.shape[0]}")
        rets_daily = self.daily_data[first_oos_daily_idx:, :].copy()
        T, N = rets_daily.shape
        logging.info(f"Daily returns shape: T {T}, N {N}")
        factor_sharpe_ratios = np.zeros(len(num_factors_list))
        factor_ct = 0

        # Select assets with sufficient data to produce the assets to consider filter (contains all assets we'll ever consider for training)
        try:
            training_data_filename = (
                f"IPCA_DailyOOSresiduals"
                f"_{5}_factors"
                f"_{initial_months}_initialMonths"
                f"_{size_window}_window"
                f"_{reestimation_freq}_reestimationFreq"
                f"_{cap_proportion}_cap"
                ".npy"
            )
            training_data_filepath = os.path.join(
                self.output_dir, training_data_filename
            )
            training_data = np.load(training_data_filepath)
            logging.info(f"Loaded data from '{training_data_filepath}'")
            logging.info("Further filtering data for future policy training/backtest")
            assets_to_consider = compute_residual_filter(
                training_data
            )  # chooses stocks which have at least #lookback non-missing observations in all the training time
        except FileNotFoundError:
            logging.info("Computing filter for assets to consider")
            assets_to_consider = (
                np.count_nonzero(monthly_mask[initial_months - 1 :], axis=0) >= 1
            )
            logging.debug(
                "Optionally, to further reduce dimensionality of composition matrix for policy training, run this function again"
            )
        N_tilde = np.sum(assets_to_consider)
        logging.info(f"Total assets: {N}, Selected assets: {N_tilde}")
        self.assets_to_consider = assets_to_consider

        super_mask = np.count_nonzero(monthly_mask[initial_months - 1 :], axis=0) >= 1
        N_supertilde = np.sum(
            super_mask
        )  # the maximum assets that are going to be involved in the residuals
        logging.info(
            f"superMask.shape {super_mask.shape} superMask.sum() {N_supertilde}"
        )
        if save:
            np.save(
                os.path.join(self.output_dir, f"super_mask_{cap_proportion}.npy"),
                super_mask,
            )

        logging.info("Estimating residuals")
        for n_factors in num_factors_list:
            logging.info(
                f"====> Estimating residuals for cap={cap_proportion} factor={n_factors}"
            )

            residuals_oos = np.zeros_like(rets_daily, dtype=float)
            factors_oos = np.zeros_like(rets_daily[:, :n_factors], dtype=float)
            T, N = residuals_oos.shape
            comp_mtx_oos = np.zeros((T, N_tilde, N_supertilde), dtype=np.float32)
            idxs_selected_all = np.zeros((T, N), dtype=bool)

            if n_factors == 0:
                for month in range(initial_months, R.shape[0]):
                    logging.info(
                        f"==> AT MONTH {month} of {R.shape[0] - initial_months} ({n_factors} factors) <=="
                    )
                    idxs_days_month = (
                        self.daily_dates[first_oos_daily_idx:]
                        > self.monthly_dates[month - 1]
                    ) & (
                        self.daily_dates[first_oos_daily_idx:]
                        <= self.monthly_dates[month]
                    )

                    month_selection = monthly_mask[month - 1, :]
                    idxs_selected_all[idxs_days_month, :] = np.broadcast_to(
                        month_selection, (np.sum(idxs_days_month), N)
                    )
                    if np.any(month_selection & ~assets_to_consider):
                        logging.warning(
                            "Some selected indices are not in assets_to_consider!"
                        )
                        logging.warning(
                            f"Month {self.monthly_dates[month - 1]}: month_selection & ~assets_to_consider: {np.sum(month_selection & ~assets_to_consider)}"
                        )

                    rets_month = rets_daily[:, monthly_mask[month - 1, :]][
                        idxs_days_month, :
                    ]  # TxN
                    # change missing values to zeros to exclude them from calculation
                    rets_month_clean = rets_month.copy()
                    rets_month_clean[np.isnan(rets_month_clean)] = 0
                    residuals_month = rets_month
                    # set residuals equal to zero wherever there are NaNs from missing returns, as (NaN - prediction) is still NaN
                    residuals_month[np.isnan(residuals_month)] = 0
                    sparse_residuals_month = residuals_month
                    temp = residuals_oos[:, monthly_mask[month - 1, :]].copy()
                    temp[idxs_days_month, :] = residuals_month
                    residuals_oos[:, monthly_mask[month - 1, :]] = temp
                    # set comp mtx
                    Tprime, Nprime = rets_month_clean.shape
                    matrix_full = np.zeros((Tprime, N, N))
                    matrix_reduced = np.eye(Nprime)
                    mask_month = np.broadcast_to(
                        ~np.isnan(rets_month).reshape((Tprime, Nprime, 1)),
                        (Tprime, Nprime, Nprime),
                    )
                    matrix_full[
                        np.broadcast_to(
                            monthly_mask[month - 1, :].reshape((N, 1))
                            @ monthly_mask[month - 1, :].reshape((1, N)),
                            (Tprime, N, N),
                        )
                    ] = (
                        mask_month
                        * np.broadcast_to(matrix_reduced, (Tprime, Nprime, Nprime))
                    ).ravel()
                    comp_mtx_oos[idxs_days_month] = matrix_full[
                        :, assets_to_consider, :
                    ][:, :, super_mask]
            else:
                for n_window in range(n_windows):
                    f_list = None
                    logging.info(
                        f"==> AT WINDOW {n_window} of {n_windows} ({n_factors} factors) <=="
                    )

                    if not os.path.isdir(os.path.join(self.output_dir, "auxiliary")):
                        os.makedirs(os.path.join(self.output_dir, "auxiliary"))

                    # Load or estimate Gamma; use save_gamma=True to force estimation
                    # Gamma estimation
                    if n_window == 0:
                        gamma_path = os.path.join(
                            self.output_dir,
                            "auxiliary",
                            "gamma_"
                            f"{n_factors}_factors"
                            f"_{initial_months}_initialMonths"
                            f"_{size_window}_window"
                            f"_{reestimation_freq}_reestimationFreq"
                            f"_{cap_proportion}_cap"
                            f"_{n_window}.npy",
                        )
                        logging.info(f"Looking for {gamma_path}")
                        if os.path.isfile(gamma_path) and not save_gamma:
                            Gamma = np.load(gamma_path)
                            self.Gamma = Gamma
                            logging.info(f"Loaded {gamma_path}")
                        else:
                            logging.info("Estimating gamma")
                            f_list = self.initialize_factors(
                                R_list[
                                    (
                                        initial_months
                                        + n_window * reestimation_freq
                                        - size_window
                                    ) : (initial_months + n_window * reestimation_freq)
                                ],
                                Z_list[
                                    (
                                        initial_months
                                        + n_window * reestimation_freq
                                        - size_window
                                    ) : (initial_months + n_window * reestimation_freq)
                                ],
                                n_factors,
                                start_idx=initial_months
                                + n_window * reestimation_freq
                                - size_window,
                            )
                            self.Gamma = np.zeros((self.num_characteristics, n_factors))
                            iter = 0
                            while iter < max_iters:
                                Gamma = self.step_gamma(
                                    R_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    Z_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    f_list,
                                    n_factors,
                                    start_idx=initial_months
                                    + n_window * reestimation_freq
                                    - size_window,
                                )
                                f_list, _ = self.step_factors(
                                    R_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    Z_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    Gamma,
                                    start_idx=initial_months
                                    + n_window * reestimation_freq
                                    - size_window,
                                )
                                iter += 1
                                dGamma = np.max(np.abs(self.Gamma - Gamma))
                                self.Gamma = Gamma
                                if iter % log_freq == 0:
                                    logging.info(
                                        "nFactor: %d,\t nWindow: %d/%d,\t nIter: %d,\t dGamma: %0.2e"
                                        % (n_factors, n_window, n_windows, iter, dGamma)
                                    )
                                if iter > 1 and dGamma < tol:
                                    break
                            if save_gamma:
                                np.save(gamma_path, Gamma)
                    else:
                        gamma_path = os.path.join(
                            self.output_dir,
                            "auxiliary",
                            f"gamma"
                            f"_{n_factors}_factors"
                            f"_{initial_months}_initialMonths"
                            f"_{size_window}_window"
                            f"_{reestimation_freq}_reestimationFreq"
                            f"_{cap_proportion}_cap"
                            f"_{n_window}.npy",
                        )
                        logging.info(f"Looking for estimated gamma at '{gamma_path}'")
                        if (
                            os.path.isfile(gamma_path)
                            and not save_gamma
                            and not save_all_monthly_factors
                        ):
                            Gamma = np.load(gamma_path)
                            self.Gamma = Gamma
                            logging.info("Loaded gamma")
                        else:
                            logging.info("Estimating gamma")
                            iter = 0
                            while iter < max_iters // 2:
                                f_list, _ = self.step_factors(
                                    R_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    Z_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    self.Gamma,
                                    start_idx=initial_months
                                    + n_window * reestimation_freq
                                    - size_window,
                                )
                                Gamma = self.step_gamma(
                                    R_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    Z_list[
                                        (
                                            initial_months
                                            + n_window * reestimation_freq
                                            - size_window
                                        ) : (
                                            initial_months
                                            + n_window * reestimation_freq
                                        )
                                    ],
                                    f_list,
                                    n_factors,
                                    start_idx=initial_months
                                    + n_window * reestimation_freq
                                    - size_window,
                                )
                                iter += 1
                                dGamma = np.max(np.abs(self.Gamma - Gamma))
                                self.Gamma = Gamma
                                if iter % log_freq == 0:
                                    logging.info(
                                        "nFactor: %d,\t nWindow: %d/%d,\t nIter: %d,\t dGamma: %0.2e"
                                        % (n_factors, n_window, n_windows, iter, dGamma)
                                    )
                                if iter > 1 and dGamma < tol:
                                    break
                            if save_gamma:
                                np.save(gamma_path, Gamma)
                            if save_all_monthly_factors:
                                factors_monthly_path_filename = (
                                    f"monthlyFactors"
                                    f"_{n_factors}_factors"
                                    f"_{initial_months}_initialMonths"
                                    f"_{size_window}_window"
                                    f"_{reestimation_freq}_reestimationFreq"
                                    f"_{cap_proportion}_cap"
                                    f"_{n_window}_window.npy"
                                )
                                if not os.path.isdir(
                                    os.path.join(self.output_dir, "factors")
                                ):
                                    os.makedirs(
                                        os.path.join(self.output_dir, "factors")
                                    )
                                factors_monthly_path = os.path.join(
                                    self.output_dir,
                                    "factors",
                                    factors_monthly_path_filename,
                                )
                                np.save(factors_monthly_path, np.array(f_list))
                                logging.info("Monthly factors saved")

                    if not skip_oos:
                        logging.info("Estimating OOS residuals, factors, and betas")
                        # Computation of out-of-sample residuals
                        for month in range(
                            (initial_months + n_window * reestimation_freq),
                            (initial_months + (n_window + 1) * reestimation_freq),
                        ):
                            if month % log_freq == 0:
                                logging.info(
                                    f"-- Month: {month}/{(initial_months + (n_window + 1) * size_window)} --"
                                )
                            beta_month = Z[month - 1, monthly_mask[month - 1, :]].dot(
                                self.Gamma
                            )  # N x nfactors
                            idxs_days_month = (
                                self.daily_dates[first_oos_daily_idx:]
                                > self.monthly_dates[month - 1]
                            ) & (
                                self.daily_dates[first_oos_daily_idx:]
                                <= self.monthly_dates[month]
                            )

                            month_selection = monthly_mask[month - 1, :]
                            idxs_selected_all[idxs_days_month, :] = np.broadcast_to(
                                month_selection, (np.sum(idxs_days_month), N)
                            )
                            if np.any(month_selection & ~assets_to_consider):
                                logging.warning(
                                    "Some selected indices are not in assets_to_consider!"
                                )
                                logging.warning(
                                    f"Month {self.monthly_dates[month - 1]}: month_selection & ~assets_to_consider: {np.sum(month_selection & ~assets_to_consider)}"
                                )

                            rets_month = rets_daily[:, monthly_mask[month - 1, :]][
                                idxs_days_month, :
                            ]  # T x N

                            # change missing values to zeros to exclude them from calculation
                            rets_month_clean = rets_month.copy()
                            rets_month_clean[np.isnan(rets_month_clean)] = 0

                            if save_rmonth:
                                if not os.path.isdir(
                                    os.path.join(self.output_dir, "rmonth")
                                ):
                                    os.makedirs(os.path.join(self.output_dir, "rmonth"))
                                rets_month_filename = (
                                    "rmonth"
                                    f"_{month}_month"
                                    f"_{n_factors}_factors"
                                    f"_{initial_months}_initialMonths"
                                    f"_{size_window}_window"
                                    f"_{reestimation_freq}_reestimationFreq"
                                    f"_{cap_proportion}_cap"
                                    ".npy"
                                )
                                rm_path = os.path.join(
                                    self.output_dir, "rmonth", rets_month_filename
                                )
                                np.save(rm_path, rets_month_clean)

                            if weighted:
                                raise NotImplementedError(
                                    "Weighted IPCA not yet implemented"
                                )
                            else:
                                factors_month = np.linalg.pinv(
                                    beta_month.T @ beta_month
                                ).dot(
                                    beta_month.T @ rets_month_clean.T
                                )  # nfactors x T = (nFactors x N) @ (N x nFactors) @ (nFactors x N) @ (N x T)
                            factors_oos[idxs_days_month, :] = factors_month.T

                            if save_factors_month:
                                fm_filename = (
                                    "factors"
                                    f"_{month}_month"
                                    f"_{n_factors}_factors"
                                    f"_{initial_months}_initialMonths"
                                    f"_{size_window}_window"
                                    f"_{reestimation_freq}_reestimationFreq"
                                    f"_{cap_proportion}_cap"
                                    ".npy"
                                )
                                if not os.path.isdir(
                                    os.path.join(self.output_dir, "factors")
                                ):
                                    os.makedirs(
                                        os.path.join(self.output_dir, "factors")
                                    )
                                fm_path = os.path.join(
                                    self.output_dir, "factors", fm_filename
                                )
                                np.save(fm_path, factors_month)

                            if save_beta:
                                beta_filename = (
                                    "beta"
                                    f"_{month}_month"
                                    f"_{n_factors}_factors"
                                    f"_{initial_months}_initialMonths"
                                    f"_{size_window}_window"
                                    f"_{reestimation_freq}_reestimationFreq"
                                    f"_{cap_proportion}_cap"
                                    ".npy"
                                )
                                if not os.path.isdir(
                                    os.path.join(self.output_dir, "betas")
                                ):
                                    os.makedirs(os.path.join(self.output_dir, "betas"))
                                beta_path = os.path.join(
                                    self.output_dir, "betas", beta_filename
                                )
                                np.save(beta_path, beta_month)

                            if compute_residuals:
                                residuals_month = rets_month - factors_month.T.dot(
                                    beta_month.T
                                )
                                # set residuals equal to zero wherever there are NaNs from missing returns, as (NaN - prediction) is still NaN
                                residuals_month[np.isnan(residuals_month)] = 0

                                # below is same as: residuals_oos[np.ix_(idxs_days_month, monthly_mask[month-1,:])] = residuals_month
                                temp = residuals_oos[
                                    :, monthly_mask[month - 1, :]
                                ].copy()
                                temp[idxs_days_month, :] = residuals_month
                                residuals_oos[:, monthly_mask[month - 1, :]] = temp

                                Tprime, Nprime = rets_month_clean.shape
                                matrix_full = np.zeros((Tprime, N, N))
                                matrix_reduced = np.nan_to_num(
                                    np.eye(Nprime)
                                    - beta_month
                                    @ np.linalg.pinv(beta_month.T @ beta_month)
                                    @ beta_month.T
                                ).T  # Nprime x Nprime
                                mask_month = np.broadcast_to(
                                    ~np.isnan(rets_month).reshape((Tprime, Nprime, 1)),
                                    (Tprime, Nprime, Nprime),
                                )
                                matrix_full[
                                    np.broadcast_to(
                                        monthly_mask[month - 1, :].reshape((N, 1))
                                        @ monthly_mask[month - 1, :].reshape((1, N)),
                                        (Tprime, N, N),
                                    )
                                ] = (
                                    mask_month
                                    * np.broadcast_to(
                                        matrix_reduced, (Tprime, Nprime, Nprime)
                                    )
                                ).ravel()

                                comp_mtx_oos[idxs_days_month] = matrix_full[
                                    :, assets_to_consider, :
                                ][:, :, super_mask]
                    else:
                        logging.info("Skipping OOS computations")

                if not skip_oos:
                    factors_oos = np.nan_to_num(factors_oos)
                    factor_sharpe_ratios[factor_ct] = get_sharpe_tangency_portfolio(
                        factors_oos
                    )
                    factor_ct += 1

            self.idxs_selected_all = idxs_selected_all
            logging.info(
                f"Estimation complete for: factor={n_factors}, cap={cap_proportion}"
            )

            if save_factors:
                if not os.path.isdir(os.path.join(self.output_dir, "factors")):
                    os.makedirs(os.path.join(self.output_dir, "factors"))
                factors_filename = (
                    f"IPCA_factors"
                    f"_{n_factors}_factors"
                    f"_{initial_months}_initialMonths"
                    f"_{size_window}_window"
                    f"_{reestimation_freq}_reestimationFreq"
                    f"_{cap_proportion}_cap"
                    ".npy"
                )
                factors_path = os.path.join(
                    self.output_dir, "factors", factors_filename
                )
                np.save(factors_path, factors_oos)
                logging.info("Factors saved")

            if save and not skip_oos:
                logging.info(
                    "Saving asset filter of shape %s", assets_to_consider.shape
                )
                assets_to_consider_filename = f"assets-to-consider_{initial_oos_year}_initialOOSYear_{cap_proportion}_cap.npy"
                np.save(
                    os.path.join(self.output_dir, assets_to_consider_filename),
                    assets_to_consider,
                )
                logging.info("Asset filter saved")

                logging.info(f"Saving idxs selected of shape {idxs_selected_all.shape}")
                idxs_selected_all_filename = f"IPCA_idxs-selected-all_{n_factors}_factors_{initial_months}_initialMonths_{size_window}_window_{cap_proportion}_cap.npy"
                np.save(
                    os.path.join(self.output_dir, idxs_selected_all_filename),
                    idxs_selected_all,
                )
                logging.info("Idxs selected saved")

                logging.info(f"Saving residuals of shape {residuals_oos.shape}")
                residuals_filename = f"IPCA_DailyOOSresiduals_{n_factors}_factors_{initial_months}_initialMonths_{size_window}_window_{cap_proportion}_cap.npy"
                np.save(
                    os.path.join(self.output_dir, residuals_filename), residuals_oos
                )
                logging.info("Residuals saved")

                logging.info(f"Saving composition matrix of shape {comp_mtx_oos.shape}")
                comp_mtx_filename = f"IPCA_DailyMatrixOOSresiduals_{n_factors}_factors_{initial_months}_initialMonths_{size_window}_window_{cap_proportion}_cap.npy"
                np.save(os.path.join(self.output_dir, comp_mtx_filename), comp_mtx_oos)
                logging.info("Composition matrix saved")

                logging.info("Results saved")

            logging.info(
                f"====> Finished IPCA residual estimation for: cap={cap_proportion}, factor={n_factors}"
            )

        return