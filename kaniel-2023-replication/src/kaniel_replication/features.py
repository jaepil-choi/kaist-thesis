"""Carhart abnormal returns and parsimonious fund predictors."""

from __future__ import annotations

import numpy as np
import pandas as pd


FACTOR_COLUMNS = ["mkt_rf", "smb", "hml", "mom"]


def validate_factor_input(factors: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize a monthly Carhart factor table."""

    required = {"month", "rf", *FACTOR_COLUMNS}
    missing = sorted(required.difference(factors.columns))
    if missing:
        raise ValueError(f"Factor input is missing columns: {missing}")
    clean = factors.copy()
    clean["month"] = pd.to_datetime(clean["month"], errors="raise")
    if clean["month"].duplicated().any():
        raise ValueError("Factor input has duplicate months")
    for column in ["rf", *FACTOR_COLUMNS]:
        clean[column] = pd.to_numeric(clean[column], errors="raise")
    return clean.sort_values("month").reset_index(drop=True)


def compute_carhart_abnormal_returns(
    panel: pd.DataFrame,
    factors: pd.DataFrame,
    window: int = 36,
    minimum_history: int = 30,
) -> pd.DataFrame:
    """Estimate prior-window betas and compute current-month abnormal returns.

    The regression includes an intercept, but Eq. (2) subtracts only current
    factor compensation from the fund excess return.
    """

    required = {"fund_code", "month", "monthly_return"}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"Panel is missing columns: {missing}")
    factors = validate_factor_input(factors)
    merged = panel.copy()
    merged["month"] = pd.to_datetime(merged["month"], errors="raise")
    merged = merged.merge(factors, on="month", how="left", validate="many_to_one")
    merged = merged.sort_values(["fund_code", "month"]).reset_index(drop=True)
    merged["abnormal_return"] = np.nan

    for _, locations in merged.groupby("fund_code", sort=False).groups.items():
        positions = np.asarray(locations)
        fund = merged.loc[positions]
        for offset, position in enumerate(positions):
            history = fund.iloc[max(0, offset - window) : offset]
            valid = history[["monthly_return", "rf", *FACTOR_COLUMNS]].notna().all(axis=1)
            history = history.loc[valid]
            current = merged.loc[position, ["monthly_return", "rf", *FACTOR_COLUMNS]]
            if len(history) < minimum_history or current.isna().any():
                continue
            y = (history["monthly_return"] - history["rf"]).to_numpy(dtype=float)
            x_factors = history[FACTOR_COLUMNS].to_numpy(dtype=float)
            x = np.column_stack([np.ones(len(history)), x_factors])
            coefficients, *_ = np.linalg.lstsq(x, y, rcond=None)
            current_excess = float(current["monthly_return"] - current["rf"])
            factor_compensation = float(
                np.dot(current[FACTOR_COLUMNS].to_numpy(dtype=float), coefficients[1:])
            )
            merged.at[position, "abnormal_return"] = current_excess - factor_compensation

    return merged


def add_fund_momentum_features(
    panel: pd.DataFrame,
    minimum_momentum_observations: int = 8,
) -> pd.DataFrame:
    """Add the three fund-momentum variables from Table 2."""

    required = {"fund_code", "month", "abnormal_return"}
    missing = sorted(required.difference(panel.columns))
    if missing:
        raise ValueError(f"Panel is missing columns: {missing}")
    result = panel.sort_values(["fund_code", "month"]).copy()
    grouped = result.groupby("fund_code", sort=False)["abnormal_return"]
    result["F_ST_Rev"] = grouped.shift(0)
    result["F_r2_1"] = grouped.shift(1)

    shifted = grouped.shift(2)
    result["F_r12_2"] = (
        shifted.groupby(result["fund_code"], sort=False)
        .rolling(window=11, min_periods=minimum_momentum_observations)
        .mean()
        .reset_index(level=0, drop=True)
    )
    return result
