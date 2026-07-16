from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.utils import batched

if TYPE_CHECKING:
    from tiozin.api import Batch

    from .base import Job


class JobBacklogProxy(wrapt.ObjectProxy):
    """
    Internal proxy that consumes a Job backlog transactionally.

    Splits the backlog into chunks of at most `max_batches_per_run` batches and
    runs once per chunk, where all batches succeed or fail together.

    When the backlog is empty, the job runs once unless its `batch_source`
    skips on an empty backlog (UPSTREAM), in which case execution is skipped.

    This is an internal implementation detail. Tiozin developers should
    refer to the Job base class for the public API contract.
    """

    def submit(self) -> Any:
        job: Job = self.__wrapped__
        registry = Context.current().batch_registry
        runs = [()]

        job.info(f"📚 Loading backlog for `{job.qualified_resource}`")
        backlog = registry.get_backlog(**job.to_resource_dict())
        job.info(f"📚 Found {len(backlog)} batches in backlog")

        if not backlog and not job.batch_source.runs_on_empty_backlog:
            job.warning("📚 Skipping execution: no batches to process")
            return []

        if backlog:
            runs = list(batched(backlog, job.max_batches_per_run))
            job.info(
                f"📚 The backlog will be processed in {len(runs)} runs of "
                f"{job.max_batches_per_run} batches each."
            )

        return [self.submit_run(job, batches) for batches in runs]

    def submit_run(self, job: Job, batches: tuple[Batch, ...]) -> Any:
        for batch in batches:
            batch.begin()

        try:
            result = job.submit()
        except Exception as error:
            for batch in batches:
                batch.fail(__error=error)
            raise
        else:
            for batch in batches:
                batch.commit()
            return result

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
