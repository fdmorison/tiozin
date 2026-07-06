from datetime import datetime

from typing_extensions import Unpack

from tiozin.api import Batch, BatchRegistry
from tiozin.api.typehint import ResourceKwargs


class NoOpBatchRegistry(BatchRegistry):
    """
    No-op batch registry.

    Does nothing. Returns the received batch for all transitions, None for
    `get_latest`, and an empty list for the backlog and history.
    Useful for testing or when batch tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def register(self, batch: Batch) -> Batch:
        return batch

    def begin(self, batch: Batch) -> Batch:
        return batch

    def commit(self, batch: Batch) -> Batch:
        return batch

    def fail(self, batch: Batch) -> Batch:
        return batch

    def cancel(self, batch: Batch) -> Batch:
        return batch

    def quarantine(self, batch: Batch) -> Batch:
        return batch

    def replay(self, batch: Batch) -> Batch:
        return batch

    def get(self, id: str, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        return None

    def get_latest(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        return None

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        return []

    def get_history(
        self, limit: int, since: datetime, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        return []
