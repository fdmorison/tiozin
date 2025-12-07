from ..registry import MetadataRegistry


class SecretRegistry(MetadataRegistry):
    """
    Registry that manages secrets and credentials used by Tio.

    Supports any secure storage backend for secrets (e.g., HashiCorp Vault, AWS
    Secrets Manager, environment variables), while keeping Tio agnostic to the
    storage details. Ensures secrets can be retrieved safely by the application
    without hardcoding them.

    Tio automatically handles secret retrieval during pipeline execution, but the
    SecretRegistry is also available in the Context for custom manipulation by
    Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
