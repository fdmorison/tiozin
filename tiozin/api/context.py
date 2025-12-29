from tiozin.api.registries import (
    LineageRegistry,
    MetricRegistry,
    SchemaRegistry,
    SecretRegistry,
    TransactionRegistry,
)


class Context:
    """
    Runtime context for pipeline execution.

    Provides access to registries and metadata during job runs.
    Passed to Jobs, Inputs, Transforms, and Outputs.
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
