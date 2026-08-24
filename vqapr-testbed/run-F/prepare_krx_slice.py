"""Create a small KRX price/venue slice with point-in-time close timestamps."""

from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

SOURCE = Path("../../data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet")
OUTPUT = Path("krx_slice.parquet")
INSTRUMENTS = ("A000020", "A000040")
START = datetime(2015, 1, 2)
END = datetime(2015, 1, 9)

source = ds.dataset(SOURCE, format="parquet")
rows = source.to_table(
    columns=["date", "ticker", "adj_close", "return"],
    filter=(ds.field("date") >= START)
    & (ds.field("date") <= END)
    & ds.field("ticker").isin(INSTRUMENTS),
)
rows = rows.sort_by([("date", "ascending"), ("ticker", "ascending")])
wall_close = pc.add(rows["date"], pa.scalar(15 * 60 * 60 * 1_000_000, type=pa.duration("us")))
available_at = pc.assume_timezone(wall_close, "Asia/Seoul")

output = pa.table(
    {
        "available_at": available_at,
        "trade_at": available_at,
        "instrument": rows["ticker"],
        "return": rows["return"],
        "close": rows["adj_close"],
        "is_tradable": pa.array([True] * rows.num_rows, type=pa.bool_()),
    }
)
assert output.num_rows == 12, output.num_rows
assert output["available_at"].type == pa.timestamp("us", tz="Asia/Seoul")
assert output.select(["available_at", "instrument"]).group_by(
    ["available_at", "instrument"]
).aggregate([]).num_rows == output.num_rows
assert output["return"].null_count == 0
assert output["close"].null_count == 0
pq.write_table(output, OUTPUT)
print({"output": str(OUTPUT), "rows": output.num_rows, "schema": str(output.schema)})
