from tiozin import config
from tiozin.api import SettingRegistry, SettingsManifest
from tiozin.exceptions import SettingsNotFoundError
from tiozin.utils import io


class FileSettingRegistry(SettingRegistry):
    """
    File-based settings registry.

    Loads framework configuration from a tiozin.yaml file.
    Supports any path or URI accepted by fsspec, including local paths,
    object storage (``s3://``, ``gs://``, ``az://``), and remote protocols
    (``http://``, ``https://``, ``ftp://``, ``sftp://``).

    Direct instantiation requires an explicit ``location``, or the settings
    file will be discovered via environment variable or filesystem search paths
    during ``setup()``.

    tiozin.yaml may delegate settings resolution to another SettingRegistry
    by setting ``registries.settings`` to a non-null value. The delegation
    chain is followed by ``SettingRegistry.delegate()``.

    Attributes:
        location: Settings file path or remote URI.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self._settings = None

    def setup(self) -> None:
        """
        Resolve settings location and load them.
        """
        if self.ready:
            return

        SettingsNotFoundError.raise_if(
            self.location and not io.exists(self.location),
            location=self.location,
        )

        if not self.location:
            for path in config.tiozin_settings_search_paths:
                if io.exists(path):
                    self.location = str(path)
                    break

        if not self.location:
            self.info("Loading built-in settings")
            self._settings = SettingsManifest.from_arguments()
        else:
            self.info(f"Loading settings from '{self.location}'")
            data = io.read_text(self.location)
            self._settings = SettingsManifest.from_yaml_or_json(data)

        self.ready = True

    def get(self, identifier: str = None, version: str = None) -> SettingsManifest:
        self.setup()
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
