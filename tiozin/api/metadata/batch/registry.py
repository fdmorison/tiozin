from abc import abstractmethod

from typing_extensions import Unpack

from tiozin import config
from tiozin.compose import tioproxy
from tiozin.utils import default

from ...typehint import ResourceKwargs
from ..registry import Registry
from .model import Batch
from .proxy import BatchRegistryProxy


@tioproxy(BatchRegistryProxy)
class BatchRegistry(Registry[Batch]):
    """
    Storage-agnostic registry for pipeline batches.

    The registry persists and manages the lifecycle of batches represented by `Batch` objects.
    Implementations may use REST backends, relational databases, key-value stores, or table
    formats such as Iceberg or DuckLake.

    Besides status transitions, the registry exposes derived views over the collection of
    batches, such as backlogs and history.

    Attributes:
        retries:
            Maximum number of times a failed batch is retried before being
            escalated to QUARANTINED.
    """

    def __init__(self, retries: int = None, **options) -> None:
        super().__init__(**options)
        self.retries = default(retries, config.default_batch_retries)

    @abstractmethod
    def register(self, batch: Batch) -> Batch:
        """
        Creates a new batch.

        Raises:
            BatchAlreadyExistsError: If a batch with the same natural key already exists.
        """

    @abstractmethod
    def begin(self, batch: Batch) -> Batch:
        """Transitions the batch to RUNNING and persists it."""

    @abstractmethod
    def commit(self, batch: Batch) -> Batch:
        """Transitions the batch to SUCCEEDED and persists it."""

    @abstractmethod
    def fail(self, batch: Batch) -> Batch:
        """Transitions the batch to FAILED and persists it."""

    @abstractmethod
    def cancel(self, batch: Batch) -> Batch:
        """Transitions the batch to CANCELED and persists it."""

    @abstractmethod
    def quarantine(self, batch: Batch) -> Batch:
        """Transitions the batch to QUARANTINED and persists it."""

    @abstractmethod
    def replay(self, batch: Batch) -> Batch:
        """Transitions the batch to PENDING and persists it."""

    @abstractmethod
    def get_latest(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        """
        Returns the most recently registered batch for the resource by created_at, or
        `None` if none exists.

        The returned batch may have any status. Callers are responsible for inspecting
        the status and deciding whether to retry, wait, or advance to the next batch.
        """

    @abstractmethod
    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        """
        Returns the backlog for the resource.

        The backlog contains all batches currently awaiting processing.
        """

    @abstractmethod
    def get_history(self, limit: int, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        """
        Returns the most recently registered batches for the resource, regardless of
        status, ordered by created_at descending.

        Useful for debugging backlog progression over time.
        """
