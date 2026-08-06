"""Command-line interface for the Korean Arnott replication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import matplotlib
import pandas as pd
import pyarrow.parquet as pq

from .config import ReplicationConfig, load_config
from .event_study import (
    compute_event_paths,
    compute_event_window_returns,
    summarize_event_windows,
)
from .events import build_membership_events, summarize_event_counts
from .provenance import write_manifest
from .registry import load_registry, status_counts

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load(args: argparse.Namespace) -> ReplicationConfig:
    return load_config(Path(args.config))


def _status(args: argparse.Namespace) -> int:
    config = _load(args)
    registry = load_registry(config.project_root / "config" / "output-registry.yml")
    for section in ("paper_outputs", "korea_extensions"):
        print(f"{section}: {len(registry.get(section, []))}")
        for status, count in sorted(status_counts(registry, section).items()):
            print(f"  {status}: {count}")
    return 0


def _audit(args: argparse.Namespace) -> int:
    config = _load(args)
    result: dict[str, object] = {"inputs": {}, "blockers": []}
    for key in ("constituents", "index_levels", "stock_prices"):
        path = config.path("data", key)
        parquet = pq.ParquetFile(path)
        result["inputs"][key] = {
            "path": str(path),
            "rows": parquet.metadata.num_rows,
            "columns": parquet.schema_arrow.names,
        }
    result["blockers"] = [
        "Announcement date/time is absent; announcement-window paper outputs remain blocked.",
        "Change reason is absent; discretionary versus nondiscretionary deletions cannot be identified.",
        "KOSPI200 methodology is not equivalent to the S&P 500 constituent-selection rule.",
    ]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _load_events(config: ReplicationConfig) -> pd.DataFrame:
    members = pd.read_parquet(
        config.path("data", "constituents"),
        columns=["일자", "적용일", "종목코드2", "종목명국문", "지수내비중"],
    )
    levels = pd.read_parquet(
        config.path("data", "index_levels"),
        columns=["VALUE_DATE", "NEXT_REBALANCE_DATE"],
    )
    event_config = config.raw["events"]
    return build_membership_events(
        members,
        levels,
        scheduled_only=bool(event_config["scheduled_only"]),
        require_both_sides=bool(event_config["require_both_sides"]),
    )


def _build_events(args: argparse.Namespace) -> int:
    config = _load(args)
    events = _load_events(config)
    output = config.output_root / "intermediate" / "membership_events.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    events.to_parquet(output, index=False)
    print(json.dumps({"path": str(output), "rows": len(events)}, ensure_ascii=False))
    return 0


def _plot_paths(paths: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 5.5))
    axis.plot(paths["offset"], paths["addition_mean"] * 100, label="Additions")
    axis.plot(paths["offset"], paths["deletion_mean"] * 100, label="Deletions")
    axis.plot(
        paths["offset"],
        paths["deletion_minus_addition"] * 100,
        label="Deletion minus addition",
        linewidth=2.2,
    )
    axis.axvline(0, color="black", linewidth=0.9, linestyle="--")
    axis.axhline(0, color="grey", linewidth=0.6)
    axis.set_xlabel("Trading-session offset from effective date")
    axis.set_ylabel("Mean cumulative market-adjusted return (%)")
    axis.set_title("KOSPI200 effective-date membership-change paths")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _core(args: argparse.Namespace) -> int:
    config = _load(args)
    event_config = config.raw["events"]
    events = _load_events(config)
    if events.empty:
        raise ValueError("No membership-change events survived the configured gates")

    levels_path = config.path("data", "index_levels")
    levels = pd.read_parquet(levels_path, columns=["VALUE_DATE", "VALUE"])
    minimum_date = pd.Timestamp(events["effective_date"].min()) - pd.Timedelta(days=550)
    maximum_date = pd.Timestamp(events["effective_date"].max()) + pd.Timedelta(days=550)
    tickers = sorted(events["ticker"].unique())
    price_path = config.path("data", "stock_prices")
    prices = pd.read_parquet(
        price_path,
        columns=["date", "ticker", "return"],
        filters=[
            ("ticker", "in", tickers),
            ("date", ">=", minimum_date.to_pydatetime()),
            ("date", "<=", maximum_date.to_pydatetime()),
        ],
    )

    intermediate = config.output_root / "intermediate"
    tables = config.output_root / "tables"
    figures = config.output_root / "figures"
    for directory in (intermediate, tables, figures):
        directory.mkdir(parents=True, exist_ok=True)

    event_path = intermediate / "membership_events.parquet"
    event_returns_path = intermediate / "effective_date_event_returns.parquet"
    counts_path = tables / "kr_table_01_membership_changes.csv"
    summary_path = tables / "kr_table_02_effective_date_event_returns.csv"
    paths_path = intermediate / "effective_date_event_paths.parquet"
    figure_path = figures / "kr_fig_01_effective_date_event_paths.png"

    events.to_parquet(event_path, index=False)
    summarize_event_counts(events).to_csv(counts_path, index=False, encoding="utf-8")
    event_returns = compute_event_window_returns(
        events,
        prices,
        levels,
        event_config["windows"],
        minimum_coverage=float(event_config["minimum_return_coverage"]),
    )
    event_returns.to_parquet(event_returns_path, index=False)
    summarize_event_windows(event_returns).to_csv(
        summary_path, index=False, encoding="utf-8"
    )
    paths = compute_event_paths(
        events,
        prices,
        levels,
        minimum_offset=int(event_config["path_min_offset"]),
        maximum_offset=int(event_config["path_max_offset"]),
        minimum_coverage=float(event_config["minimum_return_coverage"]),
    )
    paths.to_parquet(paths_path, index=False)
    _plot_paths(paths, figure_path)

    outputs = [
        event_path,
        event_returns_path,
        counts_path,
        summary_path,
        paths_path,
        figure_path,
    ]
    write_manifest(
        config.output_root / "manifests" / "core.json",
        command="core",
        inputs={
            "constituents": config.path("data", "constituents"),
            "index_levels": levels_path,
            "stock_prices": price_path,
        },
        outputs=outputs,
        parameters=event_config,
        limitations=[
            "This is an effective-date Korean extension, not an announcement-date exact replication.",
            "Announcement dates and change reasons remain missing.",
            "Missing post-event stock returns are not zero-filled.",
        ],
    )
    print(
        json.dumps(
            {
                "events": len(events),
                "event_groups": int(events["event_id"].nunique()),
                "event_return_rows": len(event_returns),
                "outputs": [str(path) for path in outputs],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    project_root = _default_project_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default=str(project_root / "config" / "default.yml")
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("audit")
    subparsers.add_parser("build-events")
    subparsers.add_parser("core")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {
        "status": _status,
        "audit": _audit,
        "build-events": _build_events,
        "core": _core,
    }[args.command](args)
