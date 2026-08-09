import argparse
import datetime
import json
import logging
import gzip
import os
import pickle
import shutil
import socket
import time
from typing import List, Tuple, Optional, Dict, Any

import petname
import numpy as np
import pandas as pd
import torch
from tabulate import tabulate

from simulation import simulate
from data import perturb
from preprocessing import *
from models import *
from utils import (
    get_git_info, 
    initialize_logging, 
    nploadp, 
    import_string, 
    get_all_free_gpu_ids, 
    send_twilio_message, 
    send_telegram_message,
    add_config_to_args,
    get_model_tag,
    FAMA_FRENCH_5_FACTORS_FILENAME,
    FAMA_FRENCH_5_FACTORS_URL,
)
    

def configure_logging(
    app_name: str, 
    run_id: str = None, 
    logdir: str = "logs", 
    debug: bool = False,
) -> Tuple[str, str, str, str]:
    """
    Configure logging for the application.

    Args:
        app_name (str): Name of the application
        run_id (str, optional): Run ID. Defaults to None.
        logdir (str, optional): Log directory. Defaults to "logs".
        debug (bool, optional): Debug mode. Defaults to False.

    Returns:
        Tuple[str, str, str, str]: Tuple of username, hostname, log tag, and start time string
    """
    debugtag = "-debug" if debug else ""
    run_id = str(run_id)
    username = os.path.split(os.path.expanduser("~"))[-1]
    hostname = socket.gethostname().replace(".stanford.edu","")
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    starttimestr = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logtag = petname.Generate(2)
    # make handlers
    fh = logging.FileHandler(f"{logdir}/{app_name}{debugtag}_{run_id}_{logtag}_{username}_{hostname}_{starttimestr}.log")
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter(f"[%(asctime)s] Run-{run_id} - %(levelname)s - %(message)s", '%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logging.getLogger("").handlers = []
    logging.getLogger("").addHandler(fh)
    logging.getLogger("").addHandler(ch)
    logging.info("STARTED LOGGING FROM CHILD")
    return username, hostname, logtag, starttimestr


def choose_device_configuration(
    gpu_device_ids: List[int], 
    config: Dict[str, Any], 
    use_comp_mtx: bool
) -> Tuple[List[int], str]:
    """
    Estimate number of GPUs needed for training and parse the given device IDs into a list of GPU device IDs and a device string.

    Args:
        gpu_device_ids (List[int]): List of GPU device IDs
        config (dict): Configuration dictionary
        use_comp_mtx (bool): Whether to use a composition matrix (should always be True unless debugging)

    Returns:
        Tuple[List[int], str]: Tuple of list of GPU device IDs and device string
    """
    if gpu_device_ids is None:
        if   config["model"]["lookback"] == 30 and config["length_training"] == 1000:
            num_gpus_needed = 3
        elif config["model"]["lookback"] == 30 and config["length_training"] >= 2000:
            num_gpus_needed = 3
        elif config["model"]["lookback"] == 60 and config["length_training"] == 1000:
            num_gpus_needed = 4
        else:
            logging.error("Unknown context for estimating number of GPUs needed for training")
            num_gpus_needed = int(input("Enter number of GPUs needed for model (integer):"))
            logging.info(f"User entered '{num_gpus_needed}' GPUs needed for this model's training")
        if not use_comp_mtx:
            num_gpus_needed -= 1
        # the base model needs at least 9000 MB of GPU memory per GPU
        device_ids = get_all_free_gpu_ids(min_memory_mb=9000)[:num_gpus_needed]
        if len(device_ids) == 0:
            logging.error("No GPUs available for training!")
            exit(1)
        device = f'cuda:{device_ids[0]}'
        logging.info(f"Running on found GPU device IDs {device_ids}")
    else:
        if gpu_device_ids == [] or "cpu" in gpu_device_ids:
            device = "cpu"
            device_ids = []
            logging.info("Running on CPU")
        else:
            device = f"cuda:{gpu_device_ids[0]}"
            device_ids = gpu_device_ids
            logging.info(f"Running on given GPU device IDs {device_ids}")
    return device_ids, device


def get_factor_models(
    config: Dict[str, Any], 
    factor_model_tagstr: str
) -> Tuple[List[str], List[str], List[str], List[str], Optional[int]]:
    """
    Assemble factor model metadata for train/test.

    Args:
        config (dict): Configuration dictionary
        factor_model_tagstr (str): String representing the factor model tag

    Returns:
        Tuple[List[str], List[str], List[str], List[str], Optional[int]]: 
            list of
            - factor model residual data filepaths, 
            - factor model names, 
            - number of factors, 
            - factor composition matrix filepaths, 
            - (optional) date to start testing.
    """

    cap = config["cap_proportion"]
    residuals_dir = config["residuals_dir"]
    factor_config = config["factor_model_settings"]
    factor_models = config["factor_models"]

    filepaths = []
    comp_mtx_filepaths = []
    factor_model_names = []
    num_factors = []

    if "IPCA" in factor_models and len(factor_models["IPCA"]) > 0:
        ipca_dir = factor_config["IPCA"]["directory"]
        ipca_rtag = factor_config["IPCA"]["residual_tag"]
        ipca_mtag = factor_config["IPCA"]["comp_mtx_tag"]
        im = factor_config["IPCA"]["initial_months"]
        w = factor_config["IPCA"]["window_size"]
        start_year = int(config["start_date"][:4])
        end_year = int(config["end_date"][:4])

        for factor in factor_models["IPCA"]:
            residual_filepath = os.path.join(
                residuals_dir,
                ipca_dir,
                f"{ipca_rtag}_{factor}_factors_{im}_initialMonths_{w}_window_{cap}_cap{factor_model_tagstr}.npy",
            )
            if not os.path.exists(residual_filepath):
                residual_filepath = os.path.join(
                    residuals_dir,
                    ipca_dir,
                    f"{ipca_rtag}_{factor}_factors_{im}_initialMonths_{w}_window_12_strideMonths_{cap}_cap{factor_model_tagstr}.npy",
                )
                if not os.path.exists(residual_filepath):
                    residual_filepath = os.path.join(
                        residuals_dir,
                        ipca_dir,
                        f"{ipca_rtag}_{factor}_factors_{im}_initialMonths_{w}_window_12_reestimationFreq_{cap}_cap{factor_model_tagstr}.npy",
                    )
                    if not os.path.exists(residual_filepath):
                        raise ValueError(f"Could not find residual file for IPCA{factor}; checked {residual_filepath}")
            filepaths.append(residual_filepath)

            comp_mtx_filepath = os.path.join(
                residuals_dir,
                ipca_dir,
                f"{ipca_mtag}_{factor}_factors_{im}_initialMonths_{w}_window_{cap}_cap{factor_model_tagstr}.npy",
            )
            if not os.path.exists(comp_mtx_filepath):
                comp_mtx_filepath = os.path.join(
                    residuals_dir,
                    ipca_dir,
                    f"{ipca_mtag}_{factor}_factors_{im}_initialMonths_{w}_window_12_strideMonths_{cap}_cap{factor_model_tagstr}.npy",
                )
                if not os.path.exists(comp_mtx_filepath):
                    comp_mtx_filepath = os.path.join(
                        residuals_dir,
                        ipca_dir,
                        f"{ipca_mtag}_{factor}_factors_{im}_initialMonths_{w}_window_12_reestimationFreq_{cap}_cap{factor_model_tagstr}.npy",
                    )
                    if not os.path.exists(comp_mtx_filepath):   
                        raise ValueError(f"Could not find composition matrix file for IPCA{factor}; checked {comp_mtx_filepath}")
            comp_mtx_filepaths.append(comp_mtx_filepath)

            factor_model_names.append("IPCA")
            num_factors.append(factor)

        # Users can optionally provide a 2-element numpy array containing the first OOS daily date. 
        # First entry is index of the date; second entry is the date, an int in form YYYMMDD.
        first_oos_daily_date_index = None
        first_oos_date_filepath = os.path.join(residuals_dir, ipca_dir, f"first-oos-date_{im}_initialMonths_{w}_window{factor_model_tagstr}.npy")
        if os.path.exists(first_oos_date_filepath):
            first_oos_daily_date_info = np.load(first_oos_date_filepath, allow_pickle=True)
            logging.info(f"First OOS daily date info (IPCA): {first_oos_daily_date_info}")
            first_oos_daily_date_index = int(first_oos_daily_date_info[0])
    
    if "PCA" in factor_models and len(factor_models["PCA"]) > 0:
        pca_dir = factor_config["PCA"]["directory"]
        pca_rtag = factor_config["PCA"]["residual_tag"]
        pca_mtag = factor_config["PCA"]["comp_mtx_tag"]
        w = factor_config["PCA"]["rolling_window"]
        cw = factor_config["PCA"]["covariance_window_size"]
        ioy = factor_config["PCA"].get("initial_oos_year", None)
        if ioy is None:
            ioy = int(config["start_date"][:4])
        im = factor_config["PCA"]["initial_months"]
        start_year = int(config["start_date"][:4])
        end_year = int(config["end_date"][:4])

        for factor in factor_models["PCA"]:
            residual_filepath = os.path.join(
                residuals_dir,
                pca_dir,
                f"{pca_rtag}_{factor}_factors_{w}_rollingWindow_{cw}_covWindow_{cap}_cap{factor_model_tagstr}.npy",
            )
            if not os.path.exists(residual_filepath):
                residual_filepath = os.path.join(
                    residuals_dir,
                    pca_dir,
                    f"{pca_rtag}_{factor}_factors_{ioy}_initialOOSYear_{w}_rollingWindow_{cw}_covWindow_{cap}_Cap{factor_model_tagstr}.npy",
                )
                if not os.path.exists(residual_filepath):
                    raise ValueError(f"Could not find residual file for PCA{factor} in either format; checked {residual_filepath}")
            filepaths.append(residual_filepath)

            comp_mtx_filepath = os.path.join(
                residuals_dir,
                pca_dir,
                f"{pca_mtag}_{factor}_factors_{w}_rollingWindow_{cw}_covWindow_{cap}_cap{factor_model_tagstr}.npy",
            )
            if not os.path.exists(comp_mtx_filepath):
                comp_mtx_filepath = os.path.join(
                    residuals_dir,
                    pca_dir,
                    f"{pca_mtag}_{factor}_factors_{ioy}_initialOOSYear_{w}_rollingWindow_{cw}_covWindow_{cap}_Cap{factor_model_tagstr}.npy",
                )
                if not os.path.exists(comp_mtx_filepath):
                    raise ValueError(f"Could not find composition matrix file for PCA{factor} in either format; checked {comp_mtx_filepath}")
            comp_mtx_filepaths.append(comp_mtx_filepath)

            factor_model_names.append("PCA")
            num_factors.append(factor)

        # Users can optionally provide a 2-element numpy array containing the first OOS daily date. 
        # First entry is index of the date; second entry is the date, an int in form YYYMMDD.
        first_oos_daily_date_index = None
        first_oos_date_filepath = os.path.join(residuals_dir, pca_dir, f"first-oos-date_{start_year}_beginYear_{end_year}_endYear_{im}_initialMonths.npy")
        if os.path.exists(first_oos_date_filepath):
            first_oos_daily_date_info = np.load(first_oos_date_filepath, allow_pickle=True)
            logging.info(f"First OOS daily date info (PCA): {first_oos_daily_date_info}")
            first_oos_daily_date_index = int(first_oos_daily_date_info[0])
    
    if 'FamaFrench' in factor_models and len(factor_models["FamaFrench"]) > 0:
        ff_dir = factor_config["FamaFrench"]["directory"]
        ff_rtag = factor_config["FamaFrench"]["residual_tag"]
        ff_mtag = factor_config["FamaFrench"]["comp_mtx_tag"]
        w = factor_config["FamaFrench"]["rolling_window"]
        ioy = factor_config["FamaFrench"].get("initial_oos_year", None)
        if ioy is None:
            ioy = int(config["start_date"][:4])
        im = factor_config["FamaFrench"]["initial_months"]
        start_year = int(config["start_date"][:4])
        end_year = int(config["end_date"][:4])

        for factor in factor_models["FamaFrench"]:
            residual_filepath = os.path.join(
                residuals_dir,
                ff_dir,
                f"{ff_rtag}_{factor}_factors_{w}_rollingWindow_{cap}_cap{factor_model_tagstr}.npy",
            )
            if not os.path.exists(residual_filepath):
                residual_filepath = os.path.join(
                    residuals_dir,
                    ff_dir,
                    f"{ff_rtag}_{factor}_factors_{ioy}_initialOOSYear_{w}_rollingWindow_{cap}_Cap{factor_model_tagstr}.npy",
                )
                if not os.path.exists(residual_filepath):
                    raise ValueError(f"Could not find residual file for FamaFrench{factor}; checked {residual_filepath}")
            filepaths.append(residual_filepath)

            comp_mtx_filepath = os.path.join(
                residuals_dir,
                ff_dir,
                f"{ff_mtag}_{factor}_factors_{w}_rollingWindow_{cap}_cap{factor_model_tagstr}.npy",
            )
            if not os.path.exists(comp_mtx_filepath):
                comp_mtx_filepath = os.path.join(
                    residuals_dir,
                    ff_dir,
                    f"{ff_mtag}_{factor}_factors_{ioy}_initialOOSYear_{w}_rollingWindow_{cap}_Cap{factor_model_tagstr}.npy",
                )
                if not os.path.exists(comp_mtx_filepath):
                    raise ValueError(f"Could not find composition matrix file for FamaFrench{factor}; checked {comp_mtx_filepath}")
            comp_mtx_filepaths.append(comp_mtx_filepath)

            factor_model_names.append('FamaFrench')
            num_factors.append(factor)

        # Users can optionally provide a 2-element numpy array containing the first OOS daily date. 
        # First entry is index of the date; second entry is the date, an int in form YYYMMDD.
        first_oos_daily_date_index = None
        first_oos_date_filepath = os.path.join(residuals_dir, ff_dir, f"first-oos-date_{im}_initialMonths_{w}_window{factor_model_tagstr}.npy")
        if os.path.exists(first_oos_date_filepath):
            first_oos_daily_date_info = np.load(first_oos_date_filepath, allow_pickle=True)
            logging.info(f"First OOS daily date info (FamaFrench): {first_oos_daily_date_info}")
            first_oos_daily_date_index = int(first_oos_daily_date_info[0])

    return filepaths, factor_model_names, num_factors, comp_mtx_filepaths, first_oos_daily_date_index


def run(
    config: dict, 
    run_id: str = None,
    gpu_device_ids: List[int] = None,
    notification_phone_number: str = None,
    notification_telegram: bool = False
) -> None:
    """
    Runs a test of a trading policy model over a residual time series using the configuration `config`.

    If run_id is given, logging messages and results files will incorporate it (useful when automating calls to run() for e.g. grid search)
    If gpu_device_ids is None, GPUs will automatically be selected. Set to a list of ints to use those device IDs (useful when automating calls to run() for e.g. grid search).
    If notification_phone_number is given and Twilio is set up, phone number will be sent an SMS upon completion of or exception in a trading policy test.
    If notification_telegram is True, a Telegram message will be sent upon completion of or exception in a trading policy test.

    Args:
        config (dict): Configuration dictionary
        run_id (str, optional): Run ID. Defaults to None.
        gpu_device_ids (List[int], optional): List of GPU device IDs. Defaults to None.
        notification_phone_number (str, optional): Phone number for SMS notifications. Defaults to None.
        notification_telegram (bool, optional): Whether to send Telegram notifications. Defaults to False.

    Returns:
        None. Runs the trading policy model over a residual time series and saves results.
    """
    model_name = config["model_name"]
    results_tag = config["results_tag"]
    debug = config["debug"]

    data_dir = config["data_dir"]
    output_dir = config["output_dir"]
    start_date = config["start_date"]
    end_date = config["end_date"]
    use_comp_mtx = config["use_comp_mtx"]

    factor_model_tag = config["factor_model_tag"]
    factor_model_tagstr = "" if (factor_model_tag is None or factor_model_tag == "") else f"__{factor_model_tag}"
    factor_model_tagtag = "" if (factor_model_tag is None or factor_model_tag == "") else f"--{factor_model_tag}"
    results_tag = f"{results_tag}{factor_model_tagtag}"
    config['results_tag_str'] = results_tag
    
    username, hostname, log_tag, starttime = configure_logging(model_name, run_id=run_id, debug=debug) \
                                            if run_id else initialize_logging(model_name, debug=debug)

    config["run"] = {
        "username": username,
        "hostname": hostname,
        "log_tag": log_tag,
        "starttime": starttime,
        "run_id": run_id,
    }

    if notification_phone_number is None and "notification_phone_number" in config:
        notification_phone_number = config["notification_phone_number"]
        del config["notification_phone_number"]
    if notification_telegram is False and "notification_telegram" in config:
        notification_telegram = config["notification_telegram"]
        del config["notification_telegram"]

    torch.set_default_dtype(torch.float)
    if debug:
        torch.cuda.init()
        torch.autograd.set_detect_anomaly(True)
        torch.backends.cudnn.deterministic = True
        os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
        torch._C._jit_set_profiling_executor(False)
        torch._C._jit_set_profiling_mode(False)
        logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
        # torch.backends.cudnn.benchmark = True
        # torch.use_deterministic_algorithms()
    
    try:
        config["git"] = get_git_info()
        logging.info(f"Config: \n{json.dumps(config, indent=2, sort_keys=False)}")
        
        results_filename = f"results_{log_tag}_{int(time.time())}{'_' + results_tag if results_tag else ''}"
        filepaths, factor_model_names, num_factors, comp_mtx_filepaths, first_oos_daily_date_index = get_factor_models(config, factor_model_tagstr)

        # Load dates for testing
        if config.get("daily_data_npz_name"):
            daily_npz_name = config["daily_data_npz_name"]
            daily_data_filepath = os.path.join(data_dir, f"{daily_npz_name}{factor_model_tagstr}.npz")
            with np.load(daily_data_filepath) as zfile:
                if "daily_dates" in zfile:
                    daily_dates = pd.to_datetime(zfile["daily_dates"], format='%Y%m%d')
                elif "date" in zfile:
                    daily_dates = pd.to_datetime(zfile["date"], format='%Y%m%d')
                else:
                    raise ValueError("Neither 'daily_dates' nor 'date' found in the preprocessed daily data .npz file's keys, but expected to find one of them.")
                if first_oos_daily_date_index is None:
                    daily_dates = daily_dates[(start_date <= daily_dates) & (daily_dates <= end_date)]
                else:
                    daily_dates = daily_dates[int(first_oos_daily_date_index):]
            logging.info("Loaded daily dates")
        else:
            dates_filepath = os.path.join(data_dir, FAMA_FRENCH_5_FACTORS_FILENAME)
            if not os.path.exists(dates_filepath):
                ff5 = pd.read_csv(FAMA_FRENCH_5_FACTORS_URL, header=2, index_col=0)
                ff5.to_csv(dates_filepath)
            ff_daily_data = pd.read_csv(dates_filepath, index_col=0) / 100
            start_date_int = int(start_date.replace('-', ''))
            end_date_int = int(end_date.replace('-', ''))
            daily_dates = pd.to_datetime(ff_daily_data.index[(start_date_int <= ff_daily_data.index) & (ff_daily_data.index <= end_date_int)], format ='%Y%m%d')
        
        # Test loop
        results_dict = {}
        for i in range(len(filepaths)):
            logging.info(f"Beginning simulation for {filepaths[i]}")
            
            # Modify config dict for each factor_model and num_factors so that results are saved with a unique config dict
            config["factor_model"] = factor_model_names[i]
            config["num_factors"] = num_factors[i]

            # Load residuals and perturb if configured
            filepath = filepaths[i]
            logging.info("Loading residuals")
            if not os.path.exists(filepath) and os.path.exists(filepath + ".gz"):
                logging.info("Unzipping residual file")
                with gzip.open(filepath + ".gz", 'rb') as f_in:
                    with open(filepath, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            residuals = np.load(filepath).astype(np.float32)
            if "perturbation" in config and len(config["perturbation"]) > 0:
                logging.info(f"Before perturbing residuals: std: {np.std(residuals[residuals != 0]):0.4f}")
                residuals = perturb(residuals, config['perturbation'])
                logging.info(f"After perturbing residuals: std: {np.std(residuals[residuals != 0]):0.4f}")
            logging.info(f"Residuals loaded; shape: {residuals.shape}")
            residuals[np.isnan(residuals)] = 0

            # Define model and preprocess function
            model_func = import_string(f"models.{config['model_name']}.{config['model_name']}")
            preprocess_func = import_string(f"preprocessing.{config['preprocess_func']}")
            model_tag = get_model_tag(config, factor_model_names[i], num_factors[i])
            logging.info(f"RUN STARTING for model: {model_tag}")

            device_ids, device = choose_device_configuration(gpu_device_ids, config, use_comp_mtx)

            # Prepare output folder
            outdir = os.path.join(output_dir, config["model_name"])
            if not os.path.exists(outdir):
                os.makedirs(outdir)

            if use_comp_mtx:
                logging.info(f"Loading residual composition matrix from {comp_mtx_filepaths[i]}")
                comp_mtx = nploadp(comp_mtx_filepaths[i])
                logging.info(f"Residual composition matrix loaded; shape: {comp_mtx.shape}")
            else:
                comp_mtx = None
                logging.warning("Not using residual composition matrix; this option is for debugging only!")

            # Save the config file
            config_filepath = os.path.join(outdir, f"config_{model_tag}.json")
            with open(config_filepath, "w") as f:
                json.dump(config, f, indent=2)
            
            # Run procedure            
            logging.info(f"Running on devices {device_ids}")
            model_start_time = datetime.datetime.now()
            performance_stats = simulate(
                data=residuals, 
                daily_dates=daily_dates,
                model=model_func,
                preprocess=preprocess_func,
                config=config,
                output_path=outdir, 
                model_tag=model_tag, 
                comp_mtx=comp_mtx,
                save_params=True,
                device=device, 
                device_ids=device_ids,
                factor_model_name=factor_model_names[i],
                num_factors=num_factors[i],
            )

            # Save performance stats (contains e.g. rets, sharpe, ret, std, turnover, short_proportion, leverage)
            performance_stats["start_time"] = model_start_time
            performance_stats["end_time"] = datetime.datetime.now()
            performance_stats["timestamp"] = performance_stats["end_time"]
            performance_stats["config"] = config
            results_dict[model_tag] = performance_stats
            os.makedirs(os.path.join(output_dir, model_name), exist_ok=True)
            pkl_filename = os.path.join(output_dir, model_name, results_filename)
            if os.path.exists(pkl_filename + ".pickle"):
                pkl_filename += str(int(time.time())) + ".pickle"
            else:
                pkl_filename += ".pickle"
            with open(pkl_filename, "wb") as handle:
                pickle.dump(results_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

            # Print the results in a pretty table
            table_data = []
            for k in results_dict:
                table_data.append({
                    "model": model_name,
                    "setting": k,
                    "sharpe": f"{results_dict[k]['sharpe']:0.2f}",
                    "mean": f"{results_dict[k]['ret']*100:0.1f}%",
                    "vol": f"{results_dict[k]['std']*100:0.1f}%"
                })
            tdf = pd.DataFrame(table_data)
            print(tabulate(tdf, headers="keys", tablefmt="grid"))
    except Exception as e:
        logging.error("Uncaught exception", exc_info=e)
        error_msg = f"RUN FAILED: {results_tag} - {model_name} - {log_tag} - {username}@{hostname} - {starttime} - {repr(e)}"
        if notification_phone_number:
            try:
                send_twilio_message(error_msg, notification_phone_number)
            except Exception as twilex:
                logging.error("Twilio exception", exc_info=twilex)
        if notification_telegram:
            try:
                send_telegram_message(error_msg)
            except Exception as tex:
                logging.error("Telegram exception", exc_info=tex)
        raise e
    completion_msg = f"RUN COMPLETED: {results_tag} - {model_name} - {log_tag} - {username}@{hostname} - {starttime}"
    if notification_phone_number:
        try:
            send_twilio_message(completion_msg, notification_phone_number)
        except Exception as twilex:
            logging.error("Twilio exception", exc_info=twilex)
            logging.info(completion_msg)
    if notification_telegram:
        try:
            send_telegram_message(completion_msg)
        except Exception as tex:
            logging.error("Telegram exception", exc_info=tex)
            logging.info(completion_msg)
    

def init_argparse():
    """
    Initialize argparse for running a simulation.
    """
    parser = argparse.ArgumentParser(
        description="Train and/or test trading policy model on residual time series given configuration files."
    )
    parser.add_argument("--config", "-c", help="path to a config .yaml configuration file (e.g. 'configs/config.yaml')", required=True)
    parser.add_argument("--config-model", "-cm", help="path to a model .yaml configuration file (e.g. 'configs/cnntransformer-full.yaml')", required=True)
    parser.add_argument("--run-id", "-r", help="identifier string carrying external information (e.g. 'run42')", required=False)
    parser.add_argument("--gpu-device-ids", "-g", nargs="*", type=int, help="space-separated list of GPU device IDs to use (e.g. '0 1 2 3')", required=False)
    parser.add_argument("--notification-phone-number", "-np", help="notification phone number string (e.g. '+12345678900')", required=False)
    parser.add_argument("--notification-telegram", "-nt", help="whether to send notification via Telegram", action="store_true", required=False)
    return parser


def main():
    """
    Main function for running a simulation.
    """
    parser = init_argparse()
    args = parser.parse_args()
    args = add_config_to_args(args)
    print("Running...")
    run(**vars(args))


if __name__ == "__main__":
    main()
