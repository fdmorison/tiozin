from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import wrapt

from tiozin.compose import TiozinTemplateOverlay
from tiozin.compose.templating.date import TemplateDate
from tiozin.compose.templating.env import TemplateEnv

if TYPE_CHECKING:
    from tiozin import Registry


class RegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that enables template variables in Registry attributes.

    During setup, string attributes can reference runtime values such as
    {{ ENV.HOME }} or {{ DAY.ds }}. The rendered values remain available for
    the entire registry lifetime and are restored to their original values on
    teardown.

    Available template variables:

    - ENV: read-only access to environment variables.
    - DAY: TemplateDate representing the setup timestamp.

    This is an internal implementation detail. Tiozin developers should refer to
    the Registry base class for the public API contract.
    """

    def __init__(self, wrapped) -> None:
        super().__init__(wrapped)
        self._self_context = contextlib.ExitStack()

    @property
    def registry(self) -> Registry:
        return self.__wrapped__

    @wrapt.synchronized
    def setup(self) -> None:
        if self.registry.ready:
            return

        try:
            now = TemplateDate()
            template_vars = now.to_dict()
            template_vars["DAY"] = now
            template_vars["ENV"] = TemplateEnv()

            self._self_context.enter_context(TiozinTemplateOverlay(self.registry, template_vars))
            self.registry.setup()
            self.registry.ready = True
        except Exception as e:
            self.registry.error(f"🚨 Setup failed: {e}.")
            self._self_context.close()
            if self.registry.failfast:
                raise

    @wrapt.synchronized
    def teardown(self) -> None:
        if not self.registry.ready:
            return

        try:
            self.registry.teardown()
        except Exception:
            self.registry.exception("🚨 Shutdown failed.")
        finally:
            self._self_context.close()
            self.registry.ready = False

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
