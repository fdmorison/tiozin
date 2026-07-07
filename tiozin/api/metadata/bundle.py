from __future__ import annotations

from dataclasses import dataclass

from .batch.base import BatchRegistry
from .job.base import JobRegistry
from .lineage.base import LineageRegistry
from .metric.base import MetricRegistry
from .schema.base import SchemaRegistry
from .secret.base import SecretRegistry
from .setting.base import SettingRegistry


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
    batch: BatchRegistry = None
    job: JobRegistry = None
    metric: MetricRegistry = None
    lineage: LineageRegistry = None

    def __post_init__(self) -> None:
        from tiozin.family.tio_kernel import (
            EnvSecretRegistry,
            FileJobRegistry,
            NoOpBatchRegistry,
            NoOpLineageRegistry,
            NoOpMetricRegistry,
            NoOpSchemaRegistry,
            NoOpSettingRegistry,
        )

        for name, factory in (
            ("setting", NoOpSettingRegistry),
            ("secret", EnvSecretRegistry),
            ("schema", NoOpSchemaRegistry),
            ("batch", NoOpBatchRegistry),
            ("job", FileJobRegistry),
            ("metric", NoOpMetricRegistry),
            ("lineage", NoOpLineageRegistry),
        ):
            if getattr(self, name) is None:
                object.__setattr__(self, name, factory())
