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

    Any field left as `None` is automatically filled with its NoOp equivalent,
    so every `Registries` instance is safe to use without configuration.
    """

    setting: SettingRegistry = None
    secret: SecretRegistry = None
    schema: SchemaRegistry = None
    transaction: TransactionRegistry = None
    job: JobRegistry = None
    metric: MetricRegistry = None
    lineage: LineageRegistry = None

    def __post_init__(self) -> None:
        from tiozin.family.tio_kernel import (
            EnvSecretRegistry,
            FileJobRegistry,
            NoOpLineageRegistry,
            NoOpMetricRegistry,
            NoOpSchemaRegistry,
            NoOpSettingRegistry,
            NoOpTransactionRegistry,
        )

        for name, factory in (
            ("setting", NoOpSettingRegistry),
            ("secret", EnvSecretRegistry),
            ("schema", NoOpSchemaRegistry),
            ("transaction", NoOpTransactionRegistry),
            ("job", FileJobRegistry),
            ("metric", NoOpMetricRegistry),
            ("lineage", NoOpLineageRegistry),
        ):
            if getattr(self, name) is None:
                object.__setattr__(self, name, factory())
