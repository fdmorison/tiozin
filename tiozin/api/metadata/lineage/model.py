from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from openlineage.client.generated.base import InputDataset, OutputDataset
from pydantic import Field

from tiozin import config
from tiozin.utils import utcnow

from ..model import Metadata
from ..schema.model import Schema
from .enums import LineageJobType, LineageProcessingType, LineageRunEventType

if TYPE_CHECKING:
    from tiozin.api import Context, Dataset


class LineageDataset(Metadata):
    """
    Represents a dataset in a lineage event.

    Carries the `(namespace, name)` identity and optional schema facet
    following OpenLineage naming conventions.

    https://openlineage.io/docs/spec/naming/
    """

    namespace: str | None = None
    name: str | None = None
    schema: Schema | None = None

    @classmethod
    def from_dataset(cls, dataset: Dataset) -> LineageDataset:
        return cls(
            namespace=dataset.tiozin_namespace,
            name=dataset.tiozin_name,
            schema=dataset.tiozin_schema,
        )

    def as_input(self) -> InputDataset:
        return InputDataset(
            namespace=self.namespace,
            name=self.name,
            facets=self.facets(),
        )

    def as_output(self) -> OutputDataset:
        return OutputDataset(
            namespace=self.namespace,
            name=self.name,
            facets=self.facets(),
        )

    def facets(self) -> dict:
        return {"schema": self.schema.export("openlineage")} if self.schema else {}


class LineageJob(Metadata):
    QUERY: ClassVar = LineageJobType.QUERY
    COMMAND: ClassVar = LineageJobType.COMMAND
    DAG: ClassVar = LineageJobType.DAG
    TASK: ClassVar = LineageJobType.TASK
    JOB: ClassVar = LineageJobType.JOB
    MODEL: ClassVar = LineageJobType.MODEL

    namespace: str
    name: str
    type: LineageJobType
    processing_type: LineageProcessingType
    integration: str

    @classmethod
    def from_context(cls, ctx: Context) -> LineageJob:
        return cls(
            namespace=ctx.namespace,
            name=ctx.qualified_slug,
            type=LineageJobType.JOB,
            processing_type=LineageProcessingType.STREAMING
            if ctx.runner.streaming
            else LineageProcessingType.BATCH,
            integration=config.app_name.upper(),
        )


class LineageParentRun(Metadata):
    run_id: str
    name: str
    namespace: str

    @classmethod
    def from_context(cls, ctx: Context) -> LineageParentRun | None:
        if ctx.is_root:
            return None
        return cls(
            run_id=ctx.job.run_id,
            name=ctx.job.qualified_slug,
            namespace=ctx.job.namespace,
        )


class LineageRunEvent(Metadata):
    """
    Tiozin's internal representation of a lineage run event.

    Captures the state of a run at a specific point in time, including job identity,
    inputs, outputs, governance tags, and optional parent context for steps.
    Backends (e.g. `OpenLineageRegistry`) convert this into their own protocol format.
    """

    START: ClassVar = LineageRunEventType.START
    COMPLETE: ClassVar = LineageRunEventType.COMPLETE
    FAIL: ClassVar = LineageRunEventType.FAIL
    ABORT: ClassVar = LineageRunEventType.ABORT

    type: LineageRunEventType
    producer: str
    timestamp: datetime
    nominal_time: datetime
    run_id: str
    job: LineageJob
    tags: dict[str, str]
    parent: LineageParentRun | None = None
    inputs: list[LineageDataset] = Field(default_factory=list)
    outputs: list[LineageDataset] = Field(default_factory=list)

    @classmethod
    def from_context(
        cls,
        ctx: Context,
        type: LineageRunEventType,
        inputs: list[Dataset] | None = None,
        outputs: list[Dataset] | None = None,
    ) -> LineageRunEvent:
        return cls(
            type=LineageRunEventType(type),
            producer=config.app_identifier,
            timestamp=ctx.executed_at or utcnow(),
            nominal_time=ctx.nominal_time,
            run_id=ctx.run_id,
            job=LineageJob.from_context(ctx),
            parent=LineageParentRun.from_context(ctx),
            tags={
                "org": ctx.org,
                "region": ctx.region,
                "domain": ctx.domain,
                "subdomain": ctx.subdomain,
                "layer": ctx.layer,
                "product": ctx.product,
                "model": ctx.model,
                "owner": ctx.owner,
                "maintainer": ctx.maintainer,
                "cost_center": ctx.cost_center,
                **ctx.labels,
            },
            inputs=[LineageDataset.from_dataset(d) for d in (inputs or [])],
            outputs=[LineageDataset.from_dataset(d) for d in (outputs or [])],
        )
