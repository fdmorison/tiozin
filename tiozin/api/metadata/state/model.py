from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any
from uuid import NAMESPACE_OID, uuid5

from pydantic import Field, model_validator

from tiozin.api.conventions import DOMAIN_FIELDS, PRODUCT_FIELDS, RESOURCE_FIELDS
from tiozin.utils import utcnow

from ..model import Metadata
from .status import BatchStatus

if TYPE_CHECKING:
    from tiozin.api.metadata.state.registry import StateRegistry


class State(Metadata):
    """
    Represents the lifecycle of a logical batch of data.

    A state uniquely identifies a batch within a resource and tracks its
    processing lifecycle. A batch may represent a partition, file, offset,
    snapshot, or any other job-defined unit of work.

    States are uniquely identified by `(resource, batch_key)`. Their status
    evolves over time as the batch progresses through processing, replay,
    quarantine, or cancellation.

    Collections of states support higher-level concepts such as:

    - Watermarks, representing the highest successfully processed batch.
    - Backlogs, representing batches awaiting processing.

    Attributes:
        id:
            Deterministic UUID derived from the natural key
            (`resource + batch_key`). Stable across updates to the same state.

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

        batch_key:
            Job-defined identifier of the logical batch represented by this state. Typical values
            include partition dates, filenames, offsets, snapshot identifiers, or any other value
            that uniquely identifies a batch within the resource.

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
            UTC timestamp when the state was first registered.

        updated_at:
            UTC timestamp when the state was last updated.
    """

    id: str | None = None

    org: str
    region: str
    domain: str
    subdomain: str
    layer: str
    product: str
    model: str

    batch_key: str
    status: BatchStatus = BatchStatus.PENDING
    failure_count: int = Field(0, ge=0)
    attributes: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def _init(self) -> State:
        if not self.id:
            self.id = str(uuid5(NAMESPACE_OID, ".".join(self.natural_key)))
        return self

    def _registry(self) -> StateRegistry:
        from tiozin.api.context import Context

        return Context.current().registries.state

    def register(self) -> State:
        self._registry().register(self)
        return self

    def begin(self, **attributes) -> State:
        self.attributes |= attributes
        self._registry().begin(self)
        return self

    def commit(self, **attributes) -> State:
        self.attributes |= attributes
        self._registry().commit(self)
        return self

    def fail(self, **attributes) -> State:
        self.attributes |= attributes
        self.failure_count += 1
        self._registry().fail(self)
        return self

    def cancel(self, **attributes) -> State:
        self.attributes |= attributes
        self._registry().cancel(self)
        return self

    def quarantine(self, **attributes) -> State:
        self.attributes |= attributes
        self._registry().quarantine(self)
        return self

    def replay(self, **attributes) -> State:
        self.attributes |= attributes
        self.failure_count = 0
        self._registry().replay(self)
        return self

    @property
    def batch_date(self) -> date:
        return date.fromisoformat(self.batch_key)

    @batch_date.setter
    def batch_date(self, value: date | datetime) -> None:
        if isinstance(value, datetime):
            value = value.date()
        self.batch_key = value.isoformat()

    @property
    def batch_timestamp(self) -> datetime:
        return datetime.fromisoformat(self.batch_key)

    @batch_timestamp.setter
    def batch_timestamp(self, value: date | datetime) -> None:
        if type(value) is date:
            value = datetime(value.year, value.month, value.day, tzinfo=UTC)
        self.batch_key = value.isoformat()

    @property
    def batch_int(self) -> int:
        return int(self.batch_key)

    @batch_int.setter
    def batch_int(self, value: int) -> None:
        self.batch_key = str(value)

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
        return (*self.resource_key, self.batch_key)

    def __str__(self) -> str:
        return ".".join(self.natural_key)
