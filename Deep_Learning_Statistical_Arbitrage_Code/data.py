import numpy as np
import torch

torch.set_default_dtype(torch.float)
torch.autograd.set_detect_anomaly(True)
torch.backends.cudnn.deterministic = False
    

def perturb(data: np.ndarray, perturbation_config: dict) -> np.ndarray:
    """
    Perturbs residuals matrix to add noise.

    Takes in TxN NumPy residuals matrix and a perturbation configuration.
    
    Args:
        data (np.ndarray): TxN NumPy residuals matrix.
        perturbation_config (dict): Perturbation configuration dictionary with the following keys:
            - noise_type (str): Type of noise to add ('gaussian').
            - noise_mean (float): Mean of the noise.
            - noise_std_pct (float): Portion (as decimal) of the data's standard deviation which the noise should use as its standard deviation.
            - per_residual (bool): True to estimate/use std for each residual separately, False to estimate/use global std of all residuals.
            - noise_only (bool): True to replace the data with noise, False to add the noise to the data.

    Returns:
        np.ndarray: Perturbed residuals matrix.
    """
    if perturbation_config['per_residual']:
        # compute std of each residual
        # trick: replace zeros with NaNs using np.where and use np.nanstd to except zeros from std calculation
        # this is done because zeros code for missing data in our dataset
        data_std = np.nanstd(np.where(np.isclose(data,0), np.nan, data), axis=0)
        # some residuals are all zero, and np.nanstd makes the resultant std nan, so set those std's back to zero, as they should be
        data_std[np.isnan(data_std)] = 0
    else:
        data_std = np.std(data[data != 0])
    if perturbation_config['noise_type'] == "gaussian":
        noise = perturbation_config['noise_mean'] + perturbation_config['noise_std_pct'] * data_std * np.random.randn(*(data.shape))
    else:
        raise Exception(f"Unimplemented noise type '{perturbation_config['noise_type']}'")
    # don't add noise to missing observations
    if perturbation_config['noise_only']:
        data = (data != 0) * noise
    else:
        data += (data != 0) * noise
    return data