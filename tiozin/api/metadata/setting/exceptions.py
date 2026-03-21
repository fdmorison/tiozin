from __future__ import annotations

from typing import Self

from tiozin.exceptions.base import TiozinUsageError
from tiozin.exceptions.categories import TiozinNotFoundError


class SettingsError(TiozinUsageError):
    """
    Base exception for settings registry errors.
    """

    message = "An error occurred while loading settings."


class SettingsNotFoundError(SettingsError, TiozinNotFoundError):
    """
    Raised when settings cannot be found at the specified path.
    """

    message = "Settings not found: '{location}'."

    def __init__(self, location: str) -> None:
        super().__init__(location=location)

    @classmethod
    def raise_if(cls, condition: bool, location: str) -> type[Self]:
        if condition:
            raise cls(location)
        return cls
