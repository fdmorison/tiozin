from abc import abstractmethod
from datetime import datetime

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

    A batch registry persists `Batch` objects and exposes operations for
    registering, updating, and querying batches associated with a resource.

    Implementations may use relational databases, REST services, key-value
    stores, or open table formats.

    Methods that mutate an existing batch may raise `BatchNotFoundError`.
    Registering an already existing batch raises `BatchAlreadyExistsError`.

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
            BatchAlreadyExistsError: If another batch with the same natural key already exists.
        """

    @abstractmethod
    def begin(self, batch: Batch) -> Batch:
        """
        Persists the batch in the RUNNING state.

        Raises:
            BatchNotFoundError: If the batch does not exist.
        """

    @abstractmethod
    def commit(self, batch: Batch) -> Batch:
        """
        Persists the batch in the SUCCEEDED state.

        Raises:
            BatchNotFoundError: If the batch does not exist.
        """

    @abstractmethod
    def fail(self, batch: Batch) -> Batch:
        """
        Persists the batch in the FAILED state.

        Raises:
            BatchNotFoundError: If the batch does not exist.
        """

    @abstractmethod
    def cancel(self, batch: Batch) -> Batch:
        """
        Persists the batch in the CANCELED state.

        Raises:
            BatchNotFoundError: If the batch does not exist.
        """

    @abstractmethod
    def quarantine(self, batch: Batch) -> Batch:
        """
        Persists the batch in the QUARANTINED state.

        Raises:
            BatchNotFoundError: If the batch does not exist.
        """

    @abstractmethod
    def replay(self, batch: Batch) -> Batch:
        """
        Persists the batch in the PENDING state.

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
            The latest batch, or `None` if no batches have been registered
            for the resource.
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
