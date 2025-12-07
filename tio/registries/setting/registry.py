from ..registry import MetadataRegistry


class SettingRegistry(MetadataRegistry):
    """
    Registry that manages system settings and configuration parameters in Tio.

    Supports any storage backend for settings (e.g., databases, YAML/JSON files,
    environment variables, key/value stores like Consul), while keeping Tio agnostic
    to the storage details. Enables pipelines and tasks to access configuration
    consistently across different environments.

    Tio automatically handles settings retrieval during pipeline execution, but
    the SettingRegistry is also available in the Context for custom manipulation
    by Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
