import glob
import logging
import os
import time
from typing import Optional, Any, Callable, List, Dict, Tuple

import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn

from factor_models.utils import MINIMUM_LOOKBACK, compute_residual_filter
from utils import import_string, moving_average_pytorch, get_model_attr, get_model_tag


def transform_weights(
    weights: torch.Tensor,
    residuals: torch.Tensor,
    comp_mtx_t: torch.Tensor,
    config: dict,
) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
    """
    Transform weights by applying some policy (such as smoothing, sparsification, etc.) and normalization (e.g. of L1 norm).
    
    Note that comp_mtx_t multiplied by returns on the right gives residuals. For example, the first row of comp_mtx_t gives the 
    weights of the assets comprising the first residual. The first column of comp_mtx_t gives the weights of the residuals
    comprising the first asset. Note that comp_mtx_t should always be provided, unless debugging.

    This function could use refactoring.

    Args:
        weights (torch.Tensor): (T1, N1) window of residual allocation weights
        residuals (torch.Tensor): (T1, N1) window of cumulative (?) residuals
        comp_mtx_t (torch.Tensor): (T1, N1, N2) window of N1xN2 residual composition matrices (N1 is #resids, N2 is #assets)
        config (dict): configuration dictionary

    Returns:
        Tuple[torch.Tensor, Optional[torch.Tensor]]: Tuple containing
            - weights (torch.Tensor): (T1, N1) window of residual allocation weights
            - asset_weights (Optional[torch.Tensor]): (T1, N2) window of asset allocation weights (if composition matrix is provided)
    """
    eps = 1e-8  # Small epsilon to avoid division by zero

    # weights is T1xN1
    if comp_mtx_t is None:
        T1,N1 = weights.shape
    else:
        T1,N1,N2 = comp_mtx_t.shape
        assert(weights.shape == comp_mtx_t.shape[:2])

    has_weight_policy = (
        "weight_policy" in config and config["weight_policy"]["name"] != "normal"
    )
    normalize_residual_leverage = has_weight_policy or (config["weight_policy"]["type"] == "residuals")
    # If we explicitly want to not normalize, then don't
    if has_weight_policy and "normalize_leverage" in config["weight_policy"]:
        if not config["weight_policy"]["normalize_leverage"]:
            normalize_residual_leverage = False

    # Apply weight policies based on residual weights
    if has_weight_policy and config["weight_policy"]["type"] == "residuals":
        if config["weight_policy"]["name"] == "moving_average":
            # Replace weights in batch with simple moving average of weights over past `window` periods
            ma_window = config["weight_policy"]["window"]
            weights = moving_average_pytorch(
                weights, n=ma_window, axis=0, device=weights.device
            )
        elif config["weight_policy"]["name"] == "sparse_percent":
            raise Exception("sparse_percent policy is not yet implemented")
        else:
            raise Exception(f"Invalid residuals weight policy '{config['weight_policy']['name']}'")
    
    if normalize_residual_leverage:
        # Apply leverage constraint
        if comp_mtx_t is None:
            # Mormalize by the residual weights' L1 norm; this may NOT explicitly enforce the leverage constraint
            abs_sum = torch.sum(torch.abs(weights), axis=1, keepdim=True)
        else:  
            # Apply residual composition matrix to get asset weights' L1 norm, for leverage constraint.
            # asset_weights are for underlying asset space, so they'll be T1xN2
            asset_weights = torch.bmm(weights.reshape(T1,1,N1), comp_mtx_t).squeeze() 
            abs_sum = torch.sum(torch.abs(asset_weights), axis=1, keepdim=True)
            asset_weights = asset_weights/(abs_sum + eps)
        weights = weights/(abs_sum + eps)
    else:
        if not has_weight_policy:
            if comp_mtx_t is not None:
                asset_weights = torch.bmm(weights.reshape(T1,1,N1), comp_mtx_t).squeeze()
            else:
                asset_weights = weights
        elif has_weight_policy and config['weight_policy']['type'] != 'assets':
            if comp_mtx_t is not None:
                asset_weights = torch.bmm(weights.reshape(T1,1,N1), comp_mtx_t).squeeze()
            else:
                asset_weights = weights
        else:
            # will be normalized if necessary in asset weights section
            pass

    # Apply weight policies based on asset weights, and normalize leverage constraint
    if has_weight_policy and config["weight_policy"]["type"] == "assets":
        if config["weight_policy"]["name"] == "moving_average":
            abs_sum = torch.sum(torch.abs(weights), axis=1, keepdim=True)
            weights = weights / (abs_sum + eps)
            # Replace weights in batch with simple moving average of weights over past `window` periods
            ma_window = config["weight_policy"]["window"]
            weights = moving_average_pytorch(
                weights, n=ma_window, axis=0, device=weights.device
            )
            asset_weights = torch.bmm(weights.reshape(T1, 1, N1), comp_mtx_t).squeeze()
        elif config["weight_policy"]["name"] == "sparse_percent":
            raise Exception("sparse_percent policy is not yet implemented")
        else:
            raise Exception(f"Invalid assets weight policy '{config['weight_policy']['name']}'")

    return weights, asset_weights if comp_mtx_t is not None else None
    
    
