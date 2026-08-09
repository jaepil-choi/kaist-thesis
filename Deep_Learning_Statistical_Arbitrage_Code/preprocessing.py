"""
Functions to preprocess residual time series into time series for use with models.

Add new preprocessing functions here.
"""

import logging
from typing import Any, Dict, Tuple

import numpy as np
import torch

from factor_models.utils import compute_nonmissing_indices


def preprocess_cumsum(
    data: np.ndarray, lookback: int, config: Dict[str, Any]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Preprocess TxN numpy ndarray `data` into cumulative sum windows along first 
    (i.e. T-th) axis of integer length `lookback`, while filtering asset time series to
    select only valid time series without missing data (which is represented as zero). 
    Works with any signal type.
    
    Note: This can be implemented much more efficiently, but is written for readability.

    Args:
        data: TxN numpy ndarray of asset returns.
        lookback: Integer length of the window.
        config: Dictionary of configuration settings.
        
    Returns:
        Tuple[np.ndarry, np.ndarray]:
            - TxNxlookback numpy ndarray of cumulative sum windows.
            - TxN boolean mask of filtered asset time series.
    """
    signal_length = lookback
    T,N = data.shape
    cumsums = np.cumsum(data, axis=0)
    windows = np.zeros((T-lookback, N, signal_length), dtype=np.float32)
    idxs_selected = np.zeros((T-lookback,N), dtype=bool)
    for t in range(lookback,T):
        # Chooses assets which have no missing returns in the t-th lookback window
        idxs = compute_nonmissing_indices(idxs_selected, data, t, lookback)

        if t == lookback:
            windows[t-lookback,idxs,:] = cumsums[t-lookback:t,idxs].T
        else:
            # This makes the cumulative sum start at each day's return for every day
            # (instead of being a subperiod of the cumulative sum over all time T)
            windows[t-lookback,idxs,:] = cumsums[t-lookback:t,idxs].T - cumsums[t-lookback-1,idxs].reshape(int(sum(idxs)),1)

    return windows, torch.as_tensor(idxs_selected)


def preprocess_fourier(
    data: np.ndarray, lookback: int, config: Dict[str, Any]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Preprocess TxN numpy ndarray `data` into Fourier coefficients calculated from the
    cumulative sums of input data in windows along first (i.e. T-th) axis of integer 
    length `lookback`, while filtering time series to select only valid time series 
    without missing data (which is represented as zero). Works with any signal type.
    
    Note: This can be implemented much more efficiently, but is written for readability.

    Args:
        data: TxN numpy ndarray of asset returns.
        lookback: Integer length of the window.
        config: Dictionary of configuration settings.
        
    Returns:
        Tuple[np.ndarry, np.ndarray]:
            - TxNxlookback numpy ndarray of Fourier coefficients.
            - TxN boolean mask of filtered asset time series.
    """
    signal_length = lookback
    T,N = data.shape
    cumsums = np.cumsum(data, axis=0)
    windows = np.zeros((T-lookback, N, signal_length), dtype=np.float32)
    idxs_selected = np.zeros((T-lookback,N), dtype=bool)
    for t in range(lookback,T):
        # Chooses assets which have no missing returns in the t-th lookback window
        idxs = compute_nonmissing_indices(idxs_selected, data, t, lookback)
        
        if t == lookback:
            windows[t-lookback,idxs,:] = cumsums[t-lookback:t,idxs].T
        else:
            # this makes the cumulative sum start at each day's return for every day 
            # (instead of being a subperiod of the cum. sum over all time T)
            windows[t-lookback,idxs,:] = cumsums[t-lookback:t,idxs].T - cumsums[t-lookback-1,idxs].reshape(int(sum(idxs)),1)
                
    fourier_coefs = np.fft.rfft(windows,axis=-1)
    windows[:,:,:(lookback//2+1)] = np.real(fourier_coefs)
    windows[:,:,(lookback//2+1):] = np.imag(fourier_coefs[:,:,1:-1])    
    
    return windows, torch.as_tensor(idxs_selected)


def preprocess_ou(
    data: np.ndarray, lookback: int, config: Dict[str, Any]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Preprocess TxN numpy ndarray `data` into Ornstein-Uhlenbeck (OU) signal windows
    calculated from the cumulative sums of input data in windows along first (i.e. T-th)
    axis of integer length `lookback`, while filtering time series to select only valid
    time series without missing data (which is represented as zero). Works with any signal type.
    
    Note: This can be implemented much more efficiently, but is written for readability.
    
    Args:
        data: TxN numpy ndarray of asset returns.
        lookback: Integer length of the window.
        config: Dictionary of configuration settings.
        
    Returns:
        Tuple[np.ndarry, np.ndarray]:
            - TxNx4 numpy ndarray of OU signal windows containing (last price, mu, sigma, R^2).
            - TxN boolean mask of filtered asset time series.
    """
    signal_length = 4
    eps = 1e-6
    T,N = data.shape
    cumsums = np.cumsum(data, axis=0)
    windows = np.zeros((T-lookback, N, signal_length), dtype=np.float32)
    idxs_selected = np.zeros((T-lookback,N), dtype=bool)
    for t in range(lookback,T):
        # Chooses assets which have no missing returns in the t-th lookback window
        idxs = compute_nonmissing_indices(idxs_selected, data, t, lookback)
        
        if t == lookback:
            x = cumsums[t-lookback:t,idxs].T
        else:
            # This makes the cumulative sum start at each day's return for every day
            # (instead of being a subperiod of the cum. sum over all time T)
            x = cumsums[t-lookback:t,idxs].T - cumsums[t-lookback-1,idxs].reshape(int(sum(idxs)),1)
        
        # Compute OU parameters and signal
        Nx, Tx = x.shape
        X = x[:, :-1]  # (N,T-1)
        Y = x[:, 1:]
        means_x = np.mean(X, axis=1)  # N
        means_y = np.mean(Y, axis=1)
        vars_x = np.var(X, axis=1)  # N
        vars_y = np.var(Y, axis=1)
        covs = np.mean((X - means_x.reshape((Nx, 1))) * (Y - means_y.reshape((Nx, 1))), axis=1)  # N
        r2 = covs**2 / (vars_x * vars_y)  # N
        bs = covs / vars_x  # N
        cs = means_y - bs * means_x
        mus = cs / (1 - bs + eps)
        mask = (bs > 0) * (bs < 1)
        # kappas = -np.log(bs) / delta_t  # if bs is between 0 and 1
        residuals = Y - bs.reshape((Nx, 1)) * X - cs.reshape((Nx, 1))  # (N,T-1)
        sigmas = np.sqrt(np.var(residuals, axis=1) / np.abs(1 - bs**2 + eps))  # N
        signal = np.zeros((Nx))
        # signal =  (mus - Y[:,-1]) / sigmas * mask
        signal[mask] = (mus[mask] - Y[:, -1][mask]) / sigmas[mask]
        windows[t - lookback, idxs, 0] = Y[:, -1]
        windows[t - lookback, idxs, 1] = mus
        windows[t - lookback, idxs, 2] = sigmas
        windows[t - lookback, idxs, 3] = r2

        idxs_selected[t - lookback, idxs] = idxs_selected[t - lookback, idxs] & mask

    return windows, torch.as_tensor(idxs_selected)