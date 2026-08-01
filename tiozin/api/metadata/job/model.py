from __future__ import annotations

from pydantic import Field

from tiozin.api.enums import Cadence
from tiozin.api.metadata.batch.enums import BacklogPolicy
from tiozin.api.owned import Owned
from tiozin.api.resourceful import OptionalResourceful, Resourceful

from .. import docs
from ..model import Manifest


class RunnerManifest(Manifest):
    """
    Declarative runtime environment definition.

    Specifies the execution backend and runtime behavior for the job.
    """

    @classmethod
    def __produces__(cls):
        from tiozin import Runner

        return Runner

    # Identity
    name: str | None = Field(None, description=docs.RUNNER_NAME)
    description: str | None = Field(None, description=docs.RUNNER_DESCRIPTION)

    # Specific
    streaming: bool = Field(False, description=docs.RUNNER_STREAMING)


class InputManifest(OptionalResourceful, Manifest):
    """
    Declarative data source definition.

    Specifies how and where data is read into the pipeline.
    """

    @classmethod
    def __produces__(cls):
        from tiozin import Input

        return Input

    # Identity
    name: str = Field(description=docs.INPUT_NAME)
    description: str | None = Field(None, description=docs.INPUT_DESCRIPTION)

    # Specific
    schema_subject: str | None = Field(None, description=docs.INPUT_SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.INPUT_SCHEMA_VERSION)


class TransformManifest(OptionalResourceful, Manifest):
    """
    Declarative transformation definition.

    Specifies operations that modify or enrich data.
    """

    @classmethod
    def __produces__(cls):
        from tiozin import Transform

        return Transform

    # Identity
    name: str = Field(description=docs.TRANSFORM_NAME)
    description: str | None = Field(None, description=docs.TRANSFORM_DESCRIPTION)

    # Specific
    schema_subject: str | None = Field(None, description=docs.TRANSFORM_SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.TRANSFORM_SCHEMA_VERSION)


class OutputManifest(OptionalResourceful, Manifest):
    """
    Declarative data destination definition.

    Specifies where and how processed data is written.
    """

    @classmethod
    def __produces__(cls):
        from tiozin import Output

        return Output

    # Identity
    name: str = Field(description=docs.OUTPUT_NAME)
    description: str | None = Field(None, description=docs.OUTPUT_DESCRIPTION)

    # Specific
    schema_subject: str | None = Field(None, description=docs.OUTPUT_SCHEMA_SUBJECT)
    schema_version: str | None = Field(None, description=docs.OUTPUT_SCHEMA_VERSION)


class JobManifest(Resourceful, Owned, Manifest):
    """
    Declarative job definition.

    Describes a job as structured data including metadata, taxonomy, and pipeline components.
    Can be stored, versioned, and transferred as code.
    """

    @classmethod
    def __produces__(cls):
        from tiozin import Job

        return Job

    # Identity
    name: str = Field(description=docs.JOB_NAME)
    description: str | None = Field(None, description=docs.JOB_DESCRIPTION)

    # Execution
    cadence: Cadence | None = Field(None, description=docs.JOB_CADENCE)
    max_batches_per_run: int | None = Field(None, description=docs.JOB_MAX_BATCHES_PER_RUN)
    backlog_policy: BacklogPolicy | None = Field(None, description=docs.JOB_BACKLOG_POLICY)

    # Pipeline Components
    runner: RunnerManifest = Field(description=docs.JOB_RUNNER)
    inputs: list[InputManifest] = Field(description=docs.JOB_INPUTS, min_length=1)
    transforms: list[TransformManifest] | None = Field(
        default_factory=list, description=docs.JOB_TRANSFORMS
    )
    outputs: list[OutputManifest] | None = Field(default_factory=list, description=docs.JOB_OUTPUTS)
