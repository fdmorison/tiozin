from __future__ import annotations

from collections.abc import Generator
from contextlib import _GeneratorContextManager, contextmanager
from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.exceptions import AccessViolationError

from .. import TiozinTemplateOverlay

if TYPE_CHECKING:
    from tiozin import Runner


class RunnerProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps Runner plugins with runtime capabilities.

    This proxy intercepts Runner lifecycle methods to add:
    - Template variable overlay from the caller's context
    - Standardized logging for setup, run, and teardown phases
    - Error handling and timing metrics

    Direct calls to setup() and teardown() are blocked; use the context
    manager interface instead: `with runner(context) as r: ...`

    This is an internal implementation detail. Tiozin developers should
    refer to the Runner base class for the public API contract.
    """

    def setup(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise AccessViolationError(self)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)

    def __call__(self) -> _GeneratorContextManager[RunnerProxy, None, None]:
        return self.activate()

    @contextmanager
    def activate(self) -> Generator[RunnerProxy, None, None]:
        runner: Runner = self.__wrapped__
        context = runner.context

        with TiozinTemplateOverlay(runner, context.template_vars):
            try:
                runner.info(f"▶️  Runner initialized for '{context.name}'")
                runner.setup()
                yield self
            finally:
                try:
                    runner.teardown()
                    runner.info(f"Runner released for '{context.name}'")
                except Exception as e:
                    runner.error(f"🚨 Runner cleanup failed for '{context.name}': {e}")

    def run(self, *args, **kwargs) -> Any:
        """Wraps Runner.run() with logging and error handling."""
        runner: Runner = self.__wrapped__
        context = runner.context
        try:
            runner.info(f"▶️  Running '{context.name}'")
            result = runner.run(*args, **kwargs)
        except Exception:
            runner.error(
                f"🚨 Failed execution of '{context.name}' in {context.execution_delay:.2f}s"
            )
            raise
        else:
            runner.info(
                f"✅ Completed execution of '{context.name}' in {context.execution_delay:.2f}s"
            )
            return result
