#!/usr/bin/env python3
"""Script to generate statistics and tables for model results."""

import argparse
import glob
import io
import os
import pickle
import re
import traceback
import zipfile
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
import torch
import yaml
from scipy.stats import ttest_1samp
from tabulate import tabulate


def extract_factor_model_info(s: str) -> Tuple[str, int]:
    """Extract factor model name and number from string."""
    if s.startswith('FamaFrench'):
        return 'FamaFrench', int(s[len('FamaFrench'):])
    elif s.startswith('IPCA'):
        return 'IPCA', int(s[len('IPCA'):])
    elif s.startswith('PCA'):
        return 'PCA', int(s[len('PCA'):])
    else:
        raise ValueError(f"Unknown factor model in string: {s}")


def load_results(filepath: str) -> Any:
    """Load results from pickle file."""
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def compute_statistics(returns: np.ndarray) -> Dict[str, float]:
    """Compute basic statistics for returns."""
    annual_factor = np.sqrt(252)  # Annualization factor for daily returns
    mean_return = np.mean(returns) * 252  # Annualized mean return
    volatility = np.std(returns) * annual_factor  # Annualized volatility
    sharpe = mean_return / volatility
    
    # T-test against zero
    t_stat, p_value = sm.stats.ttest_1samp(returns, 0)
    
    return {
        'mean_return': mean_return,
        'volatility': volatility,
        'sharpe': sharpe,
        't_stat': t_stat,
        'p_value': p_value
    }


def perform_regression(returns: np.ndarray, factors: np.ndarray) -> sm.regression.linear_model.OLS:
    """
    Perform regression analysis of returns on factors.

    Args:
        returns (np.ndarray): Returns of the assets of shape (T,).
        factors (np.ndarray): Factors to be used in the regression of shape (T, L).
        
    Returns:
        sm.regression.linear_model.OLS: Regression results.
    """
    X = sm.add_constant(factors)
    model = sm.OLS(returns, X)
    results = model.fit()
    return results


def download_and_process_ff8_factors(output_path: str) -> pd.DataFrame:
    """
    Download and process Fama-French 8 factors from Kenneth French's website.
    
    Downloads the required CSV files, processes them to extract the factor returns,
    and combines them into a single DataFrame with aligned dates.
    
    Args:
        output_path (str): Path where to save the processed CSV file.
        
    Returns:
        pd.DataFrame: DataFrame containing the 8 factors.
    """
    # URLs for the factor data
    urls = {
        'FF5': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip',
        'MOM': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip',
        'LTR': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_LT_Reversal_Factor_daily_CSV.zip',
        'STR': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_ST_Reversal_Factor_daily_CSV.zip'
    }
    
    factor_dfs = {}
    common_dates = None
    
    for factor_name, url in urls.items():
        # Download and extract the ZIP file
        response = requests.get(url)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download {factor_name} factors from {url}")
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            csv_name = zip_file.namelist()[0]  # Get the first file in the ZIP
            with zip_file.open(csv_name) as csv_file:
                # Read all lines to find where the data starts and ends
                lines = [line.decode('utf-8').strip() for line in csv_file.readlines()]
                
                # Find the first line that starts with a date (YYYY or MM/DD/YYYY format)
                start_idx = 0
                for i, line in enumerate(lines):
                    if re.match(r'^(\d{8}|\d{1,2}/\d{1,2}/\d{4})', line):
                        start_idx = i
                        break
                
                # Find the last line of data by looking for the last line with numbers
                # A data line should have at least one number and commas
                end_idx = start_idx
                for i in range(start_idx, len(lines)):
                    line = lines[i]
                    if line and ',' in line and any(c.isdigit() for c in line):
                        end_idx = i
                
                # Create DataFrame from the data portion (including header row)
                data_lines = [lines[start_idx-1]] + [line for line in lines[start_idx:end_idx+1] 
                                                    if line and not line.isspace()]  # Skip blank lines
                df = pd.read_csv(io.StringIO('\n'.join(data_lines)))
                
                # First column is always the date
                date_col = df.columns[0]
                
                # Convert date formats to YYYYMMDD
                if '/' in str(df[date_col].iloc[0]):
                    df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y%m%d')
                else:
                    # Skip data with only YYYY format
                    print(f"Warning: Skipping rows with YYYY format in {factor_name} data")
                    df = df[df[date_col].astype(str).str.len() == 8]
                
                # Rename date column to DATE
                df = df.rename(columns={date_col: 'DATE'})
                
                # Set index but keep DATE as a column too
                df = df.set_index('DATE')
                
                if factor_name == 'FF5':
                    # Keep Mkt-RF (renamed to MKT-RF), SMB, HML, RMW, CMA
                    df = df.iloc[:, :5]
                    df = df.rename(columns={'Mkt-RF': 'MKT-RF'})
                    factor_dfs[factor_name] = df
                else:
                    # Keep only the factor column (last column for MOM, LTR, STR)
                    factor_name_map = {'MOM': 'MOM', 'LTR': 'LTR', 'STR': 'STR'}
                    factor_dfs[factor_name] = df.iloc[:, -1].to_frame(factor_name_map[factor_name])
                
                # Update common dates
                if common_dates is None:
                    common_dates = set(df.index)
                else:
                    common_dates &= set(df.index)
    
    # Filter all DataFrames to common dates
    for factor_name in factor_dfs:
        factor_dfs[factor_name] = factor_dfs[factor_name].loc[sorted(common_dates)]
    
    # Combine all factors
    ff8 = pd.concat([factor_dfs['FF5'], 
                    factor_dfs['MOM'], 
                    factor_dfs['LTR'], 
                    factor_dfs['STR']], axis=1)
    
    # Convert to decimal format (original data is in percentages)
    ff8 = ff8 / 100
    
    # Round to 8 decimal places to avoid floating point precision issues
    ff8 = ff8.round(8)
    
    # Sort by date
    ff8 = ff8.sort_index()
    
    # Save to CSV with controlled float format
    ff8.to_csv(output_path, float_format='%.8f')
    
    return ff8


