README
======

Manuscript title: Deep Learning Statistical Arbitrage
Manuscript authors: Jorge Guijarro-Ordonez, Markus Pelger, and Greg Zanotti

# Overview

This repo contains the official code for our paper *Deep Learning Statistical Arbitrage*, available at https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3862004 and https://arxiv.org/abs/2106.04028.

In the following sections, we provide instructions and details for replicating the results from the paper. Due to the size of the data and the computational requirements of training the trading policy models, we provide residual time series and pre-trained policy models which can be used in the commands given in the following sections to quickly reproduce tables and figures from the paper. Due to the size of the associated residual composition matrices, we only provide residuals for the IPCA 5-factor models. However, we also provide configuration files and instructions for training your own policy models. The full results for any $k$-factor model can be replicated by training the appropriate model.

# Data availability and provenance

Below we describe the data sets used in the paper. Each description below states how any future users of this package can access and recreate each data set. The step-by-step instructions allow any user to readily run our code and (re)produce our results. For each data set, we list information such as the data set origin, details of the data set (including its location/accessibility at the origin, date ranges, versions, exclusions, etc.), whether the data set is included in the package, the filepath and format at which the data set should be placed to run the code, the approximate size and number of files in the dataset, and if, the data set was generated, how this generation is implemented (including code for generation if applicable).

1. Deep Learning in Asset Pricing (DLAP) Dataset
   - Description: Daily CRSP returns and monthly characteristics data for all ~28,000 US stocks in the CRSP database from "Deep Learning in Asset Pricing" (2024).
   - Source: Markus Pelger
   - Location: mpelger@stanford.edu
   - Version: N/A
   - Exclusions: See https://pubsonline.informs.org/doi/10.1287/mnsc.2023.4695 for details
   - Date range: 1960-01-01 through 2016-12-31
   - Included: No
   - Format: Numpy NPY files; see relevant subsection below for details
   - Filepaths: Configurable, e.g. `data/...`; see relevant subsection below for details
   - Size: ~55GB
   - Instructions: Email Markus Pelger for access
2. Fama-French Factors
   - Description: Daily Fama-French 5, momentum, short-term reversal, and long-term reversal factors
   - Source: Kenneth French's website
   - Location: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
   - Version: N/A
   - Exclusions: See https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
   - Date range: 1960-01-01 through 2016-12-31
   - Included: No
   - Format: .zip
   - Filepaths: Configurable, e.g. `data/...`; see relevant subsection below for details
   - Size: ~1MB
   - Instructions: Publicly available for download; automatically retrieved by code in this repo
3. Residuals Data
   - Description: Daily residual returns and residual compositions fors factor models
   - Source: Generated in this project
   - Location: Generated in this project
   - Version: N/A
   - Exclusions: None
   - Date range: 1998-01-01 through 2016-12-31
   - Included: Partially
   - Format: Numpy NPY files
   - Filepaths: `residuals/...`; see relevant subsection below for details
   - Size: ~200GB
   - Instructions: See relevant subsection below for details

## Deep Learning Asset Pricing (DLAP) dataset

For fundamentals and price information, we use the dataset from "Deep Learning in Asset Pricing" (Chen, Pelger, and Zhu, 2024). The paper contains
all details of the dataset's construction in the online appendix, which is available from SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3350138.
In short, the dataset combines CRSP and Compustat prices and fundamentals. It is available from Markus Pelger. It contains the following files, which
should be placed at the following filenames in the `data` directory for residual computations (see below section for instructions):

| Size   | Filename                           | Description                                                  |
|--------|------------------------------------|--------------------------------------------------------------|
| 970MB  | characteristics-replication.csv    | Monthly characteristics and returns data [CRSP/Compustat]    |
| 2.2GB  | daily-returns-replication.csv      | Daily returns data [CRSP]                                    |
| 9.4KB  | CharacteristicVariables.pdf        | Descriptions of characteristics used in the datasets         |

- `characteristics-replication.csv`: CSV containing the following columns:
   - `yy`: Year of the observation
   - `mm`: Month of the observation
   - `date`: Date of the observation
   - `permno`: Permno of the observation
   - `ret`: Montly return for the permno
   - Other characteristics columns, each of which is outlined in `CharacteristicVaribles.pdf`
- `daily-returns-replication.csv`: CSV file with the following columns:
   - `date`: Date of the observation
   - `permno`: Permno of the observation
   - `ret`: Daily return of the observation
- `CharacteristicsVariables.pdf`: Variable descriptions of characteristics

## Residuals data 

To reproduce the residuals data:

