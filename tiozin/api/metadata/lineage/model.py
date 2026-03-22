from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import pendulum
from pydantic import BaseModel, ConfigDict, Field

from tiozin import config
from tiozin.utils import utcnow

if TYPE_CHECKING:
    from tiozin.api.runtime.context import Context


class LineageRunEventType(str, Enum):
    START = "START"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    ABORT = "ABORT"

    def __str__(self) -> str:
        return self.value


class LineageJob(BaseModel):
    namespace: str
    name: str
    job_type: str
    processing_type: str
    integration: str


class LineageParentRun(BaseModel):
    run_id: str
    job_name: str
    namespace: str


class LineageDataset(BaseModel):
    namespace: str
    name: str


class LineageRunEvent(BaseModel):
    """
    Tiozin's internal representation of a lineage run event.

    Captures the state of a run at a specific point in time, including job identity,
    inputs, outputs, governance tags, and optional parent context for steps.
    Backends (e.g. `OpenLineageRegistry`) convert this into their own protocol format.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: LineageRunEventType
    producer: str
    timestamp: pendulum.DateTime
    nominal_time: pendulum.DateTime
    run_id: str
    job: LineageJob
    parent: LineageParentRun | None = None
    inputs: list[LineageDataset] = Field(default_factory=list)
    outputs: list[LineageDataset] = Field(default_factory=list)
    tags: dict[str, str]

    @classmethod
    def from_context(
        cls,
        ctx: Context,
        type: LineageRunEventType,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
    ) -> LineageRunEvent:
        job = ctx.job
        namespace = f"{ctx.org}.{ctx.region}.{ctx.domain}.{ctx.subdomain}.{ctx.layer}"
        job_namespace = f"{job.org}.{job.region}.{job.domain}.{job.subdomain}.{job.layer}"
        return cls(
            type=type.value,
            producer=config.app_identifier,
            timestamp=ctx.executed_at or utcnow(),
            nominal_time=ctx.nominal_time,
            run_id=ctx.run_id,
            job=LineageJob(
                namespace=namespace,
                name=ctx.slug,
                job_type=ctx.kind,
                processing_type="STREAMING" if ctx.runner.streaming else "BATCH",
                integration=ctx.runner.name,
            ),
            parent=LineageParentRun(
                run_id=job.run_id,
                job_name=job.slug,
                namespace=job_namespace,
            )
            if job is not ctx
            else None,
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
            inputs=[
                LineageDataset(
                    namespace=namespace,
                    name=n,
                )
                for n in (inputs or [])
            ],
            outputs=[
                LineageDataset(
                    namespace=namespace,
                    name=n,
                )
                for n in (outputs or [])
            ],
        )


__all__ = [
    "LineageRunEventType",
    "LineageDataset",
    "LineageJob",
    "LineageParentRun",
    "LineageRunEvent",
]
