from tiozin import LineageEvent, LineageRegistry


class LineageRegistryStub(LineageRegistry):
    def __init__(self, **kwargs):
        super().__init__(location="stub://lineage", **kwargs)
        self.captured_event: LineageEvent = None

    def emit(self, value: LineageEvent) -> None:
        self.captured_event = value


class FailingLineageRegistryStub(LineageRegistry):
    def __init__(self, **kwargs):
        super().__init__(location="stub://lineage", **kwargs)
        self.emit_called = False

    def emit(self, event: LineageEvent) -> None:
        self.emit_called = True
        raise RuntimeError("backend unavailable")
