"""Tests for the durable remaining-replication orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

from guijarro_ordonez_replication.orchestration import (
    EXPECTED_IPCA_FAILURE,
    artifact_inventory,
    audit_index,
    default_tasks,
)


def test_default_tasks_cover_remaining_pipeline_in_order() -> None:
    tasks = default_tasks()

    assert [task.name for task in tasks] == [
        "five_day_holding",
        "alternative_networks",
        "ipca_k1_short_history",
        "report_strategies",
        "build_robustness",
        "build_interpretability",
        "build_appendix",
        "build_appendix_signals",
        "build_risk_premium",
        "project_status",
        "pytest",
        "ruff",
    ]
    assert tasks[0].active_markers == (
        "simulate-pca",
        "--simulation-holding-days",
        "5",
    )
    assert tasks[2].acceptable_failure_text == EXPECTED_IPCA_FAILURE


def test_artifact_inventory_hashes_outputs_and_excludes_runtime_state(
    tmp_path: Path,
) -> None:
    (tmp_path / "paper-korean").mkdir()
    artifact = tmp_path / "paper-korean" / "result.csv"
    artifact.write_text("value\n1\n", encoding="utf-8")
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "checkpoints" / "model.pt").write_bytes(b"checkpoint")
    (tmp_path / "orchestration").mkdir()
    (tmp_path / "orchestration" / "terminal.log").write_text(
        "changing", encoding="utf-8"
    )

    rows = artifact_inventory(tmp_path)

    assert [row["path"] for row in rows] == ["paper-korean/result.csv"]
    assert len(rows[0]["sha256"]) == 64


def test_audit_index_parses_audits_and_records_invalid_json(tmp_path: Path) -> None:
    valid = tmp_path / "simulation_audit.json"
    valid.write_text(json.dumps({"sharpe": 1.5}), encoding="utf-8")
    invalid = tmp_path / "broken_audit.json"
    invalid.write_text("not-json", encoding="utf-8")

    rows = audit_index(tmp_path)

    assert [row["path"] for row in rows] == [
        "broken_audit.json",
        "simulation_audit.json",
    ]
    assert rows[0]["parse_error"] is not None
    assert rows[1]["payload"] == {"sharpe": 1.5}
