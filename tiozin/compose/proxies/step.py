from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.exceptions import PluginAccessForbiddenError
from tiozin.utils import utcnow

from .. import TiozinTemplateOverlay

if TYPE_CHECKING:
    from tiozin import EtlStep


class StepProxy(wrapt.ObjectProxy):
    """
    Runtime proxy that enriches a Step with Tiozin's core capabilities.

    The StepProxy adds cross-cutting runtime features such as templating, logging, context
    propagation, and lifecycle control to Input, Transform, and Output implementations without
    modifying the original class. This is the recommended way to implement features
    in a Tio provider.

    The wrapped Step remains unaware of the proxy and is expected to focus exclusively on
    domain-specific ETL logic, while the proxy handles boilerplate concerns.

    Core responsibilities include:
    - Managing the execution lifecycle (setup, execute, teardown)
    - Constructing and providing a Context from a Context
    - Propagating template variables and shared session state
    - Enforcing runtime constraints and access policies
    - Providing standardized logging, timing, and error handling

    This proxy belongs to Tiozin's runtime layer and is not an orchestration mechanism.
    It does not schedule executions, manage dependencies, or define execution order.
    Its responsibility is to provide a consistent and safe execution environment for
    Step plugins.
    """

    def setup(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def read(self) -> None:
        return self._run("read")

    def transform(self, *args, **kwargs) -> None:
        return self._run("transform", *args, **kwargs)

    def write(self, *args, **kwargs) -> None:
        return self._run("write", *args, **kwargs)

    def _run(self, method_name: str, *args, **kwargs) -> Any:
        step: EtlStep = self.__wrapped__

        context = (
            current.for_child_step(step)
            if (current := Context.current(required=False))
            else Context.for_step(step)
        )

        with context, TiozinTemplateOverlay(step, context.template_vars):
            try:
                step.info(f"▶️  Starting to {context.tiozin_kind} data")
                step.debug(f"Temporary workdir is {context.temp_workdir}")
                context.setup_at = utcnow()
                step.setup(*args, **kwargs)
                context.executed_at = utcnow()
                execute = getattr(step, method_name)
                result = execute(*args, **kwargs)
            except Exception:
                step.error(f"{context.kind} failed in {context.execution_delay:.2f}s")
                raise
            else:
                step.info(f"{context.kind} finished in {context.execution_delay:.2f}s")
                return result
            finally:
                context.teardown_at = utcnow()
                try:
                    step.teardown(*args, **kwargs)
                except Exception as e:
                    step.error(f"🚨 {context.kind} teardown failed because {e}")
                context.finished_at = utcnow()

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
