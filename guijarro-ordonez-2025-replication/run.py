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
from guijarro_ordonez_replication.kimchi_methodology import (  # noqa: E402
    annual_yield_percent_to_period_return,
)
from guijarro_ordonez_replication.residuals import (  # noqa: E402
    map_residual_to_asset_weights,
    project_residual_returns,
    residual_composition_matrix,
)
from guijarro_ordonez_replication.characteristics import (  # noqa: E402
    build_monthly_characteristics,
    load_ipca_annual_accounting,
    load_ipca_daily_returns,
    load_ipca_price_panel,
)
from guijarro_ordonez_replication.ipca import (  # noqa: E402
    estimate_daily_ipca_residuals,
)
from guijarro_ordonez_replication.pca import (  # noqa: E402
    estimate_daily_pca_residuals,
)
from guijarro_ordonez_replication.trading import (  # noqa: E402
    SimulationConfig,
    load_pca_residual_panel,
    simulate_rolling_strategy,
)
from guijarro_ordonez_replication.results import (  # noqa: E402
    build_korean_pca5_report,
)
from guijarro_ordonez_replication.spec_outputs import (  # noqa: E402
    build_spec_outputs,
)
from guijarro_ordonez_replication.fama_french_residuals import (  # noqa: E402
    estimate_daily_fama_french_residuals,
)
from guijarro_ordonez_replication.trading import (  # noqa: E402
    load_fama_french_residual_panel,
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


def _load_daily_excess_returns(
    repository: Path,
    config: dict[str, object],
) -> pd.DataFrame:
    """Load price returns and subtract the backward-matched ECOS daily RF."""

    data = config["data"]
    if not isinstance(data, dict):
        raise TypeError("config data section must be a mapping")
    prices = load_ipca_daily_returns(repository / str(data["stock_daily"]))
    _, rf_yield = load_ecos_market_and_rf(
        repository / str(data["kospi_index_ecos_raw"]),
        repository / str(data["risk_free_ecos_raw"]),
    )
    trading_dates = pd.DataFrame({"date": sorted(prices["date"].unique())})
    daily_rf = pd.merge_asof(
        trading_dates,
        rf_yield.sort_values("date"),
        on="date",
        direction="backward",
        tolerance=pd.Timedelta(days=7),
    )
    daily_rf["RF"] = annual_yield_percent_to_period_return(
        daily_rf["annual_rf_percent"], periods_per_year=252
    )
    if daily_rf["RF"].isna().any():
        first_missing = daily_rf.loc[daily_rf["RF"].isna(), "date"].iloc[0]
        raise ValueError(f"ECOS daily RF is missing on {first_missing.date()}")
    prices = prices.merge(
        daily_rf[["date", "RF"]], on="date", how="left", validate="many_to_one"
    )
    prices["return"] = prices["return"] - prices["RF"]
    return prices.drop(columns="RF")


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


def command_build_ipca_characteristics(
    *,
    allow_non_pit_statements: bool,
    impute_missing_characteristics: bool,
) -> None:
    """Build the paper's 46-characteristic panel from Korean sources."""

    if not allow_non_pit_statements:
        raise SystemExit(
            "The IPCA accounting inputs are latest-revision snapshots. Re-run "
            "with --allow-non-pit-statements to execute the labeled fixed-3-month-lag "
            "sensitivity."
        )
    repository = PROJECT.parent
    config = yaml.safe_load((PROJECT / "config" / "default.yml").read_text("utf-8"))
    data = config["data"]
    prices = load_ipca_price_panel(repository / data["stock_daily"])
    accounting = load_ipca_annual_accounting(
        repository / data["statement_facts"],
        repository / data["annual_share_counts"],
        repository / data["dividend_items"],
        reporting_lag_months=3,
    )
    result = build_monthly_characteristics(
        prices,
        accounting,
        impute_missing=impute_missing_characteristics,
    )
    output = PROJECT / "outputs" / "ipca"
    output.mkdir(parents=True, exist_ok=True)
    result.raw.to_parquet(output / "monthly_characteristics_raw.parquet", index=False)
    result.normalized.to_parquet(
        output / "monthly_characteristics_normalized.parquet", index=False
    )
    (output / "characteristic_audit.json").write_text(
        json.dumps(result.audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {"output": str(output), **result.audit},
            ensure_ascii=False,
            indent=2,
        )
    )


def command_estimate_ipca(
    *,
    factors: int,
    initial_months: int,
    window_months: int,
    allow_short_history: bool,
    max_iterations: int,
    tolerance: float,
) -> None:
    """Estimate daily IPCA residuals from the generated monthly panel."""

    repository = PROJECT.parent
    config = yaml.safe_load((PROJECT / "config" / "default.yml").read_text("utf-8"))
    output = PROJECT / "outputs" / "ipca"
    monthly_path = output / "monthly_characteristics_normalized.parquet"
    if not monthly_path.exists():
        raise SystemExit(
            "Build monthly characteristics first with build-ipca-characteristics."
        )
    monthly = pd.read_parquet(monthly_path)
    prices = _load_daily_excess_returns(repository, config)

    def report_progress(event: dict[str, object]) -> None:
        print(json.dumps(event, ensure_ascii=False), file=sys.stderr, flush=True)

    result = estimate_daily_ipca_residuals(
        monthly,
        prices,
        n_factors=factors,
        initial_months=initial_months,
        window_months=window_months,
        reestimate_every_months=12,
        allow_short_history=allow_short_history,
        max_iterations=max_iterations,
        tolerance=tolerance,
        progress=report_progress,
        daily_return_definition=(
            "cash-dividend-excluding adjusted price return minus ECOS daily RF"
        ),
    )
    tag = f"k{factors}_i{initial_months}_w{window_months}"
    result.residuals.to_parquet(output / f"daily_residuals_{tag}.parquet", index=False)
    result.loadings.to_parquet(output / f"monthly_loadings_{tag}.parquet", index=False)
    (output / f"ipca_audit_{tag}.json").write_text(
        json.dumps(result.audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result.audit, ensure_ascii=False, indent=2))


def command_estimate_pca(
    *,
    factors: int,
    initial_oos_date: str,
    covariance_window_days: int,
    loading_window_days: int,
    max_oos_days: int | None,
) -> None:
    """Estimate rolling daily PCA residuals using the public-code equations."""

    repository = PROJECT.parent
    config = yaml.safe_load((PROJECT / "config" / "default.yml").read_text("utf-8"))
    output = PROJECT / "outputs" / "pca"
    monthly_path = (
        PROJECT / "outputs" / "ipca" / "monthly_characteristics_raw.parquet"
    )
    if not monthly_path.exists():
        raise SystemExit(
            "Build raw monthly characteristics first with build-ipca-characteristics."
        )
    monthly = pd.read_parquet(monthly_path)
    daily = _load_daily_excess_returns(repository, config)

    def report_progress(event: dict[str, object]) -> None:
        print(json.dumps(event, ensure_ascii=False), file=sys.stderr, flush=True)

    result = estimate_daily_pca_residuals(
        monthly,
        daily,
        n_factors=factors,
        initial_oos_date=initial_oos_date,
        covariance_window_days=covariance_window_days,
        loading_window_days=loading_window_days,
        max_oos_days=max_oos_days,
        progress=report_progress,
    )
    output.mkdir(parents=True, exist_ok=True)
    date_tag = pd.Timestamp(initial_oos_date).strftime("%Y%m%d")
    tag = (
        f"k{factors}_{date_tag}_c{covariance_window_days}_l{loading_window_days}"
    )
    if max_oos_days is not None:
        tag += f"_d{max_oos_days}"
    result.residuals.to_parquet(output / f"daily_residuals_{tag}.parquet", index=False)
    result.loadings.to_parquet(output / f"daily_low_rank_loadings_{tag}.parquet", index=False)
    (output / f"pca_audit_{tag}.json").write_text(
        json.dumps(result.audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result.audit, ensure_ascii=False, indent=2))


def command_simulate_pca(
    *,
    model_name: str,
    objective: str,
    lookback_days: int,
    epochs: int,
    transaction_cost: float,
    short_holding_cost: float,
    rolling_retrain: bool,
) -> None:
    """Run the paper's rolling trading policy on the Korean K=5 PCA branch."""

    pca_output = PROJECT / "outputs" / "pca"
    residual_path = (
        pca_output / "daily_residuals_k5_20200102_c252_l60.parquet"
    )
    loading_path = (
        pca_output / "daily_low_rank_loadings_k5_20200102_c252_l60.parquet"
    )
    if not residual_path.exists() or not loading_path.exists():
        raise SystemExit(
            "Build the full K=5 PCA branch first with estimate-pca "
            "--pca-initial-oos-date 2020-01-02."
        )
    cost_tag = (
        f"tc{transaction_cost:g}_hc{short_holding_cost:g}"
        if transaction_cost or short_holding_cost
        else "no-cost"
    )
    tag = (
        f"pca5_{model_name}_{objective}_lb{lookback_days}_e{epochs}_"
        f"{'rolling' if rolling_retrain else 'constant'}_{cost_tag}"
    )
    output = PROJECT / "outputs" / "strategies" / tag
    output.mkdir(parents=True, exist_ok=True)
    panel = load_pca_residual_panel(residual_path, loading_path)
    simulation_config = SimulationConfig(
        model_name=model_name,
        objective=objective,
        lookback_days=lookback_days,
        epochs=epochs,
        transaction_cost=transaction_cost,
        short_holding_cost=short_holding_cost,
        rolling_retrain=rolling_retrain,
        checkpoint_directory=output / "checkpoints",
    )

    def report_progress(event: dict[str, object]) -> None:
        print(json.dumps(event, ensure_ascii=False), file=sys.stderr, flush=True)

    result = simulate_rolling_strategy(
        panel,
        simulation_config,
        progress=report_progress,
    )
    result.daily.to_csv(output / "daily_performance.csv", index=False)
    result.weights.to_parquet(output / "daily_asset_weights.parquet")
    (output / "simulation_audit.json").write_text(
        json.dumps(result.audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"output": str(output), **result.audit}, ensure_ascii=False, indent=2))


