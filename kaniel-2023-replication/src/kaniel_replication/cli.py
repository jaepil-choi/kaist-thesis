"""Command-line interface for the replication project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import pandas as pd
import pyarrow.dataset as ds

from .audit import audit_inputs
from .config import ReplicationConfig, load_config
from .panel import build_class_month_panel
from .model import (
    build_parsimonious_sample,
    fit_cross_oos_mlp,
    form_prediction_portfolios,
)
from .provenance import sha256, write_manifest
from .registry import load_registry, status_counts
from .share_class_figures import generate_share_class_figures
from .share_classes import validate_share_classes
from .static_outputs import generate_static_outputs
from .stock_factors import (
    attach_risk_free,
    build_carhart_equity_factors,
    derive_non_pit_book_equity,
    prepare_monthly_stock_panel,
)


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load(args: argparse.Namespace) -> ReplicationConfig:
    return load_config(Path(args.config))


def _status(args: argparse.Namespace) -> int:
    config = _load(args)
    registry = load_registry(config.project_root / "config" / "output-registry.yml")
    counts = status_counts(registry)
    print(f"Registered outputs: {len(registry['outputs'])}")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")
    return 0


def _audit(args: argparse.Namespace) -> int:
    result = audit_inputs(_load(args))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def _static(args: argparse.Namespace) -> int:
    paths = generate_static_outputs(_load(args))
    for path in paths:
        print(path)
    return 0


def _build_panel(args: argparse.Namespace) -> int:
    config = _load(args)
    panel_config = config.raw["panel"]
    universe = config.raw["universe"]
    if universe.get("use_snapshot_attributes_as_historical_filter", False):
        raise ValueError(
            "Historical filtering by current snapshot attributes is disabled by design"
        )
    output = (
        Path(args.output).resolve()
        if args.output
        else config.output_root / "intermediate" / "class_month_panel.parquet"
    )
    result = build_class_month_panel(
        source=config.path("data", "fund_daily"),
        output=output,
        active_type_codes=set(universe["active_type_codes"]),
        large_type_code=str(universe["large_type_code"]),
        start=args.start,
        end=args.end,
        batch_size=int(panel_config["batch_size"]),
        plausible_factor_min=float(panel_config["plausible_daily_factor_min"]),
        plausible_factor_max=float(panel_config["plausible_daily_factor_max"]),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def _validate_external(args: argparse.Namespace) -> int:
    config = _load(args)
    missing = []
    for key in ("factor_monthly", "sentiment_monthly", "activity_monthly"):
        path = config.path("data", key)
        print(f"{key}: {'OK' if path.exists() else 'MISSING'} - {path}")
        if not path.exists():
            missing.append(key)
    return 2 if missing else 0


def _build_stock_factors(args: argparse.Namespace) -> int:
    config = _load(args)
    construction = config.raw["factor_construction"]
    allow_non_pit = bool(args.allow_non_pit_book_equity)
    lag = args.reporting_lag_months
    if lag is None:
        raise ValueError(
            "--reporting-lag-months is required; no economic lag is inferred from fiscal dates"
        )
    if not allow_non_pit:
        raise ValueError(
            "Exact HML is blocked because historical announcement timestamps are absent. "
            "Use --allow-non-pit-book-equity only for a labeled sensitivity run."
        )
    if not args.risk_free:
        raise ValueError("--risk-free is required and must contain month,rf in decimal units")
    price_path = config.path("data", "stock_prices")
    filters = []
    if args.start:
        filters.append(("date", ">=", pd.Timestamp(args.start).to_pydatetime()))
    if args.end:
        filters.append(("date", "<=", pd.Timestamp(args.end).to_pydatetime()))
    prices = pd.read_parquet(
        price_path,
        columns=["date", "ticker", "return", "market_cap"],
        filters=filters or None,
    )
    statement_path = config.path("data", "statement_facts")
    dataset = ds.dataset(statement_path, format="parquet", partitioning="hive")
    statement_filter = (
        (ds.field("statement_scope") == "consolidated")
        & (ds.field("settlement_type") == "D")
        & (ds.field("account_code") == "4001160000")
    )
    facts = dataset.to_table(
        filter=statement_filter,
        columns=[
            "ticker",
            "fiscal_period",
            "settlement_type",
            "statement_scope",
            "account_code",
            "numeric_value",
            "dump_last_modified",
        ],
    ).to_pandas()
    monthly = prepare_monthly_stock_panel(prices)
    book = derive_non_pit_book_equity(
        facts,
        reporting_lag_months=int(lag),
        allow_non_pit=allow_non_pit,
    )
    equity_factors = build_carhart_equity_factors(monthly, book)
    risk_free_path = Path(args.risk_free).resolve()
    factors = attach_risk_free(equity_factors, pd.read_csv(risk_free_path))
    output = (
        Path(args.output).resolve()
        if args.output
        else config.output_root / "intermediate" / "korea_carhart_monthly_non_pit.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    factors.to_csv(output, index=False, encoding="utf-8")
    write_manifest(
        output.with_suffix(".manifest.json"),
        {
            "kind": "non_pit_factor_sensitivity",
            "inputs": {
                "prices": {"path": str(price_path), "sha256": sha256(price_path)},
                "statement_facts": str(statement_path),
                "risk_free": {
                    "path": str(risk_free_path),
                    "sha256": sha256(risk_free_path),
                },
            },
            "parameters": {
                **construction,
                "reporting_lag_months": int(lag),
                "allow_non_pit_book_equity": True,
                "start": args.start,
                "end": args.end,
            },
            "rows": len(factors),
            "limitations": [
                "Historical statement announcement timestamps are unavailable.",
                "Latest local dump revisions may contain restatement look-ahead.",
                "market_cap basis and total-return semantics remain unverified.",
            ],
        },
    )
    print(json.dumps({"path": str(output), "rows": len(factors)}, ensure_ascii=False))
    return 0


def _run_parsimonious(args: argparse.Namespace) -> int:
    config = _load(args)
    panel_path = (
        Path(args.panel).resolve()
        if args.panel
        else config.output_root / "intermediate" / "class_month_panel.parquet"
    )
    required_paths = {
        "panel": panel_path,
        "factors": config.path("data", "factor_monthly"),
        "sentiment": config.path("data", "sentiment_monthly"),
    }
    missing = [f"{key}: {path}" for key, path in required_paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing parsimonious inputs: " + "; ".join(missing))
    panel = pd.read_parquet(panel_path)
    factors = pd.read_csv(required_paths["factors"])
    sentiment = pd.read_csv(required_paths["sentiment"])
    abnormal = config.raw["abnormal_return"]
    sample = build_parsimonious_sample(
        panel,
        factors,
        sentiment,
        rolling_window_months=int(abnormal["rolling_window_months"]),
        minimum_history_months=int(abnormal["minimum_history_months"]),
        momentum_minimum_observations=int(abnormal["momentum_minimum_observations"]),
    )
    model = config.raw["model"]
    predictions = fit_cross_oos_mlp(
        sample,
        feature_columns=["rank_flow", "rank_F_r12_2", "sentiment"],
        scheme=str(model["sampling_scheme"]),
        random_seed=int(config.raw["random_seed"]),
        ensemble_size=int(model["ensemble_size"]),
        hidden_units=int(model["hidden_units"]),
        learning_rate=float(model["learning_rate"]),
        l2_penalty=float(model["l2_penalty"]),
        max_iter=int(model["max_iter"]),
    )
    portfolios = form_prediction_portfolios(predictions)
    intermediate = config.output_root / "intermediate"
    tables = config.output_root / "tables"
    intermediate.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    prediction_path = intermediate / "parsimonious_cross_oos_predictions.parquet"
    portfolio_path = tables / "table_07_parsimonious_portfolios.csv"
    predictions.to_parquet(prediction_path, index=False)
    portfolios.to_csv(portfolio_path, index=False, encoding="utf-8")
    write_manifest(
        config.output_root / "manifests" / "parsimonious.json",
        {
            "kind": "parsimonious_cross_oos",
            "inputs": {key: str(path) for key, path in required_paths.items()},
            "model": model,
            "dropout_gap": "sklearn MLP backend does not implement paper dropout_keep_probability=0.95",
            "prediction_rows": int(predictions["prediction"].notna().sum()),
            "portfolio_months": len(portfolios),
        },
    )
    print(
        json.dumps(
            {
                "predictions": int(predictions["prediction"].notna().sum()),
                "portfolio_months": len(portfolios),
                "outputs": [str(prediction_path), str(portfolio_path)],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _validate_share_classes(args: argparse.Namespace) -> int:
    config = _load(args)
    panel_path = (
        Path(args.panel).resolve()
        if args.panel
        else config.output_root / "intermediate" / "class_month_panel.parquet"
    )
    if not panel_path.exists():
        raise FileNotFoundError(
            f"Build the class-month panel before validation: {panel_path}"
        )
    result = validate_share_classes(
        panel_path=panel_path,
        relations_path=config.path("data", "class_relations"),
        output_dir=config.output_root / "quality" / "share_classes",
        thresholds=config.raw["share_class_validation"],
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def _share_class_figures(args: argparse.Namespace) -> int:
    config = _load(args)
    quality_dir = config.output_root / "quality" / "share_classes"
    required = {
        "comparison": quality_dir / "share_class_month_comparison.parquet",
        "diagnostics": quality_dir / "share_class_group_diagnostics.csv",
        "summary": quality_dir / "share_class_validation_summary.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Run validate-share-classes before figures: " + ", ".join(missing)
        )
    paths = generate_share_class_figures(
        comparison_path=required["comparison"],
        diagnostics_path=required["diagnostics"],
        summary_path=required["summary"],
        output_dir=quality_dir / "figures",
    )
    for path in paths:
        print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    project_root = _default_project_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(project_root / "config" / "default.yml"),
        help="Path to the replication YAML configuration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Validate and summarize the output registry.")
    subparsers.add_parser(
        "audit", help="Audit source schemas and external-input presence."
    )
    subparsers.add_parser("static", help="Generate data-independent paper outputs.")
    subparsers.add_parser(
        "validate-inputs", help="Check whether factor and macro inputs are present."
    )
    stock_factors = subparsers.add_parser(
        "build-stock-factors",
        help="Build a labeled non-PIT Carhart sensitivity series from local stock data.",
    )
    stock_factors.add_argument("--start")
    stock_factors.add_argument("--end")
    stock_factors.add_argument("--reporting-lag-months", type=int)
    stock_factors.add_argument("--allow-non-pit-book-equity", action="store_true")
    stock_factors.add_argument("--risk-free")
    stock_factors.add_argument("--output")
    parsimonious = subparsers.add_parser(
        "run-parsimonious",
        help="Run flow + fund momentum + sentiment cross-OOS prediction.",
    )
    parsimonious.add_argument("--panel")
    share_classes = subparsers.add_parser(
        "validate-share-classes",
        help="Compare representative rows with lag-TNA-weighted share classes.",
    )
    share_classes.add_argument("--panel", help="Optional class-month panel path.")
    subparsers.add_parser(
        "share-class-figures",
        help="Plot TNA agreement, return gaps, and consolidation decisions.",
    )

    panel = subparsers.add_parser(
        "build-panel", help="Build the point-in-time class-level monthly panel."
    )
    panel.add_argument("--start", help="Inclusive date filter (YYYY-MM-DD).")
    panel.add_argument("--end", help="Inclusive date filter (YYYY-MM-DD).")
    panel.add_argument("--output", help="Optional output Parquet path.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected command."""

    args = build_parser().parse_args(argv)
    handlers = {
        "status": _status,
        "audit": _audit,
        "static": _static,
        "build-panel": _build_panel,
        "validate-inputs": _validate_external,
        "build-stock-factors": _build_stock_factors,
        "run-parsimonious": _run_parsimonious,
        "validate-share-classes": _validate_share_classes,
        "share-class-figures": _share_class_figures,
    }
    return handlers[args.command](args)
