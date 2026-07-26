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
    def get_frontier(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        """
        Returns the batch at the frontier of processed data for the resource.

        This method is primarily intended for jobs with `BacklogPolicy.INCREMENTAL`,
        where the frontier determines whether a new batch should be created or an
        existing one should be resumed.

        The frontier is the latest batch whose processing window still determines
        the pipeline's progress. This includes batches that have already advanced
        the frontier (such as SUCCEEDED or QUARANTINED) and batches that must be
        resolved before progress can continue (such as PENDING, RUNNING, or FAILED).

        CANCELED batches must never be returned, since an abandoned window should not
        advance the frontier.
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
