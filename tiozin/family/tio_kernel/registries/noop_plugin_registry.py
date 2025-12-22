from typing import Any

from tiozin.model.registry import Registry


class NoOpPluginRegistry(Registry):
    """
    No-op registry implementation.

    This registry performs no operations and always returns None for retrievals.
    Useful as a placeholder or default when settings management is not required
    or for testing purposes.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get(self, identifier: str, failfast: bool = False) -> None:
        return None

    def register(self, identifier: str, value: Any) -> None:
        return None
