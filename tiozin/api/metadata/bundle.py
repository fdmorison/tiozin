from __future__ import annotations

from dataclasses import dataclass

from .job.registry import JobRegistry
from .lineage.registry import LineageRegistry
from .metric.registry import MetricRegistry
from .schema.registry import SchemaRegistry
from .secret.registry import SecretRegistry
from .setting.registry import SettingRegistry
from .transaction.registry import TransactionRegistry


@dataclass(frozen=True)
class Registries:
    """
    Holds the registry instances for a job execution.

    Passed to `Context.for_job()` and `Context.for_step()` to inject
    infrastructure dependencies without coupling the context to any
    specific registry implementation.
    """

    setting: SettingRegistry = None
    secret: SecretRegistry = None
    schema: SchemaRegistry = None
    transaction: TransactionRegistry = None
    job: JobRegistry = None
    metric: MetricRegistry = None
    lineage: LineageRegistry = None

    @staticmethod
    def from_baseline() -> Registries:
        """
        Returns a `Registries` pre-configured for minimal execution without
        external dependencies or an active TiozinApp.

        Each registry is chosen to work out of the box — no setup, no network
        connections, no external systems required:

        - `EnvSecretRegistry` — secrets read from environment variables
        - `FileJobRegistry` — job spec persisted to local files
        - `NoOpSchemaRegistry` — no schema validation
        - `NoOpTransactionRegistry` — no transaction management
        - `NoOpMetricRegistry` — no metrics collection
        - `NoOpLineageRegistry` — no lineage tracking
        - `NoOpSettingRegistry` — no configuration source
        """
        from tiozin.family.tio_kernel import (
            EnvSecretRegistry,
            FileJobRegistry,
            NoOpLineageRegistry,
            NoOpMetricRegistry,
            NoOpSchemaRegistry,
            NoOpSettingRegistry,
            NoOpTransactionRegistry,
        )

        return Registries(
            setting=NoOpSettingRegistry(),
            secret=EnvSecretRegistry(),
            schema=NoOpSchemaRegistry(),
            transaction=NoOpTransactionRegistry(),
            metric=NoOpMetricRegistry(),
            lineage=NoOpLineageRegistry(),
            job=FileJobRegistry(),
        )
