import argparse
import datetime
import glob
import logging
import os
import pickle
import signal
import socket
import subprocess
import sys
from collections import OrderedDict
from collections.abc import MutableMapping
from functools import reduce
from importlib import import_module
from typing import List, Tuple, Dict, Iterable, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import petname
import psutil
import requests
import torch
import torch.nn as nn
import yaml
from gpuinfo import GPUInfo
from torch.nn.modules.module import _addindent
from twilio.rest import Client


FAMA_FRENCH_5_FACTORS_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
FAMA_FRENCH_5_FACTORS_FILENAME = "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"


def initialize_logging(
    app_name: str,
    logdir: str = "logs",
    debug: bool = False,
    run_id: int = None,
) -> Tuple[str, str, str, str]:
    """
    Initialize logging and monitoring for an application.

    Args:
        app_name: The name of the application.
        logdir: The directory in which to store log files.
        debug: Whether to log debug messages.
        run_id: The ID of the run, if any.

    Returns:
        Tuple[str, str, str, str]: The username, hostname, log tag (a human-readable short name for the process), and start time.
    """
    debugtag = "-debug" if debug else ""
    logtag = petname.Generate(2)
    username = os.path.split(os.path.expanduser("~"))[-1]
    hostname = socket.gethostname().replace(".stanford.edu", "")
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    starttimestr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if run_id is not None:
        raise Exception("Unimplemented")
        run_id = str(run_id)
        fh = logging.FileHandler(
            f"{logdir}/{app_name}{debugtag}_{run_id}_{logtag}_{username}_{hostname}_{starttimestr}.log"
        )
        ch = logging.StreamHandler()
        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            f"[%(asctime)s] Run{run_id} - %(levelname)s - %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logging.getLogger("").handlers = []
        logging.getLogger("").addHandler(fh)
        logging.getLogger("").addHandler(ch)
        logging.info(f"HANDLER LEN: {len(logging.getLogger('').handlers)}")
        logging.getLogger("").level = logging.INFO if not debug else logging.DEBUG
    else:
        logging.basicConfig(
            level=logging.INFO if not debug else logging.DEBUG,
            format="[%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler(
                    f"{logdir}/{app_name}{debugtag}_{logtag}_{username}_{hostname}_{starttimestr}.log"
                ),
                logging.StreamHandler(),
            ],
        )

    def signal_handler(sig, frame):
        logging.error(f"Caught signal {sig}; frame: {frame}")
        logging.error("Exiting...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)
    signal.signal(signal.SIGILL, signal_handler)
    signal.signal(signal.SIGFPE, signal_handler)
    logging.info(
        f"Logging initialized for '{app_name}' by '{username}' on host '{hostname}' with "
        f"ID '{logtag}' at '{starttimestr}' (PID: {os.getpid()})"
    )
    return username, hostname, logtag, starttimestr


def slides_barplot(labels: List[str], data_by_group: Dict[str, Iterable[float]]):
    """
    Create a bar plot with multiple groups of bars, each with multiple bars.

    Example input:
        labels = ['FF', 'PCA', 'IPCA', 'SDF']
        data_by_group['1'] = [20, 34, 30, 35]
        data_by_group['3'] = [25, 32, 34, np.nan]

    Args:
        labels (List[str]): The labels for the x-axis.
        data_by_group (Dict[str, Iterable[float]]): A dictionary mapping group names to lists of data points.

    Returns:
        None. Displays the plot.
    """
    # ax, fig = plt.subplot()

    # get width of bar
    barWidth = 0.25

    # set height of bar
    bars1 = [12, 30, 1, 8, 22]
    bars2 = [28, 6, 16, 5, 10]
    bars3 = [29, 3, 24, 25, 17]

    # Set position of bar on X axis
    r1 = np.arange(len(bars1))
    r2 = [x + barWidth for x in r1]
    r3 = [x + barWidth for x in r2]

    # Make the plot
    plt.bar(r1, bars1, color="#7f6d5f", width=barWidth, edgecolor="white", label="var1")
    plt.bar(r2, bars2, color="#557f2d", width=barWidth, edgecolor="white", label="var2")
    plt.bar(r3, bars3, color="#2d7f5e", width=barWidth, edgecolor="white", label="var3")

    # Add xticks on the middle of the group bars
    plt.xlabel("group", fontweight="bold")
    plt.xticks([r + barWidth for r in range(len(bars1))], ["A", "B", "C", "D", "E"])

    # Create legend & Show graphic
    plt.legend()
    plt.show()


def nploadp(
    filepath: str,
    blocksize: int = 1024,
    log: bool = True,
):
    """
    Load Numpy array in chunks with progress messages.

    Log progress using logging if log=True, otherwise print.
    Tune blocksize for performance/granularity.

    Args:
        filepath (str): The path to the Numpy file.
        blocksize (int): The size of the blocks to load.
        log (bool): Whether to log progress.

    Returns:
        np.ndarray: The loaded Numpy array.
    """
    mmap = None
    try:
        mmap = np.load(filepath, mmap_mode="r")
        y = np.empty_like(mmap)
        n_blocks = int(np.ceil(mmap.shape[0] / blocksize))
        for b in range(n_blocks):
            if log:
                logging.info(
                    "Loading Numpy array into memory, block {}/{}".format(
                        b + 1, n_blocks
                    )
                )
            else:
                nowdatestr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"[{nowdatestr}] Loading Numpy array into memory, block {b + 1}/{n_blocks}"
                )
            y[b * blocksize : (b + 1) * blocksize] = mmap[
                b * blocksize : (b + 1) * blocksize
            ]
    finally:
        del mmap  # make sure file is closed again
    return y


