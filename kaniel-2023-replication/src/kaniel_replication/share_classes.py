"""Validate representative-fund rows against TNA-weighted share classes."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .provenance import sha256, write_manifest


PANEL_COLUMNS = ["month", "fund_code", "end_tna", "monthly_return"]


def load_share_class_relations(path: Path) -> pd.DataFrame:
    """Load one-to-many share-class relations, excluding mother-child links."""

    relations = pq.read_table(path).to_pandas()
    share = relations.loc[
        relations["펀드구분"].eq("1") & relations["설정구분"].eq("0"),
        ["대표펀드코드", "서브펀드코드"],
    ].drop_duplicates()
    share = share.rename(
        columns={"대표펀드코드": "representative_code", "서브펀드코드": "class_code"}
    )
    if share["representative_code"].eq(share["class_code"]).any():
        raise ValueError("Share-class relations contain self-links")
    representatives_per_class = share.groupby("class_code")[
        "representative_code"
    ].nunique()
    ambiguous = representatives_per_class[representatives_per_class > 1]
    if not ambiguous.empty:
        raise ValueError(
            f"{len(ambiguous)} share classes map to multiple representatives"
        )
    return share


def _safe_rate(series: pd.Series) -> float:
    return float(series.mean()) if len(series) else float("nan")


def compute_share_class_diagnostics(
    panel: pd.DataFrame,
    relations: pd.DataFrame,
    thresholds: dict[str, float | int],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Compare representative returns with lag-TNA-weighted class returns."""

    missing = sorted(set(PANEL_COLUMNS).difference(panel.columns))
    if missing:
        raise ValueError(f"Class-month panel is missing columns: {missing}")
    panel = panel[PANEL_COLUMNS].copy()
    panel["month"] = pd.to_datetime(panel["month"], errors="raise")
    if panel.duplicated(["month", "fund_code"]).any():
        raise ValueError("Class-month panel has duplicate month/fund_code keys")
    panel = panel.sort_values(["fund_code", "month"])
    panel["lag_tna"] = panel.groupby("fund_code", sort=False)["end_tna"].shift(1)

    linked_counts = relations.groupby("representative_code")["class_code"].nunique()
    class_rows = relations.merge(
        panel.rename(columns={"fund_code": "class_code"}),
        on="class_code",
        how="inner",
        validate="one_to_many",
    )
    class_rows["positive_lag_tna"] = class_rows["lag_tna"].where(
        class_rows["lag_tna"].gt(0)
    )
    eligible = class_rows["positive_lag_tna"].notna() & class_rows[
        "monthly_return"
    ].notna()
    class_rows["eligible_weight"] = class_rows["positive_lag_tna"].where(eligible)
    class_rows["weighted_return_component"] = (
        class_rows["eligible_weight"] * class_rows["monthly_return"]
    )
    class_rows["positive_current_tna"] = class_rows["end_tna"].where(
        class_rows["end_tna"].gt(0)
    )
    class_rows["eligible_class"] = eligible.astype(int)

    grouped = class_rows.groupby(["representative_code", "month"], as_index=False)
    class_month = grouped.agg(
        observed_classes=("class_code", "nunique"),
        eligible_classes=("eligible_class", "sum"),
        observed_lag_tna=("positive_lag_tna", lambda values: values.sum(min_count=1)),
        eligible_lag_tna=("eligible_weight", lambda values: values.sum(min_count=1)),
        weighted_component=(
            "weighted_return_component",
            lambda values: values.sum(min_count=1),
        ),
        class_current_tna_sum=(
            "positive_current_tna",
            lambda values: values.sum(min_count=1),
        ),
    )
    class_month["class_weighted_return"] = class_month["weighted_component"].div(
        class_month["eligible_lag_tna"]
    )
    class_month["return_weight_coverage"] = class_month["eligible_lag_tna"].div(
        class_month["observed_lag_tna"]
    )
    class_month["linked_classes_snapshot"] = class_month[
        "representative_code"
    ].map(linked_counts)

    representative_rows = panel.loc[
        panel["fund_code"].isin(relations["representative_code"])
    ].rename(
        columns={
            "fund_code": "representative_code",
            "end_tna": "representative_tna",
            "monthly_return": "representative_return",
            "lag_tna": "representative_lag_tna",
        }
    )
    comparison = class_month.merge(
        representative_rows,
        on=["representative_code", "month"],
        how="left",
        validate="one_to_one",
    )
    comparison["representative_present"] = comparison["representative_tna"].notna()
    comparison["return_difference_bps"] = (
        comparison["representative_return"]
        - comparison["class_weighted_return"]
    ).abs() * 10_000
    comparison["tna_ratio"] = comparison["representative_tna"].div(
        comparison["class_current_tna_sum"]
    )
    comparison["tna_difference_fraction"] = comparison["tna_ratio"].sub(1).abs()

    minimum_overlap = int(thresholds["minimum_overlap_months"])
    return_tolerance = float(thresholds["return_tolerance_bps"])
    minimum_return_match = float(thresholds["minimum_return_match_rate"])
    tna_tolerance = float(thresholds["tna_tolerance_fraction"])
    minimum_tna_match = float(thresholds["minimum_tna_match_rate"])
    complete_coverage = float(thresholds["complete_representative_coverage_rate"])
    minimum_higher_rate = float(thresholds["minimum_representative_higher_rate"])
    maximum_fee_like_median = float(thresholds["maximum_fee_like_median_bps"])

    diagnostics_rows: list[dict[str, Any]] = []
    for representative_code, group in comparison.groupby(
        "representative_code", sort=False
    ):
        comparable_returns = group["return_difference_bps"].dropna()
        signed_return_differences = (
            group["representative_return"] - group["class_weighted_return"]
        ).dropna() * 10_000
        comparable_tna = group["tna_difference_fraction"].dropna()
        representative_coverage = _safe_rate(group["representative_present"])
        return_match_rate = _safe_rate(comparable_returns.le(return_tolerance))
        tna_match_rate = _safe_rate(comparable_tna.le(tna_tolerance))
        enough_return_evidence = len(comparable_returns) >= minimum_overlap
        enough_tna_evidence = len(comparable_tna) >= minimum_overlap
        representative_higher_rate = _safe_rate(signed_return_differences.gt(0))
        median_signed_difference = signed_return_differences.median()

        if enough_tna_evidence and tna_match_rate >= minimum_tna_match:
            tna_decision = (
                "representative_tna_preferred"
                if representative_coverage >= complete_coverage
                else "representative_tna_then_class_fallback"
            )
        elif not group["representative_present"].any():
            tna_decision = "class_tna_aggregate_only"
        elif not enough_tna_evidence:
            tna_decision = "tna_insufficient_evidence"
        else:
            tna_decision = "tna_manual_review"

        if enough_return_evidence and return_match_rate >= minimum_return_match:
            return_relation = "return_equivalent"
        elif (
            enough_return_evidence
            and representative_higher_rate >= minimum_higher_rate
            and 0 < median_signed_difference <= maximum_fee_like_median
        ):
            return_relation = "representative_higher_fee_like"
        elif not enough_return_evidence:
            return_relation = "return_insufficient_evidence"
        else:
            return_relation = "return_manual_review"

        if tna_decision.startswith("representative_tna"):
            if return_relation == "return_equivalent":
                consolidation_decision = "representative_row_preferred"
            elif return_relation == "representative_higher_fee_like":
                consolidation_decision = "separate_return_basis_required"
            else:
                consolidation_decision = "manual_review"
        elif tna_decision == "class_tna_aggregate_only":
            consolidation_decision = "class_aggregate_only"
        elif "insufficient" in tna_decision or "insufficient" in return_relation:
            consolidation_decision = "insufficient_evidence"
        else:
            consolidation_decision = "manual_review"

        diagnostics_rows.append(
            {
                "representative_code": representative_code,
                "linked_classes_snapshot": int(
                    group["linked_classes_snapshot"].iloc[0]
                ),
                "class_months": len(group),
                "representative_month_coverage": representative_coverage,
                "comparable_return_months": len(comparable_returns),
                "median_return_difference_bps": comparable_returns.median(),
                "p95_return_difference_bps": comparable_returns.quantile(0.95),
                "return_match_rate": return_match_rate,
                "median_signed_return_difference_bps": median_signed_difference,
                "representative_higher_rate": representative_higher_rate,
                "return_relation": return_relation,
                "comparable_tna_months": len(comparable_tna),
                "median_tna_ratio": group["tna_ratio"].median(),
                "p95_tna_difference_fraction": comparable_tna.quantile(0.95),
                "tna_match_rate": tna_match_rate,
                "tna_decision": tna_decision,
                "consolidation_decision": consolidation_decision,
            }
        )

    diagnostics = pd.DataFrame(diagnostics_rows).sort_values(
        ["consolidation_decision", "representative_code"]
    )
    summary = {
        "relation_rows": len(relations),
        "representative_groups_with_class_history": len(diagnostics),
        "comparison_months": len(comparison),
        "tna_decision_counts": dict(Counter(diagnostics["tna_decision"])),
        "return_relation_counts": dict(Counter(diagnostics["return_relation"])),
        "consolidation_decision_counts": dict(
            Counter(diagnostics["consolidation_decision"])
        ),
        "thresholds": thresholds,
        "overall": {
            "median_return_difference_bps": comparison[
                "return_difference_bps"
            ].median(),
            "return_match_rate": _safe_rate(
                comparison["return_difference_bps"].dropna().le(return_tolerance)
            ),
            "median_signed_return_difference_bps": (
                comparison["representative_return"]
                - comparison["class_weighted_return"]
            ).median()
            * 10_000,
            "representative_higher_rate": _safe_rate(
                (
                    comparison["representative_return"]
                    - comparison["class_weighted_return"]
                )
                .dropna()
                .gt(0)
            ),
            "median_tna_ratio": comparison["tna_ratio"].median(),
            "tna_match_rate": _safe_rate(
                comparison["tna_difference_fraction"].dropna().le(tna_tolerance)
            ),
        },
    }
    return comparison, diagnostics, summary


