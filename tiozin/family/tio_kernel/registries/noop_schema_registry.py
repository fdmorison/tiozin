from typing import Any

from ....model.registry import Registry


class NoOpSchemaRegistry(Registry):
    """
    No-op schema registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when schema validation is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, failfast: bool = False) -> None:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