def command_estimate_fama_french(
    *,
    factors: int,
    initial_oos_date: str,
    loading_window_days: int,
) -> None:
    """Estimate Korean rolling Fama-French residuals and synthetic factor legs."""

    repository = PROJECT.parent
    config = yaml.safe_load((PROJECT / "config" / "default.yml").read_text("utf-8"))
    monthly_path = PROJECT / "outputs" / "ipca" / "monthly_characteristics_raw.parquet"
    if not monthly_path.exists():
        raise SystemExit("Build raw monthly characteristics first.")
    result = estimate_daily_fama_french_residuals(
        pd.read_parquet(monthly_path),
        _load_daily_excess_returns(repository, config),
        pd.read_csv(PROJECT / "outputs" / "kimchi-exact" / "daily_factor_returns.csv"),
        n_factors=factors,
        initial_oos_date=initial_oos_date,
        loading_window_days=loading_window_days,
        progress=lambda event: print(
            json.dumps(event, ensure_ascii=False), file=sys.stderr, flush=True
        ),
    )
    output = PROJECT / "outputs" / "fama-french"
    output.mkdir(parents=True, exist_ok=True)
    date_tag = pd.Timestamp(initial_oos_date).strftime("%Y%m%d")
    tag = f"ff{factors}_{date_tag}_l{loading_window_days}"
    result.residuals.to_parquet(output / f"daily_residuals_{tag}.parquet", index=False)
    result.factor_legs.to_parquet(output / f"daily_factor_legs_{tag}.parquet", index=False)
    (output / f"fama_french_audit_{tag}.json").write_text(
        json.dumps(result.audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"output": str(output), **result.audit}, ensure_ascii=False, indent=2))


