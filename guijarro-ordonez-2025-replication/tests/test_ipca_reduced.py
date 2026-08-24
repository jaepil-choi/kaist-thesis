"""Tests for the reduced-instrument and ridge-Gamma IPCA deviations.

Both features default to the paper's specification.  These tests pin the
defaults, the opt-in warnings, and the algebra of the penalized Gamma step.
"""

import numpy as np
import pandas as pd
import pytest

from guijarro_ordonez_replication.characteristics import CHARACTERISTIC_COLUMNS
from guijarro_ordonez_replication.ipca import (
    PAPER_GAMMA_RIDGE,
    ReducedCharacteristicIPCAWarning,
    RidgeIPCAWarning,
    ShortHistoryIPCAWarning,
    _gamma_step,
    estimate_daily_ipca_residuals,
    fit_ipca_als,
    ipca_run_tag,
    prepare_ipca_monthly_panel,
    select_characteristics_by_coverage,
    validate_characteristic_columns,
    validate_gamma_ridge,
)


def _coverage(**overrides: float) -> dict[str, float]:
    coverage = dict.fromkeys(CHARACTERISTIC_COLUMNS, 0.5)
    coverage.update(overrides)
    return coverage


def test_coverage_selection_keeps_canonical_order() -> None:
    coverage = _coverage(Variance=0.99, r2_1=1.0, BEME=0.95)

    selected = select_characteristics_by_coverage(coverage, threshold=0.90)

    assert selected == ("r2_1", "BEME", "Variance")
    order = [CHARACTERISTIC_COLUMNS.index(name) for name in selected]
    assert order == sorted(order)


def test_zero_threshold_reproduces_the_paper_instrument_set() -> None:
    assert select_characteristics_by_coverage(
        _coverage(), threshold=0.0
    ) == tuple(CHARACTERISTIC_COLUMNS)


def test_coverage_selection_rejects_empty_and_incomplete_input() -> None:
    with pytest.raises(ValueError, match="no characteristic reaches"):
        select_characteristics_by_coverage(_coverage(), threshold=0.99)
    with pytest.raises(ValueError, match="missing characteristics"):
        select_characteristics_by_coverage({"r2_1": 1.0}, threshold=0.5)
    with pytest.raises(ValueError, match="threshold must be"):
        select_characteristics_by_coverage(_coverage(), threshold=1.5)


def test_full_instrument_set_is_silent_and_subset_warns() -> None:
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert validate_characteristic_columns(None) == tuple(
            CHARACTERISTIC_COLUMNS
        )

    with pytest.warns(ReducedCharacteristicIPCAWarning, match="8 of 46"):
        validate_characteristic_columns(CHARACTERISTIC_COLUMNS[:8])

    with pytest.raises(ValueError, match="unknown characteristics"):
        validate_characteristic_columns(["not_a_characteristic"])
    with pytest.raises(ValueError, match="duplicates"):
        validate_characteristic_columns(["r2_1", "r2_1"])
    with pytest.raises(ValueError, match="must not be empty"):
        validate_characteristic_columns([])


def test_paper_ridge_is_zero_and_any_penalty_warns() -> None:
    import warnings

    assert PAPER_GAMMA_RIDGE == 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert validate_gamma_ridge(0.0) == 0.0

    with pytest.warns(RidgeIPCAWarning, match="0.01"):
        assert validate_gamma_ridge(0.01) == 0.01

    with pytest.raises(ValueError, match="non-negative"):
        validate_gamma_ridge(-1.0)
    with pytest.raises(ValueError, match="non-negative"):
        validate_gamma_ridge(float("nan"))


def test_gamma_step_ridge_matches_explicit_penalized_normal_equations() -> None:
    returns = (np.array([0.01, -0.02, 0.03]),)
    characteristics = (np.array([[0.5, -0.5], [0.0, 0.5], [-0.5, 0.0]]),)
    factors = (np.array([0.2, -0.1]),)
    ridge = 0.05

    design = np.kron(characteristics[0], factors[0].reshape(1, -1))
    left = design.T @ design
    scale = np.trace(left) / left.shape[0]
    expected = (
        np.linalg.solve(
            left + ridge * scale * np.eye(left.shape[0]), design.T @ returns[0]
        )
    ).reshape(2, 2)

    actual = _gamma_step(
        returns,
        characteristics,
        factors,
        n_characteristics=2,
        n_factors=2,
        ridge=ridge,
    )

    np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_gamma_step_ridge_defaults_to_the_unpenalized_solution() -> None:
    returns = (np.array([0.01, -0.02, 0.03]),)
    characteristics = (np.array([[0.5, -0.5], [0.0, 0.5], [-0.5, 0.0]]),)
    factors = (np.array([0.2, -0.1]),)

    baseline = _gamma_step(
        returns, characteristics, factors, n_characteristics=2, n_factors=2
    )
    explicit_zero = _gamma_step(
        returns,
        characteristics,
        factors,
        n_characteristics=2,
        n_factors=2,
        ridge=0.0,
    )

    np.testing.assert_array_equal(baseline, explicit_zero)