def get_all_free_gpu_ids(
    min_memory_mb: int = 4000, gpu_memory_capacity_mb: int = 12000
) -> List[int]:
    """
    Returns a list of integer IDs of GPUs with at least `min_memory_mb` memory free.

    Args:
        min_memory_mb (int): The minimum memory requirement in MB.
        gpu_memory_capacity_mb (int): The total memory capacity of the GPU in MB.

    Returns:
        List[int]: The list of GPU IDs.
    """
    # get GPU utilization (first row volatile GPU utilization % in [0,100], second row memory used in [0,12000])
    mem_free = gpu_memory_capacity_mb - np.array(GPUInfo.gpu_usage())  # 2 x num_GPUs
    # copy GPU indices into first row
    mem_free[0, :] = np.arange(mem_free.shape[1])
    # sort column of (GPU index, free memory) by free memory
    mem_free = mem_free[:, mem_free[1, :].argsort(kind="stable")[::-1]]
    # return indices which have more than min_memory_mb, and free memory in GB, sorted in order of most free memory
    return mem_free[0, np.where(mem_free[1, :] >= min_memory_mb)[0]].tolist()


def get_free_gpu_ids(
    used_gpu_ids: List[int],
    min_memory_pattern_mb: List[int],
    gpu_memory_capacity_mb: int = 12000,
) -> List[int]:
    """
    Returns an ordered list of integer IDs of GPUs with at least `min_memory_pattern_mb` memory free in MB, elementwise.

    Returns exactly list of IDs of length exactly == len(min_memory_pattern).

    Args:
        used_gpu_ids (List[int]): The list of GPU IDs to exclude.
        min_memory_pattern_mb (List[int]): The list of minimum memory requirements in MB.
        gpu_memory_capacity_mb (int): The total memory capacity of the GPU in MB.

    Returns:
        List[int]: The list of GPU IDs.
    """
    mins = np.array(min_memory_pattern_mb)
    # get GPU info (first row volatile GPU utilization % in [0,100], second row memory used in [0,mem_capacity_mb])
    info = np.array(GPUInfo.gpu_usage())
    utilizations = np.array(info[0, :]).tolist()
    mem_free = gpu_memory_capacity_mb - info  # (2 x num_GPUs) array
    # copy GPU indices into first row
    mem_free[0, :] = np.arange(mem_free.shape[1])
    del info
    # remove entries of used GPU IDs
    free_mask = ~np.isin(mem_free[0, :], used_gpu_ids)
    mem_free = mem_free[:, free_mask]
    id2idx = dict(zip(mem_free[0, :], range(len(mem_free[0, :]))))
    # find indices which satisfy each min_mem_pattern
    free_gpu_ids_by_mem_needed = {mm: [] for mm in np.unique(mins).tolist()}
    for min_mem in np.unique(mins):
        # get IDs above min_mem (+10% min_mem as buffer)
        mem_threshold = min(gpu_memory_capacity_mb * 0.99, min_mem * 1.1)
        free_gpu_ids_by_mem_needed[min_mem] = mem_free[
            0, np.where(mem_free[1, :] > mem_threshold)[0]
        ].tolist()
    gpu_ids = []

    def score_gpu(id_, mem):
        score = (
            0.5 * utilizations[id2idx[id_]] / 100
            + 0.5 * abs(mem_free[1, id2idx[id_]] - mem) / gpu_memory_capacity_mb
        )
        return score

    for mem in mins:
        # if we can't fulfill the request, just return what we can
        if len(free_gpu_ids_by_mem_needed[mem]) == 0:
            return gpu_ids
        # choose GPU with smallest utilization and memory free closest to mem
        id_ = min(free_gpu_ids_by_mem_needed[mem], key=lambda x: score_gpu(x, mem))
        gpu_ids.append(id_)
        # remove from free GPU IDs
        for k in free_gpu_ids_by_mem_needed.keys():
            if id_ in free_gpu_ids_by_mem_needed[k]:
                free_gpu_ids_by_mem_needed[k].remove(id_)
    return gpu_ids


