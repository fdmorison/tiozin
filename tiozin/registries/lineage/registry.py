from ..registry import MetadataRegistry


class LineageRegistry(MetadataRegistry):
    """
    Registry that tracks data lineage in Tiozin according to the Open Lineage standard
    (https://openlineage.io/).

    Supports any storage backend for lineage information, while keeping Tiozin agnostic
    to the storage details. Lineage events and relationships conform to the Open
    Lineage specification to ensure interoperability and standardization.

    Tiozin automatically handles lineage tracking during pipeline execution. The
    LineageRegistry is used internally by Tiozin and is not available in the Context.
    """

    def __init__(self) -> None:
        super().__init__()
