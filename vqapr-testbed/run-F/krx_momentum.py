"""A long-only cross-sectional Strategy.

Registering this file as written succeeds and running it produces a result. Change the marked
signal line to express a different view.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from vqapr.public import (
    Budget,
    DataRequirement,
    EconomicPortfolioIntent,
    IntentSourceRef,
    NoDecision,
    PortfolioDirection,
    PortfolioTarget,
    RowsLookback,
    StrategyModel,
)

STRATEGY_ID = "krx_momentum"
DATASET_ID = "krx_prices"
LOOKBACK = 3
"""Rows of history each name needs. A five-day return needs six observations, not five."""

INVESTED = Decimal("0.9")
"""Fraction of NAV held in names; the remainder stays in cash."""

BUDGET = Budget(
    PortfolioDirection.LONG_ONLY,
    Decimal("0"),
    Decimal("1"),
    Decimal("0"),
    Decimal("1"),
)


class KrxMomentum(StrategyModel):
    """Ranks the cross-section and holds the selected names in equal weight."""

    def requirements(self):
        return (
            DataRequirement.of(
                STRATEGY_ID,
                DATASET_ID,
                fields=("adj_close",),
                lookback=RowsLookback(LOOKBACK),
            ),
        )

    def on_occurrence(self, context):
        rows = context.window.observations(self.requirements()[0]).rows
        history: dict[str, list[Decimal]] = {}
        for row in rows:
            value = row["adj_close"]
            if value is not None:
                # `Decimal(str(v))` rather than `Decimal(v)`: a parquet float64 column arrives as
                # `float`, and money compared or subtracted across `float` and `Decimal` raises.
                # Going through `str` also avoids inheriting the binary float's exact expansion,
                # so 0.1 stays 0.1 instead of becoming 0.1000000000000000055511151231257827.
                history.setdefault(str(row["instrument"]), []).append(Decimal(str(value)))

        # A name is eligible when the declared lookback is fully present. A newly listed name has
        # too few rows and a delisted name stops appearing, so both leave the cross-section here
        # without the Strategy ever asking whether they are tradable.
        eligible = {
            name: values for name, values in history.items() if len(values) == LOOKBACK
        }
        if len(eligible) < 2:
            return NoDecision("a cross-sectional view needs at least two names with full history")

        # ---- the one line to change -------------------------------------------------------
        # Three-observation momentum: the strongest recent return becomes the largest score.
        scores = {
            name: values[-1] / values[0] - Decimal(1) for name, values in eligible.items()
        }
        # -----------------------------------------------------------------------------------

        selected = [name for name, score in scores.items() if score > 0]
        if not selected:
            return NoDecision("no name scored above zero")

        weight = INVESTED / Decimal(len(selected))
        targets = tuple(
            PortfolioTarget(name, weight=weight) for name in sorted(selected)
        )
        return EconomicPortfolioIntent(
            uuid5(NAMESPACE_URL, f"{STRATEGY_ID}/{context.occurrence.occurrence_id}"),
            STRATEGY_ID,
            targets,
            Decimal(1) - weight * Decimal(len(selected)),
            BUDGET,
            _source_refs(context),
            context.account.version,
            None,
        )


def _source_refs(context):
    """Exactly the sources this callback read, in first-read order.

    The Flow recomputes this from the window and refuses an intent whose provenance disagrees,
    so it must be derived from the accesses rather than declared.
    """
    seen: dict[str, str] = {}
    for access in context.window.accesses:
        seen.setdefault(access.source_id, access.source_digest)
    return tuple(IntentSourceRef(source, digest) for source, digest in seen.items())
