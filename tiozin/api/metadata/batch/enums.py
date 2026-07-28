from enum import auto
from typing import ClassVar, Self

from tiozin import config
from tiozin.api.enums import LowerEnum
from tiozin.utils import default

from .exceptions import BatchTransitionError


class BacklogPolicy(LowerEnum):
    """
    Defines how a job participates in batch backlogs.

    A backlog policy is a cohesive set of rules that governs how a job handles
    batches in its backlog, defining the process governing batch creation, execution, and lifecycle.

    Attributes:
        STATELESS:
            The job runs without batches.

        INCREMENTAL:
            The job produces and consumes its own batches, advancing the processing window
            after each successful execution.

        CONSUMER:
            The job consumes batches produced by external sources, such as manually created
            batches or upstream jobs.
    """

    STATELESS = (
        auto(),
        dict(
            produces_backlog=False,
            consumes_backlog=False,
        ),
    )
    INCREMENTAL = (
        auto(),
        dict(
            produces_backlog=True,
            consumes_backlog=True,
        ),
    )
    CONSUMER = (
        auto(),
        dict(
            produces_backlog=False,
            consumes_backlog=True,
        ),
    )

    produces_backlog: bool
    consumes_backlog: bool

    def __new__(cls, value: str, traits: dict[str, bool]) -> Self:
        member = str.__new__(cls, value)
        member._value_ = value
        vars(member).update(traits)
        return member

    @classmethod
    def default(cls, backlog: Self = None) -> Self:
        """
        Resolves an optional backlog policy, falling back to the configured
        default when absent.
        """
        return cls(default(backlog, config.default_backlog_policy))


class BatchStatus(LowerEnum):
    """
    Lifecycle states of a batch, forming a state machine.

    PENDING is the initial status. The state advances through RUNNING and, on
    success, reaches SUCCEEDED. From there it can be replayed back to PENDING.

    Every status is either terminal or runnable: parked until replayed, or
    able to enter execution.

    PENDING -> RUNNING -> SUCCEEDED
        Happy path: a queued batch runs and completes successfully.

    PENDING -> RUNNING -> FAILED * N -> QUARANTINED
        A running batch that fails is retried via RUNNING. After exhausting
        the retry limit, it is escalated to QUARANTINED instead of retried again.

    FAILED -> QUARANTINED
        A batch can still be quarantined by manual or administrative action, such as an operator
        using the CLI. This is a separate path, not part of automatic retry exhaustion.

    PENDING|RUNNING -> CANCELED
        A batch can be abandoned while queued or while running.

    Any status -> PENDING (replay)
        Every status can be replayed back to PENDING, including RUNNING (an
        interrupted execution) and FAILED (restart retries from 0).

    Attributes:
        PENDING:
            Queued and awaiting the start of processing.
        RUNNING:
            Actively being processed.
        FAILED:
            Processing failed. Retried via RUNNING until retries are exhausted, then
            escalated to QUARANTINED.
        SUCCEEDED:
            Processing completed successfully.
        QUARANTINED:
            Definitively failed or isolated by business logic. Requires manual replay.
        CANCELED:
            Abandoned by manual action, whether queued or in progress.
    """

    PENDING = auto()
    RUNNING = auto()
    FAILED = auto()

    SUCCEEDED = auto()
    QUARANTINED = auto()
    CANCELED = auto()

    __state_machine__: ClassVar[dict[Self, set[Self]]] = {
        PENDING: {PENDING, RUNNING, CANCELED},
        RUNNING: {RUNNING, PENDING, SUCCEEDED, FAILED, CANCELED, QUARANTINED},
        FAILED: {PENDING, RUNNING, QUARANTINED},
        SUCCEEDED: {PENDING},
        CANCELED: {PENDING},
        QUARANTINED: {PENDING},
    }

    def can_transition_to(self, target: Self) -> bool:
        """
        Checks if the transition to the target state is valid.
        """
        return target in self.__state_machine__[self]

    def transition_to(self, target: Self, failfast: bool = True) -> Self:
        """
        Transitions to target, validating against the allowed transitions.

        Args:
            target: The desired target state.
            failfast: If True, raises an exception on invalid transitions.

        Returns:
            Target state if allowed, otherwise current state (when failfast=False).

        Raises:
            BatchTransitionError: If transition is invalid (when failfast=True).
        """
        if self.can_transition_to(target):
            return target

        if failfast:
            raise BatchTransitionError(source=self, target=target)

        return self

    def is_terminal(self) -> bool:
        """
        Returns True if a batch in this status can no longer enter execution.

        Terminal statuses are parked: nothing happens to them until they are
        explicitly replayed back to PENDING. Always the negation of
        `is_operational`.
        """
        return not self.can_transition_to(self.RUNNING)

    def is_operational(self) -> bool:
        """
        Returns True if a batch in this status can enter or re-enter execution.

        Covers every path into RUNNING: the first run of a pending batch, the
        retry of a failed one, and the resumption of an interrupted one.
        Always the negation of `is_terminal`.
        """
        return self.can_transition_to(self.RUNNING)

    def is_replayable(self) -> bool:
        """
        Returns True if a batch in this status can be replayed back to PENDING.
        """
        return self.can_transition_to(self.PENDING)

    def is_done(self) -> bool:
        return not self.is_terminal()

    def is_todo(self) -> bool:
        return not self.is_operational()

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
