"""Command-line entry point for the DLSA replication project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))

from guijarro_ordonez_replication.registry import (  # noqa: E402
    load_registry,
    status_counts,
)
from guijarro_ordonez_replication.factors import (  # noqa: E402
    build_annual_memberships,
    build_daily_factors,
    build_momentum_membership,
    build_reversal_memberships,
    compare_bucket_returns,
    compare_return_columns,
    derive_lagged_annual_characteristics,
    load_kimchi_factor_data,
    load_statement_facts,
    prepare_daily_stock_panel,
)
from guijarro_ordonez_replication.exact_kimchi_factors import (  # noqa: E402
    build_exact_kimchi_factors,
    derive_accounting_signals,
    load_ecos_market_and_rf,
    load_market_snapshots,
    load_price_panel,
    load_statement_facts as load_exact_statement_facts,
)
from guijarro_ordonez_replication.residuals import (  # noqa: E402
    map_residual_to_asset_weights,
    project_residual_returns,
    residual_composition_matrix,
)


def command_status() -> None:
    registry = load_registry(PROJECT / "config" / "output-registry.yml")
    payload = {
        "paper": registry["paper"],
        "status_counts": dict(sorted(status_counts(registry).items())),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def command_demo_residuals() -> None:
    """Run the four-stock teaching example without external data."""

    loadings = np.array([[1.2], [0.8], [1.0], [1.0]])
    factor_weights = np.full((4, 1), 0.25)
    composition = residual_composition_matrix(loadings, factor_weights)
    returns = np.array([0.020, 0.008, 0.014, 0.006])
    residual_allocations = np.array([0.4, -0.2, 0.0, 0.6])
    payload = {
        "composition": composition.round(6).tolist(),
        "residual_returns": project_residual_returns(
            returns, composition
        ).round(6).tolist(),
        "asset_weights": map_residual_to_asset_weights(
            residual_allocations, composition
        ).round(6).tolist(),
    }
    print(json.dumps(payload, indent=2))


def command_build_factors_proxy(*, allow_non_pit_statements: bool) -> None:
    """Build the superseded broad-universe proxy for diagnostics only."""

    repository = PROJECT.parent
    config = yaml.safe_load((PROJECT / "config" / "default.yml").read_text("utf-8"))
    factor_config = config["factor_models"]["fama_french"]
    lag_months = int(factor_config["reporting_lag_months"])
    if not allow_non_pit_statements:
        raise SystemExit(
            "Accounting snapshots are not historical PIT data. Re-run with "
            "--allow-non-pit-statements to execute the labeled 3-month-lag sensitivity."
        )

    prices_path = repository / config["data"]["stock_daily"]
    statement_path = repository / config["data"]["statement_facts"]
    kimchi_path = repository / config["data"]["kimchi_factor_daily"]
    prices = pd.read_parquet(
        prices_path,
        columns=["date", "ticker", "return", "market_cap"],
    )
    daily = prepare_daily_stock_panel(prices)
    facts = load_statement_facts(statement_path)
    characteristics = derive_lagged_annual_characteristics(
        facts,
        reporting_lag_months=lag_months,
        allow_non_pit=True,
    )
    annual_memberships = build_annual_memberships(daily, characteristics)
    momentum_membership = build_momentum_membership(daily)
    reversal_memberships = build_reversal_memberships(daily)
    kimchi_returns, kimchi_buckets = load_kimchi_factor_data(kimchi_path)
    risk_free = kimchi_returns.set_index("date")["RF"]
    factors, bucket_returns = build_daily_factors(
        daily,
        annual_memberships,
        momentum_membership,
        risk_free=risk_free,
        reversal_memberships=reversal_memberships,
    )
    comparison_columns = ["RM", "RMRF", "SMB", "HML", "RMW", "CMA", "MOM", "RF"]
    aligned, comparison = compare_return_columns(
        factors,
        kimchi_returns,
        comparison_columns,
    )
    bucket_comparison = compare_bucket_returns(bucket_returns, kimchi_buckets)

    output = PROJECT / "outputs" / "factors"
    output.mkdir(parents=True, exist_ok=True)
    factors.to_csv(output / "constructed_daily_factors.csv", index=False)
    bucket_returns.to_csv(output / "constructed_2x3_bucket_returns.csv", index=False)
    aligned.to_csv(output / "kimchi_aligned_daily_returns.csv", index=False)
    comparison.to_csv(output / "kimchi_factor_comparison.csv", index=False)
    bucket_comparison.to_csv(output / "kimchi_bucket_comparison.csv", index=False)
    for factor, membership in annual_memberships.items():
        membership.to_csv(output / f"{factor.lower()}_annual_membership.csv", index=False)
    momentum_membership.to_csv(output / "mom_monthly_membership.csv", index=False)
    for factor, membership in reversal_memberships.items():
        membership.to_csv(
            output / f"{factor.lower()}_monthly_membership.csv", index=False
        )

    audit = {
        "classification": "non-PIT accounting sensitivity",
        "reporting_lag_months": lag_months,
        "accounting_snapshot_rule": "latest local dump revision per logical key",
        "risk_free_source": "Kimchi Factor RF; only RMRF depends on this benchmark input",
        "price_rows": len(daily),
        "price_tickers": int(daily["ticker"].nunique()),
        "price_start": daily["date"].min().date().isoformat(),
        "price_end": daily["date"].max().date().isoformat(),
        "statement_fact_rows_selected": len(facts),
        "characteristic_rows": len(characteristics),
        "annual_memberships": {
            factor: {
                "rows": len(membership),
                "tickers": int(membership["ticker"].nunique()),
                "formation_year_start": int(membership["formation_year"].min()),
                "formation_year_end": int(membership["formation_year"].max()),
            }
            for factor, membership in annual_memberships.items()
        },
        "future_accounting_membership_rows": int(
            sum(
                membership["available_date"].gt(membership["formation_date"]).sum()
                for membership in annual_memberships.values()
            )
        ),
        "momentum_membership_rows": len(momentum_membership),
        "reversal_membership_rows": {
            factor: len(membership)
            for factor, membership in reversal_memberships.items()
        },
        "constructed_factor_rows": len(factors),
        "factor_duplicate_dates": int(factors["date"].duplicated().sum()),
        "bucket_duplicate_keys": int(
            bucket_returns.duplicated(["date", "factor", "bucket"]).sum()
        ),
        "factor_coverage": {
            factor: {
                "observations": int(factors[factor].notna().sum()),
                "start": factors.loc[factors[factor].notna(), "date"]
                .min()
                .date()
                .isoformat(),
                "end": factors.loc[factors[factor].notna(), "date"]
                .max()
                .date()
                .isoformat(),
            }
            for factor in ["RM", "SMB", "HML", "RMW", "CMA", "MOM", "LTR", "STR"]
        },
    }
    (output / "factor_construction_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    payload = {
        "output": str(output),
        "classification": audit["classification"],
        "comparison": comparison.to_dict(orient="records"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def command_build_kimchi_factors(*, allow_non_pit_statements: bool) -> None:
    """Build the documented Kimchi factors from 2018 onward."""

    if not allow_non_pit_statements:
        raise SystemExit(
            "The local statements are latest-revision snapshots without announcement "
            "timestamps. Re-run with --allow-non-pit-statements to execute the "
            "documented fixed-3-month-lag sensitivity."
        )
    repository = PROJECT.parent
    config = yaml.safe_load((PROJECT / "config" / "default.yml").read_text("utf-8"))
    data = config["data"]
    prices = load_price_panel(repository / data["stock_daily"], start="2017-01-01")
    snapshots = load_market_snapshots(repository / data["security_master_pit"])
    facts = load_exact_statement_facts(repository / data["statement_facts"])
    accounting = derive_accounting_signals(facts, reporting_lag_months=3)
    kospi, rf_yield = load_ecos_market_and_rf(
        repository / data["kospi_index_ecos_raw"],
        repository / data["risk_free_ecos_raw"],
    )
    result = build_exact_kimchi_factors(
        prices=prices,
        snapshots=snapshots,
        accounting=accounting,
        kospi=kospi,
        rf_yield=rf_yield,
        start="2018-01-01",
    )

    kimchi_returns, kimchi_buckets = load_kimchi_factor_data(
        repository / data["kimchi_factor_daily"]
    )
    daily_vw = result.daily_returns.loc[
        result.daily_returns["weight"].eq("vw")
    ].copy()
    comparison_columns = ["RM", "RMRF", "SMB", "HML", "RMW", "CMA", "MOM", "RF"]
    aligned, comparison = compare_return_columns(
        daily_vw,
        kimchi_returns,
        comparison_columns,
    )
    bucket_vw = result.daily_2x3_buckets.loc[
        result.daily_2x3_buckets["weight"].eq("vw"),
        ["date", "factor", "bucket", "ret", "n_stocks"],
    ]
    bucket_comparison = compare_bucket_returns(bucket_vw, kimchi_buckets)

    output = PROJECT / "outputs" / "kimchi-exact"
    output.mkdir(parents=True, exist_ok=True)
    daily_market_rf = result.daily_returns.loc[
        result.daily_returns["weight"].eq("vw"), ["date", "RM", "RF", "RMRF"]
    ]
    monthly_market_rf = result.monthly_returns.loc[
        result.monthly_returns["weight"].eq("vw"), ["date", "RM", "RF", "RMRF"]
    ]
    artifacts = {
        "daily_factor_returns.csv": result.daily_returns,
        "monthly_factor_returns.csv": result.monthly_returns,
        "daily_market_rf.csv": daily_market_rf,
        "monthly_market_rf.csv": monthly_market_rf,
        "daily_2x3_bucket_returns.csv": result.daily_2x3_buckets,
        "monthly_2x3_bucket_returns.csv": result.monthly_2x3_buckets,
        "daily_quintile_bucket_returns.csv": result.daily_quintile_buckets,
        "monthly_quintile_bucket_returns.csv": result.monthly_quintile_buckets,
        "annual_memberships.csv": result.annual_memberships,
        "momentum_memberships.csv": result.momentum_memberships,
        "accounting_signals.csv": result.accounting_signals,
        "kimchi_aligned_daily_returns.csv": aligned,
        "kimchi_factor_comparison.csv": comparison,
        "kimchi_bucket_comparison.csv": bucket_comparison,
    }
    for filename, frame in artifacts.items():
        frame.to_csv(output / filename, index=False, encoding="utf-8-sig")

    audit = dict(result.audit)
    audit["benchmark"] = {
        "source": str(repository / data["kimchi_factor_daily"]),
        "factor_comparison": comparison.to_dict(orient="records"),
        "bucket_comparison_rows": len(bucket_comparison),
    }
    (output / "factor_construction_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "classification": audit["classification"],
                "comparison": comparison.to_dict(orient="records"),
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "status",
            "demo-residuals",
            "build-factors-proxy",
            "build-kimchi-factors",
        ),
    )
    parser.add_argument(
        "--allow-non-pit-statements",
        action="store_true",
        help="allow the labeled fixed-lag accounting sensitivity",
    )
    args = parser.parse_args()
    if args.command == "status":
        command_status()
    elif args.command == "demo-residuals":
        command_demo_residuals()
    elif args.command == "build-factors-proxy":
        command_build_factors_proxy(
            allow_non_pit_statements=args.allow_non_pit_statements
        )
    else:
        command_build_kimchi_factors(
            allow_non_pit_statements=args.allow_non_pit_statements
        )


if __name__ == "__main__":
    main()
