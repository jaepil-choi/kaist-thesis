import logging
import os
from typing import List, Tuple

import numpy as np
import pandas as pd
from numba import njit
from tqdm import tqdm

MINIMUM_LOOKBACK = 30
FAMA_FRENCH_FACTORS_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
FAMA_FRENCH_5_FACTORS_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
FAMA_FRENCH_MOM_FACTOR_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"
FAMA_FRENCH_LT_REV_FACTOR_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_ST_Reversal_Factor_daily_CSV.zip"
FAMA_FRENCH_ST_REV_FACTOR_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_LT_Reversal_Factor_daily_CSV.zip"


def produce_ff8_factors(output_path: str) -> pd.DataFrame:
    """
    Load Fama-French 8 factors (FF5 + momentum + long-term reversal + short-term reversal), 
    or download and prepare them if they don't exist.

    Args:
        output_path (str): Path to save the downloaded factors.

    Returns:
        pd.DataFrame: Dataframe of Fama-French 8 factors with dates as index.
    """
    if not os.path.exists(output_path):
        logging.info("Downloading Fama-French factors")
        ff5 = pd.read_csv(FAMA_FRENCH_5_FACTORS_URL, header=2, index_col=0)
        mom = pd.read_csv(FAMA_FRENCH_MOM_FACTOR_URL, header=11, index_col=0)
        strev = pd.read_csv(FAMA_FRENCH_ST_REV_FACTOR_URL, header=11, index_col=0)
        ltrev = pd.read_csv(FAMA_FRENCH_LT_REV_FACTOR_URL, header=11, index_col=0)
        factors = [ff5,mom,strev,ltrev]
        for i in range(len(factors)):
            factors[i].index = factors[i].index.map(str)
        ff8 = pd.concat(factors, axis=1, join="inner")
        ff8.index = ff8.index.astype('int')
        ff8.rename(columns={col:col.strip() for col in ff8.columns}, inplace=True)
        ff8.drop(columns=['RF'], inplace=True)   
        logging.info("Saving Fama-French factors to %s", output_path)
        ff8.to_csv(output_path)
    else:
        logging.info("Loading Fama-French factors from %s", output_path)
        ff8 = pd.read_csv(output_path, index_col=0)
    return ff8


def compute_monthly_permno_filter(
    unnormalized_monthly_chars: np.ndarray, 
    monthly_returns: np.ndarray, 
    cap_pct: float, 
    mcap_idx: int,
    use_market_cap_filter=True,
    use_non_nan_return_filter=True,
    use_non_nan_chars_filter=True,
) -> np.ndarray:
    """
    Gets the filter (a binary mask matrix) to select permnos for each month.
    
    A permno is selected if it satisfies all of the following filters:
    - a market cap s.t. the permno's market cap for month >= cap_pct/100 * sum(all permno's market caps in month), if use_market_cap_filter=True
    - a non-missing monthly return in the given month, if use_non_nan_return_filter=True
    - non-missing characteristics in the given month, if use_non_nan_chars_filter=True

    Example: Letting cap_pct=0 returns all indices, as market caps are always >= 0.
    Example: Letting cap_pct=1 returns indices for permnos with market cap >= 1% of the total sum of market caps for each month.
    Example: Letting cap_pct=0.1 returns indices for permnos with market cap >= 0.1% of the total sum of market caps for each month.
    
    Args:
        unnormalized_monthly_chars (np.array(T,N,L)): TxNxL array of UNNORMALIZED monthly data, T=months, N=permnos, L=characteristics.
            - In MFD data, market caps are in characteristic index 20.
            - In DLAP data, returns are in characteristic index 0, and market caps in characteristic index 19.
        monthly_returns (np.array(T,N)): TxN array of monthly returns, T=months, N=permnos.
        cap_pct (float): the percent threshold to filter for, typically 0.01 or 0.001
        mcap_idx (int): index of market cap in `unnormalized_monthly_chars`, either 19 for DLAP data or 20 for MFD data
        use_market_cap_filter (bool): whether to use the cap-chosen indices filter
        use_non_nan_return_filter (bool): whether to use the non-NaN return filter
        use_non_nan_chars_filter (bool): whether to use the non-NaN characteristic filter
    
    Returns:
        np.ndarray(T,N): The filter of T months by N permnos which contains a True in the index for the selected permnos each month and False otherwise.
    """
    if cap_pct >= 100 or cap_pct < 0:
        raise Exception("cap_pct must be in range [0, 100)")
    monthly_caps = np.nan_to_num(unnormalized_monthly_chars[:,:,mcap_idx])
    market_cap_mask = monthly_caps / np.nansum(monthly_caps, axis=1, keepdims=True) >= cap_pct * 0.01
    non_nan_ret_mask = (~np.isnan(monthly_returns))
    non_nan_char_mask = (~np.isnan(unnormalized_monthly_chars.sum(axis=2)))
    mask = np.ones_like(monthly_caps, dtype=bool)
    if use_non_nan_return_filter:
        mask = mask & non_nan_ret_mask
    if use_non_nan_chars_filter:
        mask = mask & non_nan_char_mask
    if use_market_cap_filter:
        mask = mask & market_cap_mask
    return mask


