from tiozin import LineageEvent
from tiozin.api.metadata.lineage.registry import LineageRegistry


class LineageRegistryStub(LineageRegistry):
    def __init__(self, **kwargs):
        super().__init__(location="stub://lineage", **kwargs)
        self.captured_identifier = None
        self.captured_event: LineageEvent = None

    def get(self, identifier: str = None, version: str = None) -> LineageEvent:
        return None

    def register(self, identifier: str, value: LineageEvent) -> None:
        self.captured_identifier = identifier
        self.captured_event = value


class FailingLineageRegistryStub(LineageRegistry):
    def __init__(self, **kwargs):
        super().__init__(location="stub://lineage", **kwargs)
        self.register_called = False

    def get(self, identifier: str = None, version: str = None) -> LineageEvent:
        return None

    def register(self, identifier: str, value: LineageEvent) -> None:
        self.register_called = True
        raise RuntimeError("backend unavailable")
