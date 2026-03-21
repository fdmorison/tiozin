from abc import abstractmethod

from tiozin.api.registry import Registry

from .model import RunEvent, RunState


class LineageRegistry(Registry[RunEvent]):
    """
    Emits OpenLineage run events during pipeline execution.

    `register()` is the generic emit — subclasses implement it to send events
    to a lineage backend (e.g. Marquez, OpenMetadata).

    Convenience methods per run state delegate to `register()`, reading job
    identity and run ID from the active execution context:

        registry.start()
        registry.complete(outputs=["finance.orders"])
        registry.fail()
    """

    @abstractmethod
    def get(self, identifier: str = None, version: str = None) -> RunEvent:
        """Retrieve lineage events for a job or run."""

    @abstractmethod
    def register(self, identifier: str, value: RunEvent) -> None:
        """Emit a run event."""

    def start(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = RunEvent.from_context(
            self.context,
            RunState.START,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def complete(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = RunEvent.from_context(
            self.context,
            RunState.COMPLETE,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def fail(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = RunEvent.from_context(
            self.context,
            RunState.FAIL,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)

    def abort(self, inputs: list[str] = None, outputs: list[str] = None) -> None:
        event = RunEvent.from_context(
            self.context,
            RunState.ABORT,
            inputs,
            outputs,
        )
        self.register(event.run_id, event)
