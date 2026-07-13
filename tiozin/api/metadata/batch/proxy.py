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

    Resolves core defaults before delegating to the wrapped registry.

    This is an internal implementation detail. Callers rely on `BatchRegistry`
    and should not interact with this proxy directly.
    """

    def get_history(
        self, limit: int = None, since: datetime = None, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        registry: BatchRegistry = self.__wrapped__
        limit = default(limit, config.default_batch_history_limit)
        since = default(since, utcnow() - timedelta(days=config.default_batch_history_since_days))
        return registry.get_history(limit, since, **resource)
