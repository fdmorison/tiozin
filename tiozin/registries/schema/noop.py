from typing import Any

from ..registry import MetadataRegistry


class NoOpSchemaRegistry(MetadataRegistry):
    """
    No-op schema registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when schema validation is disabled.
    """

    def __init__(self) -> None:
        super().__init__()

    def get(self, name: str) -> None:
        return None

    def register(self, name: str, value: Any) -> None:
        return None
