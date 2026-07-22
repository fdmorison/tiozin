from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import wrapt
from typing_extensions import Unpack

from tiozin import config
from tiozin.api.typehint import ResourceKwargs
from tiozin.utils import default, utcnow

if TYPE_CHECKING:
    from .base import BatchRegistry
    from .model import Batch


class BatchRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps BatchRegistry implementations with core-level batch handling.

    Resolves core defaults before delegating to the wrapped registry, and stamps every
    batch it returns with a reference back to itself, so batch verbs can reach their
    registry directly instead of depending on an active context.

    This is an internal implementation detail. Callers rely on `BatchRegistry`
    and should not interact with this proxy directly.
    """

    @property
    def _registry(self) -> BatchRegistry:
        return self.__wrapped__

    def _attach_registry(self, *batches: Batch | None) -> None:
        for batch in filter(None, batches):
            batch._registry_ref = batch._registry_ref or self

    def register(self, batch: Batch) -> Batch:
        result = self._registry.register(batch)
        self._attach_registry(result, batch)
        return result or batch

    def register_transition(self, batch: Batch) -> Batch:
        batch.updated_at = utcnow()
        result = self._registry.register_transition(batch)
        self._attach_registry(result, batch)
        return result or batch

    def get(self, id: str, **resource: Unpack[ResourceKwargs]) -> Batch:
        batch = self._registry.get(id, **resource)
        self._attach_registry(batch)
        return batch

    def get_latest(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        batch = self._registry.get_latest(**resource)
        self._attach_registry(batch)
        return batch

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        batches = self._registry.get_backlog(**resource)
        self._attach_registry(*batches)
        return batches

    def get_history(
        self, limit: int = None, since: datetime = None, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        limit = default(limit, config.default_batch_history_limit)
        since = default(since, utcnow() - timedelta(days=config.default_batch_history_since_days))
        batches = self._registry.get_history(limit, since, **resource)
        self._attach_registry(*batches)
        return batches
