from typing import Self

from tiozin import config
from tiozin.api import SettingRegistry, SettingsManifest
from tiozin.exceptions import SettingsNotFoundError, TiozinInternalError
from tiozin.utils import io


class FileSettingRegistry(SettingRegistry):
    """
    File-based settings registry.

    Loads framework configuration from tiozin.yaml file or environment variables.
    Supports explicit paths, filesystem discovery, and registry delegation.

    Resolution order:

    1. Path provided via constructor.
    2. Path from TIO_SETTINGS_PATH environment variable.
    3. Project configuration:
       - ./tiozin.yaml
    4. User configuration:
       - ~/tiozin.yaml
       - ~/.config/tiozin/tiozin.yaml
    5. Container configuration:
       - /etc/tiozin/tiozin.yaml
       - /tiozin/tiozin.yaml
       - /config/tiozin.yaml
       - /tiozin.yaml
    6. Built-in settings derived from environment variables.

    tiozin.yaml may delegate settings resolution to another SettingRegistry
    (e.g. ConsulSettingRegistry). If delegated registry is also FileSettingRegistry,
    another settings file is loaded.

    Attributes:
        path: Settings file path. Overrides filesystem discovery when provided.
    """

    def __init__(self, path: io.StrOrPath = None, **options) -> None:
        super().__init__(**options)
        self.path = path or config.tiozin_settings_path
        self._settings = None

    def get(self, identifier: str = None, version: str = None) -> SettingsManifest:
        """
        Load settings manifest from filesystem.

        Args:
            identifier: Not used in this implementation.
            version: Not used in this implementation.

        Returns:
            SettingsManifest instance.

        Raises:
            SettingsNotFoundError: If an explicit path is set but the file does not exist.
            ManifestError: If the file contains invalid YAML or fails validation.
        """
        if self._settings:
            return self._settings

        data = self._get_from_file() or self._get_from_system()

        if data:
            self._settings = SettingsManifest.from_yaml_or_json(data)
        else:
            self.info("Loading built-in settings")
            self._settings = SettingsManifest.from_arguments()

        return self._settings

    def register(self, identifier: str, value: SettingsManifest) -> None:
        """
        Write a settings manifest to the filesystem.

        Args:
            identifier: File path with a ``.yaml``, ``.yml``, or ``.json`` extension.
            value: ``SettingsManifest`` instance to serialize and save.

        Raises:
            ValueError: If the file extension is not supported.
        """
        self.info(f"Writing settings manifest to {identifier}")

        if identifier.endswith((".yaml", ".yml")):
            data = value.to_yaml()
        elif identifier.endswith(".json"):
            data = value.to_json()
        else:
            raise ValueError(f"Unsupported settings format: {identifier}")

        io.write_text(identifier, data)

    def _get_from_file(self) -> str | None:
        if not self.path:
            return None

        self.info(f"Loading settings from '{self.path}'")
        SettingsNotFoundError.raise_if(
            not io.exists(self.path),
            location=self.path,
        )
        return io.read_text(self.path)

    def _get_from_system(self) -> str | None:
        for path in config.tiozin_settings_search_paths:
            if io.exists(path):
                self.info(f"Loading settings from '{path}'")
                return io.read_text(path)
        return None

    def delegate(self) -> Self:
        """
        Resolve the settings registry through delegation.

        Reads ``registries.settings`` from the current manifest. If it points
        to another ``FileSettingRegistry``, follows the chain. Stops when the
        manifest points to a different registry kind and loads it.

        Returns:
            The resolved ``SettingRegistry`` instance.

        Raises:
            TiozinInternalError: If circular delegation is detected.
        """
        from tiozin.compose.assembly.tiozin_registry import tiozin_registry

        visited = []
        manifest = self.get().registries.settings
        registry = tiozin_registry.load_manifest(manifest)

        while isinstance(registry, FileSettingRegistry):
            registry.ready = self.ready
            if not registry.path:
                return registry

            TiozinInternalError.raise_if(
                registry.path in visited,
                f"Circular settings delegation detected: {visited}",
            )
            visited.append(registry.path)
            manifest = registry.get().registries.settings
            registry = tiozin_registry.load_manifest(manifest)

        return registry
