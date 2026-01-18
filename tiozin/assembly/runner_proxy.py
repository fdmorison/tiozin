from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import RunnerContext
from tiozin.assembly.plugin_template import PluginTemplateOverlay
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.utils.helpers import utcnow

if TYPE_CHECKING:
    from tiozin import JobContext, Runner


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
        runner: Runner = self.__wrapped__

        context = RunnerContext(
            # Job
            job=context,
            # Identity
            name=runner.name,
            kind=runner.plugin_name,
            plugin_kind=runner.plugin_kind,
            # Templating
            template_vars=context.template_vars,
            # Shared state
            session=context.session,
            # Extra provider/plugin parameters
            options=runner.options,
        )

        try:
            runner.info(f"▶️  Starting the {context.kind}")
            runner.debug(f"Temporary workdir is {context.temp_workdir}")
            context.setup_at = utcnow()
            runner.setup(context)
            with PluginTemplateOverlay(runner, context):
                context.executed_at = utcnow()
                result = runner.run(context, *args, **kwargs)
        except Exception:
            runner.error(f"❌  {context.kind} failed after {context.execution_delay:.2f}s")
            raise
        else:
            runner.info(f"✔️  {context.kind} finished after {context.execution_delay:.2f}s")
            return result
        finally:
            context.teardown_at = utcnow()
            try:
                runner.teardown(context)
            except Exception as e:
                # TODO Fix: exc_info=True is failing and does not show error message
                runner.error(f"🚨 {context.kind} teardown failed because {e}")
            context.finished_at = utcnow()

    def setup(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