def get_free_memory_gbs(username, per_process_gb_usage, num_running_processes) -> int:
    """
    Get the amount of free memory in GB available to the user `username`, accounting for the number of running processes.

    Args:
        username (str): The username.
        per_process_gb_usage (int): The amount of memory in GB used by each process.
        num_running_processes (int): The number of running processes.

    Returns:
        int: The amount of free memory in GB.
    """
    user_memory_cmd = (
        f"ps -U {username} --no-headers  -o rss | (tr '\n' +; echo 0) | bc"
    )
    used_by_me_gbs = (
        int(
            subprocess.check_output(user_memory_cmd, shell=True).strip().decode("utf-8")
        )
        // 1024**2
    )
    available_gbs = psutil.virtual_memory().available // 1024**3
    return min(
        available_gbs,
        available_gbs + used_by_me_gbs - num_running_processes * per_process_gb_usage,
    )


def send_telegram_message(message: str) -> None:
    """
    Send a message to a Telegram chat using the Telegram bot API.

    Get API token and chat ID from `credentials.yaml` file in main directory.
    To get these, see https://stackoverflow.com/a/75118239.

    Args:
        message (str): The message to send.

    Returns:
        None.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        with open(os.path.join(dir_path, "credentials.yaml"), "r") as f:
            credentials = yaml.safe_load(f)
    except Exception as e:
        logging.warning("Could not load credentials.yaml file", exc_info=e)
        return
    try:
        token = credentials["TELEGRAM_BOT_TOKEN"]
        chat_id = credentials["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        response = requests.get(url).json()
        if response["ok"]:
            logging.info(f"Sent the following Telegram message: '{message}'")
        else:
            logging.warning(
                f"Could not send the following Telegram message: '{message}'; response: {response}"
            )
    except Exception as e:
        logging.warning("Could not send Telegram message", exc_info=e)
        return


def send_twilio_message(message: str, to: str) -> None:
    """
    Send a message to a phone number using the Twilio API.

    The `to` number must be in the form of "+1234567890" for e.g. +1 123 456 7890
    Find your Account SID and Auth Token at twilio.com/console, see http://twil.io/secure.
    Put credentials into `credentials.yaml` file in main directory.

    Args:
        message (str): The message to send.
        to (str): The phone number to send the message to.

    Returns:
        None.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        with open(os.path.join(dir_path, "credentials.yaml"), "r") as f:
            credentials = yaml.safe_load(f)
    except Exception as e:
        logging.warning("Could not load credentials.yaml file", exc_info=e)
        return
    try:
        account_sid = credentials["TWILIO_ACCOUNT_SID"]
        auth_token = credentials["TWILIO_AUTH_TOKEN"]
        from_phone_number = credentials["TWILIO_PHONE_NUMBER"]
        client = Client(account_sid, auth_token)
        message = client.api.account.messages.create(
            body=message, from_=from_phone_number, to=to
        )
    except Exception as e:
        logging.warning("Could not send Twilio message", exc_info=e)
        return


