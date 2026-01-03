from __future__ import annotations

from pydantic import Field

from . import docs
from .input_manifest import InputManifest
from .manifest import Manifest
from .output_manifest import OutputManifest
from .runner_manifest import RunnerManifest
from .transform_manifest import TransformManifest


class JobManifest(Manifest):
    """
    Declarative job definition.

    Describes a job as structured data including metadata, taxonomy, and pipeline components.
    Can be stored, versioned, and transferred as code.
    """

    # Identity
    kind: str = Field(description=docs.KIND)
    name: str = Field(description=docs.JOB_NAME)
    description: str | None = Field(None, description=docs.JOB_DESCRIPTION)

    # Ownership
    owner: str | None = Field(None, description=docs.JOB_OWNER)
    maintainer: str | None = Field(None, description=docs.JOB_MAINTAINER)
    cost_center: str | None = Field(None, description=docs.JOB_COST_CENTER)
    labels: dict[str, str] | None = Field(default_factory=dict, description=docs.JOB_LABELS)

    # Business Taxonomy
    org: str = Field(description=docs.JOB_ORG)
    region: str = Field(description=docs.JOB_REGION)
    domain: str = Field(description=docs.JOB_DOMAIN)
    product: str = Field(description=docs.JOB_PRODUCT)
    model: str = Field(description=docs.JOB_MODEL)
    layer: str = Field(description=docs.JOB_LAYER)

    # Pipeline Components
    runner: RunnerManifest = Field(description=docs.JOB_RUNNER)
    inputs: list[InputManifest] = Field(description=docs.JOB_INPUTS)
    transforms: list[TransformManifest] = Field(
        default_factory=list, description=docs.JOB_TRANSFORMS
    )
    outputs: list[OutputManifest] = Field(default_factory=list, description=docs.JOB_OUTPUTS)
