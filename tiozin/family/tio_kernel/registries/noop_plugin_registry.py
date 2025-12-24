from typing import Any, Optional

from tiozin.model.registries import PluginRegistry


class NoOpPluginRegistry(PluginRegistry):
    """
    No-op registry implementation.

    This registry performs no operations and always returns None for retrievals.
    Useful as a placeholder or default when settings management is not required
    or for testing purposes.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, version: Optional[str] = None) -> Any:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
