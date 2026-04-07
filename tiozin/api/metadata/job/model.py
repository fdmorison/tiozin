from __future__ import annotations

from pydantic import Field

from .. import docs
from ..model import Manifest


class RunnerManifest(Manifest):
    """
    Declarative runtime environment definition.

    Specifies the execution backend and runtime behavior for the job.
    """

    # Identity
    name: str | None = Field(None, description=docs.RUNNER_NAME)
    description: str | None = Field(None, description=docs.RUNNER_DESCRIPTION)

    # Specific
    streaming: bool = Field(False, description=docs.RUNNER_STREAMING)


class InputManifest(Manifest):
    """
    Declarative data source definition.

    Specifies how and where data is read into the pipeline.
    """

    # Identity
    name: str = Field(description=docs.INPUT_NAME)
    description: str | None = Field(None, description=docs.INPUT_DESCRIPTION)

    # Business Taxonomy
    org: str | None = Field(None, description=docs.INPUT_ORG)
    region: str | None = Field(None, description=docs.INPUT_REGION)
    domain: str | None = Field(None, description=docs.INPUT_DOMAIN)
    subdomain: str | None = Field(None, description=docs.INPUT_SUBDOMAIN)
    layer: str | None = Field(None, description=docs.INPUT_LAYER)
    product: str | None = Field(None, description=docs.INPUT_PRODUCT)
    model: str | None = Field(None, description=docs.INPUT_MODEL)

    # Specific
    schema_subject: str | None = Field(None, description=docs.INPUT_SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.INPUT_SCHEMA_VERSION)


class TransformManifest(Manifest):
    """
    Declarative transformation definition.

    Specifies operations that modify or enrich data.
    """

    # Identity
    name: str = Field(description=docs.TRANSFORM_NAME)
    description: str | None = Field(None, description=docs.TRANSFORM_DESCRIPTION)

    # Business Taxonomy
    org: str | None = Field(None, description=docs.TRANSFORM_ORG)
    region: str | None = Field(None, description=docs.TRANSFORM_REGION)
    domain: str | None = Field(None, description=docs.TRANSFORM_DOMAIN)
    subdomain: str | None = Field(None, description=docs.TRANSFORM_SUBDOMAIN)
    layer: str | None = Field(None, description=docs.TRANSFORM_LAYER)
    product: str | None = Field(None, description=docs.TRANSFORM_PRODUCT)
    model: str | None = Field(None, description=docs.TRANSFORM_MODEL)

    # Specific
    schema_subject: str | None = Field(None, description=docs.TRANSFORM_SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.TRANSFORM_SCHEMA_VERSION)


class OutputManifest(Manifest):
    """
    Declarative data destination definition.

    Specifies where and how processed data is written.
    """

    # Identity
    name: str = Field(description=docs.OUTPUT_NAME)
    description: str | None = Field(None, description=docs.OUTPUT_DESCRIPTION)

    # Business Taxonomy
    org: str | None = Field(None, description=docs.OUTPUT_ORG)
    region: str | None = Field(None, description=docs.OUTPUT_REGION)
    domain: str | None = Field(None, description=docs.OUTPUT_DOMAIN)
    subdomain: str | None = Field(None, description=docs.OUTPUT_SUBDOMAIN)
    layer: str | None = Field(None, description=docs.OUTPUT_LAYER)
    product: str | None = Field(None, description=docs.OUTPUT_PRODUCT)
    model: str | None = Field(None, description=docs.OUTPUT_MODEL)

    # Specific
    schema_subject: str | None = Field(None, description=docs.OUTPUT_SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.OUTPUT_SCHEMA_VERSION)


class JobManifest(Manifest):
    """
    Declarative job definition.

    Describes a job as structured data including metadata, taxonomy, and pipeline components.
    Can be stored, versioned, and transferred as code.
    """

    # Identity
    name: str = Field(description=docs.JOB_NAME)
    description: str | None = Field(None, description=docs.JOB_DESCRIPTION)

    # Ownership
    owner: str | None = Field(None, description=docs.JOB_OWNER)
    maintainer: str | None = Field(None, description=docs.JOB_MAINTAINER)
    cost_center: str | None = Field(None, description=docs.JOB_COST_CENTER)
    labels: dict[str, str] | None = Field(default_factory=dict, description=docs.JOB_LABELS)

    # Domain
    org: str = Field(description=docs.JOB_ORG)
    region: str = Field(description=docs.JOB_REGION)
    domain: str = Field(description=docs.JOB_DOMAIN)
    subdomain: str = Field(description=docs.JOB_SUBDOMAIN)
    layer: str = Field(description=docs.JOB_LAYER)
    product: str = Field(description=docs.JOB_PRODUCT)
    model: str = Field(description=docs.JOB_MODEL)

    # Pipeline Components
    runner: RunnerManifest = Field(description=docs.JOB_RUNNER)
    inputs: list[InputManifest] = Field(description=docs.JOB_INPUTS, min_length=1)
    transforms: list[TransformManifest] | None = Field(
        default_factory=list, description=docs.JOB_TRANSFORMS
    )
    outputs: list[OutputManifest] | None = Field(default_factory=list, description=docs.JOB_OUTPUTS)