def analyze_ff8_regression(returns: np.ndarray, start_date: int, end_date: int, dates: np.ndarray) -> Dict[str, Any]:
    """Perform Fama-French 8-factor regression analysis.
    
    Args:
        returns (np.ndarray): Array of returns to analyze of shape (T,)
        start_date (int): Start date in YYYYMMDD format
        end_date (int): End date in YYYYMMDD format
        dates (np.ndarray): Array of dates in YYYYMMDD format of shape (T,)
        
    Returns:
        dict: Dictionary containing regression results and factor exposures
    """
    ff8_path = "FamaFrench8Daily.csv"
    start_date = pd.to_datetime(start_date, format='%Y%m%d')
    end_date = pd.to_datetime(end_date, format='%Y%m%d')
    
    # Load or download FF8 factors
    if not os.path.exists(ff8_path):
        print("FamaFrench8Daily.csv not found. Downloading from Kenneth French's website...")
        ff8 = download_and_process_ff8_factors(ff8_path)
    else:
        ff8 = pd.read_csv(ff8_path, index_col=0, parse_dates=['DATE'])
    
    if dates is not None:
        # Convert dates to same format as FF8 index
        dates = pd.to_datetime(dates, format='%Y%m%d')
        dates_df = pd.DataFrame({'date': dates, 'returns': returns})
        # Find intersection of dates
        common_dates = np.intersect1d(dates_df['date'], ff8.index)
    else:
        # Use start_date and end_date to filter FF8 dates
        common_dates = ff8.index[(start_date <= ff8.index) & (ff8.index <= end_date)]
        if len(returns) != len(common_dates):
            print(f"Error: length of returns is {len(returns)} and length of common_dates is {len(common_dates)}")
            raise ValueError("Number of returns and dates does not match; edit start_date and end_date in code to match returns")
        # Create DataFrame from returns and dates
        dates_df = pd.DataFrame({'date': common_dates, 'returns': returns})
    
    # Filter both returns and factors to common dates
    dates_df = dates_df.set_index('date')
    returns_aligned = dates_df.loc[common_dates, 'returns']
    ff8_aligned = ff8.loc[common_dates]
    
    # Perform regression
    reg_results = perform_regression(returns_aligned, ff8_aligned)
    
    # Extract key statistics
    factor_exposures = reg_results.params.iloc[1:]  # Skip intercept
    t_stats = reg_results.tvalues.iloc[1:]  # Skip intercept
    r_squared = reg_results.rsquared
    adj_r_squared = reg_results.rsquared_adj
    
    return {
        'alpha': reg_results.params.iloc[0] * 252,
        'alpha_tstat': reg_results.tvalues.iloc[0],
        'alpha_pvalue': reg_results.pvalues.iloc[0],
        'factor_exposures': factor_exposures,
        't_statistics': t_stats,
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared
    }


