"""Declarative experiment-grid expansion and audit-backed coverage checks."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_ARTIFACTS = (
    "simulation_audit.json",
    "daily_performance.csv",
    "daily_asset_weights.parquet",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Experiment:
    family: str
    priority: int
    factor_family: str
    k: int
    model: str
    objective: str
    lookback_days: int
    epochs: int
    rolling_retrain: bool
    holding_days: int
    transaction_cost: float
    short_holding_cost: float
    oos_start: str
    oos_end: str
    subperiods: int

    @property
    def id(self) -> str:
        mode = "rolling" if self.rolling_retrain else "constant"
        return (
            f"{self.family}__{self.factor_family}{self.k}__{self.model}__"
            f"{self.objective}__lb{self.lookback_days}__{mode}__"
            f"h{self.holding_days}__tc{self.transaction_cost:g}__"
            f"hc{self.short_holding_cost:g}"
        )

    @property
    def output_tag(self) -> str:
        prefix = "pca" if self.factor_family == "pca" else "ff"
        mode = "rolling" if self.rolling_retrain else "constant"
        cost = (
            f"tc{self.transaction_cost:g}_hc{self.short_holding_cost:g}"
            if self.transaction_cost or self.short_holding_cost
            else "no-cost"
        )
        tag = (
            f"{prefix}{self.k}_{self.model}_{self.objective}_"
            f"lb{self.lookback_days}_e{self.epochs}_{mode}_{cost}"
        )
        if self.holding_days != 1:
            tag += f"_h{self.holding_days}"
        return tag

    def command(self, project: Path) -> list[str]:
        simulation = "simulate-pca" if self.factor_family == "pca" else "simulate-fama-french"
        factor_flag = "--pca-factors" if self.factor_family == "pca" else "--ff-factors"
        command = [
            "uv",
            "run",
            "--no-sync",
            "python",
            str(project / "run.py"),
            simulation,
            factor_flag,
            str(self.k),
            "--simulation-model",
            self.model,
            "--simulation-objective",
            self.objective,
            "--simulation-lookback-days",
            str(self.lookback_days),
            "--simulation-epochs",
            str(self.epochs),
            "--simulation-holding-days",
            str(self.holding_days),
            "--simulation-transaction-cost",
            str(self.transaction_cost),
            "--simulation-short-holding-cost",
            str(self.short_holding_cost),
        ]
        if not self.rolling_retrain:
            command.append("--simulation-constant-model")
        return command

    def output_directory(self, project: Path) -> Path:
        return project / "outputs" / "strategies" / self.output_tag


def _values(value: object) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"factor grid must be a list, got {type(value).__name__}")
    return [int(item) for item in value]


def load_experiments(project: Path) -> tuple[list[Experiment], list[dict[str, Any]]]:
    path = project / "config" / "experiment-matrix.yml"
    config = yaml.safe_load(path.read_text("utf-8"))
    contract = config["contract"]
    experiments: list[Experiment] = []
    for family, raw in config["families"].items():
        common = {
            "family": family,
            "priority": int(raw["priority"]),
            "lookback_days": int(raw.get("lookback_days", contract["lookback_days"])),
            "epochs": int(raw.get("epochs", contract["epochs"])),
            "rolling_retrain": bool(raw.get("rolling_retrain", contract["rolling_retrain"])),
            "holding_days": int(raw.get("holding_days", contract["holding_days"])),
            "transaction_cost": float(raw.get("transaction_cost", contract["transaction_cost"])),
            "short_holding_cost": float(raw.get("short_holding_cost", contract["short_holding_cost"])),
            "oos_start": str(contract["oos_start"]),
            "oos_end": str(contract["oos_end"]),
            "subperiods": int(contract["subperiods"]),
        }
        for objective in raw["objectives"]:
            for factor_family in ("pca", "ff"):
                grid = raw.get(factor_family, [])
                if isinstance(grid, dict):
                    grid = grid.get(objective, [])
                for k in _values(grid):
                    for model in raw["models"]:
                        experiments.append(
                            Experiment(
                                factor_family=factor_family,
                                k=k,
                                model=str(model),
                                objective=str(objective),
                                **common,
                            )
                        )
    experiments.sort(key=lambda item: (item.priority, item.factor_family, item.model, item.k))
    ids = [experiment.id for experiment in experiments]
    if len(ids) != len(set(ids)):
        raise ValueError("experiment matrix contains duplicate identifiers")
    return experiments, list(config["non_runnable"])


def _matches(actual: object, expected: object) -> bool:
    if isinstance(expected, float):
        try:
            return math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=1e-12)
        except (TypeError, ValueError):
            return False
    return actual == expected


def validate_experiment(project: Path, experiment: Experiment) -> dict[str, Any]:
    directory = experiment.output_directory(project)
    missing = [name for name in REQUIRED_ARTIFACTS if not (directory / name).is_file()]
    base = {**asdict(experiment), "id": experiment.id, "output_directory": str(directory)}
    if missing:
        return {**base, "status": "unrun", "reason": f"missing artifacts: {', '.join(missing)}"}
    audit_path = directory / "simulation_audit.json"
    try:
        audit = json.loads(audit_path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {**base, "status": "unrun", "reason": f"invalid audit: {error}"}

    expected: dict[str, object] = {
        "model": experiment.model,
        "objective": experiment.objective,
        "lookback_days": experiment.lookback_days,
        "epochs": experiment.epochs,
        "rolling_retrain": experiment.rolling_retrain,
        "holding_days": experiment.holding_days,
        "transaction_cost": experiment.transaction_cost,
        "short_holding_cost": experiment.short_holding_cost,
        "oos_start": experiment.oos_start,
        "oos_end": experiment.oos_end,
        "subperiods": experiment.subperiods,
    }
    mismatches = {
        key: {"expected": value, "actual": audit.get(key)}
        for key, value in expected.items()
        if not _matches(audit.get(key), value)
    }
    factor_model = audit.get("factor_model")
    if experiment.factor_family == "pca":
        accepted = {"Stock returns K0"} if experiment.k == 0 else {f"PCA{experiment.k}", "PCA"}
    else:
        accepted = {f"Korean FF{experiment.k}"}
    if factor_model not in accepted:
        mismatches["factor_model"] = {"expected": sorted(accepted), "actual": factor_model}
    if mismatches:
        return {**base, "status": "unrun", "reason": "audit contract mismatch", "mismatches": mismatches}

    artifacts = {
        name: {"path": str(directory / name), "sha256": sha256_file(directory / name)}
        for name in REQUIRED_ARTIFACTS
    }
    return {
        **base,
        "status": "complete",
        "audit_path": str(audit_path),
        "audit_sha256": artifacts["simulation_audit.json"]["sha256"],
        "artifacts": artifacts,
    }


def experiment_coverage(project: Path) -> dict[str, Any]:
    experiments, non_runnable = load_experiments(project)
    runnable = [validate_experiment(project, experiment) for experiment in experiments]
    counts: dict[str, int] = {}
    for record in [*runnable, *non_runnable]:
        status = str(record["status"])
        counts[status] = counts.get(status, 0) + 1
    family_counts: dict[str, dict[str, int]] = {}
    for record in runnable:
        family = str(record["family"])
        status = str(record["status"])
        family_counts.setdefault(family, {})[status] = family_counts.setdefault(family, {}).get(status, 0) + 1
    return {
        "matrix": str(project / "config" / "experiment-matrix.yml"),
        "summary": dict(sorted(counts.items())),
        "runnable_total": len(runnable),
        "runnable": runnable,
        "non_runnable": non_runnable,
        "families": family_counts,
    }
