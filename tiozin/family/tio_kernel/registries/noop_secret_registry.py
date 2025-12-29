from typing import Any, Optional

from tiozin.api.registries import SecretRegistry


class NoOpSecretRegistry(SecretRegistry):
    """
    No-op secret registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when secret management is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: Optional[str] = None) -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
