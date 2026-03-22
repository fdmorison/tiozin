from tiozin.api import LineageRegistry, LineageRunEvent


class NoOpLineageRegistry(LineageRegistry):
    """
    No-op lineage registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when lineage tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def get(self, identifier: str = None, version: str = "latest") -> LineageRunEvent:
        return None

    def register(self, _identifier: str, _value: LineageRunEvent) -> None:
        return None
