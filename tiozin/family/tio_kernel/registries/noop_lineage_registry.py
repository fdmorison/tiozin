from tiozin.api import LineageEvent, LineageRegistry


class NoOpLineageRegistry(LineageRegistry):
    """
    No-op lineage registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when lineage tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def get(self, identifier: str = None, version: str = "latest") -> LineageEvent:
        return None

    def emit(self, _identifier: str, _value: LineageEvent) -> None:
        return None