1. Place the returns and characteristics data at the given filenames in the `data` directory (see above section). The code is designed to run with relative pathnames, and data in `data` will be automatically detected.
2. Use the `run_factor_model.py` script to process the raw data and generate the residuals, inputting the appropriate factor model name (e.g. `ipca`).
3. All processed data and generated residuals will be saved in the `residuals` folder. 

The residuals dataset is composed of the following files:

- **Residual returns files:** Files with names like `IPCA_DailyOOSresiduals_5_factors_12_initialMonths_60_window_0.01_cap.npy`. These files contain the daily residual returns for each asset in the factor model. See the configuration files for more details and explicit settings. 300-500 MB each.
- **Residual composition matrix files:** Files with names like `IPCA_DailyMatrixOOSresiduals_8_factors_420_initialMonths_240_window_0.01_cap.npy`. These files contain the residual composition matrices for each asset in the factor model. See the configuration files for more details and explicit settings. 100-200 GB each.
- **Asset selection mask files:** Files with names like `IPCA_idxs-selected-all_0_factors_420_initialMonths_240_window_0.01_cap.npy`. These files contain the assets selected each day for use by the factor model. ~50 MB each.
- **Asset universe mask files:** Files with names like `mask_420_initialMonths_240_window_0.01_cap.npy` or `assets-to-consider_420_initialMonths_240_window_0.01_cap.npy` or `super_mask_0.01.npy`. These files contain a one or zero for each asset processed by the factor model. The entry will be one if the asset is ever selected by the factor model, and zero otherwise. These are used to denote the set of all assets which are used throughout for training and testing. These may not be created for all models. ~10 KB each.


# Variable dictionaries

We include descriptions for all used data files (whether included or not) below.

## DLAP Dataset

The data file descriptions for the DLAP dataset are given below.

**Monthly characteristics data:**

Please see `CharacteristicVariables.pdf`

**Daily price data:**

Please see table above.

## Residuals data

- **Residual returns files:** `T x N'`-dimensional matrices containing the returns for all `N'` residuals for all `T` dates in the data set.
- **Residual composition matrix files:** `T x N x N'`-dimensional tensors containing the composition weights for all `N'` residuals over all `N` assets for all `T` days in the data set.
- **Asset selection mask files:** `T x N`-dimensional matrices containing ones for assets which are selected for trading on the given date and zeros otherwise.
- **Asset universe mask files:** `N`-dimensional vectors containing ones for assets which are available for trading throughout the entire period and zeros otherwise.



# Computational requirements

This package is compatible with Python 3.10 on Linux. Python packages and versions are given in `requirements.txt`. All packages can be installed by running `pip install -r requirements.txt`. Our code uses fixed seeds.

Our code is not entirely optimized for efficiency and requires computational resources and runtime. We cover two computation scenarios.

## Full replication

Scenario: Full reproduction (from scratch, including residual estimation and trading policy model training/testing) for any one of the three factor models covered in the paper.

Minimal hardware requirements:
- CPU: 16 cores
- RAM: 384GB
- Disk space: 2TB
- Total GPU VRAM: 36GB

Runtime depends on the compute capabilities and number of the GPU(s) chosen. We give some approximate runtimes for some GPU choices:
- 3x NVIDIA Titan V: ~14 days
- 1x NVIDIA RTX A6000: ~7 days

## Partial replication

Scenario: Replication of just the results from a pre-trained trading policy model using provided residual data set.

Minimal hardware requirements:
- CPU: 4 cores
- RAM: 256GB
- Disk space: 300GB
- GPU VRAM: 12GB

Runtime depends on the compute capabilities and number of the GPU(s) chosen. We give some approximate runtimes for some GPU choices:
- 3x NVIDIA Titan V: ~4 hours
- 1x NVIDIA RTX A6000: ~2 hours


# Programs/code

Several code files comprise our package. Below we describe the structure of the package, provide details for some common tasks, and give instructions describing the order which code files need to be run in order to reproduce all figures and tables in our paper. These instruction indicate where in the code which table/figure/result is produced. 

## Structure

This repo is organized as follows:
- `run_sim.py` is a user interface to `simulation.py` which deals with configuration, logging, saving results, etc.
- `simulation.py` contains the code for training a trading policy model and simulating trading.
- `preprocessing.py` contains functions for preprocessing residual time series data into a form usable by a trading policy model
- `data.py` contains miscellaneous functions for altering residual time series data
- `configs` contains configuration files which define various tests of trading policy models on residual time series and performance statistics computations
- `data` contains raw input data used to create residuals
- `factor_models` contains code for creating residuals from raw input data
- `residuals` stores residual time series data sets created by the code in `factor_models`
- `models` contains code for trading policy models
- `results` contains the results of and plots for trading policy model tests conducted by `run_sim.py`
- `notebooks` may contain miscellaneous code and notebooks for interpreting and exploring `results` and saved models
- `utils.py` contains helpful functions used throughout