def moving_average(a: np.ndarray, n: int, axis=1) -> np.ndarray:
    """
    Creates a simple moving average for the matrix `a`, with a window size of `n`, along the given `axis`.

    Args:
        a (np.ndarray): The matrix to average.
        n (int): The window size.
        axis (int): The axis along which to average.

    Returns:
        np.ndarray: The moving average matrix.
    """
    ret = np.cumsum(a, axis=axis)
    N = a.shape[axis]
    if axis == 0:
        ret[n:] = (
            ret[n:] - ret[:-n]
        )  # np.take(ret, range(n,N), axis=axis) - np.take(ret, range(0,N-n), axis=axis, out = )
        try:
            ret[: n - 1] = ret[: n - 1] / np.linspace(1, min(n - 1, N), min(n - 1, N))
        except:
            ret[: n - 1] = ret[: n - 1] / np.linspace(
                1, min(n - 1, N), min(n - 1, N)
            ).reshape((min(n - 1, N), 1))
        ret[n - 1 :] = ret[n - 1 :] / n
    elif axis == 1:
        ret[:, n:] = (
            ret[:, n:] - ret[:, :-n]
        )  # np.take(ret, range(n,N), axis=axis) - np.take(ret, range(0,N-n), axis=axis, out = )
        ret[:, : n - 1] = ret[:, : n - 1] / np.linspace(
            1, min(n - 1, N), min(n - 1, N)
        ).reshape((min(n - 1, N), 1))
        ret[:, n - 1 :] = ret[:, n - 1 :] / n
    else:
        raise Exception(f"Invalid axis for moving average '{axis}'")
    return ret


def moving_average_pytorch(
    a: torch.Tensor, n: int, axis=1, device="cpu"
) -> torch.Tensor:
    """
    Creates a simple moving average for the tensor `a`, with a window size of `n`, along the given `axis`.

    Args:
        a (torch.Tensor): The tensor to average.
        n (int): The window size.
        axis (int): The axis along which to average.
        device (str): The device to use.

    Returns:
        torch.Tensor: The moving average tensor.
    """
    ret = torch.cumsum(a, dim=axis)
    N = a.shape[axis]
    if axis == 0:
        ret[n:] = ret[n:] - ret[:-n]
        try:
            ret[: n - 1] = ret[: n - 1] / torch.linspace(
                1, min(n - 1, N), min(n - 1, N), device=device
            )
        except:
            ret[: n - 1] = ret[: n - 1] / torch.linspace(
                1, min(n - 1, N), min(n - 1, N), device=device
            ).reshape((min(n - 1, N), 1))
        ret[n - 1 :] = ret[n - 1 :] / n
    elif axis == 1:
        ret[:, n:] = ret[:, n:] - ret[:, :-n]
        ret[:, : n - 1] = ret[:, : n - 1] / torch.linspace(
            1, min(n - 1, N), min(n - 1, N), device=device
        ).reshape((min(n - 1, N), 1))
        ret[:, n - 1 :] = ret[:, n - 1 :] / n
    else:
        raise Exception(f"Invalid axis for moving average '{axis}'")
    return ret


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path.

    Raises ImportError if the import failed.
    From https://docs.djangoproject.com/en/dev/_modules/django/utils/module_loading/.

    Args:
        dotted_path (str): The dotted path to the module.

    Returns:
        Any: The imported module.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err


