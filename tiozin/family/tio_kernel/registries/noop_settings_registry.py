from typing import Any, Optional

from tiozin.api.registries import SettingRegistry


class NoOpSettingRegistry(SettingRegistry):
    """
    No-op setting registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when settings management is disabled.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: Optional[str] = None) -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
