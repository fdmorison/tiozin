from typing import Any

from tiozin.model.registry import Registry


class NoOpSettingRegistry(Registry):
    """
    No-op setting registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when settings management is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, failfast: bool = False) -> None:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