def flatten(d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """
    Flattens a nested dictionary with string keys to a flat dictionary using
    `sep` to concatenate keys at different levels, and using `parent_key` as
    the top-level key.

    Args:
        d (Dict[str, Any]): The dictionary to flatten.
        parent_key (str): The parent key.
        sep (str): The separator.

    Returns:
        Dict[str, Any]: The flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_model_attr(model: Any, attr: str) -> Any:
    """
    Gets a model attribute, regardless of whether the model is wrapped in a DataParallel object or not.

    Args:
        model (Any): The model.
        attr (str): The attribute.

    Returns:
        Any: The attribute value.
    """
    if (
        hasattr(model, "module")
        and hasattr(model.module, attr)
        and getattr(model.module, attr)
    ):
        return True
    if (not hasattr(model, "module")) and hasattr(model, attr) and getattr(model, attr):
        return True
    return False


def load_results(
    results_directory_path: str,
    results_tag: str = None,
    drop_static_columns: bool = True,
) -> pd.DataFrame:
    """
    Loads pickle file results in `results_directory_path` which contain `results_tag` in the filename
    and organizes them into a pandas.DataFrame.

    Generally this works best setting `results_directory_path` to a subdir of the results directory,
    such as "CNNTransformer", instead of the top-level "results" directory.

    Args:
        results_directory_path (str): The path to the results directory.
        results_tag (str): The tag to filter results by.
        drop_static_columns (bool): Whether to drop columns which are all the same value.

    Returns:
        pd.DataFrame: The results DataFrame.
    """
    results_dicts = []
    if results_tag:
        filepaths = glob.glob(
            os.path.join(results_directory_path, "**", f"*{results_tag}*.pickle"),
            recursive=False,
        ) + glob.glob(
            os.path.join(results_directory_path, f"*{results_tag}*.pickle"),
            recursive=False,
        )
    else:
        filepaths = glob.glob(
            os.path.join(results_directory_path, "**", "*.pickle"), recursive=False
        ) + glob.glob(os.path.join(results_directory_path, "*.pickle"), recursive=False)

    def _add_config(d, config, results_key):
        if "factor_model" not in config and "num_factors" not in config:
            fminfo = results_key.split("__", 1)[0]
            config["factor_model"] = "".join([c for c in fminfo if not c.isdigit()])
            config["num_factors"] = int("".join([c for c in fminfo if c.isdigit()]))
        if "factor_models" in config:
            del config["factor_models"]
        config = flatten(config, sep=".")
        for config_var in config.keys():
            dd[config_var] = config[config_var]

    for fp in filepaths:
        end_ts = os.path.getmtime(fp)
        end_dt = datetime.datetime.fromtimestamp(end_ts)
        d = pickle.load(open(fp, "rb"))
        for results_key in d.keys():
            dd = d[results_key].copy()
            c = dd["config"]
            del dd["config"]
            dd["end_time"] = end_dt
            dd["start_time"] = dd.pop("timestamp")
            dd["filepath"] = fp
            if "turnover" in dd:
                dd["turnovers"] = dd.pop("turnover")
            dd["turnover"] = np.mean(dd["turnovers"])
            if "short_proportion" in dd:
                dd["short_proportions"] = dd.pop("short_proportion")
            dd["short_proportion"] = np.mean(dd["short_proportions"])
            _add_config(dd, c, results_key)
            results_dicts.append(dd)
    df = pd.DataFrame.from_dict(results_dicts)
    if drop_static_columns:
        # drop columns which are all the same value
        cols_to_drop = []
        for c in df.columns:
            try:
                if df[c].nunique(dropna=False) == 1:
                    cols_to_drop.append(c)
            except:
                pass  # for columns which contain unhashable values, nunique may fail
        df.drop(cols_to_drop, axis=1, inplace=True)
    return df


def get_git_info() -> Dict[str, str]:
    """
    Get git branch, current commit hash, and whether repo contains uncommitted changes.

    Returns:
        Dict[str, str]: The git information.
    """
    gitwd = os.path.dirname(os.path.abspath(__file__))
    try:
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=gitwd
            )
            .strip()
            .decode()
        )
    except:
        branch = "None"
    try:
        hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=gitwd)
            .strip()
            .decode()
        )
    except:
        hash = "None"
    try:
        uncommitted_changes = (
            subprocess.check_output(["git", "status", "--porcelain"], cwd=gitwd)
            .strip()
            .decode()
            != ""
        )
    except:
        uncommitted_changes = "None"
    return {
        "branch": branch,
        "hash": hash,
        "uncommitted_changes": uncommitted_changes,
        "git_working_dir": gitwd,
    }


def get_model_tag(
    config: Dict[str, Any],
    factor_model: str,
    factor_number: int,
    load_log_tag: str = None,
    load_subperiod: int = None,
) -> str:
    """
    Get a tag for a model based on its configuration, factor model, and factor number.

    Args:
        config (Dict[str, Any]): The configuration.
        factor_model (str): The factor model.
        factor_number (int): The factor number.
        load_log_tag (str): The log tag to load.
        load_subperiod (int): The subperiod to load.

    Returns:
        str: The model tag.
    """
    residual_weight_marker = "__comp_mtx" if config["use_comp_mtx"] else ""
    objective = config["objective"]
    factor_model_tag = config["factor_model_tag"]
    factor_model_tagtag = (
        ""
        if (factor_model_tag is None or factor_model_tag == "")
        else f"--{factor_model_tag}"
    )
    results_tag = config["results_tag"]
    results_tag_str = f"{results_tag}{factor_model_tagtag}"
    log_tag = config["run"]["log_tag"] if load_log_tag is None else load_log_tag
    return (
        factor_model
        + str(factor_number)
        + f"__{config['model_name']}"
        + residual_weight_marker
        + f"__{config['cap_proportion']}cap"
        + f"__{objective}"
        + f"__{config['trans_cost']}trans_cost"
        + f"__{config['hold_cost']}hold_cost"
        + f"__{config['model']['lookback']}lookback"
        + f"__{config['length_training']}length_training"
        + f"__{config['holding_days']}holding_days"
        + (f"__{results_tag_str}" if results_tag_str != "" else "")
        + f"__{log_tag}"
        + (f"__subperiod{load_subperiod}" if load_subperiod is not None else "")
    )


def add_config_to_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    Add configuration from a .yaml file to the args namespace.

    Args:
        args (argparse.Namespace): The arguments.

    Returns:
        argparse.Namespace: The arguments with the configuration added.
    """
    with open(args.config, "r") as stream:
        try:
            config = yaml.safe_load(stream)
            args.config = config
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)
    with open(args.config_model, "r") as stream:
        try:
            model_config = yaml.safe_load(stream)
            if len(set(args.config.keys()).intersection(set(model_config.keys()))) > 0:
                raise Exception(
                    "Cannot have same keys in config .yaml file and model config .yaml file"
                )
            args.config.update(model_config)
            del args.config_model
            del model_config
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)
    return args


