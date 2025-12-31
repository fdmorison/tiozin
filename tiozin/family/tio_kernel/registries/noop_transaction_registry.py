from typing import Any

from tiozin.api.registries import TransactionRegistry


class NoOpTransactionRegistry(TransactionRegistry):
    """
    No-op transaction registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when transaction tracking is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: str | None = None) -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