def compute_residual_filter(residuals):
    """
    Computes a filter for residuals to determine which permnos have enough non-zero residuals
    in the lookback window. This is used as a prefilter to filter out residuals which will never,
    at any future time, have enough data to fill the lookback window that trading policy models
    require to be full of non-missing data.
    
    This function checks if each residual has at least `MINIMUM_LOOKBACK` non-zero returns
    in the lookback window. This is done by counting the number of non-zero entries along the
    first axis (time) of the residuals array. If the count is greater than or equal to
    `MINIMUM_LOOKBACK`, the corresponding permno is considered valid (True), and kept. Otherwise,
    it is considered invalid (False) and filtered out. This helps to ensure that only residuals
    with sufficient data are included in further analysis or modeling.
    
    Note that whenever this filter is used, the point-in-time filter `compute_nonmissing_indices` 
    will be used at each time step to ensure that only the valid permnos are selected based on the 
    available data up to that point in time.
    
    Args:
        residuals (np.ndarray): The residuals array of shape (T, N), where T is the number of days
            and N is the number of residuals. Each entry in this array represents the residual for a
            given permno at a given day.
            
    Returns:
        np.ndarray: A binary mask of shape (T, N) where each entry is True if the corresponding permno
            has at least `MINIMUM_LOOKBACK` non-zero residuals in the lookback window, and False otherwise.
    """
    return np.count_nonzero(residuals, axis=0) >= MINIMUM_LOOKBACK


def compute_nonmissing_indices(idxs_selected, data, t, lookback):
    """
    Selects non-missing indices for the given time t based on the lookback window.
    This function updates the `idxs_selected` array to mark which assets have no missing returns
    in the t-th lookback window. 
    
    This function is used to filter out residuals that do not have enough data for the selection 
    of residuals for trading policy models.
    
    Note that the filter used here,
    ```
    ~np.any(data[(t - lookback) : t, :] == 0, axis=0)
    ```
    is exactly equivalent to the same filter used in `compute_residual_filter`, i.e.
    ```
    np.count_nonzero(data[(t - lookback) : t, :], axis=0) >= lookback
    ```
    The only difference is that this filter is faster, as it returns False for a residual
    as soon as a zero is found in the lookback window, whereas `compute_residual_filter` counts
    the number of non-zero entries in the lookback window and only returns True if the count
    is greater than or equal to the lookback.
    
    Args:
        idxs_selected (np.ndarray): The binary mask array to update, shape (T-lookback, N).
        data (np.ndarray): The data array containing returns, shape (T, N).
        t (int): The current time index.
        lookback (int): The lookback window size.
        
    Returns:
        np.ndarray: The binary mask for the selected indices at time t. 
            This will be a boolean array of shape (N,) where each entry is True if the corresponding
            asset has no missing returns in the lookback window, and False otherwise.
    """
    idxs_selected[t - lookback, :] = ~np.any(data[(t - lookback) : t, :] == 0, axis=0).ravel()
    return idxs_selected[t - lookback, :]


