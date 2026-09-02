"""A DataModel that derives one column from declared observations."""

from __future__ import annotations

from decimal import Decimal

from vqapr.public import DataModel, DataRequirement, RowsLookback

MODEL_ID = "krx_prices_model"
DATASET_ID = "krx_adjusted_prices"
LOOKBACK = 1


class KrxPricesModel(DataModel):
    """Emits one derived value per instrument at each materialization time."""

    def requirements(self):
        return (
            DataRequirement.of(
                MODEL_ID,
                DATASET_ID,
                fields=("close",),
                lookback=RowsLookback(LOOKBACK),
            ),
        )

    def compute(self, context):
        rows = context.window.observations(self.requirements()[0]).rows
        history: dict[str, list[Decimal]] = {}
        for row in rows:
            value = row["close"]
            if value is not None:
                history.setdefault(str(row["instrument"]), []).append(Decimal(str(value)))

        # ---- the one line to change -------------------------------------------------------
        # Trailing return over the declared lookback.
        derived = {
            name: values[-1] / values[0] - Decimal(1)
            for name, values in history.items()
            if len(values) == LOOKBACK
        }
        # -----------------------------------------------------------------------------------

        return [
            {"instrument": name, "value": value}
            for name, value in sorted(derived.items())
        ]
