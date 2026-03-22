from abc import abstractmethod

from tiozin.api.registry import Registry
from tiozin.compose import tioproxy
from tiozin.compose.proxies.lineage import LineageRegistryProxy

from .model import LineageRunEvent, LineageRunEventType


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

    def start(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.START,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def complete(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.COMPLETE,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def fail(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.FAIL,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def abort(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = LineageRunEvent.from_context(
            self.context,
            LineageRunEventType.ABORT,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)
