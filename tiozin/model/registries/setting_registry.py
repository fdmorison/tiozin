from ..registry import Registry


class SettingRegistry(Registry[object]):
    """
    Manages system settings and configuration.

    Storage-agnostic contract for setting backends (like databases, YAML files, or Consul).
    Available in Context for configuration access in Transforms, Inputs, and Outputs.
    """

    def __init__(self, *args, **options) -> None:
        super().__init__(*args, **options)