def preprocess_monthly_chars_dlap(
    monthly_characteristics_csv_path: str,
    output_dir: str,
    char_indices: List[int] = None,
    normalize_characteristics: bool = True,
    save_filename: str = "MonthlyData.npz",
):
    """
    Preprocesses monthly characteristics from DLAP paper.

    Args:
        monthly_characteristics_csv_path (str): The filepath to the monthly data to preprocess. Must contain monthly characteristics.
        output_dir (str): The directory to save the preprocessed data to.
        char_indices (List[int]): The indices which contain characteristics in the given data.
        normalize_characteristics (bool): Whether to normalize the characteristics.
        save_filename (str): The filename to save the preprocessed data to.

    Returns:
        None
    """
    if normalize_characteristics:
        save_filename = save_filename
    else:
        save_filename = save_filename.replace(".npz", "Unnormalized.npz")

    savepath = os.path.join(output_dir, save_filename)
    if os.path.exists(savepath):
        logging.info("Monthly characteristics data already processed; skipping")
        return
    
    logging.info("Loading characteristics data")
    data = pd.read_csv(monthly_characteristics_csv_path)

    if char_indices is None:
        char_indices = [2]+list(range(5, data.shape[1]))
    
    if normalize_characteristics:
        char_data = data.iloc[:,char_indices]
        grouped = char_data.groupby("date")
        char_data_normalized = grouped.transform(
            lambda x: x.rank(method="first") / x.count() - 0.5
        )
        data.iloc[:, 5:] = char_data_normalized

    data.index = pd.MultiIndex.from_frame(data[["date", "permno"]])
    data = data.drop(columns=data.columns[range(0, 4)])
    data.sort_index(inplace=True)
    shape = data.index.levshape + tuple([len(data.columns)])
    data_array = np.full(shape, np.nan)
    data_array[tuple(data.index.codes)] = data.values

    date = data.index.levels[0].to_numpy()
    permno = data.index.levels[1].to_numpy()
    variable = data.columns.to_numpy()

    np.save(os.path.join(output_dir, "permnos.npy"), permno)
    np.savez(savepath, data=data_array, date=date, permno=permno, variable=variable)
    return


