"""Compare IPCA residual panels against each other and the PCA5 reference.

An arbitrage residual is only useful if it has removed systematic risk.  This
script reports, per residual file, the annualized residual volatility, the
share of excess-return variance removed, and how much market exposure is left
after the factor projection.  It also reports the cross-panel correlation so
that a ridge and a no-ridge fit can be compared directly.

Usage:

    uv run python guijarro-ordonez-2025-replication/scripts/compare_ipca_residuals.py
    uv run python .../compare_ipca_residuals.py --residuals a.parquet b.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
OUTPUT = PROJECT / "outputs"

DEFAULT_FILES = (
    OUTPUT / "ipca" / "daily_residuals_k5_i60_w60_c8.parquet",
    OUTPUT / "ipca" / "daily_residuals_k5_i60_w60_c8_r0p01.parquet",
    OUTPUT / "pca" / "daily_residuals_k5_20200102_c252_l60.parquet",
)
TRADING_DAYS = 252


def load(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    frame["date"] = pd.to_datetime(frame["date"])
    if "return_observed" in frame.columns:
        # Unobserved days are written as zero residuals by construction; they
        # would otherwise depress every dispersion statistic below.
        frame = frame.loc[frame["return_observed"]]
    return frame[["date", "ticker", "residual"]]


def market_excess_return() -> pd.Series:
    """Equal-weight market excess return over the same daily universe."""

    import yaml

    from run import PROJECT as RUN_PROJECT, _load_daily_excess_returns

    config = yaml.safe_load(
        (RUN_PROJECT / "config" / "default.yml").read_text("utf-8")
    )
    daily = _load_daily_excess_returns(RUN_PROJECT.parent, config)
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.groupby("date")["return"].mean().sort_index()


def describe(
    name: str, frame: pd.DataFrame, market: pd.Series
) -> dict[str, object]:
    wide = frame.pivot_table(
        index="date", columns="ticker", values="residual", aggfunc="last"
    ).sort_index()
    aligned_market = market.reindex(wide.index)
    market_variance = float(aligned_market.var(ddof=1))
    betas = []
    for ticker in wide.columns:
        series = wide[ticker].dropna()
        if len(series) < 250 or market_variance <= 0:
            continue
        pair = pd.concat([series, aligned_market], axis=1, join="inner").dropna()
        if len(pair) < 250:
            continue
        betas.append(
            float(pair.iloc[:, 0].cov(pair.iloc[:, 1]) / pair.iloc[:, 1].var(ddof=1))
        )
    residual = frame["residual"].to_numpy(float)
    return {
        "name": name,
        "rows": int(len(frame)),
        "days": int(wide.shape[0]),
        "tickers": int(wide.shape[1]),
        "start": wide.index.min().date().isoformat(),
        "end": wide.index.max().date().isoformat(),
        "daily_std": float(np.std(residual, ddof=1)),
        "annualized_std": float(np.std(residual, ddof=1) * np.sqrt(TRADING_DAYS)),
        "max_abs": float(np.max(np.abs(residual))),
        "equal_weight_residual_index_annual_std": float(
            market.std(ddof=1) * np.sqrt(TRADING_DAYS)
        ),
        "mean_abs_market_beta": float(np.mean(np.abs(betas)))
        if betas
        else float("nan"),
        "median_abs_market_beta": float(np.median(np.abs(betas)))
        if betas
        else float("nan"),
        "tickers_with_beta": len(betas),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--residuals", nargs="+", type=Path, default=None)
    parser.add_argument("--output", default="ipca_residual_comparison.json")
    args = parser.parse_args()

    paths = [Path(p) for p in (args.residuals or DEFAULT_FILES)]
    market = market_excess_return()
    frames: dict[str, pd.DataFrame] = {}
    summaries: list[dict[str, object]] = []
    for path in paths:
        if not path.exists():
            print(f"skipping missing {path}", file=sys.stderr)
            continue
        frame = load(path)
        frames[path.stem] = frame
        summaries.append(describe(path.stem, frame, market))

    if not summaries:
        raise SystemExit("no residual panels were loaded")

    correlations: dict[str, float] = {}
    names = list(frames)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            merged = frames[left].merge(
                frames[right], on=["date", "ticker"], suffixes=("_l", "_r")
            )
            if merged.empty:
                continue
            correlations[f"{left} vs {right}"] = float(
                merged["residual_l"].corr(merged["residual_r"])
            )
            by_year = (
                merged.assign(year=merged["date"].dt.year)
                .groupby("year")
                .apply(
                    lambda g: float(g["residual_l"].corr(g["residual_r"])),
                    include_groups=False,
                )
            )
            correlations[f"{left} vs {right} [by year]"] = {
                int(year): round(value, 4) for year, value in by_year.items()
            }

    payload = {
        "classification": "Korean IPCA residual diagnostic",
        "trading_days_per_year": TRADING_DAYS,
        "panels": summaries,
        "overlapping_correlations": correlations,
    }
    destination = OUTPUT / "ipca" / args.output
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"{'panel':<44} {'days':>5} {'stocks':>7} {'ann.std':>9} "
        f"{'max|e|':>8} {'|beta|':>7}"
    )
    for row in summaries:
        print(
            f"{row['name']:<44} {row['days']:>5} {row['tickers']:>7} "
            f"{row['annualized_std']:>9.4f} {row['max_abs']:>8.3f} "
            f"{row['mean_abs_market_beta']:>7.3f}"
        )
    print("\ncross-panel correlation on the overlapping (date, ticker) grid:")
    for key, value in correlations.items():
        if isinstance(value, dict):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.4f}")
    print(f"\nwrote {destination}")


if __name__ == "__main__":
    main()
