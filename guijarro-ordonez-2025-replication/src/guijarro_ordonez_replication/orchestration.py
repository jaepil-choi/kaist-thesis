"""Run the remaining DLSA replication pipeline with durable audit logs."""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from typing import Any

import psutil


PROJECT = Path(__file__).resolve().parents[2]
REPOSITORY = PROJECT.parent
OUTPUTS = PROJECT / "outputs"
ORCHESTRATION_ROOT = OUTPUTS / "orchestration"
RUNNER = PROJECT / "run.py"
EXPECTED_IPCA_FAILURE = "IPCA ALS did not converge"


@dataclass(frozen=True)
class Task:
    """One sequential replication command and its completion contract."""

    name: str
    arguments: tuple[str, ...]
    expected_artifact: str | None = None
    active_markers: tuple[str, ...] = ()
    acceptable_failure_text: str | None = None


def default_tasks() -> tuple[Task, ...]:
    """Return the ordered, resumable remainder of the replication pipeline."""

    return (
        Task(
            name="five_day_holding",
            arguments=(
                "simulate-pca",
                "--simulation-model",
                "cnn_transformer",
                "--simulation-holding-days",
                "5",
            ),
            expected_artifact=(
                "outputs/strategies/"
                "pca5_cnn_transformer_sharpe_lb30_e100_rolling_no-cost_h5/"
                "simulation_audit.json"
            ),
            active_markers=("simulate-pca", "--simulation-holding-days", "5"),
        ),
        Task(
            name="alternative_networks",
            arguments=(
                "run-alternative-networks",
                "--alternative-max-models",
                "5",
                "--simulation-epochs",
                "100",
            ),
            expected_artifact=(
                "outputs/paper-korean/alternative-networks/"
                "alternative_network_audit.json"
            ),
        ),
        Task(
            name="ipca_k1_short_history",
            arguments=(
                "estimate-ipca",
                "--ipca-factors",
                "1",
                "--ipca-initial-months",
                "60",
                "--ipca-window-months",
                "60",
                "--allow-short-history-ipca",
            ),
            expected_artifact="outputs/ipca/ipca_audit_k1_i60_w60.json",
            acceptable_failure_text=EXPECTED_IPCA_FAILURE,
        ),
        Task(name="report_strategies", arguments=("report-strategies",)),
        Task(name="build_robustness", arguments=("build-robustness",)),
        Task(name="build_interpretability", arguments=("build-interpretability",)),
        Task(name="build_appendix", arguments=("build-appendix",)),
        Task(name="build_appendix_signals", arguments=("build-appendix-signals",)),
        Task(name="build_risk_premium", arguments=("build-risk-premium",)),
        Task(name="project_status", arguments=("status",)),
        Task(
            name="pytest",
            arguments=(
                "__external__",
                "-m",
                "pytest",
                str(PROJECT / "tests"),
                "-p",
                "no:cacheprovider",
            ),
        ),
        Task(
            name="ruff",
            arguments=(
                "__external__",
                "-m",
                "ruff",
                "check",
                str(PROJECT),
            ),
        ),
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def capture(command: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.stdout.strip()


def environment_snapshot() -> dict[str, Any]:
    """Capture the executable, ROCm device, packages, Git, and disk state."""

    import torch

    packages = sorted(
        {
            distribution.metadata["Name"]: distribution.version
            for distribution in importlib.metadata.distributions()
            if distribution.metadata["Name"]
        }.items()
    )
    disk = shutil.disk_usage(OUTPUTS)
    return {
        "captured_at": utc_now(),
        "repository": str(REPOSITORY),
        "project": str(PROJECT),
        "python_executable": sys.executable,
        "python_prefix": sys.prefix,
        "python_version": sys.version,
        "platform": platform.platform(),
        "torch_version": torch.__version__,
        "torch_hip": torch.version.hip,
        "cuda_available": torch.cuda.is_available(),
        "device_name": (
            torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        ),
        "device_count": torch.cuda.device_count(),
        "git_commit": capture(["git", "rev-parse", "HEAD"], cwd=REPOSITORY),
        "git_branch": capture(
            ["git", "branch", "--show-current"], cwd=REPOSITORY
        ),
        "git_status": capture(["git", "status", "--short"], cwd=REPOSITORY),
        "disk_total_bytes": disk.total,
        "disk_free_bytes": disk.free,
        "packages": [{"name": name, "version": version} for name, version in packages],
    }


def source_fingerprints() -> list[dict[str, Any]]:
    paths = (
        REPOSITORY / "pyproject.toml",
        REPOSITORY / "uv.lock",
        PROJECT / "run.py",
        PROJECT / "scripts" / "run_remaining_replication.py",
        PROJECT / "src" / "guijarro_ordonez_replication" / "orchestration.py",
        PROJECT / "config" / "default.yml",
        PROJECT / "config" / "output-registry.yml",
        PROJECT / "docs" / "replication-checklist.md",
        PROJECT / "docs" / "execution-status.md",
    )
    return [
        {
            "path": path.relative_to(REPOSITORY).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in paths
        if path.exists()
    ]


def artifact_inventory(output_root: Path) -> list[dict[str, Any]]:
    """Hash regenerated artifacts while excluding caches and checkpoints."""

    rows: list[dict[str, Any]] = []
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_root)
        lowered_parts = {part.lower() for part in relative.parts}
        if "orchestration" in lowered_parts or "checkpoints" in lowered_parts:
            continue
        if path.suffix.lower() == ".pt":
            continue
        stat = path.stat()
        rows.append(
            {
                "path": relative.as_posix(),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat(),
                "sha256": sha256_file(path),
            }
        )
    return rows


def audit_index(output_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(output_root.rglob("*.json")):
        relative = path.relative_to(output_root)
        lowered_parts = {part.lower() for part in relative.parts}
        if "orchestration" in lowered_parts or "checkpoints" in lowered_parts:
            continue
        if "audit" not in path.name.lower():
            continue
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
            parse_error = None
        except (OSError, json.JSONDecodeError) as error:
            payload = None
            parse_error = str(error)
        rows.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(path),
                "payload": payload,
                "parse_error": parse_error,
            }
        )
    return rows


def matching_processes(markers: tuple[str, ...]) -> list[int]:
    if not markers:
        return []
    matches: list[int] = []
    for process in psutil.process_iter(("pid", "cmdline")):
        try:
            if process.pid == os.getpid():
                continue
            command = " ".join(process.info["cmdline"] or ())
            if all(marker in command for marker in markers):
                matches.append(process.pid)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return matches


class Orchestrator:
    """Sequential runner that persists state after every transition."""

    def __init__(self, run_directory: Path, *, poll_seconds: int = 30) -> None:
        self.run_directory = run_directory
        self.run_directory.mkdir(parents=True, exist_ok=True)
        self.poll_seconds = poll_seconds
        self.terminal_log = run_directory / "terminal.log"
        self.events_path = run_directory / "events.jsonl"
        self.manifest_path = run_directory / "manifest.json"
        self.manifest: dict[str, Any] = {
            "schema_version": 1,
            "run_id": run_directory.name,
            "started_at": utc_now(),
            "status": "running",
            "tasks": [],
        }

    def log(self, message: str) -> None:
        line = f"[{utc_now()}] {message}"
        print(line, flush=True)
        with self.terminal_log.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def event(self, event: str, **payload: Any) -> None:
        append_jsonl(
            self.events_path, {"timestamp": utc_now(), "event": event, **payload}
        )

    def save(self) -> None:
        write_json_atomic(self.manifest_path, self.manifest)

    def wait_for_existing(self, task: Task) -> None:
        processes = matching_processes(task.active_markers)
        if not processes:
            return
        self.log(f"task={task.name} waiting_for_existing_processes pids={processes}")
        self.event("waiting_for_existing_processes", task=task.name, pids=processes)
        while processes:
            time.sleep(self.poll_seconds)
            processes = matching_processes(task.active_markers)
        self.log(f"task={task.name} existing_processes_finished")

    def command_for(self, task: Task) -> list[str]:
        if task.arguments[0] == "__external__":
            return [sys.executable, *task.arguments[1:]]
        return [sys.executable, str(RUNNER), *task.arguments]

    def run_task(self, task: Task) -> dict[str, Any]:
        self.wait_for_existing(task)
        expected = PROJECT / task.expected_artifact if task.expected_artifact else None
        if expected is not None and expected.exists():
            result = {
                "name": task.name,
                "outcome": "skipped_existing_artifact",
                "expected_artifact": task.expected_artifact,
                "started_at": utc_now(),
                "finished_at": utc_now(),
                "exit_code": 0,
            }
            self.log(f"task={task.name} skipped artifact={expected}")
            self.event("task_skipped", task=task.name, artifact=str(expected))
            return result

        command = self.command_for(task)
        started = time.monotonic()
        result: dict[str, Any] = {
            "name": task.name,
            "arguments": list(task.arguments),
            "command": subprocess.list2cmdline(command),
            "expected_artifact": task.expected_artifact,
            "started_at": utc_now(),
        }
        self.log(f"task={task.name} started command={result['command']}")
        self.event("task_started", task=task.name, command=command)
        environment = os.environ.copy()
        environment.update(
            {
                "DLSA_DEVICE": "cuda",
                "PYTHONUNBUFFERED": "1",
                "MIOPEN_USER_DB_PATH": str(
                    ORCHESTRATION_ROOT / "rocm-cache" / "miopen-user-db"
                ),
                "MIOPEN_CUSTOM_CACHE_DIR": str(
                    ORCHESTRATION_ROOT / "rocm-cache" / "miopen-kernel-cache"
                ),
            }
        )
        Path(environment["MIOPEN_USER_DB_PATH"]).mkdir(parents=True, exist_ok=True)
        Path(environment["MIOPEN_CUSTOM_CACHE_DIR"]).mkdir(
            parents=True, exist_ok=True
        )
        tail: deque[str] = deque(maxlen=200)
        process = subprocess.Popen(
            command,
            cwd=REPOSITORY,
            env=environment,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        assert process.stdout is not None
        for raw_line in process.stdout:
            line = raw_line.rstrip("\r\n")
            tail.append(line)
            self.log(f"task={task.name} | {line}")
        exit_code = process.wait()
        output_tail = "\n".join(tail)
        artifact_present = expected is None or expected.exists()
        if exit_code == 0 and artifact_present:
            outcome = "success"
        elif (
            task.acceptable_failure_text
            and task.acceptable_failure_text in output_tail
        ):
            outcome = "expected_methodological_failure"
        elif exit_code == 0:
            outcome = "failed_missing_artifact"
        else:
            outcome = "failed"
        result.update(
            {
                "finished_at": utc_now(),
                "duration_seconds": round(time.monotonic() - started, 3),
                "exit_code": exit_code,
                "outcome": outcome,
                "artifact_present": artifact_present,
                "output_tail": list(tail),
            }
        )
        self.log(
            f"task={task.name} finished outcome={outcome} exit_code={exit_code} "
            f"duration_seconds={result['duration_seconds']}"
        )
        self.event(
            "task_finished",
            task=task.name,
            outcome=outcome,
            exit_code=exit_code,
        )
        return result

    def run(self, tasks: tuple[Task, ...]) -> int:
        expected_prefix = (REPOSITORY / ".venv").resolve()
        if Path(sys.prefix).resolve() != expected_prefix:
            raise RuntimeError(
                f"orchestrator must run from {expected_prefix}, got {sys.prefix}"
            )
        environment = environment_snapshot()
        if not environment["cuda_available"]:
            raise RuntimeError("ROCm GPU is not available through torch.cuda")
        write_json_atomic(self.run_directory / "environment.json", environment)
        write_json_atomic(
            self.run_directory / "source_fingerprints.json", source_fingerprints()
        )
        self.manifest["task_contract"] = [asdict(task) for task in tasks]
        self.save()
        self.log(
            f"orchestration_started run_id={self.run_directory.name} "
            f"device={environment['device_name']} git={environment['git_commit']}"
        )
        try:
            for task in tasks:
                result = self.run_task(task)
                self.manifest["tasks"].append(result)
                self.save()
        except BaseException as error:
            self.manifest.update(
                {
                    "status": "interrupted",
                    "finished_at": utc_now(),
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
            self.save()
            self.log(f"orchestration_interrupted error={type(error).__name__}: {error}")
            raise

        write_json_atomic(
            self.run_directory / "audit_index.json", audit_index(OUTPUTS)
        )
        write_json_atomic(
            self.run_directory / "artifact_inventory.json",
            artifact_inventory(OUTPUTS),
        )
        failed = [
            result
            for result in self.manifest["tasks"]
            if result["outcome"] in {"failed", "failed_missing_artifact"}
        ]
        expected_failures = [
            result
            for result in self.manifest["tasks"]
            if result["outcome"] == "expected_methodological_failure"
        ]
        status = "completed_with_failures" if failed else "completed"
        if not failed and expected_failures:
            status = "completed_with_expected_methodological_failure"
        self.manifest.update({"status": status, "finished_at": utc_now()})
        self.save()
        self.write_summary()
        self.log(f"orchestration_finished status={status}")
        return 1 if failed else 0

    def write_summary(self) -> None:
        lines = [
            f"# DLSA orchestration {self.manifest['run_id']}",
            "",
            f"- Status: `{self.manifest['status']}`",
            f"- Started: `{self.manifest['started_at']}`",
            f"- Finished: `{self.manifest.get('finished_at')}`",
            "- Classification: Korean price-return replication variants; not exact U.S. replication.",
            "- Exact IPCA remains blocked by the 240-month history requirement.",
            "",
            "## Tasks",
            "",
        ]
        for task in self.manifest["tasks"]:
            lines.append(
                f"- `{task['name']}`: `{task['outcome']}` "
                f"(exit `{task.get('exit_code')}`)"
            )
        lines.extend(
            [
                "",
                "## Evidence",
                "",
                "- `terminal.log`: timestamped stdout/stderr for every command.",
                "- `events.jsonl`: machine-readable task transitions.",
                "- `manifest.json`: command contract, outcomes, durations, and output tails.",
                "- `environment.json`: Git, Python, Torch/ROCm, device, packages, and disk.",
                "- `source_fingerprints.json`: hashes of canonical code/config inputs.",
                "- `audit_index.json`: parsed audit files and their hashes.",
                "- `artifact_inventory.json`: output sizes, timestamps, and SHA-256 hashes.",
            ]
        )
        (self.run_directory / "summary.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )


def acquire_lock() -> Path:
    ORCHESTRATION_ROOT.mkdir(parents=True, exist_ok=True)
    lock_path = ORCHESTRATION_ROOT / "active.lock"
    if lock_path.exists():
        try:
            payload = json.loads(lock_path.read_text(encoding="utf-8"))
            pid = int(payload["pid"])
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            pid = -1
        if pid > 0 and psutil.pid_exists(pid):
            raise RuntimeError(f"another orchestrator is active with pid={pid}")
        lock_path.unlink(missing_ok=True)
    descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump({"pid": os.getpid(), "started_at": utc_now()}, handle)
    return lock_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id",
        help="stable output directory name; defaults to the current UTC timestamp",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=30,
        help="seconds between checks for an already-running holding experiment",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.poll_seconds <= 0:
        raise SystemExit("--poll-seconds must be positive")
    run_id = args.run_id or datetime.now(timezone.utc).strftime(
        "run-%Y%m%dT%H%M%SZ"
    )
    lock = acquire_lock()
    try:
        orchestrator = Orchestrator(
            ORCHESTRATION_ROOT / run_id, poll_seconds=args.poll_seconds
        )
        raise SystemExit(orchestrator.run(default_tasks()))
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
