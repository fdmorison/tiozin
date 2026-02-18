from pydantic import Field

from . import docs
from .manifest import Manifest


class RunnerManifest(Manifest):
    """
    Declarative runtime environment definition.

    Specifies the execution backend and runtime behavior for the job.
    """

    # Identity
    kind: str = Field(description=docs.KIND)
    name: str | None = Field(None, description=docs.RUNNER_NAME)
    description: str | None = Field(None, description=docs.RUNNER_DESCRIPTION)

    # Specific
    streaming: bool = Field(False, description=docs.RUNNER_STREAMING)
