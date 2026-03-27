from __future__ import annotations

import json

from datacontract.export.avro_exporter import to_avro_schema_json
from datacontract.export.bigquery_exporter import to_bigquery_fields_array
from datacontract.export.jsonschema_exporter import to_jsonschema_json
from datacontract.export.sql_exporter import _to_sql_table
from open_data_contract_standard.model import SchemaObject
from pydantic import Field

from tiozin.utils.io import StrOrPath, read_yaml, write_yaml

from ...domain import DomainModel


class SchemaManifest(DomainModel):
    subject: str = Field(...)
    version: str = Field("latest")
    schema: SchemaObject

    @staticmethod
    def load(path: StrOrPath) -> SchemaManifest:
        data = read_yaml(path)
        spec = SchemaObject(**data)
        return SchemaManifest(subject=spec.name, schema=spec)

    def save(self, path: StrOrPath) -> SchemaManifest:
        write_yaml(path, self.schema.model_dump())
        return self

    def to(self, format: str) -> str:
        match format:
            case "avro":
                return to_avro_schema_json(self.subject, self.schema)
            case "jsonschema":
                return to_jsonschema_json(self.subject, self.schema)
            case "postgres":
                return _to_sql_table(self.subject, self.schema, "postgres")
            case "spark":
                from datacontract.export.spark_exporter import to_spark_schema

                return to_spark_schema(self.schema)
            case "bigquery":
                return json.dumps(
                    {"fields": to_bigquery_fields_array(self.schema.properties or [])},
                    indent=2,
                )
            case _:
                raise ValueError(f"Unsupported export format: {format}")
