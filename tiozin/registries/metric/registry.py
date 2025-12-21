from ...model.registry import Registry


class MetricRegistry(Registry):
    """
    Manages metrics and indicators.

    Storage-agnostic contract for metric backends (like Prometheus, InfluxDB, or Datadog).
    Available in Context for custom metrics from Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
