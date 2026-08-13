from __future__ import annotations

import json
from pathlib import Path

from guijarro_ordonez_replication.experiment_matrix import (
    Experiment,
    load_experiments,
    validate_experiment,
)


PROJECT = Path(__file__).resolve().parents[1]


def test_matrix_has_handoff_job_counts() -> None:
    experiments, non_runnable = load_experiments(PROJECT)
    counts: dict[str, int] = {}
    for experiment in experiments:
        counts[experiment.family] = counts.get(experiment.family, 0) + 1
    assert counts == {
        "p0_baseline_cnn_sharpe": 10,
        "p1_mean_variance": 20,
        "p2_cnn_60_day": 10,
        "p3_cnn_four_year_constant": 10,
        "p4_signal_ablation": 20,
        "p5_friction_aware_cnn": 12,
    }
    assert len(experiments) == 82
    assert {item["status"] for item in non_runnable} == {"data_blocked", "not_applicable"}


def test_command_and_output_tag_match_run_cli() -> None:
    experiment = Experiment(
        family="test",
        priority=0,
        factor_family="pca",
        k=3,
        model="cnn_transformer_frictions",
        objective="meanvar",
        lookback_days=30,
        epochs=100,
        rolling_retrain=False,
        holding_days=1,
        transaction_cost=0.0005,
        short_holding_cost=0.0001,
        oos_start="2024-01-19",
        oos_end="2026-07-20",
        subperiods=5,
    )
    assert experiment.output_tag == "pca3_cnn_transformer_frictions_meanvar_lb30_e100_constant_tc0.0005_hc0.0001"
    command = experiment.command(PROJECT)
    assert command[:4] == ["uv", "run", "--no-sync", "python"]
    assert "--simulation-constant-model" in command


def test_validation_requires_contract_and_all_artifacts(tmp_path: Path) -> None:
    experiment = Experiment(
        family="test",
        priority=0,
        factor_family="ff",
        k=3,
        model="cnn_transformer",
        objective="sharpe",
        lookback_days=30,
        epochs=100,
        rolling_retrain=True,
        holding_days=1,
        transaction_cost=0.0,
        short_holding_cost=0.0,
        oos_start="2024-01-19",
        oos_end="2026-07-20",
        subperiods=5,
    )
    output = experiment.output_directory(tmp_path)
    output.mkdir(parents=True)
    audit = {
        "factor_model": "Korean FF3",
        "model": "cnn_transformer",
        "objective": "sharpe",
        "lookback_days": 30,
        "epochs": 100,
        "rolling_retrain": True,
        "holding_days": 1,
        "transaction_cost": 0.0,
        "short_holding_cost": 0.0,
        "oos_start": "2024-01-19",
        "oos_end": "2026-07-20",
        "subperiods": 5,
    }
    (output / "simulation_audit.json").write_text(json.dumps(audit), encoding="utf-8")
    assert validate_experiment(tmp_path, experiment)["status"] == "unrun"
    (output / "daily_performance.csv").write_text("date,return\n", encoding="utf-8")
    (output / "daily_asset_weights.parquet").write_bytes(b"fixture")
    complete = validate_experiment(tmp_path, experiment)
    assert complete["status"] == "complete"
    assert set(complete["artifacts"]) == {
        "simulation_audit.json",
        "daily_performance.csv",
        "daily_asset_weights.parquet",
    }
