from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from pendulum import DateTime

from tiozin.utils import utcnow

if TYPE_CHECKING:
    from tiozin.api.runtime.context import Context


class RunState(StrEnum):
    START = "START"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    ABORT = "ABORT"


@dataclass
class RunEvent:
    """
    Represents an OpenLineage run event.

    Captures the state of a job run at a specific point in time,
    including its identity, inputs, and outputs.
    """

    state: RunState
    job: str
    namespace: str
    run_id: str
    event_time: DateTime
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    @classmethod
    def from_context(
        cls,
        context: Context,
        state: RunState,
        inputs: list[str] = None,
        outputs: list[str] = None,
    ) -> RunEvent:
        """Build a `RunEvent` from an active execution context."""
        return cls(
            state=state,
            job=context.slug,
            namespace=f"{context.org}.{context.region}.{context.domain}.{context.subdomain}.{context.layer}",
            run_id=context.run_id,
            event_time=utcnow(),
            inputs=inputs or [],
            outputs=outputs or [],
        )
