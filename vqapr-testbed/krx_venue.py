"""Exchange component: whole-share KRX venue, no price-limit regime.

The venue table (`krx_venue` execution input) carries only a close price, so this venue is built
with `price_limits=False` -- the switch documented on `krx_rules` for exactly this case.
"""

from __future__ import annotations

from vqapr.public import InstrumentKind, KrxExchange, krx_rules

INSTRUMENTS = ("A000020", "A000660", "A005930")


def build() -> KrxExchange:
    universe = {name: InstrumentKind.STOCK for name in INSTRUMENTS}
    listings, instruments = krx_rules(universe, price_limits=False)
    return KrxExchange(listings, exchange_id="krx_venue", instruments=instruments)
