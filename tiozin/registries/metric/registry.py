from ..registry import MetadataRegistry


class MetricRegistry(MetadataRegistry):
    """
    Manages metrics and indicators.

    Storage-agnostic contract for metric backends (like Prometheus, InfluxDB, or Datadog).
    Available in Context for custom metrics from Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
