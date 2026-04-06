from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.exceptions import AccessViolationError
from tiozin.utils import human_join, utcnow

from ...compose import TiozinTemplateOverlay

if TYPE_CHECKING:
    from .job import Job


class JobProxy(wrapt.ObjectProxy):
    """
    Wraps a Job to add Tiozin's runtime behavior.

    The wrapped job focuses on assembling and coordinating steps. The proxy handles
    everything else: context propagation, template rendering, lifecycle hooks, logging,
    timing, and lineage emission.
    """

    def setup(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def submit(self) -> Any:
        job: Job = self.__wrapped__
        context = Context.current(required=False) or Context.for_job(job)
        lineage = context.registries.lineage
        catalog = context.catalog

        with context, TiozinTemplateOverlay(job, context.template_vars):
            try:
                families = [t.replace("_", " ").title() for t in job.families]
                job.info(f"🚀 Job `{context.name}` is starting — {human_join(families)} on duty")
                job.debug(f"Temporary workdir is {context.temp_workdir}")

                context.setup_at = utcnow()
                job.setup()
                context.executed_at = utcnow()

                with job.runner():
                    lineage.start(inputs=[], outputs=[])
                    result = job.submit()

            except Exception:
                job.error(f"❌  {context.kind} failed in {context.delay:.2f}s")
                lineage.fail(
                    inputs=catalog.get_inputs(job.inputs),
                    outputs=catalog.get_outputs(job.outputs),
                )
                raise

            else:
                job.info(f"✅  {context.kind} finished in {context.delay:.2f}s")
                lineage.complete(
                    inputs=catalog.get_inputs(job.inputs),
                    outputs=catalog.get_outputs(job.outputs),
                )
                return result

            finally:
                context.teardown_at = utcnow()
                try:
                    job.teardown()
                except Exception as e:
                    job.error(f"🚨 {context.kind} teardown failed because {e}")
                context.finished_at = utcnow()

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
