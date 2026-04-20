from __future__ import annotations

from typing import TYPE_CHECKING

import requests
import wrapt

from tiozin.utils import human_join

from .enums import EmitLevel

if TYPE_CHECKING:
    from .registry import LineageRegistry

EVENT_METHODS = frozenset(
    {
        "emit",
        "run_started",
        "run_completed",
        "run_failed",
        "run_aborted",
        "dataset_updated",
        "job_updated",
    }
)


class LineageRegistryProxy(wrapt.ObjectProxy):
    """
    Proxy that wraps lineage emission methods with fire-and-forget safeness
    and emit-level control.

    Only methods defined in `_EMISSION_METHODS` are intercepted.
    All other attributes are passed through unmodified.
    """

    @property
    def _registry(self) -> LineageRegistry:
        return self.__wrapped__

    def __getattr__(self, name: str):
        attr = getattr(self.__wrapped__, name)

        if name in EVENT_METHODS:

            def _safe(*args, **kwargs) -> None:
                self._safe_emit(attr, *args, **kwargs)

            return _safe

        return attr

    def _safe_emit(self, emit, *args, **kwargs) -> None:
        from tiozin.api import Context

        context = Context.current(required=False)
        emit_level = self._registry.emit_level

        if context is None:
            self._registry.warning("Skipping lineage emission: no active execution context")
            return

        should_emit = (
            emit_level == EmitLevel.ALL
            or (emit_level == EmitLevel.JOB and context.is_job)
            or (emit_level == EmitLevel.STEP and context.is_step)
        )

        if not should_emit:
            return

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
