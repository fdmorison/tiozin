from enum import StrEnum, auto
from typing import Any

from ..exceptions import AlreadyFinishedException, AlreadyRunningException


class Status(StrEnum):
    """
    Represents the status of an app, job, pipeline, or transaction.

    Values:
        PENDING   - waiting to start or in the process of starting
        RUNNING   - currently executing
        SUCCESS   - finished successfully
        FAILURE   - finished with an error
        FINISHED  - finished, either successfully or with failure
    """

    PENDING = auto()
    RUNNING = auto()
    CANCELED = auto()
    SUCCESS = auto()
    FAILURE = auto()
    FINISHED = auto()

    def is_pending(self) -> bool:
        return self is Status.PENDING

    def is_running(self) -> bool:
        return self is Status.RUNNING

    def is_canceled(self) -> bool:
        return self is Status.CANCELED

    def is_success(self) -> bool:
        return self is Status.SUCCESS

    def is_failure(self) -> bool:
        return self is Status.FAILURE

    def is_runnable(self) -> bool:
        return self in {
            Status.PENDING,
            Status.FAILURE,
        }

    def is_finished(self) -> bool:
        return self in {
            Status.SUCCESS,
            Status.FAILURE,
            Status.FINISHED,
            Status.CANCELED,
        }

    def set_running(self, resource: Any = None, failfast: bool = True) -> Status:
        """
        Transition to RUNNING if allowed, optionally raising on conflicts.

        Raises:
            AlreadyRunningException if already running and failfast=True
            AlreadyFinishedException if the resource is already finished
        """
        if self.is_running():
            if failfast:
                raise AlreadyRunningException(resource)
            return self

        if self.is_runnable():
            return Status.RUNNING

        raise AlreadyFinishedException(resource)

    def set_finished(self, resource: Any = None, failfast: bool = True) -> Status:
        """
        Transition to FINISHED, optionally raising if already finished.

        Raises:
            AlreadyFinishedException if the resource is already finished and failfast=True
        """
        if self.is_finished():
            if failfast:
                raise AlreadyFinishedException(resource)
            return self
        return Status.FINISHED

    def set_success(self, resource: Any = None, failfast: bool = True) -> Status:
        """
        Transition to SUCCESS if allowed.

        Raises:
            AlreadyFinishedException if the resource is already finished and failfast=True
        """
        if self.is_finished():
            if failfast:
                raise AlreadyFinishedException(resource)
            return self
        return Status.SUCCESS

    def set_failure(self, resource: Any = None, failfast: bool = True) -> Status:
        """
        Transition to FAILURE if allowed.

        Raises:
            AlreadyFinishedException if the resource is already finished and failfast=True
        """
        if self.is_finished():
            if failfast:
                raise AlreadyFinishedException(resource)
            return self
        return Status.FAILURE

    def set_canceled(self, resource: Any = None, failfast: bool = True) -> "Status":
        """
        Transition to CANCELED if allowed.

        Raises:
            AlreadyFinishedException if the resource is already finished and failfast=True
        """
        if self.is_finished():
            if failfast:
                raise AlreadyFinishedException(resource)
            return self
        return Status.CANCELED
