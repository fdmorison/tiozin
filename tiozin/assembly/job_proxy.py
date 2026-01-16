from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import JobContext
from tiozin.assembly.templating import PluginTemplateOverlay
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.utils.helpers import utcnow

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
    - Constructing and providing a JobContext for the Job execution
    - Initializing template variables and shared session state
    - Enforcing runtime constraints and access policies
    - Providing standardized logging, timing, and error handling

    This proxy belongs to Tiozin's runtime layer and is not an orchestration mechanism.
    It does not schedule jobs, manage dependencies between jobs, or perform distributed
    orchestration. Its responsibility is to provide a consistent and safe execution
    environment for Job plugins.
    """

    def execute(self, *args, **kwargs) -> Any:
        job: Job = self.__wrapped__

        context = JobContext(
            # Identity
            name=job.name,
            kind=job.plugin_name,
            plugin_kind=job.plugin_kind,
            # Fundamentals
            maintainer=job.maintainer,
            cost_center=job.cost_center,
            owner=job.owner,
            labels=job.labels,
            org=job.org,
            region=job.region,
            domain=job.domain,
            layer=job.layer,
            product=job.product,
            model=job.model,
            # Runtime
            runner=job.runner,
            # Templating
            template_vars={},
            # Shared state
            session={},
            # Extra provider/plugin parameters
            options=job.options,
        )

        try:
            context.setup_at = utcnow()
            job.setup(context)
            job.info(f"▶️  Starting {context.kind}")
            with PluginTemplateOverlay(job, context):
                context.executed_at = utcnow()
                result = job.run(context, *args, **kwargs)
        except Exception:
            job.error(f"❌  {context.kind} failed after {context.delay:.2f}s")
            raise
        else:
            job.info(f"✔️  {context.kind} finished after {context.delay:.2f}s")
            return result
        finally:
            context.teardown_at = utcnow()
            try:
                job.teardown(context)
            except Exception as e:
                # TODO Fix: exc_info=True is failing and does not show error message
                job.error(f"🚨 {context.kind} teardown failed because {e}")
            context.finished_at = utcnow()

    def setup(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
