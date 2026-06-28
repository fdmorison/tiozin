from __future__ import annotations

from typing import TYPE_CHECKING

from tiozin.exceptions.base import TiozinUsageError
from tiozin.exceptions.categories import TiozinConflictError

if TYPE_CHECKING:
    from .model import State
    from .status import BatchStatus


class StateError(TiozinUsageError):
    """
    Base exception for state-related errors.
    """

    message = "An error occurred while processing the state."


class StateTransitionError(StateError, TiozinConflictError):
    """
    Raised when a state transition is not allowed by the state machine.
    """

    message = "Invalid transition: {source} -> {target}."

    def __init__(self, message: str = None, *, source: BatchStatus, target: BatchStatus) -> None:
        super().__init__(message, source=source, target=target)


class StateAlreadyExistsError(StateError, TiozinConflictError):
    """
    Raised when attempting to register a state that already exists.
    """

    message = "The state '{state}' already exists."

    def __init__(self, message: str = None, *, state: State) -> None:
        super().__init__(message, state=state)
