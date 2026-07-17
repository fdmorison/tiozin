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
    Internal proxy that executes jobs over pending backlogs.

    It extends the Job execution model with backlog consumption, allowing a single
    job to process one or more pending batches transactionally across multiple runs.

    This is an internal implementation detail. Tiozin developers should refer to
    the Job base class for the public API contract.
    """

    def submit(self) -> Any:
        job: Job = self.__wrapped__
        runs = [()]

        job.info(f"📚 Loading backlog for `{job.qualified_resource}`")
        backlog = Context.current().batch_registry.get_backlog(**job.to_resource_dict())
        job.info(f"📚 Found {len(backlog)} batches in backlog")

        if not backlog and not job.backlog.runs_on_empty_backlog:
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
            Context.current().catalog.register(job, backlog=list(batches))
            result = job.submit()
        except Exception as error:
            for batch in batches:
                batch.rollback(error=error)
            raise
        else:
            for batch in batches:
                batch.commit()
            return result

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