def preprocess_daily_returns_dlap(
    daily_returns_csv_path: str,
    risk_free_rate_csv_path: str,
    output_dir: str,
    begin_year: int,
    end_year: int,
    save_filename: str = "DailyReturns-RFadjusted.npz",
    risk_free_adjust: bool = True,
):
    """
    Preprocesses daily data from DLAP paper.

    Args:
        daily_returns_csv_path (str): The filepath to the CRSP daily data to preprocess. Must contain daily returns. Must have columns ['date', 'permno', 'ret'].
        risk_free_rate_csv_path (str): The filepath to the risk free rates to adjust the returns by if risk_free_adjust is True. Must have index 'date'.
        output_dir (str): The directory to save the preprocessed data to.
        save_filename (str): The filename to save the preprocessed data to.
        risk_free_adjust (bool): Whether to adjust the returns by the risk free rates.

    Returns:
        None
    """
    savepath = os.path.join(output_dir, save_filename)
    if os.path.exists(savepath):
        logging.info("Daily returns already processed; skipping")
        return
    
    logging.info("Loading daily returns")
    data = pd.read_csv(daily_returns_csv_path)
    logging.info("Loading risk-free rates")
    if not os.path.exists(risk_free_rate_csv_path):
        rf_rates = pd.read_csv(FAMA_FRENCH_FACTORS_URL, header=3, index_col=0)
        if rf_rates.empty:
            raise ValueError("Risk-free rate data is empty; check the URL content")
        if 'RF' not in rf_rates.columns:
            raise ValueError("Risk-free rate data must contain 'RF' column")
        rf_rates = rf_rates.iloc[:-1,:]
        rf_rates.index = rf_rates.index.astype('int')
        rf_rates.index.name = 'Date'
        rf_rates.to_csv(risk_free_rate_csv_path)
    else:
        rf_rates = pd.read_csv(risk_free_rate_csv_path, index_col=0)
    risk_free_rates = rf_rates.loc[(rf_rates.index >= begin_year * 10_000) & (rf_rates.index < (end_year + 1) * 10_000),['RF']].to_numpy() / 100

    data = data[["date", "permno", "ret"]]
    data.index = pd.MultiIndex.from_frame(data[["date", "permno"]])
    data = data.drop(columns=data.columns[range(0, 2)])
    data.sort_index(inplace=True)
    shape = data.index.levshape + tuple([len(data.columns)])
    data_array = np.full(shape, np.nan)
    data_array[tuple(data.index.codes)] = data.values
    returns = data_array[:, :, 0]

    if risk_free_adjust:
        returns -= risk_free_rates

    date = data.index.levels[0].to_numpy()
    permno = data.index.levels[1].to_numpy()

    try:
        pmask = np.load(os.path.join(output_dir, "permnos.npy"))
    except FileNotFoundError:
        raise FileNotFoundError("Permnos file not found; make sure to run preprocess_monthly_data_dlap() first")
    returns = returns[:, np.isin(permno, pmask)]
    permno = pmask

    np.savez(savepath, data=returns, date=date, permno=permno)
    return


@njit
def fast_nan_to_num_2d(arr, nan_val=0.0, posinf_val=0.5, neginf_val=0.5):
    """
    Converts NaN and infinite values in a 2D numpy array to specified values.
    
    This function replaces:
    - NaN values with `nan_val`
    - Positive infinity values with `posinf_val`
    - Negative infinity values with `neginf_val`
    
    This is faster than NumPy's `np.nan_to_num` for large arrays.
    
    Args:
        arr (np.ndarray): The input 2D numpy array to process.
        nan_val (float): The value to replace NaN values with. Default is 0.0.
        posinf_val (float): The value to replace positive infinity values with. Default is 0.5.
        neginf_val (float): The value to replace negative infinity values with. Default is 0.5.
        
    Returns:
        None: The function modifies the input array `arr` in place.
    """
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if np.isnan(arr[i,j]):
                arr[i,j] = nan_val
            elif np.isinf(arr[i,j]):
                if arr[i,j] > 0:
                    arr[i,j] = posinf_val
                else:
                    arr[i,j] = neginf_val

@njit
def fast_nan_to_num_3d(arr, nan_val=0.0, posinf_val=0.5, neginf_val=0.5):
    """
    Converts NaN and infinite values in a 3D numpy array to specified values.
    
    This function replaces:
    - NaN values with `nan_val`
    - Positive infinity values with `posinf_val`
    - Negative infinity values with `neginf_val`
    
    This is faster than NumPy's `np.nan_to_num` for large arrays.
    
    Args:
        arr (np.ndarray): The input 3D numpy array to process.
        nan_val (float): The value to replace NaN values with. Default is 0.0.
        posinf_val (float): The value to replace positive infinity values with. Default is 0.5.
        neginf_val (float): The value to replace negative infinity values with. Default is 0.5.
        
    Returns:
        None: The function modifies the input array `arr` in place.
    """
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            for k in range(arr.shape[2]):
                if np.isnan(arr[i,j,k]):
                    arr[i,j,k] = nan_val
                elif np.isinf(arr[i,j,k]):
                    if arr[i,j,k] > 0:
                        arr[i,j,k] = posinf_val
                    else:
                        arr[i,j,k] = neginf_val