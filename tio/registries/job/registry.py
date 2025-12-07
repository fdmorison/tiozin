from ..registry import MetadataRegistry


class JobRegistry(MetadataRegistry):
    """
    Registry that provides access to the job manifests executed by Tio.

    Acts as an abstraction layer, allowing different storage backends (e.g., DynamoDB,
    Consul, MongoDB, Postgres) to manage job metadata while keeping Tio agnostic
    to the storage details.

    Tio automatically handles job manifest retrieval when executing commands
    like `tio run ingestion.yaml`, `tio run ingestion_job`, or `tio run job#12345`.

    The JobRegistry is used internally by Tio and is not available in the Context.
    """

    def __init__(self) -> None:
        super().__init__()
