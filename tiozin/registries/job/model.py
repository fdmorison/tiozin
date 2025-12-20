from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from tiozin.exceptions import JobManifestException

from . import docs


class Manifest(BaseModel):
    """
    Base definition for any resource in a job manifest.

    Provides identity and business context that can be reused by
    pipeline components (runner, inputs, transforms, outputs).
    """

    model_config = ConfigDict(extra="allow")

    # Identity
    kind: str = Field(description=docs.KIND)
    description: Optional[str] = Field(None, description=docs.DESCRIPTION)

    # Business context inspired by Datamesh principles
    org: Optional[str] = Field(None, description=docs.ORG)
    region: Optional[str] = Field(None, description=docs.REGION)
    domain: Optional[str] = Field(None, description=docs.DOMAIN)
    product: Optional[str] = Field(None, description=docs.PRODUCT)
    model: Optional[str] = Field(None, description=docs.MODEL)
    layer: Optional[str] = Field(None, description=docs.LAYER)

    @classmethod
    def model_validate(cls, *args, **kwargs) -> None:
        try:
            return super().model_validate(*args, **kwargs)
        except ValidationError as e:
            raise JobManifestException.from_pydantic(e)


class RunnerManifest(Manifest):
    """
    Defines how a job runs.

    Describes the execution environment and runtime behavior,
    e.g., Spark, SQL, or custom runners.
    """

    streaming: bool = Field(False, description=docs.STREAMING)


class InputManifest(Manifest):
    """
    Represents a data source for the job.

    Defines how and from where data is read into the pipeline.
    """

    schema: Optional[str] = Field(None, description=docs.SCHEMA)
    schema_subject: Optional[str] = Field(None, description=docs.SCHEMA_SUBJECT)
    schema_version: Optional[str] = Field(None, description=docs.SCHEMA_VERSION)


class TransformManifest(Manifest):
    """
    Represents a data transformation step.

    Defines operations that modify or enrich data between input and output.
    """


class OutputManifest(Manifest):
    """
    Represents a data destination for the job.

    Defines where and how processed data is written or published.
    """


class JobManifest(Manifest):
    """
    Declarative representation of a data job.

    This manifest describes the job as a structured document, including metadata,
    business taxonomy, and pipeline components. It allows the job to be treated as code:
    it can be stored in a database, transferred via APIs, versioned, or even used
    as training data for AI models. Essentially, it is the blueprint of the job,
    decoupled from execution.
    """

    model_config = ConfigDict(extra="ignore")

    # Identity & Ownership
    name: str = Field(description=docs.NAME)
    owner: Optional[str] = Field(None, description=docs.OWNER)
    team: Optional[str] = Field(None, description=docs.TEAM)
    cost_center: Optional[str] = Field(None, description=docs.COST_CENTER)
    labels: Optional[dict[str, str]] = Field(default_factory=dict, description=docs.LABELS)

    # Business Taxonomy (required)
    org: str = Field(description=docs.JOB_ORG)
    region: str = Field(description=docs.JOB_REGION)
    domain: str = Field(description=docs.JOB_DOMAIN)
    product: str = Field(description=docs.JOB_PRODUCT)
    model: str = Field(description=docs.JOB_MODEL)
    layer: str = Field(description=docs.JOB_LAYER)

    # Pipeline Components
    runner: RunnerManifest = Field(description=docs.RUNNER)
    inputs: dict[str, InputManifest] = Field(description=docs.INPUTS)
    transforms: dict[str, TransformManifest] = Field(description=docs.TRANSFORMS)
    outputs: dict[str, OutputManifest] = Field(description=docs.OUTPUTS)

    @model_validator(mode="after")
    def should_have_at_least_one_step(cls, model: JobManifest) -> JobManifest:
        if not model.inputs:
            raise ValueError("Job must have at least one Input step")
        return model
