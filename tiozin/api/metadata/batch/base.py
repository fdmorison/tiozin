from abc import abstractmethod
from datetime import datetime

from typing_extensions import Unpack

from tiozin import config
from tiozin.compose import tioproxy
from tiozin.utils import default, utcnow

from ...typehint import ResourceKwargs
from ..registry import Registry
from .model import Batch
from .proxy import BatchRegistryProxy


@tioproxy(BatchRegistryProxy)
class BatchRegistry(Registry[Batch]):
    """
    Storage-agnostic registry for pipeline batches.

    A batch registry manages the lifecycle of `Batch` objects and exposes operations to register,
    transition, and query batches associated with a resource.

    Transitions are orchestrated here, in methods shared by every backend: each verb guards
    against no-op transitions, mutates the batch, and delegates recording it to
    `register_transition`. Backends implement the storage primitives and the queries, and may
    override a verb at their own risk.

    Implementations may be backed by relational databases, REST services, key-value stores, or
    open table formats.

    Attributes:
        retries:
            Maximum number of retry attempts before the batch is quarantined.
    """

    def __init__(self, retries: int = None, **options) -> None:
        super().__init__(**options)
        self.retries = default(retries, config.default_batch_retries)

    @abstractmethod
    def register(self, batch: Batch) -> Batch:
        """
        Creates a new batch.

        Raises:
            BatchAlreadyExistsError: If another batch with the same natural key already exists.
        """

    @abstractmethod
    def register_transition(self, batch: Batch) -> Batch:
        """
        Records that a batch's status has just changed.

        The batch's new status is authoritative, so implementations may react
        to it, for example by moving the batch to a different partition once
        it becomes terminal.

        Raises:
            BatchNotFoundError: If the batch does not exist.
        """

    @abstractmethod
    def get(self, id: str, **resource: Unpack[ResourceKwargs]) -> Batch:
        """
        Returns the batch identified by `id` within the resource.

        Raises:
            BatchNotFoundError: If the batch does not exist.
        """

    @abstractmethod
    def get_latest(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        """
        Returns the most recently registered batch for the resource.

        Returns:
            The latest batch, or `None` if no batches have been registered for the resource.
        """

    @abstractmethod
    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        """
        Returns batches awaiting for processing.

        The backlog should include only batches in the PENDING, RUNNING, or FAILED states.
        """

    @abstractmethod
    def get_history(
        self, limit: int, since: datetime, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        """
        Returns recently registered batches for the resource.

        Results are ordered by `created_at` in descending order and include
        batches of any status. Only batches registered at or after `since`
        are considered. Up to `limit` batches are returned.
        """

    def begin(self, batch: Batch, **attributes) -> Batch:
        """
        Transitions the batch to RUNNING, or skips if it already is.
        """
        if batch.status.is_running():
            self.warning("Batch %s is already running, so there is nothing to begin.", batch)
            return batch

        batch.status = batch.status.to_running(failfast=self.failfast)
        batch.attributes |= attributes
        batch.updated_at = utcnow()
        return self.register_transition(batch)

    def commit(self, batch: Batch, **attributes) -> Batch:
        """
        Transitions the batch to SUCCEEDED, or skips if it already is.
        """
        if batch.status.is_succeeded():
            self.warning("Batch %s has already succeeded, so there is nothing to commit.", batch)
            return batch

        batch.status = batch.status.to_succeeded(failfast=self.failfast)
        batch.attributes |= attributes
        batch.updated_at = utcnow()
        return self.register_transition(batch)

    def fail(self, batch: Batch, **attributes) -> Batch:
        """
        Transitions the batch to FAILED, or skips if it already is.

        The failure count is incremented on every failure. Once it exceeds the
        retry limit, the batch is quarantined instead of failed.
        """
        if batch.status.is_failed():
            self.warning("Batch %s has already failed, so there is nothing to fail.", batch)
            return batch

        batch.failure_count += 1
        batch.status = batch.status.to_failed(failfast=self.failfast)

        if batch.failure_count > self.retries:
            return self.quarantine(batch, **attributes)

        batch.attributes |= attributes
        batch.updated_at = utcnow()
        return self.register_transition(batch)

    def quarantine(self, batch: Batch, **attributes) -> Batch:
        """
        Transitions the batch to QUARANTINED, or skips if it already is.
        """
        if batch.status.is_quarantined():
            self.warning(
                "Batch %s is already quarantined, so there is nothing to quarantine.", batch
            )
            return batch

        batch.status = batch.status.to_quarantined(failfast=self.failfast)
        batch.attributes |= attributes
        batch.updated_at = utcnow()
        return self.register_transition(batch)

    def cancel(self, batch: Batch, **attributes) -> Batch:
        """
        Transitions the batch to CANCELED, or skips if it already is.
        """
        if batch.status.is_canceled():
            self.warning("Batch %s is already canceled, so there is nothing to cancel.", batch)
            return batch

        batch.status = batch.status.to_canceled(failfast=self.failfast)
        batch.attributes |= attributes
        batch.updated_at = utcnow()
        return self.register_transition(batch)

    def replay(self, batch: Batch, **attributes) -> Batch:
        """
        Transitions the batch back to PENDING, or skips if it already is.

        The failure count is reset so the batch becomes eligible for a fresh round of retries.
        """
        if batch.status.is_pending():
            self.warning("Batch %s is already pending, so there is nothing to replay.", batch)
            return batch

        batch.status = batch.status.to_pending(failfast=self.failfast)
        batch.attributes |= attributes
        batch.failure_count = 0
        batch.updated_at = utcnow()
        return self.register_transition(batch)
