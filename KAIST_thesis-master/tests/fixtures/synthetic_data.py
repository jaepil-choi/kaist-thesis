"""
Synthetic data generation for Fama-MacBeth regression tests.

Generates 7 test cases covering various real-world scenarios:
1. Perfect data - fully filled, no missing values
2. Missing peer returns - TNIC returns missing for first 12 months
3. New listing - security appears mid-sample
4. Delisting - security disappears mid-sample
5. Annual characteristics - log(ME), log(BE/ME) step functions
6. Trading halt - random NaN in return series
7. Too few securities - insufficient cross-sectional observations
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta


def _generate_dates(n_periods: int = 41, start_year: int = 2010) -> pd.DatetimeIndex:
    """Generate monthly date range."""
    start_date = datetime(start_year, 1, 31)
    dates = pd.date_range(start=start_date, periods=n_periods, freq='ME')  # Month end
    return dates


def _generate_securities(n_securities: int = 5) -> list:
    """Generate security IDs."""
    return [f'SEC{str(i).zfill(3)}' for i in range(1, n_securities + 1)]


def _generate_returns(
    dates: pd.DatetimeIndex,
    securities: list,
    mean: float = 0.01,
    std: float = 0.05,
    seed: int = 42
) -> pd.DataFrame:
    """Generate synthetic monthly returns."""
    np.random.seed(seed)
    n_periods = len(dates)
    n_securities = len(securities)

    # Returns with some persistence (AR(1) process)
    returns = np.zeros((n_periods, n_securities))
    returns[0] = np.random.normal(mean, std, n_securities)

    for t in range(1, n_periods):
        # AR(1): r_t = 0.1 * r_{t-1} + epsilon
        returns[t] = 0.1 * returns[t-1] + np.random.normal(mean, std, n_securities)

    return pd.DataFrame(returns, index=dates, columns=securities)


def _generate_peer_returns(
    own_returns: pd.DataFrame,
    correlation: float = 0.3,
    seed: int = 43
) -> pd.DataFrame:
    """Generate peer returns correlated with own returns."""
    np.random.seed(seed)

    # Peer returns = correlation * own_returns + noise
    noise = pd.DataFrame(
        np.random.normal(0, 0.03, own_returns.shape),
        index=own_returns.index,
        columns=own_returns.columns
    )

    peer_returns = correlation * own_returns + np.sqrt(1 - correlation**2) * noise
    return peer_returns


def _generate_characteristics(
    dates: pd.DatetimeIndex,
    securities: list,
    annual_update: bool = True,
    seed: int = 44
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate log(ME) and log(BE/ME) characteristics.

    Parameters:
    -----------
    annual_update : bool
        If True, characteristics update once per year (step function)
        If False, characteristics vary monthly
    """
    np.random.seed(seed)
    n_periods = len(dates)
    n_securities = len(securities)

    if annual_update:
        # Generate annual values
        years = pd.Series(dates).dt.year.unique()
        n_years = len(years)

        # log(ME): varies by firm and year
        log_me_annual = np.random.uniform(12, 16, (n_years, n_securities))

        # log(BE/ME): varies by firm and year, negative to positive
        log_be_me_annual = np.random.uniform(-1, 1, (n_years, n_securities))

        # Broadcast to monthly
        log_me = np.zeros((n_periods, n_securities))
        log_be_me = np.zeros((n_periods, n_securities))

        for i, date in enumerate(dates):
            year_idx = np.where(years == date.year)[0][0]
            log_me[i] = log_me_annual[year_idx]
            log_be_me[i] = log_be_me_annual[year_idx]

        log_me_df = pd.DataFrame(log_me, index=dates, columns=securities)
        log_be_me_df = pd.DataFrame(log_be_me, index=dates, columns=securities)

    else:
        # Monthly variation
        log_me_df = pd.DataFrame(
            np.random.uniform(12, 16, (n_periods, n_securities)),
            index=dates,
            columns=securities
        )
        log_be_me_df = pd.DataFrame(
            np.random.uniform(-1, 1, (n_periods, n_securities)),
            index=dates,
            columns=securities
        )

    return log_me_df, log_be_me_df


def generate_perfect_data(
    n_securities: int = 5,
    n_periods: int = 41,
    seed: int = 100
) -> Dict[str, pd.DataFrame]:
    """
    Test Case 1: Perfect data with no missing values.

    All securities have complete data for all periods.
    """
    dates = _generate_dates(n_periods)
    securities = _generate_securities(n_securities)

    returns = _generate_returns(dates, securities, seed=seed)
    tnic_ret = _generate_peer_returns(returns, correlation=0.4, seed=seed+1)
    sic_ret = _generate_peer_returns(returns, correlation=0.3, seed=seed+2)
    log_me, log_be_me = _generate_characteristics(dates, securities, annual_update=True, seed=seed+3)

    # Past returns
    ret_t1 = returns.shift(1)
    ret_t2_t12 = returns.rolling(window=11, min_periods=1).mean().shift(2)

    return {
        'returns': returns,
        'tnic_ret': tnic_ret,
        'sic_ret': sic_ret,
        'log_me': log_me,
        'log_be_me': log_be_me,
        'ret_t1': ret_t1,
        'ret_t2_t12': ret_t2_t12,
        'description': 'Perfect data - no missing values'
    }


