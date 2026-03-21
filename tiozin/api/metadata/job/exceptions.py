from __future__ import annotations

from typing import Self

from tiozin.exceptions.base import TiozinUsageError
from tiozin.exceptions.categories import TiozinConflictError, TiozinNotFoundError


class JobError(TiozinUsageError):
    """
    Base exception for job-related errors.
    """

    message = "An error occurred while processing the job."


class JobNotFoundError(JobError, TiozinNotFoundError):
    """
    Raised when a job cannot be found.
    """

    message = "Could not find a job matching `{name}`."

    def __init__(self, message: str = None, *, name: str = None) -> None:
        super().__init__(message, name=name)

    @classmethod
    def raise_if(cls, condition: bool, message: str = None, *, name: str = None) -> type[Self]:
        if condition:
            raise cls(message, name=name)
        return cls


class JobAlreadyExistsError(JobError, TiozinConflictError):
    """
    Raised when a job with the same name already exists.
    """

    message = "The job `{name}` already exists."

    def __init__(self, message: str = None, *, name: str) -> None:
        super().__init__(
            message,
            name=name,
        )

    @classmethod
    def raise_if(cls, condition: bool, message: str = None, *, name: str) -> type[Self]:
        if condition:
            raise cls(message, name=name)
        return cls
