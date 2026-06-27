from __future__ import annotations

from tiozin.exceptions.base import TiozinUsageError
from tiozin.exceptions.categories import TiozinConflictError


class StateError(TiozinUsageError):
    """
    Base exception for state-related errors.
    """

    message = "An error occurred while processing the state."


class StateTransitionError(StateError, TiozinConflictError):
    """
    Raised when a state transition is not allowed by the state machine.
    """

    message = "Invalid transition: {source} -> {target}. Valid: {valid}."

    def __init__(self, message: str = None, *, source: str, target: str, valid: str) -> None:
        super().__init__(message, source=source, target=target, valid=valid)
