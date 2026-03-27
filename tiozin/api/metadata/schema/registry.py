from ..registry import Registry
from .model import SchemaManifest


class SchemaRegistry(Registry[SchemaManifest]):
    """
    Retrieves and stores schemas.

    Storage-agnostic contract for schema backends (like Confluent Schema Registry).
    Available in Context for schema handling in Transforms, Inputs, and Outputs.
    """
