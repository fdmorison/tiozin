from openlineage.client import OpenLineageClient, OpenLineageClientOptions
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

    Emits run events to OpenLineage backends (e.g. Marquez, OpenMetadata) using the standard
    HTTP API (`POST /api/v1/lineage`) or a custom transport (e.g. Kafka) when configured
    via `options`.

    See the OpenLineage Python client documentation for supported transports and configuration:
    https://openlineage.io/docs/client/python/#transport

    Attributes:
        location:
            Base URL of the OpenLineage backend (e.g. `http://localhost:5000`).
            Not required when using a custom transport.
        verify:
            Whether to verify TLS certificates. Defaults to `True`.
        api_key:
            Optional bearer token sent with HTTP requests.
        options:
            Extra keyword arguments forwarded to `OpenLineageClient`.
            Use this to configure custom transports (e.g. `transport={...}`).

    Examples:

        ```python
        OpenLineageRegistry(
            location="http://marquez:5000",
            api_key="{{ ENV.LINEAGE_API_KEY }}"
        )
        ```

        To configure via `tiozin.yaml`, declare the registry under `registries.lineage`:

        ```yaml
        registries:
          lineage:
            kind: tio_kernel:OpenLineageRegistry
            location: http://marquez:5000
            api_key: "{{ ENV.LINEAGE_API_KEY }}"
        ```

        Any extra field in `tiozin.yaml` is forwarded as a keyword argument to `OpenLineageClient`,
        which allows configuring alternative transports. The example below uses Kafka:

        ```yaml
        registries:
          lineage:
            kind: tio_kernel:OpenLineageRegistry
            transport:
              type: kafka
              topicName: openlineage.events
              messageKey: some-value
              properties:
                bootstrap.servers: localhost:9092,another.host:9092
                acks: all
                retries: 3
                key.serializer: org.apache.kafka.common.serialization.StringSerializer
                value.serializer: org.apache.kafka.common.serialization.StringSerializer
        ```
    """

    def __init__(
        self,
        location: str = None,
        verify: bool = True,
        api_key: str = None,
        **options,
    ) -> None:
        super().__init__(location=location, **options)
        self.verify = verify
        self.api_key = api_key
        self._client: OpenLineageClient = None

    def setup(self) -> None:
        self._client = OpenLineageClient(
            url=self.location,
            options=OpenLineageClientOptions(
                timeout=self.timeout,
                api_key=self.api_key,
                verify=self.verify,
            ),
            **self.options,
        )
        self.ready = True

    def teardown(self) -> None:
        self._client = None
        self.ready = False

    def get(self, identifier: str = None, version: str = None) -> LineageRunEvent:
        # TODO
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
