"""Small KRX venue for the bounded real-data slice."""

from vqapr.public import KrxExchange


class SmallKrxExchange(KrxExchange):
    def __init__(self) -> None:
        super().__init__(
            listings=("A000020", "A000040", "A000050"),
            exchange_id="krx_exchange",
        )
