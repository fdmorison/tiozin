# isort: skip_file
"""
Tiozin API public package.

This module defines the public, stable interface for building Tiozin pipelines.

Only the symbols exported here are considered part of the supported API.
All other modules and classes inside this package are internal implementation
details and may change without notice.
"""

from typing import TypeAlias

# Bases
from .tiozin import Tiozin
from .registry import Registry

# Metadata
from .metadata.job.manifest import JobManifest
from .metadata.lineage.model import LineageRunEvent
from .metadata.secret.model import Secret
from .metadata.setting.manifest import SettingsManifest

# Registries
from .metadata.job.registry import JobRegistry
from .metadata.lineage.registry import LineageRegistry
from .metadata.metric.registry import MetricRegistry
from .metadata.schema.registry import SchemaRegistry
from .metadata.secret.registry import SecretRegistry
from .metadata.setting.registry import SettingRegistry
from .metadata.transaction.registry import TransactionRegistry

# Runtime
from .runtime.context import Context
from .runtime.runner import Runner
from .runtime.input import Input
from .runtime.transform import Transform, CoTransform
from .runtime.output import Output
from .runtime.job import Job

# Type aliases
EtlStep: TypeAlias = Transform | Input | Output

__all__ = [
    # Bases
    "Registry",
    "Tiozin",
    # Metadata
    "JobManifest",
    "LineageRunEvent",
    "Secret",
    "SettingsManifest",
    # Registries
    "JobRegistry",
    "LineageRegistry",
    "MetricRegistry",
    "SchemaRegistry",
    "SecretRegistry",
    "SettingRegistry",
    "TransactionRegistry",
    # Runtime
    "Context",
    "Input",
    "Job",
    "Output",
    "Runner",
    "Transform",
    "CoTransform",
    # Type aliases
    "EtlStep",
]