def command_simulate_fama_french(
    *,
    factors: int,
    model_name: str,
    objective: str,
    lookback_days: int,
    epochs: int,
    transaction_cost: float,
    short_holding_cost: float,
    rolling_retrain: bool,
) -> None:
    """Run a paper policy on Korean rolling Fama-French residuals."""

    residual_root = PROJECT / "outputs" / "fama-french"
    tag = f"ff{factors}_20200102_l60"
    residual_path = residual_root / f"daily_residuals_{tag}.parquet"
    leg_path = residual_root / f"daily_factor_legs_{tag}.parquet"
    if not residual_path.exists() or not leg_path.exists():
        raise SystemExit(f"Build {tag} residuals first with estimate-fama-french.")
    cost_tag = (
        f"tc{transaction_cost:g}_hc{short_holding_cost:g}"
        if transaction_cost or short_holding_cost
        else "no-cost"
    )
    run_tag = (
        f"ff{factors}_{model_name}_{objective}_lb{lookback_days}_e{epochs}_"
        f"{'rolling' if rolling_retrain else 'constant'}_{cost_tag}"
    )
    output = PROJECT / "outputs" / "strategies" / run_tag
    output.mkdir(parents=True, exist_ok=True)
    simulation_config = SimulationConfig(
        model_name=model_name,
        objective=objective,
        lookback_days=lookback_days,
        epochs=epochs,
        transaction_cost=transaction_cost,
        short_holding_cost=short_holding_cost,
        rolling_retrain=rolling_retrain,
        checkpoint_directory=output / "checkpoints",
    )
    result = simulate_rolling_strategy(
        load_fama_french_residual_panel(residual_path, leg_path),
        simulation_config,
        progress=lambda event: print(
            json.dumps(event, ensure_ascii=False), file=sys.stderr, flush=True
        ),
    )
    result.daily.to_csv(output / "daily_performance.csv", index=False)
    result.weights.to_parquet(output / "daily_asset_weights.parquet")
    audit = {**result.audit, "factor_model": f"Korean FF{factors}"}
    (output / "simulation_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"output": str(output), **audit}, ensure_ascii=False, indent=2))


def command_report_pca() -> None:
    """Build core Korean PCA5 tables and figures from completed exact-policy runs."""

    strategy_root = PROJECT / "outputs" / "strategies"
    directories = [
        strategy_root / "pca5_ou_threshold_sharpe_lb30_e100_rolling_no-cost",
        strategy_root / "pca5_fourier_ffn_sharpe_lb30_e100_rolling_no-cost",
        strategy_root / "pca5_cnn_transformer_sharpe_lb30_e100_rolling_no-cost",
    ]
    available = [
        directory
        for directory in directories
        if (directory / "simulation_audit.json").exists()
    ]
    if not available:
        raise SystemExit("Run at least one full-contract PCA5 strategy first.")
    audit = build_korean_pca5_report(
        available,
        PROJECT / "outputs" / "kimchi-exact" / "daily_factor_returns.csv",
        PROJECT / "outputs" / "paper-korean-pca5",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


def command_build_spec_outputs() -> None:
    """Generate the paper outputs that depend only on the stated model spec."""

    audit = build_spec_outputs(PROJECT / "outputs" / "paper-spec")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "status",
            "demo-residuals",
            "build-factors-proxy",
            "build-kimchi-factors",
            "build-ipca-characteristics",
            "estimate-ipca",
            "estimate-pca",
            "simulate-pca",
            "report-pca",
            "build-spec-outputs",
            "estimate-fama-french",
            "simulate-fama-french",
        ),
    )
    parser.add_argument(
        "--allow-non-pit-statements",
        action="store_true",
        help="allow the labeled fixed-lag accounting sensitivity",
    )
    parser.add_argument(
        "--impute-missing-characteristics",
        action="store_true",
        help="fill missing cross-sectional ranks with the monthly median rank 0",
    )
    parser.add_argument("--ipca-factors", type=int, default=5)
    parser.add_argument("--ipca-initial-months", type=int, default=420)
    parser.add_argument("--ipca-window-months", type=int, default=240)
    parser.add_argument("--ipca-max-iterations", type=int, default=1500)
    parser.add_argument("--ipca-tolerance", type=float, default=1e-3)
    parser.add_argument("--pca-factors", type=int, default=5)
    parser.add_argument("--pca-initial-oos-date", default="2018-01-02")
    parser.add_argument("--pca-covariance-window-days", type=int, default=252)
    parser.add_argument("--pca-loading-window-days", type=int, default=60)
    parser.add_argument("--pca-max-oos-days", type=int)
    parser.add_argument("--ff-factors", choices=(1, 3, 5, 8), type=int, default=5)
    parser.add_argument("--ff-initial-oos-date", default="2020-01-02")
    parser.add_argument("--ff-loading-window-days", type=int, default=60)
    parser.add_argument(
        "--simulation-model",
        choices=("cnn_transformer", "fourier_ffn", "ou_threshold"),
        default="cnn_transformer",
    )
    parser.add_argument(
        "--simulation-objective", choices=("sharpe", "meanvar"), default="sharpe"
    )
    parser.add_argument("--simulation-lookback-days", type=int, default=30)
    parser.add_argument("--simulation-epochs", type=int, default=100)
    parser.add_argument("--simulation-transaction-cost", type=float, default=0.0)
    parser.add_argument("--simulation-short-holding-cost", type=float, default=0.0)
    parser.add_argument(
        "--simulation-constant-model",
        action="store_true",
        help="train only the first subperiod instead of the paper's rolling retraining",
    )
    parser.add_argument(
        "--allow-short-history-ipca",
        action="store_true",
        help="allow a labeled IPCA window shorter than the paper's 240 months",
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
    elif args.command == "build-kimchi-factors":
        command_build_kimchi_factors(
            allow_non_pit_statements=args.allow_non_pit_statements
        )
    elif args.command == "build-ipca-characteristics":
        command_build_ipca_characteristics(
            allow_non_pit_statements=args.allow_non_pit_statements,
            impute_missing_characteristics=args.impute_missing_characteristics,
        )
    elif args.command == "estimate-ipca":
        command_estimate_ipca(
            factors=args.ipca_factors,
            initial_months=args.ipca_initial_months,
            window_months=args.ipca_window_months,
            allow_short_history=args.allow_short_history_ipca,
            max_iterations=args.ipca_max_iterations,
            tolerance=args.ipca_tolerance,
        )
    elif args.command == "estimate-pca":
        command_estimate_pca(
            factors=args.pca_factors,
            initial_oos_date=args.pca_initial_oos_date,
            covariance_window_days=args.pca_covariance_window_days,
            loading_window_days=args.pca_loading_window_days,
            max_oos_days=args.pca_max_oos_days,
        )
    elif args.command == "simulate-pca":
        command_simulate_pca(
            model_name=args.simulation_model,
            objective=args.simulation_objective,
            lookback_days=args.simulation_lookback_days,
            epochs=args.simulation_epochs,
            transaction_cost=args.simulation_transaction_cost,
            short_holding_cost=args.simulation_short_holding_cost,
            rolling_retrain=not args.simulation_constant_model,
        )
    elif args.command == "estimate-fama-french":
        command_estimate_fama_french(
            factors=args.ff_factors,
            initial_oos_date=args.ff_initial_oos_date,
            loading_window_days=args.ff_loading_window_days,
        )
    elif args.command == "simulate-fama-french":
        command_simulate_fama_french(
            factors=args.ff_factors,
            model_name=args.simulation_model,
            objective=args.simulation_objective,
            lookback_days=args.simulation_lookback_days,
            epochs=args.simulation_epochs,
            transaction_cost=args.simulation_transaction_cost,
            short_holding_cost=args.simulation_short_holding_cost,
            rolling_retrain=not args.simulation_constant_model,
        )
    elif args.command == "report-pca":
        command_report_pca()
    else:
        command_build_spec_outputs()


if __name__ == "__main__":
    main()
