"""A DataModel that derives one column from declared observations."""

from __future__ import annotations

from decimal import Decimal

from vqapr.public import DataModel, DataRequirement, RowsLookback

MODEL_ID = "f_krx_signal"
DATASET_ID = "f_krx_prices"
LOOKBACK = 2


class FKrxSignal(DataModel):
    """Emits one derived value per instrument at each materialization time."""

    def requirements(self):
        return (
            DataRequirement.of(
                MODEL_ID,
                DATASET_ID,
                fields=("return",),
                lookback=RowsLookback(LOOKBACK),
            ),
        )

    def compute(self, context):
        rows = context.window.observations(self.requirements()[0]).rows
        history: dict[str, list[Decimal]] = {}
        for row in rows:
            value = row["return"]
            if value is not None:
                # `Decimal(str(v))` rather than `Decimal(v)`: a parquet float64 column arrives as
                # `float`, and money compared or subtracted across `float` and `Decimal` raises.
                # Going through `str` also avoids inheriting the binary float's exact expansion,
                # so 0.1 stays 0.1 instead of becoming 0.1000000000000000055511151231257827.
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
