from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.exceptions import AccessViolationError
from tiozin.utils import human_join, utcnow

from .. import TiozinTemplateOverlay

if TYPE_CHECKING:
    from tiozin import Job


class JobProxy(wrapt.ObjectProxy):
    """
    Runtime proxy that enriches a Job with Tiozin's core capabilities.

    The JobProxy adds cross-cutting runtime features, such as templating, logging,
    context creation, and lifecycle control, to Tio-defined Job implementations,
    without modifying the original Tiozin plugin.

    The wrapped Job remains unaware of the proxy and is expected to focus exclusively
    on assembling and coordinating its steps, rather than managing runtime concerns.

    Core responsibilities include:
    - Managing the execution lifecycle (setup, execute, teardown)
    - Constructing and providing a Context for the Job execution
    - Initializing template variables and shared session state
    - Enforcing runtime constraints and access policies
    - Providing standardized logging, timing, and error handling

    This proxy belongs to Tiozin's runtime layer and is not an orchestration mechanism.
    It does not schedule jobs, manage dependencies between jobs, or perform distributed
    orchestration. Its responsibility is to provide a consistent and safe execution
    environment for Job Tiozin plugins.
    """

    def setup(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def submit(self) -> Any:
        job: Job = self.__wrapped__
        context = Context.for_job(job)

        with context, TiozinTemplateOverlay(job, context.template_vars):
            try:
                tios = [t.replace("_", " ").title() for t in job.tios]
                job.info(f"🚀 {context.kind} is starting — {human_join(tios)} on duty")
                job.debug(f"Temporary workdir is {context.temp_workdir}")
                context.setup_at = utcnow()
                job.setup()
                context.executed_at = utcnow()
                with job.runner():
                    result = job.submit()
            except Exception:
                job.error(f"❌  {context.kind} failed in {context.delay:.2f}s")
                raise
            else:
                job.info(f"✅  {context.kind} finished in {context.delay:.2f}s")
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
