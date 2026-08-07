"""Read-only input audits."""

from __future__ import annotations

from typing import Any

import pyarrow.dataset as ds
import pyarrow.parquet as pq

from .config import ReplicationConfig
from .provenance import write_manifest


DATASETS = {
    "fund_daily": {
        "date": "기준일자",
        "required": {
            "기준일자",
            "협회펀드코드",
            "순자산",
            "실현수익률",
            "BM수익률",
            "대유형코드",
            "유형코드",
        },
    },
    "manager_daily": {
        "date": "기준일자",
        "required": {
            "기준일자",
            "운용사코드",
            "제로인유형코드",
            "펀드수",
            "순자산",
            "실현수익률",
        },
    },
    "fund_master": {
        "date": None,
        "required": {
            "협회펀드코드",
            "운용사코드",
            "대유형코드",
            "유형코드",
            "설정일",
            "해지일",
        },
    },
    "fund_attributes": {
        "date": None,
        "required": {"협회펀드코드", "속성코드"},
    },
    "class_relations": {
        "date": None,
        "required": {"펀드구분", "대표펀드코드", "서브펀드코드", "설정구분"},
    },
}


def _metadata_date_range(parquet: pq.ParquetFile, date_column: str) -> tuple[Any, Any]:
    column_index = parquet.schema_arrow.names.index(date_column)
    minima: list[Any] = []
    maxima: list[Any] = []
    for index in range(parquet.metadata.num_row_groups):
        stats = parquet.metadata.row_group(index).column(column_index).statistics
        if stats is not None and stats.has_min_max:
            minima.append(stats.min)
            maxima.append(stats.max)
    return (min(minima), max(maxima)) if minima else (None, None)


def audit_inputs(config: ReplicationConfig) -> dict[str, Any]:
    """Audit physical schemas without modifying the source datasets."""

    result: dict[str, Any] = {
        "datasets": {},
        "stock_factor_inputs": {},
        "external_inputs": {},
        "methodology_gates": {},
    }
    for name, contract in DATASETS.items():
        path = config.path("data", name)
        if not path.exists():
            raise FileNotFoundError(path)
        parquet = pq.ParquetFile(path)
        columns = parquet.schema_arrow.names
        missing = sorted(contract["required"].difference(columns))
        if missing:
            raise ValueError(f"{name} is missing columns: {missing}")
        date_min, date_max = (None, None)
        if contract["date"]:
            date_min, date_max = _metadata_date_range(parquet, contract["date"])
        result["datasets"][name] = {
            "path": str(path),
            "rows": parquet.metadata.num_rows,
            "row_groups": parquet.metadata.num_row_groups,
            "columns": columns,
            "date_min": date_min,
            "date_max": date_max,
        }

    for name in (
        "factor_monthly",
        "risk_free_monthly",
        "sentiment_monthly",
        "activity_monthly",
    ):
        path = config.path("data", name)
        result["external_inputs"][name] = {
            "path": str(path),
            "exists": path.exists(),
        }

    price_path = config.path("data", "stock_prices")
    price_parquet = pq.ParquetFile(price_path)
    result["stock_factor_inputs"]["stock_prices"] = {
        "path": str(price_path),
        "rows": price_parquet.metadata.num_rows,
        "columns": price_parquet.schema_arrow.names,
    }
    statement_path = config.path("data", "statement_facts")
    statement_dataset = ds.dataset(
        statement_path, format="parquet", partitioning="hive"
    )
    result["stock_factor_inputs"]["statement_facts"] = {
        "path": str(statement_path),
        "rows": statement_dataset.count_rows(),
        "columns": statement_dataset.schema.names,
    }
    construction = config.raw["factor_construction"]
    result["methodology_gates"] = {
        "historical_announcement_timestamps": False,
        "reporting_lag_months": construction["reporting_lag_months"],
        "allow_non_pit_book_equity": construction["allow_non_pit_book_equity"],
        "market_cap_basis_verified": construction["market_cap_basis_verified"],
        "price_total_return_verified": construction["price_total_return_verified"],
    }

    manifest = config.output_root / "manifests" / "input_audit.json"
    write_manifest(manifest, result)
    return result
