from tiozin.api import SettingRegistry, SettingsManifest


class NoOpSettingRegistry(SettingRegistry):
    """
    No-op setting registry.

    Does nothing. Returns an empty `SettingsManifest` for reads and ignores writes.
    Useful for testing or when settings management is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def get(self) -> SettingsManifest:
        return SettingsManifest()
