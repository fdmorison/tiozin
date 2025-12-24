from typing import Any, Optional

from tiozin.model.registries import MetricRegistry


class NoOpMetricRegistry(MetricRegistry):
    """
    No-op metric registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: Optional[str] = None) -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
