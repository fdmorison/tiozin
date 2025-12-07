from ..registry import MetadataRegistry


class MetricRegistry(MetadataRegistry):
    """
    Registry that manages metrics and indicators collected by Tio.

    Supports any storage backend for metrics (e.g., Prometheus, InfluxDB, Datadog, local
    files), while keeping Tio agnostic to the storage details. Enables pipelines
    and tasks to report and retrieve metrics consistently across different environments.

    Tio automatically handles metric collection and retrieval during pipeline
    execution, but the MetricRegistry is also available in the Context for custom
    manipulation by Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
