from typing import TYPE_CHECKING

import requests
import wrapt

from tiozin.utils import human_join

from .enums import EmitLevel
from .model import LineageRunEvent

if TYPE_CHECKING:
    from tiozin.api.metadata.lineage.registry import LineageRegistry


class LineageRegistryProxy(wrapt.ObjectProxy):
    """
    Proxy that enables fire-and-forget lineage emission with emit-level control.

    Emission failures are caught and logged as warnings, never propagated, ensuring
    that lineage does not interrupt job execution.

    Events are emitted in `register()` only when the configured emit level matches
    the current execution context (job or step).
    """

    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        registry: LineageRegistry = self.__wrapped__
        return registry.get(identifier, version)

    def register(self, identifier: str, value: LineageRunEvent) -> None:
        from tiozin.api import Context

        registry: LineageRegistry = self.__wrapped__
        context = Context.current(required=False)
        emit_level = registry.emit_level

        if context is None:
            registry.warning("No active context, lineage event ignored")
            return

        if emit_level == EmitLevel.JOB and not context.is_job:
            return

        if emit_level == EmitLevel.STEP and not context.is_step:
            return

        try:
            registry.register(identifier, value)
        except requests.HTTPError as e:
            content = e.response.json() or {}
            message = content.get("message", "Failed to emit lineage event")
            details = content.get("errors", [])
            registry.warning(f"[{identifier}] {message}: {human_join(details)}")
        except Exception as e:
            registry.warning(f"[{identifier}] Failed to emit lineage event: {e}")

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
