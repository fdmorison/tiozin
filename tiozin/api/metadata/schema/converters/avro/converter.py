from __future__ import annotations

import json
from typing import Any

from ...model import Schema
from ..converter import SchemaConverter
from .reader import AvroSchemaReader
from .writer import AvroSchemaWriter


class AvroSchemaConverter(SchemaConverter[dict[str, Any]]):
    """
    Converts to and from an Avro record schema in JSON.

    Dumping returns the record as parsed JSON, a dict. Loading takes the
    record as a dict or as JSON text.

    Usually reached through Schema with the "avro" format rather than built
    directly.

    Examples:

        ```python
        schema = Schema.from_format(
            "avro",
            '{"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}',
        )

        schema.to_format("avro")
        # {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
        ```

        The converter can also be used on its own:

        ```python
        converter = AvroSchemaConverter()
        schema = converter.load({"type": "record", "name": "users", "fields": []})
        record = converter.dump(schema)
        ```
    """

    format = "avro"

    def dump(self, schema: Schema, **options) -> dict[str, Any]:
        return AvroSchemaWriter().write(schema)

    def load(self, schema: dict[str, Any] | str, **options) -> Schema:
        record = json.loads(schema) if isinstance(schema, str) else schema
        return AvroSchemaReader().read(record)
