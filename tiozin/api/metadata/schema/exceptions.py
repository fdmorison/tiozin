from __future__ import annotations

from typing import Self

from tiozin.exceptions.categories import TiozinInputError, TiozinNotFoundError


class SchemaError(TiozinInputError):
    """
    Raised when a schema is invalid or an operation cannot be applied to it.
    """

    message = "The schema is invalid."


class SchemaViolationError(SchemaError, TiozinInputError):
    """
    Raised when an input violates one or more schema constraints.
    """

    message = "The input violates one or more schema constraints."


class SchemaNotFoundError(SchemaError, TiozinNotFoundError):
    """
    Raised when a schema subject cannot be found in the registry.
    """

    message = "Schema `{subject}` not found in the registry."

    def __init__(self, subject: str) -> None:
        super().__init__(subject=subject)

    @classmethod
    def raise_if(cls, condition: bool, subject: str) -> type[Self]:
        if condition:
            raise cls(subject)
        return cls


class PropertyNotFoundError(SchemaError, TiozinNotFoundError):
    """
    Raised when no property exists at the given path.
    """

    message = "Property `{path}` not found."

    def __init__(self, path: object) -> None:
        super().__init__(path=path)