def generate_missing_peer_data(
    n_securities: int = 5,
    n_periods: int = 41,
    seed: int = 200
) -> Dict[str, pd.DataFrame]:
    """
    Test Case 2: Missing peer returns for first 12 months.

    Simulates scenario where TNIC peer relationships not yet calculated
    for early periods.
    """
    dates = _generate_dates(n_periods)
    securities = _generate_securities(n_securities)

    returns = _generate_returns(dates, securities, seed=seed)
    tnic_ret = _generate_peer_returns(returns, correlation=0.4, seed=seed+1)
    sic_ret = _generate_peer_returns(returns, correlation=0.3, seed=seed+2)
    log_me, log_be_me = _generate_characteristics(dates, securities, seed=seed+3)

    # TNIC returns missing for first 12 months
    tnic_ret.iloc[:12, :] = np.nan

    ret_t1 = returns.shift(1)
    ret_t2_t12 = returns.rolling(window=11, min_periods=1).mean().shift(2)

    return {
        'returns': returns,
        'tnic_ret': tnic_ret,
        'sic_ret': sic_ret,
        'log_me': log_me,
        'log_be_me': log_be_me,
        'ret_t1': ret_t1,
        'ret_t2_t12': ret_t2_t12,
        'description': 'TNIC peer returns missing for first 12 months'
    }


def generate_new_listing_data(
    n_securities: int = 5,
    n_periods: int = 41,
    listing_month: int = 10,
    seed: int = 300
) -> Dict[str, pd.DataFrame]:
    """
    Test Case 3: New listing - security appears mid-sample.

    Last security (SEC005) lists at month 10, all data NaN before that.
    """
    dates = _generate_dates(n_periods)
    securities = _generate_securities(n_securities)

    returns = _generate_returns(dates, securities, seed=seed)
    tnic_ret = _generate_peer_returns(returns, correlation=0.4, seed=seed+1)
    sic_ret = _generate_peer_returns(returns, correlation=0.3, seed=seed+2)
    log_me, log_be_me = _generate_characteristics(dates, securities, seed=seed+3)

    # Last security lists at listing_month
    new_listing_sec = securities[-1]
    returns.loc[:dates[listing_month-1], new_listing_sec] = np.nan
    tnic_ret.loc[:dates[listing_month-1], new_listing_sec] = np.nan
    sic_ret.loc[:dates[listing_month-1], new_listing_sec] = np.nan
    log_me.loc[:dates[listing_month-1], new_listing_sec] = np.nan
    log_be_me.loc[:dates[listing_month-1], new_listing_sec] = np.nan

    ret_t1 = returns.shift(1)
    ret_t2_t12 = returns.rolling(window=11, min_periods=1).mean().shift(2)

    return {
        'returns': returns,
        'tnic_ret': tnic_ret,
        'sic_ret': sic_ret,
        'log_me': log_me,
        'log_be_me': log_be_me,
        'ret_t1': ret_t1,
        'ret_t2_t12': ret_t2_t12,
        'description': f'{new_listing_sec} lists at month {listing_month}'
    }


def generate_delisting_data(
    n_securities: int = 5,
    n_periods: int = 41,
    delisting_month: int = 30,
    seed: int = 400
) -> Dict[str, pd.DataFrame]:
    """
    Test Case 4: Delisting - security disappears mid-sample.

    First security (SEC001) delists at month 30, all data NaN after that.
    """
    dates = _generate_dates(n_periods)
    securities = _generate_securities(n_securities)

    returns = _generate_returns(dates, securities, seed=seed)
    tnic_ret = _generate_peer_returns(returns, correlation=0.4, seed=seed+1)
    sic_ret = _generate_peer_returns(returns, correlation=0.3, seed=seed+2)
    log_me, log_be_me = _generate_characteristics(dates, securities, seed=seed+3)

    # First security delists at delisting_month
    delisted_sec = securities[0]
    returns.loc[dates[delisting_month]:, delisted_sec] = np.nan
    tnic_ret.loc[dates[delisting_month]:, delisted_sec] = np.nan
    sic_ret.loc[dates[delisting_month]:, delisted_sec] = np.nan
    log_me.loc[dates[delisting_month]:, delisted_sec] = np.nan
    log_be_me.loc[dates[delisting_month]:, delisted_sec] = np.nan

    ret_t1 = returns.shift(1)
    ret_t2_t12 = returns.rolling(window=11, min_periods=1).mean().shift(2)

    return {
        'returns': returns,
        'tnic_ret': tnic_ret,
        'sic_ret': sic_ret,
        'log_me': log_me,
        'log_be_me': log_be_me,
        'ret_t1': ret_t1,
        'ret_t2_t12': ret_t2_t12,
        'description': f'{delisted_sec} delists at month {delisting_month}'
    }