def extract_model_info(key: str) -> Tuple[str, int, str]:
    """Extract factor model, number of factors, and trading policy from a result key.
    
    Example key format:
    'IPCA5__CNNTransformer__comp_mtx__0.01cap__sharpe__0trans_cost__0hold_cost__30lookback__1000length_training__1holding_days__replication__full-lab'

    Args:
        key (str): The result key from which to extract information.
    
    Returns:
        Tuple[str, int, str]: A tuple containing the factor model, number of factors, and trading policy.
    """
    try:
        # First part contains factor model and number
        model_part = key.split('__')[0]
        # Extract factor model name and number
        if model_part.startswith('IPCA'):
            factor_model = 'IPCA'
            n_factors = int(model_part[4:])
        elif model_part.startswith('PCA'):
            factor_model = 'PCA'
            n_factors = int(model_part[3:])
        elif model_part.startswith('FamaFrench'):
            factor_model = 'FamaFrench'
            n_factors = int(model_part[10:])
        else:
            return None
            
        # Extract trading policy model
        trading_policy = key.split('__')[1]
        
        return factor_model, n_factors, trading_policy
    except (IndexError, ValueError):
        return None


def discover_factor_models(results_dir: str) -> Dict[Tuple[str, int], Tuple[str, float, str]]:
    """
    Discover available factor models in a directory by examining all pickle files.

    Args:
        results_dir (str): Directory containing pickle files with results.
    
    Returns:
        Dict[Tuple[str, int], Tuple[str, float, str]]: Dictionary mapping (factor_model, n_factors) tuple to (filepath, mtime, latest_key).
    """
    factor_models = {}  # (factor_model, n_factors) -> (filepath, mtime, latest_key)
    
    # Look at all pickle files in the directory
    pickle_files = glob.glob(os.path.join(results_dir, "results_*.pickle"))
    
    for filepath in pickle_files:
        try:
            # Get file modification time
            mtime = os.path.getmtime(filepath)
            
            # Load results
            results = load_results(filepath)
            
            # Process each key in the results
            for key in results.keys():
                model_info = extract_model_info(key)
                if model_info is None:
                    continue
                    
                factor_model, n_factors, trading_policy = model_info
                result_key = (factor_model, n_factors)
                
                # Update if this is a newer file for this combo
                if result_key not in factor_models or mtime > factor_models[result_key][1]:
                    factor_models[result_key] = (filepath, mtime, key)
                    
        except Exception as e:
            print(f"Warning: Error processing {filepath}: {str(e)}")
            continue
    
    # Sort the factor models by model type and number
    def sort_key(item):
        (factor_model, n_factors), _ = item
        # Order: IPCA, PCA, FamaFrench
        model_order = {
            'IPCA': 0, 
            'PCA': 1, 
            'FamaFrench': 2
        }
        # Return tuple of (model order, factor number) for proper sorting
        return (model_order[factor_model], int(n_factors))
    
    return dict(sorted(factor_models.items(), key=sort_key))


def extract_run_id(filepath: str) -> str:
    """Extract run_id from a results filepath."""
    try:
        # Extract the part between results_ and .pickle
        filename = os.path.basename(filepath)
        parts = filename.replace('results_', '').replace('.pickle', '').split('_')
        
        # The run_id is the part right after "results_"
        # e.g., from "results_full-lab_1737679472_replication.pickle"
        # we want "full-lab"
        if len(parts) >= 2:
            return parts[0]
    except Exception:
        pass
    return None


def pvalue_to_stars(p: float) -> str:
    """Convert p-value to significance stars."""
    if p > 0.05:
        return ""
    if p <= 0.001:
        return "***"
    if p <= 0.01:
        return "**"
    if p <= 0.05:
        return "*"


def format_stat(x: float) -> str:
    """Format numeric statistics."""
    if abs(x) <= 9.9:
        return f"{x:0.1f}"
    else:
        return f"{x:0.2g}"


