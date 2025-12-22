from typing import Any

from tiozin.model.registry import Registry


class NoOpMetricRegistry(Registry):
    """
    No-op metric registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when metric tracking is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, failfast: bool = False) -> None:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
