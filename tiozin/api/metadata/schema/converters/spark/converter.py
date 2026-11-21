from __future__ import annotations

import json
from typing import Any

from ...model import Schema
from ..converter import SchemaConverter
from .reader import SparkSchemaReader
from .writer import SparkSchemaWriter


class SparkSchemaConverter(SchemaConverter[dict[str, Any]]):
    """
    Converts to and from a Spark struct type in JSON. Loading also accepts the
    JSON as a string, such as the output of `StructType.json()`.

    Examples:

        ```python
        schema = Schema.from_spark(
            {
                "type": "struct",
                "fields": [
                    {"name": "id", "type": "long", "nullable": False, "metadata": {}},
                ],
            }
        )
        schema = Schema.from_spark(df.schema.json())

        schema.to_spark()
        # {
        #     "type": "struct",
        #     "fields": [
        #         {"name": "id", "type": "long", "nullable": False, "metadata": {}},
        #     ],
        # }
        ```
    """

    format = "spark"

    def dump(self, schema: Schema, version: str = None, **options) -> dict[str, Any]:
        return SparkSchemaWriter(version).write(schema)

    def load(self, schema: dict[str, Any] | str, **options) -> Schema:
        struct = json.loads(schema) if isinstance(schema, str) else schema
        return SparkSchemaReader().read(struct)
