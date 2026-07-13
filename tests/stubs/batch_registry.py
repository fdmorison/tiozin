from datetime import datetime

from typing_extensions import Unpack

from tiozin import Batch, BatchRegistry
from tiozin.api.typehint import ResourceKwargs


class BatchRegistryStub(BatchRegistry):
    def __init__(self, retries: int = None, failfast: bool = None):
        super().__init__(location="stub://batch", retries=retries, failfast=failfast)

    def register(self, batch: Batch) -> Batch:
        return batch

    def register_transition(self, batch: Batch) -> Batch:
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
