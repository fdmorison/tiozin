"""
The Spark format: a Spark struct type in JSON.

The JSON form is what `StructType.jsonValue()` produces and
`StructType.fromJson()` accepts, so this package never imports pyspark.

Examples:

    ```python
    schema = Schema.from_spark(df.schema.jsonValue())
    struct = StructType.fromJson(schema.to_spark())
    ```
"""

from .converter import SparkSchemaConverter
from .enums import SparkTimeType
from .reader import SparkSchemaReader
from .spark_type import SparkType
from .writer import SparkSchemaWriter

__all__ = [
    "SparkSchemaConverter",
    "SparkSchemaReader",
    "SparkSchemaWriter",
    "SparkTimeType",
    "SparkType",
]
