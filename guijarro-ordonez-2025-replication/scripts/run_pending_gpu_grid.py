"""Run the audit-validated Korean GPU experiment grid sequentially and resumably."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parent
sys.path.insert(0, str(PROJECT / "src"))

from guijarro_ordonez_replication.experiment_matrix import (  # noqa: E402
    experiment_coverage,
    load_experiments,
    sha256_file,
    validate_experiment,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _run_text(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _preflight() -> dict[str, Any]:
    import numpy
    import pandas
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("GPU preflight failed: torch.cuda.is_available() is false")
    device = torch.device("cuda")
    value = (torch.ones(8, device=device) * 3).sum().item()
    if value != 24:
        raise RuntimeError(f"GPU tensor smoke test returned {value}, expected 24")
    required = [PROJECT / "outputs" / "kimchi-exact" / "daily_factor_returns.csv"]
    for k in (1, 3, 5, 8, 10, 15):
        required.extend(
            [
                PROJECT / "outputs" / "pca" / f"daily_residuals_k{k}_20200102_c252_l60.parquet",
                PROJECT / "outputs" / "pca" / f"daily_low_rank_loadings_k{k}_20200102_c252_l60.parquet",
            ]
        )
    for k in (1, 3, 5):
        required.extend(
            [
                PROJECT / "outputs" / "fama-french" / f"daily_residuals_ff{k}_20200102_l60.parquet",
                PROJECT / "outputs" / "fama-french" / f"daily_factor_legs_ff{k}_20200102_l60.parquet",
            ]
        )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing required inputs: {missing}")
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "hip": getattr(torch.version, "hip", None),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "device_name": torch.cuda.get_device_name(0),
        "device_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
        "tensor_smoke_test": "passed",
        "required_inputs": len(required),
    }


def _source_hashes() -> dict[str, str]:
    paths = [
        PROJECT / "run.py",
        PROJECT / "config" / "experiment-matrix.yml",
        PROJECT / "scripts" / "run_pending_gpu_grid.py",
        PROJECT / "src" / "guijarro_ordonez_replication" / "experiment_matrix.py",
        PROJECT / "src" / "guijarro_ordonez_replication" / "trading.py",
        PROJECT / "src" / "guijarro_ordonez_replication" / "policies.py",
    ]
    return {str(path.relative_to(REPOSITORY)): sha256_file(path) for path in paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", action="append", help="run only a named matrix family")
    parser.add_argument("--max-jobs", type=int, help="stop after this many newly executed jobs")
    parser.add_argument("--dry-run", action="store_true", help="write a manifest without training")
    parser.add_argument("--poll-seconds", type=float, default=20.0)
    parser.add_argument("--run-id")
    args = parser.parse_args()

    run_id = args.run_id or datetime.now(UTC).strftime("gpu-grid-%Y%m%dT%H%M%SZ")
    orchestration = PROJECT / "outputs" / "orchestration"
    run_directory = orchestration / run_id
    logs = run_directory / "logs"
    logs.mkdir(parents=True, exist_ok=False)
    lock_path = orchestration / "pending-gpu-grid.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd: int | None = None
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(lock_fd, f"pid={os.getpid()} run_id={run_id}\n".encode())
        environment = _preflight()
        experiments, _ = load_experiments(PROJECT)
        selected = [item for item in experiments if not args.family or item.family in args.family]
        unknown = sorted(set(args.family or []) - {item.family for item in experiments})
        if unknown:
            raise ValueError(f"unknown families: {unknown}")
        initial = experiment_coverage(PROJECT)
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "run_id": run_id,
            "started_at": _now(),
            "finished_at": None,
            "status": "running",
            "invocation": sys.argv,
            "git": {
                "commit": _run_text(["git", "rev-parse", "HEAD"]),
                "branch": _run_text(["git", "branch", "--show-current"]),
                "status_before": _run_text(["git", "status", "--short"]),
            },
            "environment": environment,
            "source_hashes": _source_hashes(),
            "matrix_summary_before": initial["summary"],
            "selected_families": args.family,
            "tasks": [],
        }
        manifest_path = run_directory / "manifest.json"
        _write_json(manifest_path, manifest)
        print(json.dumps({"event": "start", "run_id": run_id, "selected": len(selected), "coverage": initial["summary"]}), flush=True)

        executed = 0
        for ordinal, experiment in enumerate(selected, start=1):
            before = validate_experiment(PROJECT, experiment)
            if before["status"] == "complete":
                record = {"ordinal": ordinal, "id": experiment.id, "status": "skipped_complete", "validated": before, "finished_at": _now()}
                manifest["tasks"].append(record)
                _write_json(manifest_path, manifest)
                print(json.dumps({"event": "skip", "ordinal": ordinal, "total": len(selected), "id": experiment.id}), flush=True)
                continue
            if args.max_jobs is not None and executed >= args.max_jobs:
                break
            if args.dry_run:
                manifest["tasks"].append({"ordinal": ordinal, "id": experiment.id, "status": "dry_run_unrun", "validation": before})
                continue

            executed += 1
            log_path = logs / f"{ordinal:03d}-{experiment.output_tag}.log"
            command = experiment.command(PROJECT)
            record = {
                "ordinal": ordinal,
                "id": experiment.id,
                "status": "running",
                "started_at": _now(),
                "command": command,
                "log": str(log_path),
                "validation_before": before,
            }
            manifest["tasks"].append(record)
            _write_json(manifest_path, manifest)
            print(json.dumps({"event": "job_start", "ordinal": ordinal, "total": len(selected), "id": experiment.id, "log": str(log_path)}), flush=True)
            env = os.environ.copy()
            env["DLSA_DEVICE"] = "cuda"
            env.setdefault("MIOPEN_USER_DB_PATH", str(PROJECT / "outputs" / "miopen-cache"))
            env.setdefault("MIOPEN_CUSTOM_CACHE_DIR", str(PROJECT / "outputs" / "miopen-cache"))
            started = time.monotonic()
            with log_path.open("w", encoding="utf-8") as log:
                process = subprocess.Popen(
                    command,
                    cwd=REPOSITORY,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                while process.poll() is None:
                    time.sleep(args.poll_seconds)
                    print(json.dumps({"event": "heartbeat", "ordinal": ordinal, "id": experiment.id, "elapsed_seconds": round(time.monotonic() - started, 1)}), flush=True)
            record["returncode"] = process.returncode
            record["elapsed_seconds"] = round(time.monotonic() - started, 3)
            record["finished_at"] = _now()
            record["log_sha256"] = sha256_file(log_path)
            if process.returncode != 0:
                record["status"] = "failed"
                manifest["status"] = "failed"
                manifest["finished_at"] = _now()
                _write_json(manifest_path, manifest)
                raise SystemExit(f"{experiment.id} failed with exit code {process.returncode}; see {log_path}")
            after = validate_experiment(PROJECT, experiment)
            record["validation_after"] = after
            if after["status"] != "complete":
                record["status"] = "failed_validation"
                manifest["status"] = "failed"
                manifest["finished_at"] = _now()
                _write_json(manifest_path, manifest)
                raise SystemExit(f"{experiment.id} finished but failed artifact validation: {after}")
            record["status"] = "completed"
            _write_json(manifest_path, manifest)
            print(json.dumps({"event": "job_complete", "ordinal": ordinal, "total": len(selected), "id": experiment.id, "elapsed_seconds": record["elapsed_seconds"]}), flush=True)

        final = experiment_coverage(PROJECT)
        matrix_snapshot = run_directory / "experiment_matrix.json"
        _write_json(matrix_snapshot, final)
        manifest["source_hashes_after"] = _source_hashes()
        manifest["source_changed_during_run"] = (
            manifest["source_hashes_after"] != manifest["source_hashes"]
        )
        manifest["matrix_summary_after"] = final["summary"]
        manifest["matrix_snapshot"] = {"path": str(matrix_snapshot), "sha256": sha256_file(matrix_snapshot)}
        manifest["status"] = "dry_run" if args.dry_run else "complete"
        manifest["finished_at"] = _now()
        _write_json(manifest_path, manifest)
        print(json.dumps({"event": "finish", "run_id": run_id, "executed": executed, "coverage": final["summary"]}), flush=True)
    except BaseException:
        raise
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if lock_path.exists():
            lock_path.unlink()


if __name__ == "__main__":
    main()
