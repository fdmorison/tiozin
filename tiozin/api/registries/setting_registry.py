from .. import Registry, SettingsManifest


class SettingRegistry(Registry[SettingsManifest]):
    """
    Manages system settings and configuration.

    Storage-agnostic contract for setting backends (like databases, YAML files, or Consul).
    Available in Context for configuration access in Transforms, Inputs, and Outputs.
    """