def generate_annual_characteristics_data(
    n_securities: int = 5,
    n_periods: int = 41,
    seed: int = 500
) -> Dict[str, pd.DataFrame]:
    """
    Test Case 5: Annual characteristics with step-function updates.

    log(ME) and log(BE/ME) update once per year, constant within year.
    """
    dates = _generate_dates(n_periods)
    securities = _generate_securities(n_securities)

    returns = _generate_returns(dates, securities, seed=seed)
    tnic_ret = _generate_peer_returns(returns, correlation=0.4, seed=seed+1)
    sic_ret = _generate_peer_returns(returns, correlation=0.3, seed=seed+2)

    # Key difference: annual_update=True creates step functions
    log_me, log_be_me = _generate_characteristics(dates, securities, annual_update=True, seed=seed+3)

    ret_t1 = returns.shift(1)
    ret_t2_t12 = returns.rolling(window=11, min_periods=1).mean().shift(2)

    return {
        'returns': returns,
        'tnic_ret': tnic_ret,
        'sic_ret': sic_ret,
        'log_me': log_me,
        'log_be_me': log_be_me,
        'ret_t1': ret_t1,
        'ret_t2_t12': ret_t2_t12,
        'description': 'Characteristics update annually (step function)'
    }


def generate_trading_halt_data(
    n_securities: int = 5,
    n_periods: int = 41,
    n_halts: int = 3,
    seed: int = 600
) -> Dict[str, pd.DataFrame]:
    """
    Test Case 6: Trading halts - random NaN in return series.

    Simulates sporadic missing returns due to trading suspensions.
    """
    np.random.seed(seed)
    dates = _generate_dates(n_periods)
    securities = _generate_securities(n_securities)

    returns = _generate_returns(dates, securities, seed=seed)
    tnic_ret = _generate_peer_returns(returns, correlation=0.4, seed=seed+1)
    sic_ret = _generate_peer_returns(returns, correlation=0.3, seed=seed+2)
    log_me, log_be_me = _generate_characteristics(dates, securities, seed=seed+3)

    # Introduce random NaN (trading halts) in middle of sample
    # Avoid first/last 5 periods to ensure some continuous data
    for sec in securities:
        halt_indices = np.random.choice(
            range(5, n_periods - 5),
            size=n_halts,
            replace=False
        )
        returns.iloc[halt_indices, returns.columns.get_loc(sec)] = np.nan

    ret_t1 = returns.shift(1)
    ret_t2_t12 = returns.rolling(window=11, min_periods=1).mean().shift(2)

    return {
        'returns': returns,
        'tnic_ret': tnic_ret,
        'sic_ret': sic_ret,
        'log_me': log_me,
        'log_be_me': log_be_me,
        'ret_t1': ret_t1,
        'ret_t2_t12': ret_t2_t12,
        'description': f'Trading halts - {n_halts} random NaN per security'
    }


def generate_too_few_securities_data(
    n_securities: int = 3,  # Deliberately small
    n_periods: int = 41,
    seed: int = 700
) -> Dict[str, pd.DataFrame]:
    """
    Test Case 7: Too few securities for cross-sectional regression.

    Only 3 securities, with some having missing data, resulting in
    insufficient observations for some time periods.
    """
    dates = _generate_dates(n_periods)
    securities = _generate_securities(n_securities)

    returns = _generate_returns(dates, securities, seed=seed)
    tnic_ret = _generate_peer_returns(returns, correlation=0.4, seed=seed+1)
    sic_ret = _generate_peer_returns(returns, correlation=0.3, seed=seed+2)
    log_me, log_be_me = _generate_characteristics(dates, securities, seed=seed+3)

    # Make it worse: add some missing data
    returns.iloc[10:15, 0] = np.nan  # SEC001 missing months 10-15
    returns.iloc[20:25, 1] = np.nan  # SEC002 missing months 20-25

    ret_t1 = returns.shift(1)
    ret_t2_t12 = returns.rolling(window=11, min_periods=1).mean().shift(2)

    return {
        'returns': returns,
        'tnic_ret': tnic_ret,
        'sic_ret': sic_ret,
        'log_me': log_me,
        'log_be_me': log_be_me,
        'ret_t1': ret_t1,
        'ret_t2_t12': ret_t2_t12,
        'description': f'Only {n_securities} securities with gaps'
    }


def get_all_test_cases() -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Generate all 7 test cases.

    Returns:
    --------
    test_cases : dict
        {case_name: case_data}
    """
    return {
        'perfect': generate_perfect_data(),
        'missing_peer': generate_missing_peer_data(),
        'new_listing': generate_new_listing_data(),
        'delisting': generate_delisting_data(),
        'annual_char': generate_annual_characteristics_data(),
        'trading_halt': generate_trading_halt_data(),
        'too_few_sec': generate_too_few_securities_data()
    }
