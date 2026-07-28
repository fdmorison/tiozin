from __future__ import annotations

from collections.abc import Generator
from contextlib import _GeneratorContextManager, contextmanager
from typing import TYPE_CHECKING, Any

import wrapt

from tiozin.exceptions import AccessViolationError
from tiozin.utils.decorators import log_delay

from ....compose import TiozinTemplateOverlay
from ..dataset import Dataset

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

    def setup(self) -> None:
        raise AccessViolationError(self)

    def teardown(self) -> None:
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
                runner.info(f"⏳ Initializing `{runner.name}` runtime resources...")
                runner.setup()
                runner.info(f"🟢 `{runner.name}` runtime resources initialized successfully")
                yield self
            finally:
                try:
                    runner.info(f"🛑 Releasing `{runner.name}` runtime resources")
                    runner.info(f"⏳ Releasing `{runner.name}` runtime resources...")
                    runner.teardown()

                except Exception as e:
                    runner.error(f"🚨 Runner teardown failed: {e}")

    @log_delay("Runner")
    def run(self, *args, **kwargs) -> Any:
        runner: Runner = self.__wrapped__
        raw_args = [Dataset.unwrap(arg) for arg in args]
        result = runner.run(*raw_args, **kwargs)
        return Dataset.unwrap(result)
