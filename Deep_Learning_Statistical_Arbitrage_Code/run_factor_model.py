import argparse
import logging
import os
import pprint
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from factor_models.famafrench import FamaFrenchResidualModelDLAP
from factor_models.pca import PCAResidualModelDLAP
from factor_models.ipca import IPCAResidualModelDLAP
from factor_models.utils import (
    preprocess_monthly_chars_dlap, 
    preprocess_daily_returns_dlap,
    produce_ff8_factors,
)
from utils import initialize_logging, send_telegram_message



def preprocess_dlap_data(
    monthly_characteristics_csv_path: str = "data/characteristics-replication.csv",
    daily_returns_csv_path: str = "data/daily-returns-replication.csv",
    risk_free_rate_csv_path: str = "data/F-F_Research_Data_Factors_daily.CSV",
    begin_year: int = 1963,
    end_year: int = 2016,
) -> None:
    """
    Preprocess DLAP data.
    
    Args:
        monthly_characteristics_csv_path (str): Path to monthly characteristics data.
        daily_returns_csv_path (str): Path to daily returns data.
        risk_free_rate_csv_path (str): Path to risk-free rate data.
        begin_year (int): Begin year for data.
        end_year (int): End year for data.

    Returns:
        None. Creates data directory and preprocessed data if it doesn't exist.
    """
    logging.info("Preprocessing DLAP data")
    if not os.path.exists("data"):
        os.makedirs("data")
    logging.info("Beginning preprocessing of monthly characteristics data")
    preprocess_monthly_chars_dlap(
        monthly_characteristics_csv_path=monthly_characteristics_csv_path, 
        output_dir='data'
    )
    preprocess_monthly_chars_dlap(
        monthly_characteristics_csv_path=monthly_characteristics_csv_path, 
        output_dir='data',
        normalize_characteristics=False,
    )
    logging.info("Beginning preprocessing of daily returns")
    preprocess_daily_returns_dlap(
        daily_returns_csv_path=daily_returns_csv_path, 
        risk_free_rate_csv_path=risk_free_rate_csv_path, 
        output_dir='data', 
        begin_year=begin_year, 
        end_year=end_year
    )
    logging.info("Preprocessing complete")


def run_ipca_dlap(
    output_dir: str = "residuals-replication/ipca",
    path_monthly_data: str = "data/MonthlyData.npz",
    path_daily_data: str = "data/DailyReturns-RFadjusted.npz",
    path_monthly_data_unnormalized: str = "data/MonthlyDataUnnormalized.npz",
    cap_proportion: float = 0.01,
    num_factors_list: List[int] = [5],  # [0, 1, 3, 5, 8, 10, 15],
    initial_months: int = 420,
    size_window: int = 20 * 12,
    reestimation_freq: int = 12,
    max_iters: int = 1500,
    tol: float = 1e-03,
    log_freq: int = 8,
    num_characteristics: int = 46,
    monthly_data_returns_idx: int = 0,
    monthly_data_market_cap_idx: int = 19,
    debug: bool = True,
) -> None:
    """
    Run IPCA factor model with configurable parameters to estimate and save residuals for the DLAP dataset.
    
    Args:
        output_dir (str): Directory for output files.
        path_monthly_data (str): Path to normalized monthly data.
        path_daily_data (str): Path to daily returns data.
        path_monthly_data_unnormalized (str): Path to unnormalized monthly data.
        cap_proportion (float): Market cap threshold for selecting assets.
        num_factors_list (list): List of number of factors to estimate.
        initial_months (int): Number of initial months for factor estimation.
        size_window (int): Lookback window size for estimating IPCA gamma matrix.
        reestimation_freq (int): Frequency of reestimation in months.
        max_iters (int): Maximum number of iterations for IPCA.
        tol (float): Tolerance for IPCA.
        log_freq (int): Logging frequency.
        num_characteristics (int): Number of characteristics.
        monthly_data_returns_idx (int): Index of the returns column in the monthly data.
        monthly_data_market_cap_idx (int): Index of the market capitalization column in the monthly data.
        debug (bool): Debug mode.
    
    Returns:
        None. Outputs are saved to the output directory.
    """
    logging.info("Beginning IPCA residual computations")

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ipca = IPCAResidualModelDLAP(
        output_dir=output_dir,
        path_monthly_data=path_monthly_data,
        path_daily_data=path_daily_data,
        path_monthly_data_unnormalized=path_monthly_data_unnormalized,
        num_characteristics=num_characteristics,
        monthly_data_returns_idx=monthly_data_returns_idx,
        monthly_data_market_cap_idx=monthly_data_market_cap_idx,
        debug=debug,
    )
    ipca.estimate_daily_oos_residuals(
        save=True,
        weighted=False,
        cap_proportion=cap_proportion,
        num_factors_list=num_factors_list,
        initial_months=initial_months,
        size_window=size_window,
        reestimation_freq=reestimation_freq,
        max_iters=max_iters,
        tol=tol,
        log_freq=log_freq,
        compute_residuals=True,
        save_mask=True,
        save_beta=False,
        save_gamma=False,
        save_rmonth=False,
        save_sparse_weights_month=False,
        skip_oos=False,
    )
    logging.info("IPCA residual computations complete")


