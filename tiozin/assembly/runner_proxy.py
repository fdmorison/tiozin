from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import RunnerContext
from tiozin.assembly.templating import PluginTemplateOverlay
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.utils.helpers import utcnow

if TYPE_CHECKING:
    from tiozin import JobContext, Runner

_LIFECYCLE_METHODS = {"setup", "teardown"}


class RunnerProxy(wrapt.ObjectProxy):
    """
    Runtime proxy that enriches a Runner with Tiozin's core capabilities.

    The RunnerProxy adds cross-cutting runtime features—such as templating, logging,
    context propagation, and lifecycle control—to provider-defined Runner implementations,
    without modifying the original plugin.

    The wrapped Runner remains unaware of the proxy and is expected to focus exclusively
    on its domain-specific execution logic.

    Core responsibilities include:
    - Managing the execution lifecycle (setup, execute, teardown)
    - Constructing and providing a RunnerContext from a JobContext
    - Propagating template variables and shared session state
    - Enforcing runtime constraints and access policies
    - Providing standardized logging, timing, and error handling

    This proxy belongs to Tiozin's runtime layer and is not an orchestration mechanism.
    It does not schedule executions, manage dependencies, or define execution order.
    Its responsibility is to provide a consistent and safe execution environment for
    Runner plugins.
    """

    def execute(self, context: JobContext, *args, **kwargs) -> Any:
        plugin: Runner = self.__wrapped__

        context = RunnerContext(
            # Job
            job=context,
            # Identity
            id=plugin.id,
            name=plugin.name,
            kind=plugin.plugin_name,
            plugin_kind=plugin.plugin_kind,
            # Templating
            template_vars=context.template_vars,
            # Shared state
            session=context.session,
            # Extra provider/plugin parameters
            options=plugin.options,
        )

        try:
            context.setup_at = utcnow()
            plugin.setup(context, **kwargs)
            plugin.info(f"▶️  Starting the {context.kind}")
            with PluginTemplateOverlay(plugin, context):
                context.executed_at = utcnow()
                result = plugin.execute(context, *args, **kwargs)
        except Exception:
            plugin.error(f"❌  {context.kind} failed after {context.execution_delay:.2f}s")
            raise
        else:
            plugin.info(f"✔️  {context.kind} finished after {context.execution_delay:.2f}s")
            return result
        finally:
            context.teardown_at = utcnow()
            try:
                plugin.teardown(context, **kwargs)
            except Exception as e:
                # TODO Fix: exc_info=True is failing and does not show error message
                plugin.error(f"🚨 {context.kind} teardown failed because {e}")
            context.finished_at = utcnow()

    def __getattr__(self, name: str) -> Any:
        if name in _LIFECYCLE_METHODS:
            raise PluginAccessForbiddenError(self)
        return super().__getattr__(name)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
