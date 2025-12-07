from ..registry import MetadataRegistry


class SchemaRegistry(MetadataRegistry):
    """
    Registry that represents schema backends able to retrieve and upsert schemas,
    similar to the Confluent Schema Registry.

    Supports any storage backend for schemas, typically JSON or Avro, while keeping
    Tio agnostic to the storage details.

    Tio automatically handles schema retrieval during pipeline execution, but the
    SchemaRegistry is also available in the Context for custom manipulation by
    Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