def run_pca_dlap(
    output_dir: str = 'residuals-replication/pca', 
    path_daily_data: str = 'data/DailyReturns-RFadjusted.npz',
    path_monthly_data_unnormalized: str = 'data/MonthlyDataUnnormalized.npz',
    path_monthly_data: str = 'data/MonthlyData.npz',
    cap_proportion: int = 0.01,
    initial_oos_year: int = 1998,
    size_window: int = 60, 
    size_covariance_window: int = 252, 
    factor_list: List[int] = [5],  # [0, 1, 3, 5, 8, 10, 15],
    monthly_data_returns_idx: int = 0,
    monthly_data_market_cap_idx: int = 19,
) -> None:
    """
    Run PCA factor model with configurable parameters to estimate and save residuals for the DLAP dataset.

    Args:
        output_dir (str): Directory for output files.
        path_daily_data (str): Path to daily returns data.
        path_monthly_data_unnormalized (str): Path to unnormalized monthly data.
        path_monthly_data (str): Path to normalized monthly data.
        cap_proportion (float): Market cap threshold for selecting assets.
        initial_oos_year (int): Initial year for beginning factor estimation.
        size_window (int): Size of rolling window for estimating factors.
        size_covariance_window (int): Size of window for estimating covariance matrix.
        factor_list (list): List of number of factors to estimate.
        monthly_data_returns_idx (int): Index of the returns column in the monthly data.
        monthly_data_market_cap_idx (int): Index of the market capitalization column in the monthly data.
    
    Returns:
        None. Outputs are saved to the output directory.
    """
    logging.info("Beginning PCA residual computations")
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pca = PCAResidualModelDLAP(
        output_dir=output_dir,
        path_daily_data=path_daily_data,
        path_monthly_data_unnormalized=path_monthly_data_unnormalized,
        path_monthly_data=path_monthly_data,
        monthly_data_returns_idx=monthly_data_returns_idx,
        monthly_data_market_cap_idx=monthly_data_market_cap_idx,
    )
    pca.estimate_daily_oos_residuals(
        save=True, 
        cap_proportion=cap_proportion, 
        initial_oos_year=initial_oos_year,
        size_window=size_window, 
        size_covariance_window=size_covariance_window, 
        num_factors_list=factor_list,
    )
    logging.info("PCA residual computations complete")


