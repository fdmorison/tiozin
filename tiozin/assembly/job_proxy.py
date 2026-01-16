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
        plugin: Job = self.__wrapped__

        context = JobContext(
            # Identity
            id=plugin.id,
            name=plugin.name,
            kind=plugin.plugin_name,
            plugin_kind=plugin.plugin_kind,
            # Fundamentals
            maintainer=plugin.maintainer,
            cost_center=plugin.cost_center,
            owner=plugin.owner,
            labels=plugin.labels,
            org=plugin.org,
            region=plugin.region,
            domain=plugin.domain,
            layer=plugin.layer,
            product=plugin.product,
            model=plugin.model,
            # Runtime
            runner=plugin.runner,
            # Templating
            template_vars={},
            # Shared state
            session={},
            # Extra provider/plugin parameters
            options=plugin.options,
        )

        try:
            context.setup_at = utcnow()
            plugin.setup(context, *args, **kwargs)
            plugin.info(f"▶️  Starting {context.kind}")
            with PluginTemplateOverlay(plugin, context):
                context.executed_at = utcnow()
                result = plugin.execute(context, *args, **kwargs)
        except Exception:
            plugin.error(f"❌  {context.kind} failed after {context.delay:.2f}s")
            raise
        else:
            plugin.info(f"✔️  {context.kind} finished after {context.delay:.2f}s")
            return result
        finally:
            context.teardown_at = utcnow()
            try:
                plugin.teardown(context, *args, **kwargs)
            except Exception as e:
                # TODO Fix: exc_info=True is failing and does not show error message
                plugin.error(f"🚨 {context.kind} teardown failed because {e}")
            context.finished_at = utcnow()

    def setup(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
