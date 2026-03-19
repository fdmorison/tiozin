import wrapt

from tiozin import config
from tiozin.api import SettingRegistry, SettingsManifest
from tiozin.exceptions import SettingsNotFoundError
from tiozin.utils import io


class FileSettingRegistry(SettingRegistry):
    """
    File-based settings registry.

    Loads framework configuration from any path or URI supported by fsspec,
    including local paths, object storage (``s3://``, ``gs://``, ``az://``),
    and remote protocols (``http://``, ``https://``, ``ftp://``, ``sftp://``).

    If ``location`` is not provided, Tiozin searches standard filesystem paths
    and falls back to built-in defaults. A ``tiozin.yaml`` can delegate to
    another ``SettingRegistry`` via ``registries.settings``.

    Attributes:
        location: Path or URI of the settings file (e.g. a local path, an S3 URI,
            or an HTTP URL). Optional: discovered automatically if not set.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)

    @wrapt.synchronized
    def setup(self) -> None:
        """
        Resolve the settings file location.

        Searches standard filesystem paths if ``location`` is not set.
        No-op if already resolved.
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

        if self.location:
            self.info(f"Loading settings from '{self.location}'")
        else:
            self.info("Loading built-in settings")

        self.ready = True

    def get(self, identifier: str = None, version: str = None) -> SettingsManifest:
        """
        Load and return the settings manifest from any fsspec-supported location.

        Args:
            identifier: Not used in this implementation.
            version: Not used in this implementation.

        Returns:
            The SettingsManifest. Falls back to built-in defaults if no settings file found.
        """
        if not self.location:
            return SettingsManifest.from_arguments()

        data = io.read_text(self.location)
        return SettingsManifest.from_yaml_or_json(data)

    def register(self, identifier: str, value: SettingsManifest) -> None:
        """
        Write a settings manifest to any fsspec-supported location.

        Args:
            identifier: File name, relative path, or absolute URI (.yaml, .yml, or .json).
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
