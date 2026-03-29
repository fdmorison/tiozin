from tiozin.compose import tioproxy

from ..registry import Registry
from .model import Schema
from .proxy import SchemaRegistryProxy


@tioproxy(SchemaRegistryProxy)
class SchemaRegistry(Registry[Schema]):
    """
    Retrieves and stores schemas.

    Storage-agnostic contract for schema backends (like Confluent Schema Registry).
    Available in Context for schema handling in Transforms, Inputs, and Outputs.

    Attributes:
        show_schema: When `True`, logs the retrieved schema to the console after each
            successful `get()` call. Defaults to `False`.
    """

    def __init__(self, show_schema: bool = False, **options) -> None:
        super().__init__(**options)
        self.show_schema = show_schema
