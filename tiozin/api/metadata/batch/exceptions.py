from __future__ import annotations

from typing import TYPE_CHECKING

from tiozin.exceptions.base import TiozinUsageError
from tiozin.exceptions.categories import TiozinConflictError, TiozinNotFoundError

if TYPE_CHECKING:
    from .model import Batch
    from .status import BatchStatus


class BatchError(TiozinUsageError):
    """
    Base exception for batch-related errors.
    """

    message = "An error occurred while processing the batch."


class BatchTransitionError(BatchError, TiozinConflictError):
    """
    Raised when a status transition is not allowed by the batch state machine.
    """

    message = "Invalid transition: {source} -> {target}."

    def __init__(self, message: str = None, *, source: BatchStatus, target: BatchStatus) -> None:
        super().__init__(message, source=source, target=target)


class BatchAlreadyExistsError(BatchError, TiozinConflictError):
    """
    Raised when attempting to register a batch that already exists.
    """

    message = "The batch '{batch}' already exists."

    def __init__(self, message: str = None, *, batch: Batch) -> None:
        super().__init__(message, batch=batch)


class BatchNotFoundError(BatchError, TiozinNotFoundError):
    """
    Raised when attempting to update a batch that does not exist.
    """

    message = "The batch '{batch}' was not found."

    def __init__(self, message: str = None, *, batch: Batch) -> None:
        super().__init__(message, batch=batch)
