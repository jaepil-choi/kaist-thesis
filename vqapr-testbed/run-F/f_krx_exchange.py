"""KRX exchange component for the bounded two-name run."""

from vqapr.public import KrxExchange


class FKrxExchange(KrxExchange):
    """Configured KRX exchange that the component loader can construct."""

    def __init__(self) -> None:
        super().__init__(
            listings=["A000020", "A000040"],
            exchange_id="f_krx_exchange",
        )
