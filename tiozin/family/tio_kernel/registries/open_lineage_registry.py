from openlineage.client import OpenLineageClient
from openlineage.client.generated.base import (
    InputDataset,
    Job,
    OutputDataset,
    Run,
    RunEvent,
)
from openlineage.client.generated.job_type_job import JobTypeJobFacet
from openlineage.client.generated.nominal_time_run import NominalTimeRunFacet
from openlineage.client.generated.parent_run import Job as ParentJob
from openlineage.client.generated.parent_run import ParentRunFacet
from openlineage.client.generated.parent_run import Run as ParentRun
from openlineage.client.generated.tags_run import TagsRunFacet, TagsRunFacetFields

from tiozin.api import LineageRegistry, LineageRunEvent


class OpenLineageRegistry(LineageRegistry):
    """
    OpenLineage-compatible lineage registry.

    Emits run events to any OpenLineage-compatible backend (e.g. Marquez, OpenMetadata)
    via the standard HTTP API at `POST /api/v1/lineage`.

    Attributes:
        location: Base URL of the OpenLineage backend (e.g. `http://localhost:5000`).
    """

    def __init__(self, location: str, **options) -> None:
        super().__init__(location=location, **options)
        self._client: OpenLineageClient = None

    def setup(self) -> None:
        self._client = OpenLineageClient(
            url=self.location,
            config={
                **self.options,
                "timeout": self.timeout or 3,
            },
        )
        self.ready = True

    def teardown(self) -> None:
        self._client = None
        self.ready = False

    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        return None

    def register(self, identifier: str, value: LineageRunEvent) -> None:
        """Convert a Tiozin lineage event to OpenLineage format and emit it."""
        self._client.emit(
            event=self._build_run_event(value),
        )

    def _build_run_event(self, event: LineageRunEvent) -> RunEvent:
        return RunEvent(
            eventType=event.type,
            eventTime=event.timestamp.isoformat(timespec="milliseconds"),
            producer=event.producer,
            run=Run(
                runId=event.run_id.split("_", 1)[-1],
                facets={
                    "nominalTime": NominalTimeRunFacet(
                        nominalStartTime=event.nominal_time.isoformat(timespec="milliseconds")
                    ),
                    "tags": TagsRunFacet(
                        tags=[TagsRunFacetFields(key=k, value=v) for k, v in event.tags.items()]
                    ),
                    **(
                        {
                            "parent": ParentRunFacet(
                                run=ParentRun(runId=event.parent.run_id.split("_", 1)[-1]),
                                job=ParentJob(
                                    namespace=event.parent.namespace, name=event.parent.job_name
                                ),
                            )
                        }
                        if event.parent is not None
                        else {}
                    ),
                },
            ),
            job=Job(
                namespace=event.job.namespace,
                name=event.job.name,
                facets={
                    "jobType": JobTypeJobFacet(
                        processingType=event.job.processing_type,
                        integration=event.job.integration,
                        jobType=event.job.job_type,
                    ),
                },
            ),
            inputs=[InputDataset(namespace=d.namespace, name=d.name) for d in event.inputs],
            outputs=[OutputDataset(namespace=d.namespace, name=d.name) for d in event.outputs],
        )
