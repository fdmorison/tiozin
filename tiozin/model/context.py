from tiozin.registries import (
    LineageRegistry,
    MetricRegistry,
    SchemaRegistry,
    SecretRegistry,
    TransactionRegistry,
)


class Context:
    """
    Represents the execution context for a Tiozin pipeline run.

    The Context encapsulates all runtime information needed during execution,
    including access to sessions, utilities, and metadata. It is passed to Jobs,
    Inputs, Transforms, and Outputs, allowing them to interact with the runtime
    environment.
    """

    def __init__(
        self,
        lineage_registry: LineageRegistry,
        metric_registry: MetricRegistry,
        schema_registry: SchemaRegistry,
        secret_registry: SecretRegistry,
        transaction_registry: TransactionRegistry,
    ) -> None:
        self.lineage_registry = lineage_registry
        self.metric_registry = metric_registry
        self.schema_registry = schema_registry
        self.secret_registry = secret_registry
        self.transaction_registry = transaction_registry
