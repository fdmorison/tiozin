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

    A batch registry persists and queries `Batch` objects associated with a
    resource.

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
    def get_board(
        self, limit: int, since: datetime, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        """
        Returns the full board of batches for the resource, across every status.

        Results are ordered by `created_at` in descending order. Only batches
        registered at or after `since` are considered. Up to `limit` batches
        are returned.
        """
