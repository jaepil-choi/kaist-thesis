"""Inventory KAIST pilot files without loading parquet payloads into memory.

Run from the repository root:
    uv run python scripts/kaist_pilot/inventory.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parquet_metadata(path: Path) -> dict[str, Any]:
    parquet_file = pq.ParquetFile(path)
    metadata = parquet_file.metadata
    schema = parquet_file.schema_arrow
    return {
        "rows": metadata.num_rows,
        "row_groups": metadata.num_row_groups,
        "columns": metadata.num_columns,
        "schema": [
            {"name": field.name, "type": str(field.type), "nullable": field.nullable}
            for field in schema
        ],
    }


def inventory(root: Path, include_hashes: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        record: dict[str, Any] = {
            "relative_path": path.relative_to(root).as_posix(),
            "extension": path.suffix.lower(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path) if include_hashes else None,
        }
        if path.suffix.lower() == ".parquet":
            try:
                record.update(parquet_metadata(path))
                record["readable"] = True
                record["error"] = None
            except Exception as exc:  # noqa: BLE001 - inventory must report corrupt files
                record.update(
                    {
                        "rows": None,
                        "row_groups": None,
                        "columns": None,
                        "schema": None,
                        "readable": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        rows.append(record)
    return rows


def write_outputs(rows: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "file_inventory.json"
    csv_path = output_dir / "file_inventory.csv"
    summary_path = output_dir / "inventory_summary.json"

    json_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "relative_path",
                "extension",
                "bytes",
                "sha256",
                "rows",
                "row_groups",
                "columns",
                "readable",
                "error",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    extensions = Counter(row["extension"] or "(none)" for row in rows)
    unreadable = [
        row["relative_path"] for row in rows if row.get("readable") is False
    ]
    hashes = Counter(row["sha256"] for row in rows if row.get("sha256"))
    duplicate_hashes = {
        digest: [
            row["relative_path"] for row in rows if row.get("sha256") == digest
        ]
        for digest, count in hashes.items()
        if count > 1
    }
    summary = {
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "extensions": dict(sorted(extensions.items())),
        "unreadable_parquet": unreadable,
        "exact_duplicate_groups": duplicate_hashes,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path("data/kaist_pilot"), help="data root"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scratch-pad-for-ai/outputs/kaist_pilot_inventory"),
    )
    parser.add_argument(
        "--hashes", action="store_true", help="compute SHA-256 for every file"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"data root does not exist: {root}")
    rows = inventory(root, include_hashes=args.hashes)
    write_outputs(rows, args.output_dir.resolve())
    print(
        json.dumps(
            {
                "root": str(root),
                "files": len(rows),
                "bytes": sum(row["bytes"] for row in rows),
                "unreadable_parquet": sum(
                    row.get("readable") is False for row in rows
                ),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
