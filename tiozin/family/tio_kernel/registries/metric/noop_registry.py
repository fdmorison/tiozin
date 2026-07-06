from tiozin.api import MetricRegistry


class NoOpMetricRegistry(MetricRegistry):
    """
    No-op metric registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)
