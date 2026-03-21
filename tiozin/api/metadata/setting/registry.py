from __future__ import annotations

from tiozin.compose import SettingRegistryProxy, tioproxy

from ... import Registry, SettingsManifest


@tioproxy(SettingRegistryProxy)
class SettingRegistry(Registry[SettingsManifest]):
    """
    Manages system settings and configuration.

    Storage-agnostic contract for setting backends (like databases, YAML files, or Consul).
    Available in Context for configuration access in Transforms, Inputs, and Outputs.
    """
