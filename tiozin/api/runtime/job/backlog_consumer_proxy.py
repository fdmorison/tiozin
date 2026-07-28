from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.utils import batched

if TYPE_CHECKING:
    from tiozin.api import Batch

    from .base import Job


class BacklogConsumerJobProxy(wrapt.ObjectProxy):
    """
    Internal proxy that executes jobs over pending backlogs.

    It extends the Job execution model with backlog consumption, allowing a single
    job to process one or more pending batches transactionally across multiple runs.

    This is an internal implementation detail. Tiozin developers should refer to
    the Job base class for the public API contract.
    """

    def submit(self) -> list[Any]:
        job: Job = self.__wrapped__

        if job.backlog_policy.consumes_backlog:
            return self._submit_backlog()

        return [job.submit()]

    def _submit_backlog(self) -> Any:
        job: Job = self.__wrapped__

        backlog = job.context.batch_registry.get_backlog(**job.to_resource_dict())
        job.info(f"📚 Backlog has {len(backlog)} pending batches")

        sliced_backlog = batched(backlog, job.max_batches_per_run)
        return [self._submit_backlog_slice(batch) for batch in sliced_backlog]

    def _submit_backlog_slice(self, batches: tuple[Batch, ...]) -> Any:
        job: Job = self.__wrapped__
        max_retries = job.context.batch_registry.retries

        for batch in batches:
            job.info(f"📦 Processing batch `{batch}`")
            batch.begin()

        try:
            job.context.catalog.register(job, backlog=list(batches))
            result = job.submit()
        except Exception as error:
            for batch in batches:
                if batch.retries < max_retries:
                    batch.rollback(error)
                else:
                    batch.quarantine(error)
            raise
        else:
            for batch in batches:
                batch.commit()
            return result

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
