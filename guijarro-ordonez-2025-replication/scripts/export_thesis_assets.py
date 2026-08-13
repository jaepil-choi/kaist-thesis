"""Export report-ready thesis assets from ignored model outputs.

Run from the repository root with::

    uv run --no-sync python \
        guijarro-ordonez-2025-replication/scripts/export_thesis_assets.py

The output registry remains the source of truth.  This script snapshots only the
numbered paper figures and tables into a Git-tracked directory and records their
hashes so the Markdown draft never depends on an untracked ``outputs/`` tree.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[1]
REGISTRY = PROJECT / "config" / "output-registry.yml"
DESTINATION = PROJECT / "paper-assets"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    outputs = registry["paper_outputs"]
    run_manifests = [
        *list((PROJECT / "outputs" / "orchestration").glob("run-*/manifest.json")),
        *list((PROJECT / "outputs" / "orchestration").glob("gpu-grid-*/manifest.json")),
    ]
    if not run_manifests:
        raise FileNotFoundError("no orchestration run manifest is available")
    run_manifest = max(run_manifests, key=lambda path: path.stat().st_mtime_ns)
    run_id = run_manifest.parent.name
    exported: list[dict[str, object]] = []

    for item in outputs:
        source_fields = ["path"]
        if "companion_path" in item:
            source_fields.append("companion_path")

        for source_field in source_fields:
            source = PROJECT / item[source_field]
            if not source.is_file():
                raise FileNotFoundError(
                    f"registry artifact is missing: {source.relative_to(PROJECT)}"
                )

            subdirectory = "figures" if item["kind"] == "figure" else "tables"
            destination = DESTINATION / subdirectory / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            exported.append(
                {
                    "id": item["id"],
                    "kind": item["kind"],
                    "status": item["status"],
                    "source_field": source_field,
                    "source_path": source.relative_to(PROJECT).as_posix(),
                    "exported_path": destination.relative_to(PROJECT).as_posix(),
                    "sha256": sha256(destination),
                    "bytes": destination.stat().st_size,
                }
            )

    manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_run_id": run_id,
        "source_run_manifest": run_manifest.relative_to(PROJECT).as_posix(),
        "source_run_manifest_sha256": sha256(run_manifest),
        "classification": (
            "Korean price-return replication variants and specification-derived "
            "assets; not exact U.S. replication"
        ),
        "registry": REGISTRY.relative_to(PROJECT).as_posix(),
        "artifact_count": len(exported),
        "artifacts": exported,
    }
    DESTINATION.mkdir(parents=True, exist_ok=True)
    (DESTINATION / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"artifact_count": len(exported), "run_id": run_id}, indent=2))


if __name__ == "__main__":
    main()
