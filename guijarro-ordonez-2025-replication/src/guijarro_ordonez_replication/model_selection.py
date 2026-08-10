"""Appendix C.1 validation grid and alternative CNN network experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .results import performance_statistics
from .trading import ResidualPanel, SimulationConfig, simulate_rolling_strategy


@dataclass(frozen=True)
class CNNModelSpecification:
    """One CNN+Transformer hyperparameter specification."""

    name: str
    filters: tuple[int, ...]
    attention_heads: int
    hidden_units_factor: int
    dropout: float
    training_window_days: int


VALIDATION_GRID = tuple(
    CNNModelSpecification(
        name=f"D{filters}_A{heads}_H{hidden_factor}_P{dropout:g}",
        filters=(1, filters),
        attention_heads=heads,
        hidden_units_factor=hidden_factor,
        dropout=dropout,
        training_window_days=750,
    )
    for filters in (8, 16)
    for heads in (2, 4)
    for hidden_factor in (2, 3)
    for dropout in (0.25, 0.5)
)


ALTERNATIVE_NETWORKS = (
    CNNModelSpecification("Network 1", (1, 8), 4, 2, 0.25, 1000),
    CNNModelSpecification("Network 2", (1, 16), 4, 2, 0.5, 1000),
    CNNModelSpecification("Network 3", (1, 8), 2, 2, 0.25, 1000),
    CNNModelSpecification("Network 4", (1, 8), 4, 2, 0.25, 1250),
    CNNModelSpecification("Network 5", (1, 8), 4, 2, 0.25, 750),
)


def slice_panel(panel: ResidualPanel, stop: int) -> ResidualPanel:
    """Truncate a residual panel without changing its coordinate system."""

    if not 0 < stop <= len(panel.dates):
        raise ValueError("panel stop must lie inside the available dates")
    return ResidualPanel(
        dates=panel.dates[:stop],
        tickers=panel.tickers,
        residuals=panel.residuals[:stop],
        left=panel.left[:stop],
        right=panel.right[:stop],
        observed=panel.observed[:stop],
        extra_asset_loadings=(
            None
            if panel.extra_asset_loadings is None
            else panel.extra_asset_loadings[:stop]
        ),
        asset_tickers=panel.asset_tickers,
    )


def _simulation_config(
    specification: CNNModelSpecification,
    output_directory: Path,
    *,
    epochs: int,
    stride_days: int,
    rolling_retrain: bool,
) -> SimulationConfig:
    return SimulationConfig(
        model_name="cnn_transformer",
        objective="sharpe",
        training_window_days=specification.training_window_days,
        stride_days=stride_days,
        epochs=epochs,
        rolling_retrain=rolling_retrain,
        checkpoint_directory=output_directory / "checkpoints",
        cnn_filter_numbers=specification.filters,
        cnn_attention_heads=specification.attention_heads,
        cnn_hidden_units_factor=specification.hidden_units_factor,
        cnn_dropout=specification.dropout,
    )


def _run_or_load(
    panel: ResidualPanel,
    specification: CNNModelSpecification,
    directory: Path,
    *,
    epochs: int,
    stride_days: int,
    rolling_retrain: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    audit_path = directory / "simulation_audit.json"
    daily_path = directory / "daily_performance.csv"
    if audit_path.exists() and daily_path.exists():
        return pd.read_csv(daily_path, parse_dates=["date"]), json.loads(
            audit_path.read_text("utf-8")
        )
    directory.mkdir(parents=True, exist_ok=True)
    result = simulate_rolling_strategy(
        panel,
        _simulation_config(
            specification,
            directory,
            epochs=epochs,
            stride_days=stride_days,
            rolling_retrain=rolling_retrain,
        ),
        progress=lambda event: print(json.dumps(event, ensure_ascii=False), flush=True),
    )
    result.daily.to_csv(daily_path, index=False)
    result.weights.to_parquet(directory / "daily_asset_weights.parquet")
    audit = {
        **result.audit,
        "model_specification": specification.name,
    }
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result.daily, audit


def write_alternative_network_specification(output_directory: Path) -> pd.DataFrame:
    """Write the data-independent Korean copy of paper Table A.IV."""

    output_directory.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(
        [
            {
                "model": spec.name,
                "filter_numbers": list(spec.filters),
                "filter_size": 2,
                "attention_heads": spec.attention_heads,
                "hidden_units": spec.hidden_units_factor * spec.filters[-1],
                "dropout": spec.dropout,
                "lookback_days": 30,
                "training_window_days": spec.training_window_days,
            }
            for spec in ALTERNATIVE_NETWORKS
        ]
    )
    table.to_csv(output_directory / "table_a04_alternative_network_specification.csv", index=False)
    return table


def run_validation_grid(
    panel: ResidualPanel,
    output_directory: Path,
    *,
    epochs: int = 100,
    max_candidates: int = 16,
) -> dict[str, object]:
    """Train on days 1-750 and evaluate days 751-1000 for paper Table A.III."""

    if len(panel.dates) < 1000:
        raise ValueError("validation grid needs at least 1000 residual days")
    if not 1 <= max_candidates <= len(VALIDATION_GRID):
        raise ValueError("max_candidates must be between 1 and 16")
    validation_panel = slice_panel(panel, 1000)
    rows = []
    for index, specification in enumerate(VALIDATION_GRID[:max_candidates]):
        daily, _ = _run_or_load(
            validation_panel,
            specification,
            output_directory / "candidates" / f"candidate_{index + 1:02d}",
            epochs=epochs,
            stride_days=250,
            rolling_retrain=False,
        )
        rows.append(
            {
                "candidate": index + 1,
                "filters": specification.filters[-1],
                "attention_heads": specification.attention_heads,
                "hidden_units_factor": specification.hidden_units_factor,
                "dropout": specification.dropout,
                **performance_statistics(daily["return"].to_numpy()),
            }
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(
        output_directory / "table_a03_candidate_validation_performance.csv", index=False
    )
    audit = {
        "classification": "Korean PCA5 validation-grid variant",
        "candidate_count": len(rows),
        "epochs": epochs,
        "training_days": 750,
        "validation_days": 250,
        "paper_grid_complete": len(rows) == 16 and epochs == 100,
        "exact_ipca_validation": "blocked by 240-month IPCA history",
    }
    (output_directory / "model_selection_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_alternative_network_specification(output_directory)
    return audit


def run_alternative_networks(
    panels: dict[str, ResidualPanel],
    output_directory: Path,
    *,
    epochs: int = 100,
    max_models: int = 5,
) -> dict[str, object]:
    """Evaluate Table A.IV networks on available benchmark residual datasets."""

    if not 1 <= max_models <= len(ALTERNATIVE_NETWORKS):
        raise ValueError("max_models must be between 1 and 5")
    rows = []
    for panel_name, panel in panels.items():
        for index, specification in enumerate(ALTERNATIVE_NETWORKS[:max_models]):
            daily, _ = _run_or_load(
                panel,
                specification,
                output_directory / "runs" / panel_name / f"network_{index + 1}",
                epochs=epochs,
                stride_days=125,
                rolling_retrain=True,
            )
            rows.append(
                {
                    "residual_model": panel_name,
                    "model": specification.name,
                    **performance_statistics(daily["return"].to_numpy()),
                }
            )
    output_directory.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(
        output_directory / "table_a05_alternative_network_performance.csv", index=False
    )
    write_alternative_network_specification(output_directory)
    audit = {
        "classification": "Korean available-residual alternative-network variants",
        "residual_models": sorted(panels),
        "network_count": max_models,
        "epochs": epochs,
        "paper_network_contract_complete": max_models == 5 and epochs == 100,
        "exact_ipca_column": "blocked by 240-month IPCA history",
    }
    (output_directory / "alternative_network_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit
