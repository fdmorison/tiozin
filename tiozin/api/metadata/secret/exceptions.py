from __future__ import annotations

from typing import Self

from tiozin.exceptions.base import TiozinUsageError
from tiozin.exceptions.categories import TiozinNotFoundError


class SecretError(TiozinUsageError):
    """
    Base exception for secret registry errors.
    """

    message = "An error occurred while retrieving a secret."


class SecretNotFoundError(SecretError, TiozinNotFoundError):
    """
    Raised when a secret cannot be found in the registry.
    """

    message = "Secret '{name}' not found."

    def __init__(self, name: str) -> None:
        super().__init__(name=name)

    @classmethod
    def raise_if(cls, condition: bool, name: str) -> type[Self]:
        if condition:
            raise cls(name)
        return cls
