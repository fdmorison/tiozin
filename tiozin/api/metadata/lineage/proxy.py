from __future__ import annotations

from typing import TYPE_CHECKING

import requests
import wrapt

from tiozin.utils import human_join

from .enums import EmitLevel
from .model import LineageEvent

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

    def get(self, identifier: str = None, version: str = None) -> LineageEvent:
        return self._registry.get(identifier, version)

    def register(self, identifier: str, value: LineageEvent) -> None:
        self._safe_emit(self._registry.register, identifier, value)

    def start(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.start, inputs, outputs)

    def complete(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.complete, inputs, outputs)

    def fail(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.fail, inputs, outputs)

    def abort(self, inputs=None, outputs=None) -> None:
        self._safe_emit(self._registry.abort, inputs, outputs)

    def _safe_emit(self, emit, *args, **kwargs) -> None:
        """
        Proxy entrypoint for lineage emission.

        Enforces conditional emission and ensures all errors are swallowed,
        making lineage strictly best-effort.
        """
        from tiozin.api import Context

        context = Context.current(required=False)
        emit_level = self._registry.emit_level

        if context is None:
            self._registry.warning("Skipping lineage emission: no active execution context")
            return False

        should_emit = (
            emit_level == EmitLevel.ALL
            or (emit_level == EmitLevel.JOB and context.is_job)
            or (emit_level == EmitLevel.STEP and context.is_step)
        )

        if not should_emit:
            return None

        try:
            emit(*args, **kwargs)
        except requests.HTTPError as e:
            content = e.response.json() or {}
            message = content.get("message", "Lineage emission failed")
            details = content.get("errors", [])
            self._registry.warning(f"{message}: {human_join(details)}")
        except Exception as e:
            self._registry.warning(f"Lineage emission failed: {e}")

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
