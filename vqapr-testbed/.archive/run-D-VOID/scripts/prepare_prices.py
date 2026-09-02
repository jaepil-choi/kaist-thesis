"""Prepare adjusted_prices.parquet for vqapr dataset registration.

- source `date` is a naive daily timestamp (midnight, no session-close instant, no tz).
- vqapr's dataset template refuses a naive `available_at` column (see FRICTION F-002).
- KRX regular session closes 15:30 Asia/Seoul; a daily close is available at that instant,
  not at midnight of the same date. This is domain knowledge (the KRX close time) that
  neither the source parquet nor the framework's docs supplied.
- Output keeps the original columns and adds `available_at`, tz-aware in Asia/Seoul.
"""

from decimal import Decimal

import pandas as pd

SRC = "../data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet"
OUT = "workspace/prepared_data/adjusted_prices.parquet"

df = pd.read_parquet(SRC)

# Full file is 8.65M rows; converting to Decimal at that scale is a Python-level map over every
# cell and is minutes slow (see PROFILING.md). This dev run only needs five names over six
# months, so filter first -- the framework gives no guidance that Decimal conversion is expected
# or that it should happen before or after filtering.
UNIVERSE = ["A000020", "A000040", "A000050", "A000060", "A000070"]
df = df[df["ticker"].isin(UNIVERSE) & (df["date"] >= "2015-09-01") & (df["date"] <= "2016-12-31")].copy()

df["available_at"] = (
    df["date"].dt.tz_localize("Asia/Seoul") + pd.Timedelta(hours=15, minutes=30)
)

# Strategy callbacks receive Decimal, and the scaffold (`vqapr new strategy`) assumes it without
# saying so: `korean_equity_strategy.py` did `value / values[0]` on `row["close"]` and crashed with
# "unsupported operand type(s) for -: 'float' and 'decimal.Decimal'" the first time it ran against
# this float64 source column (F-008). Registration does not coerce dtype, so the cast has to
# happen here, in data prep, same as the available_at tz-localization above.
for col in ("adj_close", "return", "trade_volume"):
    df[col] = df[col].map(lambda v: Decimal(str(v)) if pd.notna(v) else None)

df.to_parquet(OUT, index=False)
print(len(df), df["available_at"].min(), df["available_at"].max())
