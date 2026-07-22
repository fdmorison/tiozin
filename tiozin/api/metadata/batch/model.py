from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, ClassVar, Self

from pydantic import ConfigDict, Field, PrivateAttr

from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.utils import current_context, isozformat, utcnow

from ...types import Attributes, Counter, NominalTime, TechnicalTime, TimeOrderedId
from ..model import Metadata
from .enums import BatchStatus
from .state import BatchState

if TYPE_CHECKING:
    from tiozin import BatchRegistry


class Batch(Metadata):
    """
    Stateful physical batch of data.

    A batch is a portion of data delimited by a nominal processing window. It
    may represent either an increment or the full history; the window, not the
    batch, determines which. Typical physical representations include
    partitions, files, offset ranges, or snapshots.

    A batch is not an execution. It remains the same batch regardless of how
    many executions are required to process it.

    Batches are uniquely identified by `(resource, nominal_time)`. Their status
    evolves over time as they are processed, replayed, quarantined, or canceled.

    Collections of batches form backlogs representing data awaiting processing.

    Attributes:
        id:
            Unique identifier of the batch. Generated as a UUIDv7, so ids are
            monotonically increasing and chronologically sortable.

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
            UTC datetime that uniquely identifies the logical execution time of the run.
            It represents the expected execution time rather than the actual execution time.
            Truncated according to the run cadence (minute precision by default).
            Equivalent to OpenLineage's nominal time concept, see
            https://openlineage.io/docs/1.47.0/spec/facets/run-facets/nominal_time/

        status:
            Current lifecycle status of the batch.

        attempts:
            Number of attempts to execute the batch since it was started for
            first time or replayed. Incremented on every begin.

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

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        validate_default=True,
    )

    _registry_ref: BatchRegistry = PrivateAttr(default=None)
    _attributes_snapshot: Attributes = PrivateAttr(default=None)

    resource_fields: ClassVar[tuple[str, ...]] = RESOURCE_FIELDS
    natural_key_fields: ClassVar[tuple[str, ...]] = (*RESOURCE_FIELDS, "nominal_time")

    id: TimeOrderedId = Field(frozen=True)

    org: str = Field(frozen=True)
    region: str = Field(frozen=True)
    domain: str = Field(frozen=True)
    subdomain: str = Field(frozen=True)
    layer: str = Field(frozen=True)
    product: str = Field(frozen=True)
    model: str = Field(frozen=True)

    nominal_time: NominalTime = Field(frozen=True)

    status: BatchStatus = BatchStatus.PENDING
    attempts: Counter
    state: BatchState = Field(default_factory=BatchState)
    attributes: Attributes

    created_at: TechnicalTime = Field(default_factory=utcnow, frozen=True)
    updated_at: TechnicalTime = Field(default_factory=utcnow)

    def model_post_init(self, __context) -> None:
        self._attributes_snapshot = deepcopy(self.attributes)

    def _registry(self) -> BatchRegistry:
        return self._registry_ref or current_context().registries.batch

    def register(self) -> Self:
        return self._registry().register(self)

    def begin(self, **attributes) -> Self:
        registry = self._registry()
        self.attempts += 1
        self.status = self.status.transition_to(BatchStatus.RUNNING, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def commit(self, **attributes) -> Self:
        registry = self._registry()
        self.status = self.status.transition_to(BatchStatus.SUCCEEDED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def rollback(self, error: Exception = None, **attributes) -> Self:
        registry = self._registry()
        self.attributes = deepcopy(self._attributes_snapshot)

        if error:
            self.attributes["__error"] = str(error)

        self.status = self.status.transition_to(BatchStatus.FAILED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def cancel(self, **attributes) -> Self:
        registry = self._registry()
        self.status = self.status.transition_to(BatchStatus.CANCELED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def quarantine(self, error: Exception = None, **attributes) -> Self:
        registry = self._registry()

        if error:
            self.attributes["__error"] = str(error)

        self.status = self.status.transition_to(BatchStatus.QUARANTINED, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

    def replay(self, **attributes) -> Self:
        registry = self._registry()
        self.attempts = 0
        self.status = self.status.transition_to(BatchStatus.PENDING, failfast=registry.failfast)
        self.attributes |= attributes
        return registry.register_transition(self)

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