def sort_result_key(key: str) -> Tuple[int, int, int]:
    """
    Sort result keys by policy model and factor model.

    Args:
        key (str): The result key to sort.

    Returns:
        Tuple[int, int, int]: A tuple of (policy order, model order, factor number) for proper sorting.
    """
    policy, factor_model_str = key.split('_')
    
    # Extract factor model name and number
    if factor_model_str.startswith('IPCA'):
        factor_model = 'IPCA'
        n_factors = int(factor_model_str[4:])
    elif factor_model_str.startswith('PCA'):
        factor_model = 'PCA'
        n_factors = int(factor_model_str[3:])
    elif factor_model_str.startswith('FamaFrench'):
        factor_model = 'FamaFrench'
        n_factors = int(factor_model_str[10:])
    else:
        return (float('inf'), float('inf'), float('inf'))
    
    # Order: CNNTransformer, FourierFFN, OUThreshold
    policy_order = {
        'CNNTransformer': 0,
        'FourierFFN': 1,
        'OUThreshold': 2
    }
    # Order: IPCA, PCA, FamaFrench
    model_order = {
        'FamaFrench': 0,
        'PCA': 1,
        'IPCA': 2,
    }
    
    return (policy_order.get(policy, float('inf')), 
            model_order.get(factor_model, float('inf')), 
            int(n_factors))


