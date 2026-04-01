from __future__ import annotations

from typing import TYPE_CHECKING

import requests
import wrapt

from tiozin.utils import human_join

from .enums import EmitLevel
from .model import LineageRunEvent

if TYPE_CHECKING:
    from .registry import LineageRegistry


class LineageRegistryProxy(wrapt.ObjectProxy):
    """
    Proxy that provides fire-and-forget lineage emission with emit-level control.

    All lineage operations are executed in a best-effort manner: errors raised during
    event construction or emission are caught and logged as warnings, never propagated,
    ensuring lineage does not interrupt job execution.

    Emission is conditional and only occurs when the configured emit level matches
    the current execution context (job or step).
    """

    @property
    def _registry(self) -> LineageRegistry:
        return self.__wrapped__

    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        return self._registry.get(identifier, version)

    def register(self, identifier: str, value: LineageRunEvent) -> None:
        self._safe_emit(self._registry.register, identifier, value)

    def start(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.start, inputs, outputs)

    def complete(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.complete, inputs, outputs)

    def fail(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.fail, inputs, outputs)

    def abort(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.abort, inputs, outputs)

    def _should_emit(self) -> bool:
        from tiozin.api import Context

        context = Context.current(required=False)
        if context is None:
            self._registry.warning("Skipping lineage emission: no active execution context")
            return False

        return (
            self._registry.emit_level == EmitLevel.ALL
            or (self._registry.emit_level == EmitLevel.JOB and context.is_job)
            or (self._registry.emit_level == EmitLevel.STEP and context.is_step)
        )

    def _safe_emit(self, fn, *args, **kwargs) -> None:
        if not self._should_emit():
            return

        try:
            fn(*args, **kwargs)
        except requests.HTTPError as e:
            content = e.response.json() or {}
            message = content.get("message", "Lineage emission failed")
            details = content.get("errors", [])
            self._registry.warning(f"{message}: {human_join(details)}")
        except Exception as e:
            self._registry.warning(f"Lineage emission failed: {e}")

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
