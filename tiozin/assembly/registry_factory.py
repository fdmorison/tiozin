from tiozin.registries import (
    FileJobRegistry,
    JobRegistry,
    LineageRegistry,
    MetricRegistry,
    NoOpLineageRegistry,
    NoOpMetricRegistry,
    NoOpSchemaRegistry,
    NoOpSecretRegistry,
    NoOpSettingRegistry,
    NoOpTransactionRegistry,
    Registry,
    SchemaRegistry,
    SecretRegistry,
    SettingRegistry,
    TransactionRegistry,
)


class RegistryFactory:
    """
    Creates and manages registry instances.

    Accepts custom registries or defaults to NoOp implementations.
    """

    def __init__(
        self,
        job_registry: JobRegistry = None,
        lineage_registry: LineageRegistry = None,
        metric_registry: MetricRegistry = None,
        schema_registry: SchemaRegistry = None,
        secret_registry: SecretRegistry = None,
        transaction_registry: TransactionRegistry = None,
        setting_registry: SettingRegistry = None,
    ):
        self._job_registry = job_registry or FileJobRegistry()
        self._lineage_registry = lineage_registry or NoOpLineageRegistry()
        self._metric_registry = metric_registry or NoOpMetricRegistry()
        self._schema_registry = schema_registry or NoOpSchemaRegistry()
        self._secret_registry = secret_registry or NoOpSecretRegistry()
        self._transaction_registry = transaction_registry or NoOpTransactionRegistry()
        self._setting_registry = setting_registry or NoOpSettingRegistry()

    def all_registries(self) -> list[Registry]:
        return [
            self._job_registry,
            self._lineage_registry,
            self._metric_registry,
            self._schema_registry,
            self._secret_registry,
            self._transaction_registry,
            self._setting_registry,
        ]

    @property
    def job_registry(self) -> JobRegistry:
        return self._job_registry

    @property
    def lineage_registry(self) -> LineageRegistry:
        return self._lineage_registry

    @property
    def metric_registry(self) -> MetricRegistry:
        return self._metric_registry

    @property
    def schema_registry(self) -> SchemaRegistry:
        return self._schema_registry

    @property
    def secret_registry(self) -> SecretRegistry:
        return self._secret_registry

    @property
    def transaction_registry(self) -> TransactionRegistry:
        return self._transaction_registry

    @property
    def setting_registry(self) -> SettingRegistry:
        return self._setting_registry
