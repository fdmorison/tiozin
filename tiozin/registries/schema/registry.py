from ..registry import MetadataRegistry


class SchemaRegistry(MetadataRegistry):
    """
    Retrieves and stores schemas.

    Storage-agnostic contract for schema backends (like Confluent Schema Registry).
    Available in Context for schema handling in Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
