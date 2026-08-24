"""Diagnose IPCA ALS convergence for reduced instrument sets and ridge Gamma.

The paper estimates Gamma on 46 characteristics over a 240-month rolling
window with no penalty.  The Korean panel has 139 months and only eight
characteristics reach 90% raw coverage, and the K=5 46-instrument fit diverges.
This script fits the same alternating-least-squares system that
``run.py estimate-ipca`` would fit, over the same annual windows, for a grid of
coverage thresholds, factor counts and ridge intensities, and reports whether
each specification converges.  It writes no residuals: its only purpose is to
find which specifications are numerically admissible.

Usage:

    uv run python guijarro-ordonez-2025-replication/scripts/ipca_reduced_grid.py
    uv run python .../ipca_reduced_grid.py --coverage 0.9 --factors 5 --ridge 0 0.01
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import warnings

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from guijarro_ordonez_replication.ipca import (  # noqa: E402
    ReducedCharacteristicIPCAWarning,
    RidgeIPCAWarning,
    _monthly_arrays,
    fit_ipca_als,
    prepare_ipca_monthly_panel,
    select_characteristics_by_coverage,
)

OUTPUT = PROJECT / "outputs" / "ipca"


def instrument_condition(characteristics: tuple[np.ndarray, ...]) -> float:
    """Condition number of the pooled instrument Gram sum_t Z_t' Z_t.

    This is the collinearity diagnostic that does not depend on the factor
    count: median-rank imputation makes sparsely observed accounting columns
    nearly identical, which is what makes the Gamma system ill-posed.
    """

    gram = sum(z.T @ z for z in characteristics)
    return float(np.linalg.cond(gram))


def evaluate(
    monthly: pd.DataFrame,
    dates: pd.DatetimeIndex,
    columns: tuple[str, ...],
    *,
    n_factors: int,
    gamma_ridge: float,
    initial_months: int,
    window_months: int,
    reestimate_every_months: int,
    max_iterations: int,
    tolerance: float,
) -> dict[str, object]:
    """Fit every annual window for one specification and summarize it."""

    fits: list[dict[str, object]] = []
    previous_gamma: np.ndarray | None = None
    started = time.perf_counter()
    for oos_idx in range(initial_months, len(dates), reestimate_every_months):
        train_dates = dates[oos_idx - window_months : oos_idx]
        returns, chars = _monthly_arrays(monthly, train_dates, columns)
        # Mirror the estimator: warm-start later windows and halve their budget.
        fit = fit_ipca_als(
            returns,
            chars,
            n_factors=n_factors,
            max_iterations=(
                max_iterations if previous_gamma is None else max_iterations // 2
            ),
            tolerance=tolerance,
            initial_gamma=previous_gamma,
            gamma_ridge=gamma_ridge,
        )
        previous_gamma = fit.gamma
        fits.append(
            {
                "train_start": train_dates[0].date().isoformat(),
                "train_end": train_dates[-1].date().isoformat(),
                "iterations": fit.iterations,
                "converged": bool(fit.converged),
                "final_delta": float(fit.final_delta),
                "gamma_max_abs": float(np.max(np.abs(fit.gamma))),
                "instrument_condition": instrument_condition(chars),
                "mean_stocks": float(np.mean([len(r) for r in returns])),
            }
        )
    elapsed = time.perf_counter() - started
    return {
        "n_characteristics": len(columns),
        "characteristics": list(columns),
        "n_factors": n_factors,
        "gamma_ridge": gamma_ridge,
        "windows": len(fits),
        "all_converged": all(f["converged"] for f in fits),
        "converged_windows": sum(1 for f in fits if f["converged"]),
        "worst_final_delta": max(f["final_delta"] for f in fits),
        "max_gamma_abs": max(f["gamma_max_abs"] for f in fits),
        "max_instrument_condition": max(f["instrument_condition"] for f in fits),
        "seconds": round(elapsed, 1),
        "fits": fits,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coverage",
        type=float,
        nargs="+",
        default=[0.90, 0.80, 0.0],
        help="raw-coverage thresholds; 0 keeps the paper's 46 instruments",
    )
    parser.add_argument("--factors", type=int, nargs="+", default=[1, 3, 5])
    parser.add_argument(
        "--ridge",
        type=float,
        nargs="+",
        default=[0.0, 0.001, 0.01, 0.1],
        help="dimensionless ridge intensities; 0 is the paper's estimator",
    )
    parser.add_argument("--initial-months", type=int, default=60)
    parser.add_argument("--window-months", type=int, default=60)
    parser.add_argument("--reestimate-every-months", type=int, default=12)
    parser.add_argument("--max-iterations", type=int, default=1500)
    parser.add_argument("--tolerance", type=float, default=1e-3)
    parser.add_argument("--output", default="reduced_characteristic_grid.json")
    parser.add_argument(
        "--panel-tag",
        default="",
        help="characteristic panel suffix, e.g. '_sepscope_common'",
    )
    parser.add_argument(
        "--coverage-basis",
        choices=("universe", "raw"),
        default="universe",
        help="judge coverage on the market-cap estimation universe or the raw panel",
    )
    args = parser.parse_args()

    monthly_path = (
        OUTPUT / f"monthly_characteristics_normalized{args.panel_tag}.parquet"
    )
    audit_path = OUTPUT / f"characteristic_audit{args.panel_tag}.json"
    if not monthly_path.exists() or not audit_path.exists():
        raise SystemExit("run build-ipca-characteristics first")
    audit = json.loads(audit_path.read_text("utf-8"))
    coverage_key = (
        "coverage_estimation_universe"
        if args.coverage_basis == "universe"
        else "coverage"
    )
    if coverage_key not in audit:
        raise SystemExit(f"{audit_path.name} has no '{coverage_key}' block")
    coverage = audit[coverage_key]
    panel = pd.read_parquet(monthly_path)
    monthly, dates = prepare_ipca_monthly_panel(panel)
    print(
        f"panel: {len(monthly):,} rows, {len(dates)} months, "
        f"{dates[0].date()}..{dates[-1].date()}",
        file=sys.stderr,
    )

    results: list[dict[str, object]] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ReducedCharacteristicIPCAWarning)
        warnings.simplefilter("ignore", RidgeIPCAWarning)
        for threshold in args.coverage:
            columns = select_characteristics_by_coverage(
                coverage, threshold=threshold
            )
            for n_factors in args.factors:
                if n_factors > len(columns):
                    continue
                for ridge in args.ridge:
                    record = evaluate(
                        monthly,
                        dates,
                        columns,
                        n_factors=n_factors,
                        gamma_ridge=ridge,
                        initial_months=args.initial_months,
                        window_months=args.window_months,
                        reestimate_every_months=args.reestimate_every_months,
                        max_iterations=args.max_iterations,
                        tolerance=args.tolerance,
                    )
                    record["coverage_threshold"] = threshold
                    results.append(record)
                    print(
                        f"cov>={threshold:<4} L={record['n_characteristics']:<3}"
                        f" K={n_factors} ridge={ridge:<6g}"
                        f" converged={record['converged_windows']}/{record['windows']}"
                        f" worst_delta={record['worst_final_delta']:.3g}"
                        f" cond={record['max_instrument_condition']:.3g}"
                        f" ({record['seconds']}s)",
                        file=sys.stderr,
                        flush=True,
                    )

    payload = {
        "classification": "Korean IPCA numerical-admissibility diagnostic",
        "panel_tag": args.panel_tag,
        "coverage_basis": args.coverage_basis,
        "purpose": (
            "identify which reduced-instrument and ridge specifications satisfy "
            "the public code's convergence gate; no residuals are written"
        ),
        "months_available": len(dates),
        "paper_window_months": 240,
        "initial_months": args.initial_months,
        "window_months": args.window_months,
        "reestimate_every_months": args.reestimate_every_months,
        "max_iterations": args.max_iterations,
        "tolerance": args.tolerance,
        "results": results,
    }
    destination = OUTPUT / args.output
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    header = "| coverage | L | K | ridge | converged | worst delta | cond(ZZ) |"
    print("\n" + header)
    print("|---|---:|---:|---:|---:|---:|---:|")
    for r in results:
        print(
            f"| >={r['coverage_threshold']:g} | {r['n_characteristics']} "
            f"| {r['n_factors']} | {r['gamma_ridge']:g} "
            f"| {r['converged_windows']}/{r['windows']} "
            f"| {r['worst_final_delta']:.3g} "
            f"| {r['max_instrument_condition']:.3g} |"
        )
    print(f"\nwrote {destination}")


if __name__ == "__main__":
    main()
