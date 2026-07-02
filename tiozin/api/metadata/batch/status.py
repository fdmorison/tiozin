from enum import auto
from typing import ClassVar, Self

from tiozin.api.enums import LowerEnum
from tiozin.api.metadata.batch.exceptions import BatchTransitionError


class BatchStatus(LowerEnum):
    """
    Lifecycle states of a batch, forming a state machine.

    PENDING is the initial state. The batch advances through RUNNING and, on
    success, reaches SUCCEEDED. From there it can be replayed back to PENDING.

    On failure, the batch enters FAILED and is automatically retried via
    RUNNING. After exhausting retry attempts it is escalated to QUARANTINED.
    Batches can also be abandoned at any point via CANCELED. Both QUARANTINED
    and CANCELED support replay by returning to PENDING.

    Attributes:
        PENDING:
            Queued and awaiting the start of processing.
        RUNNING:
            Actively being processed.
        SUCCEEDED:
            Processing completed successfully.
        FAILED:
            Processing failed. Eligible for retry via RUNNING, or escalated to
            QUARANTINED after exhausting retry attempts.
        CANCELED:
            Abandoned by manual action or business logic. Can be replayed.
        QUARANTINED:
            Definitively failed or isolated by business logic. Requires manual
            intervention before replaying.
    """

    PENDING = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    CANCELED = auto()
    QUARANTINED = auto()

    __transitions__: ClassVar[dict[Self, set[Self]]] = {
        PENDING: {RUNNING, CANCELED},
        RUNNING: {SUCCEEDED, FAILED, QUARANTINED},
        FAILED: {RUNNING, QUARANTINED},
        SUCCEEDED: {PENDING},
        CANCELED: {PENDING},
        QUARANTINED: {PENDING},
    }

    def can_transition_to(self, target: Self) -> bool:
        """Checks if the transition to the target state is valid."""
        return target is self or target in self.__transitions__[self]

    def transition_to(self, target: Self, failfast: bool = True) -> Self:
        """
        Transitions to target, validating against the allowed transitions.

        Args:
            target: The desired target state.
            failfast: If True, raises an exception on invalid transitions.

        Returns:
            Target state if allowed, otherwise current state (when failfast=False).

        Raises:
            ValueError: If transition is invalid (when failfast=True).
        """
        if self.can_transition_to(target):
            return target

        if failfast:
            raise BatchTransitionError(source=self, target=target)

        return self

    def is_terminal(self) -> bool:
        """Returns True if the batch is no longer progressing and can only be replayed."""
        return self.__transitions__[self] <= {self.PENDING}

    def is_retriable(self) -> bool:
        """Returns True if this state can transition back to RUNNING for a retry."""
        return self.RUNNING in self.__transitions__[self]

    def is_pending(self) -> bool:
        return self is self.PENDING

    def is_running(self) -> bool:
        return self is self.RUNNING

    def is_succeeded(self) -> bool:
        return self is self.SUCCEEDED

    def is_failed(self) -> bool:
        return self is self.FAILED

    def is_canceled(self) -> bool:
        return self is self.CANCELED

    def is_quarantined(self) -> bool:
        return self is self.QUARANTINED

    def to_pending(self, failfast: bool = True) -> Self:
        return self.transition_to(self.PENDING, failfast)

    def to_running(self, failfast: bool = True) -> Self:
        return self.transition_to(self.RUNNING, failfast)

    def to_succeeded(self, failfast: bool = True) -> Self:
        return self.transition_to(self.SUCCEEDED, failfast)

    def to_failed(self, failfast: bool = True) -> Self:
        return self.transition_to(self.FAILED, failfast)

    def to_canceled(self, failfast: bool = True) -> Self:
        return self.transition_to(self.CANCELED, failfast)

    def to_quarantined(self, failfast: bool = True) -> Self:
        return self.transition_to(self.QUARANTINED, failfast)
