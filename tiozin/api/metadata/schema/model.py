from __future__ import annotations

from typing import Any

from open_data_contract_standard.model import (
    OpenDataContractStandard,
    SchemaObject,
)

from tiozin.api.metadata.model import Metadata

from .converters import SchemaConverter
from .exceptions import SchemaNotFoundError


class Schema(SchemaObject, Metadata):
    @classmethod
    def from_contract(cls, contract: OpenDataContractStandard, name: str) -> Schema:
        """
        Creates a Schema from an Open Data Contract.
        Looks up a schema by name and converts it using the "odcs" format.
        Raises an exception if the schema is not found.
        """
        contract = contract.schema_ or []
        schema = next((schema for schema in contract if schema.name == name), None)
        SchemaNotFoundError.raise_if(
            schema is None,
            name=name,
        )
        return cls.import_("odcs", schema)

    def export(self, format: str) -> Any:
        """
        Converts this schema to another format.

        Supported formats include:
        - "odcs": returns a `SchemaObject` from `open_data_contract_standard`
        - "spark": returns a `StructType` from `pyspark.sql.types`
        - "openlineage": returns a `SchemaDatasetFacet` from `openlineage.client`

        Raises an exception if the format is not supported.
        """
        return SchemaConverter.for_format(format).export(self)

    @classmethod
    def import_(cls, format: str, data: Any) -> Schema:
        """
        Creates a Schema from another format.

        Supported formats include:
        - "odcs": expects a `SchemaObject` from `open_data_contract_standard`
        - "spark": expects a `StructType` from `pyspark.sql.types`

        The "openlineage" format does not support import.

        Raises an exception if the format is not supported.
        """
        return SchemaConverter.for_format(format).import_(data)
