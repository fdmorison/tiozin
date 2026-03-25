from __future__ import annotations

from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.exceptions import AccessViolationError, TiozinInternalError
from tiozin.utils import utcnow

from .. import TiozinTemplateOverlay

if TYPE_CHECKING:
    from tiozin import EtlStep, Lineage


class StepProxy(wrapt.ObjectProxy):
    """
    Wraps an Input, Transform, or Output to add Tiozin's runtime behavior.

    The wrapped step focuses on ETL logic. The proxy handles everything else:
    context propagation, template rendering, lifecycle hooks, logging, and timing.
    """

    def setup(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def read(self) -> None:
        return self._execute()

    def transform(self, *args, **kwargs) -> None:
        return self._execute(*args, **kwargs)

    def write(self, *args, **kwargs) -> None:
        return self._execute(*args, **kwargs)

    def lineage_datasets(self) -> Lineage:
        step: EtlStep = self.__wrapped__
        context = Context.for_step(step)
        with context, TiozinTemplateOverlay(step, context.template_vars):
            return step.lineage_datasets()

    def _execute(self, *args, **kwargs) -> Any:
        from tiozin import Input, Output, Transform

        step: EtlStep = self.__wrapped__
        context = Context.for_step(step)

        with context, TiozinTemplateOverlay(step, context.template_vars):
            try:
                step.info(f"▶️  Starting to {context.tiozin_role} data")
                step.debug(f"Temporary workdir is {context.temp_workdir}")
                context.setup_at = utcnow()
                step.setup(*args, **kwargs)
                context.executed_at = utcnow()
                match step:
                    case Input():
                        result = step.read(*args, **kwargs)
                    case Transform():
                        result = step.transform(*args, **kwargs)
                    case Output():
                        result = step.write(*args, **kwargs)
                    case _:
                        raise TiozinInternalError(f"Not a Tiozin: {step}")
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
