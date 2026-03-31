import types
from typing import TYPE_CHECKING, Any

import requests
import wrapt

from tiozin.utils import human_join

if TYPE_CHECKING:
    from tiozin import Registry


class LineageRegistryProxy(wrapt.ObjectProxy):
    """
    Proxy that makes lineage emission fire-and-forget.

    Catches any exception raised during a lineage call and logs a warning
    instead of propagating it. A lineage backend failure must never abort a job.
    """

    def __getattr__(self, name: str):
        registry: Registry = self.__wrapped__

        attr = getattr(registry, name)
        if not isinstance(attr, types.MethodType):
            return attr

        def safe_call(*args, **kwargs) -> Any | None:
            try:
                return attr(*args, **kwargs)
            except requests.HTTPError as e:
                content = e.response.json() or {}
                message = content.get("message", "Failed to emit event")
                details = content.get("errors", [])
                registry.warning(f"{message}: {human_join(details)}")
            except Exception as e:
                registry.warning(f"Failed to emit event: {e}")

        return safe_call
