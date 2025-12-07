from typing import Any

from ..registry import MetadataRegistry


class NoOpSchemaRegistry(MetadataRegistry):
    """
    No-op registry implementation.

    This registry performs no operations and always returns None for retrievals.
    Useful as a placeholder or default when settings management is not required
    or for testing purposes.
    """

    def __init__(self) -> None:
        super().__init__()

    def get(self, name: str) -> None:
        return None

    def register(self, name: str, value: Any) -> None:
        return None
