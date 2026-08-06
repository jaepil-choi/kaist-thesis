"""Parsimonious cross-out-of-sample prediction and portfolio construction."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import add_fund_momentum_features, compute_carhart_abnormal_returns


def cross_sectional_rank_normalize(values: pd.Series) -> pd.Series:
    """Map observed ranks to [-0.5, 0.5], preserving missing values."""

    result = pd.Series(np.nan, index=values.index, dtype=float)
    observed = values.dropna()
    if observed.empty:
        return result
    if len(observed) == 1:
        result.loc[observed.index] = 0.0
        return result
    ranks = observed.rank(method="average")
    result.loc[observed.index] = (ranks - 1.0) / (len(observed) - 1.0) - 0.5
    return result


def assign_month_folds(
    months: pd.Series | pd.DatetimeIndex,
    *,
    scheme: str,
    random_seed: int,
) -> pd.DataFrame:
    """Assign unique months to the paper's three random or chronological folds."""

    unique = np.array(sorted(pd.to_datetime(pd.Series(months).dropna().unique())))
    if len(unique) < 3:
        raise ValueError("At least three unique months are required")
    if scheme == "random":
        rng = np.random.default_rng(random_seed)
        ordered = rng.permutation(unique)
    elif scheme == "chronological":
        ordered = unique
    else:
        raise ValueError("scheme must be 'random' or 'chronological'")
    records = []
    for fold, values in enumerate(np.array_split(ordered, 3)):
        records.extend({"month": pd.Timestamp(value), "fold": fold} for value in values)
    return pd.DataFrame.from_records(records).sort_values("month").reset_index(drop=True)


def build_parsimonious_sample(
    panel: pd.DataFrame,
    factors: pd.DataFrame,
    sentiment: pd.DataFrame,
    *,
    rolling_window_months: int = 36,
    minimum_history_months: int = 30,
    momentum_minimum_observations: int = 8,
) -> pd.DataFrame:
    """Create time-t flow/momentum/sentiment inputs for time-t+1 abnormal returns."""

    abnormal = compute_carhart_abnormal_returns(
        panel,
        factors,
        window=rolling_window_months,
        minimum_history=minimum_history_months,
    )
    featured = add_fund_momentum_features(
        abnormal, minimum_momentum_observations=momentum_minimum_observations
    )
    macro = sentiment.copy()
    if not {"month", "sentiment"}.issubset(macro.columns):
        raise ValueError("sentiment input must contain month and sentiment")
    macro["month"] = pd.to_datetime(macro["month"], errors="raise")
    macro["sentiment"] = pd.to_numeric(macro["sentiment"], errors="raise")
    if macro["month"].duplicated().any():
        raise ValueError("sentiment input has duplicate months")
    result = featured.merge(macro, on="month", how="left", validate="many_to_one")
    result = result.sort_values(["fund_code", "month"]).reset_index(drop=True)
    grouped = result.groupby("fund_code", sort=False)
    result["realized_month"] = grouped["month"].shift(-1)
    result["target_abnormal_return"] = grouped["abnormal_return"].shift(-1)
    formation_period = result["month"].dt.to_period("M")
    realized_period = result["realized_month"].dt.to_period("M")
    nonconsecutive = (realized_period.astype("int64") - formation_period.astype("int64")).ne(1)
    result.loc[nonconsecutive, "target_abnormal_return"] = np.nan
    for column in ("flow", "F_r12_2"):
        if column not in result:
            raise ValueError(f"panel is missing parsimonious feature: {column}")
        result[f"rank_{column}"] = result.groupby("month", group_keys=False)[column].apply(
            cross_sectional_rank_normalize
        )
    return result


