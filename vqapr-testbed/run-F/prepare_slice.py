"""Build a tiny KRX adjusted-price slice and prove available_at localization first."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SOURCE = Path("../../data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet")
OUTPUT = Path("krx_slice.parquet")
PROOF = Path("available_at_proof.json")
SEOUL = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")


def prove_localization() -> None:
    local = datetime(2015, 1, 2, 15, 0, tzinfo=SEOUL)
    utc = local.astimezone(UTC)
    round_trip = utc.astimezone(SEOUL)
    assert round_trip.date().isoformat() == "2015-01-02"
    assert round_trip.time().isoformat() == "15:00:00"
    assert round_trip.utcoffset().total_seconds() == 9 * 60 * 60
    assert utc.isoformat() == "2015-01-02T06:00:00+00:00"
    PROOF.write_text(
        json.dumps(
            {
                "local": local.isoformat(),
                "utc": utc.isoformat(),
                "round_trip": round_trip.isoformat(),
                "assertions_passed": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    prove_localization()

    table = pq.read_table(
        SOURCE,
        columns=["date", "ticker", "adj_close", "return", "is_trading_halt"],
        filters=[("date", ">=", datetime(2024, 1, 2)), ("date", "<=", datetime(2024, 1, 10))],
    )
    frame = table.to_pandas()
    counts = frame.groupby("ticker", sort=True)["date"].nunique()
    instruments = counts[counts == counts.max()].index[:3].tolist()
    frame = frame[frame["ticker"].isin(instruments)].copy()
    frame["instrument"] = frame["ticker"].astype(str)
    local_close = frame["date"].dt.normalize() + pd.Timedelta(hours=15, minutes=30)
    frame["available_at"] = local_close.dt.tz_localize("Asia/Seoul")
    frame["trade_at"] = frame["available_at"]
    frame["close"] = frame["adj_close"].astype(float)
    frame["is_tradable"] = (~frame["is_trading_halt"].fillna(False)) & frame["close"].notna()
    output = frame[
        ["available_at", "trade_at", "instrument", "adj_close", "return", "close", "is_tradable"]
    ].sort_values(["available_at", "instrument"])
    pq.write_table(pa.Table.from_pandas(output, preserve_index=False), OUTPUT)
    print(json.dumps({"rows": len(output), "instruments": instruments, "output": str(OUTPUT)}))


if __name__ == "__main__":
    main()
