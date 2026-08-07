"""Validate ECOS raw responses and build Kaniel monthly research inputs.

Run from the repository root:
    uv run python scripts/kaist_pilot/build_kaniel_ecos_inputs.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_RAW = Path("data/kaist_pilot/canonical/kaniel_2023/ecos/raw")
DEFAULT_OUTPUT = Path("data/kaist_pilot/canonical/kaniel_2023/ecos/derived")
DEFAULT_MANIFEST = Path(
    "data/kaist_pilot/metadata/manifests/113_kaniel_ecos_inputs_20260807.json"
)
SENTIMENT_COMPONENT_COLUMNS = (
    "kospi_turnover_pct",
    "kosdaq_turnover_pct",
    "individual_buy_sell_imbalance",
    "investor_deposits_log_change",
    "margin_loan_balance_log_change",
)
SENTIMENT_ANCHOR_COLUMNS = (
    "kospi_turnover_pct",
    "kosdaq_turnover_pct",
    "margin_loan_balance_log_change",
)
SENTIMENT_CALIBRATION_START = pd.Timestamp("2005-01-31")
SENTIMENT_CALIBRATION_END = pd.Timestamp("2014-12-31")
SENTIMENT_APPLICATION_SOURCE_START = pd.Timestamp("2014-12-31")


@dataclass(frozen=True)
class SeriesContract:
    filename: str
    stat_code: str
    item_codes: tuple[str, ...]
    unit: str
    start: str
    end: str


CONTRACTS = {
    "rf_msb_91d": SeriesContract(
        "rf_msb_91d.json", "721Y001", ("6010300",), "연%", "200609", "202607"
    ),
    "rf_cd_91d": SeriesContract(
        "rf_cd_91d.json", "721Y001", ("2010000",), "연%", "199103", "202607"
    ),
    "esi_original": SeriesContract(
        "esi_original.json", "513Y001", ("E1000",), "", "200301", "202607"
    ),
    "esi_cyclical": SeriesContract(
        "esi_cyclical.json", "513Y001", ("E2000",), "", "200301", "202607"
    ),
    "ccsi": SeriesContract(
        "ccsi.json", "511Y002", ("FME", "99988"), "", "200807", "202607"
    ),
    "investor_deposits": SeriesContract(
        "investor_deposits.json", "901Y056", ("S23A",), "원", "199806", "202607"
    ),
    "margin_loan_balance": SeriesContract(
        "margin_loan_balance.json", "901Y056", ("S23E",), "원", "199806", "202607"
    ),
    "kospi_turnover": SeriesContract(
        "kospi_turnover.json", "901Y014", ("1090000",), "%", "200501", "202606"
    ),
    "kosdaq_turnover": SeriesContract(
        "kosdaq_turnover.json", "901Y014", ("2110000",), "%", "200401", "202606"
    ),
    "individual_buy_value": SeriesContract(
        "individual_buy_value.json",
        "901Y055",
        ("S22BB", "VA"),
        "백만원",
        "200401",
        "202606",
    ),
    "individual_sell_value": SeriesContract(
        "individual_sell_value.json",
        "901Y055",
        ("S22AB", "VA"),
        "백만원",
        "200401",
        "202606",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _row_codes(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(row.get(f"ITEM_CODE{position}", ""))
        for position in range(1, 5)
        if row.get(f"ITEM_CODE{position}")
    )


def load_series(raw_dir: Path, contract: SeriesContract) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = raw_dir / contract.filename
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("service") != "StatisticSearch":
        raise ValueError(f"{path}: unexpected service {payload.get('service')!r}")
    request = str(payload.get("request", ""))
    if "{key}" not in request:
        raise ValueError(f"{path}: request provenance is not redacted")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: no observations")
    if payload.get("returned_count") != len(rows):
        raise ValueError(f"{path}: returned_count mismatch")
    if payload.get("list_total_count") != len(rows):
        raise ValueError(f"{path}: row window did not retrieve the complete series")

    times: list[str] = []
    values: list[float] = []
    item_names: set[tuple[str, ...]] = set()
    for row in rows:
        if str(row.get("STAT_CODE")) != contract.stat_code:
            raise ValueError(f"{path}: unexpected STAT_CODE")
        if _row_codes(row) != contract.item_codes:
            raise ValueError(f"{path}: unexpected item-code tuple {_row_codes(row)}")
        if str(row.get("UNIT_NAME") or "") != contract.unit:
            raise ValueError(f"{path}: unexpected unit {row.get('UNIT_NAME')!r}")
        time = str(row.get("TIME", ""))
        if len(time) != 6 or not time.isdigit():
            raise ValueError(f"{path}: invalid monthly TIME {time!r}")
        try:
            value = float(str(row.get("DATA_VALUE", "")).replace(",", ""))
        except ValueError as exc:
            raise ValueError(f"{path}: nonnumeric value at {time}") from exc
        times.append(time)
        values.append(value)
        item_names.add(
            tuple(
                str(row.get(f"ITEM_NAME{position}", ""))
                for position in range(1, len(contract.item_codes) + 1)
            )
        )

    expected_times = [
        period.strftime("%Y%m")
        for period in pd.period_range(contract.start, contract.end, freq="M")
    ]
    if times != expected_times:
        raise ValueError(f"{path}: missing, duplicate, or unsorted months")
    frame = pd.DataFrame(
        {
            "month": pd.PeriodIndex(times, freq="M").to_timestamp("M"),
            "value": values,
        }
    )
    metadata = {
        "path": str(path),
        "sha256": sha256(path),
        "request": request,
        "stat_code": contract.stat_code,
        "item_codes": list(contract.item_codes),
        "item_names": [list(names) for names in sorted(item_names)],
        "unit": contract.unit,
        "start": times[0],
        "end": times[-1],
        "row_count": len(frame),
    }
    return frame, metadata


def annual_yield_percent_to_monthly_return(values: pd.Series) -> pd.Series:
    if values.lt(-100).any():
        raise ValueError("annual yield below -100% cannot be compounded")
    return (1.0 + values / 100.0) ** (1.0 / 12.0) - 1.0


def _write_csv(frame: pd.DataFrame, path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", encoding="utf-8")
    return {
        "path": str(path),
        "sha256": sha256(path),
        "row_count": len(frame),
        "start": frame["month"].min().strftime("%Y-%m-%d"),
        "end": frame["month"].max().strftime("%Y-%m-%d"),
        "columns": list(frame.columns),
    }


def build_sentiment_proxy(
    components: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build a fixed-calibration, one-month-lagged ECOS market-sentiment proxy."""

    required = {"month", *SENTIMENT_COMPONENT_COLUMNS}
    missing = sorted(required.difference(components.columns))
    if missing:
        raise ValueError(f"sentiment components are missing columns: {missing}")
    clean = components.loc[:, ["month", *SENTIMENT_COMPONENT_COLUMNS]].copy()
    clean["month"] = pd.to_datetime(clean["month"], errors="raise")
    if clean["month"].duplicated().any():
        raise ValueError("sentiment components contain duplicate months")

    calibration = clean.loc[
        clean["month"].between(
            SENTIMENT_CALIBRATION_START,
            SENTIMENT_CALIBRATION_END,
        )
    ].dropna()
    expected_months = pd.date_range(
        SENTIMENT_CALIBRATION_START,
        SENTIMENT_CALIBRATION_END,
        freq="ME",
    )
    if not calibration["month"].reset_index(drop=True).equals(
        pd.Series(expected_months, name="month")
    ):
        raise ValueError("sentiment calibration window is incomplete or unsorted")

    means = calibration.loc[:, SENTIMENT_COMPONENT_COLUMNS].mean()
    scales = calibration.loc[:, SENTIMENT_COMPONENT_COLUMNS].std(ddof=0)
    if scales.le(0).any():
        raise ValueError("sentiment calibration contains a constant component")
    standardized = (calibration.loc[:, SENTIMENT_COMPONENT_COLUMNS] - means) / scales
    _, singular_values, right_vectors = np.linalg.svd(
        standardized.to_numpy(dtype=float),
        full_matrices=False,
    )
    loadings = right_vectors[0]
    calibration_scores = standardized.to_numpy(dtype=float) @ loadings
    anchor = standardized.loc[:, SENTIMENT_ANCHOR_COLUMNS].mean(axis=1)
    anchor_correlation = float(np.corrcoef(calibration_scores, anchor)[0, 1])
    if not np.isfinite(anchor_correlation):
        raise ValueError("sentiment PCA orientation anchor is undefined")
    if anchor_correlation < 0:
        loadings = -loadings
        calibration_scores = -calibration_scores
        anchor_correlation = -anchor_correlation
    score_scale = float(np.std(calibration_scores, ddof=0))
    if not np.isfinite(score_scale) or score_scale <= 0:
        raise ValueError("sentiment PCA score scale is invalid")

    application = clean.loc[
        clean["month"].ge(SENTIMENT_APPLICATION_SOURCE_START)
    ].dropna()
    application_standardized = (
        application.loc[:, SENTIMENT_COMPONENT_COLUMNS] - means
    ) / scales
    proxy = pd.DataFrame(
        {
            "month": application["month"] + pd.offsets.MonthEnd(1),
            "sentiment": (
                application_standardized.to_numpy(dtype=float) @ loadings
            )
            / score_scale,
        }
    )
    if proxy["month"].duplicated().any() or proxy["sentiment"].isna().any():
        raise ValueError("sentiment proxy output is not a complete monthly series")
    expected_proxy_months = pd.date_range(
        proxy["month"].min(), proxy["month"].max(), freq="ME"
    )
    if not proxy["month"].reset_index(drop=True).equals(
        pd.Series(expected_proxy_months, name="month")
    ):
        raise ValueError("sentiment proxy has missing or unsorted months")

    metadata = {
        "kind": "ecos_only_fixed_calibration_pca_proxy",
        "exact_baker_wurgler": False,
        "component_columns": list(SENTIMENT_COMPONENT_COLUMNS),
        "calibration_start": SENTIMENT_CALIBRATION_START.strftime("%Y-%m-%d"),
        "calibration_end": SENTIMENT_CALIBRATION_END.strftime("%Y-%m-%d"),
        "calibration_rows": len(calibration),
        "application_source_start": SENTIMENT_APPLICATION_SOURCE_START.strftime(
            "%Y-%m-%d"
        ),
        "availability_lag_months": 1,
        "standardization_ddof": 0,
        "loadings": dict(
            zip(SENTIMENT_COMPONENT_COLUMNS, loadings.tolist(), strict=True)
        ),
        "explained_variance_ratio": float(
            singular_values[0] ** 2 / np.square(singular_values).sum()
        ),
        "orientation_anchor_columns": list(SENTIMENT_ANCHOR_COLUMNS),
        "orientation_anchor_correlation": anchor_correlation,
        "calibration_score_scale": score_scale,
    }
    return proxy, metadata


