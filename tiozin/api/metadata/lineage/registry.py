from abc import abstractmethod

from tiozin import config
from tiozin.compose import tioproxy

from ...runtime.dataset import Dataset
from ..registry import Registry
from .enums import EmitLevel, RunEventType
from .model import LineageEvent, LineageRunEvent
from .proxy import LineageRegistryProxy


@tioproxy(LineageRegistryProxy)
class LineageRegistry(Registry[LineageEvent]):
    """
    Lineage registry interface.

    Defines a contract for emitting lineage events during pipeline execution.
    Subclasses implement `emit()` to send events to a backend.

    Convenience methods build events from the active context and delegate to `emit()`.

    Attributes:
        emit_level: Controls which events are emitted (`JOB`, `STEP`, `ALL`).
    """

    def __init__(self, emit_level: EmitLevel = None, **options) -> None:
        super().__init__(**options)
        self.emit_level = EmitLevel(emit_level or config.default_lineage_emit_level)

    @abstractmethod
    def emit(self, event: LineageEvent) -> None:
        """Send a lineage event to the backend."""

    def run_started(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(self.context, RunEventType.START, inputs, outputs)
        self.emit(event)

    def run_completed(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(self.context, RunEventType.COMPLETE, inputs, outputs)
        self.emit(event)

    def run_failed(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(self.context, RunEventType.FAIL, inputs, outputs)
        self.emit(event)

    def run_aborted(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(self.context, RunEventType.ABORT, inputs, outputs)
        self.emit(event)
