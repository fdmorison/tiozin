from enum import StrEnum, auto
from typing import ClassVar, Self


class AppStatus(StrEnum):
    """
    Represents the lifecycle states of a batch-oriented application.

    This status reflects both the application lifecycle and the outcome
    of the last executed job. A job failure does not imply that the
    application itself is unusable.
    """

    CREATED = auto()
    # Application instance was created but not initialized yet.
    # No resources were allocated and no setup was executed.

    BOOTING = auto()
    # Application is initializing, no job can be executed yet.

    WAITING = auto()
    # Application is fully initialized and idle, ready to execute jobs.

    RUNNING = auto()
    # A job is currently running.

    SUCCESS = auto()
    # The last executed job finished successfully.
    # The application remains ready to run new jobs.

    FAILURE = auto()
    # The last executed job failed.
    # The application is still ready and may retry or execute another job.

    CANCELED = auto()
    # A running job was explicitly canceled (e.g., via shutdown signal).
    # The application is finished and will not execute new jobs.

    COMPLETED = auto()
    # Application finished its lifecycle without a running job
    # (e.g., shutdown before execution or normal termination).

    __transitions__: ClassVar[dict[Self, set[Self]]] = {
        CREATED: {COMPLETED, BOOTING},
        BOOTING: {COMPLETED, CANCELED, FAILURE, WAITING},
        WAITING: {COMPLETED, RUNNING},
        RUNNING: {CANCELED, SUCCESS, FAILURE},
        SUCCESS: {COMPLETED, RUNNING},
        FAILURE: {COMPLETED, RUNNING},
        CANCELED: {},
        COMPLETED: {},
    }

    def can_transition_to(self, target: Self) -> bool:
        """Checks if the transition to the target state is valid."""
        return target in self.__transitions__[self]

    def transition_to(self, target: Self, failfast: bool = True) -> Self:
        """
        Performs a safe transition to target state.

        Args:
            target: The desired target state
            failfast: If True, raises exception on invalid transitions

        Returns:
            Target state if allowed, otherwise current state (when failfast=False)

        Raises:
            ValueError: If transition is invalid (when failfast=True)
        """
        if not self.can_transition_to(target):
            if failfast:
                valid_transitions = ", ".join(self.__transitions__[self])
                raise ValueError(
                    f"Invalid transition: {self} -> {target}. "
                    f"Expected: {valid_transitions or 'none'}"
                )
            return self
        return target

    def set_booting(self, failfast: bool = True) -> Self:
        return self.transition_to(self.BOOTING, failfast)

    def set_waiting(self, failfast: bool = True) -> Self:
        return self.transition_to(self.WAITING, failfast)

    def set_running(self, failfast: bool = True) -> Self:
        return self.transition_to(self.RUNNING, failfast)

    def set_success(self, failfast: bool = True) -> Self:
        return self.transition_to(self.SUCCESS, failfast)

    def set_failure(self, failfast: bool = True) -> Self:
        return self.transition_to(self.FAILURE, failfast)

    def set_canceled(self, failfast: bool = True) -> Self:
        return self.transition_to(self.CANCELED, failfast)

    def set_completed(self, failfast: bool = True) -> Self:
        return self.transition_to(self.COMPLETED, failfast)

    def is_created(self) -> bool:
        return self is self.CREATED

    def is_booting(self) -> bool:
        return self is self.BOOTING

    def is_waiting(self) -> bool:
        return self is self.WAITING

    def is_running(self) -> bool:
        return self is self.RUNNING

    def is_success(self) -> bool:
        return self is self.SUCCESS

    def is_failure(self) -> bool:
        return self is self.FAILURE

    def is_canceled(self) -> bool:
        return self is self.CANCELED

    def is_completed(self) -> bool:
        return self is self.COMPLETED

    def is_healthy(self) -> bool:
        return self not in {self.FAILURE, self.CANCELED, self.COMPLETED}

    def is_ready(self) -> bool:
        return self in {self.WAITING, self.RUNNING, self.SUCCESS, self.FAILURE}

    def is_idle(self) -> bool:
        return self in {self.WAITING, self.SUCCESS, self.FAILURE}

    def is_job_finished(self) -> bool:
        return self in {self.SUCCESS, self.FAILURE, self.CANCELED, self.COMPLETED}

    def is_app_finished(self) -> bool:
        return self in {self.CANCELED, self.COMPLETED}
