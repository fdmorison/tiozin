from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

from tiozin.exceptions import TiozinInternalError

if TYPE_CHECKING:
    from tiozin.api import SettingRegistry


class SettingRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that resolves settings delegation during setup.

    When `setup()` is called, it boots the wrapped registry and then follows
    the delegation chain, replacing the wrapped instance with the final resolved
    registry. After setup, all calls transparently target the resolved registry
    without the caller needing to know about delegation.

    This is an internal implementation detail of the settings boot process.
    """

    def setup(self, *args, **kwargs) -> None:
        from tiozin.compose.assembly.tiozin_factory import tiozin_factory

        registry: SettingRegistry = self.__wrapped__
        visited = []

        while True:
            TiozinInternalError.raise_if(
                registry.location in visited,
                f"Circular settings delegation detected: {visited + [registry.location]}",
            )
            visited.append(registry.location)

            registry.setup(*args, **kwargs)
            settings = registry.get()
            if settings is None:
                break

            target_registry = settings.registries.setting
            if target_registry is None:
                break

            next_registry: SettingRegistry = tiozin_factory.load_manifest(target_registry)
            TiozinInternalError.raise_if(
                not next_registry.location,
                f"Declared settings registry '{next_registry.kind}' has no location.",
            )
            registry = next_registry

        self.__wrapped__ = registry
