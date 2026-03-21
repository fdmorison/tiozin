from __future__ import annotations

from typing import Self

from tiozin.exceptions.base import TiozinUsageError
from tiozin.exceptions.categories import TiozinConflictError, TiozinNotFoundError
from tiozin.utils import human_join


class PluginError(TiozinUsageError):
    """
    Base exception for plugin discovery, resolution, and loading errors.
    """

    message = "The Tiozin plugin discovery, resolution or load failed."


class PluginNotFoundError(PluginError, TiozinNotFoundError):
    """
    Raised when a Tiozin plugin cannot be found for the given name.
    """

    message = "Tiozin `{name}` not found."

    def __init__(self, *, name: str = None) -> None:
        super().__init__(name=name)

    @classmethod
    def raise_if(cls, condition: bool, *, name: str = None) -> type[Self]:
        if condition:
            raise cls(name=name)
        return cls


class PluginConflictError(PluginError, TiozinConflictError):
    """
    Raised when a Tiozin name matches multiple registered plugins.
    """

    message = (
        "The Tiozin name '{name}' matches multiple registered Tiozin plugins. "
        "Available provider-qualified options are: {candidates}. "
        "You can disambiguate by specifying the provider-qualified name "
        "or the fully qualified Python class path."
    )

    def __init__(self, *, name: str = None, candidates: list[str] = None) -> None:
        super().__init__(
            name=name,
            candidates=human_join(candidates or []),
        )

    @classmethod
    def raise_if(
        cls,
        condition: bool,
        *,
        name: str = None,
        candidates: list[str] = None,
    ) -> type[Self]:
        if condition:
            raise cls(name=name, candidates=candidates)
        return cls
