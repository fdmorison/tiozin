from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import wrapt
from typing_extensions import Unpack

from tiozin import config
from tiozin.api.typehint import ResourceKwargs
from tiozin.utils import default, utcnow

if TYPE_CHECKING:
    from .model import Batch
    from .registry import BatchRegistry

VERSION_KEY = "__framework_version"
VERSION_VALUE = f"v{config.app_version}"


class BatchRegistryProxy(wrapt.ObjectProxy):
    """
    Proxy that enforces state machine transitions before delegating to the
    wrapped registry.

    Registry implementations receive a fully mutated Batch and are
    responsible only for persistence. Transition validation happens here
    regardless of whether the registry is called through Batch methods or
    directly.
    """

    def register(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        batch.attributes |= {VERSION_KEY: VERSION_VALUE}
        return registry.register(batch)

    def begin(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_running():
            registry.warning("The batch was already RUNNING.")

        batch.status = batch.status.to_running(failfast=registry.failfast)
        batch.updated_at = utcnow()
        batch.attributes |= {VERSION_KEY: VERSION_VALUE}
        return registry.begin(batch)

    def commit(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_succeeded():
            registry.warning("The batch was already SUCCEEDED.")

        batch.status = batch.status.to_succeeded(failfast=registry.failfast)
        batch.updated_at = utcnow()
        batch.attributes |= {VERSION_KEY: VERSION_VALUE}
        return registry.commit(batch)

    def fail(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.failure_count > registry.retries:
            return self.quarantine(batch)

        if batch.status.is_failed():
            registry.warning("The batch was already FAILED.")

        batch.status = batch.status.to_failed(failfast=registry.failfast)
        batch.updated_at = utcnow()
        batch.attributes |= {VERSION_KEY: VERSION_VALUE}
        return registry.fail(batch)

    def cancel(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_canceled():
            registry.warning("The batch was already CANCELED.")

        batch.status = batch.status.to_canceled(failfast=registry.failfast)
        batch.updated_at = utcnow()
        batch.attributes |= {VERSION_KEY: VERSION_VALUE}
        return registry.cancel(batch)

    def quarantine(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_quarantined():
            registry.warning("The batch was already QUARANTINED.")

        batch.status = batch.status.to_quarantined(failfast=registry.failfast)
        batch.updated_at = utcnow()
        batch.attributes |= {VERSION_KEY: VERSION_VALUE}
        return registry.quarantine(batch)

    def replay(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_pending():
            registry.warning("The batch was already PENDING.")

        batch.status = batch.status.to_pending(failfast=registry.failfast)
        batch.failure_count = 0
        batch.updated_at = utcnow()
        batch.attributes |= {VERSION_KEY: VERSION_VALUE}
        return registry.replay(batch)

    def get_history(
        self, limit: int = None, since: datetime = None, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        registry: BatchRegistry = self.__wrapped__
        limit = default(limit, config.default_batch_history_limit)
        since = default(since, utcnow() - timedelta(days=config.default_batch_history_since_days))
        return registry.get_history(limit, since, **resource)