def fit_cross_oos_mlp(
    sample: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str = "target_abnormal_return",
    scheme: str = "random",
    random_seed: int = 202307,
    ensemble_size: int = 8,
    hidden_units: int = 64,
    learning_rate: float = 0.01,
    l2_penalty: float = 0.001,
    max_iter: int = 300,
) -> pd.DataFrame:
    """Fit fixed-paper-architecture MLPs and return one OOS prediction per row.

    This sklearn backend matches the single 64-unit ReLU layer, Adam learning
    rate, L2 penalty, and eight-fit ensemble. It does not implement the paper's
    0.95 dropout; that gap is intentionally documented by the caller.
    """

    required = {"month", target_column, *feature_columns}
    missing = sorted(required.difference(sample.columns))
    if missing:
        raise ValueError(f"sample is missing columns: {missing}")
    if ensemble_size < 1:
        raise ValueError("ensemble_size must be positive")
    complete = sample[list(required)].notna().all(axis=1)
    working = sample.loc[complete].copy()
    working["_source_index"] = working.index
    folds = assign_month_folds(
        working["month"], scheme=scheme, random_seed=random_seed
    )
    working = working.merge(folds, on="month", how="left", validate="many_to_one")
    working["prediction"] = np.nan
    features = list(feature_columns)
    for evaluation_fold in range(3):
        train = working["fold"].ne(evaluation_fold)
        evaluate = working["fold"].eq(evaluation_fold)
        if not train.any() or not evaluate.any():
            raise ValueError(f"Empty train/evaluation split for fold {evaluation_fold}")
        predictions = []
        for member in range(ensemble_size):
            model = make_pipeline(
                StandardScaler(),
                MLPRegressor(
                    hidden_layer_sizes=(hidden_units,),
                    activation="relu",
                    solver="adam",
                    alpha=l2_penalty,
                    learning_rate_init=learning_rate,
                    max_iter=max_iter,
                    random_state=random_seed + evaluation_fold * 1000 + member,
                ),
            )
            model.fit(working.loc[train, features], working.loc[train, target_column])
            predictions.append(model.predict(working.loc[evaluate, features]))
        working.loc[evaluate, "prediction"] = np.mean(predictions, axis=0)
    result = sample.copy()
    result["prediction"] = np.nan
    result["fold"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    source_index = working["_source_index"].to_numpy()
    result.loc[source_index, "prediction"] = working["prediction"].to_numpy()
    result.loc[source_index, "fold"] = working["fold"].astype("Int64").to_numpy()
    return result


def _prediction_weighted_return(group: pd.DataFrame, decile: int) -> float:
    prediction = group["prediction"].astype(float)
    if decile == 10:
        shifted = prediction - prediction.min()
    elif decile == 1:
        shifted = prediction - prediction.max()
    else:
        raise ValueError("Prediction weights are implemented for extreme deciles")
    denominator = shifted.sum()
    if np.isclose(denominator, 0.0):
        weights = np.repeat(1.0 / len(group), len(group))
    else:
        weights = shifted / denominator
    return float(np.dot(weights, group["target_abnormal_return"]))


def form_prediction_portfolios(
    predictions: pd.DataFrame, *, minimum_funds: int = 10
) -> pd.DataFrame:
    """Form top/bottom deciles with equal and paper Eq. (4)-(6) weights."""

    required = {"month", "prediction", "target_abnormal_return"}
    missing = sorted(required.difference(predictions.columns))
    if missing:
        raise ValueError(f"predictions is missing columns: {missing}")
    rows: list[dict[str, object]] = []
    for month, group in predictions.groupby("month", sort=True):
        valid = group.dropna(subset=["prediction", "target_abnormal_return"]).copy()
        if len(valid) < minimum_funds:
            continue
        order = valid["prediction"].rank(method="first") - 1
        valid["decile"] = np.floor(order * 10 / len(valid)).astype(int) + 1
        valid["decile"] = valid["decile"].clip(1, 10)
        bottom = valid.loc[valid["decile"].eq(1)]
        top = valid.loc[valid["decile"].eq(10)]
        top_equal = top["target_abnormal_return"].mean()
        bottom_equal = bottom["target_abnormal_return"].mean()
        top_prediction = _prediction_weighted_return(top, 10)
        bottom_prediction = _prediction_weighted_return(bottom, 1)
        rows.append(
            {
                "month": month,
                "funds": len(valid),
                "top_equal": top_equal,
                "bottom_equal": bottom_equal,
                "long_short_equal": top_equal - bottom_equal,
                "top_prediction": top_prediction,
                "bottom_prediction": bottom_prediction,
                "long_short_prediction": top_prediction - bottom_prediction,
            }
        )
    return pd.DataFrame.from_records(rows)
