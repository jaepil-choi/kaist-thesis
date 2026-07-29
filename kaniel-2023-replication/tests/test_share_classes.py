import pandas as pd

from kaniel_replication.share_classes import compute_share_class_diagnostics


THRESHOLDS = {
    "minimum_overlap_months": 24,
    "return_tolerance_bps": 5.0,
    "minimum_return_match_rate": 0.90,
    "tna_tolerance_fraction": 0.02,
    "minimum_tna_match_rate": 0.80,
    "complete_representative_coverage_rate": 0.95,
    "minimum_representative_higher_rate": 0.90,
    "maximum_fee_like_median_bps": 25.0,
}


def _synthetic_panel(representative_return_offset: float = 0.0) -> pd.DataFrame:
    months = pd.date_range("2020-01-31", periods=30, freq="ME")
    rows = []
    for month in months:
        rows.extend(
            [
                {
                    "month": month,
                    "fund_code": "A",
                    "end_tna": 60.0,
                    "monthly_return": 0.01,
                },
                {
                    "month": month,
                    "fund_code": "B",
                    "end_tna": 40.0,
                    "monthly_return": 0.02,
                },
                {
                    "month": month,
                    "fund_code": "R",
                    "end_tna": 100.0,
                    "monthly_return": 0.014 + representative_return_offset,
                },
            ]
        )
    return pd.DataFrame(rows)


def _relations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "representative_code": ["R", "R"],
            "class_code": ["A", "B"],
        }
    )


def test_incomplete_validated_representative_uses_class_fallback() -> None:
    panel = _synthetic_panel()
    last_months = sorted(panel["month"].unique())[-3:]
    panel = panel.loc[
        ~(
            panel["fund_code"].eq("R")
            & panel["month"].isin(last_months)
        )
    ]
    _, diagnostics, _ = compute_share_class_diagnostics(
        panel, _relations(), THRESHOLDS
    )
    row = diagnostics.iloc[0]
    assert row["tna_decision"] == "representative_tna_then_class_fallback"
    assert row["return_relation"] == "return_equivalent"
    assert row["consolidation_decision"] == "representative_row_preferred"
    assert row["median_return_difference_bps"] < 1e-10
    assert abs(row["median_tna_ratio"] - 1.0) < 1e-12


def test_systematic_small_premium_requires_separate_return_basis() -> None:
    panel = _synthetic_panel(representative_return_offset=0.001)
    _, diagnostics, _ = compute_share_class_diagnostics(
        panel, _relations(), THRESHOLDS
    )
    row = diagnostics.iloc[0]
    assert row["return_relation"] == "representative_higher_fee_like"
    assert row["consolidation_decision"] == "separate_return_basis_required"
    assert row["return_match_rate"] == 0


def test_large_return_mismatch_requires_manual_review() -> None:
    panel = _synthetic_panel(representative_return_offset=0.01)
    _, diagnostics, _ = compute_share_class_diagnostics(
        panel, _relations(), THRESHOLDS
    )
    row = diagnostics.iloc[0]
    assert row["return_relation"] == "return_manual_review"
    assert row["consolidation_decision"] == "manual_review"
