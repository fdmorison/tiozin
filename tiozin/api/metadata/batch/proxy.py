from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

if TYPE_CHECKING:
    from .model import Batch
    from .registry import BatchRegistry


class BatchRegistryProxy(wrapt.ObjectProxy):
    """
    Proxy that enforces state machine transitions before delegating to the
    wrapped registry.

    Registry implementations receive a fully mutated Batch and are
    responsible only for persistence. Transition validation happens here
    regardless of whether the registry is called through Batch methods or
    directly.
    """

    def begin(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_running():
            registry.warning("The batch was already RUNNING.")

        batch.status = batch.status.to_running(failfast=registry.failfast)
        return registry.begin(batch)

    def commit(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_succeeded():
            registry.warning("The batch was already SUCCEEDED.")

        batch.status = batch.status.to_succeeded(failfast=registry.failfast)
        return registry.commit(batch)

    def fail(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.failure_count > registry.retries:
            return self.quarantine(batch)

        if batch.status.is_failed():
            registry.warning("The batch was already FAILED.")

        batch.status = batch.status.to_failed(failfast=registry.failfast)
        return registry.fail(batch)

    def cancel(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_canceled():
            registry.warning("The batch was already CANCELED.")

        batch.status = batch.status.to_canceled(failfast=registry.failfast)
        return registry.cancel(batch)

    def quarantine(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_quarantined():
            registry.warning("The batch was already QUARANTINED.")

        batch.status = batch.status.to_quarantined(failfast=registry.failfast)
        return registry.quarantine(batch)

    def replay(self, batch: Batch) -> Batch:
        registry: BatchRegistry = self.__wrapped__

        if batch.status.is_pending():
            registry.warning("The batch was already PENDING.")

        batch.status = batch.status.to_pending(failfast=registry.failfast)
        return registry.replay(batch)
