"""Prepare the execution-input (venue) table from adjusted_prices.parquet.

is_tradable: the source has `is_trading_halt` and `is_admin_issue` booleans. Neither the
dataset schema nor any doc in this testbed says whether an admin-issue (관리종목) name is
still executable — that is domain knowledge about KRX admin-issue trading rules that the
framework does not supply. Chosen here, conservatively, as: tradable iff not halted and not
under admin-issue designation. Recorded as friction (see FRICTION.md).

trade_at reuses the same close+15:30 Asia/Seoul instant used for the dataset's available_at,
since both describe the same session close.
"""

from decimal import Decimal

import pandas as pd

SRC = "../data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet"
OUT = "workspace/prepared_data/venue.parquet"

df = pd.read_parquet(
    SRC,
    columns=["date", "ticker", "adj_close", "is_trading_halt", "is_admin_issue"],
)
UNIVERSE = ["A000020", "A000040", "A000050", "A000060", "A000070"]
df = df[df["ticker"].isin(UNIVERSE) & (df["date"] >= "2015-09-01") & (df["date"] <= "2016-12-31")].copy()

df["trade_at"] = df["date"].dt.tz_localize("Asia/Seoul") + pd.Timedelta(hours=15, minutes=30)
df["is_tradable"] = ~(df["is_trading_halt"].fillna(False) | df["is_admin_issue"].fillna(False))
df["adj_close"] = df["adj_close"].map(lambda v: Decimal(str(v)) if pd.notna(v) else None)
df = df.drop(columns=["date", "is_trading_halt", "is_admin_issue"])
df.to_parquet(OUT, index=False)
print(len(df), df["is_tradable"].mean())
