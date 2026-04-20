from tiozin.api import TransactionRegistry


class NoOpTransactionRegistry(TransactionRegistry):
    """
    No-op transaction registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when transaction tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)
