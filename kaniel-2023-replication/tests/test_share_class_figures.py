import json
from pathlib import Path

import pandas as pd

from kaniel_replication.share_class_figures import generate_share_class_figures


def test_generate_share_class_figures(tmp_path: Path) -> None:
    comparison = pd.DataFrame(
        {
            "tna_difference_fraction": [0.001, 0.01, 0.03, 0.50],
            "representative_return": [0.011, 0.012, 0.010, 0.020],
            "class_weighted_return": [0.010, 0.011, 0.010, 0.005],
        }
    )
    diagnostics = pd.DataFrame(
        {
            "consolidation_decision": [
                "representative_row_preferred",
                "separate_return_basis_required",
                "manual_review",
            ]
        }
    )
    comparison_path = tmp_path / "comparison.parquet"
    diagnostics_path = tmp_path / "diagnostics.csv"
    summary_path = tmp_path / "summary.json"
    output_dir = tmp_path / "figures"
    comparison.to_parquet(comparison_path, index=False)
    diagnostics.to_csv(diagnostics_path, index=False)
    summary_path.write_text(
        json.dumps(
            {
                "thresholds": {
                    "tna_tolerance_fraction": 0.02,
                    "return_tolerance_bps": 5.0,
                }
            }
        ),
        encoding="utf-8",
    )

    outputs = generate_share_class_figures(
        comparison_path,
        diagnostics_path,
        summary_path,
        output_dir,
    )

    assert len(outputs) == 3
    assert all(path.exists() and path.stat().st_size > 0 for path in outputs)
    manifest = json.loads(
        (output_dir / "share_class_figures.manifest.json").read_text(encoding="utf-8")
    )
    assert len(manifest["outputs"]) == 3
