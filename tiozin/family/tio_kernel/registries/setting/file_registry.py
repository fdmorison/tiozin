import wrapt

from tiozin import SettingRegistry, SettingsManifest, config
from tiozin.exceptions import SettingsNotFoundError
from tiozin.utils import io

DEFAULTS = SettingsManifest()


class FileSettingRegistry(SettingRegistry):
    """
    File-based settings registry.

    Resolves settings location and delegates I/O to the model layer.

    Supports local paths and remote URIs via fsspec:
    s3://, gs://, az://, http://, https://, ftp://, sftp://.

    Formats: YAML (.yaml, .yml) and JSON (.json).

    Attributes:
        location: Path or URI of the ``tiozin.yaml`` file. If not provided,
            searches paths defined in ``config.tiozin_settings_search_paths``
            and falls back to built-in defaults if none are found.
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

    def get(self) -> SettingsManifest:
        if not self.location:
            return DEFAULTS
        return SettingsManifest.from_file(self.location, **self.options)