def main(config_path: Optional[str] = None):
    """Main function to process results and generate statistics."""
    print("Running stats...")
    
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'configs', 'stats-config.yaml')
    
    # Load configuration from YAML file
    with open(config_path, 'r') as f:
        CONFIG = yaml.safe_load(f)

    # Sort trading policy models
    model_order = {
        'CNNTransformer': 0, 
        'FourierFFN': 1, 
        'OUThreshold': 2
    }
    CONFIG = dict(sorted(CONFIG.items(), key=lambda x: model_order.get(x[0], float('inf'))))

    results_data = {}
    plot_files = []
    
    print("\nProcessing results for each model configuration...")
    print("=" * 80)

    # Process each trading policy model
    for model_key, model_config in CONFIG.items():
        results_dir = os.path.join(model_config['results_dir'], model_key)
        run_id = model_config.get('run_id', '')
        tag = model_config.get('tag', '')
        
        print(f"\nProcessing {model_key} in {results_dir}")
        
        # Discover available factor models in this directory
        factor_models = discover_factor_models(results_dir)
        if not factor_models:
            print(f"Warning: No factor model results found in {results_dir}")
            continue
            
        # Process each factor model's results
        for (factor_model, n_factors), (filepath, _, latest_key) in factor_models.items():
            result_key = f"{model_key}_{factor_model}{n_factors}"
            
            try:
                # Set file's run_id or extract from filename
                if run_id:
                    file_run_id = run_id
                else:
                    file_run_id = extract_run_id(filepath)
                if file_run_id is None:
                    continue
                
                # Load results
                results = load_results(filepath)
                
                # Get the results for this specific key
                result = results[latest_key]
                
                # Extract returns and dates
                returns = result.get('returns', None)
                dates = result.get('dates', None)
                if returns is None:
                    print(f"Warning: Missing returns in results for {result_key} {file_run_id}{' ' + tag if tag else ''}! Skipping...")
                    continue
                
                if dates is None:
                    print(f"Warning: Missing dates in results for {result_key} {file_run_id} {tag if tag else ''}"
                          "; assuming start and end date are 2001-12-26 and 2016-12-30.")
                    start_date = 20011226
                    end_date = 20161230
                else:
                    start_date = dates[0]
                    end_date = dates[-1]
                
                # Convert torch tensors to numpy if needed
                if isinstance(returns, torch.Tensor):
                    returns = returns.numpy()
                if isinstance(dates, torch.Tensor):
                    dates = dates.numpy()
                if isinstance(result['sharpe'], torch.Tensor):
                    result['sharpe'] = result['sharpe'].item()
                if isinstance(result['ret'], torch.Tensor):
                    result['ret'] = result['ret'].item()
                if isinstance(result['std'], torch.Tensor):
                    result['std'] = result['std'].item()
                
                # stats = compute_statistics(returns)
                stats = {
                    'sharpe': float(result['sharpe']),
                    'mean_return': float(result['ret']),
                    'volatility': float(result['std']),
                }
                
                # perform t-test on returns
                test_results = ttest_1samp(returns, 0)
                test_stats = {
                    't_stat': float(test_results.statistic),
                    'p_value': float(test_results.pvalue),
                }
                
                ff8_analysis = analyze_ff8_regression(returns, start_date, end_date, dates)
                
                # Store results
                results_data[result_key] = {
                    'filepath': filepath,
                    'stats': stats,
                    'test_stats': test_stats,
                    'ff8_analysis': ff8_analysis,
                    'returns': returns,
                }
                
                if tag:
                    plot_pattern = f"{factor_model}{n_factors}__{model_key}__*__{tag}__*__{file_run_id}_*.png"
                else:
                    plot_pattern = f"{factor_model}{n_factors}__{model_key}__*__{file_run_id}_*.png"
                    
                # Look for plot files with matching factor model and run_id
                model_plot_files = glob.glob(os.path.join(results_dir, plot_pattern))
                plot_files.extend(model_plot_files)
            
            except Exception as e:
                print(f"Error processing {result_key}: {str(e)}")
                print(f"Error details: {e}")
                print(traceback.format_exc())
                continue

    if not results_data:
        print("\nNo valid results found to analyze!")
        return

    # Display source files for each result
    print("\nSource files used for each model:")
    print("=" * 80)
    for result_key in sorted(results_data.keys(), key=sort_result_key):
        filepath = results_data[result_key]['filepath']
        print(f"  {result_key}: {filepath}")

    # Display plot files
    if plot_files:
        print("\nAvailable Plot Files:")
        print("=" * 80)
        for plot_file in sorted(plot_files):
            print(f"  {os.path.basename(plot_file)}")

    # Create and display basic metrics table
    stats_data = []
    for result_key in sorted(results_data.keys(), key=sort_result_key):
        data = results_data[result_key]
        stats = data['stats']
        # Get file modification time
        filepath = data['filepath']
        mtime = os.path.getmtime(filepath)
        last_update = pd.to_datetime(mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S')
        stats_data.append({
            'Policy': result_key.split('_')[0],
            'Factor Model': result_key.split('_')[1],
            'Sharpe': f"{stats['sharpe']:.2f}",
            'Mean Return (%)': f"{stats['mean_return']*100:.1f}%",
            'Volatility (%)': f"{stats['volatility']*100:.1f}%",
            'Last Update': last_update,
        })
    
    stats_df = pd.DataFrame(stats_data)
    print("\nPerformance Metrics Table:")
    print("=" * 80)
    # Print table for basic stats
    print(tabulate(stats_df, headers='keys', tablefmt='grid'))
    # print(stats_df.to_string(index=False))
    
    # Create and display regression results and statistics table
    reg_data = []
    for result_key in sorted(results_data.keys(), key=sort_result_key):
        data = results_data[result_key]
        ff8 = data['ff8_analysis']
        stats = data['stats']
        test_stats = data['test_stats']
        reg_data.append({
            'Policy': result_key.split('_')[0],
            'Factor Model': result_key.split('_')[1],
            'Mean (%)': f"{format_stat(stats['mean_return']*100)}%",
            'Mean t-stat': f"{format_stat(test_stats['t_stat'])}{pvalue_to_stars(test_stats['p_value'])}",
            'Alpha (%)': f"{format_stat(ff8['alpha']*100)}%",
            'Alpha t-stat': f"{format_stat(ff8['alpha_tstat'])}{pvalue_to_stars(ff8['alpha_pvalue'])}",
            'R^2 (%)': f"{format_stat(ff8['r_squared']*100)}%",
            'Adj R^2 (%)': f"{format_stat(ff8['adj_r_squared']*100)}%",
            # 'MKT t-stat': f"{ff8['t_statistics'][0]:.2f}{pvalue_to_stars(ff8['t_statistics'][1])}",
        })
    
    reg_df = pd.DataFrame(reg_data)
    print("\nPerformance Regression Results and Statistics Table:")
    print("=" * 80)
    # print(reg_df.to_string(index=False))
    print(tabulate(reg_df, headers='keys', tablefmt='grid'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate statistics for model results")
    parser.add_argument("--config", "-c", type=str, help="Path to custom yaml configuration file")
    args = parser.parse_args()
    
    main(args.config)
