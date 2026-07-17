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
from .metadata.registry import Registry

# Enums
from .enums import Cadence, LowerEnum, UpperEnum

# Metadata
from .metadata.job.model import (
    InputManifest,
    JobManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from .metadata.lineage.model import LineageDataset, LineageEvent, LineageRunEvent
from .metadata.secret.model import Secret
from .metadata.setting.model import SettingsManifest
from .metadata.schema.model import Schema
from .metadata.batch.enums import BacklogPolicy, BatchStatus
from .metadata.batch.model import Batch

# Registries
from .metadata.job.base import JobRegistry
from .metadata.lineage.base import LineageRegistry
from .metadata.metric.base import MetricRegistry
from .metadata.schema.base import SchemaRegistry
from .metadata.secret.base import SecretRegistry
from .metadata.setting.base import SettingRegistry
from .metadata.batch.base import BatchRegistry

# Runtime
from .context import Context
from .runtime.runner.base import Runner
from .runtime.input.base import Input
from .runtime.transform.base import Transform, CoTransform
from .runtime.output.base import Output
from .runtime.job.base import Job
from .runtime.dataset import Dataset, Datasets

# Type aliases
EtlStep: TypeAlias = Transform | Input | Output

__all__ = [
    # Bases
    "Registry",
    "Tiozin",
    # Enums
    "BacklogPolicy",
    "Cadence",
    "LowerEnum",
    "UpperEnum",
    # Metadata
    "InputManifest",
    "JobManifest",
    "OutputManifest",
    "RunnerManifest",
    "TransformManifest",
    "Dataset",
    "Datasets",
    "LineageDataset",
    "LineageEvent",
    "LineageRunEvent",
    "Secret",
    "SettingsManifest",
    "Schema",
    "Batch",
    "BatchStatus",
    # Registries
    "JobRegistry",
    "LineageRegistry",
    "MetricRegistry",
    "SchemaRegistry",
    "SecretRegistry",
    "SettingRegistry",
    "BatchRegistry",
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
