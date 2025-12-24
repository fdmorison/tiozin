from typing import Any

from tiozin.model.registries import LineageRegistry


class NoOpLineageRegistry(LineageRegistry):
    """
    No-op lineage registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when lineage tracking is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: str = "latest") -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
