from tiozin.api import LineageEvent, LineageRegistry


class NoOpLineageRegistry(LineageRegistry):
    """
    No-op lineage registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when lineage tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def emit(self, event: LineageEvent) -> None:
        return None
