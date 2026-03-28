from __future__ import annotations

import json
from typing import TypeAlias

from open_data_contract_standard.model import OpenDataContractStandard, SchemaObject
from pydantic import Field, ValidationError
from ruamel.yaml.constructor import DuplicateKeyError

from tiozin import config
from tiozin.exceptions import ModelError
from tiozin.utils import dump_yaml, load_yaml

from ..model import Model
from .exceptions import SchemaNotFoundError

Schema: TypeAlias = SchemaObject


class SchemaManifest(Model):
    subject: str = Field(...)
    version: str = Field(config.tiozin_schema_default_version)
    schema: Schema = Field(...)

    @classmethod
    def from_contract(cls, contract: OpenDataContractStandard, subject: str) -> SchemaManifest:
        schemas = contract.schema_ or []
        schema = next((schema for schema in schemas if schema.name == subject), None)
        if schema is None:
            raise SchemaNotFoundError(subject)
        return cls.from_contract_schema(schema)

    @classmethod
    def from_contract_schema(cls, schema: SchemaObject) -> SchemaManifest:
        return cls(subject=schema.name, schema=schema)

    @classmethod
    def from_yaml(cls, data: str) -> SchemaManifest:
        if not isinstance(data, str):
            raise ModelError(cls.__name__, f"Expected a model string, got: {data}")

        try:
            return cls.from_contract_schema(
                SchemaObject.model_validate(load_yaml(data)),
            )
        except DuplicateKeyError as e:
            raise ModelError.from_ruamel(cls.__name__, e) from e
        except ValidationError as e:
            raise ModelError.from_pydantic(cls.__name__, e) from e
        except ModelError:
            raise
        except Exception as e:
            raise ModelError(cls.__name__, str(e)) from e

    def to_yaml(self) -> str:
        return dump_yaml(self.schema.model_dump(mode="json", exclude_unset=True))

    def to_json(self) -> str:
        return self.schema.model_dump_json(indent=2, exclude_unset=True, ensure_ascii=False) + "\n"

    def to(self, format: str) -> str:
        from datacontract.export.avro_exporter import to_avro_schema_json
        from datacontract.export.bigquery_exporter import to_bigquery_fields_array
        from datacontract.export.jsonschema_exporter import to_jsonschema_json
        from datacontract.export.sql_exporter import _to_sql_table

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
