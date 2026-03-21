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
