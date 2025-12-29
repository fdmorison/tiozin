from typing import Any, Optional

from tiozin.api.registries import SchemaRegistry


class NoOpSchemaRegistry(SchemaRegistry):
    """
    No-op schema registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when schema validation is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: Optional[str] = None) -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
