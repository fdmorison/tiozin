from abc import abstractmethod

from tiozin import config
from tiozin.api.runtime.dataset import Dataset
from tiozin.compose import tioproxy

from ..registry import Registry
from .enums import EmitLevel, LineageRunEventType
from .model import LineageRunEvent
from .proxy import LineageRegistryProxy


@tioproxy(LineageRegistryProxy)
class LineageRegistry(Registry[LineageRunEvent]):
    """
    Emits lineage run events during pipeline execution.

    `register()` is implemented by subclasses to send events to a lineage backend.
    Convenience methods (e.g. `start()`, `complete()`, `fail()`) delegate to it
    using the active execution context.

    Attributes:
        emit_level: Controls which events are emitted (`JOB`, `STEP`, `ALL`).
    """

    def __init__(self, emit_level: EmitLevel = None, **options) -> None:
        super().__init__(**options)
        self.emit_level = EmitLevel(emit_level or config.default_lineage_emit_level)

    @abstractmethod
    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        """Retrieve a lineage event by run ID or job name."""

    @abstractmethod
    def register(self, identifier: str, value: LineageRunEvent) -> None:
        """Emit a run event."""

    def start(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.START,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def complete(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.COMPLETE,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def fail(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.FAIL,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def abort(self, inputs: list[Dataset] = None, outputs: list[Dataset] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.ABORT,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)
