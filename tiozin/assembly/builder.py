from typing import Self

from tiozin.api import Job, JobManifest
from tiozin.family.tio_kernel import NoOpInput, NoOpRunner

from .plugin_factory import PluginFactory


class JobBuilder:
    """
    Builds Job instances from manifests.

    Constructs Jobs from manifest definitions (YAML, JSON, or Python).

    Example:
        builder = JobBuilder()
        job = builder.from_manifest(manifest).build()
        job.run(context)
    """

    def __init__(self) -> None:
        self.plugin_factory = PluginFactory()

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
        with PluginFactory() as plugins:
            return plugins.get_job(
                kind="LinearJob",
                name="kinglear_word_count_job",
                description="Pre-processes Shakespeare source texts",
                org="tiozin",
                region="latam",
                domain="literature",
                product="shakespeare",
                model="kinglear",
                layer="refined",
                runner=NoOpRunner(
                    org="test",
                    region="test",
                    domain="test",
                    product="test",
                    model="test",
                    layer="test",
                    name="NoOpRunner",
                ),
                inputs=[
                    NoOpInput(
                        org="test",
                        region="test",
                        domain="test",
                        product="test",
                        model="test",
                        layer="test",
                        name="ReadNothing",
                    )
                ],
                transforms=[],
                outputs=[],
            )
