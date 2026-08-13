"""Synchronize Markdown result tables from audit-backed generated CSV files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from guijarro_ordonez_replication.experiment_matrix import experiment_coverage  # noqa: E402


DRAFT = PROJECT / "guijarro-korea-replication.md"
REPORT = PROJECT / "outputs" / "paper-korean"
K_VALUES = (0, 1, 3, 5, 8, 10, 15)
PERFORMANCE_HEADER = (
    "| K | Fama-French SR | Fama-French μ | Fama-French σ | "
    "PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |"
)
ALPHA_HEADER = (
    "| K | Fama-French α | Fama-French tα | Fama-French R² | "
    "Fama-French μ | Fama-French tμ | PCA α | PCA tα | PCA R² | "
    "PCA μ | PCA tμ | IPCA α | IPCA tα | IPCA R² | IPCA μ | IPCA tμ |"
)


def _replace_nth_table(text: str, anchor: str, table: str, occurrence: int = 0) -> str:
    anchor_at = text.index(anchor)
    starts = [match.start() for match in re.finditer(r"(?m)^\|", text[anchor_at:])]
    table_starts: list[int] = []
    for relative in starts:
        absolute = anchor_at + relative
        first_end = text.index("\n", absolute)
        second_end = text.index("\n", first_end + 1)
        second = text[first_end + 1 : second_end]
        if re.fullmatch(r"\|[ :\-\|]+\|", second):
            table_starts.append(absolute)
    start = table_starts[occurrence]
    end = text.find("\n\n", start)
    if end < 0:
        end = len(text)
    return text[:start] + table.rstrip() + text[end:]


def _factor_key(value: object) -> tuple[str, int]:
    label = str(value).removesuffix(" average residual")
    if label == "Stock returns K0":
        return "stock", 0
    if label == "PCA":
        return "pca", 5
    match = re.fullmatch(r"PCA(\d+)", label)
    if match:
        return "pca", int(match.group(1))
    match = re.fullmatch(r"Korean FF(\d+)", label)
    if match:
        return "ff", int(match.group(1))
    raise ValueError(f"unrecognized factor model: {value}")


def _select(frame: pd.DataFrame, family: str, k: int, model: str | None = None) -> pd.Series | None:
    for _, row in frame.iterrows():
        source = row["factor_model"] if "factor_model" in row else row["strategy"]
        row_family, row_k = _factor_key(source)
        factor_matches = row_family == "stock" if k == 0 else (row_family, row_k) == (family, k)
        model_matches = model is None or row.get("model") == model
        if factor_matches and model_matches:
            return row
    return None


def _pct(value: object) -> str:
    return f"{float(value) * 100:.1f}%"


def _number(value: object, digits: int) -> str:
    return f"{float(value):.{digits}f}"


def _missing(family: str, k: int, width: int, *, eight_year: bool = False) -> list[str]:
    if eight_year:
        symbol = "—ᴺ" if family == "ff" and k in {10, 15} else "—ᴰ"
    elif family == "ff" and k == 8:
        symbol = "—ᴰ"
    elif family == "ff" and k in {10, 15}:
        symbol = "—ᴺ"
    elif family == "ipca" and k != 0:
        symbol = "—ᴰ"
    else:
        symbol = "—ᵁ"
    return [symbol] * width


def _performance_cells(frame: pd.DataFrame, family: str, k: int, model: str) -> list[str]:
    row = _select(frame, family, k, model)
    if row is None:
        return _missing(family, k, 3)
    return [_number(row["sharpe"], 3), _pct(row["annual_return"]), _pct(row["annual_volatility"])]


def _alpha_cells(
    performance: pd.DataFrame,
    alpha: pd.DataFrame,
    family: str,
    k: int,
    model: str,
) -> list[str]:
    perf = _select(performance, family, k, model)
    if perf is None:
        return _missing(family, k, 5)
    candidates = alpha.loc[
        alpha["strategy"].eq(perf["strategy"])
        & alpha["factor_model"].eq("Korean 6-factor")
    ]
    if len(candidates) != 1:
        raise ValueError(f"missing unique Korean 6-factor alpha for {perf['strategy']}")
    row = candidates.iloc[0]
    return [
        _pct(row["annual_alpha"]),
        _number(row["alpha_t_statistic"], 2),
        _pct(row["r_squared"]),
        _pct(perf["annual_return"]),
        _number(perf["mean_t_statistic"], 2),
    ]


def _performance_table(frame: pd.DataFrame, model: str, *, eight_year: bool = False) -> str:
    lines = [PERFORMANCE_HEADER, "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k in K_VALUES:
        cells: list[str] = []
        for family in ("ff", "pca", "ipca"):
            cells.extend(_missing(family, k, 3, eight_year=True) if eight_year else _performance_cells(frame, family, k, model))
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _alpha_table(performance: pd.DataFrame, alpha: pd.DataFrame, model: str, *, eight_year: bool = False) -> str:
    lines = [ALPHA_HEADER, "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k in K_VALUES:
        cells: list[str] = []
        for family in ("ff", "pca", "ipca"):
            cells.extend(_missing(family, k, 5, eight_year=True) if eight_year else _alpha_cells(performance, alpha, family, k, model))
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _table_one(performance: pd.DataFrame) -> str:
    header = "| Model | K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |"
    lines = [header, "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for model, display in (("cnn_transformer", "**CNN+Trans**"), ("fourier_ffn", "**Fourier+FFN**"), ("ou_threshold", "**OU + Thresh**")):
        for k in K_VALUES:
            cells: list[str] = []
            for family in ("ff", "pca", "ipca"):
                cells.extend(_performance_cells(performance, family, k, model))
            lines.append(f"| {display} | {k} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _unconditional_alpha_cells(performance: pd.DataFrame, alpha: pd.DataFrame, family: str, k: int) -> list[str]:
    perf = _select(performance, family, k)
    if perf is None:
        return _missing(family, k, 5)
    candidates = alpha.loc[
        alpha["strategy"].eq(perf["strategy"])
        & alpha["factor_model"].eq("Korean 6-factor")
    ]
    if len(candidates) != 1:
        raise ValueError(f"missing unconditional alpha for {perf['strategy']}")
    row = candidates.iloc[0]
    returns = pd.read_csv(REPORT / "appendix" / "unconditional_average_residual_returns.csv")
    sample = returns.loc[returns["strategy"].eq(str(perf["strategy"]).removesuffix(" average residual"))]
    mean = sample["return"].to_numpy()
    mean_t = mean.mean() / (mean.std(ddof=1) / len(mean) ** 0.5)
    return [_pct(row["annual_alpha"]), _number(row["alpha_t_statistic"], 2), _pct(row["r_squared"]), _pct(perf["annual_return"]), _number(mean_t, 2)]


def _unconditional_tables() -> tuple[str, str]:
    performance = pd.read_csv(REPORT / "appendix" / "table_a06_unconditional_performance.csv")
    alpha = pd.read_csv(REPORT / "appendix" / "table_a07_unconditional_alpha.csv")
    perf_lines = [PERFORMANCE_HEADER, "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    alpha_lines = [ALPHA_HEADER, "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k in K_VALUES:
        perf_cells: list[str] = []
        alpha_cells: list[str] = []
        for family in ("ff", "pca", "ipca"):
            row = _select(performance, family, k)
            if row is None:
                perf_cells.extend(_missing(family, k, 3))
            else:
                perf_cells.extend([_number(row["sharpe"], 3), _pct(row["annual_return"]), _pct(row["annual_volatility"])])
            alpha_cells.extend(_unconditional_alpha_cells(performance, alpha, family, k))
        perf_lines.append(f"| {k} | " + " | ".join(perf_cells) + " |")
        alpha_lines.append(f"| {k} | " + " | ".join(alpha_cells) + " |")
    return "\n".join(perf_lines), "\n".join(alpha_lines)


def _correlation_table() -> str:
    labels = ["Fama-French 3", "PCA 3", "IPCA 3", "Fama-French 5", "PCA 5", "IPCA 5", "PCA 10", "IPCA 10"]
    sources = {
        "Fama-French 3": "Korean FF3",
        "PCA 3": "PCA3",
        "Fama-French 5": "Korean FF5",
        "PCA 5": "PCA5",
        "PCA 10": "PCA10",
    }
    frame = pd.read_csv(REPORT / "appendix" / "table_a08_strategy_correlations.csv", index_col=0)
    def actual(label: str) -> str | None:
        prefix = sources.get(label)
        if prefix is None:
            return None
        matches = [name for name in frame.index if str(name).startswith(prefix + " /")]
        return matches[0] if len(matches) == 1 else None
    lines = ["|  | " + " | ".join(labels) + " |", "|---|" + "---:|" * len(labels)]
    for row_label in labels:
        cells = []
        for column_label in labels:
            row_source, column_source = actual(row_label), actual(column_label)
            if row_source is None or column_source is None:
                cells.append("—ᴰ" if "IPCA" in row_label + column_label else "—ᵁ")
            else:
                cells.append(_number(frame.loc[row_source, column_source], 2))
        lines.append(f"| {row_label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _ablation_table() -> str:
    frame = pd.read_csv(REPORT / "appendix" / "table_a09_time_series_ablation.csv")
    header = "| Model | K | Fama-French SR | Fama-French μ | Fama-French σ | PCA SR | PCA μ | PCA σ | IPCA SR | IPCA μ | IPCA σ |"
    lines = [header, "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for model, display in (("ou_ffn", "OU+FFN"), ("direct_ffn", "FFN")):
        for k in K_VALUES:
            cells: list[str] = []
            for family in ("ff", "pca", "ipca"):
                cells.extend(_performance_cells(frame, family, k, model))
            lines.append(f"| {display} | {k} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _friction_table() -> str:
    frame = pd.read_csv(REPORT / "appendix" / "table_a10_pca_cnn_friction_trained.csv")
    lines = [
        "| K | Sharpe ratio SR | Sharpe ratio μ | Sharpe ratio σ | Mean-variance SR | Mean-variance μ | Mean-variance σ |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for k in (0, 1, 3, 5, 10, 15):
        cells = _performance_cells(frame.loc[frame["objective"].eq("sharpe")], "pca", k, "cnn_transformer_frictions")
        cells += _performance_cells(frame.loc[frame["objective"].eq("meanvar")], "pca", k, "cnn_transformer_frictions")
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    coverage = experiment_coverage(PROJECT)
    if coverage["summary"].get("unrun", 0):
        raise SystemExit(f"refusing partial draft sync: {coverage['summary']}")
    text = DRAFT.read_text("utf-8")
    tables: dict[int, tuple[pd.DataFrame, pd.DataFrame | None]] = {}
    for number in (1, 3, 5, 7):
        tables[number] = (pd.read_csv(REPORT / f"table_{number:02d}_korean_performance.csv"), None)
    for number in (2, 4, 6, 8):
        tables[number] = (
            pd.read_csv(REPORT / f"table_{number - 1:02d}_korean_performance.csv"),
            pd.read_csv(REPORT / f"table_{number:02d}_korean_factor_alpha.csv"),
        )

    text = _replace_nth_table(text, "**Table 1.", _table_one(tables[1][0]))
    for index, model in enumerate(("cnn_transformer", "fourier_ffn", "ou_threshold")):
        text = _replace_nth_table(text, "**Table 2.", _alpha_table(tables[2][0], tables[2][1], model), index)
    for index, model in enumerate(("cnn_transformer", "fourier_ffn")):
        text = _replace_nth_table(text, "**Table 3.", _performance_table(tables[3][0], model), index)
        text = _replace_nth_table(text, "**Table 4.", _alpha_table(tables[4][0], tables[4][1], model), index)
    text = _replace_nth_table(text, "**Table 5.", _performance_table(tables[5][0], "cnn_transformer"))
    text = _replace_nth_table(text, "**Table 6.", _alpha_table(tables[6][0], tables[6][1], "cnn_transformer"))
    text = _replace_nth_table(text, "**Table 7.", _performance_table(tables[7][0], "cnn_transformer"), 0)
    text = _replace_nth_table(text, "**Table 7.", _performance_table(tables[7][0], "cnn_transformer", eight_year=True), 1)
    text = _replace_nth_table(text, "**Table 8.", _alpha_table(tables[8][0], tables[8][1], "cnn_transformer"), 0)
    text = _replace_nth_table(text, "**Table 8.", _alpha_table(tables[8][0], tables[8][1], "cnn_transformer", eight_year=True), 1)

    blocked_lines = [
        "| K | Sharpe ratio SR | Sharpe ratio μ | Sharpe ratio σ | Mean-variance SR | Mean-variance μ | Mean-variance σ |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        "| 0 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |",
        "| 1 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |",
        "| 3 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |",
        "| 5 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |",
        "| 10 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |",
        "| 15 | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ | —ᴰ |",
    ]
    text = _replace_nth_table(text, "**Table 9.", "\n".join(blocked_lines))

    unconditional_performance, unconditional_alpha = _unconditional_tables()
    text = _replace_nth_table(text, "**Table A.VI.", unconditional_performance)
    text = _replace_nth_table(text, "**Table A.VII.", unconditional_alpha)
    text = _replace_nth_table(text, "**Table A.VIII.", _correlation_table())
    text = _replace_nth_table(text, "**Table A.IX.", _ablation_table())
    text = _replace_nth_table(text, "**Table A.X.", _friction_table())

    stale = [line for line in text.splitlines() if line.startswith("|") and "—ᵁ" in line]
    if stale:
        raise ValueError(f"unfilled runnable table cells remain: {stale[:3]}")
    DRAFT.write_text(text, encoding="utf-8")
    print(f"updated {DRAFT} from audit-backed generated tables")


if __name__ == "__main__":
    main()
