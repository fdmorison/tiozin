from tiozin.api.metadata.metric.registry import MetricRegistry


class MetricRegistryStub(MetricRegistry):
    def __init__(self):
        super().__init__(location="stub://metric")

    def get(self, identifier: str = None, version: str = None) -> None:
        return None

    def register(self, identifier: str, value: object) -> None:
        pass
