from ..registry import MetadataRegistry


class SettingRegistry(MetadataRegistry):
    """
    Manages system settings and configuration.

    Storage-agnostic contract for setting backends (like databases, YAML files, or Consul).
    Available in Context for configuration access in Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