def run_famafrench_dlap(
    data_dir: str = "data",
    output_dir: str = "residuals-replication/famafrench",
    daily_returns_path: str = "data/DailyReturns-RFadjusted.npz",
    monthly_data_unnormalized_path: str = "data/MonthlyDataUnnormalized.npz",
    monthly_data_path: str = "data/MonthlyData.npz",
    daily_fama_french_8_factors_csv_path: str = "data/FamaFrench8Daily.csv",
    window_size: int = 60,
    cap_threshold: float = 0.01,
    initial_oos_year: int = 1998,
    factors_to_compute: List[int] = [5],  # [0, 1, 5, 8],
    monthly_data_returns_idx: int = 0,
    monthly_data_market_cap_idx: int = 19,
) -> None:
    """
    Run Fama-French factor model with configurable parameters to estimate and save residuals for the DLAP dataset.
    
    Args:
        data_dir (str): Base directory for data files.
        output_dir (str): Directory for output files.
        daily_returns_path (str): Path to daily returns data.
        monthly_data_unnormalized_path (str): Path to unnormalized monthly data.
        monthly_data_path (str): Path to normalized monthly data.
        daily_fama_french_factors_csv_path (str): Path to Fama-French 8 factors daily data.
        window_size (int): Size of rolling window for estimating factors.
        cap_threshold (float): Market cap threshold for selecting assets.
        initial_oos_year (int): Initial year for beginning factor estimation.
        factors_to_compute (list): List of number of factors to estimate.
        monthly_data_returns_idx (int): Index of the returns column in the monthly data.
        monthly_data_market_cap_idx (int): Index of the market capitalization column in the monthly data.

    Returns:
        None. Outputs are saved to the output directory.
    """
    logging.info("Beginning Fama-French residual computations")
    
    # Ensure output and data directories exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Download Fama-French factors if not already downloaded
    _ = produce_ff8_factors(daily_fama_french_8_factors_csv_path)

    ff = FamaFrenchResidualModelDLAP(
        output_dir=output_dir,
        daily_returns_path=daily_returns_path,
        monthly_data_unnormalized_path=monthly_data_unnormalized_path,
        monthly_data_path=monthly_data_path,
        daily_fama_french_8_factors_path=daily_fama_french_8_factors_csv_path,
        monthly_data_returns_idx=monthly_data_returns_idx,
        monthly_data_market_cap_idx=monthly_data_market_cap_idx,
    )
    ff.estimate_daily_oos_residuals(
        save=True,
        initial_oos_year=initial_oos_year,
        size_window=window_size,
        cap_proportion=cap_threshold,
        num_factors_list=factors_to_compute,
    )
    logging.info("Fama-French residual computations complete")


def init_argparse():
    """
    Initialize argument parser for running a factor model.
    """
    parser = argparse.ArgumentParser(
        description="Run factor model to create residuals from raw returns."
    )
    parser.add_argument("--model", "-m", help="the name of a factor model ('ipca', 'pca', or 'famafrench')", required=True)
    parser.add_argument("--data", "-d", help="dataset to use (i.e. 'dlap')", required=True)
    parser.add_argument("--notification-telegram", "-nt", help="Notify Telegram upon completion or error", required=False)
    return parser


def main():
    """
    Main function to run a factor model to estimate residuals.
    """
    print("Running...")
    parser = init_argparse()
    args = parser.parse_args()
    username, hostname, log_tag, starttime = initialize_logging("FactorModel")
    model_name = args.model.lower()
    notification_telegram = args.notification_telegram
    try:
        if args.data.lower() == "dlap":
            preprocess_dlap_data()
            if args.model.lower() == "ipca":
                run_ipca_dlap()
            elif args.model.lower() == "pca":
                run_pca_dlap()
            elif args.model.lower() == "famafrench":
                run_famafrench_dlap()
            else:
                raise Exception(f"Invalid factor model '{args.model}'")
        else:
            raise Exception(f"Invalid dataset '{args.data}'")
    except Exception as e:
        logging.error("Uncaught exception", exc_info=e)
        error_msg = f"RUN FAILED: {model_name} - {log_tag} - {username}@{hostname} - {starttime} - {repr(e)}"
        if notification_telegram:
            try:
                send_telegram_message(error_msg)
            except Exception as tex:
                logging.error("Telegram exception", exc_info=tex)
        raise
    completion_msg = f"RUN COMPLETED: {model_name} - {log_tag} - {username}@{hostname} - {starttime}"
    if notification_telegram:
        try:
            send_telegram_message(completion_msg)
        except Exception as tex:
            logging.error("Telegram exception", exc_info=tex)
            logging.info(completion_msg)


if __name__ == "__main__":
    main()
