from tiozin import LineageRunEvent
from tiozin.api.metadata.lineage.registry import LineageRegistry


class LineageRegistryStub(LineageRegistry):
    def __init__(self):
        super().__init__(location="stub://lineage")
        self.captured_identifier = None
        self.captured_event: LineageRunEvent = None

    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        return None

    def register(self, identifier: str, value: LineageRunEvent) -> None:
        self.captured_identifier = identifier
        self.captured_event = value


class FailingLineageRegistryStub(LineageRegistry):
    def __init__(self):
        super().__init__(location="stub://lineage")
        self.register_called = False

    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        return None

    def register(self, identifier: str, value: LineageRunEvent) -> None:
        self.register_called = True
        raise RuntimeError("backend unavailable")