## Common Tasks

### Quickstart

To test a trading policy model on a residual time series, use `run_sim.py`. This file provides a CLI interface to `simulation.py`. The CLI interface allows you to specify a configuration file and a model file to train and test. In general, the command will look like:
```
python3 run_sim.py -c configs/simulation/config_name_here.yaml -cm configs/policy/model_name_here.yaml
```
where `config_name_here.yaml` is a configuration file from the relevant `configs` subdirectory.
You can write your own configuration file to edit hyperparameters and other settings for the trading simulation. See the `configs` subdirectory for examples.

### Generating residuals

To create residuals, run `run_factor_model.py`, providing the name of a factor model in the `factor_models` directory.
```
python3 run_factor_model.py -m factor_model_name_here -d dlap
```
Generated residuals for the factor model which has been run will be saved in the `residuals` folder.

### Running trading policy models

To run trading policy models on the generated residuals, use the `run_sim.py` script. This script allows you to train and test various trading policy models on the residual time series data.

1. Ensure you have generated the residuals using the instructions in the "Generating residuals" section above.

2. Navigate to the main directory of the project.

3. Run the following command:
   ```
   python3 run_sim.py -c configs/simulation/your_config_file.yaml -cm configs/policy/your_model_config_file.yaml
   ```
   Replace `your_config_file.yaml` and `your_policy_model_config_file.yaml` with the name of the configuration file you want to use from the `configs` folder.

4. The script will train the model specified in the configuration file on the residual data and then test its performance.

5. Results and plots will be saved to the subdirectory of the `results` folder indicated in the simulation config file.


## Replicating results

This section provides the instructions and commands to replicate the results in the paper. For each result (e.g. Table 1, Figure 1, etc.), the table includes the command or instructions to run in order to replicate it (e.g. `python3 run_sim.py ...`).

The basic workflow is:

1. Run command to create factors using `run_factor_model.py`.
2. Run command to simulate a trading policy with `run_sim.py`, using config files in `configs/simulation` and `configs/policy`.
3. Run command to view performance statistics of the trading simulation with `run_stats.py`, using config files in `configs/stats`.

Note: 

- Before running these commands, ensure that you have generated the necessary residuals using the instructions in the "Generating residuals" section above.
- The commands assume that the main directory of the project is the current working directory.
- Only GPUs devices are supported. You can specify a specific space-separated list of GPU device IDs to use by employing the `-g` flag, e.g. `python3 run_sim.py -c configs/simulation/config-dlap.yaml -cm configs/policy/cnntransformer.yaml -g 0 1 2`. 
- Some of the results require prior results to be generated. When appropriate, this will be noted in the description for each result.
- Some results are generated for specific models, denoted by `{model_name}`. To specify a model, use the following strings in place of `{model_name}`:
  - `cnntransformer`
  - `fourierffn`
  - `outhreshold`
- Many results, such as plots, are saved with a `model_tag`, a string containing the factor model, trading policy, and other information about the simulation.

Note that some results may be different if different architectures, OSes, seeds, hardware, etc. are used.

We give two options for replication below in the following instructions.


### Replication instructions

**Partial replication.** To stay within reasonable time and resource limits for a replication, we provide source data, estimated residuals, and estimated models which can be run to replicate the results for the IPCA 5-factor residuals and CNN+Transformer trading policy, which is the main model analyzed in the paper, in this paragraph. Please note that the source data released in this code package has been perturbed by noise in order to prevent recovery of the true returns, etc. of each asset. This step is performed to comply with our vendors' data licenses, which prevent us from releasing the raw source data. As a consequence, some results will differ from those reported in the paper, but we expect them to be fairly characteristically similar. To replicate these results, run each of the commands in each of the subsections below, entitled e.g. Table 1, Table 2, ..., Figure 5, etc. For some figures describing not to the results, but the analysis of the models, code is located in the Jupyter notebooks referenced.

**Full replication.** For a full replication, first, note that multiple weeks of computation and terabytes of storage will be required on the suggested hardware. To fully replicate results for each of the given commands below, please remove "-replication" from the simulation config file name, and add all numbers of factors for each factor model desired to the resulting config file (e.g. [1, 3, 5, 8, 10, 15]). Then update stats config files to point to the results directories specified in each full replication simulation config file. Finally, run the commands in each of the sections, just as you would for the partial replication outlined in the partial replication paragraph just above. We recommend utilizing a cluster of high-VRAM GPU nodes and parallelizing all computation if full replication is desired.


### Table 1

