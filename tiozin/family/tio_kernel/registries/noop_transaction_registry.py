from typing import Any, Optional

from tiozin.model.registries import TransactionRegistry


class NoOpTransactionRegistry(TransactionRegistry):
    """
    No-op transaction registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when transaction tracking is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: Optional[str] = None) -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