def test_ridge_shrinks_gamma_monotonically() -> None:
    rng = np.random.default_rng(11)
    returns = tuple(rng.normal(scale=0.05, size=30) for _ in range(24))
    characteristics = tuple(rng.normal(size=(30, 4)) for _ in range(24))

    norms = []
    for ridge in (0.0, 0.1, 1.0, 10.0):
        fit = fit_ipca_als(
            returns,
            characteristics,
            n_factors=2,
            max_iterations=200,
            tolerance=1e-10,
            gamma_ridge=ridge,
        )
        norms.append(float(np.linalg.norm(fit.gamma)))
        assert fit.gamma_ridge == ridge

    assert norms == sorted(norms, reverse=True)


def test_ridge_regularizes_an_exactly_duplicated_instrument() -> None:
    """A duplicated column makes Z'Z singular; ridge restores a unique solve."""

    rng = np.random.default_rng(3)
    returns = []
    characteristics = []
    for _ in range(18):
        base = rng.normal(size=(25, 2))
        # Third column duplicates the first, exactly as r2_1 duplicates ST_Rev.
        z = np.column_stack([base, base[:, 0]])
        characteristics.append(z)
        returns.append(z @ np.array([0.5, -0.2, 0.5]) * 0.01)

    penalized = fit_ipca_als(
        tuple(returns),
        tuple(characteristics),
        n_factors=1,
        max_iterations=300,
        tolerance=1e-10,
        gamma_ridge=0.01,
    )

    assert np.isfinite(penalized.gamma).all()
    # The duplicated pair must receive an identical, split loading.
    assert penalized.gamma[0, 0] == pytest.approx(penalized.gamma[2, 0], rel=1e-6)


def test_run_tag_only_marks_deviations() -> None:
    assert ipca_run_tag(factors=5, initial_months=420, window_months=240) == (
        "k5_i420_w240"
    )
    assert (
        ipca_run_tag(
            factors=5,
            initial_months=420,
            window_months=240,
            n_characteristics=len(CHARACTERISTIC_COLUMNS),
        )
        == "k5_i420_w240"
    )
    assert (
        ipca_run_tag(
            factors=5,
            initial_months=60,
            window_months=60,
            n_characteristics=8,
            gamma_ridge=0.01,
        )
        == "k5_i60_w60_c8_r0p01"
    )


def test_panel_preparation_applies_the_small_cap_exclusion() -> None:
    panel = pd.DataFrame(
        {
            "date": ["2020-01-15", "2020-01-31", "2020-01-20"],
            "ticker": ["a", "b", "c"],
            "market_cap": [9_000.0, 1_000.0, 0.05],
            "return": [0.01, 0.02, 0.03],
        }
    )

    prepared, dates = prepare_ipca_monthly_panel(panel, cap_proportion=0.01)

    assert sorted(prepared["ticker"]) == ["A", "B"]
    assert list(dates) == [pd.Timestamp("2020-01-31")]
    with pytest.raises(ValueError, match="cap_proportion"):
        prepare_ipca_monthly_panel(panel, cap_proportion=-1.0)


def _synthetic_panels(
    columns: tuple[str, ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(19)
    tickers = [f"A{i}" for i in range(8)]
    months = pd.date_range("2020-01-31", periods=5, freq="ME")
    monthly_rows = []
    daily_rows = []
    for month_index, month in enumerate(months):
        for ticker_index, ticker in enumerate(tickers):
            chars = dict.fromkeys(CHARACTERISTIC_COLUMNS, np.nan)
            chars.update(
                dict(zip(columns, rng.normal(size=len(columns)), strict=True))
            )
            monthly_rows.append(
                {
                    "date": month,
                    "ticker": ticker,
                    "return": 0.01 * (ticker_index - 3),
                    "market_cap": 100.0 + ticker_index,
                    **chars,
                }
            )
        if month_index > 0:
            span = pd.bdate_range(
                months[month_index - 1] + pd.Timedelta(days=1), month
            )
            for day in span:
                for ticker_index, ticker in enumerate(tickers):
                    daily_rows.append(
                        {
                            "date": day,
                            "ticker": ticker,
                            "return": 0.001 * (ticker_index - 3),
                        }
                    )
    return pd.DataFrame(monthly_rows), pd.DataFrame(daily_rows)


def test_reduced_ridge_run_is_labeled_and_ignores_uncovered_columns() -> None:
    columns = CHARACTERISTIC_COLUMNS[:5]
    monthly, daily = _synthetic_panels(columns)

    with pytest.warns(
        (
            ShortHistoryIPCAWarning,
            ReducedCharacteristicIPCAWarning,
            RidgeIPCAWarning,
        )
    ):
        result = estimate_daily_ipca_residuals(
            monthly,
            daily,
            n_factors=1,
            window_months=2,
            reestimate_every_months=1,
            allow_short_history=True,
            max_iterations=20,
            characteristic_columns=columns,
            gamma_ridge=0.01,
            require_convergence=False,
        )

    audit = result.audit
    assert audit["characteristic_count"] == 5
    assert audit["paper_characteristic_count"] == len(CHARACTERISTIC_COLUMNS)
    assert audit["characteristic_columns"] == list(columns)
    assert audit["gamma_ridge"] == 0.01
    assert audit["deviations"] == [
        "short-history",
        "reduced-characteristics",
        "ridge-gamma",
    ]
    assert audit["classification"] == (
        "Korean IPCA sensitivity "
        "(short-history, reduced-characteristics, ridge-gamma)"
    )
    # The 41 all-NaN columns must not drop a single stock from the universe.
    assert not result.residuals.empty
    assert result.loadings["ticker"].nunique() == 8
