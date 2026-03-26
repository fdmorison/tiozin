from abc import abstractmethod

from tiozin.compose import tioproxy

from ..registry import Registry
from .model import LineageDataset, LineageRunEvent, LineageRunEventType
from .proxy import LineageRegistryProxy


@tioproxy(LineageRegistryProxy)
class LineageRegistry(Registry[LineageRunEvent]):
    """
    Emits lineage run events during pipeline execution.

    `register()` is the generic emit — subclasses implement it to send events
    to a lineage backend (e.g. Marquez, OpenMetadata).

    Convenience methods per run state delegate to `register()`, reading job
    identity and run ID from the active execution context:

        registry.start()
        registry.complete(outputs=["finance.orders"])
        registry.fail()

    See Also:
        `OpenLineage Naming Spec <https://openlineage.io/docs/spec/naming/>`_
    """

    @abstractmethod
    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        """Retrieve a lineage event by run ID or job name."""

    @abstractmethod
    def register(self, identifier: str, value: LineageRunEvent) -> None:
        """Emit a run event."""

    def start(
        self, inputs: list[LineageDataset] = None, outputs: list[LineageDataset] = None
    ) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.START,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def complete(
        self, inputs: list[LineageDataset] = None, outputs: list[LineageDataset] = None
    ) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.COMPLETE,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def fail(
        self, inputs: list[LineageDataset] = None, outputs: list[LineageDataset] = None
    ) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.FAIL,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def abort(
        self, inputs: list[LineageDataset] = None, outputs: list[LineageDataset] = None
    ) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.ABORT,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)