def hierarchical_summary(model, print_summary=False) -> str:
    """
    Summarize the model in a hierarchical format.

    From https://github.com/amarczew/pytorch_model_summary/.

    Args:
        model: The model.
        print_summary: Whether to print the summary.

    Returns:
        str: The summary.
    """

    def repr(model):
        # We treat the extra repr like the sub-module, one item per line
        extra_lines = []
        extra_repr = model.extra_repr()
        # empty string will be split into list ['']
        if extra_repr:
            extra_lines = extra_repr.split("\n")
        child_lines = []
        total_params = 0
        for key, module in model._modules.items():
            if module is None:
                continue
            mod_str, num_params = repr(module)
            mod_str = _addindent(mod_str, 2)
            child_lines.append("(" + key + "): " + mod_str)
            total_params += num_params
        lines = extra_lines + child_lines

        for name, p in model._parameters.items():
            if p is not None:
                total_params += reduce(lambda x, y: x * y, p.shape)

        main_str = model._get_name() + "("
        if lines:
            # simple one-liner info, which most builtin Modules will use
            if len(extra_lines) == 1 and not child_lines:
                main_str += extra_lines[0]
            else:
                main_str += "\n  " + "\n  ".join(lines) + "\n"

        main_str += ")"
        main_str += ", {:,} params".format(total_params)
        return main_str, total_params

    string, count = repr(model)

    # Building hierarchical output
    _pad = int(max(max(len(_) for _ in string.split("\n")) - 20, 0) / 2)
    lines = list()
    lines.append("=" * _pad + " Hierarchical Summary " + "=" * _pad + "\n")
    lines.append(string)
    lines.append("\n\n" + "=" * (_pad * 2 + 22) + "\n")

    str_summary = "\n".join(lines)
    if print_summary:
        print(str_summary)

    return str_summary, count


