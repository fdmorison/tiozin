from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import StepContext
from tiozin.assembly.plugin_template import PluginTemplateOverlay
from tiozin.exceptions import PluginAccessForbiddenError, TiozinUnexpectedError
from tiozin.utils.helpers import utcnow

if TYPE_CHECKING:
    from tiozin import JobContext


class StepProxy(wrapt.ObjectProxy):
    """
    Runtime proxy that enriches a Step with Tiozin's core capabilities.

    The StepProxy adds cross-cutting runtime features—such as templating, logging,
    context propagation, and lifecycle control—to provider-defined Input, Transform,
    and Output implementations, without modifying the original plugin.

    The wrapped Step remains unaware of the proxy and is expected to focus exclusively
    on its domain-specific data logic.

    Core responsibilities include:
    - Managing the execution lifecycle (setup, execute, teardown)
    - Constructing and providing a StepContext from a JobContext
    - Propagating template variables and shared session state
    - Enforcing runtime constraints and access policies
    - Providing standardized logging, timing, and error handling

    This proxy belongs to Tiozin's runtime layer and is not an orchestration mechanism.
    It does not schedule executions, manage dependencies, or define execution order.
    Its responsibility is to provide a consistent and safe execution environment for
    Step plugins.
    """

    def execute(self, context: JobContext, *args, **kwargs) -> Any:
        from tiozin import Input, Output, Transform

        step: Transform | Input | Output = self.__wrapped__

        context = StepContext(
            # Job
            job=context,
            # Identity
            name=step.name,
            kind=step.plugin_name,
            plugin_kind=step.plugin_kind,
            # Fundamentals
            org=step.org,
            region=step.region,
            domain=step.domain,
            layer=step.layer,
            product=step.product,
            model=step.model,
            # Templating
            template_vars=context.template_vars,
            # Shared state
            session=context.session,
            # Extra provider/plugin parameters
            options=step.options,
        )

        try:
            context.setup_at = utcnow()
            step.setup(context, *args, **kwargs)
            step.info(f"▶️  Starting to {context.plugin_kind} data")
            step.debug(f"Temporary directory is {context.tempdir}")
            with PluginTemplateOverlay(step, context):
                context.executed_at = utcnow()
                result = None
                match step:
                    case Input():
                        result = step.read(context)
                    case Transform():
                        result = step.transform(context, *args, **kwargs)
                    case Output():
                        result = step.write(context, *args, **kwargs)
                    case _:
                        raise TiozinUnexpectedError(
                            "Expected an Input, Transform, or Output step, "
                            f"but received an instance of {type(step).__name__}. "
                            "Only pipeline steps may be part of a Job."
                        )
        except Exception:
            step.error(f"❌  {context.kind} failed after {context.execution_delay:.2f}s")
            raise
        else:
            step.info(f"✔️  {context.kind} finished after {context.execution_delay:.2f}s")
            return result
        finally:
            context.teardown_at = utcnow()
            try:
                step.teardown(context, *args, **kwargs)
            except Exception as e:
                # TODO Fix: exc_info=True is failing and does not show error message
                step.error(f"🚨 {context.kind} teardown failed because {e}")
            context.finished_at = utcnow()

    def setup(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
