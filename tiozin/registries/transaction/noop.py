from typing import Any

from ...model.registry import Registry


class NoOpTransactionRegistry(Registry):
    """
    No-op transaction registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when transaction tracking is disabled.
    """

    def __init__(self) -> None:
        super().__init__()

    def get(self, name: str) -> None:
        return None

    def register(self, name: str, value: Any) -> None:
        return None
