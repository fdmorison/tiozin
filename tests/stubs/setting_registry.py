from tiozin.api.metadata.setting.base import SettingsManifest
from tiozin.api.metadata.setting.registry import SettingRegistry


class SettingRegistryStub(SettingRegistry):
    def __init__(self):
        super().__init__(location="stub://setting")

    def get(self) -> SettingsManifest:
        return SettingsManifest()
