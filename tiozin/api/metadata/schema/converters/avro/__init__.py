"""
The Avro format: an Avro record schema in JSON.

This package reads and writes the JSON directly, so it never imports an Avro
library.

Examples:

    ```python
    schema = Schema.from_format(
        "avro",
        {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]},
    )

    schema.to_format("avro")
    # {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
    ```
"""

from .converter import AvroSchemaConverter
from .reader import AvroSchemaReader
from .writer import AvroSchemaWriter

__all__ = [
    "AvroSchemaConverter",
    "AvroSchemaReader",
    "AvroSchemaWriter",
]