def model_summary(
    model,
    *inputs,
    batch_size=-1,
    show_input=False,
    show_hierarchical=False,
    print_summary=False,
    max_depth=100,
    show_parent_layers=False,
) -> str:
    """
    Show output shape and hierarchical view of neural net.

    Example:
    `print(summary(Net(), torch.zeros((1, 1, 28, 28)), show_input=False, show_hierarchical=True))`
    where the second argument is the input tensor.

    From https://github.com/amarczew/pytorch_model_summary/.

    Args:
        model: The model.
        inputs: The inputs.
        batch_size: The batch size.
        show_input: Whether to show the input shape.
        show_hierarchical: Whether to show the hierarchical view.
        print_summary: Whether to print the summary.
        max_depth: The maximum depth.
        show_parent_layers: Whether to show parent layers.

    Returns:
        str: The summary.
    """
    max_depth = max_depth if max_depth is not None else 9999

    def build_module_tree(module):
        def _in(module, id_parent, depth):
            for c in module.children():
                # ModuleList and Sequential do not count as valid layers
                if isinstance(c, (nn.ModuleList, nn.Sequential)):
                    _in(c, id_parent, depth)
                else:
                    _module_name = str(c.__class__).split(".")[-1].split("'")[0]
                    _parent_layers = (
                        f"{module_summary[id_parent].get('parent_layers')}"
                        f"{'/' if module_summary[id_parent].get('parent_layers') != '' else ''}"
                        f"{module_summary[id_parent]['module_name']}"
                    )

                    module_summary[id(c)] = {
                        "module_name": _module_name,
                        "parent_layers": _parent_layers,
                        "id_parent": id_parent,
                        "depth": depth,
                        "n_children": 0,
                    }

                    module_summary[id_parent]["n_children"] += 1

                    _in(c, id(c), depth + 1)

        # Defining summary for the main module
        module_summary[id(module)] = {
            "module_name": str(module.__class__).split(".")[-1].split("'")[0],
            "parent_layers": "",
            "id_parent": None,
            "depth": 0,
            "n_children": 0,
        }

        _in(module, id_parent=id(module), depth=1)

        # Defining layers that will be printed
        for k, v in module_summary.items():
            module_summary[k]["show"] = v["depth"] == max_depth or (
                v["depth"] < max_depth and v["n_children"] == 0
            )

    def register_hook(module):
        def shapes(x):
            _lst = list()

            def _shapes(_):
                if isinstance(_, torch.Tensor):
                    _lst.append(list(_.size()))
                elif isinstance(_, (tuple, list)):
                    for _x in _:
                        _shapes(_x)
                else:
                    # TODO: decide what to do when there is an input which is not a tensor
                    raise Exception("Object not supported")

            _shapes(x)

            return _lst

        def hook(module, input, output=None):
            if id(module) in module_mapped:
                return

            module_mapped.add(id(module))
            module_name = module_summary.get(id(module)).get("module_name")
            module_idx = len(summary)

            m_key = "%s-%i" % (module_name, module_idx + 1)
            summary[m_key] = OrderedDict()
            summary[m_key]["parent_layers"] = module_summary.get(id(module)).get(
                "parent_layers"
            )

            summary[m_key]["input_shape"] = shapes(input) if len(input) != 0 else input

            if show_input is False and output is not None:
                summary[m_key]["output_shape"] = shapes(output)

            params = 0
            params_trainable = 0
            trainable = False
            for m in module.parameters():
                _params = torch.prod(torch.LongTensor(list(m.size())))
                params += _params
                params_trainable += _params if m.requires_grad else 0
                # if any parameter is trainable, then module is trainable
                trainable = trainable or m.requires_grad

            summary[m_key]["nb_params"] = params
            summary[m_key]["nb_params_trainable"] = params_trainable
            summary[m_key]["trainable"] = trainable

        _map_module = module_summary.get(id(module), None)
        if _map_module is not None and _map_module.get("show"):
            if show_input is True:
                hooks.append(module.register_forward_pre_hook(hook))
            else:
                hooks.append(module.register_forward_hook(hook))

    # create properties
    summary = OrderedDict()
    module_summary = dict()
    module_mapped = set()
    hooks = []

    # register id of parent modules
    build_module_tree(model)

    # register hook
    model.apply(register_hook)

    model_training = model.training

    model.eval()
    model(*inputs)

    if model_training:
        model.train()

    # remove these hooks
    for h in hooks:
        h.remove()

    # params to format output - dynamic width
    _key_shape = "input_shape" if show_input else "output_shape"
    _len_str_parent = (
        max([len(v["parent_layers"]) for v in summary.values()] + [13]) + 3
    )
    _len_str_layer = max([len(layer) for layer in summary.keys()] + [15]) + 3
    _len_str_shapes = (
        max(
            [
                len(", ".join([str(_) for _ in summary[layer][_key_shape]]))
                for layer in summary
            ]
            + [15]
        )
        + 3
    )
    _len_line = (
        35
        + _len_str_parent * int(show_parent_layers)
        + _len_str_layer
        + _len_str_shapes
    )
    fmt = (
        "{:>%d} " % _len_str_parent if show_parent_layers else ""
    ) + "{:>%d}  {:>%d} {:>15} {:>15}" % (_len_str_layer, _len_str_shapes)

    """ starting to build output text """

    # Table header
    lines = list()
    lines.append("-" * _len_line)
    _fmt_args = ("Parent Layers",) if show_parent_layers else ()
    _fmt_args += (
        "Layer (type)",
        f"{'Input' if show_input else 'Output'} Shape",
        "Param #",
        "Tr. Param #",
    )
    lines.append(fmt.format(*_fmt_args))
    lines.append("=" * _len_line)

    total_params = 0
    trainable_params = 0
    for layer in summary:
        # Table content (for each layer)
        _fmt_args = (summary[layer]["parent_layers"],) if show_parent_layers else ()
        _fmt_args += (
            layer,
            ", ".join([str(_) for _ in summary[layer][_key_shape]]),
            "{0:,}".format(summary[layer]["nb_params"]),
            "{0:,}".format(summary[layer]["nb_params_trainable"]),
        )
        line_new = fmt.format(*_fmt_args)
        lines.append(line_new)

        total_params += summary[layer]["nb_params"]
        trainable_params += summary[layer]["nb_params_trainable"]

    # Table footer
    lines.append("=" * _len_line)
    lines.append("Total params: {0:,}".format(total_params))
    lines.append("Trainable params: {0:,}".format(trainable_params))
    lines.append("Non-trainable params: {0:,}".format(total_params - trainable_params))
    if batch_size != -1:
        lines.append("Batch size: {0:,}".format(batch_size))
    lines.append("-" * _len_line)

    if show_hierarchical:
        h_summary, _ = hierarchical_summary(model, print_summary=False)
        lines.append("\n")
        lines.append(h_summary)

    str_summary = "\n".join(lines)
    if print_summary:
        print(str_summary)

    return str_summary

