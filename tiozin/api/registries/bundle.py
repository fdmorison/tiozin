from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tiozin.api.registries.job_registry import JobRegistry
    from tiozin.api.registries.lineage_registry import LineageRegistry
    from tiozin.api.registries.metric_registry import MetricRegistry
    from tiozin.api.registries.schema_registry import SchemaRegistry
    from tiozin.api.registries.secret_registry import SecretRegistry
    from tiozin.api.registries.setting_registry import SettingRegistry
    from tiozin.api.registries.transaction_registry import TransactionRegistry


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
