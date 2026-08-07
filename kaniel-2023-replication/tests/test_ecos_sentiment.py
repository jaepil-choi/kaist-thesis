from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "kaist_pilot"
    / "build_kaniel_ecos_inputs.py"
)
SPEC = importlib.util.spec_from_file_location("build_kaniel_ecos_inputs", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_sentiment_proxy_uses_fixed_calibration_and_one_month_lag() -> None:
    months = pd.date_range("2005-01-31", "2015-12-31", freq="ME")
    time = np.arange(len(months), dtype=float)
    components = pd.DataFrame(
        {
            "month": months,
            "kospi_turnover_pct": 50 + 0.2 * time + np.sin(time / 3),
            "kosdaq_turnover_pct": 80 + 0.3 * time + np.cos(time / 4),
            "individual_buy_sell_imbalance": np.sin(time / 5) / 10,
            "investor_deposits_log_change": np.cos(time / 6) / 20,
            "margin_loan_balance_log_change": 0.001 * time + np.sin(time / 7) / 30,
        }
    )

    proxy, metadata = MODULE.build_sentiment_proxy(components)
    repeated, repeated_metadata = MODULE.build_sentiment_proxy(components)

    pd.testing.assert_frame_equal(proxy, repeated)
    assert metadata == repeated_metadata
    assert metadata["exact_baker_wurgler"] is False
    assert metadata["calibration_rows"] == 120
    assert metadata["availability_lag_months"] == 1
    assert metadata["orientation_anchor_correlation"] > 0
    assert proxy["month"].min() == pd.Timestamp("2015-01-31")
    assert proxy["month"].max() == pd.Timestamp("2016-01-31")
    assert len(proxy) == 13
    assert proxy["sentiment"].notna().all()