from __future__ import annotations

from tiozin.exceptions import TiozinInternalError

from .. import Registry, SettingsManifest


class SettingRegistry(Registry[SettingsManifest]):
    """
    Manages system settings and configuration.

    Storage-agnostic contract for setting backends (like databases, YAML files, or Consul).
    Available in Context for configuration access in Transforms, Inputs, and Outputs.
    """

    def delegate(self) -> SettingRegistry:
        """
        Resolve the final settings registry through delegation.

        Reads ``registries.settings`` from the loaded manifest. If it is not
        ``None``, loads the referenced registry and repeats. Stops when:

        - ``registries.settings`` is ``None`` in the current manifest, or
        - the loaded registry's ``get()`` returns ``None`` (e.g. a NoOp).

        Location strings are used to detect circular delegation.

        Returns:
            The resolved ``SettingRegistry`` instance.

        Raises:
            TiozinInternalError: If circular delegation is detected.
        """
        from tiozin.compose.assembly.tiozin_factory import tiozin_factory

        registry = self
        visited = []

        while True:
            TiozinInternalError.raise_if(
                registry.location in visited,
                f"Circular settings delegation detected: {visited + [registry.location]}",
            )
            visited.append(registry.location)

            settings: SettingsManifest = registry.get()
            if settings is None:
                break

            target_registry = settings.registries.settings
            if target_registry is None:
                break

            next_registry: SettingRegistry = tiozin_factory.load_manifest(target_registry)
            TiozinInternalError.raise_if(
                not next_registry.location,
                f"Declared settings registry '{next_registry.kind}' has no location.",
            )
            registry = next_registry

        return registry
