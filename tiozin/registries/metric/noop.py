from typing import Any

from ..registry import MetadataRegistry


class NoOpMetricRegistry(MetadataRegistry):
    """
    No-op metric registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self) -> None:
        super().__init__()

    def get(self, name: str) -> None:
        return None

    def register(self, name: str, value: Any) -> None:
        return None
