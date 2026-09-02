"""Exchange component — hand-written, no `vqapr new` scaffold exists for this kind.

`vqapr new` offers {datamodel,strategy,dataset,execution-input,run-spec} only. The run-spec
template requires `exchange: <component_id>`, and `vqapr list components` never showed an
exchange kind either, so the fifth required component kind has no scaffold path at all (see
FRICTION F-005). Built from `vqapr.public.AcademicExchange` + `TradeRule`, discovered by reading
`help()` on `vqapr.public` symbols since no doc named which Exchange to use.

First attempt used a module-level `AcademicExchange(...)` instance bound to `object_name`; that
failed registration with `'AcademicExchange' object is not callable`, so component loading calls
`object_name()` — it must be a zero-arg constructible class, not a pre-built instance.
"""

from __future__ import annotations

from decimal import Decimal

from vqapr.public import AcademicExchange, TradeRule

INSTRUMENTS = ("A000020", "A000040", "A000050", "A000060", "A000070")


def _listings() -> dict[str, TradeRule]:
    return {
        instrument_id: TradeRule(
            instrument_id=instrument_id,
            quantity_step=Decimal("1"),
            minimum_quantity=Decimal("1"),
            fractional_allowed=False,
        )
        for instrument_id in INSTRUMENTS
    }


class KoreanEquityExchange(AcademicExchange):
    """Zero-friction academic execution for the five-name dev universe."""

    def __init__(self) -> None:
        super().__init__(listings=_listings(), exchange_id="korean_equity_academic")
