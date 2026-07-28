from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Batch
from tiozin.utils import isozformat

if TYPE_CHECKING:
    from .base import Job


class BacklogProducerJobProxy(wrapt.ObjectProxy):
    """
    Internal proxy for incremental jobs that produce their own backlog.

    It preserves bookmark state across executions, allowing the job to update
    watermarks, checkpoints, tokens, and other progress markers.

    To do so, it maintains a single active batch (the frontier), resuming it
    across executions until it reaches a terminal state before creating the next
    batch.

    Previously terminal batches (non-frontier) may still be replayed, so plugin
    developers should ensure their bookmark updates are replay-safe.

    This is an internal implementation detail. Tiozin developers should refer
    to the Job base class for the public API contract.
    """

    def submit(self) -> Any:
        job: Job = self.__wrapped__

        if job.backlog_policy.produces_backlog:
            self._produce_backlog(job)

        return job.submit()

    def _produce_backlog(self, job: Job) -> Batch:
        nominal_time = job.context.nominal_time
        resource = job.to_resource_dict()
        frontier = job.context.batch_registry.get_frontier(**resource)

        if not frontier:
            batch = Batch(
                **resource,
                nominal_time=nominal_time,
                nominal_end_time=nominal_time,
            ).register()
            job.info(f"📚 Created initial backlog batch `{batch}`")
            return batch

        if frontier.status.is_operational():
            job.info(
                f"📚 Resuming {frontier.status} batch `{frontier}` "
                f"by extending its nominal window to `{nominal_time}`"
            )
            frontier.nominal_end_time = nominal_time
            return frontier

        if frontier.nominal_time == nominal_time:
            job.warning(
                f"📚 No batch added to the backlog: nominal time "
                f"`{isozformat(nominal_time)}` is already {frontier.status}. "
                f"To process it again, replay it with `tiozin batch replay <job> {frontier.id}`."
            )
            return None

        batch = Batch(
            **resource,
            nominal_time=nominal_time,
            nominal_start_time=frontier.nominal_end_time,
            nominal_end_time=nominal_time,
            bookmarks=frontier.next_bookmarks(),
        ).register()

        job.info(f"📚 Added batch `{batch}` to backlog")
        return batch

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
