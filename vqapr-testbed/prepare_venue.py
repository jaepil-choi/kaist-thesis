import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa

SRC = "data/adjusted_prices_prepared.parquet"
OUT = "data/venue_table.parquet"

t = pq.read_table(SRC)

is_tradable = pc.and_(
    pc.invert(t.column("is_trading_halt")),
    pc.invert(t.column("is_admin_issue")),
)

out = pa.table({
    "ticker": t.column("ticker"),
    "trade_at": t.column("available_at"),
    "close": t.column("adj_close"),
    "is_tradable": is_tradable,
})

pq.write_table(out, OUT)
print("wrote", OUT, out.num_rows)
