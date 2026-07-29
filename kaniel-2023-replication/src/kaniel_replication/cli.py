"""Command-line interface for the replication project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .audit import audit_inputs
from .config import ReplicationConfig, load_config
from .panel import build_class_month_panel
from .registry import load_registry, status_counts
from .share_classes import validate_share_classes
from .static_outputs import generate_static_outputs


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
    subparsers.add_parser("audit", help="Audit source schemas and external-input presence.")
    subparsers.add_parser("static", help="Generate data-independent paper outputs.")
    subparsers.add_parser(
        "validate-inputs", help="Check whether factor and macro inputs are present."
    )
    share_classes = subparsers.add_parser(
        "validate-share-classes",
        help="Compare representative rows with lag-TNA-weighted share classes.",
    )
    share_classes.add_argument("--panel", help="Optional class-month panel path.")

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
        "validate-share-classes": _validate_share_classes,
    }
    return handlers[args.command](args)
