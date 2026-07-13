from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

from pydantic import Field

from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.utils import current_context, generate_id, isozformat, utcnow

from ...types import NominalTime, TechnicalTime
from ..model import Metadata
from .state import BatchState
from .status import BatchStatus

if TYPE_CHECKING:
    from tiozin import BatchRegistry


class Batch(Metadata):
    """
    Represents the lifecycle of a logical batch of data.

    A batch uniquely identifies a unit of work within a resource and tracks its
    processing lifecycle. It may represent a partition, file, offset, snapshot,
    or any other job-defined granularity.

    Batches are uniquely identified by `(resource, nominal_time)`. Their status
    evolves over time as the batch progresses through processing, replay,
    quarantine, or cancellation.

    Collections of batches support higher-level concepts such as backlogs,
    representing batches awaiting processing.

    Attributes:
        id:
            Deterministic UUID derived from the natural key
            (`resource + nominal_time`). Stable across updates to the same batch.

        org:
            Organization that owns the resource.

        region:
            Region associated with the resource.

        domain:
            Domain that owns the resource.

        subdomain:
            Subdomain within the domain.

        layer:
            Data layer associated with the resource.

        product:
            Product associated with the resource.

        model:
            Model associated with the resource.

        nominal_time:
            UTC datetime identifying the technical execution increment. Analogous to Airflow's
            logical_date. Truncated to minute precision (seconds and microseconds are zeroed).

        status:
            Current lifecycle status of the batch.

        failure_count:
            Number of failures since the batch was last replayed. Incremented
            each time the batch fails and reset when the batch is replayed.

        state:
            Typed processing state of the batch (execution window and
            watermarks), replicated across executions. See `BatchState`.

        attributes:
            Arbitrary job-specific metadata associated with the batch. Typical
            values include record counts, source locations, checksums, execution
            details, or any other application-defined information.

        created_at:
            UTC timestamp when the batch was first registered.

        updated_at:
            UTC timestamp when the batch was last updated.
    """

    resource_fields: ClassVar[tuple[str, ...]] = RESOURCE_FIELDS
    natural_key_fields: ClassVar[tuple[str, ...]] = (*RESOURCE_FIELDS, "nominal_time")

    id: str = Field(default_factory=generate_id, frozen=True)

    org: str = Field(frozen=True)
    region: str = Field(frozen=True)
    domain: str = Field(frozen=True)
    subdomain: str = Field(frozen=True)
    layer: str = Field(frozen=True)
    product: str = Field(frozen=True)
    model: str = Field(frozen=True)

    nominal_time: NominalTime = Field(frozen=True)

    status: BatchStatus = BatchStatus.PENDING
    failure_count: int = Field(0, ge=0)
    state: BatchState = Field(default_factory=BatchState)
    attributes: dict[str, Any] = Field(default_factory=dict)

    created_at: TechnicalTime = Field(default_factory=utcnow, frozen=True)
    updated_at: TechnicalTime = Field(default_factory=utcnow)

    def _registry(self) -> BatchRegistry:
        return current_context().registries.batch

    def register(self) -> Self:
        batch = self._registry().register(self)
        return batch or self

    def begin(self, **attributes) -> Self:
        batch = self._registry().begin(self, **attributes)
        return batch or self

    def commit(self, **attributes) -> Self:
        batch = self._registry().commit(self, **attributes)
        return batch or self

    def fail(self, **attributes) -> Self:
        batch = self._registry().fail(self, **attributes)
        return batch or self

    def cancel(self, **attributes) -> Self:
        batch = self._registry().cancel(self, **attributes)
        return batch or self

    def quarantine(self, **attributes) -> Self:
        batch = self._registry().quarantine(self, **attributes)
        return batch or self

    def replay(self, **attributes) -> Self:
        batch = self._registry().replay(self, **attributes)
        return batch or self

    @property
    def qualified_resource(self) -> str:
        return ".".join(getattr(self, field) for field in self.resource_fields)

    @property
    def qualified_natural_key(self) -> str:
        return f"{self.qualified_resource}.{isozformat(self.nominal_time)}"

    @classmethod
    def acquire(cls) -> Batch:
        context = current_context()
        resources = {field: getattr(context, field) for field in RESOURCE_FIELDS}
        previous = context.registries.batch.get_latest(**resources)

        if not previous:
            current_state = BatchState(end=context.nominal_time)
        elif previous.status.is_terminal():
            current_state = previous.state.advance_to(context.nominal_time)
        else:
            return previous

        return Batch(
            **resources,
            nominal_time=context.nominal_time,
            state=current_state,
        ).register()

    def __str__(self) -> str:
        return self.qualified_natural_key
