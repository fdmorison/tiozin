from __future__ import annotations

from types import MappingProxyType as FrozenMapping
from typing import TYPE_CHECKING

import wrapt

from .. import TiozinTemplateOverlay
from ..templating.date import TemplateDate
from ..templating.env import TemplateEnv

if TYPE_CHECKING:
    from tiozin import Registry


class RegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps Registry plugins with template rendering support.

    Intercepts ``setup()`` and ``teardown()`` to apply a persistent
    ``TiozinTemplateOverlay`` for the entire registry lifetime. Templates in
    configuration values such as ``location`` are resolved at setup time and
    remain rendered until teardown.

    Template variables available during registry setup:

    - ``ENV``: read-only view of ``os.environ`` via ``SafeEnv``
    - ``DAY``: ``TemplateDate`` anchored to the moment ``setup()`` is called,
      plus all shorthand properties from ``TemplateDate.to_dict()``
      (e.g. ``ds``, ``ts``, ``flat_date``, …)

    This is an internal implementation detail. Tiozin developers should refer to
    the Registry base class for the public API contract.
    """

    _overlay: TiozinTemplateOverlay | None = None

    def setup(self, *args, **kwargs) -> None:
        registry: Registry = self.__wrapped__
        now = TemplateDate()
        template_vars = FrozenMapping(
            {
                "ENV": TemplateEnv(),
                **now.to_dict(),
                "DAY": now,
            }
        )
        self._overlay = TiozinTemplateOverlay(registry, template_vars)
        self._overlay.__enter__()
        registry.setup(*args, **kwargs)

    def teardown(self, *args, **kwargs) -> None:
        registry: Registry = self.__wrapped__
        registry.teardown(*args, **kwargs)
        if self._overlay:
            self._overlay.__exit__(None, None, None)
            self._overlay = None

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
