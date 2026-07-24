from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Batch

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

        if job.backlog.produces_batches:
            self.resolve_batch(job)

        return job.submit()

    def resolve_batch(self, job: Job) -> Batch:
        job.info("📚 Preparing backlog")

        nominal_time = job.context.nominal_time
        resource = job.to_resource_dict()
        frontier = job.context.batch_registry.get_frontier(**resource)

        if not frontier:
            batch = Batch(
                **resource,
                nominal_time=nominal_time,
                nominal_end_time=nominal_time,
            )

        elif frontier.status.is_terminal():
            batch = Batch(
                **resource,
                nominal_time=nominal_time,
                nominal_start_time=frontier.nominal_end_time,
                nominal_end_time=nominal_time,
                bookmarks=frontier.bookmarks,
            )

        else:
            job.info(f"📚 Resuming {frontier.status} batch `{frontier}`")
            frontier.nominal_end_time = nominal_time
            return frontier

        batch = batch.register()
        job.info(f"📚 Added batch `{batch}` to backlog")
        return batch

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
