from __future__ import annotations

from datacontract.export.spark_exporter import to_spark_schema
from datacontract.imports.spark_importer import _property_from_struct_type, create_schema_object
from pyspark.sql.types import StructType

from ..model import Schema
from .converter import SchemaConverter


class SparkSchemaConverter(SchemaConverter[StructType]):
    def export(self, schema: Schema) -> StructType:
        return to_spark_schema(schema)

    def import_(self, schema: StructType) -> Schema:
        properties = [_property_from_struct_type(field) for field in schema.fields]
        odcs_schema = create_schema_object(name="", properties=properties)
        return Schema(**odcs_schema.model_dump())
