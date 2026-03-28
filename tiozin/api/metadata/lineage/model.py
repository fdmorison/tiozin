from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field

from tiozin import config
from tiozin.utils import utcnow

from ..model import Model
from .dataset import LineageDataset
from .enums import LineageJobType, LineageProcessingType, LineageRunEventType

if TYPE_CHECKING:
    from tiozin.api import Context


class Lineage(Model):
    inputs: list[LineageDataset]
    outputs: list[LineageDataset]


class LineageJob(Model):
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


class LineageParentRun(Model):
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


class LineageRunEvent(Model):
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
        inputs: list[LineageDataset] | None = None,
        outputs: list[LineageDataset] | None = None,
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
            inputs=inputs or [],
            outputs=outputs or [],
        )
