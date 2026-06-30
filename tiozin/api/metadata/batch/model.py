from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field

from tiozin.api.conventions import DOMAIN_FIELDS, PRODUCT_FIELDS, RESOURCE_FIELDS
from tiozin.utils import generate_id, utcnow

from ..model import Metadata
from .status import BatchStatus

if TYPE_CHECKING:
    from tiozin.api.metadata.batch.registry import BatchRegistry


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

        attributes:
            Arbitrary job-specific metadata associated with the batch. Typical
            values include record counts, source locations, checksums, execution
            details, or any other application-defined information.

        created_at:
            UTC timestamp when the batch was first registered.

        updated_at:
            UTC timestamp when the batch was last updated.
    """

    id: str = Field(default_factory=generate_id, frozen=True)

    org: str = Field(frozen=True)
    region: str = Field(frozen=True)
    domain: str = Field(frozen=True)
    subdomain: str = Field(frozen=True)
    layer: str = Field(frozen=True)
    product: str = Field(frozen=True)
    model: str = Field(frozen=True)
    nominal_time: datetime = Field(frozen=True)

    status: BatchStatus = BatchStatus.PENDING
    failure_count: int = Field(0, ge=0)
    attributes: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=utcnow, frozen=True)
    updated_at: datetime = Field(default_factory=utcnow)

    def _registry(self) -> BatchRegistry:
        from tiozin.api.context import Context

        return Context.current().registries.batch

    def register(self) -> Batch:
        self._registry().register(self)
        return self

    def begin(self, **attributes) -> Batch:
        self.attributes |= attributes
        self._registry().begin(self)
        return self

    def commit(self, **attributes) -> Batch:
        self.attributes |= attributes
        self._registry().commit(self)
        return self

    def fail(self, **attributes) -> Batch:
        self.attributes |= attributes
        self.failure_count += 1
        self._registry().fail(self)
        return self

    def cancel(self, **attributes) -> Batch:
        self.attributes |= attributes
        self._registry().cancel(self)
        return self

    def quarantine(self, **attributes) -> Batch:
        self.attributes |= attributes
        self._registry().quarantine(self)
        return self

    def replay(self, **attributes) -> Batch:
        self.attributes |= attributes
        self.failure_count = 0
        self._registry().replay(self)
        return self

    @property
    def domain_key(self) -> tuple[str, ...]:
        return tuple(getattr(self, field) for field in DOMAIN_FIELDS)

    @property
    def product_key(self) -> tuple[str, ...]:
        return tuple(getattr(self, field) for field in PRODUCT_FIELDS)

    @property
    def resource_key(self) -> tuple[str, ...]:
        return tuple(getattr(self, field) for field in RESOURCE_FIELDS)

    @property
    def natural_key(self) -> tuple[str, ...]:
        return (*self.resource_key, self.nominal_time.isoformat())

    def __str__(self) -> str:
        return ".".join(self.natural_key)
