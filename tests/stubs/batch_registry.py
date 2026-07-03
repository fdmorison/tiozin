from typing_extensions import Unpack

from tiozin.api import Batch, BatchRegistry
from tiozin.api.typehint import ResourceKwargs


class BatchRegistryStub(BatchRegistry):
    def __init__(self):
        super().__init__(location="stub://batch")

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

    def get_latest(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        return None

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        return []

    def get_history(self, limit: int, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        return []
