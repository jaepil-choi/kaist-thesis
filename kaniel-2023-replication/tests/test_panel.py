from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from kaniel_replication.panel import build_class_month_panel


def test_streaming_monthly_panel_and_flow(tmp_path: Path) -> None:
    daily = pd.DataFrame(
        {
            "기준일자": pd.to_datetime(
                [
                    "2020-01-02",
                    "2020-01-03",
                    "2020-01-31",
                    "2020-02-03",
                    "2020-02-28",
                    "2020-01-02",
                ]
            ),
            "협회펀드코드": ["A", "A", "A", "A", "A", "B"],
            "순자산": ["0", "100", "110", "112", "121", "100"],
            "실현수익률": ["1", "1.01", "1.02", "1.00", "1.10", "1.00"],
            "BM수익률": ["1", "1.00", "1.01", "1.00", "1.02", "1.00"],
            "대유형코드": ["20"] * 6,
            "유형코드": ["2001", "2001", "2001", "2001", "2001", "99999"],
        }
    ).sort_values(["기준일자", "협회펀드코드"])
    source = tmp_path / "daily.parquet"
    output = tmp_path / "monthly.parquet"
    pq.write_table(pa.Table.from_pandas(daily, preserve_index=False), source, row_group_size=2)

    manifest = build_class_month_panel(
        source,
        output,
        active_type_codes={"2001"},
        batch_size=2,
    )
    monthly = pq.read_table(output).to_pandas()

    assert len(monthly) == 2
    assert manifest["diagnostics"]["placeholder_rows"] == 1
    assert abs(monthly.loc[0, "monthly_return"] - (1.01 * 1.02 - 1)) < 1e-12
    assert pd.isna(monthly.loc[0, "flow"])
    expected_flow = 121 / (110 * 1.10) - 1
    assert abs(monthly.loc[1, "flow"] - expected_flow) < 1e-12


def test_implausible_return_factor_is_quarantined(tmp_path: Path) -> None:
    daily = pd.DataFrame(
        {
            "기준일자": pd.to_datetime(["2020-01-02", "2020-01-31"]),
            "협회펀드코드": ["A", "A"],
            "순자산": ["100", "200"],
            "실현수익률": ["1.01", "2.00"],
            "BM수익률": ["1.00", "1.00"],
            "대유형코드": ["20", "20"],
            "유형코드": ["2001", "2001"],
        }
    )
    source = tmp_path / "daily.parquet"
    output = tmp_path / "monthly.parquet"
    pq.write_table(pa.Table.from_pandas(daily, preserve_index=False), source)

    manifest = build_class_month_panel(source, output, active_type_codes={"2001"})
    monthly = pq.read_table(output).to_pandas()

    assert manifest["diagnostics"]["implausible_return_factors"] == 1
    assert monthly.loc[0, "return_outliers"] == 1
    assert pd.isna(monthly.loc[0, "monthly_return"])
    assert output.with_suffix(".return_outliers.parquet").exists()
