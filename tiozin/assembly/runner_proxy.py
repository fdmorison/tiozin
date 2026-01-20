from __future__ import annotations

from collections.abc import Generator
from contextlib import _GeneratorContextManager, contextmanager
from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.api import Context
from tiozin.assembly.plugin_template import PluginTemplateOverlay
from tiozin.exceptions import PluginAccessForbiddenError

if TYPE_CHECKING:
    from tiozin import JobContext, Runner


class RunnerProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps Runner plugins with runtime capabilities.

    This proxy intercepts Runner lifecycle methods to add:
    - Template variable overlay from the caller's context
    - Standardized logging for setup, run, and teardown phases
    - Error handling and timing metrics

    Direct calls to setup() and teardown() are blocked; use the context
    manager interface instead: `with runner(context) as r: ...`

    This is an internal implementation detail. Plugin developers should
    refer to the Runner base class for the public API contract.
    """

    def setup(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def teardown(self, *args, **kwargs) -> None:
        raise PluginAccessForbiddenError(self)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)

    def __call__(self, context: JobContext) -> _GeneratorContextManager[RunnerProxy, None, None]:
        return self.contextmanager(context)

    @contextmanager
    def contextmanager(self, context: JobContext) -> Generator[RunnerProxy, Any, None]:
        runner: Runner = self.__wrapped__

        with PluginTemplateOverlay(runner, context):
            try:
                runner.info(f"▶️  Runner initialized by {context.name}")
                runner.setup(context)
                yield self
            finally:
                try:
                    runner.teardown(context)
                    runner.info(f"Runner released by {context.name}")
                except Exception as e:
                    runner.error(f"🚨 Runner cleanup failed for {context.name}: {e}")

    def run(self, context: Context, *args, **kwargs) -> Any:
        """Wraps Runner.run() with logging and error handling."""
        try:
            runner: Runner = self.__wrapped__
            runner.info(f"▶️  Submiting execution of '{context.name}'")
            result = runner.run(context, *args, **kwargs)
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
