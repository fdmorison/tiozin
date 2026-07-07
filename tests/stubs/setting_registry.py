from tiozin import SettingRegistry, SettingsManifest


class SettingRegistryStub(SettingRegistry):
    def __init__(self):
        super().__init__(location="stub://setting")

    def get(self) -> SettingsManifest:
        return SettingsManifest()
