from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.assembly.plugin_template import PluginTemplateOverlay
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.utils import utcnow

if TYPE_CHECKING:
    from tiozin import Job


class JobProxy(wrapt.ObjectProxy):
    """
    Runtime proxy that enriches a Job with Tiozin's core capabilities.

    The JobProxy adds cross-cutting runtime features—such as templating, logging,
    context creation, and lifecycle control—to provider-defined Job implementations,
    without modifying the original plugin.

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
    environment for Job plugins.
    """

    def setup(self, context: Context) -> None:
        raise PluginAccessForbiddenError(self)

    def teardown(self, context: Context) -> None:
        raise PluginAccessForbiddenError(self)

    def submit(self, context: Context = None) -> Any:
        job: Job = self.__wrapped__
        context = context or Context.from_job(job)

        with PluginTemplateOverlay(job, context):
            try:
                job.info(f"▶️  Starting {context.kind}")
                job.debug(f"Temporary workdir is {context.temp_workdir}")
                context.setup_at = utcnow()
                job.setup(context)
                context.executed_at = utcnow()
                result = job.submit(context)
            except Exception:
                job.error(f"❌  {context.kind} failed in {context.delay:.2f}s")
                raise
            else:
                job.info(f"✅  {context.kind} finished in {context.delay:.2f}s")
                return result
            finally:
                context.teardown_at = utcnow()
                try:
                    job.teardown(context)
                except Exception as e:
                    job.error(f"🚨 {context.kind} teardown failed because {e}")
                context.finished_at = utcnow()

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
