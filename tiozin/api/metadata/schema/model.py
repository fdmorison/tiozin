from __future__ import annotations

from typing import Any, TypeAlias

from open_data_contract_standard.model import OpenDataContractStandard, SchemaObject
from pydantic import Field, ValidationError
from ruamel.yaml.constructor import DuplicateKeyError

from tiozin import config
from tiozin.exceptions import ModelError
from tiozin.utils import dump_yaml, load_yaml

from ..model import Model
from .converters import SchemaConverter
from .exceptions import SchemaNotFoundError

Schema: TypeAlias = SchemaObject


class SchemaManifest(Model):
    subject: str = Field(...)
    version: str = Field(config.tiozin_schema_default_version)
    schema: Schema = Field(...)

    @classmethod
    def from_yaml(cls, data: str) -> SchemaManifest:
        if not isinstance(data, str):
            raise ModelError(cls.__name__, f"Expected a model string, got: {data}")

        try:
            schema = SchemaObject.model_validate(load_yaml(data))
            return cls(subject=schema.name, schema=schema)
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

    def export(self, format: str) -> Any:
        converter = SchemaConverter.for_format(format)
        return converter.export(self.schema)

    @classmethod
    def import_(cls, format: str, data: Any) -> SchemaManifest:
        converter = SchemaConverter.for_format(format)
        schema = converter.import_(data)
        return SchemaManifest(subject=schema.name, schema=schema)

    @classmethod
    def from_contract(cls, contract: OpenDataContractStandard, schema_name: str) -> SchemaManifest:
        schemas = contract.schema_ or []
        schema = next((s for s in schemas if s.name == schema_name), None)
        if schema is None:
            raise SchemaNotFoundError(schema_name)
        schema = SchemaConverter.for_format("odcs").import_(schema)
        return cls(subject=schema.name, schema=schema)
