from ..registry import Registry


class MetricRegistry(Registry[object]):
    """
    Manages metrics and indicators.

    Storage-agnostic contract for metric backends (like Prometheus, InfluxDB, or Datadog).
    Available in Context for custom metrics from Transforms, Inputs, and Outputs.
    """
