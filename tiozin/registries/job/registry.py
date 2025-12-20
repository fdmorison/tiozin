from ..registry import MetadataRegistry


class JobRegistry(MetadataRegistry):
    """
    Registry that provides access to the job manifests executed by Tiozin.

    Acts as an abstraction layer, allowing different storage backends (e.g., DynamoDB,
    Consul, MongoDB, Postgres) to manage job metadata while keeping Tiozin agnostic
    to the storage details.

    Tiozin automatically handles job manifest retrieval when executing commands
    like `tiozin run ingestion.yaml`, `tiozin run ingestion_job`, or `tiozin run job#12345`.

    The JobRegistry is used internally by Tiozin and is not available in the Context.
    """

    def __init__(self) -> None:
        super().__init__()
