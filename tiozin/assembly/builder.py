from typing import Self

from tiozin.model.job import Job
from tiozin.registries import JobManifest


class JobBuilder:
    """
    Builds Job instances from manifests.

    Constructs Jobs from manifest definitions (YAML, JSON, or Python).

    Example:
        builder = JobBuilder()
        job = builder.from_manifest(manifest).build()
        job.run(context)
    """

    def from_manifest(self, manifest: JobManifest) -> Self:
        """
        Load a Job from manifest.

        Args:
            manifest: Declarative job definition.

        Returns:
            Self for method chaining.
        """
        return self

    def build(self) -> Job:
        """
        Build the Job instance.

        Returns:
            Fully built Job ready for execution.
        """
        return Job()
