from abc import abstractmethod

from tiozin.compose import tioproxy

from ..registry import Registry
from .model import SettingsManifest
from .proxy import SettingRegistryProxy


@tioproxy(SettingRegistryProxy)
class SettingRegistry(Registry[SettingsManifest]):
    """
    Manages system settings and configuration.

    Storage-agnostic contract for setting backends (like databases, YAML files, or Consul).
    Available in Context for configuration access in Transforms, Inputs, and Outputs.
    """

    @abstractmethod
    def get(self) -> SettingsManifest:
        """
        Retrieve the current settings manifest.

        Raises:
            NotFoundException: When not found and `failfast=True`.
        """
