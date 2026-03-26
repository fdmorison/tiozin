import types
from typing import TYPE_CHECKING, Any

import wrapt

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
            except Exception:
                registry.exception(f"Lineage event `{name}` failed.")

        return safe_call
