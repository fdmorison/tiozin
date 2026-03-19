from typing import Any

from tiozin.api import SettingRegistry


class NoOpSettingRegistry(SettingRegistry):
    """
    No-op setting registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when settings management is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def get(self, identifier: str = None, version: str | None = None) -> Any:
        return None

    def register(self, identifier: str = None, value: Any = None) -> None:
        return None