def build_inputs(raw_dir: Path, output_dir: Path, manifest_path: Path) -> dict[str, Any]:
    series: dict[str, pd.DataFrame] = {}
    source_metadata: dict[str, Any] = {}
    for name, contract in CONTRACTS.items():
        series[name], source_metadata[name] = load_series(raw_dir, contract)

    msb = series["rf_msb_91d"].rename(columns={"value": "msb_91d_yield_pct"})
    cd = series["rf_cd_91d"].rename(columns={"value": "cd_91d_yield_pct"})
    rf_proxies = msb.merge(cd, on="month", how="outer", validate="one_to_one")
    rf_proxies["msb_91d_rf"] = annual_yield_percent_to_monthly_return(
        rf_proxies["msb_91d_yield_pct"]
    )
    rf_proxies["cd_91d_rf"] = annual_yield_percent_to_monthly_return(
        rf_proxies["cd_91d_yield_pct"]
    )
    risk_free = rf_proxies.loc[rf_proxies["msb_91d_rf"].notna(), ["month"]].copy()
    risk_free["rf"] = rf_proxies.loc[
        rf_proxies["msb_91d_rf"].notna(), "msb_91d_rf"
    ].to_numpy()

    macro = (
        series["esi_original"]
        .rename(columns={"value": "esi_original"})
        .merge(
            series["esi_cyclical"].rename(columns={"value": "esi_cyclical"}),
            on="month",
            how="outer",
            validate="one_to_one",
        )
        .merge(
            series["ccsi"].rename(columns={"value": "ccsi"}),
            on="month",
            how="outer",
            validate="one_to_one",
        )
    )
    activity = macro.loc[macro["esi_cyclical"].notna(), ["month"]].copy()
    activity["activity"] = (
        macro.loc[macro["esi_cyclical"].notna(), "esi_cyclical"] - 100.0
    ).to_numpy()

    components = series["kospi_turnover"].rename(
        columns={"value": "kospi_turnover_pct"}
    )
    for name, column in (
        ("kosdaq_turnover", "kosdaq_turnover_pct"),
        ("individual_buy_value", "individual_buy_value_million_krw"),
        ("individual_sell_value", "individual_sell_value_million_krw"),
        ("investor_deposits", "investor_deposits_krw"),
        ("margin_loan_balance", "margin_loan_balance_krw"),
    ):
        components = components.merge(
            series[name].rename(columns={"value": column}),
            on="month",
            how="outer",
            validate="one_to_one",
        )
    turnover = components[
        ["individual_buy_value_million_krw", "individual_sell_value_million_krw"]
    ].sum(axis=1, min_count=2)
    components["individual_buy_sell_imbalance"] = (
        components["individual_buy_value_million_krw"]
        - components["individual_sell_value_million_krw"]
    ) / turnover.replace(0, np.nan)
    components["investor_deposits_log_change"] = np.log(
        components["investor_deposits_krw"].where(
            components["investor_deposits_krw"].gt(0)
        )
    ).diff()
    components["margin_loan_balance_log_change"] = np.log(
        components["margin_loan_balance_krw"].where(
            components["margin_loan_balance_krw"].gt(0)
        )
    ).diff()
    sentiment_proxy, sentiment_proxy_metadata = build_sentiment_proxy(components)

    outputs = {
        "risk_free_monthly": _write_csv(
            risk_free, output_dir / "risk_free_monthly.csv"
        ),
        "risk_free_proxies": _write_csv(
            rf_proxies, output_dir / "risk_free_proxies_monthly.csv"
        ),
        "activity_monthly": _write_csv(
            activity, output_dir / "korea_activity_monthly.csv"
        ),
        "macro_proxies": _write_csv(
            macro, output_dir / "macro_proxies_monthly.csv"
        ),
        "sentiment_components": _write_csv(
            components, output_dir / "sentiment_ecos_components_monthly.csv"
        ),
        "sentiment_proxy_monthly": _write_csv(
            sentiment_proxy,
            output_dir / "korea_sentiment_proxy_monthly.csv",
        ),
    }
    manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": "Bank of Korea ECOS Open API",
        "credential_in_outputs": False,
        "raw_series": source_metadata,
        "transformations": {
            "rf": "(1 + annual_yield_percent / 100) ** (1 / 12) - 1",
            "primary_rf": "Monetary Stabilization Bond 91-day monthly yield",
            "activity": "ESI cyclical component minus 100 index points",
            "individual_buy_sell_imbalance": "(buy - sell) / (buy + sell)",
            "level_growth": "first difference of natural log for positive levels",
        },
        "sentiment_status": {
            "complete_baker_wurgler_index": False,
            "proxy_built": True,
            "proxy_methodology": sentiment_proxy_metadata,
            "missing_non_ecos_components": [
                "IPO count",
                "IPO first-day return",
                "equity share in total issuance",
                "dividend premium",
            ],
            "warning": (
                "The generated sentiment series is an incomplete ECOS-only proxy, "
                "not an exact Baker-Wurgler index."
            ),
        },
        "outputs": outputs,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_inputs(args.raw_dir, args.output_dir, args.manifest)
    print(
        json.dumps(
            {
                "manifest": str(args.manifest.resolve()),
                "outputs": manifest["outputs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())