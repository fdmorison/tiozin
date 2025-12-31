from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from tiozin.exceptions import JobManifestError
from tiozin.utils.helpers import try_get

from . import job_manifest_docs as docs


class Manifest(BaseModel):
    """
    Base manifest for pipeline resources.

    Provides identity and business context for runners, inputs, transforms, and outputs.
    """

    model_config = ConfigDict(extra="allow")

    # Identity
    kind: str = Field(description=docs.KIND)
    name: str | None = Field(None, description=docs.MANIFEST_NAME)
    description: str | None = Field(None, description=docs.DESCRIPTION)

    # Business context inspired by Datamesh principles
    org: str | None = Field(None, description=docs.ORG)
    region: str | None = Field(None, description=docs.REGION)
    domain: str | None = Field(None, description=docs.DOMAIN)
    product: str | None = Field(None, description=docs.PRODUCT)
    model: str | None = Field(None, description=docs.MODEL)
    layer: str | None = Field(None, description=docs.LAYER)

    @classmethod
    def model_validate(cls, *args, **kwargs) -> None:
        try:
            return super().model_validate(*args, **kwargs)
        except ValidationError as e:
            job_name = try_get(args[0], "name") if args else None
            raise JobManifestError.from_pydantic(e, job=job_name) from e


class RunnerManifest(Manifest):
    """
    Defines job execution environment.

    Describes runtime behavior (like Spark, SQL, or custom runners).
    """

    streaming: bool = Field(False, description=docs.STREAMING)


class InputManifest(Manifest):
    """
    Defines a data source.

    Specifies how and where data is read into the pipeline.
    """

    name: str = Field(description=docs.INPUT_NAME)
    schema: str | None = Field(None, description=docs.SCHEMA)
    schema_subject: str | None = Field(None, description=docs.SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.SCHEMA_VERSION)


class TransformManifest(Manifest):
    """
    Defines a data transformation.

    Specifies operations that modify or enrich data.
    """

    name: str = Field(description=docs.TRANSFORM_NAME)


class OutputManifest(Manifest):
    """
    Defines a data destination.

    Specifies where and how processed data is written.
    """

    name: str = Field(description=docs.OUTPUT_NAME)


class JobManifest(Manifest):
    """
    Declarative job definition.

    Describes a job as structured data including metadata, taxonomy, and pipeline components.
    Can be stored, versioned, and transferred as code.
    """

    # Identity & Ownership
    name: str = Field(description=docs.NAME)
    owner: str | None = Field(None, description=docs.OWNER)
    maintainer: str | None = Field(None, description=docs.MANTAINER)
    cost_center: str | None = Field(None, description=docs.COST_CENTER)
    labels: dict[str, str] | None = Field(default_factory=dict, description=docs.LABELS)

    # Business Taxonomy (required)
    org: str = Field(description=docs.JOB_ORG)
    region: str = Field(description=docs.JOB_REGION)
    domain: str = Field(description=docs.JOB_DOMAIN)
    product: str = Field(description=docs.JOB_PRODUCT)
    model: str = Field(description=docs.JOB_MODEL)
    layer: str = Field(description=docs.JOB_LAYER)

    # Pipeline Components
    runner: RunnerManifest = Field(description=docs.RUNNER)
    inputs: list[InputManifest] = Field(description=docs.INPUTS)
    transforms: list[TransformManifest] = Field(description=docs.TRANSFORMS)
    outputs: list[OutputManifest] = Field(description=docs.OUTPUTS)

    @model_validator(mode="after")
    def should_have_at_least_one_step(cls, model: JobManifest) -> JobManifest:
        if not model.inputs:
            raise ValueError("Job must have at least one Input step")
        return model