def validate_share_classes(
    panel_path: Path,
    relations_path: Path,
    output_dir: Path,
    thresholds: dict[str, float | int],
) -> dict[str, Any]:
    """Run validation and persist detailed comparisons and decisions."""

    panel = pq.read_table(panel_path, columns=PANEL_COLUMNS).to_pandas()
    relations = load_share_class_relations(relations_path)
    comparison, diagnostics, summary = compute_share_class_diagnostics(
        panel, relations, thresholds
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = output_dir / "share_class_month_comparison.parquet"
    diagnostics_path = output_dir / "share_class_group_diagnostics.csv"
    pq.write_table(
        pa.Table.from_pandas(comparison, preserve_index=False),
        comparison_path,
        compression="zstd",
    )
    diagnostics.to_csv(diagnostics_path, index=False, encoding="utf-8")
    payload = {
        **summary,
        "inputs": {
            "panel": str(panel_path.resolve()),
            "relations": str(relations_path.resolve()),
        },
        "outputs": {
            "comparison": {
                "path": str(comparison_path),
                "sha256": sha256(comparison_path),
            },
            "diagnostics": {
                "path": str(diagnostics_path),
                "sha256": sha256(diagnostics_path),
            },
        },
    }
    write_manifest(output_dir / "share_class_validation_summary.json", payload)
    return payload
