import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa

SRC = "../data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet"
OUT = "data/adjusted_prices_prepared.parquet"

t = pq.read_table(SRC)

# `date` is a naive midnight timestamp representing the trading session date.
# KRX regular session close is 15:30 KST. The row is first knowable at that
# instant, not at midnight of the same date. Localize explicitly: registration
# refuses a naive timestamp and does not infer this for you.
date_col = t.column("date")
# add 15:30 (still naive) then LOCALIZE (not cast!) to Asia/Seoul. `.cast(..., tz=...)`
# reinterprets the underlying int64 as UTC and merely relabels it -- it does not shift the
# wall-clock value. `pc.assume_timezone` is the operation that actually localizes a naive
# timestamp. Confirmed by testing both against a known instant before trusting either.
seconds = pc.add(date_col.cast(pa.timestamp("us")), pa.scalar(15 * 3600 + 30 * 60, type=pa.duration("s")))
available_at = pc.assume_timezone(seconds, "Asia/Seoul")

t = t.append_column("available_at", available_at)

pq.write_table(t, OUT)
print("wrote", OUT, t.num_rows, "rows")
