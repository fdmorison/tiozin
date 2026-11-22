# isort: skip_file
"""
Tiozin - A friendly ETL framework

Public API for building data pipelines with Tiozin.

During shell completion, stderr is silenced before any other import, so warnings and prints from
libraries never leak into the terminal while the user presses TAB.
"""

import os

if "_TIOZIN_COMPLETE" in os.environ:
    os.dup2(os.open(os.devnull, os.O_WRONLY), 2)

# Bases
from tiozin.api import Registry, Tiozin

# Metadata
from tiozin.api import (
    InputManifest,
    JobManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
    LineageDataset,
    LineageEvent,
    LineageRunEvent,
    Secret,
    SettingsManifest,
    Dataset,
    Datasets,
    OutputMetrics,
    Schema,
    Batch,
    BatchStatus,
    BacklogPolicy,
)

# Registries
from tiozin.api import (
    JobRegistry,
    LineageRegistry,
    MetricRegistry,
    SchemaRegistry,
    SecretRegistry,
    SettingRegistry,
    BatchRegistry,
)

# Processors
from tiozin.api import Runner, Transform, CoTransform, Input, Output, Job, EtlStep

# Auxiliary
from tiozin.api import Context
from tiozin.app import TiozinApp
from tiozin.compose import tioproxy, TemplateString


__all__ = [
    # Bases
    "Tiozin",
    "Registry",
    # Metadata
    "InputManifest",
    "JobManifest",
    "OutputManifest",
    "RunnerManifest",
    "TransformManifest",
    "Dataset",
    "Datasets",
    "OutputMetrics",
    "LineageDataset",
    "LineageEvent",
    "LineageRunEvent",
    "Secret",
    "SettingsManifest",
    "Schema",
    "Batch",
    "BatchStatus",
    "BacklogPolicy",
    # Registries
    "JobRegistry",
    "LineageRegistry",
    "MetricRegistry",
    "SchemaRegistry",
    "SecretRegistry",
    "SettingRegistry",
    "BatchRegistry",
    # Processors
    "Runner",
    "Transform",
    "CoTransform",
    "Input",
    "Output",
    "Job",
    # Auxiliary
    "Context",
    "TiozinApp",
    "EtlStep",
    "tioproxy",
    "TemplateString",
]
