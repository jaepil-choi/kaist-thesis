"""Streaming construction of a class-level monthly fund panel."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .provenance import sha256, write_manifest


SOURCE_COLUMNS = [
    "기준일자",
    "협회펀드코드",
    "순자산",
    "실현수익률",
    "BM수익률",
    "대유형코드",
    "유형코드",
]


@dataclass
class PanelDiagnostics:
    """Counters collected while streaming the daily source."""

    source_rows: int = 0
    selected_rows: int = 0
    placeholder_rows: int = 0
    invalid_return_factors: int = 0
    implausible_return_factors: int = 0
    emitted_rows: int = 0
    emitted_months: int = 0


def _partial_month(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby("fund_code", sort=False, observed=True)
    partial = pd.DataFrame(
        {
            "return_factor": grouped["return_factor"].prod(min_count=1),
            "bm_return_factor": grouped["bm_return_factor"].prod(min_count=1),
            "end_tna": grouped["tna"].last(),
            "observations": grouped["return_factor"].count(),
            "return_outliers": grouped["return_outlier"].sum(),
            "first_date": grouped["date"].min(),
            "last_date": grouped["date"].max(),
            "type_code": grouped["type_code"].last(),
        }
    )
    return partial


def _combine_partial(left: pd.DataFrame | None, right: pd.DataFrame) -> pd.DataFrame:
    if left is None:
        return right
    combined = pd.concat([left, right])
    grouped = combined.groupby(level=0, sort=False)
    return pd.DataFrame(
        {
            "return_factor": grouped["return_factor"].prod(min_count=1),
            "bm_return_factor": grouped["bm_return_factor"].prod(min_count=1),
            "end_tna": grouped["end_tna"].last(),
            "observations": grouped["observations"].sum(),
            "return_outliers": grouped["return_outliers"].sum(),
            "first_date": grouped["first_date"].min(),
            "last_date": grouped["last_date"].max(),
            "type_code": grouped["type_code"].last(),
        }
    )


def _finalize_month(
    period: pd.Period,
    state: pd.DataFrame,
    previous_tna: dict[str, float],
) -> pd.DataFrame:
    output = state.reset_index()
    output.insert(0, "month", period.to_timestamp("M").normalize())
    output["monthly_return"] = output["return_factor"] - 1.0
    output["monthly_bm_return"] = output["bm_return_factor"] - 1.0
    output["previous_tna"] = output["fund_code"].map(previous_tna)
    denominator = output["previous_tna"] * output["return_factor"]
    output["flow"] = output["end_tna"].div(denominator).sub(1.0)
    output.loc[(denominator <= 0) | denominator.isna(), "flow"] = pd.NA
    contaminated = output["return_outliers"].gt(0)
    output.loc[contaminated, ["monthly_return", "flow"]] = pd.NA

    for fund_code, tna in zip(output["fund_code"], output["end_tna"], strict=True):
        if pd.notna(tna) and tna > 0:
            previous_tna[str(fund_code)] = float(tna)

    return output[
        [
            "month",
            "fund_code",
            "type_code",
            "monthly_return",
            "monthly_bm_return",
            "end_tna",
            "flow",
            "observations",
            "return_outliers",
            "first_date",
            "last_date",
        ]
    ]


def build_class_month_panel(
    source: Path,
    output: Path,
    active_type_codes: set[str],
    large_type_code: str = "20",
    start: str | None = None,
    end: str | None = None,
    batch_size: int = 250_000,
    plausible_factor_min: float = 0.5,
    plausible_factor_max: float = 1.5,
) -> dict[str, Any]:
    """Stream a sorted daily Parquet into a class-level monthly panel.

    The function intentionally does not aggregate share classes. The current class
    relation is a snapshot and requires a separate no-double-counting gate.
    """

    source = source.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    parquet = pq.ParquetFile(source)
    missing = sorted(set(SOURCE_COLUMNS).difference(parquet.schema_arrow.names))
    if missing:
        raise ValueError(f"Missing source columns: {missing}")

    start_ts = pd.Timestamp(start) if start else None
    end_ts = pd.Timestamp(end) if end else None
    date_column_index = parquet.schema_arrow.names.index("기준일자")
    selected_row_groups: list[int] = []
    for row_group_index in range(parquet.metadata.num_row_groups):
        statistics = parquet.metadata.row_group(row_group_index).column(
            date_column_index
        ).statistics
        if statistics is None or not statistics.has_min_max:
            selected_row_groups.append(row_group_index)
            continue
        row_group_min = pd.Timestamp(statistics.min)
        row_group_max = pd.Timestamp(statistics.max)
        if start_ts is not None and row_group_max < start_ts:
            continue
        if end_ts is not None and row_group_min > end_ts:
            continue
        selected_row_groups.append(row_group_index)
    if not selected_row_groups:
        raise ValueError("No Parquet row groups overlap the requested date range")
    diagnostics = PanelDiagnostics()
    current_period: pd.Period | None = None
    current_state: pd.DataFrame | None = None
    previous_tna: dict[str, float] = {}
    writer: pq.ParquetWriter | None = None
    quarantined_frames: list[pd.DataFrame] = []
    last_seen_date: pd.Timestamp | None = None

    def emit(period: pd.Period, state: pd.DataFrame) -> None:
        nonlocal writer
        frame = _finalize_month(period, state, previous_tna)
        table = pa.Table.from_pandas(frame, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(output, table.schema, compression="zstd")
        writer.write_table(table)
        diagnostics.emitted_rows += len(frame)
        diagnostics.emitted_months += 1

    try:
        for batch in parquet.iter_batches(
            columns=SOURCE_COLUMNS,
            batch_size=batch_size,
            row_groups=selected_row_groups,
        ):
            frame = batch.to_pandas()
            diagnostics.source_rows += len(frame)
            frame = frame.rename(
                columns={
                    "기준일자": "date",
                    "협회펀드코드": "fund_code",
                    "순자산": "tna",
                    "실현수익률": "return_factor",
                    "BM수익률": "bm_return_factor",
                    "대유형코드": "large_type_code",
                    "유형코드": "type_code",
                }
            )
            frame["date"] = pd.to_datetime(frame["date"], errors="raise")
            if not frame.empty:
                batch_min = frame["date"].min()
                if last_seen_date is not None and batch_min < last_seen_date:
                    raise ValueError("Daily source is not sorted by date")
                last_seen_date = frame["date"].max()

            if start_ts is not None:
                frame = frame.loc[frame["date"] >= start_ts]
            if end_ts is not None:
                frame = frame.loc[frame["date"] <= end_ts]
            frame = frame.loc[
                frame["large_type_code"].eq(large_type_code)
                & frame["type_code"].isin(active_type_codes)
            ].copy()
            if frame.empty:
                continue

            diagnostics.selected_rows += len(frame)
            for column in ("tna", "return_factor", "bm_return_factor"):
                frame[column] = pd.to_numeric(frame[column], errors="coerce")

            placeholder = frame["tna"].eq(0) & frame["return_factor"].eq(1)
            diagnostics.placeholder_rows += int(placeholder.sum())
            frame = frame.loc[~placeholder].copy()

            invalid = frame["return_factor"].le(0) | frame["return_factor"].isna()
            diagnostics.invalid_return_factors += int(invalid.sum())
            frame.loc[invalid, "return_factor"] = pd.NA
            implausible = (
                frame["return_factor"].lt(plausible_factor_min)
                | frame["return_factor"].gt(plausible_factor_max)
            )
            diagnostics.implausible_return_factors += int(implausible.sum())
            if implausible.any():
                quarantined_frames.append(
                    frame.loc[
                        implausible,
                        ["date", "fund_code", "type_code", "tna", "return_factor"],
                    ].copy()
                )
            frame["return_outlier"] = implausible
            frame.loc[implausible, "return_factor"] = pd.NA
            frame["period"] = frame["date"].dt.to_period("M")

            for period in sorted(frame["period"].unique()):
                monthly = frame.loc[frame["period"].eq(period)]
                if current_period is not None and period < current_period:
                    raise ValueError("Daily source moved backward across months")
                if current_period is not None and period != current_period:
                    if current_state is None:
                        raise RuntimeError("Missing state for completed month")
                    emit(current_period, current_state)
                    current_state = None
                current_period = period
                current_state = _combine_partial(current_state, _partial_month(monthly))

        if current_period is not None and current_state is not None:
            emit(current_period, current_state)
    finally:
        if writer is not None:
            writer.close()

    if not output.exists():
        raise ValueError("No rows matched the requested universe and date range")

    quarantine_path = output.with_suffix(".return_outliers.parquet")
    quarantine_sha256 = None
    if quarantined_frames:
        quarantine = pd.concat(quarantined_frames, ignore_index=True)
        pq.write_table(
            pa.Table.from_pandas(quarantine, preserve_index=False),
            quarantine_path,
            compression="zstd",
        )
        quarantine_sha256 = sha256(quarantine_path)

    manifest_path = output.with_suffix(".manifest.json")
    payload = {
        "source": str(source),
        "output": str(output),
        "output_sha256": sha256(output),
        "return_outlier_quarantine": {
            "path": str(quarantine_path) if quarantine_sha256 else None,
            "sha256": quarantine_sha256,
        },
        "date_filter": {"start": start, "end": end},
        "source_physical_rows": parquet.metadata.num_rows,
        "selected_row_groups": selected_row_groups,
        "universe": {
            "large_type_code": large_type_code,
            "active_type_codes": sorted(active_type_codes),
            "share_class_aggregation": "not_performed",
        },
        "diagnostics": diagnostics.__dict__,
    }
    write_manifest(manifest_path, payload)
    return payload
