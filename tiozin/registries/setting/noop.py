from typing import Any

from ...model.registry import Registry


class NoOpSettingRegistry(Registry):
    """
    No-op setting registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when settings management is disabled.
    """

    def __init__(self) -> None:
        super().__init__()

    def get(self, name: str) -> None:
        return None

    def register(self, name: str, value: Any) -> None:
        return None
