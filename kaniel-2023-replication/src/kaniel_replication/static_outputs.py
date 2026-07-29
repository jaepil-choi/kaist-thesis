"""Generate paper-definition outputs that do not require empirical data."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import pandas as pd

from .config import ReplicationConfig
from .provenance import sha256, write_manifest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402


TABLE_1 = [
    ("Past Returns", "r2_1", "Short-term momentum"),
    ("Past Returns", "r12_2", "Momentum"),
    ("Past Returns", "r12_7", "Intermediate momentum"),
    ("Past Returns", "r36_13", "Long-term momentum"),
    ("Past Returns", "ST_Rev", "Short-term reversal"),
    ("Past Returns", "LT_Rev", "Long-term reversal"),
    ("Investment", "Investment", "Investment"),
    ("Investment", "NOA", "Net operating assets"),
    ("Investment", "DPI2A", "Change in property, plant, and equipment"),
    ("Investment", "NI", "Net share issues"),
    ("Profitability", "PROF", "Profitability"),
    ("Profitability", "ATO", "Net sales over lagged net operating assets"),
    ("Profitability", "CTO", "Capital turnover"),
    ("Profitability", "FC2Y", "Fixed costs to sales"),
    ("Profitability", "OP", "Operating profitability"),
    ("Profitability", "PM", "Profit margin"),
    ("Profitability", "RNA", "Return on net operating assets"),
    ("Profitability", "ROA", "Return on assets"),
    ("Profitability", "ROE", "Return on equity"),
    ("Profitability", "SGA2S", "SG&A expenses to sales"),
    ("Profitability", "D2A", "Capital intensity"),
    ("Intangibles", "AC", "Accrual"),
    ("Intangibles", "OA", "Operating accruals"),
    ("Intangibles", "OL", "Operating leverage"),
    ("Intangibles", "PCM", "Price-to-cost margin"),
    ("Value", "A2ME", "Assets to market capitalization"),
    ("Value", "BEME", "Book-to-market ratio"),
    ("Value", "C", "Cash ratio"),
    ("Value", "CF", "Free cash flow to book value"),
    ("Value", "CF2P", "Cash flow to price"),
    ("Value", "D2P", "Dividend yield"),
    ("Value", "E2P", "Earnings to price"),
    ("Value", "Q", "Tobin's Q"),
    ("Value", "S2P", "Sales to price"),
    ("Value", "Lev", "Leverage"),
    ("Trading Frictions", "AT", "Total assets"),
    ("Trading Frictions", "Beta", "CAPM beta"),
    ("Trading Frictions", "IdioVol", "Idiosyncratic volatility"),
    ("Trading Frictions", "LME", "Size"),
    ("Trading Frictions", "LTurnover", "Turnover"),
    ("Trading Frictions", "MktBeta", "Market beta"),
    ("Trading Frictions", "Rel2High", "Closeness to past-year high"),
    ("Trading Frictions", "Resid_Var", "Residual variance"),
    ("Trading Frictions", "Spread", "Bid-ask spread"),
    ("Trading Frictions", "SUV", "Standard unexplained volume"),
    ("Trading Frictions", "Variance", "Variance"),
    ("Fund Momentum", "F_ST_Rev", "Fund short-term reversal"),
    ("Fund Momentum", "F_r2_1", "Fund short-term momentum"),
    ("Fund Momentum", "F_r12_2", "Fund momentum"),
    ("Fund Characteristics", "age", "Fund age"),
    ("Fund Characteristics", "tna", "Fund TNA"),
    ("Fund Characteristics", "flow", "Fund flow"),
    ("Fund Characteristics", "exp_ratio", "Fund expense ratio"),
    ("Fund Characteristics", "turnover_ratio", "Fund turnover ratio"),
    ("Fund Family Characteristics", "family_tna", "Family TNA"),
    ("Fund Family Characteristics", "fund_no", "Number of funds in family"),
    ("Fund Family Characteristics", "Family_r12_2", "Family momentum"),
    ("Fund Family Characteristics", "Family_age", "Family age"),
    ("Fund Family Characteristics", "Family_flow", "Family flow"),
]

TABLE_2 = [
    (
        "F_r2_1",
        "Short-term momentum",
        "Lagged one-month abnormal return",
        "Jegadeesh and Titman (1993)",
    ),
    (
        "F_r12_2",
        "Momentum",
        "Mean abnormal return at lags 2-12; at least 8 non-missing observations",
        "Fama and French (1996)",
    ),
    (
        "F_ST_Rev",
        "Short-term reversal",
        "Most recent prior-month abnormal return",
        "Jegadeesh and Titman (1993)",
    ),
]

TABLE_B1 = [
    ("HL", "Number of hidden layers", "1, 2, 3", "1"),
    ("HU", "Hidden units in each layer", "2^(6-i) or 2^(7-i), i=1..HL", "64"),
    ("DR", "Dropout keep probability", "0.90, 0.95", "0.95"),
    ("LR", "Learning rate", "0.001, 0.01", "0.01"),
    ("L1", "L1 regularization", "0, 1e-5", "0"),
    ("L2", "L2 regularization", "0, 1e-2, 1e-3", "1e-3"),
]


def _draw_network(path: Path) -> None:
    figure, axis = plt.subplots(figsize=(10, 4.8))
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 6)
    axis.axis("off")

    nodes = [
        (0.5, 1.0, 2.2, 4.0, "Inputs\nfund characteristics\n+ macro state"),
        (3.9, 0.55, 2.2, 4.9, "Hidden layer\n64 ReLU units\nregularization"),
        (7.4, 1.7, 2.1, 2.6, "Output\nnext-month\nabnormal return"),
    ]
    for x, y, width, height, label in nodes:
        patch = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.05",
            facecolor="#E8F0FE",
            edgecolor="#315A9E",
            linewidth=1.5,
        )
        axis.add_patch(patch)
        axis.text(x + width / 2, y + height / 2, label, ha="center", va="center")

    for start, end in [((2.7, 3.0), (3.9, 3.0)), ((6.1, 3.0), (7.4, 3.0))]:
        axis.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.8})
    axis.set_title("Figure 3 replication: single-hidden-layer feedforward network")
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def generate_static_outputs(config: ReplicationConfig) -> list[Path]:
    """Generate Table 1, Table 2, Figure 3, and Table B.1."""

    table_dir = config.output_root / "tables"
    figure_dir = config.output_root / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    paths = [
        table_dir / "table_01_characteristics.csv",
        table_dir / "table_02_fund_momentum.csv",
        figure_dir / "fig_03_network_architecture.png",
        table_dir / "table_b_01_tuning_grid.csv",
    ]
    pd.DataFrame(TABLE_1, columns=["category", "acronym", "name"]).to_csv(
        paths[0], index=False, encoding="utf-8"
    )
    pd.DataFrame(TABLE_2, columns=["acronym", "name", "definition", "reference"]).to_csv(
        paths[1], index=False, encoding="utf-8"
    )
    _draw_network(paths[2])
    pd.DataFrame(
        TABLE_B1,
        columns=["notation", "tuning_parameter", "candidates", "paper_optimal"],
    ).to_csv(paths[3], index=False, encoding="utf-8")

    write_manifest(
        config.output_root / "manifests" / "static_outputs.json",
        {
            "outputs": [
                {"path": str(path), "sha256": sha256(path)} for path in paths
            ]
        },
    )
    return paths
