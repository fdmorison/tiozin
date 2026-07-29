from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.exceptions import AccessViolationError
from tiozin.utils import human_join, isozformat, utcnow
from tiozin.utils.decorators import log_delay

from ....compose import TiozinTemplateOverlay

if TYPE_CHECKING:
    from .base import Job


class JobProxy(wrapt.ObjectProxy):
    """
    Wraps a Job to add Tiozin's runtime behavior.

    The wrapped job focuses on assembling and coordinating steps. The proxy handles
    everything else: context propagation, template rendering, lifecycle hooks, logging,
    timing, and lineage emission.
    """

    def setup(self) -> None:
        raise AccessViolationError(self)

    def teardown(self) -> None:
        raise AccessViolationError(self)

    def submit(self) -> Any:
        job: Job = self.__wrapped__
        context = Context.current(required=False) or Context.for_job(job)

        with context:
            return self._submit(job, context)

    @log_delay("Job")
    def _submit(self, job: Job, context: Context) -> Any:
        lineage = context.registries.lineage
        catalog = context.catalog
        families = [t.replace("_", " ").title() for t in job.families]

        job.info(
            f"🚀 Starting `{context.name}` with {human_join(families)}",
            namespace=context.namespace,
            run_id=context.run_id,
            nominal_time=isozformat(context.nominal_time),
            cadence=context.cadence,
            backlog_policy=context.backlog_policy,
        )

        with TiozinTemplateOverlay(job, context.template_vars), job.runner():
            try:
                job.debug(f"Temporary workdir is {context.temp_workdir}")

                context.setup_at = utcnow()
                job.setup()

                context.executed_at = utcnow()
                lineage.run_started(inputs=[], outputs=[])
                result = job.submit()

            except Exception:
                lineage.run_failed(
                    inputs=catalog.get_inputs(job.inputs),
                    outputs=catalog.get_outputs(job.outputs),
                )
                raise

            else:
                lineage.run_completed(
                    inputs=catalog.get_inputs(job.inputs),
                    outputs=catalog.get_outputs(job.outputs),
                )
                return result

            finally:
                context.teardown_at = utcnow()
                try:
                    job.teardown()
                except Exception as e:
                    job.error(f"🚨 `{context.name}` teardown failed because {e}")
                context.finished_at = utcnow()

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