To replicate the results for each trading policy model in Table 1, run the following commands:

CNN+Transformer
```
python3 run_sim.py -c configs/simulation/config-dlap-replication.yaml -cm configs/policy/cnntransformer.yaml
```
Fourier+FFN
```
python3 run_sim.py -c configs/simulation/config-dlap-replication.yaml -cm configs/policy/fourierffn.yaml
```
OU+Thresh
```
python3 run_sim.py -c configs/simulation/config-dlap-nontrainable-replication.yaml -cm configs/policy/outhreshold.yaml
```

### Table 2

This requires the results for Table 1 to be generated first. To generate Table 2 for each model, run the following command:
```
python3 run_stats.py -c configs/stats/stats-main.yaml
```

### Figure 5

Run the Table 1 section above. Plots are automatically saved to the specified results subdirectory with names `{model-tag}_cumulative-returns.png`.

### Table 3

CNN+Transformer
```
python3 run_sim.py -c configs/simulation/config-dlap-meanvar-replication.yaml -cm configs/policy/cnntransformer.yaml
```
Fourier+FFN
```
python3 run_sim.py -c configs/simulation/config-dlap-meanvar-replication.yaml -cm configs/policy/fourierffn.yaml
```

### Table 4

This requires the results for Table 3 to be generated first. To generate Table 4 for each model, run the following command:
```
python3 run_stats.py -c configs/stats/stats-meanvar.yaml
```

### Table 5

CNN+Transformer
```
python3 run_sim.py -c configs/simulation/config-dlap-lookback60-replication.yaml -cm configs/policy/cnntransformer-lookback60.yaml
```

### Table 6

This requires the results for Table 5 to be generated first. To generate Table 6 for each model, run the following command:
```
python3 run_stats.py -c configs/stats/stats-lookback60.yaml
```

### Table 7

CNN+Transformer 4-year:
```
python3 run_sim.py -c configs/simulation/config-dlap-constant-4year-replication.yaml -cm configs/policy/cnntransformer.yaml
```
CNN+Transformer 8-year:
```
python3 run_sim.py -c configs/simulation/config-dlap-constant-8year-replication.yaml -cm configs/policy/cnntransformer.yaml
```

### Table 8

This requires the results for Table 7 to be generated first. To generate Table 8 for each model, run the following command:

CNN+Transformer 4-year:
```
python3 run_stats.py -c configs/stats/stats-constant-4year.yaml
```
CNN+Transformer 8-year:
```
python3 run_stats.py -c configs/stats/stats-constant-8year.yaml
```

### Table 9

CNN+Transformer
```
python3 run_sim.py -c configs/simulation/config-dlap-frictions-replication.yaml -cm configs/policy/cnntransformer-frictions.yaml
```

### Figure 6

For subfigure (a), run Table 1. Plots are automatically saved to the specified results subdirectory with names `{model_tag}_turnover.png`. 
For subfigure (b), run Table 9. Plots are automatically saved to the specified results subdirectory with names `{model_tag}_turnover.png`.

### Figure 7

For subfigure (a), run Table 1. Plots are automatically saved to the specified results subdirectory with names `{model_tag}_short-proportion.png`. 
For subfigure (b), run Table 9. Plots are automatically saved to the specified results subdirectory with names `{model_tag}_short-proportion.png`.

### Figure 8

See `notebooks/strategy-analysis.ipynb`.

### Figure 9

See `notebooks/strategy-analysis.ipynb`.

### Figure 10

See `notebooks/strategy-analysis.ipynb`.

### Figure 11

See `notebooks/strategy-analysis.ipynb`.

### Figure 12

See `notebooks/strategy-analysis.ipynb`.

We already include results, but they may also be partially replicated with the following commands:

Panel A:
```
python3 run_sim.py -c configs/simulation/config-dlap-overlapping-replication.yaml -cm configs/policy/cnntransformer.yaml
```
Panel B:
```
python3 run_sim.py -c configs/simulation/config-dlap-multiholding-replication.yaml -cm configs/policy/cnntransformer.yaml
```

### Figure 13

See `notebooks/strategy-analysis.ipynb`.

### Figure 14

See `notebooks/signal-visualization.ipynb`.

### Figure 15

See `notebooks/signal-visualization.ipynb`.

### Figure 16

See `notebooks/signal-visualization.ipynb`.

### Figure 17

See `notebooks/signal-visualization.ipynb`.

### Figure 18

See `notebooks/signal-visualization.ipynb`.

### Figure 19

See `notebooks/signal-visualization.ipynb`.


# License

Any use of this software or derivations thereof for commercial purposes is prohibited. Exceptions may be approved via email by Greg Zanotti and Jorge Guijarro-Ordonez.