def train(
    model: nn.Module,
    config: dict,
    preprocess: Callable,
    data_train: np.ndarray,
    data_val: Optional[np.ndarray],
    comp_mtx_train: Optional[np.ndarray],
    comp_mtx_val: Optional[np.ndarray],
    save_params: bool,
    output_path: str,
    model_tag: str,
    device: str,
    device_ids: List[int],
    subperiod: int,
    num_total_subperiods: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Train a model on the given data.
    
    Args:
        model (nn.Module): the model to train
        config (dict): the configuration dictionary
        preprocess (Callable): a function that selects and preprocesses data from preprocessing.py
        data_train (np.ndarray): the training data
        data_val (np.ndarray): the validation data
        comp_mtx_train (np.ndarray): the composition matrix for the training data
        comp_mtx_val (np.ndarray): the composition matrix for the validation data
        save_params (bool): whether to save the parameters of the best model
        output_path (str): the path to the output directory
        model_tag (str): the tag to add to the model name
        device (str): the device to use
        device_ids (list): the device ids to use
        subperiod (int): the subperiod that `data_train` corresponds to (for model to train; 0-indexed)
        num_total_subperiods (int): the number of subperiods
    
    Returns:
        Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, np.ndarray]:
            Tuple of (returns, turnovers, short proportions, leverages, asset weights, asset filter)
    """
    validation_freq = config["validation_freq"]
    num_epochs = config["num_epochs"]
    optimizer_name = config["optimizer_name"]
    optimizer_opts = config["optimizer_opts"]
    lookback = config["model"]["lookback"]
    batchsize = config["batch_size"]
    trans_cost = config["trans_cost"]
    hold_cost = config["hold_cost"]
    holding_days = config["holding_days"]
    objective = config["objective"]
        
    if device is None: 
        device = model.device
    parallelize = device == "cuda" and len(device_ids) > 0
    
    # Preprocess data
    # assets_to_trade chooses assets which have at least MIN_LOOKBACK non-missing observations in the training period
    # idxs_selected is backward-looking, and will only select assets with at least MIN_LOOKBACK non-missing obs
    assets_to_trade = compute_residual_filter(data_train)
    data_train = data_train[:,assets_to_trade]
    data_train_tensor = torch.tensor(data_train, device=device)
    if comp_mtx_train is not None: 
        comp_mtx_train = comp_mtx_train[:,assets_to_trade,:]
    T,N = data_train.shape
    logging.info(f"train: T {T} N {N}")
    windows, idxs_selected = preprocess(data_train, lookback, config)
    if config.get("gpu_data", False):
        windows = torch.tensor(windows, device=device)
        idxs_selected = idxs_selected.to(device)
    
    # Start to train
    if parallelize:
        model = nn.DataParallel(model, device_ids=device_ids)
    is_frictions_model = get_model_attr(model, 'is_frictions_model')
    is_vol_signal_model = get_model_attr(model, 'is_vol_signal_model')
    is_trainable = get_model_attr(model, 'is_trainable')
    model.to(device) 
    model.train()
    
    # Only set up optimizer if model is trainable
    if is_trainable:
        optimizer_func = import_string(f"torch.optim.{optimizer_name}")
        optimizer = optimizer_func(model.parameters(), **optimizer_opts)
    else:
        optimizer = None
    
    begin_time = time.time()
    comp_mtx_ts = [
        torch.tensor(comp_mtx_train[lookback+batchsize*i:min(lookback+batchsize*(i+1),T)])
        if comp_mtx_train is not None else None
        for i in range(int((T-lookback)/batchsize)+1)
    ]
    idxs_selected_ts = [
        idxs_selected[batchsize*i:min(batchsize*(i+1),T-lookback),:]
        for i in range(int((T-lookback)/batchsize)+1)
    ]
    windows_ts = [
        windows[batchsize*i:min(batchsize*(i+1),T-lookback)][idxs_selected_ts[i]]
        for i in range(int((T-lookback)/batchsize)+1)
    ]   
    rets_full = torch.zeros(T-lookback, device=device)
    short_proportion = torch.zeros(T-lookback, device=device)
    turnover = torch.zeros(T-lookback, device=device)
    leverage = torch.zeros(T-lookback, device=device)  
    for epoch in range(num_epochs):        
        # Break input data up into batches of size `batchsize` and train over them 
        # This is usually 125 days per batch out of 1000 training days
        for i in range(int((T-lookback)/batchsize)+1):
            weights = torch.zeros( (min(batchsize*(i+1),T-lookback)-batchsize*i, N), device=device)
            if is_frictions_model:
                if epoch == 0: 
                    old_weights = torch.zeros((min(batchsize*(i+1),T-lookback)-batchsize*i,N),device=device)
                else:
                    rseed = model.module.random_seed if parallelize else model.random_seed
                    ow_filepath = os.path.join(output_path, f'Weights{i}-{rseed}_seed_'+ model_tag +'.pt')
                    old_weights = torch.load(ow_filepath, map_location = device)[:-1]
                    old_weights = torch.cat((torch.zeros((1,N),device=device), old_weights),0)
            if epoch == 0 and i == 0:
                logging.info(f"epoch {epoch} batch {i}")
            else:
                if config.get("debug", False):
                    logging.debug(f"epoch {epoch} batch {i}")
            if config.get("debug", False):
                logging.debug("stats: " +\
                    f"idxs_selected.shape {idxs_selected.shape}, " +\
                    f"filtered for batch {i} idxs_selected.shape {idxs_selected[batchsize*i:min(batchsize*(i+1),T-lookback),:].shape}, " +\
                    f"weights.shape {weights.shape}, " +\
                    f"batch period len {min(batchsize*(i+1),T) - batchsize*i}"
                )
                
            # Choose input data
            # idxs of valid residuals to trade in batch i
            idxs_batch_i = idxs_selected_ts[i]
            input_data_batch_i = windows_ts[i]
            if config.get("gpu_data", False):
                input_tensor = input_data_batch_i
            else:
                input_tensor = torch.tensor(input_data_batch_i, device=device)
            
            if config.get("debug", False):
                logging.debug(f"Epoch {epoch} Batch {i} - Input data shape: {input_data_batch_i.shape}, non-zero: {torch.count_nonzero(input_data_batch_i)}")
            
            # Generate weights from model
            if is_frictions_model:
                old_weights_i = old_weights[idxs_selected[batchsize*i:min(batchsize*(i+1),T-lookback),:]]
                weights[idxs_batch_i] = model(input_tensor, old_weights_i)
            elif is_vol_signal_model:
                weights[idxs_batch_i] = model(input_tensor, input_tensor.std(axis=1))
            else:
                weights[idxs_batch_i] = model(input_tensor)
            if config.get("debug", False):
                logging.debug(
                    f"Epoch {epoch} Batch {i} - Post-model weights stats: "
                    f"mean={weights.mean():.4f}, std={weights.std():.4f}, "
                    f"non-zero={torch.count_nonzero(weights)}, any_nan={torch.isnan(weights).any()}, "
                    f"weights.shape {weights.shape}, "
                    f"weights[idxs_batch_i].shape {weights[idxs_batch_i].shape}, "
                    f"idxs_batch_i.shape {idxs_batch_i.shape}"
                )

            # Transform weights
            if comp_mtx_train is not None:
                comp_mtx_t = comp_mtx_ts[i].to(device)
                if config.get("debug", False):
                    logging.debug(f"Epoch {epoch} Batch {i} - Comp matrix shape: {comp_mtx_t.shape}, non-zero: {torch.count_nonzero(comp_mtx_t)}")
            else:
                comp_mtx_t = None
            weights, asset_weights = transform_weights(weights, data_train, comp_mtx_t, config)
            if not config.get("gpu_data", False):
                comp_mtx_ts[i] = comp_mtx_ts[i].cpu()
            if epoch == 0 and i == 0:
                logging.info(f"Epoch {epoch} Batch {i} - asset_weights.shape {asset_weights.shape if asset_weights is not None else 'None'}")
            else:
                if config.get("debug", False):
                    logging.debug(f"Epoch {epoch} Batch {i} - Post-transform weights stats: "
                                f"mean={weights.mean():.4f}, std={weights.std():.4f}, "
                                f"non-zero={torch.count_nonzero(weights)}, any_nan={torch.isnan(weights).any()}, "
                                f"weights.shape {weights.shape}, "
                                f"weights[idxs_batch_i].shape {weights[idxs_batch_i].shape}, "
                                f"idxs_batch_i.shape {idxs_batch_i.shape}, "
                    )
                if asset_weights is not None:
                    if config.get("debug", False):
                        logging.debug(f"Epoch {epoch} Batch {i} - Asset weights stats: mean={asset_weights.mean():.4f}, std={asset_weights.std():.4f}, "
                                    f"non-zero={torch.count_nonzero(asset_weights)}, any_nan={torch.isnan(asset_weights).any()}, "
                                    f"asset_weights.shape {asset_weights.shape}, "
                        )
                
            if holding_days == 1:
                rets_train = torch.sum(weights * data_train_tensor[lookback+batchsize*i:min(lookback+batchsize*(i+1),T),:], axis=1) 
                if config.get("debug", False):
                    logging.debug(f"Epoch {epoch} Batch {i} - Pre-cost returns stats: "
                                f"mean={rets_train.mean():.4f}, std={rets_train.std():.4f}, "
                                f"non-zero={torch.count_nonzero(rets_train)}, any_nan={torch.isnan(rets_train).any()}, "
                                f"rets_train.shape {rets_train.shape}, "
                    )

                # Apply market frictions
                calc_weights = weights if (comp_mtx_train is None) else asset_weights  # (T1, N) or (T1, N2) depending on whether comp_mtx is used
                turnover_tensor = torch.cat((torch.zeros(1, device=device), torch.sum(torch.abs(calc_weights[1:] - calc_weights[:-1]), axis=1)))  # (T1-1,)
                short_positions_tensor = torch.sum(torch.abs(torch.min(calc_weights, torch.zeros(1, device=device))), axis=1)  # (T1,)
                rets_train = rets_train - trans_cost * turnover_tensor - hold_cost * short_positions_tensor  # (T1,)
            else:
                rets_train = get_holding_days_returns(
                    holding_days,
                    weights,
                    asset_weights,
                    data_train_tensor[lookback+batchsize*i:min(lookback+batchsize*(i+1),T),:],
                    trans_cost,
                    hold_cost,
                )
            if config.get("debug", False):
                logging.debug(f"Epoch {epoch} Batch {i} - Post-cost returns stats: "
                            f"mean={rets_train.mean():.4f}, std={rets_train.std():.4f}, "
                            f"non-zero={torch.count_nonzero(rets_train)}, any_nan={torch.isnan(rets_train).any()}, "
                            f"rets_train.shape {rets_train.shape}, "
                )

            loss, _, _, _ = get_loss(rets_train, objective, holding_days)
            
            if is_trainable:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            if is_frictions_model:
                model_seed = model.module.random_seed if parallelize else model.random_seed
                ow_filepath = os.path.join(output_path, f'Weights{i}-{model_seed}_seed_'+ model_tag +'.pt')
                torch.save(weights, ow_filepath)
            
            if epoch % validation_freq == 0:
                with torch.no_grad():
                    if i == 0:
                        rets_full[:] = 0
                        short_proportion[:] = 0
                        turnover[:] = 0
                        leverage[:] = 0
                    weights = weights.detach() if (comp_mtx_train is None) else asset_weights.detach()
                    rets_full[batchsize*i:min(batchsize*(i+1),T-lookback)] = rets_train.detach()
                    # NOTE: turnover and short proportions calculations for holding_days != 1 will be misreported here
                    turnover[batchsize*i:(min(batchsize*(i+1),T-lookback)-1)] = torch.sum(torch.abs(weights[1:]-weights[:-1]), axis=1)
                    turnover[min(batchsize*(i+1),T-lookback)-1] = turnover[min(batchsize*(i+1),T-lookback)-2]  # just to simplify things
                    short_proportion[batchsize*i:min(batchsize*(i+1),T-lookback)] = torch.sum(torch.abs(torch.clamp(weights,min=None,max=0)), axis=1)
                    leverage[batchsize*i:min(batchsize*(i+1),T-lookback)] = torch.sum(torch.abs(weights),axis=1)
        
        if epoch % validation_freq == 0:
            val_loss_description = ""
            if data_val is not None:                    
                (
                    rets_val,
                    val_loss,
                    val_sharpe,
                    val_mean_ret,
                    val_std,
                    val_turnovers,
                    val_short_proportions,
                    val_leverages,
                    weights_val,
                    a2t,
                ) = get_returns(
                    model=model,
                    config=config,
                    preprocess=preprocess,
                    data_test=data_val,
                    device=device,
                    comp_mtx=comp_mtx_val,
                    device_ids=device_ids,
                )
                model.train()
                
                val_turnover  = torch.mean(val_turnovers)
                val_short_proportion = torch.mean(val_short_proportions)
                val_leverage  = torch.mean(val_leverages)
                val_loss_description =  '      ' \
                                    f"val   Sharpe: {val_sharpe:0.2f}, " \
                                    f"ret: {val_mean_ret:0.4f}, " \
                                    f"std: {val_std:0.4f}, " \
                                    f"turnover: {val_turnover:0.3f}, " \
                                    f"short proportion: {val_short_proportion:0.3f}, " \
                                    f"leverage: {val_leverage:0.3f}, " \
                                    f"val loss {val_loss:0.2f}\n"
            else:
                val_loss_description = ''
                logging.info("No validation data provided; computing stats using full data")
            
            with torch.no_grad():
                full_ret, full_std, full_sharpe = compute_stats(rets_full, holding_days)
                full_turnover = torch.mean(turnover)
                full_short_proportion = torch.mean(short_proportion)
                full_leverage = torch.mean(leverage)
            
            logging.info(
                f"Epoch: {epoch}/{num_epochs}, Subperiod: {(subperiod + 1)}/{num_total_subperiods}, "
                f"Time per epoch: {(time.time() - begin_time) / (epoch + 1):0.2f}s \n"
                "      "
                f"train Sharpe: {full_sharpe:0.2f}, "
                f"ret: {full_ret:0.4f}, "
                f"std: {full_std:0.4f}, "
                f"turnover: {full_turnover:0.3f}, "
                f"short proportion: {full_short_proportion:0.3f}, "
                f"leverage: {full_leverage:0.3f} \n" + val_loss_description
            )
                                
    if save_params:
        # NOTE: can also save model.state_dict() directly w/o the dictionary; extension should then be .pth instead of .tar
        # there are also more modern ways to save models in PyTorch
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
        } 
        if optimizer is not None:
            checkpoint['optimizer_state_dict'] = optimizer.state_dict()
            checkpoint['loss'] = loss
            
        checkpoint_fname = f'Checkpoint-{model.module.random_seed if parallelize else model.random_seed}_seed_'+model_tag+'.tar'
        torch.save(checkpoint, os.path.join(output_path, checkpoint_fname))
        logging.info(f'Checkpoint saved to {os.path.join(output_path, checkpoint_fname)}')
                                                                        
    logging.info(f'Training done - Model: {model_tag}, seed: {model.module.random_seed if parallelize else model.random_seed}')             
    if data_val is not None:
        return rets_val, val_turnovers, val_short_proportions, val_leverages, weights_val, a2t
    else:
        return rets_full, turnover, short_proportion, leverage, weights, assets_to_trade


def b_sharpe(x: torch.Tensor, b: int):
    """
    Computes the Sharpe ratio of a series of returns over B days.
    """
    return torch.sqrt(torch.tensor(252/b)) * torch.mean(x, axis=0) / torch.std(x, axis=0)


def b_ret(x: torch.Tensor, b: int):
    """
    Computes the average return of a series of returns over B days.
    """
    return 252/b * torch.mean(x, axis=0)


def b_std(x: torch.Tensor, b: int):
    """
    Computes the standard deviation of a series of returns over B days.
    """
    return torch.sqrt(torch.tensor(252/b)) * torch.std(x, axis=0)


def b_stat(x: torch.Tensor, B: int, b_stat_func: Callable):
    """
    Computes an average of a statistic function `b_stat_func` over B days.

    Args:
        x (torch.Tensor): Returns.
        B (int): Number of holding days.
        b_stat_func (Callable): Statistic function.

    Returns:
        torch.Tensor: Average of the statistic function over B days.
    """
    stats_b = torch.zeros(B)
    for t in range(B):
        stats_b[t] = b_stat_func(x[t::B], B)
    return torch.mean(stats_b)


def compute_stats(rets: torch.Tensor, holding_days: int):
    """
    Compute the mean, standard deviation, and Sharpe ratio of returns.
    
    Args:
        rets (torch.Tensor): Returns.
        holding_days (int): Number of holding days.
        
    Returns:
        Tuple[float, float, float]: Mean return, standard deviation of returns, and Sharpe ratio.
    """
    eps = 1e-8  # Small epsilon to avoid division by zero
    if holding_days == 1:
        mean = torch.mean(rets) * 252
        std = torch.std(rets) * torch.sqrt(torch.tensor(252))
        if std == 0:
            logging.warning("std = 0 in compute_stats()")
        std = std + eps
        sharpe = mean/std
    else:
        mean = b_stat(rets * holding_days, holding_days, b_ret)
        std = b_stat(rets * holding_days, holding_days, b_std)
        if std == 0:
            logging.warning("std = 0 in compute_stats()")
        std = std + eps
        sharpe = b_stat(rets * holding_days, holding_days, b_sharpe)
    return mean, std, sharpe


def get_loss(rets: torch.Tensor, objective: str, holding_days: int):
    """
    Compute the loss based on the objective function.
    
    Args:
        rets (torch.Tensor): Returns.
        objective (str): Objective function name.
        holding_days (int): Number of holding days.
        
    Returns:
        Tuple[torch.Tensor, float, float, float]: Loss, mean return, standard deviation of returns, and Sharpe ratio.
    """
    mean, std, sharpe = compute_stats(rets, holding_days)
    risk = std
    if objective.lower() == "sharpe":
        loss = -sharpe
    elif objective.lower() == "meanvar":
        loss = -(mean - risk)
    else:
        raise Exception(f"Invalid objective loss {objective}")
    return loss, mean, std, sharpe


def get_holding_days_returns(
    holding_days: int,
    weights: torch.Tensor,
    asset_weights: torch.Tensor,
    returns: torch.Tensor,
    trans_cost: int,
    hold_cost: int,
):
    """
    Calculate the returns for a given number of holding days.
    
    Args:
        holding_days (int): Number of holding days.
        weights (torch.Tensor): Weights for the assets.
        asset_weights (torch.Tensor): Asset weights.
        returns (torch.Tensor): Returns for the assets.
        trans_cost (float): Transaction cost.
        hold_cost (float): Holding cost.
        
    Returns:
        torch.Tensor: Returns for the given number of holding days.
    """
    B = holding_days
    T1 = len(returns)
    rets = torch.zeros(T1)
    for t in range(B,T1):
        b_day_weights = weights[t-B+1:t-B+2,:].expand(B,-1)
        b_day_asset_returns = returns[t-B+1:t+1]
        b_day_ret = torch.sum(b_day_weights * b_day_asset_returns, axis=1)
        cost = 0
        if trans_cost > 0 or hold_cost > 0:
            if t < B:
                if asset_weights is None:
                    turnover = torch.sum(torch.abs(weights[t,:]))
                else:
                    turnover = torch.sum(torch.abs(asset_weights[t,:]))
            else:
                if asset_weights is None:
                    turnover = torch.sum(torch.abs(weights[t,:] - weights[t-B,:]))
                else:
                    turnover = torch.sum(torch.abs(asset_weights[t,:] - asset_weights[t-B,:]))
            if asset_weights is None:
                short = torch.sum(torch.abs(weights[t,weights[t,:] < 0]))
            else:
                short = torch.sum(torch.abs(asset_weights[t,asset_weights[t,:] < 0]))
            cost = trans_cost*turnover + hold_cost*short
        rets[t] = (torch.cumprod(1 + b_day_ret, dim=0)[-1] - 1) - cost
    rets /= B
    return rets


def get_returns(
    model: nn.Module,
    config: dict,
    preprocess: Callable,
    data_test: np.ndarray,
    comp_mtx: Optional[np.ndarray],
    device: Optional[str],
    device_ids: List[int],
    load_model_tag: Optional[str] = None,
    load_model_dir: Optional[str] = None,
    ensemble: bool = False,
) -> Tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    np.ndarray,
]:
    """
    Get returns for a model on test data.

    Args:
        model (nn.Module): The model to test
        config (dict): Configuration dictionary
        preprocess (function): a function that selects and preprocesses data from preprocessing.py
        data_test (np.ndarray): Test data
        comp_mtx (Optional[np.ndarray]): Composition matrix
        device (Optional[str]): Device to run on
        device_ids (List[int]): GPU device IDs to use
        load_model_tag (Optional[str]): Model tag; defines filename to load model parameters from
        load_model_dir (Optional[str]): Directory to load model parameter files from
        ensemble (bool): True to use an ensemble of available models when loading parameters (otherwise, use latest model)

    Returns:
        Tuple[
            torch.Tensor, 
            torch.Tensor, 
            torch.Tensor,
            torch.Tensor,
            torch.Tensor,
            torch.Tensor, 
            torch.Tensor, 
            torch.Tensor,
            torch.Tensor,
            np.ndarray
        ]: Tuple of (
            returns, 
            loss, 
            sharpe, 
            mean, 
            std, 
            asset weights, 
            turnovers, 
            short proportions, 
            leverages, 
            asset filter
        )
    """
    objective = config["objective"]
    lookback = config["model"]["lookback"]
    trans_cost = config["trans_cost"]
    hold_cost = config["hold_cost"]
    holding_days = config["holding_days"]
    parallelize = device == "cuda" and len(device_ids) > 0
    checkpoint_filepaths = []

    if load_model_tag is not None:
        # Construct checkpoint path based on load_model_tag
        model_dir = load_model_dir if load_model_dir is not None else config["output_dir"]
        checkpoint_pattern = "Checkpoint-*_seed_" + load_model_tag + ".tar"
        checkpoint_pattern = os.path.join(model_dir, checkpoint_pattern)
        # Find matching checkpoint files
        logging.info(f"Attempting to find models like: {checkpoint_pattern}")
        matching_files = glob.glob(checkpoint_pattern)
        if len(matching_files) == 0:
            raise ValueError(f"No checkpoint files found matching pattern '{checkpoint_pattern}'")
        elif len(matching_files) == 1:
            checkpoint_filepaths = [matching_files[0]]
            logging.info(f"Will load model from checkpoint: {checkpoint_filepaths[0]}")
        elif len(matching_files) > 1:
            if not ensemble:
                logging.warning(f"Multiple checkpoint files found matching '{checkpoint_pattern}', but ensemble is False; using most recent")
                matching_files.sort(key=os.path.getmtime, reverse=True)
                checkpoint_filepaths = [matching_files[0]]
                logging.info(f"Will load model from checkpoint: {checkpoint_filepaths[0]}")
            else:
                logging.info(f"Multiple checkpoint files found matching '{checkpoint_pattern}', using all in ensemble")
                matching_files.sort(key=os.path.getmtime, reverse=True)
                checkpoint_filepaths = matching_files
                logging.info(f"Will load models from checkpoints: \n{checkpoint_filepaths}")
    
    if device is None: 
        device = model.device
    if parallelize: 
        model = nn.DataParallel(model, device_ids=device_ids).to(device)
    is_frictions_model = get_model_attr(model, "is_frictions_model")
    is_vol_signal_model = get_model_attr(model, "is_vol_signal_model")
    is_trainable = get_model_attr(model, "is_trainable")
    
    # Can choose to apply the residual selection filter here to improve performance, but 
    # we just choose all residuals to assure readers there is no lookahead bias in the test.
    assets_to_trade = np.ones(data_test.shape[1], dtype=bool)
    data_test = data_test[:,assets_to_trade]
    if comp_mtx is not None:
        comp_mtx = comp_mtx[:,assets_to_trade]
    T,N = data_test.shape
    
    windows, idxs_selected = preprocess(data_test, lookback, config)
    
    rets_test = torch.zeros(T-lookback)
    weights = torch.zeros((T-lookback,N),device=device)
    model.eval()
    
    def load_and_predict(model, inputs, additional_input=None, checkpoint_filepaths=None, load_model_tag=None, device='cpu'):
        """
        Helper function to load model checkpoints and make predictions with consistent handling across model types.
        
        Note:
            N_selected is the number of assets selected by idxs_selected mask
            When checkpoint_filepaths is provided, predictions from each checkpoint are summed
        
        Args:
            model (nn.Module): The PyTorch model to use for predictions
            inputs (torch.Tensor): Input tensor, e.g. with shape (N_selected, lookback) containing cumulative sums of returns
            additional_input (torch.Tensor, optional): Additional input tensor with shape depending on model type:
                - Frictions model: (N_selected,) previous weights
                - Vol signal model: (N_selected,) standard deviation of inputs
                - Normal model: Not used (None)
            checkpoint_filepaths (List[str], optional): List of checkpoint files to load and ensemble.
                If provided, predictions from each checkpoint are averaged.
            load_model_tag (str, optional): Tag to use when loading model checkpoints
            device (str): Device to run model on (e.g. 'cpu' or 'cuda' or 'cuda:0' etc.)
        
        Returns:
            torch.Tensor: Predicted weights with shape (N_selected,)
        """
        if not checkpoint_filepaths:
            return model(inputs) if additional_input is None else model(inputs, additional_input)
        weights = None
        for checkpoint_path in checkpoint_filepaths:
            if load_model_tag is not None:
                load_model_from_checkpoint(model, checkpoint_path, device)
                logging.info(f"Loaded model from checkpoint: {checkpoint_path}")
            pred = model(inputs) if additional_input is None else model(inputs, additional_input)
            weights = pred if weights is None else weights + pred
        return weights
    
    with torch.no_grad(): 
        if is_frictions_model:
            logging.info("Using frictions model")
            # Perform sequential computation of weights because we need old_weights at each time step
            for t in range(lookback,T):
                idxs_selected = ~np.any(data_test[(t - lookback):t, :] == 0, axis=0).ravel()
                old_weights = torch.zeros(N, device=device) if t == lookback else weights[t-lookback-1]
                inputs = np.cumsum(data_test[(t - lookback):t, idxs_selected], axis=0).T  # (N,T)
                inputs = torch.tensor(inputs, device=device)
                weights[t-lookback,idxs_selected] = load_and_predict(model, inputs, old_weights[idxs_selected], checkpoint_filepaths, load_model_tag, device)
        elif is_vol_signal_model:
            # This was implemented at the request of a reviewer and adds the standard deviation of the inputs as additional features
            logging.info("Using vol signal model")
            inputs = torch.tensor(windows[idxs_selected], device=device)
            std_data = inputs.std(axis=1)
            weights[idxs_selected] = load_and_predict(model, inputs, std_data, checkpoint_filepaths, load_model_tag, device)
        else:
            # Regular model with no additional input
            inputs = torch.tensor(windows[idxs_selected], device=device)
            weights[idxs_selected] = load_and_predict(model, inputs, None, checkpoint_filepaths, load_model_tag, device)
        
        if len(checkpoint_filepaths) > 1:
            weights /= len(checkpoint_filepaths)
        if comp_mtx is not None:
            comp_mtx_t = torch.tensor(comp_mtx[lookback:T,:,:], device=device)
        else:
            comp_mtx_t = None
        weights, asset_weights = transform_weights(weights, data_test, comp_mtx_t, config)

        if holding_days == 1:
            rets_test = torch.sum(weights * torch.tensor(data_test[lookback:T,:], device=device), axis=1)
        else:
            rets_test = get_holding_days_returns(holding_days, weights, asset_weights,
                                                 torch.tensor(data_test[lookback:T,:],device=device),
                                                 trans_cost, hold_cost)
        if comp_mtx is not None:
            weights = asset_weights
        turnover = torch.cat((torch.zeros(1,device=device),torch.sum(torch.abs(weights[1:]-weights[:-1]),axis=1)))
        short_proportion = torch.sum(torch.abs(torch.min(weights,torch.zeros(1,device=device))),axis=1)
        leverage = torch.sum(torch.abs(weights),axis=1)
        if holding_days == 1:
            rets_test = rets_test - trans_cost*turnover - hold_cost*short_proportion
        turnover[0] = torch.mean(turnover[1:])
        loss, mean, std, sharpe = get_loss(rets_test, objective, holding_days)
    return (
        rets_test,
        loss, 
        sharpe, 
        mean, 
        std, 
        turnover, 
        short_proportion, 
        leverage,
        weights, 
        assets_to_trade,
    )


def load_model_from_checkpoint(
    model: nn.Module, checkpoint_path: str, device: str
) -> None:
    """
    Load model weights from a checkpoint, handling DataParallel and non-DataParallel cases.
    
    Args:
        model (nn.Module): The model to load weights into
        checkpoint_path (str): Path to the checkpoint file
        device (str): Device to load the model onto
        
    Returns:
        None. Model is updated with loaded weights.
    """
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    state_dict = checkpoint['model_state_dict']
    
    # Check if current model is DataParallel
    is_data_parallel = isinstance(model, torch.nn.DataParallel)
    # Check if saved model was DataParallel
    has_module = any(k.startswith("module.") for k in state_dict.keys())

    if has_module and not is_data_parallel:
        # If saved model was DataParallel but current model is not
        new_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
    elif not has_module and is_data_parallel:
        # If saved model was not DataParallel but current model is
        new_state_dict = {f"module.{k}": v for k, v in state_dict.items()}
    else:
        # Both are DataParallel or both are not
        new_state_dict = state_dict
    
    model.load_state_dict(new_state_dict)
    model.to(device)
    model.eval()


def set_up_data(
    data: np.ndarray, 
    config: dict,
    model_tag: str, 
    comp_mtx: Optional[np.ndarray],
):
    """
    Validate settings, filter assets, and set up data for simulation.
    
    Args:
        data (np.ndarray): Residual data, a 2D array of size (T, N) where T is the number of time periods (days) and N is the number of residuals
        config (dict): Configuration dictionary
        model_tag (str): Model tag, a string indicating the model type and other relevant information
        comp_mtx (Optional[np.ndarray]): Composition matrix, a 3D array of size (T, N, N') where T is the number of time periods, 
                                         N is the number of residuals, and N' is the number of underlying assets
    
    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
            Tuple of empty arrays (returns, loss, sharpe, mean, std, turnover, short_proportion, leverage, weights, assets_to_trade)
    """
    length_training = config['length_training']
    cap_proportion = config['cap_proportion']
    residuals_dir = config['residuals_dir']
    ipca_dir = config['factor_model_settings']['IPCA']['directory']
    pca_dir = config['factor_model_settings']['PCA']['directory']
    ff_dir = config['factor_model_settings']['FamaFrench']['directory']
    initial_oos_year = config['start_date'][:4]
    lookback = config['model']['lookback']
    assert lookback >= MINIMUM_LOOKBACK, f"`lookback` must be at least {MINIMUM_LOOKBACK}"

    if "IPCA" in model_tag:
        factor_model_dir = ipca_dir
    elif "PCA" in model_tag:
        factor_model_dir = pca_dir
    elif "FamaFrench" in model_tag:
        factor_model_dir = ff_dir
    else:
        raise ValueError(f"Unknown factor model in model tag: {model_tag}")
    
    residuals_to_consider = compute_residual_filter(data)
    
    filter_assets = False
    if residuals_to_consider.sum() == comp_mtx.shape[1]:
        logging.info("Using pre-filtered composition matrix")
        data = data[:,residuals_to_consider]
    elif residuals_to_consider.sum() < comp_mtx.shape[1]:
        filter_assets = True
        filter_filepath = os.path.join(residuals_dir, factor_model_dir, f"assets-to-consider_{initial_oos_year}_initialOOSYear_{cap_proportion}_cap.npy")
        alt_filter_filepath = os.path.join(residuals_dir, factor_model_dir, f"assets-to-consider_{initial_oos_year}_initialOOSYear_{cap_proportion}_Cap.npy")
        if os.path.exists(filter_filepath):
            logging.info("Loading asset filter")
            fm_assets_to_consider = np.load(filter_filepath)
        elif os.path.exists(alt_filter_filepath):
            logging.info("Loading asset filter")
            fm_assets_to_consider = np.load(alt_filter_filepath)
        else:
            raise ValueError(
                f"No file found for assets filter at '{filter_filepath}' or '{alt_filter_filepath}'; "
                "make sure factor model has been run properly (check the residuals directory and factor model configs)"
            )
        if config.get("disable_prefilter", False):
            residuals_to_consider = fm_assets_to_consider
        data = data[:,residuals_to_consider]
        logging.info("Processing composition matrix")
        if comp_mtx is not None:
            if config.get("disable_prefilter", False):
                # If prefiltering is disabled, use all residuals in the composition matrix
                pass
            else:
                prefilter = residuals_to_consider[fm_assets_to_consider]
                comp_mtx = comp_mtx[:,prefilter,:]
    else: 
        raise ValueError("Number of residuals to consider is greater than the number of residuals in the composition matrix; this should not happen")

    T, N = data.shape
    initial_t = config['initial_t']
    length_testing = T - length_training - initial_t

    returns = np.zeros(length_testing)
    turnovers = np.zeros(length_testing)
    short_proportions = np.zeros(length_testing)
    leverages = np.zeros(length_testing)

    # Select assets to consider
    if comp_mtx is not None and 'FamaFrench' in model_tag:
        # Select fama-french factors as part of assets to consider
        n_ff_factor_assets = comp_mtx.shape[2] - residuals_to_consider.sum()
        if n_ff_factor_assets > 0:
            all_weights = np.zeros((length_testing, len(residuals_to_consider) + n_ff_factor_assets))
            assets_to_consider = np.append(residuals_to_consider, np.ones(n_ff_factor_assets, dtype=np.bool))
        else:
            all_weights = np.zeros((length_testing, len(residuals_to_consider)))
            assets_to_consider = residuals_to_consider
    elif comp_mtx is not None and 'IPCA' in model_tag:
        # For IPCA, we use the super mask to select assets
        # this is the same as the fm_assets_to_consider for the residual model and only separate for convenience
        ipca_a2c_path = os.path.join(residuals_dir, ipca_dir, f'super_mask_{cap_proportion}.npy')
        assets_to_consider = np.load(ipca_a2c_path)
        all_weights = np.zeros((length_testing, len(assets_to_consider)))
    elif comp_mtx is not None and 'PCA' in model_tag and 'IPCA' not in model_tag:
        assets_to_consider = residuals_to_consider
        if filter_assets:
            filter_assets_in_comp_mtx = config.get('filter_assets_in_comp_mtx', True)
            if filter_assets_in_comp_mtx:
                comp_mtx = comp_mtx[:,:,assets_to_consider[fm_assets_to_consider]]
                all_weights = np.zeros((length_testing, assets_to_consider[fm_assets_to_consider].sum()))
            else:
                logging.info("Not filtering assets in composition matrix")
                assets_to_consider = fm_assets_to_consider
                assert fm_assets_to_consider.sum() == comp_mtx.shape[2]
                all_weights = np.zeros((length_testing, len(assets_to_consider)))
        else:
            all_weights = np.zeros((length_testing, len(assets_to_consider)))
    elif comp_mtx is None:
        assets_to_consider = residuals_to_consider
        all_weights = np.zeros((length_testing, len(assets_to_consider)))
    else:
        raise ValueError("Composition matrix is not None, but model tag is not recognized")

    return data, comp_mtx, assets_to_consider, returns, turnovers, short_proportions, leverages, all_weights


def process_and_save_output(
    returns: np.ndarray,
    all_weights: np.ndarray,
    turnovers: np.ndarray,
    short_proportions: np.ndarray,
    leverages: np.ndarray,
    holding_days: int, 
    daily_dates: np.ndarray,
    output_path: str, 
    model_tag: str, ):
    """
    Compute and save stats and plots describing the performance of the model.
    
    Args:
        returns (np.ndarray): Returns
        all_weights (np.ndarray): Weights
        turnovers (np.ndarray): Turnover
        short_proportions (np.ndarray): Short proportions
        leverages (np.ndarray): Leverages
        holding_days (int): Holding days
        daily_dates (np.ndarray): Daily dates
        output_path (str): Output path
        model_tag (str): Model tag
    
    Returns:
        None, but saves performance statistics and plots to output_path
    """
    cumulative_rets = np.cumprod(1 + returns)

    np.save(os.path.join(output_path, "WeightsComplete_" + model_tag + ".npy"), all_weights)
    
    full_ret, full_std, full_sharpe = compute_stats(torch.tensor(returns), holding_days)
    
    logging.info(
        f"==> Sharpe: {full_sharpe:.2f}, "\
        f"ret: {full_ret:.4f}, "\
        f"std: {full_std:.4f}, "\
        f"turnover: {np.mean(turnovers) :.4f}, "\
        f"short_proportion: {np.mean(short_proportions) :.4f}, "\
        f"leverage: {np.mean(leverages):.4f}"
    )
    
    try:
        plt.figure()
        plt.plot(daily_dates[-len(cumulative_rets):], cumulative_rets)
        plt.savefig(os.path.join(output_path, model_tag + "_cumulative-returns.png"))
        plt.close()
    
        plt.figure()
        plt.plot(daily_dates[-len(cumulative_rets):], turnovers)
        plt.savefig(os.path.join(output_path, model_tag + "_turnover.png"))
        plt.close()         
    
        plt.figure()
        plt.plot(daily_dates[-len(cumulative_rets):], short_proportions)
        plt.savefig(os.path.join(output_path, model_tag + "_short-proportion.png"))
        plt.close()
    
        plt.figure()
        plt.plot(daily_dates[-len(cumulative_rets):], leverages)
        plt.savefig(os.path.join(output_path, model_tag + "_leverage.png"))
        plt.close()
    except Exception as exc:
        logging.warning("Tried to plot but failed. Details:", exc_info=exc)
    
    performance_stats = {
        "dates": daily_dates[-len(cumulative_rets):],
        "returns": returns,
        "sharpe": full_sharpe,
        "ret": full_ret,
        "std": full_std,
        "turnover": turnovers,
        "short_proportion": short_proportions,
        "leverage": leverages,
    }        
    return performance_stats


def simulate(
    data: np.ndarray, 
    daily_dates: np.ndarray,
    model: nn.Module,
    preprocess: Callable,
    config: Dict[str, Any],
    output_path: str, 
    model_tag: str,
    comp_mtx: Optional[np.ndarray],
    save_params: bool,
    device: str,
    device_ids: List[int],
    factor_model_name: str,
    num_factors: int,) -> Dict[str, Any]:
    """
    Perform simulated trading via rolling training and testing of a model.
    
    Args:
        data (np.ndarray): Input data
        daily_dates (np.ndarray): Array of dates
        model (Any): Model class to use
        preprocess (Callable): a function that selects and preprocesses data from preprocessing.py
        config (Dict[str, Any]): Configuration dictionary
        output_path (str): Path to save outputs
        model_tag (str): Tag for model identification
        comp_mtx (np.ndarray): Composition matrix
        save_params (bool): Whether to save model parameters
        device (str): Device to run on
        device_ids (List[int]): GPU device IDs to use
        
    Returns:
        Dict[str, Any]: Dictionary containing performance statistics
    """
    # Extract parameters from config
    lookback = config["model"]["lookback"]
    length_training = config["length_training"]
    stride = config["stride"]
    holding_days = config["holding_days"]
    mode = config.get("mode", "train").lower()
    assert mode in ["train", "test"], (
        f"Mode must be 'train' or 'test'; got mode='{mode}'"
    )
    
    data, comp_mtx, assets_to_consider, returns, turnovers, short_proportions, leverages, all_weights = set_up_data(
        data=data, 
        config=config, 
        model_tag=model_tag,
        comp_mtx=comp_mtx,
    )
    T,N = data.shape
    
    # Run train/test over dataset
    initial_t = int(config["initial_t"])
    if initial_t != 0:
        logging.info(f"Starting from initial_t={initial_t}")
    
    old_model_t = None
    num_subperiods = int((T-length_training)/stride)+1
    for t in range(initial_t, num_subperiods):
        start_date = daily_dates[t*stride]
        end_date = daily_dates[length_training+t*stride]
        logging.info(f'At subperiod {t+1}/{num_subperiods} (t={t}, start_date={start_date}, end_date={end_date})')
        data_train_t = data[t*stride:length_training+t*stride]
        data_test_t = data[length_training+t*stride-lookback:min(length_training+(t+1)*stride,T)]
        comp_mtx_train_t = (None if comp_mtx is None
                            else comp_mtx[t*stride:length_training+t*stride])
        comp_mtx_test_t = (None if comp_mtx is None 
                           else comp_mtx[length_training+t*stride-lookback:min(length_training+(t+1)*stride,T)])
        model_tag_t = model_tag + f"__subperiod{t}"
        model_t = model(**config["model"])
        is_trainable = get_model_attr(model_t, "is_trainable")
        test_mode = mode == "test"

        if is_trainable and (not test_mode) and (config.get("rolling_retrain", True) or t == 0):
            logging.info("Running training for subperiod")
            rets_t,turns_t,shorts_t,levs_t,weights_t,a2t = train(
                model = model_t,
                config = config,
                preprocess = preprocess,
                data_train = data_train_t, 
                data_val = data_test_t,  # val dataset isn't used, so test dataset goes here for progress reporting
                comp_mtx_train = comp_mtx_train_t, 
                comp_mtx_val = comp_mtx_test_t,  # val dataset isn't used, so test dataset goes here for progress reporting
                save_params = save_params, 
                output_path = output_path, 
                model_tag = model_tag_t,
                device = device, 
                device_ids = device_ids,
                subperiod = t,
                num_total_subperiods = num_subperiods,
            )
            logging.info("train() completed")
        else:
            if test_mode:
                logging.info("Running test in test mode for subperiod")
                # Check if test_model section is in config
                if 'test_model' not in config:
                    raise ValueError("test_model section must be specified in config if in test mode")
                load_log_tag = config['test_model'].get('log_tag')
                if load_log_tag is None:
                    raise ValueError("test_model.log_tag must be specified in config when in test mode"
                                     " (also, results_tag and factor_model_tag must match those of saved model)")
                load_subperiod_start = config['test_model'].get('subperiod_start')
                load_subperiod_end = config['test_model'].get('subperiod_end')
                if (load_subperiod_start is None 
                    or load_subperiod_end is None 
                    or load_subperiod_start < 0 
                    or load_subperiod_end < 0
                    or load_subperiod_start > load_subperiod_end):
                    raise ValueError("test_model.subperiod_start and test_model.subperiod_end must be present, non-negative, and start <= end")
                # Load subperiod which corresponds to t, or latest subperiod available according to start and end
                load_subperiod = min(t, load_subperiod_end)
                load_model_tag = get_model_tag(config, factor_model_name, num_factors, load_log_tag, load_subperiod)
                load_model_dir = config['test_model'].get('trained_model_dir', output_path)
            else:
                load_model_tag = None
                load_model_dir = None
                logging.info("Running test for subperiod using constant model")
                if old_model_t is not None:
                    model_t = old_model_t
                else:
                    if is_trainable:
                        raise ValueError("Model is trainable but no old model is available; cannot run test")
                    else:
                        model_t = model(**config["model"])
            rets_t,loss,sharpe,mean,std,turns_t,shorts_t,levs_t,weights_t,a2t = get_returns(
                model=model_t,
                config=config,
                preprocess=preprocess,
                data_test=data_test_t,
                comp_mtx=comp_mtx_test_t,
                device=device,
                device_ids=device_ids,
                load_model_tag=load_model_tag,
                load_model_dir=load_model_dir,
            )
            logging.info(
                f"==> Performance Metrics: Loss: {loss:.2f}, Sharpe: {sharpe:.2f}, Mean: {mean * 100:.1f}%, Std: {std * 100:.1f}%"
            )

        # Copy model_t into the old model
        old_model_t = model_t
        
        returns[t*stride:min((t+1)*stride, T-length_training)] = rets_t.cpu().numpy()
        turnovers[t*stride:min((t+1)*stride, T-length_training)] = turns_t.cpu().numpy()
        short_proportions[t*stride:min((t+1)*stride, T-length_training)] = shorts_t.cpu().numpy()
        leverages[t*stride:min((t+1)*stride, T-length_training)] = levs_t.cpu().numpy()
        if comp_mtx is None:
            w = np.zeros((min((t+1)*stride, T-length_training) - t*stride, len(a2t)))
            w[:,a2t] = weights_t.cpu().numpy()
        else:
            w = weights_t.cpu().numpy()
        
        all_weights[t*stride:min((t+1)*stride,T-length_training), assets_to_consider] = w

    if 'cpu' not in device:
        with torch.cuda.device(device):
            torch.cuda.empty_cache() 
        
    logging.info(f'Simulation complete for: {model_tag}')
    
    performance_stats = process_and_save_output(
        returns=returns,
        all_weights=all_weights,
        turnovers=turnovers,
        short_proportions=short_proportions,
        leverages=leverages,
        holding_days=holding_days,
        daily_dates=daily_dates,
        output_path=output_path,
        model_tag=model_tag,
    )
    return performance_stats
