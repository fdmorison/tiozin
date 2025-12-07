from typing import Self

from tio.model.job import Job


class JobBuilder:
    """
    Builder for creating Job instances from manifests.

    The JobBuilder provides a convenient way to construct Jobs from manifests, which
    define the Inputs, Transforms, Outputs, and Runner. In most cases, manifests are
    YAML contents stored in memory, loaded from a filesystem, bucket, or database.

    This class abstracts the details of parsing and assembling the Job, allowing TioApps
    to create Jobs in a consistent and reusable manner.

    Example:
        ```python
        builder = JobBuilder()
        job = builder.from_yaml("<yaml content here>").build()
        job.run(context)
        ```
    """

    def from_yaml(self, manifest: str) -> Self:
        """
        Load a Job manifest from a YAML content string.

        Args:
            manifest: The YAML content representing the job configuration.

        Returns:
            The builder, allowing method chaining for building the Job.
        """
        return self

    def build(self) -> Job:
        """
        Construct the Job instance from the loaded manifest.

        Returns:
            A fully built Job ready to be executed within a TioApp.
        """
        return Job()
