from tiozin.api import StateRegistry


class NoOpStateRegistry(StateRegistry):
    """
    No-op state registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when state tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)
